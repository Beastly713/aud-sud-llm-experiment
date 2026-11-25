# Implementation status

Date: 2026-11-25

## Confirmed-defect fix pass

- Corrected all development oracle selectors to exact D01 observation IDs; the
  independent oracle was not changed.
- Distinguished missing/invalid dependencies, wrong result types and valid interval
  results with unavailable intervals. Approximate, missing and ambiguous anchors now
  propagate limitations without scope substitution, false zero coverage or crashes.
- Added focused blocked-dependency and partial-window coverage regressions.
- Added explicit fully-contained versus clip-for-coverage observation selection.
- Expanded clinical bundles with event selections, candidate/selected clinical events,
  occurrence IDs, action/assertion/time fields, source revisions and limitations.
- Replaced placeholder gold slots with independently authored values, units,
  denominators, exclusions, limitations and statuses for all 25 provisional records;
  D02-Q1 is `answered` for its actual 30-second scope. D03/D04 ambiguity and partial
  answerability were corrected.
- Regenerated materialized development plans, gold, schemas and artifact-hash
  manifest; human-review fields remain pending.

## Live execution-path implementation

- Added strict live/mock execution contexts. Live B receives no authored development
  plan, and live C receives `DockerSandbox`; mock test doubles are confined to the
  offline path. Run manifests reject mode, model or schedule reuse.
- Added `--questions` selection for one or comma-separated development IDs, per-call
  raw provider records and token/retry traces, and attempted/successful/failed
  workflow summaries.
- Added Gemini support through `google-genai` with a provider-specific conservative
  response-schema conversion and local Pydantic validation for all structured outputs.
- Added frozen common prompt/definition loading to A, B and C and actual D2 argument
  schemas/manifests to B. Docker execution now validates a 64-hex digest, runs
  offline/non-root/read-only with resource/output limits, and cleans up timeouts.
- Added live-routing regression tests and retained clinical selection details in the
  D2 composition bundle. No development dataset or authoritative document was
  changed in this pass.

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
- `git diff --check` — passed.
- JSON parsing and artifact checks for all materialized fixtures, questions, plans,
  gold, schemas and manifests — passed.
- Regenerated-artifact checks confirmed 25 gold records, exact Q1 coverage plans,
  pending review status and corrected answerability statuses — passed.
- `./.venv/bin/python -m pytest` — passed: 26 tests, including live-routing,
  pinned-image, workflow, oracle and D2 semantic regressions.
- `./.venv/bin/python -m src.runner --split dev --arms A,C,B --mock
  --questions D01-Q1,D02-Q4a,D03-Q2 --run verification-mock-smoke` — passed: 9
  attempted, 9 successful, 0 failed; raw/delivered/traces/usage records present.
- The live gate was exercised without credentials; it failed before any provider
  request because `AUD_SUD_ALLOW_LIVE_API` was not enabled.
- Static checks confirmed no D2 import in `evaluation/gold_oracle.py`, no material
  files in `data/test/` or `gold/test/`, and no trailing-whitespace findings.

## Blocked checks

- The base `python3` environment still lacks project runtime packages; the repository
  `.venv` supplied the verified execution environment used above.
- `google-genai` is specified but not installed, so an offline Gemini adapter transport
  check remains pending the operator dependency installation.
- Docker client is present but the daemon socket is not accessible; the configured
  sandbox image is still the intentional placeholder and fails digest validation.
- No API credentials, provider/model selection, live requests or human review were
  performed.

## Human-review requirements

Before any benchmark freeze, independently review all five scenario cards, 25
questions, numerical/source-selection worksheets and provisional gold records; then
freeze hashes and the repeat-subset manifest. Clinical/mentor review, if obtained,
must be described as phrasing/face-validity review rather than clinical ground truth.

## Next commands after environment setup

```bash
./.venv/bin/python -m src.devdata_export
./.venv/bin/python -m src.schema_export
./.venv/bin/python -m evaluation.gold_validate --split dev
./.venv/bin/python -m pytest tests/unit tests/security tests/dev
./.venv/bin/python -m src.runner --split dev --arms A,C,B --mock --questions D01-Q1,D02-Q4a,D03-Q2 --run development-smoke-mock
```

After installing `google-genai`, selecting a provider/model, supplying the API key,
and configuring an approved sandbox digest, the operator smoke command is:

```bash
AUD_SUD_ALLOW_LIVE_API=true AUD_SUD_PROVIDER=gemini AUD_SUD_MODEL_ID='<operator-selected-model-id>' AUD_SUD_API_KEY='<operator-supplied-secret>' AUD_SUD_SANDBOX_IMAGE='<approved-image-reference-with-64-hex-digest>' ./.venv/bin/python -m src.runner --split dev --arms A,C,B --live --questions D01-Q1,D02-Q4a,D03-Q2 --run development-live-smoke
```

Replace the sandbox image placeholder in `configs/protocol.yaml` or set
`AUD_SUD_SANDBOX_IMAGE` to the approved pinned image before any System C container
run. Do not use `--live` until a model ID, provider settings, credentials, quota and
explicit execution authorization have been reviewed separately. The exact live
three-arm smoke command is in `README.md`.

