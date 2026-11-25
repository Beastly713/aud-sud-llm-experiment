"""Measurement-quality, context and named-reference-aware retrieval."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import (
    AssessmentAdherence,
    AssessmentAdequacy,
    AssessmentMembership,
    Acceptance,
    ComparisonType,
    EligibilityStatus,
    MovementStratum,
    Observation,
    ObservationArgs,
    ObservationSelectionResult,
    ReferenceStatus,
    Interval,
)
from .intervals import nominal_coverage


def _scope_for_ref(store: EvidenceStore, result: object | None) -> Interval | None:
    if result is None:
        return None
    return getattr(result, "interval", None)


def query_observations(
    store: EvidenceStore,
    args: ObservationArgs,
    interval: Interval | None = None,
) -> ObservationSelectionResult:
    selected: list[Observation] = []
    excluded: list[str] = []
    reasons: dict[str, str] = {}
    reference = None
    policy = None
    comparison_type = args.comparison_type
    if comparison_type is not None:
        if not args.reference_id or not args.policy_id:
            raise ValueError("comparison selection requires an explicit reference, policy and comparison type")
        reference = store.reference(args.reference_id)
        policy = next((item for item in store.scenario.policies if item.policy_id == args.policy_id), None)
        if policy is None:
            raise ValueError(f"unknown policy {args.policy_id}")
        if args.reference_id not in policy.reference_ids:
            raise ValueError("reference is not authorized by the selected policy")
        if comparison_type not in policy.allowed_comparison_types:
            raise ValueError("comparison type is not authorized by the selected policy")
        if reference.policy_id != args.policy_id:
            raise ValueError("reference and policy binding mismatch")
        if reference.status == ReferenceStatus.UNAVAILABLE or not store.reference_is_currently_usable(args.reference_id):
            return ObservationSelectionResult(
                selected_observation_ids=[],
                excluded_observation_ids=[],
                exclusion_reasons={},
                scope=interval,
                reference_id=args.reference_id,
                policy_id=args.policy_id,
                metric=args.metric,
                method=args.method,
                comparison_type=comparison_type,
                eligibility_status=EligibilityStatus.INDETERMINATE,
                reference_revision=reference.revision,
                limitations=[f"named reference {args.reference_id} is unavailable in this snapshot; no comparison value is available"],
            )
        if comparison_type == ComparisonType.MATCHED_ASSESSMENT and reference.status != ReferenceStatus.SUPPORTED_ASSESSMENT:
            return ObservationSelectionResult(
                selected_observation_ids=[],
                excluded_observation_ids=[],
                exclusion_reasons={},
                scope=interval,
                reference_id=args.reference_id,
                policy_id=args.policy_id,
                metric=args.metric,
                method=args.method,
                comparison_type=comparison_type,
                eligibility_status=EligibilityStatus.INELIGIBLE,
                reference_revision=reference.revision,
                limitations=[f"reference {args.reference_id} is not documented as a supported assessment reference"],
            )
    if interval:
        store.assert_scope(interval.start, interval.end)
    for observation in store.observations():
        if observation.metric != args.metric or observation.method != args.method:
            continue
        if interval:
            fully_contained = observation.nominal.start >= interval.start and observation.nominal.end <= interval.end
            overlaps = observation.nominal.start < interval.end and observation.nominal.end > interval.start
            if args.window_policy == "fully_contained" and not fully_contained:
                continue
            if args.window_policy == "clip_for_coverage" and not overlaps:
                continue
        if args.quality and observation.acceptance != args.quality:
            excluded.append(observation.observation_id)
            reasons[observation.observation_id] = "quality filter"
            continue
        if observation.source_ids and not any(store.source_is_currently_usable(source_id) for source_id in observation.source_ids):
            excluded.append(observation.observation_id)
            reasons[observation.observation_id] = "all supporting sources are unavailable or invalidated in this snapshot"
            continue
        if comparison_type is not None:
            if reference is None or observation.value.value is None:
                excluded.append(observation.observation_id)
                reasons[observation.observation_id] = "comparison requires an accepted numeric observation"
                continue
            if reference.metric != observation.metric or reference.method != observation.method or reference.site != observation.site or (reference.configuration and reference.configuration != observation.configuration):
                excluded.append(observation.observation_id)
                reasons[observation.observation_id] = "reference metric, method, site or configuration is incompatible"
                continue
            if reference.units and observation.value.units != reference.units:
                excluded.append(observation.observation_id)
                reasons[observation.observation_id] = "reference units are incompatible"
                continue
        contexts = [store.context(context_id) for context_id in observation.context_ids]
        if args.movement and not any(context.movement == args.movement for context in contexts):
            excluded.append(observation.observation_id)
            reasons[observation.observation_id] = "context movement filter"
            continue
        if args.require_eligibility or comparison_type == ComparisonType.MATCHED_ASSESSMENT:
            if not args.reference_id or not args.policy_id:
                raise ValueError("eligibility query requires explicit reference and policy")
            eligibility = store.eligibility(observation.observation_id, args.reference_id, args.policy_id, comparison_type)
            if eligibility is None or eligibility.status.value != "eligible":
                excluded.append(observation.observation_id)
                reasons[observation.observation_id] = (
                    "missing or non-eligible named-reference result"
                    if eligibility is None
                    else f"reference eligibility is {eligibility.status.value}: {', '.join(eligibility.reasons)}"
                )
                continue
            if comparison_type == ComparisonType.MATCHED_ASSESSMENT:
                if not reference or not reference.assessment_id or not observation.assessment_id:
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "documented assessment membership is required for a matched comparison"
                    continue
                assessment = store.assessment(observation.assessment_id)
                reference_assessment = store.assessment(reference.assessment_id)
                if args.target_assessment_id and observation.assessment_id != args.target_assessment_id:
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "observation is outside the bound target assessment"
                    continue
                if not store.assessment_is_currently_usable(observation.assessment_id) or not store.assessment_is_currently_usable(reference.assessment_id):
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "assessment source is unavailable or invalidated in this snapshot"
                    continue
                if assessment.membership != AssessmentMembership.ESTABLISHED:
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "documented target assessment membership is not established"
                    continue
                if assessment.adherence != AssessmentAdherence.SUPPORTED or assessment.adequacy != AssessmentAdequacy.ADEQUATE:
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "assessment adherence or adequacy is not sufficient"
                    continue
                if assessment.protocol_id != reference_assessment.protocol_id or assessment.condition != reference_assessment.condition:
                    excluded.append(observation.observation_id)
                    reasons[observation.observation_id] = "target and reference assessment procedure or condition is incompatible"
                    continue
        selected.append(observation)
    limitations: list[str] = []
    if not selected:
        limitations.append("no accepted observations matched the explicit selection")
    elif comparison_type == ComparisonType.PASSIVE_DESCRIPTIVE:
        limitations.append("selected observations support a passive descriptive difference, not a matched-assessment comparison")
    elif interval:
        covered, _ = nominal_coverage(selected, interval)
        if sum(item.seconds for item in covered) < interval.seconds:
            limitations.append("selected feature windows are sparse within the requested interval; uncovered time is unknown")
    return ObservationSelectionResult(
        selected_observation_ids=[item.observation_id for item in selected],
        excluded_observation_ids=excluded,
        exclusion_reasons=reasons,
        scope=interval,
        reference_id=args.reference_id,
        policy_id=args.policy_id,
        metric=args.metric,
        method=args.method,
        window_policy=args.window_policy,
        comparison_type=comparison_type,
        eligibility_status=EligibilityStatus.ELIGIBLE if selected and comparison_type is not None else None,
        selected_assessment_ids=sorted({item.assessment_id for item in selected if item.assessment_id}),
        reference_revision=reference.revision if reference else None,
        limitations=limitations,
    )

