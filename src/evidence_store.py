"""Immutable, participant-scoped access to one evidence snapshot."""

from __future__ import annotations

from datetime import datetime, timezone

from .schema import (
    ClinicalEvent,
    ContextAnnotation,
    EligibilityRecord,
    HistoricalReference,
    Observation,
    Scenario,
    SourceRecord,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


class EvidenceStore:
    """Read-only view over a validated scenario.

    The store never returns mutable source objects and does not accept caller-selected
    participant or snapshot IDs. Scope is fixed at construction time.
    """

    def __init__(self, scenario: Scenario):
        # Keep only canonical serialized evidence internally. Every public access is
        # a validated copy, so callers cannot mutate the snapshot used by a run.
        self._serialized = scenario.model_dump_json()
        self._scenario_id = scenario.scenario_id
        self._participant_id = scenario.participant_id
        self._snapshot_id = scenario.snapshot.snapshot_id

    @property
    def scenario(self) -> Scenario:
        return Scenario.model_validate_json(self._serialized)

    @property
    def participant_id(self) -> str:
        return self._participant_id

    @property
    def snapshot_id(self) -> str:
        return self._snapshot_id

    @property
    def scope(self):
        return tuple(self.scenario.snapshot.authorized_scope)

    def _in_scope(self, start: datetime, end: datetime) -> bool:
        return any(
            _utc(start) >= _utc(scope.start) and _utc(end) <= _utc(scope.end)
            for scope in self.scope
        )

    def observation(self, observation_id: str) -> Observation:
        for item in self.scenario.observations:
            if item.observation_id == observation_id:
                return item
        raise KeyError(f"unknown observation: {observation_id}")

    def context(self, context_id: str) -> ContextAnnotation:
        for item in self.scenario.contexts:
            if item.context_id == context_id:
                return item
        raise KeyError(f"unknown context: {context_id}")

    def event(self, mention_id: str) -> ClinicalEvent:
        for item in self.scenario.clinical_events:
            if item.mention_id == mention_id:
                return item
        raise KeyError(f"unknown clinical mention: {mention_id}")

    def reference(self, reference_id: str) -> HistoricalReference:
        for item in self.scenario.references:
            if item.reference_id == reference_id:
                return item
        raise KeyError(f"unknown reference: {reference_id}")

    def source(self, source_id: str) -> SourceRecord:
        for item in self.scenario.sources:
            if item.source_id == source_id:
                return item
        raise KeyError(f"unknown source: {source_id}")

    def eligibility(self, observation_id: str, reference_id: str, policy_id: str) -> EligibilityRecord | None:
        for item in self.scenario.eligibility:
            if (
                item.observation_id == observation_id
                and item.reference_id == reference_id
                and item.policy_id == policy_id
            ):
                return item
        return None

    def observations(self) -> tuple[Observation, ...]:
        return tuple(self.scenario.observations)

    def events(self) -> tuple[ClinicalEvent, ...]:
        return tuple(self.scenario.clinical_events)

    def resolve_source(self, source_id: str, span: str | None = None) -> SourceRecord:
        source = self.source(source_id)
        # Resolution is source-specific and never treats a syntactically valid ID as
        # proof that the source supports an unrelated claim.
        if span is not None and source.content is not None and span not in source.content:
            raise ValueError(f"span is not present in source {source_id}")
        return source

    def assert_scope(self, start: datetime, end: datetime) -> None:
        if not self._in_scope(start, end):
            raise PermissionError("requested interval exceeds the authorized evidence scope")

