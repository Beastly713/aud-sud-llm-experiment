from __future__ import annotations

import pytest

from src.devdata import make_plans, make_questions, make_scenarios
from src.evidence_store import EvidenceStore
from src.schema import ClinicalEventArgs, ClinicalStep, IntervalArgs, IntervalStep, ObservationArgs, ObservationStep, InvestigationPlan
from src.systems.d2.engine import D2Engine


def _extended_anchor_plan(base_plan: InvestigationPlan, scenario_id: str) -> InvestigationPlan:
    steps = list(base_plan.steps)
    if "span" not in {step.id for step in steps}:
        steps.extend(
            [
                IntervalStep(id="span", args=IntervalArgs(operation="between_event_anchors", start_ref="onset", end_ref="administration")),
                ObservationStep(id="hr", args=ObservationArgs(metric="heart_rate", method="chest_ecg", interval_ref="span")),
                IntervalStep(id="summary", args=IntervalArgs(operation="summary", observation_ref="hr")),
            ]
        )
    elif "summary" not in {step.id for step in steps}:
        if "hr" not in {step.id for step in steps}:
            steps.append(ObservationStep(id="hr", args=ObservationArgs(metric="heart_rate", method="chest_ecg", interval_ref="span")))
        steps.append(IntervalStep(id="summary", args=IntervalArgs(operation="summary", observation_ref="hr")))
    return InvestigationPlan(plan_id=f"blocked-{scenario_id}", intent="blocked dependent computation", steps=steps, output="qualified")


def test_approximate_anchor_blocks_dependents_without_scope_substitution() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    question = next(item for item in questions if item.question_id == "D02-Q4a")
    plan = _extended_anchor_plan(plans[question.question_id], "D02")
    results, _ = D2Engine(EvidenceStore(scenarios[1])).execute(question, plan)
    assert results["span"].interval is None
    assert results["hr"].scope is None
    assert results["hr"].selected_observation_ids == []
    assert any("anchor" in limitation or "dependent interval" in limitation for limitation in results["hr"].limitations)
    assert results["summary"].facts == []
    assert any("unavailable" in limitation for limitation in results["summary"].limitations)


def test_missing_and_ambiguous_anchors_propagate_limitations() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    for scenario_index, question_id in ((2, "D03-Q4a"), (3, "D04-Q4a")):
        question = next(item for item in questions if item.question_id == question_id)
        plan = _extended_anchor_plan(plans[question_id], question.scenario_id)
        results, _ = D2Engine(EvidenceStore(scenarios[scenario_index])).execute(question, plan)
        assert results["span"].interval is None
        assert results["hr"].selected_observation_ids == []
        assert results["summary"].facts == []
        assert results["summary"].limitations


def test_invalid_and_wrong_type_dependencies_still_fail_loudly() -> None:
    engine = D2Engine(EvidenceStore(make_scenarios()[0]))
    with pytest.raises(ValueError, match="missing dependency"):
        engine._interval_ref("missing", {})
    with pytest.raises(TypeError, match="not an interval result"):
        engine._interval_ref("wrong", {"wrong": object()})

