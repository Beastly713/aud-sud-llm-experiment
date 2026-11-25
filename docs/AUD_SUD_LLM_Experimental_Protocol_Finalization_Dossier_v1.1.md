# AUD/SUD Clinical Intelligence — LLM Experimental Protocol Finalization Dossier

**Decision document | 25 November 2026 | Protocol v1.1**  
**Authority:** `AUD_SUD_Clinical_Intelligence_Final_Integrated_Blueprint_2026-11-24_v1.6.md` (hereafter Blueprint).  
**Status:** recommended frozen protocol for approval; no experimental runs, measured improvements, clinical validation or patentability determination are claimed. All numerical examples below are constructed teaching fixtures, not results.

**v1.1 revision (25 November 2026):** Following the protocol audit, retain the three-arm D2 design, all 24 held-out scenarios and 120 questions, independent gold and all metrics. Replace full duplicate execution with a single primary run plus a prespecified 24-question reproducibility subset, defer selection of the exact model to account/API preflight, and make shared schema finalization the first implementation gate. All affected counts, formulas, scoring, reporting and execution instructions below supersede v1.0. No change to Blueprint v1.6 or measured result is implied.

## 1. Executive decision

**Proceed with a controlled, paired evaluation of D2: clinician-directed longitudinal evidence investigation.** The experiment should establish whether the same LLM produces more complete, correct, source-supported and appropriately qualified answers when operating through the proposed constrained evidence-investigation architecture rather than interpreting all evidence directly or generating general-purpose executable analysis code.

Use one benchmark, three configurations, 24 held-out fictional participant scenarios and 120 distinct questions. Use five separate development scenarios (25 questions). Each scenario contributes one Q1, one Q2, one Q3 and two Q4 questions. Run every test question once under each configuration for the primary evaluation (360 attempted answers), then independently repeat a prespecified representative subset of 24 questions under all three configurations (72 additional attempts; 432 total). Report reproducibility separately from the primary evaluation. The primary contrast is proposed D2 versus a general-purpose program-assisted LLM; direct LLM is the secondary, interpretable reference. The experiment is not an arithmetic benchmark: 40% of the tasks are clinical-event-anchored and the remaining tasks test the physiological evidence operations they depend upon.

| Decision | Selected specification |
|---|---|
| Experimental unit | Independent synthetic patient monitoring scenario; five related questions per scenario |
| Evidence | Independently constructed Bucket 4/5-style observations and structured clinical assertions with source snippets, historical references and policies |
| Configurations | A: direct LLM with review; C: general-purpose Python-assisted LLM; B: proposed constrained D2 |
| Primary endpoint | Strict grounded investigation success (whole answer, not just numeric accuracy) |
| Primary comparison | B − C in percentage points, paired by scenario and question |
| Secondary comparison | B − A; same metric and matched questions |
| Secondary endpoints | Required-fact recall, numerical correctness, grounded-claim precision, answerability handling, consequential-error incidence |
| Execution | One pinned hosted model, same definitions/evidence access, no fine-tuning; one primary run per question/arm plus a separate 24-question repeat subset |
| Implementation | Standalone Python, Pydantic, JSON fixtures, deterministic D2 tools, isolated generic-code runner, scoring scripts |
| Evidence claim | Controlled software investigation correctness on specified evidence contracts; not clinical outcome, device validation, clinician productivity or superiority over all other architectures |

The important change from the preliminary protocol is the **general-purpose computation baseline**. A direct model without tools is relevant, but beating it alone cannot establish whether D2's domain-aware evidence orchestration contributes anything beyond calculation offloading. C gives the model ordinary computational ability and all the same domain rules. It is a substantive comparison, not a deliberately weak foil. No fourth arm, multi-model sweep, external dataset integration or separate D1/D3 experiment is required for this claim.

**Success is not guaranteed.** B may beat A and tie or lose to C. That is a useful and reportable result: it means the proposed workflow has not demonstrated incremental correctness over this program-assisted comparator on the benchmark. Do not redesign the test after observing results to obtain a favorable number.

## 2. Experimental target and research hypothesis

### 2.1 What is being tested

Blueprint §§1, 2.4, 5, 7 and 10 distinguish upstream measurement validity from downstream evidence use. The independent variable is the downstream LLM execution architecture; the controlled inputs are the same clinician question, evidence snapshot, authorized scope and operation definitions. The dependent variable is the correctness and grounding of the final investigation answer.

```
Frozen B4/B5 evidence + structured clinical assertions + question
                     | identical information
         +-----------+-----------+
         |           |           |
     A direct    C Python     B typed D2
     LLM review   assisted    plan -> validation -> tools
         |           |        -> bounded evidence -> verification
         +-----------+-----------+
                    |
          independent gold and blinded scoring
```

D2 is the central interactive capability because it translates an open-form review request into the correct combination of evidence types, constraints, operations and explanation. Q4 exercises clinical semantics and time anchoring; Q1–Q3 are meaningful component behaviors within that same investigation workflow. These classes are composable, not separate agents. The experiment tests language interpretation **and** faithful execution and reporting, including when the requested information cannot be established. A correct answer requires the right patient scope, source-supported anchors, admissible measurements, correct support geometry, named comparison policy, valid computation and qualified presentation.

D1 is deliberately upstream of this experiment: clinical assertion fixtures represent independently annotated, already-ingested clinical evidence, with original synthetic text/structured records. Do not ask the evaluated systems to extract a new clinical record from raw notes. They must still respect semantic support, assertion, occurrence and action status. D3 is not evaluated; the final D2 answer is composed and grounded, but it is not a longitudinal handoff completeness test. No physiological raw signal processing, reference-threshold validation, or clinical diagnosis is required here. This is faithful isolation, not removal of other buckets.

### 2.2 Hypotheses and scope

**Objective:** compare the end-to-end correctness of three same-model clinical-evidence investigation configurations for answering bounded natural-language Q1–Q4 questions over an identical synthetic evidence view conforming to Blueprint v1.6.

**Primary directional research hypothesis (H1):** D2's typed, validated investigation plan, deterministic application of physiological/clinical evidence semantics, and verified evidence-linked composition yield higher strict grounded investigation success than a same-model general-purpose program-assisted workflow given equivalent evidence and instructions.

**Secondary hypothesis:** B also exceeds a strong direct, tool-free same-model workflow. The primary estimand is the difference in mean scenario-level strict success on the first execution of all 120 questions, B minus C; null of no positive difference is the reference, not a claim of statistically powered population inference. Report two-sided uncertainty intervals. Additional endpoints diagnose where gains or losses arise.

Anticipated mechanisms (hypotheses, not results): explicit event admission and occurrence resolution reduce wrong anchors; validated dependent operations preserve temporal and reference binding; deterministic interval handling avoids double counting; policy-specific eligibility prevents confusing quality with comparability; explicit limitations and fact/source checks reduce unsupported claims. Planning itself can fail and narrow tools can refuse legitimate questions. These are measured, not assumed away.

The comparison estimates the effect of a **package** of architecture decisions and prompts in the selected implementation, not an isolated causal contribution of each component. An oracle plan is useful only as a diagnostic unit test and is not an evaluated arm. No claim of clinical efficacy or patent novelty follows.

## 3. Research findings and methodological implications

Targeted primary-source review, not a systematic literature review. References [R1–R12] are linked in §15. No published result is treated as a result of this project.

| Research | Applicable lesson | Decision and boundary |
|---|---|---|
| EHRSQL, NeurIPS 2022; EHRSQL 2024 shared task [R1,R2] | Structured clinical question answering involves executable queries and recognizing when a reliable answer cannot be produced. | Use executable evidence operations and explicit answerability, including unsupported queries. Do not reuse its reported scores or database schema as a wearable benchmark. |
| PAL, ICML 2023 [R3] | A language model can produce intermediate programs executed by a conventional runtime instead of doing all reasoning in text. | Include C with unrestricted analysis expressivity within a safe offline fixture sandbox. A vs B alone is insufficient to distinguish offloading from domain-aware execution. |
| ReAct, ICLR 2023 [R4] | Models can combine task reasoning with actions and external observations. | Support bounded repair following tool failures, rather than force one brittle generation. No need for a multi-agent system or open-ended tool loop. |
| FinQA, EMNLP 2021 [R5]; BIRD, NeurIPS 2023 [R6] | Numerical QA over heterogeneous evidence and executable structured queries are meaningful tasks; query text similarity does not establish correct outputs. | Check the actual result, anchors and selected/excluded evidence, not exact generated-plan or source-code match. Independently derive numerical answers and keep computation available to C. |
| ALCE, EMNLP 2023 [R7]; ArchEHR-QA, ACL BioNLP 2025 and Scientific Data 2026 [R8,R9] | Correct answer content and citation quality are distinct; clinical evidence can be omitted or used incorrectly even when cited. | Annotate required factual units, acceptable evidence sets and material qualifiers. Human review of semantic support is necessary; ID existence alone is insufficient. No dependence on real hospital notes. |
| WESAD and Synthea [R10,R11] | Wearable stress recordings and synthetic health records serve different validation purposes. | Neither supplies the joint gold clinical/physiological evidence contract needed here. Use controlled fixtures and retain these resources for the Blueprint's other integration activities. |
| Cluster-robust inference guidance [R12] | Correlated observations within groups cannot be treated as independent. | Resample scenario-level paired differences; repeat runs and questions do not increase independent scenario count. Small-cluster uncertainty is descriptive and limited. |

The proposed evaluation is closest to executable clinical QA plus source-grounded synthesis, not medical multiple-choice QA, disease classification, long-context retrieval alone or summarization similarity. Public benchmarks provide methodological precedent; none validates the specific composite of support-aware wearables and clinical event semantics. The justified response is to construct a narrow auditable benchmark, not to manufacture a claim of public-benchmark equivalence.

## 4. Final system configurations

### 4.1 Identical contracts and controls

All arms receive the same question text, participant/snapshot ID, review scope, source inventory, named references and policies, episode definitions, field dictionary, operation definitions and common output schema. Same model snapshot, applicable inference settings, development examples, call/output budgets, common safety boundaries and final scoring. Baselines receive **all** evidence rows and original supporting snippets in a compact canonical JSON document, not a manually preselected subset. C reads the same JSON in its execution sandbox and sees it in its analysis prompt. B gets a manifest (available metrics, methods, policy names, scope, source categories, available ranges, not question-conditioned answers), and its tools can access the full snapshot. B final composition receives selected computed evidence plus limitations. This delivery difference is part of the architecture, not a claim of identical prompts or identical token use. All arms use the same read-only source data, precomputed Bucket 5 eligibility and reference snapshots; B does not receive hidden labels or an oracle answer.

Common instructions: answer the exact request, make descriptive claims only, identify relevant metric/method/units, preserve actual vs nominal support, label denominator, distinguish action/occurrence/assertion/time states, do not silently substitute references, distinguish no observed episode from no evidence, cite evidence for each fact, answer supported subparts, clarify materially ambiguous selection. No external knowledge, diagnosis, drug-effect attribution, unrequested treatment recommendation, external web retrieval or real data. No model access to gold or other test scenarios. All arms may infer the intended operation from the same glossary; none receives question-specific operation labels or ground-truth anchors.

**Common final output** (same structured schema, not exact-match natural language):

```json
{
  "status": "answered | partial | insufficient | clarify",
  "findings": [
    {"claim": "one atomic finding in readable language",
     "metric": null, "value": null, "unit": null,
     "interval": null, "reference_id": null,
     "source_ids": []}
  ],
  "limitations": [{"claim": "specific limitation", "source_ids": []}],
  "clarification": null
}
```

Actual schema uses enum alternatives and typed nullable fields; `value` may be numeric, categorical, or a typed range/list via a union; exact times/coverage counts get dedicated typed subfields. Status is global; partial answers can include a specific clarifying request. Evidence IDs are source-level record/feature/reference/manifest identifiers, not B-private computed fact IDs. For source absence cite the relevant scope/inventory and observed coverage; do not invent a negative clinical fact. Claims in prose must not contradict machine-readable fields. No hidden extra text outside schema. Generate a readable answer by rendering these findings and limitations deterministically for all arms. A common validator enforces schema syntax only; B's separate semantic/numeric post-check is an experimental treatment.

**Mandatory schema-first gate (v1.1):** Before authoring the five development scenarios or implementing the three workflows, define and test the versioned Pydantic contracts for source evidence and policies (§5.4), the shared final answer, and gold records (§7.2). Use small hand-written contract examples for schema tests, not the benchmark. The answer and gold contracts must share the same semantic vocabulary and typed value representation, without exposing gold values or required-slot labels to any evaluated system. In addition to the illustrative fields above, explicitly represent metric/method/site, requested statistic, coverage/support type, numerator and denominator (with units and scope), event/mention/occurrence identity and action/assertion status, event time or bounds and precision, named reference and policy ID/version/status, and evidence snapshot/revisions wherever applicable. Distinguish absent, unknown, inapplicable and numerical zero. Use typed variants or nullable fields only where meaningful; do not force every field on every claim. Include episode rule identity and grouping versus qualifying/support duration where needed. Define machine-readable required qualifiers, acceptable evidence sets, numeric tolerances and status/limitation semantics in the gold contract; narrative meaning remains subject to blinded human review. Validate that each §6.2 representative case, including partial/clarify and unknown support, can be represented and scored without losing meaning. Export common JSON schemas and test serialization, normalization, source resolution and scoring of valid/invalid examples. Review and version these contracts before development fixture construction; any necessary dev-only refinement must be applied to all arms and gold consistently before held-out freeze.

### 4.2 A — Direct LLM with explicit review

1. Give the model the question, complete canonical fixture and common definitions. Instruct it to work out the relevant selections, constraints and calculations and produce a provisional structured answer. No tools, calculator or generated-code execution. It may use internal reasoning, write intermediate calculations in a structured scratch field and apply all provided rules.
2. Fresh review call with the same evidence, question and draft, explicitly check completeness, calculations, temporal ordering, context/reference, citations and abstention; return the final common schema. If draft is malformed, use one bounded repair within budget; no manual intervention.
3. At most three semantic calls (normal two); same output caps as the others. Do not use B's evidence verifier on A's final output; the independent scorer still applies to all arms.

This is stronger than one-shot, vague chat prompting. It is a valid operational reference, not a claim that it is the strongest possible modern model configuration.

### 4.3 C — General-purpose program-assisted LLM (primary comparator)

Use a PAL-style workflow adapted to the common evidence contract, without D2's typed domain tools. In its first call the model writes a self-contained Python script that reads `fixture.json`, applies the documented investigation rules and emits an intermediate JSON object with computed facts, selected/excluded IDs and caveats. Supply examples demonstrating generic JSON parsing, time handling, and writing JSON, with the same task examples as A/B. Python standard library (`json`, `datetime`, `statistics`, `collections`, `math`, etc.) available. No prewritten interval, event or comparator functions from B or gold. The script can implement all needed operations and calculate whatever the question requests. This is not a calculator-only strawman.

Execute the script in an isolated, offline, unprivileged disposable container. Mount only the one fixture and script read-only; no credentials, host filesystem, Docker socket or network; read-only root, dropped capabilities, no new privileges, bounded CPU/memory/processes and wall time, capped stdout; parse JSON. Never run generated arbitrary Python in the main experimental process or rely on regex as a security boundary. Use a prebuilt pinned Python image with non-root user; establish sandbox on development cases before evaluating. Preserve generated code and output. One repair call allowed on script error, invalid JSON or reported schema issue; return diagnostic text only, not gold corrections. Then make a final composition call with the same question, full evidence and execution result (if successful), using the common schema. If code execution cannot resolve the issue, the final LLM may still give supported direct answers or qualify insufficiency; log fallback. C can choose not to run code when a question genuinely needs no computation; it still gets a composition/review call. No oracle hints or manual code changes. Three semantic calls max, including repair.

This comparator is general analysis with same policy text, not a clinical-specific implementation. It might reproduce D2's operations correctly from scratch. If so, a tie is entirely legitimate. It can also benefit from broad expressivity. The purpose is to see whether reliable reusable domain operations and validated bindings are better than generating bespoke logic per question. It is an engineering counterfactual, not a claim to benchmark all text-to-SQL agents or clinical AI.

### 4.4 B — Proposed D2 architecture

1. LLM receives question, scope, manifest, definitions and four tool-family schemas. Emits plan with explicit intent, typed arguments, unique step IDs and dependent references; or explicit clarification/unsupported intent. All allowed scope/defaults injected by runtime, not chosen from invented identifiers.
2. Pydantic validates structural shape; runtime validates authorization, known metric/method, reference/policy binding, operation types, acyclic backward dependencies, scope, source selection and episode definition. Maximum 12 steps (development gate checks this supports all retained task compositions). No arbitrary Python/SQL. Unique-or-clarify event selection and uncertainty policy are actual tool behaviors, not prompt promises.
3. Execute deterministic steps against one immutable snapshot. Return typed results including selected/excluded IDs, counts, denominators, anchor states, limitations and computed facts. Never let model rewrite trusted intermediate values. One plan repair if invalid/incomplete due to validation or runtime error; expected ambiguous evidence is a valid result, not a fault to retry until answered.
4. Build bounded evidence bundle with computed fact IDs internally, source pointers, explicit missingness, policy/reference version and revision bindings. LLM composes common final schema; internal fact IDs may be attached in B-only execution trace and mapped to public source IDs. Verify numeric values, units, intervals and source references against computed facts. Verify explicit status/limitation flags where machine-comparable. This is not a semantic entailment oracle. Reject/flag unsupported claims; keep supported findings, mark partial if appropriate, and explicitly indicate verification failure. Do not replace arbitrary missing content with gold or silently declare an answer fully verified. If third call unused after successful plan, it may be used for one composition correction on verifier failure; otherwise deterministic rejection. Preserve raw and delivered versions. Three semantic calls max.
5. Store question, plan, tool trace, computed facts, selected source revisions, as-of, final result, verification flags. No UI or database deployment is necessary for this artifact-binding behavior.

**Comparability:** A/C/B get equal total maximum calls and per-call output caps; actual token cost and wall time differ by design. The direct model cannot obtain external execution, but C can. B has a designed semantic runtime; C has the same specification and source data but not that reusable runtime. Prompt differences necessary for each architecture are disclosed. No exact token matching or fabricated padding. B vs C tests the domain-specific architecture as a package, not which individual verifier or tool is responsible. No extra arms or ablations unless a separate later claim requires one.

## 5. Dataset: controlled synthetic evidence benchmark

### 5.1 Why this is the correct dataset

The target is **conditional correctness given evidence**, not whether sensors correctly measure people or whether biomarkers predict withdrawal. The necessary test labels are correct source selection, anchor status, interval calculations, comparisons and qualified answers. Those can be independently established on fictional evidence. Creating a known source truth is materially easier than retrospectively adjudicating an unaligned public wearable and hospital record. Randomly pairing real physiology with unrelated clinical events would not provide real physiological-clinical linkage. WESAD is a stress/affect dataset; Synthea generates fictional clinical trajectories; EHRSQL addresses structured EHR querying; ArchEHR-QA contains clinical-note QA, not the required wearable/context history. No combination of them automatically yields gold D2 evidence. They remain relevant to broader Blueprint §4.2/§10 integration and validation, not prerequisites here.

Do not label this benchmark as real AUD/SUD data, representative of disease prevalence, calibrated physiology or an externally validated clinical dataset. Use plausible values for engineering scenarios, not simulated pharmacology or a synthetic disease classifier. A mentor/clinician review of scenario phrasing is valuable for face validity but does not convert the fixture into clinical ground truth. If such review is unavailable, disclose that only engineering face plausibility was assessed. No real patient data or protected data enters the hosted API.

### 5.2 Size and independence

Five development scenarios D01–D05, 25 questions; 24 held-out scenarios T01–T24, 120 questions. Distinct fictional participants, monitoring and historical sequences, evidence composition, anchor times and failure patterns. One scenario per participant. No cross-split copies, offset-shifted clones or questions sharing a generated gold-answer template verbatim. All test questions are semantically distinct requests, not paraphrases counted as extra trials. Twenty-four clusters permit a transparent paired descriptive estimate; this is a capstone budget choice, not a power calculation. Do not interpret 120 questions or 432 outputs as independent patients; only the first 360 outputs contribute to the primary comparison. Fix N before test execution; avoid optional stopping. Development and test generation can share the public schema and policy glossary, not exact scenario graphs or question-answer pairs.

### 5.3 Data construction procedure

1. Create an authored scenario card (fictional patient ID, supervised monitoring setting, day/epoch, available physiology, clinical events, historical reference IDs and relevant constraints). Define source data independent of questions wherever possible. Include straightforward negative findings and meaningful gaps without making every scenario a trap.
2. Construct 30–90 minute target review spans with a few recorded monitoring bouts (typically 2–4 minutes per bout) and explicit source coverage/unknown gaps. Include prior monitoring bouts on 1–3 distinct days within a named historical epoch. This is a compact evidence slice, not a claim of continuous all-day measurement. Some questions target entire span and others bounded subintervals.
3. Generate feature-level rows with simple seeded numeric trajectories/variation; include independently authored quality, actual support, method, contextual movement, source and time flags. Record overlapping accepted feature windows where meaningful. Use minute-scale rows for temperature and selected AC-G features, short windows for ECG and PPG; only per-node IMU has Blueprint's mandatory 10 s/5 s interface. Do not invent a common sample rate or actual raw waveform. For fixture simplicity use 10 s/5 s HR and pulse windows where declared, AC-G 30 s/15 s, skin temperature 60 s/30 s, and IMU 10 s/5 s. These are **test definitions only**, not production feature acceptance decisions. Make reference comparison units non-overlapping for reference statistics. Permit a minority of cases with fractional-only support or unknown clock alignment. Preserve provenance.
4. Provide independent chest and wrist motion summaries/feature-linked context labels (not physiological rest or whole-body activity), named historical references and eligibility annotations following the test policy. Treat reference unavailability separately from comparison status. Provide source rows for prior reference center and status; do not require D2 to reconstruct the actual Bucket 5 service.
5. Write 5–12 clinical assertions per scenario, with original short synthetic source snippets or structured resource fields. Include symptoms/report/assessment and medication order, completed administration, held/not-done, uncertain report, duplicated mentions with supported occurrence links as applicable. Separate documentation from event time. Include at least some no-confounder cases. An event labeled semantically supported in fixture has correct source meaning but remains clinically unreviewed.
6. Freeze one evidence snapshot and associated scope inventory per scenario. Reference source-event cutoff and available-as-of distinct. Include at least two scenarios with revision/as-of alternatives if needed by questions; represent each as two named immutable views and bind each question to one, never blend views. Synthetic source ID resolution points to fixture records or snippets, never pretend to have waveform files.
7. Write five clinician-style questions per scenario after constructing its evidence. Check distribution in §6. Derive independent gold with §7. A different person reviews test questions and answer keys before questions/fixtures are released to the executor; gold remains sealed from it. Freeze hashes and split manifests, including the 24-question repeat-subset manifest (§9.2).

Practical size target: 60–350 feature/context rows plus 5–12 clinical mentions per scenario, typical compact JSON 15–55 k tokens or less after shared metadata normalization. Hard preflight cap: 64k input tokens for the complete canonical evidence plus instructions/examples in A/C, and 96k for full call including draft/code/outputs; B uses same upper caps. Keep IDs and source locators, but use a common schema dictionary instead of repeating long descriptors. If a fixture exceeds the cap, reduce irrelevant monitoring bouts for all arms before freeze, preserving requested evidence and uncertainty. No question-conditioned truncation for only A/C. Measure actual token counts on dev and test input manifests before the first test run. Do not report token estimates as measured usage.

### 5.4 Minimal logical schema

| Table/object | Required fields and semantics |
|---|---|
| `scenario` | scenario/participant/snapshot ID, available-as-of, timezone, authorized review scope, source inventory, synthetic disclosure, definition/policy versions |
| `observations` | observation ID, participant, metric, method, node/site/configuration, value or explicit null, units, nominal `[start,end)`, acceptance enum and reasons, support kind (`intervals`, `fraction_only`, `unknown`), actual intervals or fraction/denominator, timing quality/bounds, linked context IDs, source IDs, feature version |
| `context` | ID, node, nominal/event time, actual support, movement stratum (`low`, `elevated`, `unknown`, `ambiguous`), clock status, source IDs; optional numeric IMU summaries; feature links; optional ambient qualifier where needed |
| `references` | reference ID, policy ID, metric/method/site/configuration, epoch/cutoff, as-of, status (`unavailable`, `provisional`, `supported_descriptive` as supplied fictional state), center and unit, source IDs, non-overlap comparison units/days, optional spread, revision |
| `eligibility` | observation ID + reference ID + policy ID + revision, `eligible/ineligible/indeterminate`, reasons; reference availability separate. Same observation can differ across references. |
| `clinical_events` | mention ID, event type/concept, assertion/experiencer/evidence class/action status, event time bounds and precision, documented_at, occurrence ID/link status, semantic/source/structural review states, original text/source locator; optional contradiction link |
| `source_inventory` | ID, type, locator, record/snippet, source revision, covered/unknown scope, recording availability distinct from acceptance/support. Fake archive or raw data pointers not asserted. |
| `policies` | metric/method compatibility, required node context, explicit named reference applicability, F1 admission, question operation/statistic and denominator semantics, configured episode rules |
| `questions` | question ID, scenario ID/snapshot, natural-language text, authorized selection context; Q class/difficulty/status kept in evaluation metadata, not exposed as gold hints |

Keep source references resolvable inside fixture. Use UTC timestamps with retained local offset in scenario. Use integer seconds for reference implementation calculations; `[start,end)` half-open intervals, no implicit interpolation. `accepted` does not imply full support, low motion or eligible comparison. Zero is valid if supported, null is not zero. Exact clinical point times stored as equal bounds with explicit `instant` precision, distinct from empty intervals. For non-point clinical onset use uncertainty bounds; no automatic use of documentation time. No need to reproduce hardware calibration, raw archive, database migrations, AC impedance conversion or D1 extractor. Preserve their semantics where relevant. Use method `ac_conductance_100hz` for AC-G in µS; never label it DC SCL. Use distinct ECG HR and wrist PPG pulse rate methods. HRV only if an independently specified NN-valid fixture is needed; **exclude from this initial benchmark** to avoid adding an unneeded measurement-validity question. Skin temperature and oscillatory wrist-motion evidence are optional descriptive modalities, not severity scores.

### 5.5 Frozen benchmark-specific operation rules

These remove scoring ambiguity and are not clinical thresholds or new production decisions. Shared policy file available to every arm.

- Observation summaries: median of accepted, method-compatible feature **values** with nominal window fully contained in the selected scope and timing resolved. Do not call this a time-weighted physiological mean. For a comparison, additionally require the selected reference-policy eligibility and reference availability. Return number of values and actual/nominal support as requested, report exclusions and missingness. Partially overlapping windows can contribute clipped coverage, but not to this default summary statistic. Alternative `mean` (non-time-weighted feature values), `list`, `count`, `min`, `max` only when explicitly requested; every operation label indicates its scope. No cross-modality average.
- Coverage: union eligible nominal windows intersected with requested scope; union explicitly known actual support of relevant accepted windows intersected with scope. If any material row only provides fractional or unknown support, do not assert exact total actual duration; report known supported lower bound when justified and identify unresolved part. Denominator is requested wall-clock span unless question explicitly asks for fraction of accepted feature-window coverage; name it. No sampling-rate conversion to continuous support. With no eligible values but known covered observations, report zero qualifying coverage if justified; missing recordings are not negative physiological evidence.
- References: center is supplied immutable Bucket 5 historical median over defined non-overlap units. `provisional` is allowed for explicitly qualified descriptive difference; `unavailable` yields no difference. For eligible target values compute median(target) minus named center, units unchanged; no healthy-normal inference. Do not compute a cross-method or missing-context difference. Do not combine revisions. Use a supplied low-chest-motion ECG comparator and broad ECG comparator where both exist; wrist PPG/AC-G use their own method/site policies. Reference support status is stipulated in fictional data, not derived from invented clinical adequacy cutoffs.
- Episode rule: use configured ID, threshold comparator (e.g., HR >= a fixture-supplied threshold or reference center + supplied offset), admissible feature method/quality/context, minimum grouping span, max gap. Sort nominal qualifying intervals, merge overlapping or touching intervals; group separate intervals only if intervening gap <= configured allowed gap. Retain qualifying union, grouping span and actual valid support (if known) as different quantities. A rejected intervening feature does not contribute coverage; it may only be a grouping gap. Count groups satisfying minimum span, but do not call entire span continuous elevation. Compare recurrence in explicitly specified historical scope with same rule and compatibility; no episodes where observation absent cannot be reported as evidence of absence. Include boundary case of exact allowed gap and just greater gap in development.
- Clinical anchors: only scoped, source-valid and semantically supported assertions with correct concept, experiencer, assertion/action/evidence class can support the requested claim. A completed structured administration is different from ordered, held, uncertain report or unassessed extraction. Group mentions by known occurrence links for counts; do not guess unresolved identity. A named narrative-reported onset remains a reported onset even when precise. Multiple distinct qualifying occurrences require explicit selection (e.g., first documented completed occurrence when requested) or clarification. Contradiction relevant to anchor identity/time must be reported, not silently resolved. For exact numeric event-anchored aggregates require unique point anchors, correct ordering and resolved metric timing. For uncertain anchors, give supported time bounds and possible/certain ordering or partial answer; no exact result over an invented interval. This benchmark selects the Blueprint's allowed abstain/qualify branch rather than implementing full uncertainty propagation. Exact observations wholly inside the guaranteed interval may be described only if explicitly labeled as a distinct supported subpart. If user requests exact onset-to-dose aggregate with onset approximate, no exact aggregate.
- `as_of`: only records visible in the bound snapshot; reference event cutoff independent of available-as-of. No hidden access to a later correction. Saved response references the evaluated snapshot.

## 6. Investigation questions and representative cases

### 6.1 Fixed test composition

Assign each scenario one question from each Q1–Q3 and two Q4; one Q4 question must compose a clinical anchor with at least one physiological/context/reference operation; the second must also combine clinical and physiological evidence or resolve a material barrier to doing so. The distribution below is a benchmark design decision, not an estimate of clinical prevalence.

| Class | Answered | Partial | Insufficient or clarify | Total |
|---|---:|---:|---:|---:|
| Q1 observation and coverage | 16 | 4 | 4 | 24 |
| Q2 named historical comparison | 14 | 5 | 5 | 24 |
| Q3 episodes and recurrence | 14 | 5 | 5 | 24 |
| Q4 chronology and event-anchored multimodal review | 28 | 10 | 10 | 48 |
| **Total** | **72** | **24** | **24** | **120** |

Split last column of statuses into 14 `insufficient` and 10 `clarify` cases across categories; clarify is only for unresolved choice/scope that the clinician could specify, insufficient is evidence that is unavailable/invalid even with the intended scope established. When at least one independently requested subpart is answerable, label `partial`, with the specific remaining limitation/clarification. A partial answer that supplies all supported subparts is a **fully successful** answer in the primary metric. Do not classify a fully supported negative result as insufficient.

Difficulty quotas: 24 foundational (one or two operations with meaningful constraints), 60 compositional (multiple selections and calculations or source classes), 36 complex (event/uncertainty/reference or recurrence joins with at least three material constraints). Assign labels before testing by the required semantic operations, not model failure rates. Q4 cannot be reduced to lookup. Across all cases, explicitly cover at least 12 tasks involving support vs nominal intervals, 12 reference-specific eligibility distinctions, 12 clinically consequential event action/identity/time distinctions, 8 cross-node context/timing cases, 8 method compatibility distinctions, 4 distinct-occurrence versus mention cases, and 4 revision/as-of cases. Overlap expected; these are coverage checks, not extra arms or independent sample counts. At least 12 questions mention more than one physiological metric in addition to the clinical context; not all tasks require every modality. Use ECG HR and wrist pulse most often, AC-G and skin temperature selectively; include at least six AC-G tasks and six PPG-vs-ECG or node-context distinction tasks. Include no unsupported disease score.

Construct questions manually in realistic review phrasing, with varied goals, time expressions and clause order; avoid field-name leakage such as `eligibility == eligible`. For five development scenarios, use paraphrases to test interpretation and prompt robustness; optionally keep a paired alternate wording for six held-out questions as a **separately labeled robustness diagnostic only if approved before freeze**; not part of the fixed 120 or primary result. The fixed protocol needs no extra paraphrase executions. Avoid trivial one-record lookups, needless adversarial prompts and repetitive wording. Questions may include clinically useful negative or inconclusive results; they need not all mention diazepam. Medication event examples do not provide treatment advice.

### 6.2 Representative fixtures and expected findings

These worked examples establish semantics, not test data or measured results. Times use seconds relative to the displayed UTC episode start for readability; real fixtures use UTC timestamps. All unmentioned rows within the stated example are absent; inventories describe whether the scope is known recorded, missing or unknown. IDs are examples. Required facts/limitations and evidence sets are specified explicitly below; actual gold files use the format in §7.

#### Q1 — Distinguish available feature-window coverage from valid measurement support

Question: “Over the first 30 seconds, how much accepted chest-ECG heart-rate evidence was available, and for how much of that interval do we actually have documented usable support?”

| ID | Nominal window | Accepted? | Exact support | HR (bpm) |
|---|---|---|---|---:|
| H1 | [0,10) | Yes | [0,7) | 90 |
| H2 | [5,15) | Yes | [5,12) | 92 |
| H3 | [10,20) | No, artifact | none | null |
| H4 | [20,30) | Yes | [20,28) | 88 |

Gold: nominal union `[0,15) ∪ [20,30)` = 25 s / 30 = 83.33%; actual support `[0,12) ∪ [20,28)` = 20 s / 30 = 66.67%; H3 rejected and gaps remain, do not call entire 25 seconds continuously valid. Source set H1/H2/H4 for both totals, H3 for rejected reason, scope inventory for denominator/coverage gaps. `answered`. Required fact slots: both durations and fractions (with denominator), material exclusion and coverage distinction. If H4 had fraction-only support, 20 s exact union would be unjustified; report 12 s known exact geometry and unresolved contribution rather than fabricating overlap; `partial` if nominal still answerable.

#### Q2 — Same accepted observation, different comparator eligibility

Question: “Compared with this patient's earlier low-chest-motion ECG HR reference, what is the typical HR during the review bout? Would the same accepted values all be usable if I instead used the broader ECG comparator?”

| ID | HR | Chest/wrist motion | Narrow R1 | Broad R2 |
|---|---:|---|---|---|
| H5 | 94 | low/elevated | eligible | eligible |
| H6 | 100 | elevated/low | ineligible | eligible |
| H7 | 90 | low/low | eligible | eligible |
| H8 | 96 | unknown/low | indeterminate | eligible |

All accepted, time-resolved, non-overlapping full-support ECG windows in scope. R1 = 78 bpm, earlier low-chest-motion epoch, provisional; R2 = 82 bpm, same compatible method broader policy, supported descriptive. Gold: R1 eligible H5/H7, median 92 bpm, +14 bpm vs R1, provisional descriptive reference; H6 excluded by chest motion, H8 indeterminate; wrist motion does not automatically invalidate H5. All four eligible for R2 under its explicitly broader policy; no silent substitution. Broad median/delta is not requested and need not be emitted; if emitted correctly, median 95 bpm and +13 bpm vs R2. Required references H5–H8, R1/R2 and their eligibility/context IDs. `answered`. Alternate partial variant: R1 unavailable, R2 still supported; do not report R1 difference; report only requested R2 eligibility.

#### Q3 — Feature-defined episodes, grouping versus observation, historical recurrence

Question: “Using rule E1, how many elevated ECG-HR groups were identified in this 60-second interval, what was their qualifying-window coverage versus grouping span, and did the same rule identify a comparable group in the earlier recording?”

E1: accepted ECG HR >= 95 bpm, low chest motion, minimum grouping span 15 s, maximum gap 5 s, full timing support. Fixture values are engineering settings, not clinical thresholds. Target: E11 `[0,10)` 99 bpm; E12 `[5,15)` 97; E13 `[20,30)` 96; E14 `[40,50)` 98; E15 `[50,60)` 90. All accepted, low chest motion; exact support equals nominal in this example. Earlier comparable interval: P1 `[0,10)` 98; P2 `[10,20)` 97, full support; inventory covers the relevant historical scope. Gold: `[0,30)` one qualifying group (5 s gap grouped), nominal union 25 s, actual support union 25 s, grouping span 30 s, coverage fraction 25/60 = 41.67% of requested target period **for the retained group**. E14 is an isolated candidate of span 10 s, fails minimum; E15 below threshold. Prior one qualifying group span/coverage 20 s. E11–E15, P1/P2, E1, context/scope IDs; historical comparator as applicable. No claim of 30 s continuous elevated HR or withdrawal episode. `answered`. If prior coverage unknown/absent, recurrence cannot be excluded; target remains answerable and result `partial`. If grouping gap is exactly 5 s it is included; a 6 s gap creates separate candidate groups.

#### Q4 — Clinically anchored combined investigation

Question: “Between the patient's reported onset of tremor and the documented completed diazepam administration, what was the accepted low-chest-motion ECG HR compared with the named earlier reference, and what supported wrist AC conductance was observed?”

Clinical source/event evidence: C1 patient report says onset at 09:00, documented 09:45, semantic support established, occurrence RPT1; C2 order at 09:05; C3 held at 09:10; C4 structured completed administration at 09:30; C5 later note explicitly refers to the same C4 administration; C6 uncertain report of a dose at 09:15. All are synthetic, not clinical instructions. Time-resolved features wholly in [09:00,09:30): H9 HR 96 (low chest motion), H10 HR 92 (low), H11 HR 110 (elevated chest motion), H12 rejected; H9/H10 eligible under R3, H11 ineligible. R3 historical compatible low-chest-motion median 80 bpm, supported descriptive. Wrist G1=2.5 µS accepted 100 Hz AC-G, G2=3.5 µS accepted same site/method, G3 rejected contact. Each feature has full supported own nominal window; sparse bouts, no full-interval coverage claim. Gold: reported onset at 09:00 and completed administration 09:30, 30-minute review interval; order/held/uncertain use are not completed anchors, duplicated mention not second occurrence; HR median 94 bpm from H9/H10, +14 bpm vs R3, excluded H11/H12; wrist AC-G median 3.0 µS from G1/G2, G3 excluded, sparse accepted evidence; no treatment-effect inference. Cite C1/C4, C2/C3/C5/C6 for any exclusion/identity claims, eligible physiology/context/eligibility IDs and R3, G1/G2/G3 and inventory. `answered`. Require clinical and physiological facts, methods, reference, both values, source grounding and limitations; do not accept a correct number for the wrong anchor.

#### Q4 — Uncertain/ambiguous anchors and answerability

Question: “What was the exact average HR between onset and completed administration, and what did the patient report about symptom onset?” Same C4, but C1 says “started sometime between 08:50 and 09:10,” documented 09:45. The question asks exact event-bounded result, not an estimate. Gold: reported onset bounds [08:50,09:10], source C1; documented completed C4 at 09:30 can be named if helpful; no exact interval or HR mean because onset uncertain (even if HR data exist). `partial`. The request for average uses a mean rather than default median; had exact anchors existed, operation must support explicitly requested mean of eligible fully-contained feature values or explicitly reject it if not defined; implement mean of feature values in this benchmark and label non-time-weighted. A separate variant asks only “Compare HR before and after the administration” with two distinct supported completed administrations and no selection/default: `clarify` which occurrence; cite both. Another variant with only order/held/not-done records and no completed administration: `insufficient`, cite those and the clinical inventory, do not anchor to order or imply no medication was ever given. No extra question class is necessary for these cases.

#### Cross-modal method incompatibility and negative finding examples

Q2: an accepted ECG HR and an accepted wrist PPG pulse rate with the same numerical value do not make a wrist observation eligible for the ECG historical reference; if only the ECG comparator is supplied for wrist pulse, no requested personalized delta. `insufficient` if only that delta requested. AC-G cannot use a DC-SCL reference. Q1/Q3: a fully represented review interval containing accepted values below the configured threshold supports “no qualifying group under rule E1 in that interval”; missing interval coverage does not support “no elevation occurred.” Include both types without conflating answerability.

## 7. Independent ground truth

### 7.1 Separation of roles and artifacts

The benchmark author and independent reviewer should be different people (e.g., two project teammates). One prepares the scenario/source rows, question and human-readable reasoning worksheet. Another derives or checks the answer from the frozen evidence and policy, without running B or seeing its plans/outputs. Resolve disagreements, correct fixture ambiguity and record revision history **before** any test execution. A clinician/mentor may review phrasing and material clinical source semantics; engineering reviewers can independently verify arithmetic and recorded assertion semantics but must not be described as clinicians. If a second reviewer cannot be obtained, run only as an explicitly single-annotator preliminary engineering test, not the recommended final IDF comparative evidence; disclose this dependency.

Independence means no imports from `systems/d2` in gold code or scorer, no reuse of B's selection/interval functions, no using B's computed fact IDs as gold, no LLM as unquestioned annotator or judge. An author may use spreadsheets or simple independent scripts. Freeze source facts before question answering. Do not choose only cases where B's design looks advantageous.

For arithmetic, use a **separate reference oracle**: integer-second occupancy sets (or boolean grids) for coverage/episode checking on these small integer-time fixtures, independent hand-selected row lists and `Decimal`/spreadsheet medians/means for numeric results; do not reuse production sweep-line/interval implementation. For episode grouping, independently derive contiguous qualifying runs from second-level masks, inspect gap lengths, then map back to source IDs. Document exact support unavailable cases manually. For event and reference selection, independently annotate IDs, exclusions, time and scope, rather than let the oracle implement B's policies verbatim. For mixed-support totals, annotate known lower bound and missing geometry. Spot-check reference oracle outputs with hand-worked examples and boundary cases. No need to duplicate an entire D2 engine.

### 7.2 Gold record per question

```json
{
  "question_id": "T07-Q4a",
  "snapshot_id": "T07-v1",
  "class": "Q4",
  "difficulty": "compositional",
  "status": "answered",
  "required_slots": [
    {"id": "anchor_end", "kind": "event", "expected": {"occurrence_id": "C4-occ", "time": "...", "status": "completed"}, "evidence_alternatives": [["C4"]], "material": true},
    {"id": "delta_hr", "kind": "numeric", "expected": {"value": 14, "unit": "bpm", "reference_id": "R3"}, "abs_tol": 0.1, "evidence_alternatives": [["H9", "H10", "R3", "E9", "E10"]], "material": true}
  ],
  "required_limitations": [],
  "permitted_additional_facts": [],
  "forbidden_inferences": ["medication efficacy", "order is completed administration"],
  "selection": {"included_ids": [], "excluded_ids_with_reasons": [], "anchor_candidates": []},
  "worksheet": "gold/worksheets/T07-Q4a.md",
  "review": {"author": "reviewer-id", "checker": "other-id", "resolved": true}
}
```

Illustrative incomplete record; actual gold explicitly lists each required independent fact, including denominators, units, limitation/status and all needed evidence sets. The scorer treats alternative sufficient evidence sets as valid (one set must be fully supported; redundant correct extra sources permitted, misleading sources penalized). Accept source ID aliases only through a frozen resolver that maps to the same record/span. For derived aggregates, require all contributing observation IDs plus material reference/eligibility/anchor evidence, or an existing fixture manifest ID that unambiguously resolves to exactly those records and carries appropriate scope. Do not create B-only answer manifests as a gold shortcut. Compact citations can be ID lists rendered in expandable form later; this experiment stores raw IDs. Exclusion reasons need citations when material to answer; do not require every rejected row where not necessary. Gold does not prescribe exact phrasing or exact plans. Equivalent methods (mean vs median only when expressly the same by definition/value and requested statistic preserved) are allowed if all result semantics match.

Gold status and limitations: `answered` when all requested subparts are determinately supported; `partial` for supported subparts plus identified unmet request; `insufficient` where fixed intent lacks evidence; `clarify` where multiple permissible selections or unspecified required rule cannot be resolved. Store expected clarification target, plausible candidate IDs and required absence/uncertainty reason, not only status.

### 7.3 Review, sealing, and leakage control

All 120 test gold records checked by second reviewer, including every numerical calculation, evidence set and answerability label; sign off before execution. Aim for 3–8 required atomic slots per question (more only if genuine subparts require them); do not split a single number into many scoring points to inflate results. Questions that do not have unique answer semantics are rewritten or given explicit admissible alternatives at this stage. Develop on 25 dev questions only. Split at scenario/participant level, freeze `sha256` of fixtures, questions, gold, policies, prompts, common schemas, repeat-subset manifest and commit ID. Keep gold outside LLM prompt builder/execution paths and code sandbox mounts; only evaluator reads it. Test author/reviewer can provide schema and coverage targets, not reveal answer keys to prompt tuning. Run a leakage audit on examples. No test-based prompt or algorithm tuning; genuine discovered gold defect documented, adjudicated blind to arms, rescored uniformly with original results retained; substantial design error requires a new labeled protocol and fresh held-out benchmark, not silent deletion.

## 8. Final evaluation metrics and scoring rules

### 8.1 Primary: strict grounded investigation success (SGIS)

For each question q, arm a, execution r, binary `S_aqr = 1` exactly when all of the following hold:

1. Global answerability status and substantive handling match gold (including answering supported subparts and correct clarification/limitation).
2. Every required fact/limitation slot is correct in meaning, value, unit, method, temporal/reference/denominator qualifiers as applicable and sufficiently grounded in admissible source evidence.
3. No additional material false, unsupported, scope-violating or materially misleading assertion is delivered; no material contradiction with structured values; no consequential inference prohibited by the evidence rules.
4. Response is valid and usable, not a timeout, unresolved malformed output, empty response or generic refusal. A specific gold-matching insufficiency/clarification is usable, not a failure.

Otherwise S=0. Partial-credit answers do not receive strict success, but their correctly delivered slots count in secondary recall. A gold-partial answer that fully satisfies the expected partial response gets S=1. A fabricated source ID is a material error even if its number happens to match. Correct calculations from wrong clinical event or wrong reference fail. Structural validation alone never awards success. Style/grammar not scored unless it changes meaning.

For N=24 scenarios, five questions each, use only primary executions (`r=1`):

`S_a = (1/N) * sum_i [(1/5)*sum_q_in_i S_aq1]`.

Report percent and raw successful outputs out of 120 per arm; equal scenarios make this equal to pooled output proportion. This measures the probability of a correct complete answer in the controlled design; it is stringent by intent. Primary improvement `100*(S_B - S_C)` percentage points; secondary `100*(S_B - S_A)`. No gold answer selection based on model outputs.

### 8.2 Secondary endpoints

All main-table and category rates computed on final delivered answers from the 360 primary attempts only (120 per arm); repeat-subset responses are scored by the identical rubric but summarized separately. In each formula below, the summation and denominator refer only to the indicated primary attempts for the arm being evaluated; failures count as omissions except precision where denominator is emitted claims. Required limitations are treated as slots for recall. Preserve raw numerator/denominator and distinguish non-applicable.

| Metric | Definition, denominator and handling | Meaning |
|---|---|---|
| Required grounded-fact recall (RGFR) | `sum correct AND sufficiently grounded required slots / sum all required slots` over all primary questions q (r=1). Include required limitations/clarification reason. Missing, wrong and unsupported slot = 0; one slot credited once. Report micro rate and scenario-averaged rate as descriptive check. | Partial correctness and completeness; prevents rewarding terse answers. |
| Required numerical correctness (RNC) | `sum correct required numeric slots / sum gold-required numeric slots` across all primary questions q (r=1); omissions = 0. Numeric slot requires correct unit, method, interval, reference, statistic and denominator, but source sufficiency is separately scored in RGFR. No slot when no numerical answer is expected; invented numbers count as unsupported/consequential claims. | Correctness of values and their meanings; not standalone success. |
| Grounded-claim precision (GCP) | `sum supported emitted atomic material claims / sum emitted atomic material claims`; includes additional facts and specific limitation assertions. A true number with absent/insufficient evidence is not grounded. Wrong source/action/negation fails. Deduplicate repeated claims within output. Empty output has no claim denominator; report count of zero-claim responses and do not define it as perfect. | Attribution and unsupported claim control. Unsupported claim rate = 1−GCP; report as complement, not independent metric. |
| Answerability handling accuracy (AHA) | `sum correct status AND correct handling / (N*5)`. For answered: provides at least one requested supported finding and does not falsely abstain; other missing facts caught by SGIS/RGFR. For partial: provides at least one supported finding, specifies every material unmet request/reason, no invented answer to unresolved part. For insufficient/clarify: specific valid reason or clarification target with no fabricated resolved answer. Invalid/empty/failure = 0. Also confusion matrix of expected vs delivered status (fail separate). | Appropriate abstention and avoiding over-abstention; never rewards always saying insufficient. |
| Consequential-error incidence (CEI) | `sum I(response contains >=1 predefined consequential error) / all delivered-or-attempted responses`. Predefined list below; empty/timeout counted separately as failures, not fabricated claims. Report rate alongside SGIS and failure count; abstention cannot establish superiority via CEI alone. | Exposure to clinically material evidence misrepresentation in this simulation, not patient harm. |

Strict success is the sole primary outcome; secondary metrics diagnostic, no multiplicity-driven significance claims. Do not introduce BLEU, ROUGE, embedding scores, or a generic judge rating. Latency/token overhead: engineering diagnostics only (see §9). B plan valid/executable rate and verifier rejection counts are **B-only debugging metrics**, not comparatives. Include first-attempt and final status; no requirement for exact gold plan because multiple valid plans exist.

**Consequential error taxonomy (predefined):** (E1) wrong participant/snapshot or fabricated source; (E2) incorrect action/assertion/occurrence status or unsupported precise anchor; (E3) missing/rejected measurements represented as valid/normal or nominal interval represented as continuous supported physiology; (E4) incompatible/unknown reference eligibility or method conflated, false normality; (E5) wrong denominator, wrong clinically anchored scope or substantial numeric/episode claim beyond tolerance that changes interpretation; (E6) causal/treatment/diagnostic conclusion not established by source. A wrong numeric answer within the correct descriptive frame beyond tolerance counts as strict failure regardless; mark E5 only if it changes the stated category, direction, existence/count, or materially reported coverage/comparison (pre-label material numeric slots in gold; for those any beyond-tolerance discrepancy counts). Ordinary incomplete answer is omission, not automatically consequential error. Multiple tags allowed, one primary root cause assigned by earliest observable failure (scope/anchor → selection → calculation → answerability/composition → formatting/execution). Distinguish runtime errors from unsupported statements.

### 8.3 Exact numeric tolerances and normalization

| Quantity | Rule |
|---|---|
| Event IDs, occurrence IDs, status, order, method, reference and revision | Exact semantics; equivalent source alias only via frozen map |
| Integer counts | Exact |
| Time endpoints and integer-second duration | Exact UTC normalized seconds; equivalent minutes accepted if exactly converted; if a rounded decimal minute is explicitly used, convert and require within 0.5 s; uncertainty bounds both correct |
| HR/pulse rate, descriptive difference | Absolute error <= 0.1 bpm |
| AC-G and difference | <= 0.01 µS; preserve 100 Hz AC method |
| Skin temperature | <= 0.05 °C; correct temperature type and conversion |
| Fractions/percentages | <= 0.5 percentage points; denominator and coverage type exact; seconds/counts independently checked |
| Other descriptive values if approved in schema | Predeclare unit-specific tolerance before freeze; no post-test tolerance adjustment |

Use common canonical units and compare converted numeric fields. Do not penalize conventional rounding within tolerance, but do not accept a rounded claim that flips threshold classification or changes sign where interpretation depends on it. Exact zero, missing/null and negative evidence distinct. Episode grouping span, qualifying-window union and actual support are separate slots, not exchangeable. Comparison to R1 versus R2 fails even if values coincidentally match. If metric is stated as mean vs median incorrectly, slot fails regardless of numeric equality. Numeric accuracy does not grant credit for invalid clinical scope.

### 8.4 How to score reliably without an LLM judge

Use typed fields and deterministic normalization for numerical values/units/status/IDs. Human evaluators inspect claim text, evidence snippets/rows, required qualifier and limitations. The automated check can suggest matches but cannot decide clinical semantic support; a real pointer alone is not enough. Each final answer gets a blinded review with arm label and execution trace hidden; randomly shuffle outputs, retain question/gold/source view. The reviewer maps one claim to required slots or additional fact, marks correct/unsupported/contradictory, checks citation sufficiency and codes errors. Split compound claims to atomic material claims, deduplicate; do not let systems self-label correctness. Optional true extra information must be source-supported, otherwise precision/strict success affected. Use frozen gold and explicit rubric; if two valid answer phrasings emerge, accept both. A second reviewer independently scores a stratified random 20% of the 360 primary outputs (72), plus 15 of the 72 reproducibility outputs (rounding up 20%), for 87 scheduled second reviews. Sample within each execution cohort, balanced across arms/classes/status as feasible, and include randomly selected failures, plus all material ambiguity/disputed consequential errors beyond the scheduled sample. Record binary SGIS agreement and raw agreement by claim category (Cohen's kappa for SGIS optional if both classes present); adjudicate before unblinding. If material disagreement reveals a systematic rubric ambiguity, clarify uniformly and rescore affected cases across arms. Report second-review fraction, disagreement and resolution. All gold records independently reviewed as §7, even if not all outputs double-reviewed. Human grading workload is real: 432 short structured outputs, roughly 2–4 min each as an unmeasured planning estimate (14.4–28.8 reviewer-hours), plus 87 scheduled second reviews (approximately 2.9–5.8 additional hours at that assumed rate), dispute resolution and gold preparation. This is a 40% reduction in response volume compared with v1.0, not a measured time saving. Allocate team effort; do not substitute an LLM judge to make the workload look smaller.

## 9. Reproducible execution and analysis

### 9.1 Model and budgets

Select **one capable, version-pinned hosted LLM during development preflight**; no exact model ID is mandated in v1.1. The earlier GPT-4.1 choice is not binding. Confirm actual account access and lifecycle suitability, structured-output support for the shared answer and D2 plan contracts, ability to generate Python for C, adequate context for the common caps, sufficient usable output budget and affordable quota/pricing. Use official model and structured-output documentation [R13,R14] for the candidate and verify with real development API calls; no credentials, availability or actual API behavior have been tested in this revision. Do not choose a deliberately weak baseline or select a model based on favorable B−C results. Select and record the exact provider/model/version and accepted settings before held-out freeze, run all dev gates across all arms using that configuration, and do not mix versions or substitute models mid-test. Prefer temperature 0 and top_p 1 where supported; if a model does not expose these controls, omit unsupported parameters and document the actual defaults. Fix any applicable reasoning-effort setting identically across arms. Use max 4,096 output tokens per semantic call (up to 12,288 per question/arm) where supported; verify on development that reasoning-token accounting, if applicable, leaves sufficient usable output for all workflows. If a common cap must change, document and approve the same revised cap for all arms before freeze. No web or provider-specific hidden external tools, no conversation history across queries. Record all provider-specific settings including if seed unavailable; do not assume temperature zero means deterministic. The final common response is concise; cap 12 findings and 8 limitation entries only if dev demonstrates no necessary omission; otherwise remove the item caps for every arm before freeze, retaining token cap. B's evidence bundle has max 24k input tokens of computed data; if exceeded, compact common IDs/arrays losslessly or declare execution failure, never silently omit relevant evidence. C script stdout cap 1 MB and at most 24k tokens passed as execution result; require compact JSON and use same rule. Full call cap 96k input, including all evidence, instructions and history. No per-arm arbitrary shorter cap.

Development gates: same API model successfully outputs strict schemas; all 25 dev questions executable in B with **manually written correct plans** (unit/integration gate only, not benchmark score); no unsupported required operations; fixtures fit common caps; generic code runner executes independent reference-like sample scripts and errors safely; both baseline prompts include task examples and domain policies and receive comparable refinement. Ensure direct prompt does not systematically omit sources due to formatting, C can implement interval unions and anchor selection, B verifier rejects fake facts but permits supported descriptive content. Use dev outcomes for bounded refinement, not a mandatory target score. If every arm scores near ceiling, improve diversity/realism on development scenarios and design test distribution **before** freeze, not artificially difficult arithmetic or intentional baseline degradation. If B cannot support a legitimate selected question, repair implementation against blueprint before freeze or narrow explicitly unsupported operation in all arms; don't drop bad questions after test.

### 9.2 Schedule and failure rules

**Primary cohort:** one independently initialized execution of each of the 120 questions in each of the three arms (360 attempted answers; 120 per arm). **Reproducibility cohort:** select exactly 24 of the held-out questions before any test execution, one from each scenario, covering all four Q classes and all four answerability statuses, with a mixture of difficulty levels. Aim for a roughly proportional distribution (approximately 5 Q1, 5 Q2, 5 Q3, 9 Q4); the actual selection is constrained by the authored questions and must be documented before freeze. Select using question metadata only, without access to model outputs, using a fixed seeded procedure or reviewer-approved selection; store selected IDs, class/status/difficulty counts, rationale and hash in the repeat-subset manifest. If coverage is not feasible, resolve the question distribution before freeze. Independently execute every selected question a second time in all three arms (72 additional answers; 24 per arm). Total planned test attempts: 432 (144 per arm). No reuse of previous output or cache at application layer. Use a deterministic seeded randomized order of question-arm tuples within each cohort, interleave arms across time to reduce provider drift, and run the repeat cohort after the complete primary cohort without modifying model, prompts, code, data or scoring. Label cohorts explicitly in logs. Record run ID, start/end UTC, provider response ID, request/response, prompt/config hash, model returned, token counts (input/output/cached if available), retries, plan/code, tool trace, raw answer, delivered answer, exception, latency and source revisions. Provider caching may occur; log rather than assume identical latency. Use fixed concurrency (e.g. sequential execution initially; if needed, three concurrent requests shared across arms with same scheduler), record actual. No manually retrying just bad model answers.

Transient transport errors (429, 5xx, network timeout) permit up to two identical transport retries, exponential backoff 1/2 seconds or provider retry-after, with no new semantic feedback. These are not free new attempts for bad answers. Count API refusal, truncation, semantic malformed schema, invalid plan/code and verifier failure under normal call budget; one bounded repair only as defined by arm. If entire run fails after transport retries mark failure (status `execution_failure` in evaluator, strict/recall zero), retain attempted denominator. Report provider failures separately. If service outage prevents comparable execution, resume remaining predetermined tuples once service returns; if sustained model-version change, abort protocol, disclose and start new version rather than combine. No dropping hard queries or selecting best of repeats. Retain all 360 primary attempts in the main denominators, and all 72 repeat attempts in the separate diagnostic denominators. Never average repeat outcomes into the primary results. For each arm report strict success on the same 24 selected questions in the first and second execution, raw agreement/disagreement counts (`sum I(S_aq1 != S_aq2) / 24`), and success-to-failure/failure-to-success transitions. Include failures under the same rules and report any provider issues. The paired subset is a limited reproducibility check, not an independent test cohort or a precise stochastic distribution estimate.

### 9.3 Paired scenario-level analysis

For each scenario i calculate `d_i = mean_q(S_Biq1 − S_Ciq1)`, retaining the first execution of the same five paired questions only. `Delta = mean_i(d_i)`. Repeat for B−A. Bootstrap **scenario IDs** with replacement (10,000 resamples; fixed seed 20261125), each time include all five paired primary questions and calculate mean difference; percentile 2.5/97.5 limits in percentage points. No resampling individual output rows as independent; N=24 clusters. This is a descriptive uncertainty/sensitivity measure conditional on an authored benchmark, not a probability sample of patients. With small N and possible ceiling effects, interval can be unstable/degenerate; report per-scenario differences (number B>C, B=C, B<C, min/max), no definitive population inference. Do not use unclustered McNemar on 120 paired primary outputs or present a naive binomial CI as independent patients. No confirmatory p-value or power claim needed. If mentor requires formal hypothesis testing later, pre-specify a separate adequately powered design; this one reports effect sizes and uncertainty. Category and secondary endpoints report numerator/denominator, no extra significance testing. Optional scenario cluster bootstrap for main secondary B−C contrasts with denominator recalculated for sampled clusters; if zero denominator mark undefined. No multiplicity-based cherry-picking.

Interpretation prespecified: if B−C point estimate positive and descriptive interval excludes zero, report clear observed advantage on this benchmark, explicitly conditional on the fixture construction. Positive estimate with interval crossing zero: suggestive but uncertain. If B−A improves but B−C does not, evidence supports advantage over direct prompting, not incremental advantage over general-purpose program assistance. If both near ceiling, report no demonstrated incremental correctness at this task distribution and compare measured overhead without claiming it is lower. If B worse, report bottlenecks; no post hoc tuning used as final results. Relative failure reduction `(1-S_C - (1-S_B))/(1-S_C)` is optional if baseline failure >0; show absolute percentage points first, undefined at perfect baseline, no percentages without raw denominator. No preset arbitrary required accuracy or guaranteed improvement.

### 9.4 Engineering overhead

Measure elapsed wall time from first request to final result including local execution, verification and repairs; record total input/output tokens across all calls, retries and cache metadata where returned. Summarize median, IQR and p95 latency for successful and all attempted tasks (label timeout caps), mean and total tokens per arm, number of semantic calls and repair rates. API cost only if actual billing/pricing at run time documented; not a primary result. 432 test answers (360 primary + 72 repeat) imply 864 normal semantic calls if all workflows use two, with at most 1,296 under 3-call budgets plus transport retries (1,080 primary and 216 repeat maximum). One complete dev execution entails 75 attempts across three arms; additional iterative dev use is separately logged. Report primary overhead separately from repeat-cohort overhead, and total actual resource consumption including development separately for budgeting. This is bounded but not zero-cost. Confirm quota, token budget and reviewer availability before execution. Do not falsely claim API prices or benchmark duration measured. Record actual fixture token distributions. If cost is a blocker, obtain approval to revise protocol before opening test; do not silently reduce only one arm or use weaker models. A standalone experiment still needs API access and secure C runner.

## 10. Minimum implementation and repository organization

Use Python 3.12, Pydantic v2, hosted API SDK, pytest, NumPy for bootstrap and Matplotlib for plots. Pin exact dependency versions in a lockfile at development start. JSON/JSONL fixtures and CSV scores suffice; no Kafka, RADAR-base, MinIO, PostgreSQL, frontend, model training, embeddings, LangGraph or local GPU. C's isolated execution container is solely a benchmark comparator and **not a new component of the proposed clinical system**.

```text
llm-d2-experiment/
  README.md
  pyproject.toml / lockfile
  configs/protocol.yaml
  configs/definitions.json
  data/dev/{fixtures,questions}/
  data/test/{fixtures,questions}/
  data/manifests/{splits,hashes,repeat_subset}.json
  gold/{dev,test,worksheets}/
  prompts/{common,direct,program,d2_plan,d2_compose}/
  src/
    schema.py                 # common observations/events/outputs
    evidence_store.py         # immutable scoped snapshot and source resolution
    model_client.py           # pinned configuration, retries, structured generation
    systems/
      direct.py
      program.py
      sandbox.py              # isolated runner, no access to gold or credentials
      d2/
        plan.py               # typed steps + dependent result validation
        observations.py       # quality/method/context/reference-aware retrieval
        intervals.py          # union, scope, episode, historical comparison
        events.py             # F1 clinical evidence admission and anchor resolution
        resolver.py           # source pointers
        bundle.py             # typed facts, limitations, revision binding
        compose.py
        verify.py             # numeric/source checks + explicit rejection
    runner.py                 # paired execution, seeded schedule, resume
  evaluation/
    gold_oracle.py            # independent occupancy sets/manual selected records
    gold_validate.py
    normalize.py
    blind_export.py
    score.py                  # structured checks + human-review import
    aggregate.py
    plots.py
  tests/{unit,dev,security}/
  runs/<experiment-id>/{manifest,raw,delivered,traces,usage}/
  results/<experiment-id>/{annotations,scores,summary,figures}/
```

Start with the schema-first gate in §4.1, including versioned common answer and gold contracts, before creating development fixtures. Keep gold outside system imports and unavailable to provider prompt builder. Do not include API keys or generated scripts with access to credentials. Runtime receives only authorized snapshot from the harness, not arbitrary participant IDs. Unit tests ensure scope mismatch, invalid method/metric, stale reference, malformed interval, wrong dependency result type, cycles and forward references fail safely. Include synthetic evidence source resolution tests (valid ID wrong meaning must not be regarded as verified), independent coverage/episode examples, clinical action-state/occurrence/uncertainty tests, unavailable/provisional reference cases, as-of consistency and sandbox resource isolation.

### 10.1 D2 minimal tools and input/output types

| Tool family | Required sub-operations | Typed result |
|---|---|---|
| `query_clinical_events` | Filter concept/type, assertion, experiencer, evidence class, action state and time; select unique supported or explicit first/last occurrence; group known occurrences; report candidate/contradiction/uncertainty states | `EventSelection`: selected/candidate mentions/occurrences, exact or bounded time, action/assertion state, semantic support, sources, limitations |
| `query_observations` | Scope by metric/method, interval reference, quality, context and explicit reference-policy; preserve accepted vs eligible vs excluded; fetch context and support | `ObservationSelection`: rows, exclusions/reasons, scope, support/clock status, reference binding, source IDs |
| `analyze_intervals` | Between anchors, fixed relative time before/after supported anchor, interval intersection/union, nominal and exact support coverage, feature-value mean/median/min/max/count, compare named reference, configured episode grouping/recurrence, merge compatible findings from multiple modalities without conflating methods | `IntervalResult`, `AggregateResult`, `ComparisonResult`, `EpisodeResult` carrying typed values/units, denominator, selected IDs, limitations and dependency IDs |
| `resolve_evidence` | Resolve IDs to fixture records/snippets, source inventory, revision/locator | `ResolvedSource`: source type, content, locator, revision and scope status |

For an event-bounded query with two modalities, a typical plan has steps: onset and completed administration selections → exact anchor interval or unresolved status → separate ECG and AC-G selections → ECG comparison and AC-G descriptive summary → evidence resolution as needed. Steps reference typed results, not LLM-copied timestamp or numeric strings. If anchor resolution fails, dependent exact calculations return blocked with reason; unrelated supported subparts may still run. `query_observations` must never silently change selected reference. Tool operations have discriminated input unions and explicit allowable defaults. Evidence bundle includes computed facts and source IDs; result-to-public-claim verification checks method/interval/value/unit/reference where applicable, not just existence of any matching value. Retain internal fact ID mapping; verifier should never award itself benchmark credit. It may block factual claims not tied to matching computed results, while valid narrative limitations use clinical/source evidence checks. No claim of full semantic verification.

### 10.2 Minimal prompt specification

`common`: describe scope, full definitions (§5.5), allowed tasks, source meaning, insufficiency/clarification, output schema; same examples and labels on all systems. Examples demonstrate both ordinary and blocked comparison, not test-specific records. `direct`: provisional findings and independent evidence-based review; `program`: generate general analysis script and consume runtime result; `d2_plan`: compile natural-language intent into typed steps and clarify unsupported bindings; `d2_compose`: use only computed bundle and source-supported facts, preserve limitations and do not add uncomputed numbers. System-specific examples show syntax only and convey no additional domain facts. Freeze exact prompts after development review; log SHA-256 and runtime version. Avoid prompt hacks that encode expected test questions or disallow baseline access to relevant facts.

### 10.3 Execution commands to implement (interface proposal, not existing code)

```bash
python -m evaluation.gold_validate --split dev
pytest tests/unit tests/security tests/dev
python -m src.runner --split dev --arms A,C,B --repeats 1
# freeze prompts, schemas, definitions, test manifests (including repeat subset) and gold independently
python -m src.runner --split test --arms A,C,B --cohort primary --repeats 1 --seed 20261125
python -m src.runner --split test --arms A,C,B --cohort reproducibility --question-manifest data/manifests/repeat_subset.json --repeats 1 --seed 20261125 --run RUN_ID
python -m evaluation.blind_export --run RUN_ID
# import reviewed annotations after independent scoring
python -m evaluation.score --run RUN_ID --annotations REVIEWED_JSONL
python -m evaluation.aggregate --run RUN_ID --bootstrap 10000
python -m evaluation.plots --run RUN_ID
```

The exact CLI naming may change without changing methodology. Both test cohorts belong to the same run manifest, with distinct tuple identities and a shared frozen configuration; the reproducibility command represents the second independent execution of selected questions, not a repeat of the entire primary cohort. Implement resume by immutable scheduled tuple IDs, not by reattempting failures. Preserve versioned raw results even when post-verification delivered answer differs. Do not implement the entire seven-bucket architecture for this benchmark. Actual upstream adapter compatibility and physical integration remain separate Blueprint validation layers.

## 11. Results and IDF presentation

### 11.1 Main results table (blank until experiment)

| Measure | A direct | C general program-assisted | B D2 | B−C (pp or stated unit) | B−A (pp or stated unit) |
|---|---:|---:|---:|---:|---:|
| **Strict grounded investigation success** | — /120 | — /120 | — /120 | — [95% descriptive interval] | — [95% descriptive interval] |
| Required grounded-fact recall | — | — | — | — | — |
| Required numerical correctness | — | — | — | — | — |
| Grounded-claim precision | — | — | — | — | — |
| Answerability handling accuracy | — | — | — | — | — |
| Consequential-error incidence (lower better) | — | — | — | — | — |
| Execution failure count (lower better) | — | — | — | — | — |

Main table uses only the 360 primary attempts (120 per arm). Include raw numerator/denominator for every rate (varying claim/slot denominators are not interchangeable). For lower-is-better rows use signed differences and label direction. No dummy percentages or sample chart presented as evidence.

### 11.2 Category and failure analysis

| Question class | Distinct questions / attempts per arm | A strict success | C strict success | B strict success | B−C pp |
|---|---:|---:|---:|---:|---:|
| Q1 | 24 / 24 | — | — | — | — |
| Q2 | 24 / 24 | — | — | — | — |
| Q3 | 24 / 24 | — | — | — | — |
| Q4 | 48 / 48 | — | — | — | — |

Use primary executions only for the category table, status-wise confusion counts and answerability rate; especially partial and unanswerable. Include a compact E1–E6 error table (counts of responses with each error, nonexclusive) and one representative B-correct/C-wrong and one B-wrong example selected by deterministic rule: first question in sorted ID order with the specified outcome from the primary execution; if unavailable, say so. Show relevant source excerpt/feature rows, question, gold, actual delivered excerpts and root cause; anonymization unnecessary for fictional subjects but retain clear synthetic labels. Do not select exclusively flattering examples. B plan/verification traces help explain mistakes but do not prove which component causally caused all improvements. Report computational overhead in small table (median/p95 latency, mean tokens, call count and failure rate), not as clinical efficiency.

**Recommended figures:** (1) paired difference plot for SGIS, B−C and B−A, with descriptive cluster intervals and zero line; annotate observed arm percentages in caption; (2) grouped bars of strict success by Q1–Q4 and three arms, fixed 0–100% scale, denominator in caption. The error table and actual case excerpts suffice; no redundant graph for each metric. If figure space limited, retain category chart and main table with differences/intervals. Provide scenario-level primary outcomes in supplement for reproducibility. Separately report the frozen 24-question subset: a compact table per arm with primary-subset successes /24, second-execution successes /24, disagreements /24, success-to-failure and failure-to-success counts, and execution failures. Identify the subset composition. Do not merge these counts into either main figure or primary comparative metric.

### 11.3 IDF text template — do not fill without results

> To assess the proposed LLM-based evidence investigation mechanism, a controlled comparative software experiment was conducted on [actual number] independently constructed synthetic longitudinal monitoring scenarios with [actual number] clinician-directed questions. Each question used the same source evidence, physiological-context definitions, and underlying model in direct, general-purpose program-assisted, and constrained D2 configurations, with one primary execution per configuration. A prespecified subset of [actual number] questions was independently repeated and reported separately as a reproducibility check. Ground truth was derived independently from source records and interval/statistical calculations and evaluated against required findings, evidence attribution, and uncertainty handling. The constrained architecture achieved [measured SGIS] versus [measured C] and [measured A], corresponding to [measured differences and scenario-level uncertainty]. [Observed error pattern/representative finding]. These results assess controlled evidence-investigation correctness, not wearable measurement accuracy, withdrawal diagnosis, treatment effectiveness or clinical outcomes.

If B−C not favorable, replace improvement wording with actual finding. Do not state “reduces hallucinations by X%” unless clearly defining measured unsupported-claim rate, denominator and scope. Do not claim this benchmark demonstrates clinician time savings; only a clinician-task study could establish that. No patentability conclusion.

## 12. Critical methodological audit and resolutions

| Material concern | Resolution in frozen protocol | Residual limitation |
|---|---|---|
| Direct LLM artificially disadvantaged by lack of calculation | Strong direct review plus C with genuine executable Python and full rules/evidence; B−C primary | No exhaustive comparison with all agent/tool/query systems; comparator implementation matters |
| D2 has engineered domain policies not given to baseline | Common definitions, reference/eligibility rows, source data, examples, scope, same model; C can implement every policy | B has reusable deterministic semantics by design; cannot isolate individual components without ablation |
| B could be an oracle hand-coded per question | Generic tools only; held-out scenario/question split; no gold data/hand-picked selections in planner | Authored benchmark has finite operation family coverage; not open-domain QA |
| Arithmetic dominates | 40% Q4, compositional tasks, method/anchor/context/reference/coverage and source semantics required in SGIS | Some foundational numeric tasks remain appropriate and measured |
| Synthetic evidence lacks real patient variability | Independently authored diverse scenarios with actual intended evidence distinctions; disclose synthetic | Clinical realism and external validity remain unproven, no population/disease claim |
| Independent gold circularity | Separate reviewer, integer-time oracle, manual source IDs, frozen worksheets; no B code imports | Reviewers can still err; record adjudication and defects transparently |
| Citation existence mistaken for correctness | Per-claim semantic review, complete evidence sets, qualifier requirements; B verifier not evaluator | Some human judgement remains; double scoring and agreement reporting |
| Over-abstention improves reliability metric | Strict status/required slots, zero for omissions, precision denominator reported alongside recall and strict success | Genuine safety/utility trade-off still observable; do not combine into arbitrary weighted score |
| Repeated outputs inflate sample size | Scenario paired bootstrap on primary outputs, fixed N, repeat subset analyzed separately, descriptive CIs | 24 authored clusters not a random patient sample; no formal power or broad significance claim |
| Exact uncertainty handling could require elaborate engine | Exact anchor calculations only when source-supported; partial/qualify otherwise; explicit test rule | No evaluation of advanced uncertainty propagation; scope consistent with blueprint's abstain branch |
| Test data or criteria tuned after model outputs | Freeze inputs, gold, scoring, prompts; no test optimization, uniform defect adjudication | Dev is small; held-out result is conditional on this version |
| High implementation/review overhead | Standalone file-based tools, one primary execution and 24-question repeat subset, no upstream/clinical UI; three arms only | Secure sandbox, API quota and reviewer time are real prerequisites |
| Architecture drift | Scope boundaries §2 and tools §10 match Blueprint §§2.4, 5, 7; D1/D3 not removed | Future real upstream adapter validation remains separate |

**Audit verdict:** the selected experiment is suitable to proceed after narrow operational gates. The only real unresolved dependencies are API access/quota/model snapshot, isolated runner availability, independent annotation/reviewer capacity, and the as-yet-unconstructed fixtures/implementation. None requires another broad research or architecture-selection exercise. The protocol cannot guarantee a favorable outcome; that is a necessary property of a valid experiment. A second model, public wearable dataset, hardware test, real patient records and clinician user study are **not blockers for this specific controlled software claim**.

## 13. Sequential execution roadmap

1. Approve the protocol and allocate roles (fixture author, independent gold checker, implementation/evaluation). Confirm API account, quota and code runner availability. Set budget before testing. Create repository and finalize/version the shared evidence, policy, output and gold schemas using the schema-first gate (§4.1) before constructing development scenarios.
2. Construct five dev scenarios and 25 questions, with independently checked gold. Implement minimum D2 deterministic functions and unit tests; implement A and C and secure execution checks. Implement blinded scoring against the already finalized common output and gold schema. Verify all dev tasks executable by correct manual plans, validate both baselines have full policies/data.
3. Refine prompts and tool semantics only on development. Confirm context caps and verify source IDs, action semantics, coverage and status behavior. Record exact model, dependencies, call budgets and failure handling. Resolve any dev gate failure before freeze.
4. Create 24 held-out scenarios/120 questions using distribution quotas; independent gold reviewer finalizes worksheet and source alternatives. Prespecify the 24-question repeat subset (§9.2). Seal data, gold, protocol, prompts, schema, subset manifest and code hashes. Keep gold inaccessible to execution. Check coverage matrix and token caps without inspecting model outputs.
5. Run the matched schedule for 360 primary attempts followed by 72 prespecified reproducibility attempts (432 total). Save raw/validated traces and final delivered results. No manual answer repairs or selective retries. Resume only under fixed outage policy.
6. Export blinded outputs; score against independent gold with automated numeric checks and human semantic review; second-review 72 primary and 15 reproducibility outputs (87 scheduled reviews) plus disputes; adjudicate before arm reveal. Preserve annotations and agreement.
7. Compute primary-only paired differences, cluster intervals, category and error breakdowns; separately calculate paired repeat-subset agreement; generate two figures and result tables. Report actual outcomes, including unfavorable ones, limits and overhead. Prepare concise IDF paragraph and appendix.

Completion criterion: all fixed test attempts accounted for, gold and grading independently audited, result tables reproducible from versioned artifacts, and claim language corresponds to measured result. Passing a particular percentage is not a completion criterion.

## 14. Decision register

| ID | Status | Decision | Reason / remaining dependency |
|---|---|---|---|
| D01 | Final | D2 only | Central clinician-directed investigation; D1 fixtures, D3 excluded |
| D02 | Final | Three arms A/C/B; B−C primary | Controls for ordinary program assistance, direct secondary |
| D03 | Final | Shared synthetic evidence benchmark | Correctness given evidence, no required actual measurement data |
| D04 | Final | 24 test scenarios, 120 questions; 5 dev/25 | Clustered design and manageable scope; not powered for clinical inference |
| D05 | Final | Q1/Q2/Q3 24 each, Q4 48; 72/24/24 status split | Compositional and reliability coverage |
| D06 | Final | Feature-level B4/5 fixtures, admitted clinical assertions | Preserve method, support, named policy, timing, source and revision distinctions |
| D07 | Final | Benchmark-specific operations §5.5, not production thresholds | Reproducible semantics without altering blueprint |
| D08 | Final | Independent oracle + human source-based gold, blinded scoring | Prevent circular evaluation and unsupported citation scoring |
| D09 | Final | SGIS primary; five diagnostic rates and engineering overhead | Completeness, correctness, grounding and answerability without arbitrary weights |
| D10 | Final | One primary execution per question/arm; 24-question reproducibility subset separately analyzed; primary scenario bootstrap; all attempts accounted for | Retains unique coverage, reduces review workload; limited stochastic check and appropriate grouping; no population claim |
| D11 | Selected; operational check | Select one capable pinned hosted model at development preflight, same across all arms | Account access, lifecycle, output support, context and budget must be verified; freeze actual configuration before test |
| D12 | Final; operational check | Isolated generic Python comparator | Secure container resource limits and offline isolation must be confirmed before test |
| D13 | Final | Standalone Python implementation | No unnecessary deployment dependency |
| D14 | Final; operational check | Independent gold checker and blinded review; 20% double output scoring | Reviewer availability and actual annotation effort need confirmation |
| D15 | Final | No clinical-effect/patent novelty inference or hardware validation | Experiment limited to evidence processing correctness |
| D16 | Final; implementation gate | Shared evidence, answer and gold schemas finalized before development fixtures (§4.1) | Ensure every required semantic distinction is representable and scoreable; actual contracts still to be implemented |

All conceptual experimental choices have been made. Remaining operational checks are genuine prerequisites, not alternative experimental directions. The approved Blueprint remains unchanged.

## 15. Verified research references

Primary publication/official documentation pages located during targeted web research. References support specific methodological choices in §3 and model implementation in §9. No full systematic review or reproduction of reported benchmark numbers was performed.

- **[R1]** Lee et al. (2022). *EHRSQL: A Practical Text-to-SQL Benchmark for Electronic Health Records*. NeurIPS 35, Datasets and Benchmarks. [Publisher abstract](https://papers.neurips.cc/paper_files/paper/2022/hash/643e347250cf9289e5a2a6c1ed5ee42e-Abstract-Datasets_and_Benchmarks.html).
- **[R2]** Lee, G., Kweon, S., Bae, S., & Choi, E. (2024). *Overview of the EHRSQL 2024 Shared Task on Reliable Text-to-SQL Modeling on Electronic Health Records*. ClinicalNLP, 644–654. [ACL Anthology](https://aclanthology.org/2024.clinicalnlp-1.62/). DOI: 10.18653/v1/2024.clinicalnlp-1.62.
- **[R3]** Gao, L., et al. (2023). *PAL: Program-aided Language Models*. ICML, PMLR 202, 10764–10799. [PMLR](https://proceedings.mlr.press/v202/gao23f.html).
- **[R4]** Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR. [Project and paper links](https://react-lm.github.io/), [OpenReview](https://openreview.net/forum?id=WE_vluYUL-X).
- **[R5]** Chen et al. (2021). *FinQA: A Dataset of Numerical Reasoning over Financial Data*. EMNLP. [ACL Anthology](https://aclanthology.org/2021.emnlp-main.300/).
- **[R6]** Li et al. (2023). *Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs*. NeurIPS Datasets and Benchmarks. [Publisher abstract](https://papers.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html).
- **[R7]** Gao, T., Yen, H., Yu, J., & Chen, D. (2023). *Enabling Large Language Models to Generate Text with Citations*. EMNLP, 6465–6488. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.398/). DOI: 10.18653/v1/2023.emnlp-main.398.
- **[R8]** Soni, S., Gayen, S., & Demner-Fushman, D. (2025). *Overview of the ArchEHR-QA 2025 Shared Task on Grounded Question Answering from Electronic Health Records*. BioNLP, 396–405. [ACL Anthology](https://aclanthology.org/2025.bionlp-1.34/).
- **[R9]** Soni, S., & Demner-Fushman, D. (2026). *A Dataset for Addressing Patient’s Information Needs related to Clinical Course of Hospitalization*. Scientific Data. [Article](https://www.nature.com/articles/s41597-026-06639-z). DOI: 10.1038/s41597-026-06639-z.
- **[R10]** Schmidt, P., Reiss, A., Dürichen, R., Marberger, C., & Van Laerhoven, K. (2018). *Introducing WESAD, a Multimodal Dataset for Wearable Stress and Affect Detection*. ICMI, 400–408. [Original dataset page](https://ubi29.informatik.uni-siegen.de/usi/data_wesad.html). DOI: 10.1145/3242969.3242985.
- **[R11]** Walonoski et al. (2018). *Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record*. JAMIA. [PubMed](https://pubmed.ncbi.nlm.nih.gov/29025144/). DOI: 10.1093/jamia/ocx147.
- **[R12]** MacKinnon, J. G., Nielsen, M. Ø., & Webb, M. D. (2023). *Cluster-robust inference: A guide to empirical practice*. Journal of Econometrics. [DOI](https://doi.org/10.1016/j.jeconom.2022.04.001). Cited for the grouping principle, not for an endorsement of this small-sample percentile interval as confirmatory population inference.
- **[R13]** OpenAI. *GPT-4.1 model documentation* (historical v1.0 candidate reference, not a selected model in v1.1). [Official API documentation](https://developers.openai.com/api/docs/models/gpt-4.1). Consult the selected provider/model documentation and confirm account access and lifecycle at preflight; record the actual reference in the frozen manifest.
- **[R14]** OpenAI. *Structured model outputs*. [Official API documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Schema conformance is not factual correctness.

Internal source: Blueprint v1.6, especially §§1.2, 2.3.1, 2.4, 4.2, 5.1–5.4, 6, 7.1–7.6, 8 and 10.1–10.4. The attached research request defines scope and deliverables. Neither internal document is evidence of measured performance.

---

## Consolidated experimental specification — authoritative implementation reference upon approval

```yaml
protocol: AUD-SUD-D2-experiment-v1.1
scope: controlled downstream evidence investigation only
architecture_authority: blueprint-v1.6
arms:
  A: same-model direct evidence interpretation + review
  C: same-model general Python execution + composition
  B: same-model typed D2 plan + validation + deterministic tools + verified composition
primary_contrast: B_minus_C
secondary_contrast: B_minus_A
model: null  # select and pin during development preflight, before test freeze
model_selection: capable hosted LLM; account/lifecycle, schema, context, budget and development gates
model_config: {temperature: 0, top_p: 1, max_output_tokens_per_call: 4096}  # use only supported parameters; freeze actual settings per section_9_1
semantic_calls_per_attempt_max: 3
full_evidence_input_preflight_cap_tokens: 64000
full_call_input_cap_tokens: 96000
computed_bundle_cap_tokens: 24000
plan_step_cap: 12
transport_retries_max: 2
splits:
  development: {scenarios: 5, questions: 25}
  test: {scenarios: 24, questions: 120, questions_per_scenario: 5}
question_classes: {Q1: 24, Q2: 24, Q3: 24, Q4: 48}
answerability: {answered: 72, partial: 24, insufficient: 14, clarify: 10}
difficulty: {foundational: 24, compositional: 60, complex: 36}
primary: {executions_per_question_arm: 1, attempts_per_arm: 120, attempts_total: 360}
reproducibility:
  questions: 24
  selection: one per scenario; all Q classes and answerability states; freeze manifest before test
  additional_executions_per_selected_question_arm: 1
  attempts_per_arm: 24
  attempts_total: 72
  include_in_primary_metrics: false
total_attempts_per_arm: 144
total_test_attempts: 432
inputs: independently authored synthetic B4/B5 evidence + clinical assertions and source records
source_snapshot: immutable authorized scenario view, reference/policy/revision binding
operation_rules: section_5_5
output_contract: section_4_1
schema_first_gate: finalize and test evidence, policy, shared answer and gold schemas before development fixtures
primary_endpoint: strict_grounded_investigation_success
secondary_endpoints: [required_grounded_fact_recall, required_numerical_correctness,
                      grounded_claim_precision, answerability_handling_accuracy,
                      consequential_error_incidence]
engineering_diagnostics: [latency, tokens, calls, failures, repairs]
gold: independent source selection + second-grid arithmetic oracle + reviewed worksheets
scoring: deterministic numeric checks + blinded semantic reviewer
second_output_review: {primary: 72, reproducibility: 15, scheduled_total: 87, additional: disputed material errors}
analysis: primary-only paired scenario-level differences; 10000 scenario bootstrap resamples; separate paired repeat-subset agreement
seed: 20261125
reporting: primary main table, category table, error counts, 2 plots, representative actual cases; separate repeat-subset table
prohibited_claims: [clinical_efficacy, hardware_validity, diagnosis, treatment_causality,
                    superiority_over_all_architectures, patentability]
```

**Final recommendation:** approve this experimental design and proceed directly to schema finalization, development fixtures and minimum implementation. Do not spend further effort searching for an AUD/SUD wearable dataset to satisfy this particular evidence-processing experiment. The measurable contribution to investigate is whether constrained, domain-aware execution and grounded composition improve the completeness and reliability of a same-model clinical evidence investigation, even against an ordinary computationally capable comparator. The result must be measured rather than presumed.
