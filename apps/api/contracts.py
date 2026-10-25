"""Versioned wire contracts. Edit here, then export schema and generate TypeScript."""

from __future__ import annotations

import math
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

VERSION = "1.0.0"
Scalar = str | bool | float
OptionId = Literal["A", "B"]
Pack = Literal["offer_xray", "fine_print", "open"]
Source = Literal["user", "default", "data"]
Probability = Annotated[float, Field(ge=0, le=1)]
Finite = Annotated[float, Field(allow_inf_nan=False)]
SessionStatus = Literal[
    "created",
    "extracting",
    "interviewing",
    "building",
    "simulating",
    "analyzing",
    "ready",
    "failed",
    "cancelled",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_default=True)


class Normal(Contract):
    type: Literal["normal"]
    mean: Finite
    std: Annotated[float, Field(ge=0)]


class Lognormal(Contract):
    type: Literal["lognormal"]
    mu: Finite
    sigma: Annotated[float, Field(ge=0)]


class Uniform(Contract):
    type: Literal["uniform"]
    low: Finite
    high: Finite

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.low >= self.high:
            raise ValueError("uniform low must be below high")
        return self


class Triangular(Contract):
    type: Literal["triangular"]
    low: Finite
    mode: Finite
    high: Finite

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if not self.low <= self.mode <= self.high or self.low == self.high:
            raise ValueError("triangular requires low <= mode <= high and low < high")
        return self


class Bernoulli(Contract):
    type: Literal["bernoulli"]
    p: Probability


class Discrete(Contract):
    type: Literal["discrete"]
    values: list[Finite] = Field(min_length=1)
    probs: list[Probability] = Field(min_length=1)

    @model_validator(mode="after")
    def probabilities(self) -> Self:
        if len(self.values) != len(self.probs) or len(set(self.values)) != len(self.values):
            raise ValueError("discrete values must be unique and match probability count")
        if not math.isclose(sum(self.probs), 1, abs_tol=1e-9):
            raise ValueError("discrete probabilities must sum to one")
        return self


Distribution = Annotated[
    Normal | Lognormal | Uniform | Triangular | Bernoulli | Discrete,
    Field(discriminator="type"),
]


class SweepRange(Contract):
    low: Finite
    high: Finite

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.low >= self.high:
            raise ValueError("range low must be below high")
        return self


class Provenance(Contract):
    source: Source
    source_ref: str = Field(min_length=1)
    confirmed: bool = False


class VariableBase(Provenance):
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    editable: bool = True
    sweep_range: SweepRange | None = None


class FixedVariable(VariableBase):
    kind: Literal["fixed"]
    value: Scalar


class DistributionVariable(VariableBase):
    kind: Literal["distribution"]
    dist: Distribution


Variable = Annotated[FixedVariable | DistributionVariable, Field(discriminator="kind")]


class Event(Provenance):
    name: str = Field(min_length=1)
    prob_per_year: Probability
    effect: str = Field(min_length=1)


class Option(Contract):
    id: OptionId
    label: str = Field(min_length=1)


class Metrics(Contract):
    primary: str = Field(min_length=1)
    direction: Literal["maximize", "minimize"]
    others: list[str] = Field(default_factory=list)


class DecisionSpec(Contract):
    schema_version: Literal["1.0.0"] = VERSION
    decision_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    pack: Pack
    horizon_years: int = Field(ge=1, le=20)
    step: Literal["month"] = "month"
    currency: Literal["INR"] = "INR"
    options: list[Option] = Field(min_length=2, max_length=2)
    variables: list[Variable] = Field(min_length=1)
    events: list[Event] = Field(default_factory=list)
    metrics: Metrics

    @model_validator(mode="after")
    def unique_names(self) -> Self:
        if {o.id for o in self.options} != {"A", "B"}:
            raise ValueError("exactly options A and B are required")
        for group in (self.variables, self.events):
            names = [item.name for item in group]
            if len(names) != len(set(names)):
                raise ValueError("variable and event names must be unique within each group")
        return self


class Percentiles(Contract):
    p5: list[Finite]
    p10: list[Finite]
    p25: list[Finite]
    p50: list[Finite]
    p75: list[Finite]
    p90: list[Finite]
    p95: list[Finite]

    @model_validator(mode="after")
    def consistent(self) -> Self:
        arrays = list(self.model_dump().values())
        if not arrays[0] or len({len(a) for a in arrays}) != 1:
            raise ValueError("percentile arrays must have the same nonzero length")
        if any(list(column) != sorted(column) for column in zip(*arrays, strict=True)):
            raise ValueError("percentiles must be ordered at every time point")
        return self


class Histogram(Contract):
    edges: list[Finite] = Field(min_length=2)
    counts: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_bins(self) -> Self:
        if len(self.edges) != len(self.counts) + 1 or any(c < 0 for c in self.counts):
            raise ValueError("histogram needs one more edge than nonnegative counts")
        if any(a >= b for a, b in zip(self.edges, self.edges[1:], strict=False)):
            raise ValueError("histogram edges must increase")
        return self


class MetricSummary(Contract):
    median: Finite
    unit: str
    hist: Histogram


class PathStory(Contract):
    id: int = Field(ge=0)
    events: list[str]


class OptionResults(Contract):
    label: str
    percentiles: Percentiles
    sampled_paths: list[list[Finite]] = Field(min_length=1, max_length=1000)
    path_stories: list[PathStory] = Field(min_length=1, max_length=1000)
    metrics: dict[str, MetricSummary]


class OptionPair(Contract):
    A: OptionResults
    B: OptionResults


class WinProbability(Contract):
    A: Probability
    B: Probability
    tie: Probability = 0

    @model_validator(mode="after")
    def total(self) -> Self:
        if not math.isclose(self.A + self.B + self.tie, 1, abs_tol=1e-9):
            raise ValueError("win probabilities plus ties must sum to one")
        return self


class SweepPoint(Contract):
    value: Finite
    p_win_A: Probability


class Sensitivity(Contract):
    variable: str
    unit: str
    swing: Probability
    points: list[SweepPoint] = Field(min_length=2)


class FlipPoint(Contract):
    variable: str
    threshold: Finite
    unit: str
    direction: Literal["below", "above"]
    winner_after: OptionId
    swing: Probability
    bracket: SweepRange

    @model_validator(mode="after")
    def within_bracket(self) -> Self:
        if not self.bracket.low <= self.threshold <= self.bracket.high:
            raise ValueError("threshold must be inside its search bracket")
        return self


class Frontier(Contract):
    x_var: str
    y_var: str
    x_values: list[Finite] = Field(min_length=2)
    y_values: list[Finite] = Field(min_length=2)
    grid: list[list[Probability]]

    @model_validator(mode="after")
    def dimensions(self) -> Self:
        if len(self.grid) != len(self.y_values):
            raise ValueError("frontier rows correspond to y_values")
        if any(len(row) != len(self.x_values) for row in self.grid):
            raise ValueError("frontier columns correspond to x_values")
        for axis in (self.x_values, self.y_values):
            if any(a >= b for a, b in zip(axis, axis[1:], strict=False)):
                raise ValueError("frontier axes must strictly increase")
        return self


class Results(Contract):
    schema_version: Literal["1.0.0"] = VERSION
    branch_id: str
    pack: Pack
    data_kind: Literal["mock", "simulation"]
    horizon_years: int = Field(ge=1, le=20)
    currency: Literal["INR"] = "INR"
    path_count: int = Field(gt=0)
    seed: int = Field(ge=0)
    x_points: list[str]
    primary_metric: str
    objective: Literal["maximize", "minimize"]
    options: OptionPair
    p_win: WinProbability
    sensitivities: list[Sensitivity]
    flip_points: list[FlipPoint]
    frontier: Frontier | None
    story: str
    assumptions: list[Variable]

    @model_validator(mode="after")
    def aligned_results(self) -> Self:
        expected = [f"Q{q}-Y{y}" for y in range(1, self.horizon_years + 1) for q in range(1, 5)]
        if self.x_points != expected:
            raise ValueError("x_points must contain every quarter, without an origin point")
        ids = []
        for option in (self.options.A, self.options.B):
            if len(option.percentiles.p50) != len(expected):
                raise ValueError("percentiles must match x_points")
            if any(len(path) != len(expected) for path in option.sampled_paths):
                raise ValueError("sampled paths must match x_points")
            option_ids = [s.id for s in option.path_stories]
            if len(option_ids) != len(option.sampled_paths) or len(set(option_ids)) != len(
                option_ids
            ):
                raise ValueError("one unique story ID is required per sampled path")
            if any(i >= self.path_count for i in option_ids):
                raise ValueError("story IDs must be valid simulation path indices")
            ids.append(option_ids)
            if self.primary_metric not in option.metrics:
                raise ValueError("primary metric missing from option")
            for summary in option.metrics.values():
                if sum(summary.hist.counts) != self.path_count:
                    raise ValueError("histogram must account for every simulated path")
        if ids[0] != ids[1]:
            raise ValueError("A/B samples must use the same ordered path IDs")
        return self


class SpecChange(Contract):
    variable: str
    before: Scalar
    after: Scalar


class Branch(Contract):
    id: str
    session_id: str
    parent_id: str | None
    label: str
    status: SessionStatus
    change_type: Literal["root", "param", "structural"]
    diff: list[SpecChange] = Field(default_factory=list)
    change_summary: str | None = None
    spec: DecisionSpec
    model_version_id: str | None = None
    checkpoint_id: str | None = None
    model_status: Literal["building", "passed", "failed", "fallback"] | None = None


class Evidence(Contract):
    document_id: str
    page: int = Field(ge=1)
    quote: str = Field(min_length=1)
    matched: bool


class Term(Contract):
    option_id: OptionId
    field: str
    value: Scalar | None
    unit: str
    confidence: Probability
    evidence: Evidence | None
    confirmed: bool = False


class CreateSessionRequest(Contract):
    pack: Pack
    dilemma_text: str = Field(min_length=1, max_length=10000)


class CreateSessionResponse(Contract):
    session_id: str


class UploadDocumentResponse(Contract):
    document_id: str
    extracted: list[Term]


class PatchTermsRequest(Contract):
    terms: list[Term] = Field(min_length=1)


class OkResponse(Contract):
    ok: Literal[True] = True


class InterviewQuestion(Contract):
    id: str
    text: str
    answer_type: Literal["value", "range", "choice"]
    variable: str
    required: bool
    choices: list[Scalar] = Field(default_factory=list)


class InterviewNextResponse(Contract):
    done: bool
    question: InterviewQuestion | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.done != (self.question is None):
            raise ValueError("done is true exactly when question is null")
        return self


class InterviewAnswerRequest(Contract):
    question_id: str
    value: Scalar | SweepRange


class BuildResponse(Contract):
    branch_id: str


class WhatIfRequest(Contract):
    parent_branch_id: str
    text: str = Field(min_length=1, max_length=2000)


class WhatIfResponse(Contract):
    type: Literal["param", "structural", "out_of_scope"]
    branch_id: str | None
    message: str | None = None
    suggestions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def branch_for_valid_change(self) -> Self:
        if (self.type == "out_of_scope") != (self.branch_id is None):
            raise ValueError("only out-of-scope requests have no branch")
        return self


class BranchesResponse(Contract):
    branches: list[Branch]


class ReportResponse(Contract):
    branch: Branch
    results: Results
    disclaimer: str
    rule_sources: list[str]


class ErrorResponse(Contract):
    code: str
    message: str
    recoverable: bool


class AgentStatusData(Contract):
    status: SessionStatus
    text: str


class ExtractDoneData(Contract):
    document_id: str
    terms: list[Term]


class CodeChunkData(Contract):
    file: Literal["model.py", "test_model.py"]
    text: str
    attempt: int = Field(ge=1, le=3)
    reset: bool = False


class TestResultData(Contract):
    name: str
    passed: bool
    message: str
    attempt: int = Field(ge=1, le=3)


class SandboxForkData(Contract):
    fork_id: str
    parent: str
    purpose: Literal["test", "main", "sweep", "threshold", "frontier", "whatif"]
    option_id: OptionId | None = None


class SimProgressData(Contract):
    fork_id: str
    done: int = Field(ge=0)
    total: int = Field(gt=0)

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if self.done > self.total:
            raise ValueError("done cannot exceed total")
        return self


class ReadyData(Contract):
    branch_id: str


class LlmCallData(Contract):
    tier: Literal["nano", "super", "ultra"]
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    ms: int = Field(ge=0)


class ErrorData(Contract):
    where: str
    message: str
    recoverable: bool


class EventEnvelope(Contract):
    schema_version: Literal["1.0.0"] = VERSION
    id: str
    session_id: str
    branch_id: str | None
    sequence: int = Field(ge=1)
    elapsed_ms: int = Field(ge=0)
    data_kind: Literal["mock", "simulation"]


class ExtractDoneEvent(EventEnvelope):
    event: Literal["extract.done"]
    data: ExtractDoneData


class AgentStatusEvent(EventEnvelope):
    event: Literal["agent.status"]
    data: AgentStatusData


class CodeChunkEvent(EventEnvelope):
    event: Literal["code.chunk"]
    data: CodeChunkData


class TestResultEvent(EventEnvelope):
    event: Literal["test.result"]
    data: TestResultData


class SandboxForkEvent(EventEnvelope):
    event: Literal["sandbox.fork"]
    data: SandboxForkData


class SimProgressEvent(EventEnvelope):
    event: Literal["sim.progress"]
    data: SimProgressData


class ResultsReadyEvent(EventEnvelope):
    event: Literal["results.ready"]
    data: ReadyData


class FlipReadyEvent(EventEnvelope):
    event: Literal["flip.ready"]
    data: ReadyData


class LlmCallEvent(EventEnvelope):
    event: Literal["llm.call"]
    data: LlmCallData


class ErrorEvent(EventEnvelope):
    event: Literal["error"]
    data: ErrorData


StreamEvent = Annotated[
    ExtractDoneEvent
    | AgentStatusEvent
    | CodeChunkEvent
    | TestResultEvent
    | SandboxForkEvent
    | SimProgressEvent
    | ResultsReadyEvent
    | FlipReadyEvent
    | LlmCallEvent
    | ErrorEvent,
    Field(discriminator="event"),
]


class ContractBundle(Contract):
    """Schema roots; never sent as one HTTP payload."""

    decision_spec: DecisionSpec
    results: Results
    branch: Branch
    stream_event: StreamEvent
    create_session_request: CreateSessionRequest
    create_session_response: CreateSessionResponse
    upload_document_response: UploadDocumentResponse
    patch_terms_request: PatchTermsRequest
    ok_response: OkResponse
    interview_next_response: InterviewNextResponse
    interview_answer_request: InterviewAnswerRequest
    build_response: BuildResponse
    whatif_request: WhatIfRequest
    whatif_response: WhatIfResponse
    branches_response: BranchesResponse
    report_response: ReportResponse
    error_response: ErrorResponse


class DistributionSchema(RootModel[Distribution]):
    pass


class VariableSchema(RootModel[Variable]):
    pass


class StreamEventSchema(RootModel[StreamEvent]):
    pass
