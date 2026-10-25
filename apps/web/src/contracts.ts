/* Generated from apps/api/contracts.py. Do not edit by hand. */

export type SchemaVersion = "1.0.0";
export type DecisionId = string;
export type Title = string;
export type Pack = "offer_xray" | "fine_print" | "open";
export type HorizonYears = number;
export type Step = "month";
export type Currency = "INR";
/**
 * @minItems 2
 * @maxItems 2
 */
export type Options = [Option, Option];
export type Id = "A" | "B";
export type Label = string;
/**
 * @minItems 1
 */
export type Variables = [FixedVariable | DistributionVariable, ...(FixedVariable | DistributionVariable)[]];
export type Source = "user" | "default" | "data";
export type SourceRef = string;
export type Confirmed = boolean;
export type Name = string;
export type Unit = string;
export type Editable = boolean;
export type Low = number;
export type High = number;
export type Kind = "fixed";
export type Value = string | boolean | number;
export type Source1 = "user" | "default" | "data";
export type SourceRef1 = string;
export type Confirmed1 = boolean;
export type Name1 = string;
export type Unit1 = string;
export type Editable1 = boolean;
export type Kind1 = "distribution";
export type Dist = Normal | Lognormal | Uniform | Triangular | Bernoulli | Discrete;
export type Type = "normal";
export type Mean = number;
export type Std = number;
export type Type1 = "lognormal";
export type Mu = number;
export type Sigma = number;
export type Type2 = "uniform";
export type Low1 = number;
export type High1 = number;
export type Type3 = "triangular";
export type Low2 = number;
export type Mode = number;
export type High2 = number;
export type Type4 = "bernoulli";
export type P = number;
export type Type5 = "discrete";
/**
 * @minItems 1
 */
export type Values = [number, ...number[]];
/**
 * @minItems 1
 */
export type Probs = [number, ...number[]];
export type Source2 = "user" | "default" | "data";
export type SourceRef2 = string;
export type Confirmed2 = boolean;
export type Name2 = string;
export type ProbPerYear = number;
export type Effect = string;
export type Events = Event[];
export type Primary = string;
export type Direction = "maximize" | "minimize";
export type Others = string[];
export type SchemaVersion1 = "1.0.0";
export type BranchId = string;
export type Pack1 = "offer_xray" | "fine_print" | "open";
export type DataKind = "mock" | "simulation";
export type HorizonYears1 = number;
export type Currency1 = "INR";
export type PathCount = number;
export type Seed = number;
export type XPoints = string[];
export type PrimaryMetric = string;
export type Objective = "maximize" | "minimize";
export type Label1 = string;
export type P5 = number[];
export type P10 = number[];
export type P25 = number[];
export type P50 = number[];
export type P75 = number[];
export type P90 = number[];
export type P95 = number[];
/**
 * @minItems 1
 * @maxItems 1000
 */
export type SampledPaths = [number[], ...number[][]];
/**
 * @minItems 1
 * @maxItems 1000
 */
export type PathStories = [PathStory, ...PathStory[]];
export type Id1 = number;
export type Events1 = string[];
export type Median = number;
export type Unit2 = string;
/**
 * @minItems 2
 */
export type Edges = [number, number, ...number[]];
/**
 * @minItems 1
 */
export type Counts = [number, ...number[]];
export type A = number;
export type B = number;
export type Tie = number;
export type Variable = string;
export type Unit3 = string;
export type Swing = number;
/**
 * @minItems 2
 */
export type Points = [SweepPoint, SweepPoint, ...SweepPoint[]];
export type Value1 = number;
export type PWinA = number;
export type Sensitivities = Sensitivity[];
export type Variable1 = string;
export type Threshold = number;
export type Unit4 = string;
export type Direction1 = "below" | "above";
export type WinnerAfter = "A" | "B";
export type Swing1 = number;
export type FlipPoints = FlipPoint[];
export type XVar = string;
export type YVar = string;
/**
 * @minItems 2
 */
export type XValues = [number, number, ...number[]];
/**
 * @minItems 2
 */
export type YValues = [number, number, ...number[]];
export type Grid = number[][];
export type Story = string;
export type Assumptions = (FixedVariable | DistributionVariable)[];
export type Id2 = string;
export type SessionId = string;
export type ParentId = string | null;
export type Label2 = string;
export type Status =
  | "created"
  | "extracting"
  | "interviewing"
  | "building"
  | "simulating"
  | "analyzing"
  | "ready"
  | "failed"
  | "cancelled";
export type ChangeType = "root" | "param" | "structural";
export type Variable2 = string;
export type Before = string | boolean | number;
export type After = string | boolean | number;
export type Diff = SpecChange[];
export type ChangeSummary = string | null;
export type ModelVersionId = string | null;
export type CheckpointId = string | null;
export type ModelStatus = ("building" | "passed" | "failed" | "fallback") | null;
export type StreamEvent =
  | ExtractDoneEvent
  | AgentStatusEvent
  | CodeChunkEvent
  | TestResultEvent
  | SandboxForkEvent
  | SimProgressEvent
  | ResultsReadyEvent
  | FlipReadyEvent
  | LlmCallEvent
  | ErrorEvent;
export type SchemaVersion2 = "1.0.0";
export type Id3 = string;
export type SessionId1 = string;
export type BranchId1 = string | null;
export type Sequence = number;
export type ElapsedMs = number;
export type DataKind1 = "mock" | "simulation";
export type Event1 = "extract.done";
export type DocumentId = string;
export type OptionId = "A" | "B";
export type Field = string;
export type Value2 = string | boolean | number | null;
export type Unit5 = string;
export type Confidence = number;
export type DocumentId1 = string;
export type Page = number;
export type Quote = string;
export type Matched = boolean;
export type Confirmed3 = boolean;
export type Terms = Term[];
export type SchemaVersion3 = "1.0.0";
export type Id4 = string;
export type SessionId2 = string;
export type BranchId2 = string | null;
export type Sequence1 = number;
export type ElapsedMs1 = number;
export type DataKind2 = "mock" | "simulation";
export type Event2 = "agent.status";
export type Status1 =
  | "created"
  | "extracting"
  | "interviewing"
  | "building"
  | "simulating"
  | "analyzing"
  | "ready"
  | "failed"
  | "cancelled";
export type Text = string;
export type SchemaVersion4 = "1.0.0";
export type Id5 = string;
export type SessionId3 = string;
export type BranchId3 = string | null;
export type Sequence2 = number;
export type ElapsedMs2 = number;
export type DataKind3 = "mock" | "simulation";
export type Event3 = "code.chunk";
export type File = "model.py" | "test_model.py";
export type Text1 = string;
export type Attempt = number;
export type Reset = boolean;
export type SchemaVersion5 = "1.0.0";
export type Id6 = string;
export type SessionId4 = string;
export type BranchId4 = string | null;
export type Sequence3 = number;
export type ElapsedMs3 = number;
export type DataKind4 = "mock" | "simulation";
export type Event4 = "test.result";
export type Name3 = string;
export type Passed = boolean;
export type Message = string;
export type Attempt1 = number;
export type SchemaVersion6 = "1.0.0";
export type Id7 = string;
export type SessionId5 = string;
export type BranchId5 = string | null;
export type Sequence4 = number;
export type ElapsedMs4 = number;
export type DataKind5 = "mock" | "simulation";
export type Event5 = "sandbox.fork";
export type ForkId = string;
export type Parent = string;
export type Purpose = "test" | "main" | "sweep" | "threshold" | "frontier" | "whatif";
export type OptionId1 = ("A" | "B") | null;
export type SchemaVersion7 = "1.0.0";
export type Id8 = string;
export type SessionId6 = string;
export type BranchId6 = string | null;
export type Sequence5 = number;
export type ElapsedMs5 = number;
export type DataKind6 = "mock" | "simulation";
export type Event6 = "sim.progress";
export type ForkId1 = string;
export type Done = number;
export type Total = number;
export type SchemaVersion8 = "1.0.0";
export type Id9 = string;
export type SessionId7 = string;
export type BranchId7 = string | null;
export type Sequence6 = number;
export type ElapsedMs6 = number;
export type DataKind7 = "mock" | "simulation";
export type Event7 = "results.ready";
export type BranchId8 = string;
export type SchemaVersion9 = "1.0.0";
export type Id10 = string;
export type SessionId8 = string;
export type BranchId9 = string | null;
export type Sequence7 = number;
export type ElapsedMs7 = number;
export type DataKind8 = "mock" | "simulation";
export type Event8 = "flip.ready";
export type SchemaVersion10 = "1.0.0";
export type Id11 = string;
export type SessionId9 = string;
export type BranchId10 = string | null;
export type Sequence8 = number;
export type ElapsedMs8 = number;
export type DataKind9 = "mock" | "simulation";
export type Event9 = "llm.call";
export type Tier = "nano" | "super" | "ultra";
export type TokensIn = number;
export type TokensOut = number;
export type Ms = number;
export type SchemaVersion11 = "1.0.0";
export type Id12 = string;
export type SessionId10 = string;
export type BranchId11 = string | null;
export type Sequence9 = number;
export type ElapsedMs9 = number;
export type DataKind10 = "mock" | "simulation";
export type Event10 = "error";
export type Where = string;
export type Message1 = string;
export type Recoverable = boolean;
export type Pack2 = "offer_xray" | "fine_print" | "open";
export type DilemmaText = string;
export type SessionId11 = string;
export type DocumentId2 = string;
export type Extracted = Term[];
/**
 * @minItems 1
 */
export type Terms1 = [Term, ...Term[]];
export type Ok = true;
export type Done1 = boolean;
export type Id13 = string;
export type Text2 = string;
export type AnswerType = "value" | "range" | "choice";
export type Variable3 = string;
export type Required = boolean;
export type Choices = (string | boolean | number)[];
export type QuestionId = string;
export type Value3 = string | boolean | number | SweepRange;
export type BranchId12 = string;
export type ParentBranchId = string;
export type Text3 = string;
export type Type6 = "param" | "structural" | "out_of_scope";
export type BranchId13 = string | null;
export type Message2 = string | null;
export type Suggestions = string[];
export type Branches = Branch[];
export type Disclaimer = string;
export type RuleSources = string[];
export type Code = string;
export type Message3 = string;
export type Recoverable1 = boolean;

/**
 * Schema roots; never sent as one HTTP payload.
 */
export interface ContractBundle {
  decision_spec: DecisionSpec;
  results: Results;
  branch: Branch;
  stream_event: StreamEvent;
  create_session_request: CreateSessionRequest;
  create_session_response: CreateSessionResponse;
  upload_document_response: UploadDocumentResponse;
  patch_terms_request: PatchTermsRequest;
  ok_response: OkResponse;
  interview_next_response: InterviewNextResponse;
  interview_answer_request: InterviewAnswerRequest;
  build_response: BuildResponse;
  whatif_request: WhatIfRequest;
  whatif_response: WhatIfResponse;
  branches_response: BranchesResponse;
  report_response: ReportResponse;
  error_response: ErrorResponse;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "DecisionSpec".
 */
export interface DecisionSpec {
  schema_version?: SchemaVersion;
  decision_id: DecisionId;
  title: Title;
  pack: Pack;
  horizon_years: HorizonYears;
  step?: Step;
  currency?: Currency;
  options: Options;
  variables: Variables;
  events?: Events;
  metrics: Metrics;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Option".
 */
export interface Option {
  id: Id;
  label: Label;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "FixedVariable".
 */
export interface FixedVariable {
  source: Source;
  source_ref: SourceRef;
  confirmed?: Confirmed;
  name: Name;
  unit: Unit;
  editable?: Editable;
  sweep_range?: SweepRange | null;
  kind: Kind;
  value: Value;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SweepRange".
 */
export interface SweepRange {
  low: Low;
  high: High;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "DistributionVariable".
 */
export interface DistributionVariable {
  source: Source1;
  source_ref: SourceRef1;
  confirmed?: Confirmed1;
  name: Name1;
  unit: Unit1;
  editable?: Editable1;
  sweep_range?: SweepRange | null;
  kind: Kind1;
  dist: Dist;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Normal".
 */
export interface Normal {
  type: Type;
  mean: Mean;
  std: Std;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Lognormal".
 */
export interface Lognormal {
  type: Type1;
  mu: Mu;
  sigma: Sigma;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Uniform".
 */
export interface Uniform {
  type: Type2;
  low: Low1;
  high: High1;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Triangular".
 */
export interface Triangular {
  type: Type3;
  low: Low2;
  mode: Mode;
  high: High2;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Bernoulli".
 */
export interface Bernoulli {
  type: Type4;
  p: P;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Discrete".
 */
export interface Discrete {
  type: Type5;
  values: Values;
  probs: Probs;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Event".
 */
export interface Event {
  source: Source2;
  source_ref: SourceRef2;
  confirmed?: Confirmed2;
  name: Name2;
  prob_per_year: ProbPerYear;
  effect: Effect;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Metrics".
 */
export interface Metrics {
  primary: Primary;
  direction: Direction;
  others?: Others;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Results".
 */
export interface Results {
  schema_version?: SchemaVersion1;
  branch_id: BranchId;
  pack: Pack1;
  data_kind: DataKind;
  horizon_years: HorizonYears1;
  currency?: Currency1;
  path_count: PathCount;
  seed: Seed;
  x_points: XPoints;
  primary_metric: PrimaryMetric;
  objective: Objective;
  options: OptionPair;
  p_win: WinProbability;
  sensitivities: Sensitivities;
  flip_points: FlipPoints;
  frontier: Frontier | null;
  story: Story;
  assumptions: Assumptions;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "OptionPair".
 */
export interface OptionPair {
  A: OptionResults;
  B: OptionResults;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "OptionResults".
 */
export interface OptionResults {
  label: Label1;
  percentiles: Percentiles;
  sampled_paths: SampledPaths;
  path_stories: PathStories;
  metrics: Metrics1;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Percentiles".
 */
export interface Percentiles {
  p5: P5;
  p10: P10;
  p25: P25;
  p50: P50;
  p75: P75;
  p90: P90;
  p95: P95;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "PathStory".
 */
export interface PathStory {
  id: Id1;
  events: Events1;
}
export interface Metrics1 {
  [k: string]: MetricSummary;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "MetricSummary".
 */
export interface MetricSummary {
  median: Median;
  unit: Unit2;
  hist: Histogram;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Histogram".
 */
export interface Histogram {
  edges: Edges;
  counts: Counts;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "WinProbability".
 */
export interface WinProbability {
  A: A;
  B: B;
  tie?: Tie;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Sensitivity".
 */
export interface Sensitivity {
  variable: Variable;
  unit: Unit3;
  swing: Swing;
  points: Points;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SweepPoint".
 */
export interface SweepPoint {
  value: Value1;
  p_win_A: PWinA;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "FlipPoint".
 */
export interface FlipPoint {
  variable: Variable1;
  threshold: Threshold;
  unit: Unit4;
  direction: Direction1;
  winner_after: WinnerAfter;
  swing: Swing1;
  bracket: SweepRange;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Frontier".
 */
export interface Frontier {
  x_var: XVar;
  y_var: YVar;
  x_values: XValues;
  y_values: YValues;
  grid: Grid;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Branch".
 */
export interface Branch {
  id: Id2;
  session_id: SessionId;
  parent_id: ParentId;
  label: Label2;
  status: Status;
  change_type: ChangeType;
  diff?: Diff;
  change_summary?: ChangeSummary;
  spec: DecisionSpec;
  model_version_id?: ModelVersionId;
  checkpoint_id?: CheckpointId;
  model_status?: ModelStatus;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SpecChange".
 */
export interface SpecChange {
  variable: Variable2;
  before: Before;
  after: After;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ExtractDoneEvent".
 */
export interface ExtractDoneEvent {
  schema_version?: SchemaVersion2;
  id: Id3;
  session_id: SessionId1;
  branch_id: BranchId1;
  sequence: Sequence;
  elapsed_ms: ElapsedMs;
  data_kind: DataKind1;
  event: Event1;
  data: ExtractDoneData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ExtractDoneData".
 */
export interface ExtractDoneData {
  document_id: DocumentId;
  terms: Terms;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Term".
 */
export interface Term {
  option_id: OptionId;
  field: Field;
  value: Value2;
  unit: Unit5;
  confidence: Confidence;
  evidence: Evidence | null;
  confirmed?: Confirmed3;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "Evidence".
 */
export interface Evidence {
  document_id: DocumentId1;
  page: Page;
  quote: Quote;
  matched: Matched;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "AgentStatusEvent".
 */
export interface AgentStatusEvent {
  schema_version?: SchemaVersion3;
  id: Id4;
  session_id: SessionId2;
  branch_id: BranchId2;
  sequence: Sequence1;
  elapsed_ms: ElapsedMs1;
  data_kind: DataKind2;
  event: Event2;
  data: AgentStatusData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "AgentStatusData".
 */
export interface AgentStatusData {
  status: Status1;
  text: Text;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "CodeChunkEvent".
 */
export interface CodeChunkEvent {
  schema_version?: SchemaVersion4;
  id: Id5;
  session_id: SessionId3;
  branch_id: BranchId3;
  sequence: Sequence2;
  elapsed_ms: ElapsedMs2;
  data_kind: DataKind3;
  event: Event3;
  data: CodeChunkData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "CodeChunkData".
 */
export interface CodeChunkData {
  file: File;
  text: Text1;
  attempt: Attempt;
  reset?: Reset;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "TestResultEvent".
 */
export interface TestResultEvent {
  schema_version?: SchemaVersion5;
  id: Id6;
  session_id: SessionId4;
  branch_id: BranchId4;
  sequence: Sequence3;
  elapsed_ms: ElapsedMs3;
  data_kind: DataKind4;
  event: Event4;
  data: TestResultData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "TestResultData".
 */
export interface TestResultData {
  name: Name3;
  passed: Passed;
  message: Message;
  attempt: Attempt1;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SandboxForkEvent".
 */
export interface SandboxForkEvent {
  schema_version?: SchemaVersion6;
  id: Id7;
  session_id: SessionId5;
  branch_id: BranchId5;
  sequence: Sequence4;
  elapsed_ms: ElapsedMs4;
  data_kind: DataKind5;
  event: Event5;
  data: SandboxForkData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SandboxForkData".
 */
export interface SandboxForkData {
  fork_id: ForkId;
  parent: Parent;
  purpose: Purpose;
  option_id?: OptionId1;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SimProgressEvent".
 */
export interface SimProgressEvent {
  schema_version?: SchemaVersion7;
  id: Id8;
  session_id: SessionId6;
  branch_id: BranchId6;
  sequence: Sequence5;
  elapsed_ms: ElapsedMs5;
  data_kind: DataKind6;
  event: Event6;
  data: SimProgressData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "SimProgressData".
 */
export interface SimProgressData {
  fork_id: ForkId1;
  done: Done;
  total: Total;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ResultsReadyEvent".
 */
export interface ResultsReadyEvent {
  schema_version?: SchemaVersion8;
  id: Id9;
  session_id: SessionId7;
  branch_id: BranchId7;
  sequence: Sequence6;
  elapsed_ms: ElapsedMs6;
  data_kind: DataKind7;
  event: Event7;
  data: ReadyData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ReadyData".
 */
export interface ReadyData {
  branch_id: BranchId8;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "FlipReadyEvent".
 */
export interface FlipReadyEvent {
  schema_version?: SchemaVersion9;
  id: Id10;
  session_id: SessionId8;
  branch_id: BranchId9;
  sequence: Sequence7;
  elapsed_ms: ElapsedMs7;
  data_kind: DataKind8;
  event: Event8;
  data: ReadyData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "LlmCallEvent".
 */
export interface LlmCallEvent {
  schema_version?: SchemaVersion10;
  id: Id11;
  session_id: SessionId9;
  branch_id: BranchId10;
  sequence: Sequence8;
  elapsed_ms: ElapsedMs8;
  data_kind: DataKind9;
  event: Event9;
  data: LlmCallData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "LlmCallData".
 */
export interface LlmCallData {
  tier: Tier;
  tokens_in: TokensIn;
  tokens_out: TokensOut;
  ms: Ms;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ErrorEvent".
 */
export interface ErrorEvent {
  schema_version?: SchemaVersion11;
  id: Id12;
  session_id: SessionId10;
  branch_id: BranchId11;
  sequence: Sequence9;
  elapsed_ms: ElapsedMs9;
  data_kind: DataKind10;
  event: Event10;
  data: ErrorData;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ErrorData".
 */
export interface ErrorData {
  where: Where;
  message: Message1;
  recoverable: Recoverable;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "CreateSessionRequest".
 */
export interface CreateSessionRequest {
  pack: Pack2;
  dilemma_text: DilemmaText;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "CreateSessionResponse".
 */
export interface CreateSessionResponse {
  session_id: SessionId11;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "UploadDocumentResponse".
 */
export interface UploadDocumentResponse {
  document_id: DocumentId2;
  extracted: Extracted;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "PatchTermsRequest".
 */
export interface PatchTermsRequest {
  terms: Terms1;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "OkResponse".
 */
export interface OkResponse {
  ok?: Ok;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "InterviewNextResponse".
 */
export interface InterviewNextResponse {
  done: Done1;
  question: InterviewQuestion | null;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "InterviewQuestion".
 */
export interface InterviewQuestion {
  id: Id13;
  text: Text2;
  answer_type: AnswerType;
  variable: Variable3;
  required: Required;
  choices?: Choices;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "InterviewAnswerRequest".
 */
export interface InterviewAnswerRequest {
  question_id: QuestionId;
  value: Value3;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "BuildResponse".
 */
export interface BuildResponse {
  branch_id: BranchId12;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "WhatIfRequest".
 */
export interface WhatIfRequest {
  parent_branch_id: ParentBranchId;
  text: Text3;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "WhatIfResponse".
 */
export interface WhatIfResponse {
  type: Type6;
  branch_id: BranchId13;
  message?: Message2;
  suggestions?: Suggestions;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "BranchesResponse".
 */
export interface BranchesResponse {
  branches: Branches;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ReportResponse".
 */
export interface ReportResponse {
  branch: Branch;
  results: Results;
  disclaimer: Disclaimer;
  rule_sources: RuleSources;
}
/**
 * This interface was referenced by `ContractBundle`'s JSON-Schema
 * via the `definition` "ErrorResponse".
 */
export interface ErrorResponse {
  code: Code;
  message: Message3;
  recoverable: Recoverable1;
}
