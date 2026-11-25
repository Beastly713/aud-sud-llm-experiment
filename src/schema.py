"""Versioned, shared contracts for the development experiment.

The models are intentionally data contracts rather than clinical domain objects. They
preserve evidence provenance and the protocol's missingness/uncertainty distinctions.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator


SCHEMA_VERSION = "d2-experiment.schema.v1"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class Missingness(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    INAPPLICABLE = "inapplicable"


class SupportKind(str, Enum):
    INTERVALS = "intervals"
    FRACTION_ONLY = "fraction_only"
    UNKNOWN = "unknown"


class Acceptance(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class MovementStratum(str, Enum):
    LOW = "low"
    ELEVATED = "elevated"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"


class ClockStatus(str, Enum):
    ALIGNED = "aligned"
    BOUNDED = "bounded"
    UNKNOWN = "unknown"


class ReferenceStatus(str, Enum):
    UNAVAILABLE = "unavailable"
    PROVISIONAL = "provisional"
    SUPPORTED_DESCRIPTIVE = "supported_descriptive"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INDETERMINATE = "indeterminate"


class AssertionStatus(str, Enum):
    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"


class Experiencer(str, Enum):
    PATIENT = "patient"
    OTHER = "other"
    UNKNOWN = "unknown"


class EvidenceClass(str, Enum):
    STRUCTURED_ADMINISTRATION = "structured_administration"
    STRUCTURED_ORDER = "structured_order"
    NARRATIVE_REPORT = "narrative_report"
    ASSESSMENT = "assessment"
    EXTRACTED_CANDIDATE = "extracted_candidate"


class ActionStatus(str, Enum):
    COMPLETED = "completed"
    ORDERED = "ordered"
    HELD = "held"
    NOT_DONE = "not_done"
    REPORTED = "reported"
    UNKNOWN = "unknown"


class TemporalPrecision(str, Enum):
    INSTANT = "instant"
    MINUTE = "minute"
    INTERVAL = "interval"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class ReviewState(str, Enum):
    UNASSESSED = "unassessed"
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    REVIEWED = "reviewed"


class OccurrenceLinkStatus(str, Enum):
    LINKED = "linked"
    UNRESOLVED = "unresolved"
    CONTRADICTED = "contradicted"
    NONE = "none"


class QuestionClass(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class AnswerStatus(str, Enum):
    ANSWERED = "answered"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    CLARIFY = "clarify"


class CoverageType(str, Enum):
    NOMINAL_FEATURE_WINDOW = "nominal_feature_window"
    ACTUAL_SUPPORT = "actual_support"
    KNOWN_LOWER_BOUND = "known_lower_bound"
    GROUPING_SPAN = "grouping_span"


class ClaimKind(str, Enum):
    OBSERVATION = "observation"
    COVERAGE = "coverage"
    COMPARISON = "comparison"
    EPISODE = "episode"
    EVENT = "event"
    LIMITATION = "limitation"
    OTHER = "other"


class Interval(StrictModel):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def valid_order(self) -> "Interval":
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("interval endpoints must be timezone-aware")
        if self.start >= self.end:
            raise ValueError("interval must be non-empty and use [start,end) semantics")
        return self

    @property
    def seconds(self) -> int:
        return int((self.end - self.start).total_seconds())


class TimeBounds(StrictModel):
    lower: datetime
    upper: datetime
    precision: TemporalPrecision

    @model_validator(mode="after")
    def valid_bounds(self) -> "TimeBounds":
        if self.lower.tzinfo is None or self.upper.tzinfo is None:
            raise ValueError("event times must be timezone-aware")
        if self.lower > self.upper:
            raise ValueError("lower event bound must not exceed upper bound")
        if self.precision == TemporalPrecision.INSTANT and self.lower != self.upper:
            raise ValueError("instant event time must have equal bounds")
        return self


class SourceRef(StrictModel):
    source_id: str
    span: str | None = None
    time_range: Interval | None = None


class SourceRecord(StrictModel):
    source_id: str
    source_type: str
    locator: str
    content: str | None = None
    revision: str
    covered_scope: list[Interval] = Field(default_factory=list)
    unknown_scope: list[Interval] = Field(default_factory=list)
    recording_available: bool | None = None


class MeasurementValue(StrictModel):
    value: float | int | str | None
    units: str | None = None
    missingness: Missingness = Missingness.PRESENT

    @model_validator(mode="after")
    def missingness_matches_value(self) -> "MeasurementValue":
        if self.value is None and self.missingness == Missingness.PRESENT:
            raise ValueError("null value must have an explicit non-present missingness state")
        if self.value is not None and self.missingness != Missingness.PRESENT:
            raise ValueError("non-null value cannot have a non-present missingness state")
        return self


class Observation(StrictModel):
    observation_id: str
    participant_id: str
    metric: str
    method: str
    node: str
    site: str | None = None
    configuration: str | None = None
    value: MeasurementValue
    nominal: Interval
    acceptance: Acceptance
    acceptance_reasons: list[str] = Field(default_factory=list)
    support_kind: SupportKind
    actual_support: list[Interval] = Field(default_factory=list)
    support_fraction: float | None = None
    support_denominator_seconds: int | None = None
    timing_quality: str
    context_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    feature_version: str

    @model_validator(mode="after")
    def support_shape(self) -> "Observation":
        if self.support_kind == SupportKind.INTERVALS and not self.actual_support:
            if self.acceptance == Acceptance.ACCEPTED:
                raise ValueError("accepted interval-supported observation needs actual support")
        if self.support_kind == SupportKind.FRACTION_ONLY:
            if self.support_fraction is None or self.support_denominator_seconds is None:
                raise ValueError("fraction-only support needs fraction and denominator")
            if not 0 <= self.support_fraction <= 1:
                raise ValueError("support fraction must be in [0,1]")
        if self.acceptance == Acceptance.REJECTED and self.value.missingness == Missingness.PRESENT:
            raise ValueError("rejected observation cannot carry a present value")
        return self


class ContextAnnotation(StrictModel):
    context_id: str
    participant_id: str
    node: str
    nominal: Interval
    actual_support: list[Interval] = Field(default_factory=list)
    movement: MovementStratum
    clock_status: ClockStatus
    source_ids: list[str] = Field(default_factory=list)
    linked_observation_ids: list[str] = Field(default_factory=list)
    imu_summary: dict[str, float] | None = None
    ambient_qualifier: str | None = None


class HistoricalReference(StrictModel):
    reference_id: str
    policy_id: str
    metric: str
    method: str
    site: str | None = None
    configuration: str | None = None
    epoch_label: str
    event_cutoff: datetime
    as_of: datetime
    status: ReferenceStatus
    center: float | None = None
    units: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    comparison_units: list[str] = Field(default_factory=list)
    spread: float | None = None
    revision: str

    @model_validator(mode="after")
    def reference_value(self) -> "HistoricalReference":
        if self.status == ReferenceStatus.UNAVAILABLE and self.center is not None:
            raise ValueError("unavailable reference cannot have a center")
        if self.status != ReferenceStatus.UNAVAILABLE and self.center is None:
            raise ValueError("available reference needs a center")
        if self.event_cutoff.tzinfo is None or self.as_of.tzinfo is None:
            raise ValueError("reference cutoffs must be timezone-aware")
        return self


class EligibilityRecord(StrictModel):
    observation_id: str
    reference_id: str
    policy_id: str
    revision: str
    status: EligibilityStatus
    reasons: list[str] = Field(default_factory=list)


class ClinicalEvent(StrictModel):
    mention_id: str
    participant_id: str
    event_type: str
    concept: str
    assertion: AssertionStatus
    experiencer: Experiencer
    evidence_class: EvidenceClass
    action_status: ActionStatus
    event_time: TimeBounds | None = None
    documented_at: datetime
    occurrence_id: str | None = None
    occurrence_link_status: OccurrenceLinkStatus = OccurrenceLinkStatus.NONE
    semantic_support: ReviewState
    source_review: ReviewState
    structural_review: ReviewState
    source_ids: list[str] = Field(default_factory=list)
    original_text: str
    contradiction_link: str | None = None


class EpisodeRule(StrictModel):
    rule_id: str
    metric: str
    method: str
    threshold_operator: Literal[">=", ">", "<=", "<"]
    threshold: float
    minimum_grouping_seconds: int
    maximum_gap_seconds: int
    required_acceptance: Acceptance = Acceptance.ACCEPTED
    required_movement: MovementStratum | None = None
    reference_id: str | None = None
    policy_id: str | None = None


class InvestigationPolicy(StrictModel):
    policy_id: str
    version: str
    metric: str
    method: str
    compatible_nodes: list[str]
    reference_ids: list[str] = Field(default_factory=list)
    allowed_operations: list[str]
    episode_rule_ids: list[str] = Field(default_factory=list)
    denominator_definitions: dict[str, str]


class EvidenceSnapshot(StrictModel):
    scenario_id: str
    participant_id: str
    snapshot_id: str
    available_as_of: datetime
    source_event_cutoff: datetime
    timezone: str
    authorized_scope: list[Interval]
    source_inventory: list[str]
    revision: str


class Scenario(StrictModel):
    scenario_id: str
    participant_id: str
    snapshot: EvidenceSnapshot
    sources: list[SourceRecord]
    observations: list[Observation]
    contexts: list[ContextAnnotation]
    references: list[HistoricalReference]
    eligibility: list[EligibilityRecord]
    clinical_events: list[ClinicalEvent]
    policies: list[InvestigationPolicy]
    episode_rules: list[EpisodeRule]
    synthetic_disclosure: str = "Synthetic engineering fixture; not patient data or clinical ground truth."

    @model_validator(mode="after")
    def consistent_scope(self) -> "Scenario":
        if self.snapshot.scenario_id != self.scenario_id or self.snapshot.participant_id != self.participant_id:
            raise ValueError("snapshot identity does not match scenario")
        if any(o.participant_id != self.participant_id for o in self.observations):
            raise ValueError("observation participant mismatch")
        if any(e.participant_id != self.participant_id for e in self.clinical_events):
            raise ValueError("clinical event participant mismatch")
        source_ids = {s.source_id for s in self.sources}
        if any(source_id not in source_ids for o in self.observations for source_id in o.source_ids):
            raise ValueError("observation references an unknown source")
        return self


class Question(StrictModel):
    question_id: str
    scenario_id: str
    snapshot_id: str
    text: str
    question_class: QuestionClass
    difficulty: Literal["foundational", "compositional", "complex"]
    authorized_scope: list[Interval]
    requested_status: AnswerStatus | None = None


class NumericValue(StrictModel):
    kind: Literal["numeric"] = "numeric"
    value: float
    unit: str


class CategoricalValue(StrictModel):
    kind: Literal["categorical"] = "categorical"
    value: str


class DurationValue(StrictModel):
    kind: Literal["duration"] = "duration"
    seconds: int


class FractionValue(StrictModel):
    kind: Literal["fraction"] = "fraction"
    numerator: int
    denominator: int
    fraction: float
    coverage_type: CoverageType

    @model_validator(mode="after")
    def correct_fraction(self) -> "FractionValue":
        if self.denominator <= 0 or self.numerator < 0 or self.numerator > self.denominator:
            raise ValueError("invalid fraction bounds")
        if abs(self.fraction - self.numerator / self.denominator) > 1e-9:
            raise ValueError("fraction does not match numerator/denominator")
        return self


class TimeRangeValue(StrictModel):
    kind: Literal["time_range"] = "time_range"
    lower: datetime
    upper: datetime
    precision: TemporalPrecision


class ListValue(StrictModel):
    kind: Literal["list"] = "list"
    values: list[str | float | int]


TypedValue = Annotated[
    Union[NumericValue, CategoricalValue, DurationValue, FractionValue, TimeRangeValue, ListValue],
    Field(discriminator="kind"),
]


class Finding(StrictModel):
    claim: str
    claim_kind: ClaimKind = ClaimKind.OTHER
    metric: str | None = None
    method: str | None = None
    site: str | None = None
    requested_statistic: str | None = None
    value: TypedValue | None = None
    interval: Interval | None = None
    reference_id: str | None = None
    policy_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    selected_ids: list[str] = Field(default_factory=list)
    denominator_seconds: int | None = None
    coverage_type: CoverageType | None = None
    occurrence_id: str | None = None
    action_status: ActionStatus | None = None
    assertion_status: AssertionStatus | None = None
    episode_rule_id: str | None = None


class Limitation(StrictModel):
    claim: str
    source_ids: list[str] = Field(default_factory=list)
    selected_ids: list[str] = Field(default_factory=list)
    reason_code: str


class CommonAnswer(StrictModel):
    schema_version: str = SCHEMA_VERSION
    status: AnswerStatus
    findings: list[Finding] = Field(default_factory=list)
    limitations: list[Limitation] = Field(default_factory=list)
    clarification: str | None = None

    @model_validator(mode="after")
    def status_semantics(self) -> "CommonAnswer":
        if self.status == AnswerStatus.CLARIFY and not self.clarification:
            raise ValueError("clarify answers need a clarification request")
        if self.status == AnswerStatus.INSUFFICIENT and not self.limitations:
            raise ValueError("insufficient answers need a limitation")
        return self


class GeneratedProgram(StrictModel):
    schema_version: str = SCHEMA_VERSION
    code: str



class GoldSlot(StrictModel):
    slot_id: str
    kind: str
    expected: dict[str, object]
    evidence_alternatives: list[list[str]]
    material: bool = True
    absolute_tolerance: float | None = None


class GoldRecord(StrictModel):
    question_id: str
    snapshot_id: str
    question_class: QuestionClass
    difficulty: str
    status: AnswerStatus
    required_slots: list[GoldSlot]
    required_limitations: list[GoldSlot] = Field(default_factory=list)
    permitted_additional_facts: list[dict[str, object]] = Field(default_factory=list)
    forbidden_inferences: list[str] = Field(default_factory=list)
    selection: dict[str, object]
    worksheet: str
    review_author: str = "pending-human-review"
    review_checker: str = "pending-human-review"
    review_resolved: bool = False


class ClinicalEventArgs(StrictModel):
    operation: Literal["select", "group_occurrences"] = "select"
    concept: str | None = None
    event_type: str | None = None
    action_status: ActionStatus | None = None
    assertion: AssertionStatus | None = None
    evidence_class: EvidenceClass | None = None
    selection: Literal["all", "unique_supported_or_clarify", "first_supported", "last_supported"] = "all"
    anchor_role: str | None = None


class ObservationArgs(StrictModel):
    operation: Literal["select", "list_intervals"] = "select"
    metric: str
    method: str
    interval_ref: str | None = None
    quality: Acceptance | None = Acceptance.ACCEPTED
    movement: MovementStratum | None = None
    reference_id: str | None = None
    policy_id: str | None = None
    require_eligibility: bool = False
    scope_mode: Literal["question_scope", "all_authorized"] = "question_scope"


class IntervalArgs(StrictModel):
    operation: Literal[
        "between_event_anchors",
        "coverage",
        "summary",
        "compare_to_named_reference",
        "episodes",
        "fixed_interval",
    ]
    observation_ref: str | None = None
    start_ref: str | None = None
    end_ref: str | None = None
    interval_ref: str | None = None
    target_ref: str | None = None
    reference_id: str | None = None
    policy_id: str | None = None
    statistic: Literal["median", "mean", "min", "max", "count"] = "median"
    episode_rule_id: str | None = None
    uncertainty_policy: Literal["preserve_bounds_or_abstain", "bounded_subpart"] = "preserve_bounds_or_abstain"


class ResolveArgs(StrictModel):
    operation: Literal["resolve"] = "resolve"
    evidence_ids: list[str]


class ClinicalStep(StrictModel):
    id: str
    tool: Literal["query_clinical_events"] = "query_clinical_events"
    args: ClinicalEventArgs


class ObservationStep(StrictModel):
    id: str
    tool: Literal["query_observations"] = "query_observations"
    args: ObservationArgs


class IntervalStep(StrictModel):
    id: str
    tool: Literal["analyze_intervals"] = "analyze_intervals"
    args: IntervalArgs


class ResolveStep(StrictModel):
    id: str
    tool: Literal["resolve_evidence"] = "resolve_evidence"
    args: ResolveArgs


PlanStep = Annotated[Union[ClinicalStep, ObservationStep, IntervalStep, ResolveStep], Field(discriminator="tool")]


class InvestigationPlan(StrictModel):
    plan_id: str
    intent: str
    participant_scope: Literal["authorized_context_only"] = "authorized_context_only"
    steps: list[PlanStep]
    output: str

    @model_validator(mode="after")
    def dependency_graph_shape(self) -> "InvestigationPlan":
        if not self.steps or len(self.steps) > 12:
            raise ValueError("plan must contain between one and twelve steps")
        ids = [step.id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("plan step IDs must be unique")
        known = set()
        for step in self.steps:
            refs = []
            args = step.args
            if isinstance(args, IntervalArgs):
                refs = [args.observation_ref, args.start_ref, args.end_ref, args.interval_ref, args.target_ref]
            elif isinstance(args, ObservationArgs):
                refs = [args.interval_ref]
            refs = [ref for ref in refs if ref]
            if any(ref not in known for ref in refs):
                raise ValueError(f"step {step.id} has a missing or forward dependency")
            known.add(step.id)
        return self


class EventSelectionResult(StrictModel):
    result_type: Literal["event_selection"] = "event_selection"
    selected_mention_ids: list[str]
    candidate_mention_ids: list[str]
    occurrence_ids: list[str]
    time: TimeBounds | None = None
    status: AnswerStatus
    limitations: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ObservationSelectionResult(StrictModel):
    result_type: Literal["observation_selection"] = "observation_selection"
    selected_observation_ids: list[str]
    excluded_observation_ids: list[str]
    exclusion_reasons: dict[str, str]
    scope: Interval | None = None
    reference_id: str | None = None
    policy_id: str | None = None
    limitations: list[str] = Field(default_factory=list)


class IntervalResult(StrictModel):
    result_type: Literal["interval_result"] = "interval_result"
    operation: str
    interval: Interval | None = None
    selected_ids: list[str] = Field(default_factory=list)
    excluded_ids: list[str] = Field(default_factory=list)
    facts: list[Finding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    dependency_ids: list[str] = Field(default_factory=list)


class ResolvedSource(StrictModel):
    result_type: Literal["resolved_source"] = "resolved_source"
    source_id: str
    source_type: str
    locator: str
    content: str | None
    revision: str
    scope_status: Literal["covered", "unknown", "outside_scope"]


IntermediateResult = Annotated[
    Union[EventSelectionResult, ObservationSelectionResult, IntervalResult, ResolvedSource],
    Field(discriminator="result_type"),
]


class EvidenceBundle(StrictModel):
    question_id: str
    snapshot_id: str
    plan_id: str
    effective_scope: list[Interval]
    computed_facts: list[Finding]
    limitations: list[Limitation]
    source_ids: list[str]
    selected_revisions: dict[str, str]
    internal_fact_ids: dict[str, str] = Field(default_factory=dict)


class ExecutionTrace(StrictModel):
    question_id: str
    scenario_id: str | None = None
    arm: Literal["A", "B", "C"]
    cohort: Literal["development", "primary", "reproducibility"]
    tuple_id: str
    prompt_hashes: dict[str, str]
    model_id: str
    calls: int
    transport_retries: int = 0
    plan: dict[str, object] | None = None
    code: str | None = None
    tool_trace: list[dict[str, object]] = Field(default_factory=list)
    raw_answer: dict[str, object] | None = None
    delivered_answer: dict[str, object] | None = None
    failure_class: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None


class HumanAnnotation(StrictModel):
    tuple_id: str
    sgis: int
    claim_annotations: list[dict[str, object]] = Field(default_factory=list)
    error_tags: list[str] = Field(default_factory=list)
    reviewer_id: str
    second_review: bool = False
    rgfr_correct: int = 0
    rgfr_total: int = 0
    rnc_correct: int = 0
    rnc_total: int = 0
    gcp_supported: int = 0
    gcp_emitted: int = 0
    aha: int = 0
    cei: int = 0

    @field_validator("sgis")
    @classmethod
    def binary(cls, value: int) -> int:
        if value not in (0, 1):
            raise ValueError("SGIS must be binary")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> "HumanAnnotation":
        for numerator, denominator, label in (
            (self.rgfr_correct, self.rgfr_total, "RGFR"),
            (self.rnc_correct, self.rnc_total, "RNC"),
            (self.gcp_supported, self.gcp_emitted, "GCP"),
        ):
            if numerator < 0 or denominator < 0 or numerator > denominator:
                raise ValueError(f"invalid {label} annotation counts")
        if self.aha not in (0, 1) or self.cei not in (0, 1):
            raise ValueError("AHA and CEI annotations must be binary")
        return self


class ScoreRow(StrictModel):
    tuple_id: str
    scenario_id: str | None = None
    arm: Literal["A", "B", "C"]
    cohort: Literal["development", "primary", "reproducibility"]
    sgis: int
    rgfr_correct: int = 0
    rgfr_total: int = 0
    rnc_correct: int = 0
    rnc_total: int = 0
    gcp_supported: int = 0
    gcp_emitted: int = 0
    aha: int = 0
    cei: int = 0
    error_tags: list[str] = Field(default_factory=list)
