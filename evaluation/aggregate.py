"""Primary/reproducibility aggregation and scenario-cluster bootstrap."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def _rate(rows: list[dict[str, object]], arm: str, key: str = "sgis") -> tuple[int, int, float | None]:
    selected = [row for row in rows if row["arm"] == arm]
    numerator = sum(int(row[key]) for row in selected)
    denominator = len(selected)
    return numerator, denominator, (numerator / denominator if denominator else None)


def _slot_rate(rows: list[dict[str, object]], arm: str, numerator_key: str, denominator_key: str) -> tuple[int, int, float | None]:
    selected = [row for row in rows if row["arm"] == arm]
    numerator = sum(int(row[numerator_key]) for row in selected)
    denominator = sum(int(row[denominator_key]) for row in selected)
    return numerator, denominator, (numerator / denominator if denominator else None)


def scenario_bootstrap(rows: list[dict[str, object]], arm_a: str, arm_b: str, *, seed: int = 20261125, resamples: int = 10000) -> dict[str, object]:
    primary = [row for row in rows if row["cohort"] == "primary"]
    by_scenario: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for row in primary:
        # The runner's immutable tuple IDs are not intended to encode scenario IDs;
        # production score files should add question/scenario metadata. This fallback
        # keeps the development utility explicit rather than silently treating rows as iid.
        scenario_id = str(row.get("scenario_id", ""))
        if not scenario_id:
            continue
        by_scenario[scenario_id][str(row["arm"])].append(int(row["sgis"]))
    scenarios = [key for key in by_scenario if arm_a in by_scenario[key] and arm_b in by_scenario[key]]
    if not scenarios:
        return {"delta": None, "ci": [None, None], "scenario_count": 0}
    differences = [sum(by_scenario[key][arm_a]) / len(by_scenario[key][arm_a]) - sum(by_scenario[key][arm_b]) / len(by_scenario[key][arm_b]) for key in scenarios]
    delta = sum(differences) / len(differences)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(resamples):
        sample = [rng.choice(differences) for _ in scenarios]
        values.append(sum(sample) / len(sample))
    values.sort()
    low = values[int(0.025 * (len(values) - 1))]
    high = values[int(0.975 * (len(values) - 1))]
    return {"delta": delta, "ci": [low, high], "scenario_count": len(scenarios), "differences": differences}


def aggregate(run_id: str, bootstrap: int = 10000) -> dict[str, object]:
    path = Path("results") / run_id / "scores" / "scores.jsonl"
    if not path.exists():
        raise FileNotFoundError(path)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    primary = [row for row in rows if row["cohort"] == "primary"]
    summary = {
        arm: {
            "SGIS": _rate(primary, arm, "sgis"),
            "RGFR": _slot_rate(primary, arm, "rgfr_correct", "rgfr_total"),
            "RNC": _slot_rate(primary, arm, "rnc_correct", "rnc_total"),
            "AHA": _rate(primary, arm, "aha"),
            "CEI": _rate(primary, arm, "cei"),
            "GCP": {"supported": sum(int(row["gcp_supported"]) for row in primary if row["arm"] == arm), "emitted": sum(int(row["gcp_emitted"]) for row in primary if row["arm"] == arm)},
        }
        for arm in ("A", "B", "C")
    }
    output = {"primary_only": summary, "B_minus_C": scenario_bootstrap(rows, "B", "C", resamples=bootstrap), "B_minus_A": scenario_bootstrap(rows, "B", "A", resamples=bootstrap), "reproducibility_excluded_from_primary": True}
    destination = Path("results") / run_id / "summary"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "summary.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--bootstrap", type=int, default=10000)
    args = parser.parse_args()
    print(json.dumps(aggregate(args.run, args.bootstrap), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

