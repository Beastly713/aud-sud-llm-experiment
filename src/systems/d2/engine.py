"""Validated executable D2 dependency graph."""

from __future__ import annotations

from datetime import timedelta
from statistics import median
from typing import Iterable

from ...evidence_store import EvidenceStore
from ...schema import (
    Acceptance,
    ComparisonType,
    AnswerStatus,
    ClinicalEventArgs,
    EventSelectionResult,
    CommonAnswer,
    CoverageType,
    DurationValue,
    Finding,
    FractionValue,
    HistoricalReference,
    EligibilityStatus,
    InvestigationPlan,
    Interval,
    IntervalArgs,
    IntervalResult,
    NumericValue,
    ObservationArgs,
    ObservationSelectionResult,
    Question,
    ReferenceStatus,
    ResolvedSource,
    TimeRangeValue,
)
from .events import query_clinical_events
from .intervals import actual_support, clip, group_qualifying_intervals, nominal_coverage, numeric_summary, union_seconds
from .observations import query_observations
from .plan import validate_plan
from .resolver import resolve_evidence


class D2Engine:
    """Execute only allowlisted, typed D2 operations against one snapshot."""

    def __init__(self, store: EvidenceStore):
        self.store = store
        self._question_scope: list[Interval] = []

    def execute(self, question: Question, plan: InvestigationPlan) -> tuple[dict[str, object], list[dict[str, object]]]:
        if question.scenario_id != self.store.scenario.scenario_id:
            raise PermissionError("question is outside the evidence snapshot")
        self._question_scope = list(question.authorized_scope)
        validate_plan(plan, self.store)
        results: dict[str, object] = {}
        trace: list[dict[str, object]] = []
        for step in plan.steps:
            result = self._execute_step(step, results)
            results[step.id] = result
            trace.append({"step_id": step.id, "tool": step.tool, "result_type": getattr(result, "result_type", type(result).__name__)})
        return results, trace

    def _execute_step(self, step: object, results: dict[str, object]) -> object:
        args = step.args
        if isinstance(args, ClinicalEventArgs):
            return query_clinical_events(self.store, args)
        if isinstance(args, ObservationArgs):
            interval = self._interval_ref(args.interval_ref, results)
            if args.interval_ref and interval is None:
                dependency = results.get(args.interval_ref)
                inherited = list(getattr(dependency, "limitations", []))
                inherited.append(f"dependent interval {args.interval_ref} is unavailable")
                return ObservationSelectionResult(
                    selected_observation_ids=[],
                    excluded_observation_ids=[],
                    exclusion_reasons={},
                    scope=None,
                    reference_id=args.reference_id,
                    policy_id=args.policy_id,
                    metric=args.metric,
                    method=args.method,
                    window_policy=args.window_policy,
                    limitations=list(dict.fromkeys(inherited)),
                )
            if interval is None and args.scope_mode == "question_scope":
                # The runner injects the authorized question scope; the model may not
                # invent a participant or interval identifier.
                if len(self._question_scope) != 1:
                    raise ValueError("question scope must be explicit for this observation operation")
                interval = self._question_scope[0]
            return query_observations(self.store, args, interval)
        if isinstance(args, IntervalArgs):
            return self._interval_operation(args, results)
        # ResolveArgs is intentionally checked by attribute names to avoid a large
        # union import in the hot path.
        if step.tool == "resolve_evidence":
            return resolve_evidence(self.store, args.evidence_ids)
        raise TypeError(f"unsupported D2 step: {step.tool}")

    @staticmethod
    def _interval_ref(ref: str | None, results: dict[str, object]) -> Interval | None:
        if not ref:
            return None
        value = results.get(ref)
        if value is None:
            raise ValueError(f"missing dependency result {ref}")
        if not isinstance(value, IntervalResult):
            raise TypeError(f"dependency {ref} is not an interval result")
        interval = getattr(value, "interval", None)
        return interval

    def _observation_rows(self, selection_ref: str, results: dict[str, object]):
        selection = results.get(selection_ref)
        if not isinstance(selection, ObservationSelectionResult):
            raise TypeError(f"{selection_ref} is not an observation selection")
        return [self.store.observation(item) for item in selection.selected_observation_ids], selection

    def _event_time(self, ref: str, results: dict[str, object]):
        result = results.get(ref)
        if result is None:
            raise ValueError(f"missing dependency result {ref}")
        if not isinstance(result, EventSelectionResult):
            raise TypeError(f"dependency {ref} is not a clinical-event selection result")
        return result.time

    @staticmethod
    def _event_limitations(ref: str, results: dict[str, object]) -> list[str]:
        result = results.get(ref)
        if isinstance(result, EventSelectionResult):
            return list(result.limitations)
        return []

    def _interval_operation(self, args: IntervalArgs, results: dict[str, object]) -> IntervalResult:
        if args.operation == "between_event_anchors":
            start = self._event_time(args.start_ref or "", results)
            end = self._event_time(args.end_ref or "", results)
            inherited = self._event_limitations(args.start_ref or "", results) + self._event_limitations(args.end_ref or "", results)
            if start is None or end is None:
                limitations = list(dict.fromkeys(inherited + ["one or more clinical anchors is unavailable; dependent interval cannot be resolved"]))
                return IntervalResult(
                    operation=args.operation,
                    limitations=limitations,
                    dependency_ids=[args.start_ref or "", args.end_ref or ""],
                )
            if start.upper != start.lower or end.upper != end.lower or start.lower >= end.lower:
                limitations = list(dict.fromkeys(inherited + ["event anchors are uncertain or not chronologically ordered"]))
                return IntervalResult(
                    operation=args.operation,
                    limitations=limitations,
                    dependency_ids=[args.start_ref or "", args.end_ref or ""],
                )
            return IntervalResult(
                operation=args.operation,
                interval=Interval(start=start.lower, end=end.lower),
                dependency_ids=[args.start_ref or "", args.end_ref or ""],
            )

        if args.operation == "coverage":
            rows, selection = self._observation_rows(args.observation_ref or "", results)
            if not rows:
                return IntervalResult(
                    operation=args.operation,
                    interval=selection.scope,
                    excluded_ids=selection.excluded_observation_ids,
                    limitations=list(dict.fromkeys(selection.limitations + ["no selected observations support a coverage calculation"])),
                    dependency_ids=[args.observation_ref or ""],
                )
            scope = selection.scope or self.store.scope[0]
            nominal, nominal_ids = nominal_coverage(rows, scope)
            actual, unresolved, actual_ids = actual_support(rows, scope)
            nominal_seconds = union_seconds(nominal)
            actual_seconds = union_seconds(actual)
            findings = [
                Finding(
                    claim="eligible nominal feature-window coverage",
                    claim_kind="coverage",
                    value=FractionValue(
                        numerator=nominal_seconds,
                        denominator=scope.seconds,
                        fraction=nominal_seconds / scope.seconds,
                        coverage_type=CoverageType.NOMINAL_FEATURE_WINDOW,
                    ),
                    interval=scope,
                    source_ids=sorted({source for row in rows for source in row.source_ids}),
                    selected_ids=nominal_ids,
                    denominator_seconds=scope.seconds,
                    coverage_type=CoverageType.NOMINAL_FEATURE_WINDOW,
                ),
                Finding(
                    claim="known actual measurement support",
                    claim_kind="coverage",
                    value=FractionValue(
                        numerator=actual_seconds,
                        denominator=scope.seconds,
                        fraction=actual_seconds / scope.seconds,
                        coverage_type=(CoverageType.KNOWN_LOWER_BOUND if unresolved else CoverageType.ACTUAL_SUPPORT),
                    ),
                    interval=scope,
                    source_ids=sorted({source for row in rows for source in row.source_ids}),
                    selected_ids=actual_ids,
                    denominator_seconds=scope.seconds,
                    coverage_type=CoverageType.KNOWN_LOWER_BOUND if unresolved else CoverageType.ACTUAL_SUPPORT,
                ),
            ]
            limitations = list(selection.limitations)
            if unresolved:
                limitations.append("fraction-only or unknown support prevents an exact total")
            return IntervalResult(
                operation=args.operation,
                interval=scope,
                selected_ids=[row.observation_id for row in rows],
                excluded_ids=selection.excluded_observation_ids,
                facts=findings,
                limitations=list(dict.fromkeys(limitations)),
                dependency_ids=[args.observation_ref or ""],
            )

        if args.operation == "summary":
            rows, selection = self._observation_rows(args.observation_ref or "", results)
            if selection.window_policy == "clip_for_coverage":
                return IntervalResult(
                    operation=args.operation,
                    limitations=["feature-window coverage selection cannot be reused for a value summary; select fully contained windows"],
                    dependency_ids=[args.observation_ref or ""],
                )
            value = numeric_summary(rows, args.statistic)
            if value is None:
                return IntervalResult(
                    operation=args.operation,
                    selected_ids=[],
                    limitations=list(dict.fromkeys(selection.limitations + ["no numeric observations support the requested summary"])),
                    dependency_ids=[args.observation_ref or ""],
                )
            first = rows[0]
            finding = Finding(
                claim=f"{args.statistic} of accepted {first.metric}",
                claim_kind="observation",
                metric=first.metric,
                method=first.method,
                requested_statistic=args.statistic,
                value=NumericValue(value=value, unit=first.value.units or ""),
                interval=selection.scope,
                source_ids=sorted({source for row in rows for source in row.source_ids}),
                selected_ids=[row.observation_id for row in rows],
            )
            return IntervalResult(
                operation=args.operation,
                interval=selection.scope,
                selected_ids=[row.observation_id for row in rows],
                facts=[finding],
                limitations=selection.limitations,
                dependency_ids=[args.observation_ref or ""],
            )

        if args.operation == "compare_to_named_reference":
            rows, selection = self._observation_rows(args.target_ref or "", results)
            if selection.window_policy == "clip_for_coverage":
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=args.comparison_type or selection.comparison_type,
                    limitations=["feature-window coverage selection cannot be reused for a named numeric comparison"],
                    dependency_ids=[args.target_ref or ""],
                )
            comparison_type = args.comparison_type or selection.comparison_type
            if comparison_type is None:
                raise ValueError("named comparison requires an explicit comparison type")
            if selection.comparison_type is not None and selection.comparison_type != comparison_type:
                raise ValueError("comparison type does not match the observation selection")
            reference_id = args.reference_id or selection.reference_id
            if not reference_id:
                raise ValueError("named comparison requires an explicit reference")
            reference = self.store.reference(reference_id)
            policy_id = args.policy_id or selection.policy_id
            if not policy_id:
                raise ValueError("named comparison requires an explicit policy")
            policy = next((item for item in self.store.scenario.policies if item.policy_id == policy_id), None)
            if policy is None or reference_id not in policy.reference_ids or reference.policy_id != policy_id:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INDETERMINATE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=["reference and policy binding is incompatible"],
                    dependency_ids=[args.target_ref or ""],
                )
            if args.reference_revision and args.reference_revision != reference.revision:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INDETERMINATE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=[f"requested reference revision {args.reference_revision} is not available in this snapshot"],
                    dependency_ids=[args.target_ref or ""],
                )
            if not rows:
                limitations = list(selection.limitations)
                if reference.status == ReferenceStatus.UNAVAILABLE or reference.center is None:
                    limitations.append(f"reference {reference_id} is unavailable")
                else:
                    limitations.append(f"no selected observations support comparison to {reference_id}")
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=selection.eligibility_status,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    limitations=list(dict.fromkeys(limitations)),
                    dependency_ids=[args.target_ref or ""],
                )
            selected_metric = first_metric(rows) or selection.metric or ""
            selected_method = first_method(rows) or selection.method or ""
            selected_site = next((row.site for row in rows if row.site), None)
            selected_configuration = next((row.configuration for row in rows if row.configuration), None)
            if reference.metric != selected_metric or reference.method != selected_method or (reference.site and reference.site != selected_site) or (reference.configuration and reference.configuration != selected_configuration):
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INELIGIBLE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=[f"reference {reference_id} is incompatible with the selected metric or method"],
                    dependency_ids=[args.target_ref or ""],
                )
            if reference.units and any(row.value.units != reference.units for row in rows):
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INELIGIBLE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=[f"reference {reference_id} has incompatible units"],
                    dependency_ids=[args.target_ref or ""],
                )
            if reference.status == ReferenceStatus.UNAVAILABLE or reference.center is None:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INDETERMINATE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=[f"reference {reference_id} is unavailable"],
                    dependency_ids=[args.target_ref or ""],
                )
            if comparison_type == ComparisonType.MATCHED_ASSESSMENT and reference.status != ReferenceStatus.SUPPORTED_ASSESSMENT:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=EligibilityStatus.INELIGIBLE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=[f"reference {reference_id} is not documented as a supported assessment reference"],
                    dependency_ids=[args.target_ref or ""],
                )
            if comparison_type == ComparisonType.MATCHED_ASSESSMENT and selection.eligibility_status != EligibilityStatus.ELIGIBLE:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=selection.eligibility_status or EligibilityStatus.INDETERMINATE,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[row.observation_id for row in rows],
                    limitations=["required documented matched-assessment eligibility is not established"],
                    dependency_ids=[args.target_ref or ""],
                )
            target = numeric_summary(rows, "median")
            if target is None:
                return IntervalResult(
                    operation=args.operation,
                    comparison_type=comparison_type,
                    eligibility_status=selection.eligibility_status,
                    reference_id=reference_id,
                    policy_id=policy_id,
                    reference_revision=reference.revision,
                    selected_ids=[],
                    limitations=["no eligible numeric observations support the comparison"],
                    dependency_ids=[args.target_ref or ""],
                )
            first = rows[0]
            value = target - reference.center
            assessment_ids = {row.assessment_id for row in rows if row.assessment_id}
            finding = Finding(
                claim=(f"median {first.metric} difference from matched assessment reference {reference_id}"
                       if comparison_type == ComparisonType.MATCHED_ASSESSMENT
                       else f"median {first.metric} passive descriptive difference from assessment reference {reference_id}"),
                claim_kind="comparison",
                metric=first.metric,
                method=first.method,
                requested_statistic="median_difference",
                value=NumericValue(value=value, unit=first.value.units or ""),
                interval=selection.scope,
                reference_id=reference_id,
                policy_id=policy_id,
                source_ids=sorted({source for row in rows for source in row.source_ids} | set(reference.source_ids)),
                selected_ids=[row.observation_id for row in rows],
                comparison_type=comparison_type,
                eligibility_status=selection.eligibility_status,
                assessment_id=next(iter(assessment_ids)) if len(assessment_ids) == 1 else None,
                reference_revision=reference.revision,
            )
            return IntervalResult(
                operation=args.operation,
                interval=selection.scope,
                selected_ids=[row.observation_id for row in rows],
                facts=[finding],
                limitations=list(dict.fromkeys(selection.limitations + ([f"reference status is {reference.status.value}; descriptive only"] if reference.status == ReferenceStatus.PROVISIONAL else []))),
                dependency_ids=[args.target_ref or ""],
                comparison_type=comparison_type,
                eligibility_status=selection.eligibility_status,
                reference_id=reference_id,
                policy_id=policy_id,
                reference_revision=reference.revision,
            )

        if args.operation == "episodes":
            rows, selection = self._observation_rows(args.observation_ref or "", results)
            if not args.episode_rule_id:
                raise ValueError("episode analysis requires an explicit configured rule")
            rule = next((item for item in self.store.scenario.episode_rules if item.rule_id == args.episode_rule_id), None)
            if rule is None:
                raise ValueError(f"unknown episode rule {args.episode_rule_id}")
            if not rows:
                return IntervalResult(
                    operation=args.operation,
                    limitations=list(dict.fromkeys(selection.limitations + ["no selected observations support episode analysis"])),
                    dependency_ids=[args.observation_ref or ""],
                )
            groups = group_qualifying_intervals(
                rows,
                rule.threshold_operator,
                rule.threshold,
                rule.minimum_grouping_seconds,
                rule.maximum_gap_seconds,
            )
            facts: list[Finding] = []
            for span, group, qualifying_seconds in groups:
                actual, unresolved, _ = actual_support(group, span)
                facts.extend(
                    [
                        Finding(
                            claim=f"episode grouping span under {rule.rule_id}",
                            claim_kind="episode",
                            value=TimeRangeValue(lower=span.start, upper=span.end, precision="interval"),
                            interval=span,
                            selected_ids=[row.observation_id for row in group],
                            episode_rule_id=rule.rule_id,
                        ),
                        Finding(
                            claim=f"qualifying feature-window coverage under {rule.rule_id}",
                            claim_kind="coverage",
                            value=DurationValue(seconds=qualifying_seconds),
                            interval=span,
                            selected_ids=[row.observation_id for row in group],
                            episode_rule_id=rule.rule_id,
                            coverage_type=CoverageType.NOMINAL_FEATURE_WINDOW,
                        ),
                        Finding(
                            claim=f"actual support for grouped qualifying records under {rule.rule_id}",
                            claim_kind="coverage",
                            value=DurationValue(seconds=union_seconds(actual)),
                            interval=span,
                            selected_ids=[row.observation_id for row in group],
                            episode_rule_id=rule.rule_id,
                            coverage_type=CoverageType.KNOWN_LOWER_BOUND if unresolved else CoverageType.ACTUAL_SUPPORT,
                        ),
                    ]
                )
            return IntervalResult(
                operation=args.operation,
                interval=selection.scope,
                selected_ids=[row.observation_id for row in rows],
                facts=facts,
                limitations=list(dict.fromkeys(selection.limitations + ["grouping span is not continuous measured elevation"])),
                dependency_ids=[args.observation_ref or ""],
            )

        raise ValueError(f"unsupported interval operation: {args.operation}")


def first_metric(rows: list[object]) -> str:
    if not rows:
        return ""
    return rows[0].metric


def first_method(rows: list[object]) -> str:
    if not rows:
        return ""
    return rows[0].method

