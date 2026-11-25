"""Required result figures; refuses to fabricate figures without scored results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make_plots(run_id: str) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for result figures") from exc
    summary_path = Path("results") / run_id / "summary" / "summary.json"
    if not summary_path.exists():
        raise RuntimeError("no scored summary exists; do not fabricate result figures")
    summary = json.loads(summary_path.read_text())
    arms = ["A", "B", "C"]
    rates = [summary["primary_only"][arm]["SGIS"][2] or 0 for arm in arms]
    output = Path("results") / run_id / "figures"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "primary_sgis.png"
    plt.figure(figsize=(5, 3))
    plt.bar(arms, rates)
    plt.ylabel("SGIS proportion")
    plt.title("Primary SGIS (scored outputs only)")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return [path]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    print("\n".join(str(path) for path in make_plots(args.run)))


if __name__ == "__main__":
    main()

