from __future__ import annotations

from datetime import timedelta

from src.devdata import make_plans, make_questions, make_scenarios
from src.evidence_store import EvidenceStore
from src.schema import (
    CommonAnswer,
    ComparisonType,
    EvidenceBundle,
    NumericValue,
    ObservationArgs,
    AnswerStatus,
    SourceAvailability,
)
from src.systems.d2.engine import D2Engine
from src.systems.d2.observations import query_observations
from src.systems.d2.verify import verify_answer
from src.systems.d2.workflow import run_d2
from src.model_client import MockClient
from evaluation.checks import automated_checks
from src.devdata import make_gold


def _q(scenario_id: str, suffix: str):
    return next(item for item in make_questions(make_scenarios()) if item.question_id == f"{scenario_id}-{suffix}")


def test_documented_matched_assessment_is_typed_and_eligible() -> None:
    scenarios = make_scenarios()
    scenario = scenarios[0]
    question = _q("D01", "Q2")
    results, _ = D2Engine(EvidenceStore(scenario)).execute(question, make_plans(scenarios)[question.question_id])
    finding = results["comparison"].facts[0]
    assert finding.comparison_type == ComparisonType.MATCHED_ASSESSMENT
    assert finding.assessment_id == "D01-ASSESS-TARGET"
    assert finding.reference_revision == "ref-r1"
    assert finding.value.value == -1.5


def test_low_motion_without_membership_is_passive_not_matched() -> None:
    scenarios = make_scenarios()
    scenario = scenarios[1]
    question = _q("D02", "Q2")
    results, _ = D2Engine(EvidenceStore(scenario)).execute(question, make_plans(scenarios)[question.question_id])
    selection = results["obs"]
    finding = results["comparison"].facts[0]
    assert selection.selected_observation_ids == ["D02-H1"]
    assert finding.comparison_type == ComparisonType.PASSIVE_DESCRIPTIVE
    assert finding.assessment_id is None


def test_incompatible_or_unavailable_reference_does_not_fallback() -> None:
    scenarios = make_scenarios()
    plans = make_plans(scenarios)
    for index, question_id in ((2, "D03-Q2"), (3, "D04-Q2"), (4, "D05-Q2")):
        question = next(item for item in make_questions(scenarios) if item.question_id == question_id)
        results, _ = D2Engine(EvidenceStore(scenarios[index])).execute(question, plans[question_id])
        assert results["obs"].selected_observation_ids == []
        assert results["comparison"].facts == []
        assert results["comparison"].limitations
        assert not any("passive descriptive difference" in item for item in results["comparison"].limitations)


def test_invalidated_reference_is_unavailable_in_current_snapshot() -> None:
    scenario = make_scenarios()[0]
    source = next(item for item in scenario.sources if item.source_id == "D01-S-R")
    changed = source.model_copy(update={"current_access_status": SourceAvailability.INVALIDATED})
    scenario = scenario.model_copy(update={"sources": [changed if item.source_id == changed.source_id else item for item in scenario.sources]})
    store = EvidenceStore(scenario)
    result = query_observations(
        store,
        ObservationArgs(
            metric="heart_rate",
            method="chest_ecg",
            reference_id="D01-R1",
            policy_id="D01-POLICY-NARROW",
            comparison_type=ComparisonType.MATCHED_ASSESSMENT,
            require_eligibility=True,
        ),
        scenario.snapshot.authorized_scope[0].model_copy(update={"end": scenario.snapshot.authorized_scope[0].start + timedelta(seconds=15)}),
    )
    assert result.selected_observation_ids == []
    assert "unavailable" in result.limitations[0]

    clinical_source = next(item for item in scenario.sources if item.source_id == "D01-S-C")
    scenario = scenario.model_copy(update={"sources": [clinical_source.model_copy(update={"current_access_status": SourceAvailability.INVALIDATED}) if item.source_id == clinical_source.source_id else item for item in scenario.sources]})
    from src.schema import ClinicalEventArgs
    from src.systems.d2.events import query_clinical_events
    event_result = query_clinical_events(EvidenceStore(scenario), ClinicalEventArgs(concept="tremor", event_type="symptom_onset", selection="unique_supported_or_clarify"))
    assert event_result.selected_mention_ids == []


def test_verifier_rejects_wrong_numeric_binding_but_accepts_event_fact() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    question = next(item for item in questions if item.question_id == "D01-Q4a")
    answer, trace = run_d2(MockClient(), question, scenarios[0], development_plan=plans[question.question_id])
    bundle = EvidenceBundle.model_validate(trace["bundle"])
    event = next(item for item in answer.findings if item.claim_kind.value == "event")
    accepted, problems = verify_answer(CommonAnswer(status=AnswerStatus.ANSWERED, findings=[event]), bundle)
    assert accepted.findings == [event]
    assert problems == []

    numeric = next(item for item in bundle.computed_facts if isinstance(item.value, NumericValue))
    wrong = numeric.model_copy(update={"value": NumericValue(value=999, unit=numeric.value.unit)})
    rejected, problems = verify_answer(CommonAnswer(status=AnswerStatus.ANSWERED, findings=[wrong]), bundle)
    assert rejected.findings == []
    assert problems


def test_evaluation_precheck_requires_comparison_qualification() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    question = next(item for item in questions if item.question_id == "D01-Q4a")
    answer, _ = run_d2(MockClient(), question, scenarios[0], development_plan=plans[question.question_id])
    gold = next(item for item in make_gold(questions) if item.question_id == question.question_id)
    source_ids = {source.source_id for source in scenarios[0].sources}
    checks = automated_checks(answer, gold, source_ids)
    assert checks["comparison_qualification_errors"] == 0
    assert checks["required_slot_total"] >= 2
    broken = answer.model_copy(update={"findings": [finding.model_copy(update={"comparison_type": None}) if finding.claim_kind.value == "comparison" else finding for finding in answer.findings]})
    assert automated_checks(broken, gold, source_ids)["comparison_qualification_errors"] == 1
