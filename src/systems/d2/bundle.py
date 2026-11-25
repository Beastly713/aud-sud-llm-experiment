"""Evidence bundle construction from trusted intermediate results."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import (
    ClinicalEvent,
    EventSelectionResult,
    EvidenceBundle,
    Finding,
    InvestigationPlan,
    IntervalResult,
    Limitation,
    Question,
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
                            action_status=event.action_status,
                            assertion_status=event.assertion,
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
            for limitation in result.limitations:
                if limitation:
                    limitations.append(Limitation(claim=limitation, reason_code="runtime", source_ids=[]))
            source_ids.update(source for fact in result.facts for source in fact.source_ids)
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
    return EvidenceBundle(
        question_id=question.question_id,
        snapshot_id=store.snapshot_id,
        plan_id=plan.plan_id,
        effective_scope=list(question.authorized_scope),
        computed_facts=facts,
        limitations=limitations,
        source_ids=sorted(source_ids),
        selected_revisions=revisions,
        internal_fact_ids={f"fact-{index + 1}": fact.claim for index, fact in enumerate(facts)},
        event_selections=event_selections,
        clinical_events=clinical_events,
    )

