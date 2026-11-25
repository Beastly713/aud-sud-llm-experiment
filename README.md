# AUD/SUD D2 LLM comparative experiment

This repository implements the development phase of the finalized AUD/SUD experiment. It contains versioned Pydantic contracts, five synthetic development scenarios (25 questions), an independent arithmetic oracle, deterministic System B tools, mocked A/B/C workflows, the offline System C sandbox adapter, a reproducible runner, and evaluation utilities.

The active experimental specification is `docs/AUD_SUD_LLM_Experimental_Protocol_Finalization_Dossier_v1.2.md`, bound to Blueprint v1.8; v1.1 is retained as historical protocol context. No held-out benchmark is included, no live API call is enabled by default, and no result is claimed by this repository.

## Local commands

```bash
./.venv/bin/python -m src.devdata_export
./.venv/bin/python -m src.schema_export
./.venv/bin/python -m evaluation.gold_validate --split dev
./.venv/bin/python -m pytest tests/unit tests/security tests/dev
./.venv/bin/python -m src.runner --split dev --arms A,C,B --mock --run development-mock
./.venv/bin/python -m src.runner --split dev --arms A,C,B --mock --questions D01-Q1,D02-Q4a,D03-Q2 --run development-smoke-mock
```

The dependency versions are specified in `requirements.lock`. Installation, API credentials and Docker daemon setup are operator responsibilities. Live execution requires both `AUD_SUD_ALLOW_LIVE_API=true` and the explicit `--live` flag. Live B generates its own typed plan and composition; live C uses the configured Docker sandbox. Mock runs and live runs must use different `--run` identifiers.

After manually installing dependencies, selecting an available provider/model, setting
an API key and replacing the sandbox placeholder with an approved pinned digest, an
operator may run the development smoke test with:

```bash
export AUD_SUD_ALLOW_LIVE_API=true
export AUD_SUD_PROVIDER=gemini
export AUD_SUD_MODEL_ID='<operator-selected-model-id>'
export AUD_SUD_API_KEY='<operator-supplied-secret>'
export AUD_SUD_SANDBOX_IMAGE='<approved-image-reference-with-64-hex-digest>'
./.venv/bin/python -m src.runner --split dev --arms A,C,B --live --questions D01-Q1,D02-Q4a,D03-Q2 --run development-live-smoke
```

The live command has not been run in development verification. It reports attempted,
successful and failed workflows and writes raw/delivered answers, model-call usage,
traces and a resumable execution manifest under `runs/<run-id>/`.

Materialization writes the canonical D01–D05 fixtures, 25 questions, provisional gold
and manual-plan manifest under the development directories. It does not create any
held-out question or scenario. The sandbox image digest in `configs/protocol.yaml`
must be replaced by the operator with the approved pinned image before System C live
execution.

## Boundaries

`data/test/` intentionally contains no scenarios or questions. Final benchmark construction, human review, API execution, result interpretation and clinical validation are later authorized activities. Gold artifacts are never included in system prompts or the System C sandbox.

