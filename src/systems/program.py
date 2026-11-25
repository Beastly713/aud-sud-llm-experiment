"""System C: generated general-purpose Python in isolated execution."""

from __future__ import annotations

from typing import Any

from ..model_client import LLMClient, SemanticCallBudget
from ..prompt_loader import load_prompt_bundle
from ..schema import CommonAnswer, GeneratedProgram, Question, Scenario
from .sandbox import DockerSandbox, MockSandbox, SandboxConfig, SandboxError, run_generated_python


def run_program(
    client: LLMClient,
    question: Question,
    scenario: Scenario,
    *,
    sandbox: Any | None = None,
) -> tuple[CommonAnswer, dict[str, Any]]:
    common = load_prompt_bundle().common_payload(question, scenario)
    payload = {
        **common,
        "fixture_json": scenario.model_dump(mode="json"),
        "system_instruction": "System C: write self-contained standard-library Python reading /work/fixture.json and emitting compact JSON facts; do not use external data.",
    }
    budget = SemanticCallBudget()
    responses = []
    budget.consume()
    generated = client.generate(purpose="program-code", question=question, payload=payload, schema=GeneratedProgram)
    responses.append(generated)
    # A live provider supplies only code as structured output; code is never executed
    # on the host process.
    try:
        script = GeneratedProgram.model_validate(generated.value).code
    except Exception:
        budget.consume()
        generated = client.generate(purpose="program-repair", question=question, payload={**payload, "diagnostic": "invalid generated-program schema; repair syntax/schema only"}, schema=GeneratedProgram)
        responses.append(generated)
        script = GeneratedProgram.model_validate(generated.value).code
    # Tests pass MockSandbox explicitly. Production/default execution uses the
    # configured disposable Docker sandbox and never executes generated code on
    # the host or silently falls back to a test double.
    runtime = sandbox or DockerSandbox(SandboxConfig.from_protocol())
    try:
        execution = runtime.run(scenario.model_dump(mode="json"), script) if hasattr(runtime, "run") else run_generated_python(scenario.model_dump(mode="json"), script)
        failure = None
    except SandboxError as exc:
        execution = {"error": str(exc)}
        failure = "sandbox_failure"
        if budget.used < budget.max_calls - 1:
            budget.consume()
            repaired = client.generate(purpose="program-repair", question=question, payload={**payload, "diagnostic": str(exc), "instruction": "repair the self-contained script only; do not add external access"}, schema=GeneratedProgram)
            responses.append(repaired)
            script = GeneratedProgram.model_validate(repaired.value).code
            try:
                execution = runtime.run(scenario.model_dump(mode="json"), script) if hasattr(runtime, "run") else run_generated_python(scenario.model_dump(mode="json"), script)
                failure = None
            except SandboxError as second_exc:
                execution = {"error": str(second_exc)}
    final_payload = {**payload, "generated_code": script, "execution_result": execution, "instruction": "compose the common answer from the question, complete evidence and execution result"}
    budget.consume()
    final = client.generate(purpose="program-compose", question=question, payload=final_payload, schema=CommonAnswer)
    responses.append(final)
    answer = CommonAnswer.model_validate(final.value)
    return answer, {"code": script, "execution": execution, "failure": failure, "raw_answer": answer.model_dump(mode="json"), "calls": budget.used, "model_calls": [item.model_dump(mode="json") for item in responses]}

