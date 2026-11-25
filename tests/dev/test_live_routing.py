from __future__ import annotations

from types import SimpleNamespace

from src import runner
from src.schema import AnswerStatus, CommonAnswer, Limitation


def test_live_context_cannot_use_manual_plans_or_mock_sandbox(monkeypatch) -> None:
    live_client = SimpleNamespace(model_id="approved-live-model", is_mock=False)
    live_sandbox = SimpleNamespace(config=SimpleNamespace(require_valid=lambda: None), is_mock=False)
    monkeypatch.setattr(runner, "_client", lambda live: live_client if live else None)
    monkeypatch.setattr(runner.SandboxConfig, "from_protocol", classmethod(lambda cls: live_sandbox.config))
    monkeypatch.setattr(runner, "DockerSandbox", lambda config: live_sandbox)

    context = runner._execution_context(True)

    assert context.client is live_client
    assert context.sandbox is live_sandbox
    assert context.use_manual_plans is False
    assert context.client.is_mock is False
    assert not isinstance(context.sandbox, runner.MockSandbox)


def test_offline_context_is_the_only_context_with_test_doubles(monkeypatch) -> None:
    mock_client = SimpleNamespace(model_id="mock-development-model", is_mock=True)
    monkeypatch.setattr(runner, "_client", lambda live: mock_client)

    context = runner._execution_context(False)

    assert context.client is mock_client
    assert isinstance(context.sandbox, runner.MockSandbox)
    assert context.use_manual_plans is True


def test_live_runner_passes_no_manual_plan_and_no_mock_sandbox(monkeypatch, tmp_path) -> None:
    live_client = SimpleNamespace(model_id="approved-live-model", is_mock=False)
    live_sandbox = SimpleNamespace(is_mock=False)
    context = runner.ExecutionContext(client=live_client, sandbox=live_sandbox, use_manual_plans=False)
    calls: dict[str, object] = {}
    answer = CommonAnswer(
        status=AnswerStatus.INSUFFICIENT,
        limitations=[Limitation(claim="test", reason_code="test")],
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AUD_SUD_ALLOW_LIVE_API", "true")
    monkeypatch.setattr(runner, "_execution_context", lambda live, require_sandbox=True: context)
    monkeypatch.setattr(runner, "run_direct", lambda client, question, scenario: (answer, {"calls": 0}))

    def fake_program(client, question, scenario, *, sandbox=None):
        calls["sandbox"] = sandbox
        return answer, {"calls": 0}

    def fake_d2(client, question, scenario, *, development_plan=None):
        calls["development_plan"] = development_plan
        return answer, {"calls": 0}

    monkeypatch.setattr(runner, "run_program", fake_program)
    monkeypatch.setattr(runner, "run_d2", fake_d2)

    runner.run_development(arms=["A", "C", "B"], live=True, question_ids=["D01-Q1"], experiment_id="live-routing")

    assert calls["sandbox"] is live_sandbox
    assert calls["sandbox"] is not None
    assert calls["development_plan"] is None
