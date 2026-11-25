from __future__ import annotations

from evaluation.aggregate import scenario_bootstrap


def test_reproducibility_rows_do_not_enter_primary_bootstrap() -> None:
    rows = [
        {"cohort": "primary", "scenario_id": "D01", "arm": "B", "sgis": 1},
        {"cohort": "primary", "scenario_id": "D01", "arm": "C", "sgis": 0},
        {"cohort": "reproducibility", "scenario_id": "D01", "arm": "B", "sgis": 0},
        {"cohort": "reproducibility", "scenario_id": "D01", "arm": "C", "sgis": 0},
    ]
    result = scenario_bootstrap(rows, "B", "C", resamples=10)
    assert result["scenario_count"] == 1
    assert result["delta"] == 1.0

