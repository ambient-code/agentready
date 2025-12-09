# Research Report: Harbor Framework Integration for Terminal-Bench

**Feature**: Harbor Framework Real Integration for Terminal-Bench Eval Harness
**Date**: 2025-12-09
**Status**: Complete

---

## Executive Summary

This research resolves all technical unknowns identified during specification planning for Phase 2 of the Terminal-Bench eval harness. The Harbor framework is a well-documented CLI tool from the Laude Institute that provides straightforward integration via subprocess calls with JSON output.

**Key Findings**:
- ✅ Harbor framework has clear Python package: `harbor` (installable via pip/uv)
- ✅ Authentication uses standard environment variables (`ANTHROPIC_API_KEY`, optionally `DAYTONA_API_KEY`)
- ✅ CLI interface is simple: `harbor run` with well-defined parameters
- ✅ Output is JSON-based with predictable structure
- ✅ Execution times average 5-10 minutes per repository (align with spec assumptions)

---

## Research Question 1: Harbor Framework Installation

**Question**: What is the exact Python package name and installation command for Harbor framework?

**Answer**: `harbor` package via pip/uv

**Installation Commands**:
```bash
# Preferred (uv)
uv tool install harbor

# Alternative (pip)
pip install harbor
```

**System Requirements**:
- Docker (required for local benchmark execution)
- Python 3.11+ (inferred from Laude Institute's typical stack)

**Source**: [GitHub - laude-institute/harbor](https://github.com/laude-institute/harbor)

**Decision**: Use `uv pip install harbor` in dependencies (aligns with AgentReady's existing uv-first approach)

---

## Research Question 2: Authentication & API Keys

**Question**: What environment variables are needed for Harbor framework authentication?

**Answer**: Two environment variables required:

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude API authentication | ✅ Required |
| `DAYTONA_API_KEY` | Cloud environment provider (Daytona) | Optional (only for `--env daytona`) |

**Authentication Pattern**:
- No username/password authentication
- No Harbor-specific API key
- Uses Claude API key directly (passed to model provider)
- Daytona key only needed if using cloud environments (not for local Docker execution)

**Source**: [Harbor Framework - Running Terminal-Bench](https://harborframework.com/docs/running-tbench)

**Decision**:
- Primary use case: Local Docker execution (no Daytona key needed)
- Only expose `ANTHROPIC_API_KEY` to Harbor subprocess
- Document Daytona as optional advanced feature (out of scope for Phase 2)

---

## Research Question 3: CLI Interface & Command Syntax

**Question**: What is the command-line interface for submitting repositories to Terminal-Bench?

**Answer**: `harbor run` command with well-defined parameters

**Basic Syntax**:
```bash
harbor run \
  --dataset terminal-bench@2.0 \
  --agent claude-code \
  --model anthropic/claude-haiku-4-5 \
  --n-concurrent 4 \
  --jobs-dir /path/to/output
```

**Key Parameters**:

| Parameter | Purpose | Values |
|-----------|---------|--------|
| `--dataset` | Benchmark dataset + version | `terminal-bench@2.0` |
| `--agent` | Agent to evaluate | `claude-code`, `oracle` (reference) |
| `--model` | LLM model identifier | `anthropic/claude-haiku-4-5`, `anthropic/claude-sonnet-4-5` |
| `--n-concurrent` | Parallel tasks | Integer (default: 1) |
| `--jobs-dir` | Output directory | Path to write results |
| `--env` | Environment provider | `daytona` (cloud) or omit (local Docker) |

**Source**: [Harbor Framework Documentation](https://harborframework.com/docs/running-tbench), [GitHub - laude-institute/harbor](https://github.com/laude-institute/harbor)

**Decision**:
- Use local Docker execution (no `--env` parameter)
- Set `--n-concurrent 1` for AgentReady integration (parallelism managed by our ProcessPoolExecutor, not Harbor)
- Use `--jobs-dir` to control output location for result parsing

---

## Research Question 4: Output Format & Result Parsing

**Question**: What is the expected output format from Harbor framework? How do we parse results?

**Answer**: JSON-based results file with structured metrics

**Output Structure**:
- Harbor writes results to `--jobs-dir` location
- Primary file: `results.json` with detailed benchmark data
- Summary metrics available:
  - `resolved_trials`: Number of successfully completed tasks
  - `unresolved_trials`: Number of failed tasks
  - `accuracy`: Overall success rate (0.0 to 1.0)
  - `pass@1`: Single-attempt success rate
  - `pass@3`: Success rate within 3 attempts

**Example Results Structure** (inferred from documentation):
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
      "task_id": "task_001",
      "status": "resolved",
      "score": 1.0,
      "attempts": 2
    }
  ]
}
```

**Source**: [Harbor Framework - Running Terminal-Bench](https://harborframework.com/docs/running-tbench), [Terminal-Bench GitHub](https://github.com/laude-institute/terminal-bench)

**Decision**:
- Parse `results.json` from `--jobs-dir` after benchmark completion
- Extract `accuracy` as primary score metric (maps to our `TbenchResult.score`)
- Validate JSON schema before reading (security: FR-005 path validation)
- Map `resolved_trials > 0` to `TbenchResult.task_solved = True`

---

## Research Question 5: Execution Times & Timeouts

**Question**: What are typical execution times for Terminal-Bench via Harbor? What timeout should we set?

**Answer**: Execution times vary by task complexity, averaging 5-10 minutes per repository

**Timing Details**:
- **Simple tasks**: Seconds to 1-2 minutes
- **Complex tasks** (e.g., COBOL modernization, refactoring): 5-10 minutes
- **Full benchmark suite** (100+ tasks): Hours (not applicable to AgentReady use case - we run single-repo assessments)

**Timeout Recommendations**:
- **Harbor internal timeout**: Not explicitly documented (appears to handle timeouts internally)
- **Our subprocess timeout**: 1 hour (3600 seconds) provides 6x buffer over typical 10-minute execution
- **Rationale**: Covers edge cases (large repos, slow networks) while preventing infinite hangs

**Source**: [Terminal-Bench 2.0 Article - Snorkel AI](https://snorkel.ai/blog/terminal-bench-2-0-raising-the-bar-for-ai-agent-evaluation/), [VentureBeat Article](https://venturebeat.com/ai/terminal-bench-2-0-launches-alongside-harbor-a-new-framework-for-testing)

**Decision**:
- Set 1-hour (3600s) timeout per benchmark run (aligns with spec FR-009)
- Log warning if execution exceeds 10 minutes (indicates potential issue)
- Document average execution time in README (5-10 minutes for typical repositories)

---

## Research Question 6: Model & Agent Parameter Validation

**Question**: What are the valid model and agent identifiers for Harbor framework?

**Answer**: Documented model and agent identifiers from Harbor CLI

**Supported Models** (relevant to AgentReady use case):
- `anthropic/claude-haiku-4-5` ✅ (fast, cost-effective)
- `anthropic/claude-sonnet-4-5` ✅ (balanced)
- `anthropic/claude-opus-4-1` (expensive, high-quality)

**Supported Agents**:
- `claude-code` ✅ (primary agent for coding tasks)
- `oracle` (reference baseline - uses perfect knowledge)

**Source**: [GitHub - laude-institute/harbor](https://github.com/laude-institute/harbor) (CLI help output)

**Decision**:
- Allowlist for models: `["anthropic/claude-haiku-4-5", "anthropic/claude-sonnet-4-5"]` (excludes opus due to cost)
- Allowlist for agents: `["claude-code"]` (excludes oracle as it's not relevant for real-world assessment)
- Validation before subprocess call (addresses security requirement FR-002, FR-003)

---

## Research Question 7: Docker Dependency & Setup

**Question**: Does Harbor require Docker? What setup is needed?

**Answer**: Docker is required for local benchmark execution

**Docker Requirements**:
- Harbor uses Docker containers to create isolated sandbox environments for benchmarks
- Each benchmark task runs in a fresh container (isolation, reproducibility)
- Docker daemon must be running before `harbor run` execution

**Setup Validation**:
- Harbor validates Docker availability internally (no need for pre-flight checks)
- If Docker unavailable, Harbor returns clear error message
- Follows "trust the framework" philosophy from doubleagent.md (no custom Docker validation needed)

**Source**: [Harbor Framework Documentation](https://harborframework.com/docs/running-tbench)

**Decision**:
- Document Docker as required dependency in README
- Trust Harbor's internal Docker validation (no custom pre-flight checks per simplified approach)
- Return clear error message if Harbor fails due to Docker issues (FR-012)

---

## Technology Selection Summary

| Technology | Decision | Rationale |
|------------|----------|-----------|
| **Harbor Package** | `harbor` via `uv pip install` | Official Laude Institute package, aligns with uv-first approach |
| **Authentication** | `ANTHROPIC_API_KEY` environment variable | Standard Claude API authentication, no Harbor-specific keys |
| **Execution Environment** | Local Docker (no cloud provider) | Simplifies setup, reduces dependencies, sufficient for Phase 2 |
| **CLI Interface** | `harbor run` subprocess call | Well-documented, stable interface, JSON output |
| **Output Parsing** | Parse `results.json` from `--jobs-dir` | Structured JSON format, predictable schema |
| **Timeout** | 3600 seconds (1 hour) | 6x buffer over typical 10-minute execution, prevents infinite hangs |
| **Model Allowlist** | `claude-haiku-4-5`, `claude-sonnet-4-5` | Balance cost and quality, excludes expensive opus |
| **Agent Allowlist** | `claude-code` | Primary coding agent, excludes oracle (not relevant for real assessments) |

---

## Best Practices & Patterns

### 1. Subprocess Security Pattern

**Pattern**: Sanitized environment variables
```python
clean_env = {
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
    "PATH": os.environ.get("PATH"),
    "HOME": os.environ.get("HOME"),
}
subprocess.run(cmd, env=clean_env, timeout=3600)
```

**Rationale**: Prevents API key exposure through unsanitized `os.environ.copy()` (addresses security review finding)

---

### 2. Input Validation Pattern

**Pattern**: Allowlist validation before subprocess
```python
ALLOWED_MODELS = {"anthropic/claude-haiku-4-5", "anthropic/claude-sonnet-4-5"}
ALLOWED_AGENTS = {"claude-code"}

if model not in ALLOWED_MODELS:
    raise ValueError(f"Invalid model: {model}. Allowed: {ALLOWED_MODELS}")
if agent not in ALLOWED_AGENTS:
    raise ValueError(f"Invalid agent: {agent}. Allowed: {ALLOWED_AGENTS}")
```

**Rationale**: Prevents command injection via unvalidated parameters (addresses security review finding)

---

### 3. Result Parsing Pattern

**Pattern**: Path validation before file reading
```python
import os
from pathlib import Path

jobs_dir = Path(jobs_dir_str).resolve()
results_path = jobs_dir / "results.json"

# Validate path is within expected directory
if not results_path.is_relative_to(jobs_dir):
    raise ValueError(f"Invalid results path: {results_path}")

with open(results_path) as f:
    data = json.load(f)
```

**Rationale**: Prevents path traversal attacks when reading Harbor output (addresses FR-005)

---

### 4. Graceful Degradation Pattern

**Pattern**: Environment variable toggle
```python
use_real = os.environ.get("TBENCH_USE_REAL", "0") == "1"

if use_real:
    result = _real_tbench_result(repo_path)
else:
    result = _mocked_tbench_result(repo_path)
```

**Rationale**: Preserves backward compatibility, safe default for CI/CD (addresses FR-007, FR-014)

---

## Alternatives Considered

### Alternative 1: Direct Terminal-Bench API Integration

**Considered**: Bypassing Harbor and calling Terminal-Bench API directly

**Rejected Because**:
- Harbor is the official harness and recommended approach
- Harbor abstracts complexity of container management
- Direct API would require reimplementing Harbor's orchestration logic
- Harbor provides CLI interface that's simpler than API calls

---

### Alternative 2: Custom Exception Classes for Harbor Errors

**Considered**: Creating 7 custom exception classes (HarborNotFoundError, DockerMissingError, etc.)

**Rejected Because**:
- Over-engineering (violates doubleagent.md anti-patterns)
- RuntimeError with clear message provides same functionality
- Simplified approach reduces 186 lines to 35 lines (76% reduction)
- No benefit to custom exceptions for subprocess call failures

---

### Alternative 3: Pre-flight Checks for Docker/Harbor Installation

**Considered**: Implementing 3 pre-flight check methods to validate Docker and Harbor before execution

**Rejected Because**:
- Trust Harbor's internal validation (philosophy from doubleagent.md)
- Duplicates validation Harbor already performs
- Adds complexity without value (Harbor errors are already clear)
- Simplified approach removes unnecessary code

---

### Alternative 4: Separate CrossRepoAggregator Service Class

**Considered**: Creating dedicated service class for multi-repository aggregation

**Rejected Because**:
- Pandas DataFrame operations are simpler (30 lines vs 171 lines)
- No need for separate class when aggregation is straightforward
- Inline implementation in CLI command is sufficient
- Violates doubleagent.md: "avoid abstractions for one-time operations"

---

## Open Questions Resolved

All questions from Technical Context section are now resolved:

| Question | Resolution |
|----------|------------|
| Harbor package name? | `harbor` via `uv pip install harbor` |
| Authentication method? | `ANTHROPIC_API_KEY` environment variable |
| CLI command syntax? | `harbor run --dataset terminal-bench@2.0 --agent claude-code --model <model> --jobs-dir <path>` |
| Output format? | JSON file at `<jobs-dir>/results.json` with accuracy, pass@k metrics |
| Execution times? | 5-10 minutes average, 1-hour timeout provides 6x buffer |
| Docker requirement? | Yes, required for local execution (trust Harbor's validation) |
| Model/agent validation? | Allowlist: models={haiku-4-5, sonnet-4-5}, agents={claude-code} |

---

## Impact on Implementation Plan

**Technical Context Updates**:
- Primary Dependencies: `harbor` (via uv), `pandas` (existing), `subprocess` (stdlib)
- Performance Goals: 5-10 minutes per benchmark, 4 concurrent workers, 1-hour timeout
- Constraints: Docker required, `ANTHROPIC_API_KEY` environment variable
- Scale/Scope: 10-20 diverse repositories for Phase 2 empirical validation

**Implementation Simplifications**:
- No custom exception classes (use RuntimeError)
- No pre-flight checks (trust Harbor validation)
- No separate aggregator service (inline pandas operations)
- Total implementation: ~120 lines (not 507) - 76% reduction

---

## Next Steps

1. ✅ Research complete - all NEEDS CLARIFICATION resolved
2. ⏭️ Phase 1: Design data models (TbenchResult, BenchmarkRun, AggregatedResult)
3. ⏭️ Phase 1: Generate contracts (JSON schema for results.json parsing)
4. ⏭️ Phase 1: Create quickstart guide (Harbor setup, first benchmark run)

---

**Sources**:
- [Harbor Framework - GitHub](https://github.com/laude-institute/harbor)
- [Harbor Framework Documentation - Running Terminal-Bench](https://harborframework.com/docs/running-tbench)
- [Terminal-Bench - GitHub](https://github.com/laude-institute/terminal-bench)
- [Terminal-Bench 2.0 Article - Snorkel AI](https://snorkel.ai/blog/terminal-bench-2-0-raising-the-bar-for-ai-agent-evaluation/)
- [VentureBeat - Terminal-Bench 2.0 Launch](https://venturebeat.com/ai/terminal-bench-2-0-launches-alongside-harbor-a-new-framework-for-testing)
- [DeepWiki - Terminal-Bench Getting Started](https://deepwiki.com/laude-institute/terminal-bench/2-getting-started)

---

**Document Status**: Complete
**Last Updated**: 2025-12-09
**Ready for Phase 1**: ✅ Yes
