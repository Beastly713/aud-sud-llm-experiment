"""Authored development-only scenarios, questions, plans and provisional gold.

The fixtures are intentionally small but exercise the protocol's material semantics.
They are constructed from authored constants, not generated from the D2 runtime or
the reference oracle. No test/held-out records live here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .schema import (
    Acceptance,
    ActionStatus,
    AnswerStatus,
    AssertionStatus,
    ClinicalEventArgs,
    ClinicalEvent,
    ClinicalStep,
    CommonAnswer,
    ContextAnnotation,
    EvidenceClass,
    EvidenceSnapshot,
    GoldRecord,
    GoldSlot,
    HistoricalReference,
    InvestigationPlan,
    InvestigationPolicy,
    Interval,
    IntervalArgs,
    IntervalStep,
    MeasurementValue,
    MovementStratum,
    Observation,
    ObservationArgs,
    ObservationStep,
    OccurrenceLinkStatus,
    Question,
    QuestionClass,
    ReferenceStatus,
    ResolveArgs,
    ResolveStep,
    ReviewState,
    Scenario,
    SourceRecord,
    SupportKind,
    TemporalPrecision,
    TimeBounds,
    EligibilityRecord,
    EligibilityStatus,
    EpisodeRule,
)


UTC = timezone.utc


def _time(day: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2026, 1, day, 9, minute, second, tzinfo=UTC)


def _interval(start: datetime, seconds: int) -> Interval:
    return Interval(start=start, end=start + timedelta(seconds=seconds))


def _source(source_id: str, scope: Interval, content: str, source_type: str = "synthetic_note") -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        source_type=source_type,
        locator=f"synthetic://{source_id}",
        content=content,
        revision="r1",
        covered_scope=[scope],
        recording_available=True,
    )


def _observation(
    observation_id: str,
    participant: str,
    metric: str,
    method: str,
    node: str,
    start: datetime,
    seconds: int,
    value: float | None,
    units: str,
    context_id: str,
    source_id: str,
    accepted: bool = True,
    support: str = "full",
) -> Observation:
    if accepted:
        measurement = MeasurementValue(value=value, units=units)
        acceptance = Acceptance.ACCEPTED
        reasons: list[str] = []
        if support == "fraction":
            support_kind = SupportKind.FRACTION_ONLY
            actual = []
            support_fraction = 0.5
            support_denominator = seconds
        else:
            support_kind = SupportKind.INTERVALS
            actual = [_interval(start, seconds if support == "full" else max(1, seconds - 2))]
            support_fraction = None
            support_denominator = None
    else:
        measurement = MeasurementValue(value=None, units=units, missingness="absent")
        acceptance = Acceptance.REJECTED
        reasons = ["artifact"]
        support_kind = SupportKind.UNKNOWN
        actual = []
        support_fraction = None
        support_denominator = None
    return Observation(
        observation_id=observation_id,
        participant_id=participant,
        metric=metric,
        method=method,
        node=node,
        site=node,
        value=measurement,
        nominal=_interval(start, seconds),
        acceptance=acceptance,
        acceptance_reasons=reasons,
        support_kind=support_kind,
        actual_support=actual,
        support_fraction=support_fraction,
        support_denominator_seconds=support_denominator,
        timing_quality="resolved",
        context_ids=[context_id],
        source_ids=[source_id],
        feature_version="fixture-feature-v1",
    )


def _context(context_id: str, participant: str, start: datetime, seconds: int, node: str, movement: MovementStratum, source: str) -> ContextAnnotation:
    return ContextAnnotation(
        context_id=context_id,
        participant_id=participant,
        node=node,
        nominal=_interval(start, seconds),
        actual_support=[_interval(start, seconds)],
        movement=movement,
        clock_status="aligned",
        source_ids=[source],
    )


def _event(
    mention_id: str,
    participant: str,
    concept: str,
    event_type: str,
    action: ActionStatus,
    evidence: EvidenceClass,
    source: str,
    event_time: TimeBounds | None,
    occurrence: str | None,
    text: str,
    assertion: AssertionStatus = AssertionStatus.AFFIRMED,
    semantic: ReviewState = ReviewState.SUPPORTED,
) -> ClinicalEvent:
    return ClinicalEvent(
        mention_id=mention_id,
        participant_id=participant,
        event_type=event_type,
        concept=concept,
        assertion=assertion,
        experiencer="patient",
        evidence_class=evidence,
        action_status=action,
        event_time=event_time,
        documented_at=event_time.lower if event_time else _time(1, 1),
        occurrence_id=occurrence,
        occurrence_link_status=OccurrenceLinkStatus.LINKED if occurrence else OccurrenceLinkStatus.UNRESOLVED,
        semantic_support=semantic,
        source_review=ReviewState.SUPPORTED,
        structural_review=ReviewState.SUPPORTED,
        source_ids=[source],
        original_text=text,
    )


def make_scenario(number: int) -> Scenario:
    day = number
    participant = f"D{number:02d}-P01"
    scenario_id = f"D{number:02d}"
    base = _time(day)
    target = _interval(base, 3600)
    historical = _interval(base - timedelta(days=1), 1800)
    source_ids = [f"{scenario_id}-S-H", f"{scenario_id}-S-C", f"{scenario_id}-S-R", f"{scenario_id}-S-I"]
    sources = [
        _source(source_ids[0], target, "feature rows and measurement support for the target recording", "feature_export"),
        _source(source_ids[1], target, "patient-reported tremor onset and medication documentation", "clinical_note"),
        _source(source_ids[2], historical, "named historical reference center and eligibility policy", "reference_snapshot"),
        _source(source_ids[3], target, "recording inventory: target bouts are available; unrecorded spans remain unknown", "inventory"),
    ]
    contexts = [
        _context(f"{scenario_id}-CTX-H1", participant, base, 10, "chest", MovementStratum.LOW, source_ids[0]),
        _context(f"{scenario_id}-CTX-H2", participant, base + timedelta(seconds=5), 10, "chest", MovementStratum.ELEVATED, source_ids[0]),
        _context(f"{scenario_id}-CTX-H3", participant, base + timedelta(seconds=20), 10, "chest", MovementStratum.LOW, source_ids[0]),
        _context(f"{scenario_id}-CTX-H4", participant, base + timedelta(seconds=30), 10, "chest", MovementStratum.ELEVATED, source_ids[0]),
        _context(f"{scenario_id}-CTX-H5", participant, base + timedelta(seconds=45), 10, "chest", MovementStratum.UNKNOWN, source_ids[0]),
        _context(f"{scenario_id}-CTX-W1", participant, base, 10, "wrist", MovementStratum.LOW, source_ids[0]),
        _context(f"{scenario_id}-CTX-W2", participant, base + timedelta(seconds=30), 10, "wrist", MovementStratum.LOW, source_ids[0]),
        _context(f"{scenario_id}-CTX-P1", participant, base - timedelta(days=1), 10, "chest", MovementStratum.LOW, source_ids[2]),
        _context(f"{scenario_id}-CTX-P2", participant, base - timedelta(days=1, seconds=-10), 10, "chest", MovementStratum.LOW, source_ids[2]),
    ]
    observations = [
        _observation(f"{scenario_id}-H1", participant, "heart_rate", "chest_ecg", "chest", base, 10, 96, "bpm", f"{scenario_id}-CTX-H1", source_ids[0], support="partial"),
        _observation(f"{scenario_id}-H2", participant, "heart_rate", "chest_ecg", "chest", base + timedelta(seconds=5), 10, 100, "bpm", f"{scenario_id}-CTX-H2", source_ids[0]),
        _observation(f"{scenario_id}-H3", participant, "heart_rate", "chest_ecg", "chest", base + timedelta(seconds=20), 10, None, "bpm", f"{scenario_id}-CTX-H3", source_ids[0], accepted=False),
        _observation(f"{scenario_id}-H4", participant, "heart_rate", "chest_ecg", "chest", base + timedelta(seconds=30), 10, 98, "bpm", f"{scenario_id}-CTX-H4", source_ids[0]),
        _observation(f"{scenario_id}-H5", participant, "heart_rate", "chest_ecg", "chest", base + timedelta(seconds=45), 10, 92, "bpm", f"{scenario_id}-CTX-H5", source_ids[0], support="fraction" if number == 2 else "full"),
        _observation(f"{scenario_id}-PULSE1", participant, "pulse_rate", "wrist_ppg", "wrist", base, 10, 95, "bpm", f"{scenario_id}-CTX-W1", source_ids[0]),
        _observation(f"{scenario_id}-G1", participant, "ac_conductance", "ac_conductance_100hz", "wrist", base, 30, 2.5, "µS", f"{scenario_id}-CTX-W1", source_ids[0]),
        _observation(f"{scenario_id}-G2", participant, "ac_conductance", "ac_conductance_100hz", "wrist", base + timedelta(seconds=30), 10, 3.5, "µS", f"{scenario_id}-CTX-W2", source_ids[0]),
        _observation(f"{scenario_id}-G3", participant, "ac_conductance", "ac_conductance_100hz", "wrist", base + timedelta(seconds=40), 10, None, "µS", f"{scenario_id}-CTX-W2", source_ids[0], accepted=False),
        _observation(f"{scenario_id}-P-H1", participant, "heart_rate", "chest_ecg", "chest", base - timedelta(days=1), 10, 98, "bpm", f"{scenario_id}-CTX-P1", source_ids[2]),
        _observation(f"{scenario_id}-P-H2", participant, "heart_rate", "chest_ecg", "chest", base - timedelta(days=1, seconds=-10), 10, 97, "bpm", f"{scenario_id}-CTX-P2", source_ids[2]),
    ]
    ref_status = ReferenceStatus.UNAVAILABLE if number == 4 else ReferenceStatus.PROVISIONAL
    references = [
        HistoricalReference(
            reference_id=f"{scenario_id}-R1",
            policy_id=f"{scenario_id}-POLICY-NARROW",
            metric="heart_rate",
            method="chest_ecg",
            site="chest",
            epoch_label="earlier low-chest-motion epoch",
            event_cutoff=historical.end,
            as_of=base + timedelta(hours=2),
            status=ref_status,
            center=None if ref_status == ReferenceStatus.UNAVAILABLE else 80.0,
            units="bpm",
            source_ids=[source_ids[2]],
            comparison_units=["prior-day-bout"],
            revision="ref-r1",
        ),
        HistoricalReference(
            reference_id=f"{scenario_id}-R2",
            policy_id=f"{scenario_id}-POLICY-BROAD",
            metric="heart_rate",
            method="chest_ecg",
            site="chest",
            epoch_label="earlier broad ECG epoch",
            event_cutoff=historical.end,
            as_of=base + timedelta(hours=2),
            status=ReferenceStatus.SUPPORTED_DESCRIPTIVE,
            center=82.0,
            units="bpm",
            source_ids=[source_ids[2]],
            comparison_units=["prior-day-bout"],
            revision="ref-r2",
        ),
    ]
    eligibility: list[EligibilityRecord] = []
    for observation in observations:
        if observation.metric != "heart_rate" or observation.observation_id.endswith("-H3"):
            continue
        if observation.observation_id.endswith("-H1") or observation.observation_id.endswith("-P-H1"):
            narrow = EligibilityStatus.ELIGIBLE
        elif observation.observation_id.endswith("-H2"):
            narrow = EligibilityStatus.INELIGIBLE
        else:
            narrow = EligibilityStatus.INDETERMINATE
        if number == 4:
            narrow = EligibilityStatus.INDETERMINATE
        eligibility.append(EligibilityRecord(observation_id=observation.observation_id, reference_id=f"{scenario_id}-R1", policy_id=f"{scenario_id}-POLICY-NARROW", revision="ref-r1", status=narrow, reasons=[] if narrow == EligibilityStatus.ELIGIBLE else ["motion or unavailable reference"]))
        eligibility.append(EligibilityRecord(observation_id=observation.observation_id, reference_id=f"{scenario_id}-R2", policy_id=f"{scenario_id}-POLICY-BROAD", revision="ref-r2", status=EligibilityStatus.ELIGIBLE, reasons=[]))
    onset_precision = TemporalPrecision.APPROXIMATE if number == 2 else TemporalPrecision.INSTANT
    onset = TimeBounds(lower=base - timedelta(minutes=10) if number == 2 else base, upper=base + timedelta(minutes=10) if number == 2 else base, precision=onset_precision)
    events = [
        _event(f"{scenario_id}-C1", participant, "tremor", "symptom_onset", ActionStatus.REPORTED, EvidenceClass.NARRATIVE_REPORT, source_ids[1], onset, f"{scenario_id}-O1", "patient reports tremor began at the stated time"),
        _event(f"{scenario_id}-C2", participant, "diazepam", "medication_order", ActionStatus.ORDERED, EvidenceClass.STRUCTURED_ORDER, source_ids[1], TimeBounds(lower=base + timedelta(minutes=5), upper=base + timedelta(minutes=5), precision=TemporalPrecision.INSTANT), None, "diazepam ordered"),
        _event(f"{scenario_id}-C3", participant, "diazepam", "medication_action", ActionStatus.HELD, EvidenceClass.STRUCTURED_ORDER, source_ids[1], TimeBounds(lower=base + timedelta(minutes=10), upper=base + timedelta(minutes=10), precision=TemporalPrecision.INSTANT), None, "diazepam held; not administered"),
    ]
    if number != 4:
        if number == 3:
            for suffix, minute in (("A", 20), ("B", 40)):
                events.append(_event(f"{scenario_id}-C4{suffix}", participant, "diazepam", "medication_administration", ActionStatus.COMPLETED, EvidenceClass.STRUCTURED_ADMINISTRATION, source_ids[1], TimeBounds(lower=base + timedelta(minutes=minute), upper=base + timedelta(minutes=minute), precision=TemporalPrecision.INSTANT), f"{scenario_id}-O4{suffix}", "diazepam administration completed"))
        else:
            events.append(_event(f"{scenario_id}-C4", participant, "diazepam", "medication_administration", ActionStatus.COMPLETED, EvidenceClass.STRUCTURED_ADMINISTRATION, source_ids[1], TimeBounds(lower=base + timedelta(minutes=30), upper=base + timedelta(minutes=30), precision=TemporalPrecision.INSTANT), f"{scenario_id}-O4", "diazepam administration completed"))
    events.append(_event(f"{scenario_id}-C6", participant, "diazepam", "medication_report", ActionStatus.REPORTED, EvidenceClass.NARRATIVE_REPORT, source_ids[1], TimeBounds(lower=base + timedelta(minutes=15), upper=base + timedelta(minutes=15), precision=TemporalPrecision.INSTANT), None, "patient uncertainly reports a dose", AssertionStatus.UNCERTAIN))
    policies = [
        InvestigationPolicy(policy_id=f"{scenario_id}-POLICY-NARROW", version="bucket5-v1", metric="heart_rate", method="chest_ecg", compatible_nodes=["chest"], reference_ids=[f"{scenario_id}-R1"], allowed_operations=["summary", "coverage", "compare_to_named_reference", "episodes"], episode_rule_ids=[f"{scenario_id}-E1"], denominator_definitions={"requested_interval": "wall-clock seconds"}),
        InvestigationPolicy(policy_id=f"{scenario_id}-POLICY-BROAD", version="bucket5-v1", metric="heart_rate", method="chest_ecg", compatible_nodes=["chest"], reference_ids=[f"{scenario_id}-R2"], allowed_operations=["summary", "coverage", "compare_to_named_reference"], denominator_definitions={"requested_interval": "wall-clock seconds"}),
    ]
    episode_rule = EpisodeRule(rule_id=f"{scenario_id}-E1", metric="heart_rate", method="chest_ecg", threshold_operator=">=", threshold=95.0, minimum_grouping_seconds=15, maximum_gap_seconds=5, required_movement=MovementStratum.LOW)
    snapshot = EvidenceSnapshot(scenario_id=scenario_id, participant_id=participant, snapshot_id=f"{scenario_id}-v1", available_as_of=base + timedelta(hours=2), source_event_cutoff=base + timedelta(hours=1), timezone="UTC", authorized_scope=[target, historical], source_inventory=source_ids, revision="snapshot-v1")
    return Scenario(scenario_id=scenario_id, participant_id=participant, snapshot=snapshot, sources=sources, observations=observations, contexts=contexts, references=references, eligibility=eligibility, clinical_events=events, policies=policies, episode_rules=[episode_rule])


def make_questions(scenarios: list[Scenario] | None = None) -> list[Question]:
    scenarios = scenarios or make_scenarios()
    questions: list[Question] = []
    for scenario in scenarios:
        sid = scenario.scenario_id
        base = _time(int(sid[-2:]))
        target_short = [_interval(base, 30)]
        target = [_interval(base, 1800)]
        history_and_target = [scenario.snapshot.authorized_scope[0], scenario.snapshot.authorized_scope[1]]
        questions.extend([
            Question(question_id=f"{sid}-Q1", scenario_id=sid, snapshot_id=scenario.snapshot.snapshot_id, text="Over the first 30 seconds, how much accepted chest-ECG heart-rate evidence was available, and for how much do we have documented usable support?", question_class=QuestionClass.Q1, difficulty="foundational", authorized_scope=target_short),
            Question(question_id=f"{sid}-Q2", scenario_id=sid, snapshot_id=scenario.snapshot.snapshot_id, text=("Compared with the named earlier ECG reference, what was the typical wrist pulse rate during the review bout?" if sid == "D05" else "Compared with the named earlier low-chest-motion ECG reference, what was the typical heart rate during the review bout?"), question_class=QuestionClass.Q2, difficulty="compositional", authorized_scope=[_interval(base, 15)]),
            Question(question_id=f"{sid}-Q3", scenario_id=sid, snapshot_id=scenario.snapshot.snapshot_id, text="Using the configured E1 rule, how many elevated heart-rate groups were identified, what was their qualifying-window coverage versus grouping span, and did the same rule recur earlier?", question_class=QuestionClass.Q3, difficulty="complex", authorized_scope=history_and_target),
            Question(question_id=f"{sid}-Q4a", scenario_id=sid, snapshot_id=scenario.snapshot.snapshot_id, text="Between the reported tremor onset and a documented completed diazepam administration, what accepted low-chest-motion ECG heart-rate change and wrist AC conductance were observed?", question_class=QuestionClass.Q4, difficulty="complex", authorized_scope=target),
            Question(question_id=f"{sid}-Q4b", scenario_id=sid, snapshot_id=scenario.snapshot.snapshot_id, text="Which source-supported clinical medication action and symptom-onset evidence can be stated for this review, and what remains uncertain?", question_class=QuestionClass.Q4, difficulty="compositional", authorized_scope=target),
        ])
    return questions


def make_scenarios() -> list[Scenario]:
    return [make_scenario(index) for index in range(1, 6)]


def plan_for_question(question: Question, scenario: Scenario) -> InvestigationPlan:
    sid = scenario.scenario_id
    narrow_ref = f"{sid}-R1"
    narrow_policy = f"{sid}-POLICY-NARROW"
    if question.question_class == QuestionClass.Q1:
        return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="accepted coverage and actual support", steps=[ObservationStep(id="obs", args=ObservationArgs(metric="heart_rate", method="chest_ecg")), IntervalStep(id="coverage", args=IntervalArgs(operation="coverage", observation_ref="obs"))], output="coverage")
    if question.question_class == QuestionClass.Q2:
        metric = "pulse_rate" if sid == "D05" else "heart_rate"
        method = "wrist_ppg" if sid == "D05" else "chest_ecg"
        return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="named historical comparison", steps=[ObservationStep(id="obs", args=ObservationArgs(metric=metric, method=method, reference_id=narrow_ref, policy_id=narrow_policy, require_eligibility=True)), IntervalStep(id="summary", args=IntervalArgs(operation="summary", observation_ref="obs")), IntervalStep(id="comparison", args=IntervalArgs(operation="compare_to_named_reference", target_ref="obs", reference_id=narrow_ref, policy_id=narrow_policy))], output="comparison")
    if question.question_class == QuestionClass.Q3:
        return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="configured episode recurrence", steps=[ObservationStep(id="obs", args=ObservationArgs(metric="heart_rate", method="chest_ecg", movement=MovementStratum.LOW, scope_mode="all_authorized")), IntervalStep(id="episodes", args=IntervalArgs(operation="episodes", observation_ref="obs", episode_rule_id=f"{sid}-E1"))], output="episodes")
    if question.question_id.endswith("Q4b"):
        selection = "unique_supported_or_clarify"
        return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="source-supported clinical chronology", steps=[ClinicalStep(id="onset", args=ClinicalEventArgs(concept="tremor", event_type="symptom_onset", selection=selection)), ClinicalStep(id="administration", args=ClinicalEventArgs(concept="diazepam", event_type="medication_administration", action_status=ActionStatus.COMPLETED, evidence_class=EvidenceClass.STRUCTURED_ADMINISTRATION, selection=selection)), ResolveStep(id="sources", args=ResolveArgs(evidence_ids=[f"{sid}-S-C"]))], output="clinical_evidence")
    if int(sid[-2:]) in (3, 4):
        return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="clinical anchor resolution with honest abstention", steps=[ClinicalStep(id="onset", args=ClinicalEventArgs(concept="tremor", event_type="symptom_onset", selection="unique_supported_or_clarify")), ClinicalStep(id="administration", args=ClinicalEventArgs(concept="diazepam", event_type="medication_administration", action_status=ActionStatus.COMPLETED, evidence_class=EvidenceClass.STRUCTURED_ADMINISTRATION, selection="unique_supported_or_clarify"))], output="clinical_evidence")
    return InvestigationPlan(plan_id=f"dev-{question.question_id}", intent="event-anchored multimodal comparison", steps=[ClinicalStep(id="onset", args=ClinicalEventArgs(concept="tremor", event_type="symptom_onset", selection="unique_supported_or_clarify")), ClinicalStep(id="administration", args=ClinicalEventArgs(concept="diazepam", event_type="medication_administration", action_status=ActionStatus.COMPLETED, evidence_class=EvidenceClass.STRUCTURED_ADMINISTRATION, selection="unique_supported_or_clarify")), IntervalStep(id="span", args=IntervalArgs(operation="between_event_anchors", start_ref="onset", end_ref="administration")), ObservationStep(id="hr", args=ObservationArgs(metric="heart_rate", method="chest_ecg", interval_ref="span", reference_id=narrow_ref, policy_id=narrow_policy, require_eligibility=True)), IntervalStep(id="hr_comparison", args=IntervalArgs(operation="compare_to_named_reference", target_ref="hr", reference_id=narrow_ref, policy_id=narrow_policy)), ObservationStep(id="acg", args=ObservationArgs(metric="ac_conductance", method="ac_conductance_100hz", interval_ref="span")), IntervalStep(id="acg_summary", args=IntervalArgs(operation="summary", observation_ref="acg")), ResolveStep(id="sources", args=ResolveArgs(evidence_ids=[f"{sid}-S-C", f"{sid}-S-H", f"{sid}-S-R"]))], output="evidence_linked_comparison")


def make_plans(scenarios: list[Scenario] | None = None, questions: list[Question] | None = None) -> dict[str, InvestigationPlan]:
    scenarios = scenarios or make_scenarios()
    questions = questions or make_questions(scenarios)
    by_id = {item.scenario_id: item for item in scenarios}
    return {question.question_id: plan_for_question(question, by_id[question.scenario_id]) for question in questions}


def make_gold(questions: list[Question] | None = None) -> list[GoldRecord]:
    questions = questions or make_questions()
    records: list[GoldRecord] = []
    for question in questions:
        number = int(question.scenario_id[-2:])
        status = AnswerStatus.ANSWERED
        if number == 2 and question.question_id.endswith("Q1"):
            status = AnswerStatus.PARTIAL
        if number == 2 and question.question_id.endswith("Q4a"):
            status = AnswerStatus.PARTIAL
        if number == 3 and question.question_id.endswith("Q4a"):
            status = AnswerStatus.CLARIFY
        if number == 4 and question.question_id.endswith("Q2"):
            status = AnswerStatus.INSUFFICIENT
        if number == 4 and question.question_id.endswith("Q4a"):
            status = AnswerStatus.INSUFFICIENT
        if number == 4 and question.question_id.endswith("Q4b"):
            status = AnswerStatus.INSUFFICIENT
        if number == 5 and question.question_id.endswith("Q2"):
            status = AnswerStatus.INSUFFICIENT
        slots = [
            GoldSlot(slot_id=f"{question.question_id}-status", kind="status", expected={"status": status.value}, evidence_alternatives=[[f"{question.scenario_id}-S-I"]], material=True),
        ]
        if question.question_class == QuestionClass.Q1:
            slots.extend([
                GoldSlot(slot_id="nominal_coverage", kind="fraction", expected={"coverage_type": "nominal_feature_window"}, evidence_alternatives=[[f"{question.scenario_id}-H1", f"{question.scenario_id}-H2", f"{question.scenario_id}-S-I"]], material=True),
                GoldSlot(slot_id="actual_support", kind="fraction", expected={"coverage_type": "actual_support"}, evidence_alternatives=[[f"{question.scenario_id}-H1", f"{question.scenario_id}-H2", f"{question.scenario_id}-S-I"]], material=True),
            ])
        if question.question_class == QuestionClass.Q2:
            slots.append(GoldSlot(slot_id="named_reference", kind="reference", expected={"reference_id": f"{question.scenario_id}-R1"}, evidence_alternatives=[[f"{question.scenario_id}-S-R"]], material=True))
        if question.question_class == QuestionClass.Q3:
            slots.append(GoldSlot(slot_id="episode_rule", kind="episode", expected={"episode_rule_id": f"{question.scenario_id}-E1"}, evidence_alternatives=[[f"{question.scenario_id}-S-H"]], material=True))
        if question.question_class == QuestionClass.Q4:
            slots.append(GoldSlot(slot_id="clinical_source", kind="event", expected={"source_id": f"{question.scenario_id}-S-C"}, evidence_alternatives=[[f"{question.scenario_id}-S-C"]], material=True))
        records.append(GoldRecord(question_id=question.question_id, snapshot_id=question.snapshot_id, question_class=question.question_class, difficulty=question.difficulty, status=status, required_slots=slots, required_limitations=[], forbidden_inferences=["diagnosis", "treatment effect", "normality"], selection={"included_ids": [], "excluded_ids_with_reasons": []}, worksheet="gold/worksheets/development.md"))
    return records

