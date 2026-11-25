"""Create reviewer files with arm labels and traces removed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    root = Path("runs") / args.run
    output = root / "blinded"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted((root / "delivered").glob("*.json")):
        trace = json.loads((root / "traces" / path.name).read_text())
        rows.append({"tuple_id": path.stem, "question_id": trace["question_id"], "answer": json.loads(path.read_text())})
    (output / "review.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(output / "review.jsonl")


if __name__ == "__main__":
    main()

