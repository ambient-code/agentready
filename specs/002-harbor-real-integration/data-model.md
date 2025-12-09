# Data Model: Harbor Framework Integration

**Feature**: Harbor Framework Real Integration for Terminal-Bench Eval Harness
**Date**: 2025-12-09
**Status**: Complete

---

## Overview

This document defines the data models for Harbor framework integration in the AgentReady eval harness. All models follow AgentReady's existing patterns from `src/agentready/models/` and maintain backward compatibility with the Phase 1 mocked implementation.

---

## Core Entities

### 1. TbenchResult (Existing - Extended)

**Purpose**: Represents the outcome of a single Terminal-Bench evaluation (baseline or assessor test).

**Location**: `src/agentready/services/eval_harness/tbench_runner.py` (dataclass within module)

**Fields**:

| Field | Type | Description | Validation Rules |
|-------|------|-------------|------------------|
| `score` | `float` | Benchmark accuracy score (0.0 to 1.0) | Must be >= 0.0 and <= 1.0 |
| `task_solved` | `bool` | Whether any tasks were successfully resolved | True if resolved_trials > 0 |
| `is_mocked` | `bool` | Indicates if result is from mocked or real Harbor run | True for mocked, False for real |
| `resolved_trials` | `int` (new) | Number of successfully completed tasks | Must be >= 0 |
| `unresolved_trials` | `int` (new) | Number of failed tasks | Must be >= 0 |
| `pass_at_1` | `float` (new) | Single-attempt success rate | Must be >= 0.0 and <= 1.0 |
| `pass_at_3` | `float` (new) | Success rate within 3 attempts | Must be >= 0.0 and <= 1.0 |

**Example**:
```python
@dataclass
class TbenchResult:
    score: float  # Maps to Harbor's "accuracy" field
    task_solved: bool
    is_mocked: bool
    resolved_trials: int = 0
    unresolved_trials: int = 0
    pass_at_1: float = 0.0
    pass_at_3: float = 0.0

    def __post_init__(self):
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Score must be 0.0-1.0, got {self.score}")
        if self.resolved_trials < 0 or self.unresolved_trials < 0:
            raise ValueError("Trial counts cannot be negative")
```

**Backward Compatibility**: Existing Phase 1 code creates `TbenchResult(score, task_solved, is_mocked=True)` - new fields have defaults, so this remains valid.

---

### 2. HarborConfig (New)

**Purpose**: Configuration for Harbor framework subprocess execution.

**Location**: `src/agentready/services/eval_harness/harbor_config.py` (new file)

**Fields**:

| Field | Type | Description | Validation Rules |
|-------|------|-------------|------------------|
| `model` | `str` | LLM model identifier | Must be in ALLOWED_MODELS set |
| `agent` | `str` | Agent identifier | Must be in ALLOWED_AGENTS set |
| `jobs_dir` | `Path` | Output directory for results | Must be absolute path, writable |
| `timeout` | `int` | Subprocess timeout in seconds | Must be > 0, default 3600 |
| `n_concurrent` | `int` | Harbor's internal concurrency | Must be >= 1, default 1 |
| `api_key` | `str` | Anthropic API key | Must not be empty |

**Validation Constants**:
```python
ALLOWED_MODELS = {
    "anthropic/claude-haiku-4-5",
    "anthropic/claude-sonnet-4-5",
}

ALLOWED_AGENTS = {
    "claude-code",
}
```

**Example**:
```python
@dataclass
class HarborConfig:
    model: str
    agent: str
    jobs_dir: Path
    api_key: str
    timeout: int = 3600
    n_concurrent: int = 1

    def __post_init__(self):
        if self.model not in ALLOWED_MODELS:
            raise ValueError(f"Invalid model: {self.model}")
        if self.agent not in ALLOWED_AGENTS:
            raise ValueError(f"Invalid agent: {self.agent}")
        if not self.api_key:
            raise ValueError("API key cannot be empty")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        self.jobs_dir = Path(self.jobs_dir).resolve()
```

**Usage**:
```python
config = HarborConfig(
    model="anthropic/claude-haiku-4-5",
    agent="claude-code",
    jobs_dir=Path("/tmp/tbench-results"),
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)
```

---

### 3. BenchmarkRun (New - Optional, for future batch tracking)

**Purpose**: Metadata for a single benchmark execution (used for aggregation and debugging).

**Location**: `src/agentready/services/eval_harness/models.py` (new file, or inline in CLI)

**Fields**:

| Field | Type | Description | Validation Rules |
|-------|------|-------------|------------------|
| `run_id` | `str` | Unique identifier (UUID) | Generated automatically |
| `repository_path` | `Path` | Path to repository being benchmarked | Must exist |
| `assessor_id` | `str \| None` | Assessor ID (None for baseline) | Optional |
| `result` | `TbenchResult` | Benchmark result | Required |
| `timestamp` | `datetime` | When benchmark was executed | Generated automatically |
| `duration_seconds` | `float` | Execution time | Must be >= 0 |
| `error` | `str \| None` | Error message if benchmark failed | Optional |

**Example**:
```python
@dataclass
class BenchmarkRun:
    repository_path: Path
    assessor_id: str | None
    result: TbenchResult
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    error: str | None = None
```

**Usage** (Future - Phase 3 historical tracking):
```python
run = BenchmarkRun(
    repository_path=Path("/path/to/repo"),
    assessor_id="claude_md",
    result=TbenchResult(score=0.85, task_solved=True, is_mocked=False),
    duration_seconds=347.2,
)
```

**Note**: This entity is **optional** for Phase 2. Current implementation can inline this data in CLI commands without formal model. Include only if needed for batch result storage.

---

### 4. AggregatedResult (New)

**Purpose**: Statistical summary of assessor effectiveness across multiple repositories.

**Location**: Inline in `src/agentready/cli/eval_harness.py` (summarize command) using pandas DataFrame

**Fields** (conceptual - represented as pandas DataFrame columns):

| Column | Type | Description | Validation Rules |
|--------|------|-------------|------------------|
| `assessor_id` | `str` | Assessor identifier | Required |
| `mean_delta` | `float` | Average score improvement | Can be negative (regression) |
| `median_delta` | `float` | Median score improvement | Can be negative |
| `std_delta` | `float` | Standard deviation of deltas | Must be >= 0 |
| `sample_size` | `int` | Number of repositories tested | Must be > 0 |
| `significant` | `bool` | Statistical significance indicator | True if p-value < 0.05 (placeholder) |

**Example** (pandas DataFrame):
```python
import pandas as pd

# Aggregation logic (inline in summarize command)
df = pd.DataFrame(results)  # results = List[Dict[str, Any]]
summary = df.groupby("assessor_id").agg({
    "delta_score": ["mean", "median", "std", "count"],
}).round(2)
summary.columns = ["mean_delta", "median_delta", "std_delta", "sample_size"]
summary["significant"] = summary["mean_delta"].abs() > 0.05  # Placeholder significance test
```

**Output Format** (for reports):
```
Assessor ID       | Mean Δ | Median Δ | Std Δ | Sample Size | Significant?
------------------|--------|----------|-------|-------------|-------------
claude_md         | +0.12  | +0.10    | 0.05  | 15          | ✅ Yes
test_coverage     | +0.08  | +0.07    | 0.06  | 15          | ✅ Yes
dependency_pinning| +0.02  | +0.01    | 0.08  | 12          | ❌ No
```

**Note**: No formal Python class needed - pandas DataFrame provides all aggregation functionality inline.

---

## Data Flow

```text
Repository Path
    ↓
HarborConfig (validation)
    ↓
harbor run subprocess (CLI call)
    ↓
Harbor Output: results.json
    ↓
Parse results.json → TbenchResult
    ↓
(Optional) BenchmarkRun (metadata wrapping)
    ↓
Aggregation (pandas) → AggregatedResult DataFrame
    ↓
Report Generation (markdown/JSON)
```

---

## State Transitions

### TbenchResult State

**States**:
1. **Pending**: Not yet executed (not modeled - implicit)
2. **Mocked** (`is_mocked=True`): Result from Phase 1 deterministic mock
3. **Real** (`is_mocked=False`): Result from actual Harbor framework execution
4. **Failed** (modeled via `error` field in BenchmarkRun, not TbenchResult itself)

**Transition Rules**:
- Mocked results cannot transition to Real (different execution paths)
- Failed benchmarks do not create TbenchResult (exception raised or error logged)

---

## Validation Rules

### 1. Score Ranges
- All probability scores (score, pass_at_1, pass_at_3) must be [0.0, 1.0]
- Trial counts (resolved_trials, unresolved_trials) must be non-negative integers
- Delta scores in aggregation can be negative (indicating regression)

### 2. Path Validation
- All file paths (jobs_dir, repository_path) must be resolved to absolute paths
- Results JSON path must be validated as relative to jobs_dir (prevent path traversal)

### 3. Temporal Constraints
- Benchmark duration_seconds must be non-negative
- Timeout must be positive (enforced in HarborConfig)

### 4. Security Constraints
- Model and agent parameters validated against allowlists before subprocess execution
- API key must not be empty (enforced in HarborConfig)
- Environment variable sanitization (only ANTHROPIC_API_KEY, PATH, HOME exposed)

---

## Integration with Existing Models

### Existing AgentReady Models (src/agentready/models/)

**Not Modified**:
- `Repository`: Represents scanned repository (no changes needed)
- `Attribute`: Quality attribute definition (no changes needed)
- `Finding`: Assessment result (not used in eval harness)
- `Assessment`: Complete assessment report (not used in eval harness)

**Eval Harness Models**:
- `TbenchResult`: Extended with new fields (backward compatible)
- `HarborConfig`: New, self-contained
- `BenchmarkRun`: New, optional
- `AggregatedResult`: Conceptual (pandas DataFrame, no formal model)

---

## JSON Schemas

### Harbor Output Schema (results.json)

**Expected Structure** (from Harbor framework):
```json
{
  "summary": {
    "resolved_trials": 42,
    "unresolved_trials": 8,
    "accuracy": 0.84,
    "pass@1": 0.78,
    "pass@3": 0.84
  },
  "tasks": [
    {
      "task_id": "string",
      "status": "resolved" | "unresolved",
      "score": 0.0 to 1.0,
      "attempts": integer
    }
  ]
}
```

**Parsing Logic**:
```python
def parse_harbor_results(results_path: Path) -> TbenchResult:
    with open(results_path) as f:
        data = json.load(f)

    summary = data["summary"]
    return TbenchResult(
        score=summary["accuracy"],
        task_solved=summary["resolved_trials"] > 0,
        is_mocked=False,
        resolved_trials=summary["resolved_trials"],
        unresolved_trials=summary["unresolved_trials"],
        pass_at_1=summary["pass@1"],
        pass_at_3=summary["pass@3"],
    )
```

---

### AgentReady Aggregation Output Schema (JSON export)

**For Machine Consumption**:
```json
{
  "aggregation_date": "2025-12-09T10:30:00Z",
  "total_repositories": 15,
  "assessors": [
    {
      "assessor_id": "claude_md",
      "mean_delta": 0.12,
      "median_delta": 0.10,
      "std_delta": 0.05,
      "sample_size": 15,
      "significant": true
    }
  ]
}
```

---

## Examples

### Example 1: Real Harbor Benchmark Execution

```python
# 1. Create configuration
config = HarborConfig(
    model="anthropic/claude-haiku-4-5",
    agent="claude-code",
    jobs_dir=Path("/tmp/tbench-results"),
    api_key=os.environ["ANTHROPIC_API_KEY"],
)

# 2. Execute benchmark (subprocess call)
result = run_harbor_benchmark(repo_path, config)

# 3. Result object
print(result)
# TbenchResult(
#     score=0.84,
#     task_solved=True,
#     is_mocked=False,
#     resolved_trials=42,
#     unresolved_trials=8,
#     pass_at_1=0.78,
#     pass_at_3=0.84
# )
```

---

### Example 2: Aggregation Across Repositories

```python
# 1. Collect results from multiple benchmarks
results = [
    {"assessor_id": "claude_md", "delta_score": 0.10},
    {"assessor_id": "claude_md", "delta_score": 0.12},
    {"assessor_id": "claude_md", "delta_score": 0.15},
    {"assessor_id": "test_coverage", "delta_score": 0.05},
    {"assessor_id": "test_coverage", "delta_score": 0.08},
]

# 2. Aggregate with pandas
import pandas as pd
df = pd.DataFrame(results)
summary = df.groupby("assessor_id").agg({
    "delta_score": ["mean", "median", "std", "count"]
}).round(2)

# 3. Output
print(summary)
#                   delta_score
#                          mean median  std count
# assessor_id
# claude_md                0.12   0.12 0.03     3
# test_coverage            0.07   0.07 0.02     2
```

---

## Design Decisions

### Decision 1: Extend TbenchResult vs Create New Model

**Chosen**: Extend existing `TbenchResult` with new optional fields

**Rationale**:
- Maintains backward compatibility (new fields have defaults)
- Avoids model proliferation (simpler codebase)
- Natural mapping to Harbor's output schema

**Alternative Rejected**: Create separate `HarborTbenchResult` model
- Reason: Unnecessary abstraction, increases complexity

---

### Decision 2: Inline Aggregation vs Separate Service

**Chosen**: Inline pandas aggregation in CLI `summarize` command

**Rationale**:
- Aggregation logic is <30 lines with pandas
- No need for separate service class (violates doubleagent.md anti-patterns)
- Simplified approach (76% code reduction goal)

**Alternative Rejected**: Create `CrossRepoAggregator` service class
- Reason: Over-engineering for simple DataFrame operations

---

### Decision 3: BenchmarkRun Model - Optional vs Required

**Chosen**: Optional (can be deferred to Phase 3)

**Rationale**:
- Phase 2 focus: Real Harbor integration and aggregation
- BenchmarkRun metadata useful for historical tracking (Phase 3 feature)
- Current implementation can work without formal model (inline dict/dataclass)

**Alternative Rejected**: Implement immediately
- Reason: Not required for Phase 2 MVP, adds complexity

---

## Next Steps

1. ✅ Data models designed
2. ⏭️ Create JSON schema contracts in `contracts/` directory
3. ⏭️ Generate quickstart guide for Harbor setup and first benchmark run
4. ⏭️ Update agent context with new models and Harbor integration patterns

---

**Document Status**: Complete
**Last Updated**: 2025-12-09
**Ready for Contracts Phase**: ✅ Yes
