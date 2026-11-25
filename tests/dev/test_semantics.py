from __future__ import annotations

import pytest

from src.devdata import make_scenarios
from src.evidence_store import EvidenceStore
from src.schema import ActionStatus, ClinicalEventArgs, EvidenceClass
from src.systems.d2.events import query_clinical_events
from src.systems.d2.resolver import resolve_evidence


def test_order_and_completed_administration_are_not_interchangeable() -> None:
    scenario = make_scenarios()[0]
    result = query_clinical_events(EvidenceStore(scenario), ClinicalEventArgs(concept="diazepam", action_status=ActionStatus.COMPLETED, evidence_class=EvidenceClass.STRUCTURED_ADMINISTRATION, selection="unique_supported_or_clarify"))
    assert result.selected_mention_ids == ["D01-C4"]
    assert "D01-C2" not in result.selected_mention_ids


def test_source_resolution_rejects_wrong_span() -> None:
    store = EvidenceStore(make_scenarios()[0])
    with pytest.raises(ValueError):
        store.resolve_source("D01-S-C", span="not in synthetic note")
    assert resolve_evidence(store, ["D01-S-C"])[0].source_id == "D01-S-C"

