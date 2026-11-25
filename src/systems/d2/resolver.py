"""Source resolution for evidence links."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import ResolvedSource


def resolve_evidence(store: EvidenceStore, evidence_ids: list[str]) -> list[ResolvedSource]:
    output: list[ResolvedSource] = []
    for source_id in evidence_ids:
        source = store.resolve_source(source_id)
        scope_status = "covered" if source.covered_scope else "unknown"
        output.append(
            ResolvedSource(
                source_id=source.source_id,
                source_type=source.source_type,
                locator=source.locator,
                content=source.content,
                revision=source.revision,
                scope_status=scope_status,
            )
        )
    return output

