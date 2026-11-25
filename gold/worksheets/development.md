# D01–D05 provisional calculation and source-selection worksheet

Status: `pending-human-review`. This is a provisional engineering worksheet, not
independent clinical review or a measured result. A second reviewer must check each
question before any benchmark execution.

## Frozen calculation rules

- Use UTC and half-open intervals `[start,end)`.
- Nominal feature-window coverage is the union of accepted windows clipped to the
  requested interval; overlapping windows count once.
- Actual support is a separate union of explicit support intervals. Fraction-only or
  unknown support produces a known lower bound, not an invented exact total.
- Default summaries are medians of accepted method-compatible feature values, not
  time-weighted means. Explicit `mean` requests retain that statistic label.
- Named references are policy- and method-specific. A provisional reference permits
  a qualified descriptive difference; unavailable references do not yield a delta.
- E1 groups qualifying heart-rate windows (`>=95 bpm`, minimum grouping span 15 s,
  maximum gap 5 s) while retaining grouping span, qualifying coverage and actual
  support as different quantities.
- Completed administration, order, held/not-done and uncertain narrative report are
  distinct action states. Clinical mention count is not occurrence count.

## Representative hand calculation

For each scenario's first 30 seconds, H1 `[0,10)` and H2 `[5,15)` contribute a
nominal union of 15 seconds. H1 contributes `[0,8)` actual support and H2 contributes
`[5,15)`, giving 15 seconds of known actual support; rejected H3 contributes neither.
The denominator is the 30-second requested span, so both requested fractions are
`15/30 = 0.50`. D02-Q1 is therefore `answered`: D02-H5 is fraction-only but begins at
45 seconds and is outside that question's 30-second scope.

## Derived development findings

| Questions | Expected supported findings | Material limitation/status |
|---|---|---|
| D01/D02/D03/D05-Q1 | nominal feature-window coverage 15/30 s; known actual support 15/30 s; H3 rejected | answered |
| D01/D02/D03-Q2 | H1 only; median ECG HR 96 bpm; R1 difference +16 bpm; R1 provisional | answered, descriptive only |
| D04-Q2 | no comparison value | insufficient: R1 unavailable |
| D05-Q2 | no comparison value | insufficient: wrist PPG is incompatible with ECG R1 |
| D01–D05-Q3 | one historical E1 group: grouping span 20 s, qualifying coverage 20 s, actual support 20 s; target H1 candidate fails 15 s minimum | answered, grouping is not continuous elevation |
| D01/D05-Q4a | C1 reported onset, C4 completed at 09:30; ECG difference +16 bpm from H1/R1; AC-G median 3.00 µS from G1/G2 | answered, sparse support and no treatment-effect inference |
| D02-Q4a | C1 bounds 08:50–09:10; C4 completed at 09:30 | partial: exact event-bounded aggregate blocked by approximate onset |
| D03-Q4a | C1 supported; C4A and C4B are both completed candidates | clarify which administration is intended |
| D04-Q4a | C1 reported onset only | insufficient: no completed administration anchor |
| D01/D02/D05-Q4b | reported onset plus completed administration with order/held/uncertain distinctions | answered |
| D03-Q4b | C1 plus C4A/C4B candidates | clarify which completed occurrence is intended |
| D04-Q4b | C1; C2 order and C3 held/not-done | partial: symptom onset is supported, but no completed action is supported |

Every numeric slot carries its unit, statistic, denominator/interval and evidence IDs
in the provisional gold object. Every exclusion is retained with its reason; source
and clinical review fields remain pending human review.

## Scenario/source worksheet index

| Scenario | Q1 | Q2 | Q3 | Q4a | Q4b |
|---|---|---|---|---|---|
| D01 | H1/H2/H3 + inventory; nominal vs actual support | R1, H1 eligible; H2 excluded | E1 target/history groups and gap rule | C1/C4 anchors; H1/H2; G1/G2; R1 | C1/C2/C3/C4/C6 action distinctions |
| D02 | Same with fraction-only H5 limitation | R1 provisional and policy binding | E1 target/history recurrence | approximate C1 blocks exact event-bounded aggregate | source-supported events and uncertainty |
| D03 | accepted/rejected support | R1 comparison | E1 recurrence | C4A/C4B requires clarification | multiple completed occurrence candidates |
| D04 | accepted feature evidence | R1 unavailable | E1 descriptive recurrence only | no completed administration; insufficient anchor | order/held evidence is not administration |
| D05 | accepted support | wrist PPG is incompatible with ECG R1 | E1 configured ECG rule | supported event-anchored multimodal slice | clinical source evidence with modality limitation |

All IDs above are synthetic fixture IDs resolved through the scenario source inventory;
no raw waveform, patient record or treatment-effect claim is implied.

