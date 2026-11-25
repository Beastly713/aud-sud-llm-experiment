"""Export the public contract schemas."""

from __future__ import annotations

from pathlib import Path

from .schema import (
    CommonAnswer,
    EvidenceBundle,
    GoldRecord,
    InvestigationPlan,
    Question,
    Scenario,
)
from .serialization import export_schemas


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    export_schemas(
        [Scenario, Question, CommonAnswer, GoldRecord, InvestigationPlan, EvidenceBundle],
        root / "schemas",
    )


if __name__ == "__main__":
    main()

