from __future__ import annotations

import pytest

from src.schema import (
    CommonAnswer,
    FractionValue,
    InvestigationPlan,
    IntervalArgs,
    IntervalStep,
    Limitation,
    Missingness,
    NumericValue,
    Observation,
)


def test_zero_and_absent_are_distinct() -> None:
    from src.schema import MeasurementValue

    zero = MeasurementValue(value=0, units="bpm")
    absent = MeasurementValue(value=None, units="bpm", missingness=Missingness.ABSENT)
    assert zero.value == 0
    assert absent.value is None
    with pytest.raises(ValueError):
        MeasurementValue(value=None, units="bpm")


def test_fraction_requires_matching_denominator() -> None:
    with pytest.raises(ValueError):
        FractionValue(numerator=2, denominator=4, fraction=0.6, coverage_type="actual_support")


def test_plan_rejects_forward_dependency() -> None:
    with pytest.raises(ValueError):
        InvestigationPlan(
            plan_id="p",
            intent="bad",
            steps=[IntervalStep(id="first", args=IntervalArgs(operation="summary", observation_ref="later"))],
            output="x",
        )


def test_answer_requires_reason_for_insufficiency() -> None:
    with pytest.raises(ValueError):
        CommonAnswer(status="insufficient")
    answer = CommonAnswer(status="insufficient", limitations=[Limitation(claim="missing", reason_code="unknown")])
    assert answer.status.value == "insufficient"

