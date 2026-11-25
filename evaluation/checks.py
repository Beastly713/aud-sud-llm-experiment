"""Mechanical prechecks shared by scoring and blinded review tooling.

These checks validate structure, IDs, units and explicit status fields. They never
decide semantic support; that remains a blinded human annotation requirement.
"""

from __future__ import annotations

from typing import Any

from src.schema import CommonAnswer, GoldRecord, FractionValue, NumericValue, TimeRangeValue
from src.serialization import normalize_number


def _field_value(finding: object, key: str) -> object:
    if key == "value":
        value = getattr(finding, "value", None)
        return getattr(value, "value", None) if isinstance(value, NumericValue) else None
    if key == "unit":
        value = getattr(finding, "value", None)
        return getattr(value, "unit", None)
    if key == "fraction":
        value = getattr(finding, "value", None)
        return getattr(value, "fraction", None) if isinstance(value, FractionValue) else None
    if key in {"numerator_seconds", "denominator_seconds"}:
        value = getattr(finding, "value", None)
        if isinstance(value, FractionValue):
            return value.numerator if key == "numerator_seconds" else value.denominator
        return getattr(finding, key, None)
    if key == "coverage_type":
        value = getattr(finding, "value", None)
        return (value.coverage_type.value if isinstance(value, FractionValue) else getattr(finding, key, None))
    if key == "comparison_type":
        value = getattr(finding, key, None)
        return value.value if hasattr(value, "value") else value
    if key == "eligibility_status":
        value = getattr(finding, key, None)
        return value.value if hasattr(value, "value") else value
    if key == "assertion":
        value = getattr(finding, "assertion_status", None)
        return value.value if hasattr(value, "value") else value
    if key == "action_status":
        value = getattr(finding, key, None)
        return value.value if hasattr(value, "value") else value
    if key == "selected_ids":
        return set(getattr(finding, key, []))
    if key == "interval_start":
        interval = getattr(finding, "interval", None)
        return interval.start.isoformat() if interval else None
    if key == "interval_end":
        interval = getattr(finding, "interval", None)
        return interval.end.isoformat() if interval else None
    if key == "time":
        value = getattr(finding, "value", None)
        return value.lower.isoformat() if isinstance(value, TimeRangeValue) and value.lower == value.upper else None
    if key in {"lower", "upper", "precision"}:
        value = getattr(finding, "value", None)
        if not isinstance(value, TimeRangeValue):
            return None
        if key == "lower":
            return value.lower.isoformat()
        if key == "upper":
            return value.upper.isoformat()
        return value.precision.value
    if key == "mention_id":
        return getattr(finding, "mention_id", None) or (getattr(finding, "selected_ids", [None])[0] if getattr(finding, "selected_ids", []) else None)
    if key == "evidence_class":
        value = getattr(finding, key, None)
        return value.value if hasattr(value, "value") else value
    if key == "temporal_precision":
        value = getattr(finding, key, None)
        return value.value if hasattr(value, "value") else value
    if key == "statistic":
        return getattr(finding, "requested_statistic", None)
    return getattr(finding, key, None)


def _slot_matches(finding: object, slot: object) -> bool:
    expected = slot.expected
    if "value" in expected and isinstance(expected.get("value"), (int, float)):
        actual_value = _field_value(finding, "value")
        actual_unit = _field_value(finding, "unit")
        expected_unit = expected.get("unit")
        if not isinstance(actual_value, (int, float)) or not isinstance(actual_unit, str) or not isinstance(expected_unit, str):
            return False
        actual_normalized, actual_normalized_unit = normalize_number(actual_value, actual_unit)
        expected_normalized, expected_normalized_unit = normalize_number(float(expected["value"]), expected_unit)
        tolerance = slot.absolute_tolerance if slot.absolute_tolerance is not None else 0.0
        if actual_normalized_unit != expected_normalized_unit or abs(actual_normalized - expected_normalized) > tolerance:
            return False
    for key, value in expected.items():
        if key in {"claim", "reason_code"}:
            continue
        if key in {"value", "unit"} and "value" in expected:
            continue
        actual = _field_value(finding, key)
        if key == "selected_ids":
            if actual != set(value):
                return False
        elif key == "value" and isinstance(actual, (int, float)) and isinstance(value, (int, float)):
            tolerance = slot.absolute_tolerance if slot.absolute_tolerance is not None else 0.0
            if abs(float(actual) - float(value)) > tolerance:
                return False
        elif actual != value:
            return False
    if slot.comparison_type is not None and _field_value(finding, "comparison_type") != slot.comparison_type.value:
        return False
    return True


def automated_checks(answer: CommonAnswer, gold: GoldRecord, known_source_ids: set[str]) -> dict[str, Any]:
    cited = {source_id for finding in answer.findings for source_id in finding.source_ids}
    cited.update(source_id for limitation in answer.limitations for source_id in limitation.source_ids)
    findings = answer.findings
    matched_slots = sum(any(_slot_matches(finding, slot) for finding in findings) for slot in gold.required_slots if slot.kind != "status")
    expected_limitations = {slot.expected.get("reason_code") for slot in gold.required_limitations}
    delivered_limitations = {item.reason_code for item in answer.limitations}
    limitation_matches = len(expected_limitations & delivered_limitations)
    comparison_qualification_errors = sum(
        1 for finding in findings
        if finding.claim_kind.value == "comparison"
        and finding.comparison_type is None
    )
    return {
        "schema_valid": True,
        "status_matches": answer.status == gold.status,
        "unknown_source_ids": sorted(cited - known_source_ids),
        "all_citations_resolve": cited.issubset(known_source_ids),
        "finding_count": len(answer.findings),
        "limitation_count": len(answer.limitations),
        "required_slot_matches": matched_slots,
        "required_slot_total": sum(slot.kind != "status" for slot in gold.required_slots),
        "required_limitation_matches": limitation_matches,
        "required_limitation_total": len(expected_limitations),
        "comparison_qualification_errors": comparison_qualification_errors,
        "semantic_review_required": True,
    }

