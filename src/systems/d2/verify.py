"""Mechanical B-only checks for composed answers.

The verifier binds an emitted finding to one computed fact and checks its typed
content. It is deliberately not a semantic judge; independent scoring still
handles narrative meaning and clinical-grounding review.
"""

from __future__ import annotations

from datetime import datetime
from math import isclose
from typing import Any

from ...schema import AnswerStatus, CommonAnswer, EvidenceBundle, Finding, NumericValue


def _value_matches(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return actual is expected
    if actual.kind != expected.kind:
        return False
    if isinstance(actual, NumericValue):
        if actual.unit != expected.unit:
            return False
        tolerance = 0.01 if actual.unit == "µS" else 0.1 if actual.unit in {"bpm", "°C"} else 1e-9
        return isclose(float(actual.value), float(expected.value), abs_tol=tolerance, rel_tol=0.0)
    if actual.kind == "time_range":
        return actual.lower == expected.lower and actual.upper == expected.upper and actual.precision == expected.precision
    return actual.model_dump(mode="json") == expected.model_dump(mode="json")


def _finding_matches(candidate: Finding, fact: Finding) -> bool:
    """Compare all material fields supplied by the answer to one trusted fact."""
    if candidate.claim_kind != fact.claim_kind:
        return False
    for field in (
        "metric", "method", "site", "requested_statistic", "reference_id", "policy_id",
        "episode_rule_id", "comparison_type", "eligibility_status", "assessment_id",
        "reference_revision", "denominator_seconds", "coverage_type", "occurrence_id",
        "mention_id", "evidence_class", "action_status", "assertion_status", "temporal_precision",
    ):
        if getattr(candidate, field) != getattr(fact, field):
            return False
    if fact.value is not None and not _value_matches(candidate.value, fact.value):
        return False
    if candidate.interval != fact.interval:
        return False
    if set(candidate.selected_ids) != set(fact.selected_ids):
        return False
    if fact.source_ids and not set(candidate.source_ids).issubset(set(fact.source_ids)):
        return False
    if fact.value is not None and candidate.value is None:
        return False
    if fact.value is None and candidate.value is not None:
        return False
    if fact.claim_kind.value == "event" and not candidate.selected_ids and not candidate.occurrence_id:
        return False
    return True


def _limitation_matches(candidate: Any, bundle: EvidenceBundle) -> bool:
    for limitation in bundle.limitations:
        if limitation.reason_code != candidate.reason_code:
            continue
        if candidate.source_ids and not set(candidate.source_ids).issubset(set(limitation.source_ids)):
            continue
        if candidate.selected_ids and not set(candidate.selected_ids).issubset(set(limitation.selected_ids)):
            continue
        return True
    return False


def verify_answer(answer: CommonAnswer, bundle: EvidenceBundle) -> tuple[CommonAnswer, list[str]]:
    problems: list[str] = []
    verified: list[Finding] = []
    for finding in answer.findings:
        if any(_finding_matches(finding, fact) for fact in bundle.computed_facts):
            verified.append(finding)
        else:
            problems.append("finding does not match a computed fact on its typed value, scope, evidence or comparison binding")
    for limitation in answer.limitations:
        if not _limitation_matches(limitation, bundle):
            problems.append(f"limitation is not bound to a bundle limitation: {limitation.reason_code}")
    if problems and answer.findings:
        answer = answer.model_copy(update={"findings": verified, "status": AnswerStatus.PARTIAL if verified else AnswerStatus.INSUFFICIENT})
    return answer, problems
