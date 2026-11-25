"""Structural and semantic validation for executable D2 plans."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import InvestigationPlan, IntervalArgs, ObservationArgs


def validate_plan(plan: InvestigationPlan, store: EvidenceStore) -> None:
    if plan.participant_scope != "authorized_context_only":
        raise PermissionError("D2 plans may use only the runtime-injected authorized participant scope")
    metrics = {(row.metric, row.method) for row in store.observations()}
    references = {item.reference_id for item in store.scenario.references}
    policies = {item.policy_id for item in store.scenario.policies}
    rules = {item.rule_id for item in store.scenario.episode_rules}
    for step in plan.steps:
        args = step.args
        if isinstance(args, ObservationArgs):
            if (args.metric, args.method) not in metrics:
                raise ValueError(f"unsupported metric/method: {args.metric}/{args.method}")
            if args.require_eligibility and (not args.reference_id or not args.policy_id):
                raise ValueError("eligibility retrieval requires explicit named reference and policy")
            if args.reference_id and args.reference_id not in references:
                raise ValueError(f"unknown reference {args.reference_id}")
            if args.policy_id and args.policy_id not in policies:
                raise ValueError(f"unknown policy {args.policy_id}")
        if isinstance(args, IntervalArgs):
            if args.reference_id and args.reference_id not in references:
                raise ValueError(f"unknown reference {args.reference_id}")
            if args.policy_id and args.policy_id not in policies:
                raise ValueError(f"unknown policy {args.policy_id}")
            if args.episode_rule_id and args.episode_rule_id not in rules:
                raise ValueError(f"unknown episode rule {args.episode_rule_id}")
            if args.operation == "compare_to_named_reference" and not args.reference_id:
                raise ValueError("named comparison needs an explicit reference binding")

