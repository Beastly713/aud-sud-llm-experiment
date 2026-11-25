"""Deterministic rendering used as the mocked composition path."""

from __future__ import annotations

from ...schema import CommonAnswer, EvidenceBundle, Finding, Limitation, AnswerStatus


def compose_from_bundle(bundle: EvidenceBundle) -> CommonAnswer:
    if bundle.computed_facts:
        status = AnswerStatus.PARTIAL if bundle.limitations else AnswerStatus.ANSWERED
        return CommonAnswer(status=status, findings=bundle.computed_facts, limitations=bundle.limitations)
    if bundle.limitations:
        if any("clarify" in item.claim or "multiple" in item.claim for item in bundle.limitations):
            return CommonAnswer(
                status=AnswerStatus.CLARIFY,
                limitations=bundle.limitations,
                clarification="Specify which source-supported occurrence or anchor should be selected.",
            )
        return CommonAnswer(status=AnswerStatus.INSUFFICIENT, limitations=bundle.limitations)
    return CommonAnswer(
        status=AnswerStatus.INSUFFICIENT,
        limitations=[Limitation(claim="no supported computed evidence was available", reason_code="no_evidence")],
    )

