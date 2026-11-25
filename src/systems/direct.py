"""System A: complete evidence, direct interpretation and explicit review."""

from __future__ import annotations

from typing import Any

from ..model_client import LLMClient, SemanticCallBudget
from ..schema import CommonAnswer, Question, Scenario


def run_direct(client: LLMClient, question: Question, scenario: Scenario) -> tuple[CommonAnswer, dict[str, Any]]:
    payload = {
        "question": question.text,
        "evidence_snapshot": scenario.model_dump(mode="json"),
        "operation_definitions": "shared protocol definitions; no external tools",
        "instruction": "produce a provisional common answer, then independently review it for scope, calculations, citations and abstention",
    }
    budget = SemanticCallBudget()
    budget.consume()
    draft = client.generate(purpose="direct-draft", question=question, payload=payload, schema=CommonAnswer)
    review_payload = {**payload, "draft": draft.value, "review": "return the corrected final common answer"}
    budget.consume()
    reviewed = client.generate(purpose="direct-review", question=question, payload=review_payload, schema=CommonAnswer)
    try:
        answer = CommonAnswer.model_validate(reviewed.value)
    except Exception:
        budget.consume()
        repaired = client.generate(purpose="direct-repair", question=question, payload={**review_payload, "diagnostic": "invalid common answer schema; repair only schema and evidence grounding"}, schema=CommonAnswer)
        answer = CommonAnswer.model_validate(repaired.value)
        reviewed = repaired
    return answer, {"draft": draft.value, "review": reviewed.value, "calls": budget.used}

