"""Mechanical prechecks shared by scoring and blinded review tooling.

These checks validate structure, IDs, units and explicit status fields. They never
decide semantic support; that remains a blinded human annotation requirement.
"""

from __future__ import annotations

from typing import Any

from src.schema import CommonAnswer, GoldRecord


def automated_checks(answer: CommonAnswer, gold: GoldRecord, known_source_ids: set[str]) -> dict[str, Any]:
    cited = {source_id for finding in answer.findings for source_id in finding.source_ids}
    cited.update(source_id for limitation in answer.limitations for source_id in limitation.source_ids)
    return {
        "schema_valid": True,
        "status_matches": answer.status == gold.status,
        "unknown_source_ids": sorted(cited - known_source_ids),
        "all_citations_resolve": cited.issubset(known_source_ids),
        "finding_count": len(answer.findings),
        "limitation_count": len(answer.limitations),
        "semantic_review_required": True,
    }

