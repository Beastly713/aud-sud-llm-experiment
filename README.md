# AUD/SUD D2 LLM comparative experiment

This repository implements the development phase of the finalized AUD/SUD experiment. It contains versioned Pydantic contracts, five synthetic development scenarios (25 questions), an independent arithmetic oracle, deterministic System B tools, mocked A/B/C workflows, the offline System C sandbox adapter, a reproducible runner, and evaluation utilities.

The authoritative protocol and blueprint remain in `docs/`. The protocol is the experimental specification; the blueprint supplies D2 semantics. No held-out benchmark is included, no live API call is enabled by default, and no result is claimed by this repository.

## Local commands

```bash
python3 -m src.devdata_export
python3 -m src.schema_export
python3 -m evaluation.gold_validate --split dev
python3 -m pytest tests/unit tests/security tests/dev
python3 -m src.runner --split dev --arms A,C,B --mock
```

The dependency versions are pinned in `requirements.lock`. Installation, API credentials and Docker daemon setup are operator responsibilities. Live execution requires both `AUD_SUD_ALLOW_LIVE_API=true` and the explicit `--live` flag; the development runner uses mocked model responses.

Materialization writes the canonical D01–D05 fixtures, 25 questions, provisional gold
and manual-plan manifest under the development directories. It does not create any
held-out question or scenario. The sandbox image digest in `configs/protocol.yaml`
must be replaced by the operator with the approved pinned image before System C live
execution.

## Boundaries

`data/test/` intentionally contains no scenarios or questions. Final benchmark construction, human review, API execution, result interpretation and clinical validation are later authorized activities. Gold artifacts are never included in system prompts or the System C sandbox.

