"""Deterministic rendering used as the mocked composition path."""

from __future__ import annotations

from ...schema import CommonAnswer, EvidenceBundle, Finding, Limitation, AnswerStatus


def compose_from_bundle(bundle: EvidenceBundle) -> CommonAnswer:
    if any("clarify" in item.claim or "multiple" in item.claim for item in bundle.limitations):
        return CommonAnswer(
            status=AnswerStatus.CLARIFY,
            findings=bundle.computed_facts,
            limitations=bundle.limitations,
            clarification="Specify which source-supported occurrence or anchor should be selected.",
        )
    missing_anchor = any(
        "no source-supported event matched" in item.claim
        or "no completed administration anchor" in item.claim
        for item in bundle.limitations
    )
    if bundle.question_id.endswith("Q4a") and missing_anchor and not any(fact.claim_kind.value != "event" for fact in bundle.computed_facts):
        return CommonAnswer(status=AnswerStatus.INSUFFICIENT, limitations=bundle.limitations)
    if bundle.computed_facts:
        unmet = any(
            item.reason_code in {
                "approximate_anchor",
                "uncertain_anchor_blocks_exact_aggregate",
                "reference_unavailable",
                "method_incompatible_reference",
                "no_completed_administration_anchor",
                "no_completed_administration",
            }
            or "dependent interval" in item.claim
            or "no selected observations" in item.claim
            for item in bundle.limitations
        )
        status = AnswerStatus.PARTIAL if unmet else AnswerStatus.ANSWERED
        return CommonAnswer(status=status, findings=bundle.computed_facts, limitations=bundle.limitations)
    if bundle.limitations:
        return CommonAnswer(status=AnswerStatus.INSUFFICIENT, limitations=bundle.limitations)
    return CommonAnswer(
        status=AnswerStatus.INSUFFICIENT,
        limitations=[Limitation(claim="no supported computed evidence was available", reason_code="no_evidence")],
    )

