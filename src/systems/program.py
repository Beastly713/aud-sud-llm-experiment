"""System C: generated general-purpose Python in isolated execution."""

from __future__ import annotations

from typing import Any

from ..model_client import LLMClient, SemanticCallBudget
from ..schema import CommonAnswer, GeneratedProgram, Question, Scenario
from .sandbox import MockSandbox, SandboxError, run_generated_python


def run_program(
    client: LLMClient,
    question: Question,
    scenario: Scenario,
    *,
    sandbox: Any | None = None,
) -> tuple[CommonAnswer, dict[str, Any]]:
    payload = {
        "question": question.text,
        "fixture_json": scenario.model_dump(mode="json"),
        "operation_definitions": "shared frozen definitions; standard-library Python only",
        "instruction": "write a self-contained script reading /work/fixture.json and emitting compact JSON facts; do not use external data",
    }
    budget = SemanticCallBudget()
    budget.consume()
    generated = client.generate(purpose="program-code", question=question, payload=payload, schema=GeneratedProgram)
    # A live provider supplies only code as structured output; code is never executed
    # on the host process.
    try:
        script = GeneratedProgram.model_validate(generated.value).code
    except Exception:
        budget.consume()
        generated = client.generate(purpose="program-repair", question=question, payload={**payload, "diagnostic": "invalid generated-program schema; repair syntax/schema only"}, schema=GeneratedProgram)
        script = GeneratedProgram.model_validate(generated.value).code
    runtime = sandbox or MockSandbox()
    try:
        execution = runtime.run(scenario.model_dump(mode="json"), script) if hasattr(runtime, "run") else run_generated_python(scenario.model_dump(mode="json"), script)
        failure = None
    except SandboxError as exc:
        execution = {"error": str(exc)}
        failure = "sandbox_failure"
        if budget.used < budget.max_calls - 1:
            budget.consume()
            repaired = client.generate(purpose="program-repair", question=question, payload={**payload, "diagnostic": str(exc), "instruction": "repair the self-contained script only; do not add external access"}, schema=GeneratedProgram)
            script = GeneratedProgram.model_validate(repaired.value).code
            try:
                execution = runtime.run(scenario.model_dump(mode="json"), script) if hasattr(runtime, "run") else run_generated_python(scenario.model_dump(mode="json"), script)
                failure = None
            except SandboxError as second_exc:
                execution = {"error": str(second_exc)}
    final_payload = {**payload, "generated_code": script, "execution_result": execution, "instruction": "compose the common answer from the question, complete evidence and execution result"}
    budget.consume()
    final = client.generate(purpose="program-compose", question=question, payload=final_payload, schema=CommonAnswer)
    return CommonAnswer.model_validate(final.value), {"code": script, "execution": execution, "failure": failure, "calls": budget.used}

