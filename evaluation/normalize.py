"""Deterministic normalization of structured answer fields."""

from __future__ import annotations

from typing import Any

from src.serialization import normalize_number, normalize_value


def normalized_answer(answer: dict[str, Any]) -> dict[str, Any]:
    return normalize_value(answer)


def numeric_matches(actual: dict[str, Any], expected: dict[str, Any], tolerance: float) -> bool:
    if actual.get("unit") != expected.get("unit"):
        return False
    actual_value, actual_unit = normalize_number(actual["value"], actual["unit"])
    expected_value, expected_unit = normalize_number(expected["value"], expected["unit"])
    return actual_unit == expected_unit and abs(actual_value - expected_value) <= tolerance

