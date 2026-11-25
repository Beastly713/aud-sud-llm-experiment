"""System B plan, deterministic execution, evidence bundle and composition."""

from __future__ import annotations

from typing import Any

from ...evidence_store import EvidenceStore
from ...model_client import LLMClient, SemanticCallBudget
from ...prompt_loader import d2_tool_schemas, load_prompt_bundle
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
    responses = []
    common = load_prompt_bundle().common_payload(question, scenario)
    plan_payload = {
        **common,
        "manifest": {"metrics": sorted({row.metric for row in scenario.observations}), "methods": sorted({row.method for row in scenario.observations}), "references": [ref.reference_id for ref in scenario.references], "policies": [policy.policy_id for policy in scenario.policies], "source_categories": sorted({source.source_type for source in scenario.sources})},
        "tool_schemas": d2_tool_schemas(),
        "system_instruction": "System B: compile a bounded typed dependency graph using only the supplied tool families and authorized scope.",
    }
    if development_plan is not None:
        # Only the development correctness harness supplies this plan. It is not part
        # of any evaluated-system prompt path.
        plan = development_plan
        plan_response = None
    else:
        budget.consume()
        plan_response = client.generate(purpose="d2-plan", question=question, payload=plan_payload, schema=InvestigationPlan)
        responses.append(plan_response)
        try:
            plan = InvestigationPlan.model_validate(plan_response.value)
        except Exception as exc:
            budget.consume()
            plan_response = client.generate(purpose="d2-plan-repair", question=question, payload={**plan_payload, "diagnostic": str(exc), "instruction": "repair plan schema/dependencies only"}, schema=InvestigationPlan)
            responses.append(plan_response)
            plan = InvestigationPlan.model_validate(plan_response.value)
    try:
        results, tool_trace = D2Engine(store).execute(question, plan)
    except Exception as exc:
        if plan_response is None or budget.used >= budget.max_calls - 1:
            raise
        budget.consume()
        plan_response = client.generate(purpose="d2-plan-repair", question=question, payload={**plan_payload, "diagnostic": str(exc), "instruction": "repair only the invalid plan binding"}, schema=InvestigationPlan)
        responses.append(plan_response)
        plan = InvestigationPlan.model_validate(plan_response.value)
        results, tool_trace = D2Engine(store).execute(question, plan)
    bundle = build_bundle(store, question, plan, results)
    compose_payload = {**common, "evidence_bundle": bundle.model_dump(mode="json"), "system_instruction": "System B composition: use only computed facts and source-supported clinical evidence; retain limitations and do not add uncomputed numbers."}
    # The local mock is replaced with the deterministic renderer so tests verify
    # the complete pipeline without smuggling gold into a live prompt.
    if plan_response is None:
        answer = compose_from_bundle(bundle)
        raw_answer = answer.model_dump(mode="json")
    else:
        budget.consume()
        composition_payload = compose_payload
        if client.is_mock:
            composition_payload = {**compose_payload, "mock_answer": compose_from_bundle(bundle).model_dump(mode="json")}
        response = client.generate(purpose="d2-compose", question=question, payload=composition_payload, schema=CommonAnswer)
        responses.append(response)
        answer = CommonAnswer.model_validate(response.value)
        raw_answer = answer.model_dump(mode="json")
    delivered, verification_problems = verify_answer(answer, bundle)
    return delivered, {"plan": plan.model_dump(mode="json"), "tool_trace": tool_trace, "bundle": bundle.model_dump(mode="json"), "verification_problems": verification_problems, "raw_answer": raw_answer, "delivered_answer": delivered.model_dump(mode="json"), "calls": budget.used, "model_calls": [item.model_dump(mode="json") for item in responses]}

