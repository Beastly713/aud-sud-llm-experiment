"""Support-aware interval arithmetic used by System B.

This is deliberately separate from the independent reference oracle in
``evaluation.gold_oracle``. The production-style implementation uses interval
union/intersection; the oracle uses integer-second occupancy sets.
"""

from __future__ import annotations

from datetime import datetime
from statistics import mean, median
from typing import Iterable

from ...schema import Interval, Observation, SupportKind


def clip(left: Interval, right: Interval) -> Interval | None:
    start = max(left.start, right.start)
    end = min(left.end, right.end)
    return Interval(start=start, end=end) if start < end else None


def union(intervals: Iterable[Interval]) -> list[Interval]:
    ordered = sorted(intervals, key=lambda item: (item.start, item.end))
    output: list[Interval] = []
    for item in ordered:
        if not output or item.start > output[-1].end:
            output.append(item)
        else:
            output[-1] = Interval(start=output[-1].start, end=max(output[-1].end, item.end))
    return output


def union_seconds(intervals: Iterable[Interval]) -> int:
    return sum(item.seconds for item in union(intervals))


def nominal_coverage(observations: Iterable[Observation], scope: Interval) -> tuple[list[Interval], list[str]]:
    clipped: list[Interval] = []
    ids: list[str] = []
    for observation in observations:
        intersection = clip(observation.nominal, scope)
        if intersection:
            clipped.append(intersection)
            ids.append(observation.observation_id)
    return union(clipped), ids


def actual_support(observations: Iterable[Observation], scope: Interval) -> tuple[list[Interval], bool, list[str]]:
    intervals: list[Interval] = []
    unresolved = False
    ids: list[str] = []
    for observation in observations:
        if observation.support_kind == SupportKind.INTERVALS:
            for support in observation.actual_support:
                intersection = clip(support, scope)
                if intersection:
                    intervals.append(intersection)
                    ids.append(observation.observation_id)
        else:
            unresolved = True
    return union(intervals), unresolved, ids


def numeric_summary(observations: Iterable[Observation], statistic: str = "median") -> float | None:
    values = [float(item.value.value) for item in observations if item.value.value is not None]
    if not values:
        return None
    if statistic == "median":
        return float(median(values))
    if statistic == "mean":
        return float(mean(values))
    if statistic == "min":
        return min(values)
    if statistic == "max":
        return max(values)
    if statistic == "count":
        return float(len(values))
    raise ValueError(f"unsupported statistic: {statistic}")


def qualifies(value: float, operator: str, threshold: float) -> bool:
    return {
        ">=": value >= threshold,
        ">": value > threshold,
        "<=": value <= threshold,
        "<": value < threshold,
    }[operator]


def group_qualifying_intervals(
    observations: Iterable[Observation],
    threshold_operator: str,
    threshold: float,
    minimum_grouping_seconds: int,
    maximum_gap_seconds: int,
) -> list[tuple[Interval, list[Observation], int]]:
    """Return (grouping span, rows, qualifying nominal union seconds)."""
    qualifying = [
        item
        for item in observations
        if item.value.value is not None and qualifies(float(item.value.value), threshold_operator, threshold)
    ]
    qualifying.sort(key=lambda item: item.nominal.start)
    if not qualifying:
        return []
    groups: list[list[Observation]] = [[qualifying[0]]]
    for row in qualifying[1:]:
        prior_end = max(item.nominal.end for item in groups[-1])
        gap = int((row.nominal.start - prior_end).total_seconds())
        if gap <= maximum_gap_seconds:
            groups[-1].append(row)
        else:
            groups.append([row])
    results: list[tuple[Interval, list[Observation], int]] = []
    for rows in groups:
        span = Interval(start=rows[0].nominal.start, end=max(item.nominal.end for item in rows))
        if span.seconds >= minimum_grouping_seconds:
            qualifying_union = union_seconds(item.nominal for item in rows)
            results.append((span, rows, qualifying_union))
    return results

