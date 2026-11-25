"""System B plan, deterministic execution, evidence bundle and composition."""

from __future__ import annotations

from typing import Any

from ...evidence_store import EvidenceStore
from ...model_client import LLMClient, SemanticCallBudget
from ...schema import CommonAnswer, InvestigationPlan, Question, Scenario
from .bundle import build_bundle
from .compose import compose_from_bundle
from .engine import D2Engine
from .verify import verify_answer


def run_d2(
    client: LLMClient,
    question: Question,
    scenario: Scenario,
    *,
    development_plan: InvestigationPlan | None = None,
) -> tuple[CommonAnswer, dict[str, Any]]:
    store = EvidenceStore(scenario)
    budget = SemanticCallBudget()
    plan_payload = {
        "question": question.text,
        "scope": [scope.model_dump(mode="json") for scope in question.authorized_scope],
        "manifest": {"metrics": sorted({row.metric for row in scenario.observations}), "references": [ref.reference_id for ref in scenario.references], "policies": [policy.policy_id for policy in scenario.policies]},
        "tool_schemas": ["query_clinical_events", "query_observations", "analyze_intervals", "resolve_evidence"],
    }
    if development_plan is not None:
        # Only the development correctness harness supplies this plan. It is not part
        # of any evaluated-system prompt path.
        plan = development_plan
        plan_response = None
    else:
        budget.consume()
        plan_response = client.generate(purpose="d2-plan", question=question, payload=plan_payload, schema=InvestigationPlan)
        try:
            plan = InvestigationPlan.model_validate(plan_response.value)
        except Exception as exc:
            budget.consume()
            plan_response = client.generate(purpose="d2-plan-repair", question=question, payload={**plan_payload, "diagnostic": str(exc), "instruction": "repair plan schema/dependencies only"}, schema=InvestigationPlan)
            plan = InvestigationPlan.model_validate(plan_response.value)
    try:
        results, tool_trace = D2Engine(store).execute(question, plan)
    except Exception as exc:
        if plan_response is None or budget.used >= budget.max_calls - 1:
            raise
        budget.consume()
        plan_response = client.generate(purpose="d2-plan-repair", question=question, payload={**plan_payload, "diagnostic": str(exc), "instruction": "repair only the invalid plan binding"}, schema=InvestigationPlan)
        plan = InvestigationPlan.model_validate(plan_response.value)
        results, tool_trace = D2Engine(store).execute(question, plan)
    bundle = build_bundle(store, question, plan, results)
    compose_payload = {"question": question.text, "evidence_bundle": bundle.model_dump(mode="json"), "instruction": "compose only source-grounded common answer fields; retain limitations"}
    if isinstance(client, type(None)):
        answer = compose_from_bundle(bundle)
    else:
        # The local mock is replaced with the deterministic renderer so tests verify
        # the complete pipeline without smuggling gold into a prompt.
        if plan_response is None:
            answer = compose_from_bundle(bundle)
        else:
            budget.consume()
            response = client.generate(purpose="d2-compose", question=question, payload={**compose_payload, "mock_answer": compose_from_bundle(bundle).model_dump(mode="json")}, schema=CommonAnswer)
            answer = CommonAnswer.model_validate(response.value)
    delivered, verification_problems = verify_answer(answer, bundle)
    return delivered, {"plan": plan.model_dump(mode="json"), "tool_trace": tool_trace, "bundle": bundle.model_dump(mode="json"), "verification_problems": verification_problems, "calls": budget.used}

