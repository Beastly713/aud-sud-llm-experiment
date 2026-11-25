"""Reproducible execution harness for development and later authorized cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

from .devdata import make_plans, make_questions, make_scenarios
from .model_client import MockClient, ModelConfig, HostedModelClient, RetryingClient, prompt_hash
from .schema import ExecutionTrace, Question, Scenario
from .systems.direct import run_direct
from .systems.program import run_program
from .systems.sandbox import DockerSandbox, MockSandbox, SandboxConfig
from .systems.d2.workflow import run_d2


def tuple_id(experiment_id: str, cohort: str, question_id: str, arm: str, repeat: int) -> str:
    material = f"{experiment_id}|{cohort}|{question_id}|{arm}|{repeat}".encode()
    return hashlib.sha256(material).hexdigest()[:24]


def schedule(questions: list[Question], arms: list[str], cohort: str, seed: int, experiment_id: str, repeat: int = 1) -> list[dict[str, object]]:
    rows = [
        {"tuple_id": tuple_id(experiment_id, cohort, question.question_id, arm, repeat), "question_id": question.question_id, "arm": arm, "cohort": cohort, "repeat": repeat}
        for question in questions for arm in arms
    ]
    random.Random(seed).shuffle(rows)
    return rows


def select_repeat_subset(questions: list[Question], *, seed: int = 20261125) -> list[str]:
    """Select one question per scenario using metadata only.

    The held-out question metadata is supplied by the later freeze step; this helper
    does not construct or materialize any held-out scenario here.
    """
    grouped: dict[str, list[Question]] = {}
    for question in questions:
        grouped.setdefault(question.scenario_id, []).append(question)
    rng = random.Random(seed)
    selected: list[str] = []
    for scenario_id in sorted(grouped):
        candidates = sorted(grouped[scenario_id], key=lambda item: (item.question_class.value, item.difficulty, item.question_id))
        selected.append(rng.choice(candidates).question_id)
    return selected


def select_development_questions(questions: list[Question], question_ids: list[str] | None = None) -> list[Question]:
    """Select authored development questions without constructing any held-out data."""
    if question_ids is None:
        return list(questions)
    requested = [item.strip() for item in question_ids if item.strip()]
    if not requested:
        raise ValueError("at least one development question ID is required")
    available = {question.question_id: question for question in questions}
    unknown = sorted(set(requested) - set(available))
    if unknown:
        raise ValueError(f"unknown development question ID(s): {', '.join(unknown)}")
    if len(set(requested)) != len(requested):
        raise ValueError("development question IDs must be unique")
    return [available[item] for item in requested]


def _client(live: bool):
    if live:
        provider = os.environ.get("AUD_SUD_PROVIDER", "").strip()
        model_id = os.environ.get("AUD_SUD_MODEL_ID", "").strip()
        if not provider or not model_id:
            raise RuntimeError("live execution requires AUD_SUD_PROVIDER and AUD_SUD_MODEL_ID")
        if not os.environ.get("AUD_SUD_API_KEY"):
            raise RuntimeError("live execution requires AUD_SUD_API_KEY")
        config = ModelConfig(model_id=model_id, allow_live=True, provider=provider, api_base=os.environ.get("AUD_SUD_API_BASE"))
        return RetryingClient(HostedModelClient(config, cli_live=True))
    return RetryingClient(MockClient())


@dataclass(frozen=True)
class ExecutionContext:
    client: object
    sandbox: object
    use_manual_plans: bool


def _execution_context(live: bool, *, require_sandbox: bool = True) -> ExecutionContext:
    """Build an execution context with no live fallback to test doubles."""
    if live:
        sandbox = None
        if require_sandbox:
            sandbox = DockerSandbox(SandboxConfig.from_protocol())
            sandbox.config.require_valid()
        client = _client(True)
        return ExecutionContext(client=client, sandbox=sandbox, use_manual_plans=False)
    return ExecutionContext(client=_client(False), sandbox=MockSandbox(), use_manual_plans=True)


def run_development(*, arms: list[str] | None = None, seed: int = 20261125, experiment_id: str = "development", live: bool = False, question_ids: list[str] | None = None) -> Path:
    if live and (os.environ.get("AUD_SUD_ALLOW_LIVE_API", "false").lower() != "true"):
        raise RuntimeError("live development execution requires AUD_SUD_ALLOW_LIVE_API=true")
    arms = arms or ["A", "C", "B"]
    if any(arm not in {"A", "B", "C"} for arm in arms):
        raise ValueError("arms must be drawn from A, B and C")
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    questions = select_development_questions(questions, question_ids)
    by_scenario = {scenario.scenario_id: scenario for scenario in scenarios}
    by_question = {question.question_id: question for question in questions}
    context = _execution_context(live, require_sandbox="C" in arms)
    client = context.client
    if live and (getattr(client, "is_mock", False) or isinstance(context.sandbox, MockSandbox) or context.use_manual_plans):
        raise RuntimeError("live execution was given an offline test double or authored development plan")
    if "C" in arms and context.sandbox is None:
        raise RuntimeError("System C live execution requires a configured Docker sandbox")
    plans = make_plans(scenarios, questions) if context.use_manual_plans else {}
    run_root = Path("runs") / experiment_id
    for subdir in ("manifest", "raw", "delivered", "traces", "usage"):
        (run_root / subdir).mkdir(parents=True, exist_ok=True)
    execution_manifest = run_root / "manifest" / "execution.json"
    if execution_manifest.exists():
        existing = json.loads(execution_manifest.read_text(encoding="utf-8"))
        if bool(existing.get("live")) != live:
            raise RuntimeError("run identifier is already associated with a different execution mode")
        if existing.get("model_id") != getattr(client, "model_id", "unknown"):
            raise RuntimeError("run identifier is already associated with a different model")
        expected_provider = os.environ.get("AUD_SUD_PROVIDER") if live else "mock"
        if existing.get("provider") != expected_provider:
            raise RuntimeError("run identifier is already associated with a different provider")
        if existing.get("seed") != seed:
            raise RuntimeError("run identifier is already associated with a different schedule seed")
        if existing.get("arms") != arms or existing.get("questions") != [question.question_id for question in questions]:
            raise RuntimeError("run identifier is already associated with a different schedule")
    manifest = {"experiment_id": experiment_id, "cohort": "development", "seed": seed, "arms": arms, "questions": [question.question_id for question in questions], "gold_isolation": True, "live": live, "execution_mode": "live" if live else "mock", "model_id": getattr(client, "model_id", "unknown"), "provider": os.environ.get("AUD_SUD_PROVIDER") if live else "mock"}
    execution_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = schedule(questions, arms, "development", seed, experiment_id)
    (run_root / "manifest" / "schedule.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completed = {line.split("\t", 1)[0] for line in (run_root / "manifest" / "completed.tsv").read_text().splitlines()} if (run_root / "manifest" / "completed.tsv").exists() else set()
    attempted = successful = failed = 0
    with (run_root / "manifest" / "completed.tsv").open("a", encoding="utf-8") as done:
        for row in rows:
            if row["tuple_id"] in completed:
                continue
            started = time.perf_counter()
            attempted += 1
            question = by_question[str(row["question_id"])]
            scenario = by_scenario[question.scenario_id]
            arm = str(row["arm"])
            failure = None
            try:
                if arm == "A":
                    answer, detail = run_direct(client, question, scenario)
                elif arm == "C":
                    answer, detail = run_program(client, question, scenario, sandbox=context.sandbox)
                elif arm == "B":
                    answer, detail = run_d2(client, question, scenario, development_plan=plans.get(question.question_id))
                else:
                    raise ValueError(f"unknown arm {arm}")
            except Exception as exc:  # retain attempted denominator and diagnostics
                answer = None
                detail = {"error": str(exc)}
                failure = "execution_failure"
            workflow_failure = failure or detail.get("failure")
            if workflow_failure or answer is None:
                failed += 1
            else:
                successful += 1
            raw = detail.get("raw_answer") if answer is not None else None
            delivered = detail.get("delivered_answer", answer.model_dump(mode="json")) if answer is not None else None
            (run_root / "raw" / f"{row['tuple_id']}.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (run_root / "delivered" / f"{row['tuple_id']}.json").write_text(json.dumps(delivered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            model_calls = detail.get("model_calls", [])
            (run_root / "usage" / f"{row['tuple_id']}.json").write_text(json.dumps(model_calls, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            input_tokens = sum(int(item["input_tokens"]) for item in model_calls if isinstance(item, dict) and item.get("input_tokens") is not None)
            output_tokens = sum(int(item["output_tokens"]) for item in model_calls if isinstance(item, dict) and item.get("output_tokens") is not None)
            trace = ExecutionTrace(question_id=question.question_id, scenario_id=question.scenario_id, arm=arm, cohort="development", tuple_id=str(row["tuple_id"]), prompt_hashes={"question": prompt_hash({"question": question.text})}, model_id=getattr(client, "model_id", "hosted"), calls=int(detail.get("calls", 0)), transport_retries=sum(int(item.get("transport_retries", 0)) for item in model_calls if isinstance(item, dict)), plan=detail.get("plan"), code=detail.get("code"), tool_trace=detail.get("tool_trace", []), raw_answer=raw, delivered_answer=delivered, failure_class=workflow_failure, input_tokens=input_tokens or None, output_tokens=output_tokens or None, latency_ms=(time.perf_counter() - started) * 1000, model_calls=model_calls)
            (run_root / "traces" / f"{row['tuple_id']}.json").write_text(json.dumps(trace.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            done.write(f"{row['tuple_id']}\t{arm}\t{question.question_id}\n")
    remaining = sum(1 for row in rows if row["tuple_id"] not in completed) - attempted
    summary = {"experiment_id": experiment_id, "execution_mode": "live" if live else "mock", "attempted": attempted, "successful": successful, "failed": failed, "total_scheduled": len(rows), "remaining": remaining}
    (run_root / "manifest" / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return run_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Run only the authorized development cohort by default")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--arms", default="A,C,B")
    parser.add_argument("--seed", type=int, default=20261125)
    parser.add_argument("--run", default="development")
    parser.add_argument("--mock", action="store_true", help="use the local mock client")
    parser.add_argument("--live", action="store_true", help="explicitly authorize hosted-model requests")
    parser.add_argument("--questions", help="comma-separated development question IDs, or one ID")
    args = parser.parse_args()
    if args.split != "dev":
        raise SystemExit("held-out benchmark execution is intentionally not implemented in the development repository")
    if not args.mock and not args.live:
        raise SystemExit("choose --mock or explicitly choose --live with the required environment flag")
    question_ids = [item.strip() for item in args.questions.split(",")] if args.questions else None
    root = run_development(arms=[item for item in args.arms.split(",") if item], seed=args.seed, experiment_id=args.run, live=args.live, question_ids=question_ids)
    print(root)


if __name__ == "__main__":
    main()

