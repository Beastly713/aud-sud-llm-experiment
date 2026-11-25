from __future__ import annotations

from datetime import timedelta

from evaluation.gold_oracle import oracle_coverage, oracle_episodes, oracle_summary
from src.devdata import make_scenarios


def test_reference_oracle_distinguishes_nominal_and_actual_support() -> None:
    scenario = make_scenarios()[0]
    scope = scenario.snapshot.authorized_scope[0].model_copy(update={"end": scenario.snapshot.authorized_scope[0].start + timedelta(seconds=30)})
    rows = [row for row in scenario.observations if row.observation_id.endswith(("-H1", "-H2", "-H3", "-H4"))]
    result = oracle_coverage(rows, scope)
    assert result["nominal_seconds"] == 15
    assert result["actual_seconds"] == 15


def test_oracle_summary_is_independent_numeric_calculation() -> None:
    scenario = make_scenarios()[0]
    rows = [row for row in scenario.observations if row.observation_id.endswith(("-H1", "-H2"))]
    assert oracle_summary(rows) == 98.0


def test_oracle_episode_boundary_uses_integer_seconds() -> None:
    scenario = make_scenarios()[0]
    rows = [row for row in scenario.observations if row.observation_id.endswith(("-P-H1", "-P-H2"))]
    episodes = oracle_episodes(rows, threshold=95, maximum_gap_seconds=5, minimum_grouping_seconds=15)
    assert len(episodes) == 1
    assert episodes[0].qualifying_seconds == 20

