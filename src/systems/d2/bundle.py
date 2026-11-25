"""Evidence bundle construction from trusted intermediate results."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import (
    AssessmentEvidence,
    ClinicalEvent,
    ComparisonType,
    EventSelectionResult,
    EvidenceBundle,
    Finding,
    InvestigationPlan,
    IntervalResult,
    Limitation,
    ObservationSelectionResult,
    Question,
    ResolvedSource,
    TimeRangeValue,
)


def build_bundle(
    store: EvidenceStore,
    question: Question,
    plan: InvestigationPlan,
    results: dict[str, object],
) -> EvidenceBundle:
    facts: list[Finding] = []
    limitations: list[Limitation] = []
    source_ids: set[str] = set()
    event_selections: list[EventSelectionResult] = []
    clinical_events: list[ClinicalEvent] = []
    assessments: list[AssessmentEvidence] = []
    selected_reference_revisions: dict[str, str] = {}
    selected_assessment_revisions: dict[str, str] = {}
    comparison_types: set[ComparisonType] = set()
    selected_assessment_ids: set[str] = set()
    for result in results.values():
        if isinstance(result, EventSelectionResult):
            event_selections.append(result)
            candidate_ids = result.candidate_mention_ids
            for mention_id in candidate_ids:
                event = store.event(mention_id)
                if mention_id not in {item.mention_id for item in clinical_events}:
                    clinical_events.append(event)
                source_ids.update(event.source_ids)
                if mention_id in result.selected_mention_ids:
                    event_time = event.event_time
                    value = None
                    if event_time is not None:
                        value = TimeRangeValue(lower=event_time.lower, upper=event_time.upper, precision=event_time.precision)
                    facts.append(
                        Finding(
                            claim=f"source-supported {event.concept} clinical event",
                            claim_kind="event",
                            value=value,
                            source_ids=list(event.source_ids),
                            selected_ids=[event.mention_id],
                            occurrence_id=event.occurrence_id,
                            mention_id=event.mention_id,
                            evidence_class=event.evidence_class,
                            action_status=event.action_status,
                            assertion_status=event.assertion,
                            temporal_precision=event.event_time.precision if event.event_time else None,
                        )
                    )
            for limitation in result.limitations:
                if limitation:
                    limitations.append(
                        Limitation(
                            claim=limitation,
                            reason_code="event_selection",
                            source_ids=list(result.source_ids),
                            selected_ids=list(result.selected_mention_ids or result.candidate_mention_ids),
                        )
                    )
        elif isinstance(result, IntervalResult):
            facts.extend(result.facts)
            if result.reference_id and result.reference_revision:
                selected_reference_revisions[result.reference_id] = result.reference_revision
            if result.comparison_type:
                comparison_types.add(result.comparison_type)
            for limitation in result.limitations:
                if limitation:
                    limitation_sources = sorted({source for fact in result.facts for source in fact.source_ids})
                    limitations.append(Limitation(claim=limitation, reason_code="runtime", source_ids=limitation_sources))
            source_ids.update(source for fact in result.facts for source in fact.source_ids)
        elif isinstance(result, ObservationSelectionResult):
            selected_assessment_ids.update(result.selected_assessment_ids)
            if result.reference_id and result.reference_revision:
                selected_reference_revisions[result.reference_id] = result.reference_revision
            if result.comparison_type:
                comparison_types.add(result.comparison_type)
            for observation_id in result.selected_observation_ids:
                observation = store.observation(observation_id)
                source_ids.update(observation.source_ids)
                if observation.assessment_id:
                    selected_assessment_ids.add(observation.assessment_id)
            for limitation in result.limitations:
                if limitation:
                    limitations.append(Limitation(claim=limitation, reason_code="observation_selection", source_ids=[]))
        elif isinstance(result, list) and all(isinstance(item, ResolvedSource) for item in result):
            for source in result:
                source_ids.add(source.source_id)
                if source.availability_status.value in {"unavailable", "invalidated"}:
                    limitations.append(Limitation(claim=f"source {source.source_id} is unavailable or invalidated", reason_code="source_unavailable", source_ids=[source.source_id]))
        else:
            source_ids.update(getattr(result, "source_ids", []))
            for limitation in getattr(result, "limitations", []):
                if limitation:
                    limitations.append(
                        Limitation(
                            claim=limitation,
                            reason_code="event_or_selection",
                            source_ids=list(getattr(result, "source_ids", [])),
                        )
                    )
    revisions = {source_id: store.source(source_id).revision for source_id in source_ids}
    for reference_id in selected_reference_revisions:
        reference = store.reference(reference_id)
        if reference.assessment_id:
            selected_assessment_ids.add(reference.assessment_id)
    for assessment_id in sorted(selected_assessment_ids):
        assessment = store.assessment(assessment_id)
        assessments.append(assessment)
        selected_assessment_revisions[assessment_id] = assessment.revision
        source_ids.update(assessment.source_ids)
    revisions = {source_id: store.source(source_id).revision for source_id in source_ids}
    return EvidenceBundle(
        question_id=question.question_id,
        snapshot_id=store.snapshot_id,
        plan_id=plan.plan_id,
        effective_scope=list(question.authorized_scope),
        computed_facts=facts,
        limitations=limitations,
        source_ids=sorted(source_ids),
        selected_revisions=revisions,
        internal_fact_ids={f"fact-{index + 1}": fact.model_dump(mode="json") for index, fact in enumerate(facts)},
        selected_reference_revisions=selected_reference_revisions,
        selected_assessment_revisions=selected_assessment_revisions,
        assessments=assessments,
        comparison_types=sorted(comparison_types, key=lambda item: item.value),
        event_selections=event_selections,
        clinical_events=clinical_events,
    )

