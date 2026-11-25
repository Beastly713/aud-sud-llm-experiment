"""Frozen common prompt and definition loading for all three systems."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import (
    ClinicalEventArgs,
    CommonAnswer,
    InvestigationPlan,
    ObservationArgs,
    IntervalArgs,
    ResolveArgs,
    Question,
    Scenario,
)


@dataclass(frozen=True)
class PromptBundle:
    common_instructions: str
    definitions: dict[str, Any]
    answer_schema: dict[str, Any]

    def common_payload(self, question: Question, scenario: Scenario) -> dict[str, Any]:
        return {
            "common_instructions": self.common_instructions,
            "frozen_definitions": self.definitions,
            "question": question.text,
            "authorized_scope": [scope.model_dump(mode="json") for scope in question.authorized_scope],
            "answer_contract": self.answer_schema,
            "participant_id": scenario.participant_id,
            "snapshot_id": scenario.snapshot.snapshot_id,
        }


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_prompt_bundle(root: Path | None = None) -> PromptBundle:
    root = root or _repository_root()
    common_path = root / "prompts" / "common" / "common_instructions.md"
    definitions_path = root / "configs" / "definitions.json"
    if not common_path.exists() or not definitions_path.exists():
        raise FileNotFoundError("frozen common prompt or definitions file is missing")
    return PromptBundle(
        common_instructions=common_path.read_text(encoding="utf-8"),
        definitions=json.loads(definitions_path.read_text(encoding="utf-8")),
        answer_schema=CommonAnswer.model_json_schema(),
    )


def d2_tool_schemas() -> dict[str, dict[str, Any]]:
    """Return actual typed argument schemas, not question-conditioned answers."""
    return {
        "query_clinical_events": ClinicalEventArgs.model_json_schema(),
        "query_observations": ObservationArgs.model_json_schema(),
        "analyze_intervals": IntervalArgs.model_json_schema(),
        "resolve_evidence": ResolveArgs.model_json_schema(),
        "investigation_plan": InvestigationPlan.model_json_schema(),
    }

