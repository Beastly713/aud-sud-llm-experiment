"""Independent score import; semantic claims require human annotations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.schema import HumanAnnotation, ScoreRow


def load_annotations(path: str | Path) -> dict[str, HumanAnnotation]:
    rows: dict[str, HumanAnnotation] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            annotation = HumanAnnotation.model_validate_json(line)
            if annotation.tuple_id in rows:
                raise ValueError(f"duplicate annotation {annotation.tuple_id}")
            rows[annotation.tuple_id] = annotation
    return rows


def score_run(run_id: str, annotations_path: str | Path) -> list[ScoreRow]:
    root = Path("runs") / run_id
    annotations = load_annotations(annotations_path)
    rows: list[ScoreRow] = []
    for trace_path in sorted((root / "traces").glob("*.json")):
        trace = json.loads(trace_path.read_text())
        tuple_id = trace["tuple_id"]
        annotation = annotations.get(tuple_id)
        if annotation is None:
            raise ValueError(f"missing human annotation for {tuple_id}; semantic scores cannot be completed")
        rows.append(ScoreRow(tuple_id=tuple_id, scenario_id=trace.get("scenario_id"), arm=trace["arm"], cohort=trace["cohort"], sgis=annotation.sgis, rgfr_correct=annotation.rgfr_correct, rgfr_total=annotation.rgfr_total, rnc_correct=annotation.rnc_correct, rnc_total=annotation.rnc_total, gcp_supported=annotation.gcp_supported, gcp_emitted=annotation.gcp_emitted, aha=annotation.aha, cei=annotation.cei, error_tags=annotation.error_tags))
    output = Path("results") / run_id / "scores"
    output.mkdir(parents=True, exist_ok=True)
    (output / "scores.jsonl").write_text("".join(json.dumps(row.model_dump(mode="json"), sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--annotations", required=True)
    args = parser.parse_args()
    rows = score_run(args.run, args.annotations)
    print(f"imported {len(rows)} independent human annotations")


if __name__ == "__main__":
    main()

