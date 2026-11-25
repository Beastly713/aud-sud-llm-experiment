"""Evidence bundle construction from trusted intermediate results."""

from __future__ import annotations

from ...evidence_store import EvidenceStore
from ...schema import (
    EvidenceBundle,
    Finding,
    InvestigationPlan,
    IntervalResult,
    Limitation,
    Question,
)


def build_bundle(
    store: EvidenceStore,
    question: Question,
    plan: InvestigationPlan,
    results: dict[str, object],
) -> EvidenceBundle:
    facts: list[Finding] = []
    limitations: list[Limitation] = []
    source_ids: set[str] = set()
    for result in results.values():
        if isinstance(result, IntervalResult):
            facts.extend(result.facts)
            for limitation in result.limitations:
                if limitation:
                    limitations.append(Limitation(claim=limitation, reason_code="runtime", source_ids=[]))
            source_ids.update(source for fact in result.facts for source in fact.source_ids)
        else:
            source_ids.update(getattr(result, "source_ids", []))
            for limitation in getattr(result, "limitations", []):
                if limitation:
                    limitations.append(
                        Limitation(
                            claim=limitation,
                            reason_code="event_or_selection",
                            source_ids=list(getattr(result, "source_ids", [])),
                        )
                    )
    revisions = {source_id: store.source(source_id).revision for source_id in source_ids}
    return EvidenceBundle(
        question_id=question.question_id,
        snapshot_id=store.snapshot_id,
        plan_id=plan.plan_id,
        effective_scope=list(question.authorized_scope),
        computed_facts=facts,
        limitations=limitations,
        source_ids=sorted(source_ids),
        selected_revisions=revisions,
        internal_fact_ids={f"fact-{index + 1}": fact.claim for index, fact in enumerate(facts)},
    )

