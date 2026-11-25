"""Measurement-quality, context and named-reference-aware retrieval."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import (
    Acceptance,
    MovementStratum,
    Observation,
    ObservationArgs,
    ObservationSelectionResult,
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
        contexts = [store.context(context_id) for context_id in observation.context_ids]
        if args.movement and not any(context.movement == args.movement for context in contexts):
            excluded.append(observation.observation_id)
            reasons[observation.observation_id] = "context movement filter"
            continue
        if args.require_eligibility:
            if not args.reference_id or not args.policy_id:
                raise ValueError("eligibility query requires explicit reference and policy")
            eligibility = store.eligibility(observation.observation_id, args.reference_id, args.policy_id)
            if eligibility is None or eligibility.status.value != "eligible":
                excluded.append(observation.observation_id)
                reasons[observation.observation_id] = (
                    "missing or non-eligible named-reference result"
                    if eligibility is None
                    else f"reference eligibility is {eligibility.status.value}: {', '.join(eligibility.reasons)}"
                )
                continue
        selected.append(observation)
    limitations: list[str] = []
    if not selected:
        limitations.append("no accepted observations matched the explicit selection")
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
        limitations=limitations,
    )

