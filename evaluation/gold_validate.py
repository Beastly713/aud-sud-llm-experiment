"""Validate provisional/independent gold records without executing System B."""

from __future__ import annotations

import argparse

from src.devdata import make_gold, make_questions, make_scenarios


def validate_dev() -> list[str]:
    scenarios = make_scenarios()
    questions = make_questions(scenarios)
    gold = make_gold(questions)
    errors: list[str] = []
    if len(scenarios) != 5 or len(questions) != 25 or len(gold) != 25:
        errors.append("development split must contain five scenarios and 25 questions/gold records")
    if {item.question_id for item in questions} != {item.question_id for item in gold}:
        errors.append("gold/question IDs do not match")
    for scenario in scenarios:
        if len([item for item in questions if item.scenario_id == scenario.scenario_id]) != 5:
            errors.append(f"{scenario.scenario_id} does not have five questions")
        if scenario.snapshot.snapshot_id not in {item.snapshot_id for item in questions if item.scenario_id == scenario.scenario_id}:
            errors.append(f"{scenario.scenario_id} snapshot binding mismatch")
    if any(record.review_resolved for record in gold):
        errors.append("development gold must remain pending human review")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    args = parser.parse_args()
    if args.split == "test":
        raise SystemExit("test gold is intentionally not present in the development repository")
    errors = validate_dev()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("validated 5 development scenarios, 25 questions and 25 provisional gold records")


if __name__ == "__main__":
    main()

