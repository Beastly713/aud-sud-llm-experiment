"""Structural and semantic validation for executable D2 plans."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import ComparisonType, InvestigationPlan, IntervalArgs, ObservationArgs


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
            if args.comparison_type is not None and (not args.reference_id or not args.policy_id):
                raise ValueError("comparison type requires explicit reference and policy bindings")
            if args.comparison_type is not None:
                policy = next(item for item in store.scenario.policies if item.policy_id == args.policy_id)
                reference = store.reference(args.reference_id or "")
                if args.comparison_type not in policy.allowed_comparison_types:
                    raise ValueError("comparison type is not allowed by the selected policy")
                if args.reference_id not in policy.reference_ids or reference.policy_id != args.policy_id:
                    raise ValueError("reference/policy binding is inconsistent")
        if isinstance(args, IntervalArgs):
            if args.reference_id and args.reference_id not in references:
                raise ValueError(f"unknown reference {args.reference_id}")
            if args.policy_id and args.policy_id not in policies:
                raise ValueError(f"unknown policy {args.policy_id}")
            if args.episode_rule_id and args.episode_rule_id not in rules:
                raise ValueError(f"unknown episode rule {args.episode_rule_id}")
            if args.operation == "compare_to_named_reference":
                if not args.reference_id or not args.policy_id or args.comparison_type is None:
                    raise ValueError("named comparison needs explicit reference, policy and comparison-type bindings")
                policy = next(item for item in store.scenario.policies if item.policy_id == args.policy_id)
                reference = store.reference(args.reference_id)
                if args.comparison_type not in policy.allowed_comparison_types:
                    raise ValueError("comparison type is not allowed by the selected policy")
                if args.reference_id not in policy.reference_ids or reference.policy_id != args.policy_id:
                    raise ValueError("reference/policy binding is inconsistent")
                if args.reference_revision and args.reference_revision != reference.revision:
                    raise ValueError("requested reference revision is not the bound reference revision")

