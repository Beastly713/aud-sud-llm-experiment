"""Independent development reference calculations.

This module intentionally imports no System B implementation. Coverage and episode
checks use integer-second occupancy sets; numeric summaries use independent standard
library calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, median

from src.schema import Interval, Observation


def second_set(interval: Interval, scope: Interval | None = None) -> set[int]:
    start = int(interval.start.timestamp())
    end = int(interval.end.timestamp())
    values = set(range(start, end))
    if scope is None:
        return values
    return values & set(range(int(scope.start.timestamp()), int(scope.end.timestamp())))


def occupancy(intervals: list[Interval], scope: Interval) -> set[int]:
    return set().union(*(second_set(item, scope) for item in intervals)) if intervals else set()


def oracle_coverage(observations: list[Observation], scope: Interval) -> dict[str, object]:
    accepted = [item for item in observations if item.acceptance.value == "accepted"]
    nominal = occupancy([item.nominal for item in accepted], scope)
    exact = occupancy([support for item in accepted for support in item.actual_support], scope)
    unresolved = any(item.support_kind.value != "intervals" for item in accepted)
    return {"nominal_seconds": len(nominal), "actual_seconds": len(exact), "denominator_seconds": scope.seconds, "actual_exact": not unresolved, "nominal_mask": nominal, "actual_mask": exact}


def oracle_summary(observations: list[Observation], statistic: str = "median") -> float | None:
    values = [Decimal(str(item.value.value)) for item in observations if item.value.value is not None and item.acceptance.value == "accepted"]
    if not values:
        return None
    if statistic == "median":
        value = median(values)
    elif statistic == "mean":
        value = mean(values)
    elif statistic == "min":
        value = min(values)
    elif statistic == "max":
        value = max(values)
    elif statistic == "count":
        return float(len(values))
    else:
        raise ValueError(statistic)
    return float(value)


@dataclass(frozen=True)
class OracleEpisode:
    grouping_start: int
    grouping_end: int
    qualifying_seconds: int
    row_ids: tuple[str, ...]


def oracle_episodes(observations: list[Observation], *, threshold: float, maximum_gap_seconds: int, minimum_grouping_seconds: int, operator: str = ">=") -> list[OracleEpisode]:
    def qualifies(value: float) -> bool:
        return {">=": value >= threshold, ">": value > threshold, "<=": value <= threshold, "<": value < threshold}[operator]

    rows = [item for item in observations if item.acceptance.value == "accepted" and item.value.value is not None and qualifies(float(item.value.value))]
    rows.sort(key=lambda item: item.nominal.start)
    groups: list[list[Observation]] = []
    for row in rows:
        if not groups:
            groups.append([row])
            continue
        prior_end = max(int(item.nominal.end.timestamp()) for item in groups[-1])
        gap = int(row.nominal.start.timestamp()) - prior_end
        if gap <= maximum_gap_seconds:
            groups[-1].append(row)
        else:
            groups.append([row])
    output: list[OracleEpisode] = []
    for group in groups:
        start = int(group[0].nominal.start.timestamp())
        end = max(int(item.nominal.end.timestamp()) for item in group)
        if end - start < minimum_grouping_seconds:
            continue
        mask = set().union(*(second_set(item.nominal) for item in group))
        output.append(OracleEpisode(start, end, len(mask), tuple(item.observation_id for item in group)))
    return output


def oracle_reference_difference(observations: list[Observation], reference_center: float) -> float | None:
    target = oracle_summary(observations, "median")
    return None if target is None else target - reference_center

