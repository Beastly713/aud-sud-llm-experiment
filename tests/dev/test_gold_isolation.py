from __future__ import annotations

from src.devdata import make_gold
from src.model_client import MockClient


def test_provisional_gold_is_not_reviewed() -> None:
    assert all(record.review_resolved is False for record in make_gold())


def test_mock_client_payload_does_not_need_gold() -> None:
    assert "gold" not in MockClient().__class__.__module__

