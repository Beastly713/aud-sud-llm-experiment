# Implementation status

Date: 2026-11-25

## Implemented

- Versioned Pydantic v2 contracts for the shared evidence, clinical event, reference,
  policy, answer, gold, plan, intermediate-result, bundle, trace and annotation data.
- Canonical JSON serialization, normalization, schema export command and immutable
  serialized snapshot access with source resolution.
- Authored D01–D05 development fixture factory, 25 questions, manual-plan manifest
  generation, provisional gold records and a human-readable worksheet. Gold is marked
  `pending-human-review` and is not imported by a workflow.
- Independent integer-second occupancy oracle and Decimal/statistics summaries.
- System B typed plan validation, clinical event admission/anchor handling,
  observation/context/reference selection, support-aware interval/episode/comparison
  operations, bundle construction, composition and mechanical checks.
- System A direct/review workflow; System C generated-program workflow with a
  disposable Docker command containing offline, read-only, unprivileged, resource and
  output limits; local mock sandbox for tests.
- Shared hosted-model abstraction with explicit environment + CLI live gates, mock
  client, structured output, trace fields, call/retry/token/latency slots and runner
  scheduling/resume identifiers.
- Blinded export, human annotation validation/import, SGIS/RGFR/RNC/GCP/AHA/CEI score
  fields, primary/reproducibility-aware aggregation and result-figure generation.
- No held-out scenarios/questions, test gold, final benchmark freeze or API results.

## Checks executed

- `python3 -m compileall -q src evaluation tests` — passed.
- `python3 -m py_compile $(rg --files src evaluation tests -g '*.py')` — passed.
- Static checks confirmed no D2 import in `evaluation/gold_oracle.py`, no material
  files in `data/test/` or `gold/test/`, and no trailing-whitespace findings.

## Blocked checks

- `python3 -m evaluation.gold_validate --split dev` — blocked: `pydantic` is not
  installed in the workspace.
- `python3 -m pytest tests/unit tests/security tests/dev` — blocked: `pytest` is not
  installed.
- Schema materialization, fixture JSON export, mocked workflow execution and all
  runtime tests therefore remain unexecuted; they are not reported as passed.
- Docker runtime validation is not executed: the daemon is unavailable and the
  approved pinned Python image digest still requires operator configuration.
- No API credentials, provider/model selection, live requests or human review were
  performed.

## Human-review requirements

Before any benchmark freeze, independently review all five scenario cards, 25
questions, numerical/source-selection worksheets and provisional gold records; then
freeze hashes and the repeat-subset manifest. Clinical/mentor review, if obtained,
must be described as phrasing/face-validity review rather than clinical ground truth.

## Next commands after environment setup

```bash
python3 -m src.devdata_export
python3 -m src.schema_export
python3 -m evaluation.gold_validate --split dev
python3 -m pytest tests/unit tests/security tests/dev
python3 -m src.runner --split dev --arms A,C,B --mock --run development
```

Replace the sandbox image placeholder in `configs/protocol.yaml` with the approved
pinned image before any System C container run. Do not use `--live` until a model ID,
provider settings, credentials, quota and explicit execution authorization have been
reviewed separately.

