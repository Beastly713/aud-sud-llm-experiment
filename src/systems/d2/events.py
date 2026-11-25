"""F1-admitted clinical event lookup and anchor resolution."""

from __future__ import annotations

from datetime import datetime

from ...evidence_store import EvidenceStore
from ...schema import (
    ActionStatus,
    AnswerStatus,
    AssertionStatus,
    ClinicalEvent,
    ClinicalEventArgs,
    EventSelectionResult,
    EvidenceClass,
    ReviewState,
    TemporalPrecision,
    TimeBounds,
)


def admitted(event: ClinicalEvent) -> bool:
    return (
        event.experiencer.value == "patient"
        and event.semantic_support in (ReviewState.SUPPORTED, ReviewState.REVIEWED)
        and event.source_review != ReviewState.UNSUPPORTED
        and event.structural_review != ReviewState.UNSUPPORTED
        and event.assertion in (AssertionStatus.AFFIRMED, AssertionStatus.HISTORICAL)
        and event.event_time is not None
    )


def query_clinical_events(store: EvidenceStore, args: ClinicalEventArgs) -> EventSelectionResult:
    candidates = []
    limitations: list[str] = []
    for event in store.events():
        if args.concept and args.concept.lower() not in event.concept.lower():
            continue
        if args.event_type and args.event_type != event.event_type:
            continue
        if args.action_status and event.action_status != args.action_status:
            continue
        if args.assertion and event.assertion != args.assertion:
            continue
        if args.evidence_class and event.evidence_class != args.evidence_class:
            continue
        if event.source_ids and not any(store.source_is_currently_usable(source_id) for source_id in event.source_ids):
            continue
        if admitted(event):
            candidates.append(event)
    candidates.sort(key=lambda item: (item.event_time.lower if item.event_time else item.documented_at, item.mention_id))

    selected: list[ClinicalEvent] = []
    status = AnswerStatus.ANSWERED
    if args.selection == "unique_supported_or_clarify":
        if len(candidates) == 1:
            selected = candidates
        elif len(candidates) > 1:
            status = AnswerStatus.CLARIFY
            limitations.append("multiple source-supported event candidates require explicit selection")
        else:
            status = AnswerStatus.INSUFFICIENT
            limitations.append("no source-supported event matched the requested anchor")
    elif args.selection == "first_supported":
        selected = candidates[:1]
        if not selected:
            status = AnswerStatus.INSUFFICIENT
            limitations.append("no source-supported event matched the requested anchor")
    elif args.selection == "last_supported":
        selected = candidates[-1:]
        if not selected:
            status = AnswerStatus.INSUFFICIENT
            limitations.append("no source-supported event matched the requested anchor")
    else:
        selected = candidates
        if not selected:
            status = AnswerStatus.INSUFFICIENT
            limitations.append("no source-supported event matched the requested filter")

    selected_ids = [item.mention_id for item in selected]
    occurrence_ids = [item.occurrence_id for item in selected if item.occurrence_id]
    times = [item.event_time for item in selected if item.event_time]
    exact_time = times[0] if len(times) == 1 else None
    if selected and any(item.event_time and item.event_time.precision != TemporalPrecision.INSTANT for item in selected):
        limitations.append("anchor time is bounded or approximate; exact interval arithmetic is not authorized")
    return EventSelectionResult(
        selected_mention_ids=selected_ids,
        candidate_mention_ids=[item.mention_id for item in candidates],
        occurrence_ids=occurrence_ids,
        time=exact_time,
        status=status,
        limitations=limitations,
        source_ids=sorted({source_id for item in candidates for source_id in item.source_ids}),
    )

