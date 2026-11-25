from __future__ import annotations

from src.devdata import make_plans, make_questions, make_scenarios
from src.model_client import MockClient
from src.systems.direct import run_direct
from src.systems.program import run_program
from src.systems.sandbox import MockSandbox
from src.systems.d2.workflow import run_d2


def test_mock_a_c_b_workflows_preserve_structured_answers() -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    scenario = scenarios[0]
    question = questions[0]
    client = MockClient()
    answer_a, trace_a = run_direct(client, question, scenario)
    answer_c, trace_c = run_program(client, question, scenario, sandbox=MockSandbox())
    answer_b, trace_b = run_d2(client, question, scenario, development_plan=plans[question.question_id])
    assert answer_a.schema_version == answer_c.schema_version == answer_b.schema_version
    assert trace_a["calls"] == 2
    assert trace_c["calls"] == 2
    assert "bundle" in trace_b

