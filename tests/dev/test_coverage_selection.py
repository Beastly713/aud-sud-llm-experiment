from __future__ import annotations

from datetime import timedelta

from src.devdata import make_scenarios
from src.evidence_store import EvidenceStore
from src.schema import ObservationArgs
from src.systems.d2.observations import query_observations
from src.systems.d2.intervals import nominal_coverage
from src.schema import IntervalArgs
from src.systems.d2.engine import D2Engine


def test_coverage_selection_includes_partial_windows_but_summary_selection_does_not() -> None:
    scenario = make_scenarios()[0]
    store = EvidenceStore(scenario)
    base = scenario.snapshot.authorized_scope[0].start
    scope = scenario.snapshot.authorized_scope[0].model_copy(update={"start": base + timedelta(seconds=8), "end": base + timedelta(seconds=12)})
    coverage = query_observations(store, ObservationArgs(metric="heart_rate", method="chest_ecg", window_policy="clip_for_coverage"), scope)
    summary = query_observations(store, ObservationArgs(metric="heart_rate", method="chest_ecg"), scope)
    assert "D01-H1" in coverage.selected_observation_ids
    assert "D01-H2" in coverage.selected_observation_ids
    assert summary.selected_observation_ids == []
    rows = [store.observation(item) for item in coverage.selected_observation_ids]
    union, _ = nominal_coverage(rows, scope)
    assert sum(item.seconds for item in union) == 4


def test_coverage_selection_cannot_be_reused_for_summary() -> None:
    scenario = make_scenarios()[0]
    store = EvidenceStore(scenario)
    base = scenario.snapshot.authorized_scope[0].start
    scope = scenario.snapshot.authorized_scope[0].model_copy(update={"start": base + timedelta(seconds=8), "end": base + timedelta(seconds=12)})
    selection = query_observations(store, ObservationArgs(metric="heart_rate", method="chest_ecg", window_policy="clip_for_coverage"), scope)
    result = D2Engine(store)._interval_operation(IntervalArgs(operation="summary", observation_ref="obs"), {"obs": selection})
    assert result.facts == []
    assert "coverage selection" in result.limitations[0]
