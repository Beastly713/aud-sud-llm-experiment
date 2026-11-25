from __future__ import annotations

from src.devdata import make_plans, make_questions, make_scenarios
from src.evidence_store import EvidenceStore
from src.systems.d2.engine import D2Engine


def test_all_25_manual_plans_execute() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    by_scenario = {scenario.scenario_id: scenario for scenario in scenarios}
    assert len(questions) == 25
    for question in questions:
        results, trace = D2Engine(EvidenceStore(by_scenario[question.scenario_id])).execute(question, plans[question.question_id])
        assert trace
        assert len(results) == len(plans[question.question_id].steps)

