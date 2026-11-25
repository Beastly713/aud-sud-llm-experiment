"""Materialize the canonical development objects as JSON after dependencies are installed."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .devdata import make_gold, make_questions, make_scenarios, make_plans


def export(root: Path) -> None:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    plans = make_plans(scenarios, questions)
    gold = make_gold(questions)
    fixture_dir = root / "data" / "dev" / "fixtures"
    question_dir = root / "data" / "dev" / "questions"
    gold_dir = root / "gold" / "dev"
    for directory in (fixture_dir, question_dir, gold_dir):
        directory.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        (fixture_dir / f"{scenario.scenario_id}.json").write_text(json.dumps(scenario.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for question in questions:
        (question_dir / f"{question.question_id}.json").write_text(json.dumps(question.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (gold_dir / "gold.json").write_text(json.dumps([item.model_dump(mode="json") for item in gold], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "data" / "dev" / "correct_plans.json").write_text(json.dumps({key: value.model_dump(mode="json") for key, value in plans.items()}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_paths = [
        *sorted(fixture_dir.glob("*.json")),
        *sorted(question_dir.glob("*.json")),
        gold_dir / "gold.json",
        root / "data" / "dev" / "correct_plans.json",
    ]
    artifact_hashes = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifact_paths
    }
    manifest = {"scenario_ids": [item.scenario_id for item in scenarios], "question_ids": [item.question_id for item in questions], "artifact_sha256": artifact_hashes, "status": "development-artifacts-materialized-pending-human-review"}
    (root / "data" / "manifests" / "dev_materialized.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    export(Path(args.root).resolve())
    print("materialized development fixtures, questions, gold and plans")


if __name__ == "__main__":
    main()

