"""Mechanical B-only checks for composed answers."""

from __future__ import annotations

from ...schema import CommonAnswer, EvidenceBundle, Finding


def verify_answer(answer: CommonAnswer, bundle: EvidenceBundle) -> tuple[CommonAnswer, list[str]]:
    fact_keys = {
        (fact.claim, fact.metric, fact.method, fact.reference_id, fact.episode_rule_id)
        for fact in bundle.computed_facts
    }
    problems: list[str] = []
    verified: list[Finding] = []
    for finding in answer.findings:
        key = (finding.claim, finding.metric, finding.method, finding.reference_id, finding.episode_rule_id)
        if key not in fact_keys:
            problems.append("finding is not bound to a computed fact")
            continue
        if not set(finding.source_ids).issubset(set(bundle.source_ids)):
            problems.append("finding cites a source outside the evidence bundle")
            continue
        verified.append(finding)
    if problems:
        answer = answer.model_copy(update={"findings": verified, "status": "partial" if verified else "insufficient"})
    return answer, problems

