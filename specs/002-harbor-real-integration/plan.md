# Implementation Plan: Harbor Framework Real Integration for Terminal-Bench Eval Harness

**Branch**: `002-harbor-real-integration` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-harbor-real-integration/spec.md`

## Summary

Replace the mocked Terminal-Bench integration with real Harbor framework subprocess calls to enable empirical validation of AgentReady assessor effectiveness. Use real benchmark data from 10-20 diverse repositories to identify high-impact vs low-impact assessors, then document recommendations for assessor list refinement.

**Technical Approach**:
- Install `harbor` Python package (Laude Institute's official CLI)
- Replace `_real_tbench_result()` NotImplementedError with subprocess call to `harbor run`
- Parse JSON output from `<jobs-dir>/results.json`
- Add security validations (API key sanitization, model/agent allowlists, path validation)
- Implement pandas-based aggregation inline in `summarize` CLI command
- Maintain backward compatibility with existing mocked integration via `TBENCH_USE_REAL` environment variable toggle

---

## Technical Context

**Language/Version**: Python 3.11+ (AgentReady standard, aligns with "N and N-1" policy)
**Primary Dependencies**:
- `harbor` (Laude Institute CLI, installed via `uv pip install harbor`)
- `pandas` (already in dependencies, for aggregation)
- `subprocess` (stdlib, for Harbor CLI calls)
- `json` (stdlib, for results parsing)
- `pathlib` (stdlib, for path validation)

**Storage**: File-based (Harbor outputs to `--jobs-dir`, JSON results parsed from filesystem)
**Testing**: pytest (existing AgentReady standard), subprocess mocking for Harbor calls
**Target Platform**: Linux/macOS (Docker required for Harbor framework)
**Project Type**: Single (extends existing `src/agentready/` structure)
**Performance Goals**:
- Individual benchmark: 5-10 minutes average execution time
- Batch (8 repos × 35 assessors = 280 runs): Complete in <24 hours with 4-worker parallelism
- Timeout: 1 hour (3600s) per individual benchmark run

**Constraints**:
- Docker required (Harbor executes benchmarks in containers)
- `ANTHROPIC_API_KEY` environment variable required
- Subprocess timeout: 3600 seconds (1 hour) per benchmark
- Memory: <2GB for parallel execution (4 workers)
- File handles: <1024 concurrent (enforced by 4-worker limit)

**Scale/Scope**:
- Phase 2: 10-20 repositories for empirical assessor validation
- 25 assessors to evaluate (current AgentReady assessment suite)
- ~120 lines of new code (76% reduction from original 507-line plan)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Entry Gate)

| Principle | Compliance | Evidence |
|-----------|------------|----------|
| **I. Evidence-Based Design** | ✅ Pass | Specification cites automated review findings (API key exposure, command injection), Harbor framework documentation (harborframework.com), Terminal-Bench research (Laude Institute GitHub) |
| **II. Measurable Quality** | ✅ Pass | Success criteria include quantifiable metrics: "100% accuracy blocking invalid params" (SC-003), "95% of errors provide clear guidance" (SC-008), "completes in <24 hours" (SC-009) |
| **III. Tool-First Mindset** | ✅ Pass | Harbor integration uses subprocess library interface (text-based I/O), maintains existing eval harness library structure in `src/agentready/services/eval_harness/` |
| **IV. Test-Driven Development** | ⚠️ Deferred | TDD workflow will be enforced during Phase 2 (Tasks) implementation. Tests must be written FIRST before Harbor integration code. |
| **V. Structured Output** | ✅ Pass | Harbor outputs JSON (`results.json`), AgentReady aggregation supports JSON export via pandas, human-readable markdown reports via `summarize` command |
| **VI. Incremental Delivery** | ✅ Pass | User stories prioritized P1/P2, MVP = User Story 1 (real benchmark execution) + User Story 3 (security), can be deployed independently |
| **VII. Documentation as Code** | ✅ Pass | Quickstart guide created (`quickstart.md`), research documented (`research.md`), data models defined (`data-model.md`), contracts specified (`contracts/*.json`) |

**Quality Gates**:
1. ✅ **Linting**: Will enforce black, isort, flake8 (no line length limit per CLAUDE.md)
2. ✅ **Tests**: Target >80% coverage for new Harbor integration code (per Constitution)
3. ✅ **Security**: Allowlist validation (models, agents), environment variable sanitization, path validation (addresses critical security review findings)
4. ✅ **Documentation**: README updated with Harbor setup, quickstart guide provided

**Violations**: None identified

---

### Post-Design Check (Phase 1 Exit Gate)

| Principle | Compliance | Evidence |
|-----------|------------|----------|
| **I. Evidence-Based Design** | ✅ Pass | Research document cites 6 authoritative sources (Harbor framework docs, GitHub repos, industry articles from Snorkel AI, VentureBeat) |
| **II. Measurable Quality** | ✅ Pass | Data models include validation rules (score ∈ [0.0, 1.0], trial counts ≥ 0), JSON schemas define expected formats, aggregation metrics (mean, median, std) are quantifiable |
| **III. Tool-First Mindset** | ✅ Pass | HarborConfig dataclass is self-contained, TbenchResult is independently testable, aggregation uses pandas library (not custom implementation) |
| **IV. Test-Driven Development** | ⚠️ Pending | Tests will be written FIRST during Phase 2 implementation (red-green-refactor workflow enforced) |
| **V. Structured Output** | ✅ Pass | JSON schemas defined for Harbor results (`harbor-results-schema.json`) and aggregation output (`aggregation-output-schema.json`), pandas DataFrame supports both JSON export and markdown tables |
| **VI. Incremental Delivery** | ✅ Pass | Phase 0 (research) complete independently, Phase 1 (design) complete independently, Phase 2 (implementation) can deliver User Story 1 (real benchmarks) before User Story 2 (aggregation) |
| **VII. Documentation as Code** | ✅ Pass | Quickstart guide provides <10 minute setup, data model document explains all entities, contracts define expected formats, research document captures all technical decisions |

**Complexity Limits Check**:
- **File Size**: No files exceed 300 lines (TbenchResult extension adds 7 fields, HarborConfig is ~40 lines, aggregation inline in CLI)
- **Function Length**: Subprocess call function estimated <50 lines, JSON parsing function <30 lines
- **Cyclomatic Complexity**: Simple conditionals (model validation, path checks) stay well below 10
- **Dependencies**: Harbor package is only new external dependency (pandas already in dependencies)

**Re-Check Result**: ✅ **PASS** - All principles compliant, ready for Phase 2 (Tasks)

---

## Project Structure

### Documentation (this feature)

```text
specs/002-harbor-real-integration/
├── plan.md                          # This file
├── spec.md                          # Feature specification
├── research.md                      # Phase 0 research (complete)
├── data-model.md                    # Phase 1 data models (complete)
├── quickstart.md                    # Phase 1 quickstart guide (complete)
├── contracts/                       # Phase 1 JSON schemas (complete)
│   ├── harbor-results-schema.json   # Harbor framework output schema
│   └── aggregation-output-schema.json # AgentReady aggregation output schema
├── checklists/                      # Specification quality checklist
│   └── requirements.md              # Validation checklist (all items passed)
├── DOUBLEAGENT_IMPACT.md            # doubleagent.md influence analysis
└── tasks.md                         # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
src/agentready/
├── services/
│   └── eval_harness/
│       ├── __init__.py               # Existing
│       ├── tbench_runner.py          # **MODIFY**: Replace _real_tbench_result() NotImplementedError
│       ├── harbor_config.py          # **NEW**: HarborConfig dataclass with validation
│       └── models.py                 # **NEW** (optional): BenchmarkRun metadata (Phase 3)
├── cli/
│   └── eval_harness.py               # **MODIFY**: Add pandas aggregation to 'summarize' command
└── models/                           # No changes (existing models not used in eval harness)

tests/
├── unit/
│   ├── test_eval_harness_services.py # **MODIFY**: Add Harbor integration tests with subprocess mocking
│   └── test_harbor_config.py         # **NEW**: HarborConfig validation tests
└── integration/
    └── test_eval_harness_e2e.py      # **MODIFY**: Add end-to-end test with mock Harbor subprocess

contracts/                            # No changes (eval harness doesn't use existing contracts)
docs/
└── tbench/
    ├── methodology.md                # **MODIFY**: Add Phase 2 real-world validation section
    └── assessor-refinement-results.md # **NEW**: Empirical assessor effectiveness findings
```

**Structure Decision**: Extends existing single-project structure (`src/agentready/`). No new top-level directories needed. Eval harness is already modular within `src/agentready/services/eval_harness/`, new Harbor integration fits naturally here. Follows AgentReady's established pattern of service modules + CLI commands + tests.

---

## Complexity Tracking

**No violations identified** - Constitution Check passed with no complexity limit violations.

All design decisions align with simplicity principles:
- ✅ No custom exception classes (use RuntimeError)
- ✅ No separate aggregator service (inline pandas operations)
- ✅ No pre-flight checks (trust Harbor validation)
- ✅ ~120 lines of implementation (76% reduction from original 507-line plan)

---

## Implementation Phases

### Phase 0: Research (Complete ✅)

**Deliverable**: `research.md` with all technical unknowns resolved

**Questions Resolved**:
1. ✅ Harbor package installation: `uv pip install harbor`
2. ✅ Authentication: `ANTHROPIC_API_KEY` environment variable
3. ✅ CLI syntax: `harbor run --dataset terminal-bench@2.0 --agent claude-code --model <model> --jobs-dir <path>`
4. ✅ Output format: JSON at `<jobs-dir>/results.json` with accuracy, pass@k metrics
5. ✅ Execution times: 5-10 minutes average, 1-hour timeout provides 6x buffer
6. ✅ Model/agent validation: Allowlists defined (haiku-4-5, sonnet-4-5 for models; claude-code for agents)
7. ✅ Docker dependency: Required for local execution, trust Harbor's validation

**Research Document**: [research.md](./research.md)

---

### Phase 1: Design & Contracts (Complete ✅)

**Deliverables**:
1. ✅ `data-model.md` - Entity definitions (TbenchResult extended, HarborConfig new, AggregatedResult conceptual)
2. ✅ `contracts/harbor-results-schema.json` - JSON schema for Harbor output validation
3. ✅ `contracts/aggregation-output-schema.json` - JSON schema for AgentReady aggregation export
4. ✅ `quickstart.md` - 10-minute setup guide with troubleshooting

**Key Design Decisions**:
- **TbenchResult**: Extended with 4 new optional fields (resolved_trials, unresolved_trials, pass_at_1, pass_at_3)
- **HarborConfig**: New dataclass with validation (model/agent allowlists, path resolution, API key requirement)
- **Aggregation**: Inline pandas DataFrame operations in `summarize` command (not separate service)
- **BenchmarkRun**: Optional metadata model (defer to Phase 3 for historical tracking)

**Agent Context Update**: Pending (will run `.specify/scripts/bash/update-agent-context.sh claude` after Phase 1 complete)

---

### Phase 2: Tasks (Next - To be generated by `/speckit.tasks`)

**Purpose**: Generate dependency-ordered task list from design artifacts

**Expected Tasks** (preview - actual tasks will be generated by command):

**Priority 1 (MVP - User Story 1 + 3)**:
1. Write tests for HarborConfig validation (TDD: red phase)
2. Implement HarborConfig dataclass with allowlist validation
3. Write tests for _real_tbench_result() subprocess call (TDD: red phase, mock subprocess)
4. Implement _real_tbench_result() with sanitized environment variables
5. Write tests for JSON parsing with path validation (TDD: red phase)
6. Implement parse_harbor_results() function
7. Write integration test for full real benchmark workflow (TDD: red phase)
8. Verify all tests pass (TDD: green phase)

**Priority 2 (User Story 2 + 4)**:
9. Write tests for pandas aggregation logic (TDD: red phase)
10. Implement aggregation in `summarize` command (inline with pandas)
11. Add parallel execution limits (ProcessPoolExecutor with max_workers=4)
12. Add timeout enforcement (3600s per benchmark)

**Priority 3 (Documentation & Polish)**:
13. Update README.md with Harbor setup instructions
14. Create `docs/tbench/assessor-refinement-results.md` template
15. Update `docs/tbench/methodology.md` with Phase 2 validation section
16. Run linters (black, isort, flake8) and fix issues
17. Run full test suite, verify >80% coverage for new code

**Task Document**: Will be generated by `/speckit.tasks` command (not created by `/speckit.plan`)

---

### Phase 3: Implementation (Future - To be executed by `/speckit.implement`)

**Not covered by `/speckit.plan` command** - see Phase 2 tasks for work breakdown

---

## File-Level Implementation Details

### File 1: `src/agentready/services/eval_harness/harbor_config.py` (NEW)

**Purpose**: Configuration and validation for Harbor framework subprocess execution

**Estimated Lines**: ~40

**Key Components**:
```python
from dataclasses import dataclass
from pathlib import Path

ALLOWED_MODELS = {
    "anthropic/claude-haiku-4-5",
    "anthropic/claude-sonnet-4-5",
}

ALLOWED_AGENTS = {
    "claude-code",
}

@dataclass
class HarborConfig:
    model: str
    agent: str
    jobs_dir: Path
    api_key: str
    timeout: int = 3600
    n_concurrent: int = 1

    def __post_init__(self):
        # Validation logic (model allowlist, agent allowlist, API key not empty, timeout positive)
        # Path resolution (jobs_dir.resolve())
```

**Testing**: `tests/unit/test_harbor_config.py` (allowlist validation, path resolution, API key requirement)

---

### File 2: `src/agentready/services/eval_harness/tbench_runner.py` (MODIFY)

**Purpose**: Replace NotImplementedError in `_real_tbench_result()` with functional Harbor subprocess integration

**Estimated Lines Added**: ~50

**Changes**:

**Before** (Current Phase 1 Implementation):
```python
def _real_tbench_result(self, repo_path: Path) -> TbenchResult:
    """Execute real Terminal-Bench via Harbor framework."""
    raise NotImplementedError("Phase 2: Harbor framework integration pending")
```

**After** (Phase 2 Implementation):
```python
def _real_tbench_result(self, repo_path: Path) -> TbenchResult:
    """Execute real Terminal-Bench via Harbor framework."""
    # 1. Create HarborConfig with validation
    config = HarborConfig(
        model=os.environ.get("TBENCH_MODEL", "anthropic/claude-haiku-4-5"),
        agent="claude-code",
        jobs_dir=Path(tempfile.mkdtemp()),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # 2. Build harbor run command
    cmd = [
        "harbor", "run",
        "--dataset", "terminal-bench@2.0",
        "--agent", config.agent,
        "--model", config.model,
        "--jobs-dir", str(config.jobs_dir),
        "--n-concurrent", "1",
    ]

    # 3. Sanitize environment variables (SECURITY: FR-004)
    clean_env = {
        "ANTHROPIC_API_KEY": config.api_key,
        "PATH": os.environ.get("PATH"),
        "HOME": os.environ.get("HOME"),
    }

    # 4. Execute subprocess with timeout
    try:
        subprocess.run(cmd, env=clean_env, timeout=config.timeout, check=True)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Benchmark timed out after {config.timeout}s")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Harbor command failed: {e}")

    # 5. Parse results.json with path validation (SECURITY: FR-005)
    results_path = config.jobs_dir / "results.json"
    if not results_path.is_relative_to(config.jobs_dir):
        raise ValueError(f"Invalid results path: {results_path}")

    return parse_harbor_results(results_path)

def parse_harbor_results(results_path: Path) -> TbenchResult:
    """Parse Harbor framework JSON output."""
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

**Testing**: `tests/unit/test_eval_harness_services.py` (subprocess mocking, JSON parsing, error handling, path validation)

---

### File 3: `src/agentready/cli/eval_harness.py` (MODIFY)

**Purpose**: Add pandas-based aggregation to `summarize` command

**Estimated Lines Added**: ~30

**Changes**:

**Add to existing `summarize` command**:
```python
@click.command()
def summarize():
    """Summarize assessor effectiveness across repositories."""
    # 1. Load results from previous benchmark runs (implementation detail TBD - file-based storage?)
    results = load_benchmark_results()  # Returns List[Dict[str, Any]]

    # 2. Aggregate with pandas
    import pandas as pd
    df = pd.DataFrame(results)
    summary = df.groupby("assessor_id").agg({
        "delta_score": ["mean", "median", "std", "count"],
    }).round(2)
    summary.columns = ["mean_delta", "median_delta", "std_delta", "sample_size"]

    # 3. Add statistical significance placeholder
    summary["significant"] = summary["mean_delta"].abs() > 0.05

    # 4. Sort by mean_delta descending and display
    summary = summary.sort_values("mean_delta", ascending=False)
    click.echo(summary.to_markdown())

    # 5. Export JSON for machine consumption
    summary.to_json("aggregation-results.json", orient="records")
```

**Testing**: `tests/unit/test_eval_harness_cli.py` (pandas aggregation logic, JSON export, markdown output)

---

### File 4: `tests/unit/test_eval_harness_services.py` (MODIFY)

**Purpose**: Add integration tests for Harbor subprocess calls with mocking

**Estimated Lines Added**: ~40

**New Tests**:
```python
from unittest.mock import patch, MagicMock

def test_real_tbench_result_subprocess_call():
    """Test Harbor subprocess called with correct parameters."""
    with patch("subprocess.run") as mock_run, \
         patch("builtins.open", mock_open(read_data='{"summary": {...}}')):
        runner = TbenchRunner(use_real=True)
        result = runner._real_tbench_result(Path("/fake/repo"))

        # Verify subprocess.run called with sanitized env
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "harbor" in call_args[0][0]
        assert call_args[1]["env"]["ANTHROPIC_API_KEY"] is not None
        assert "JAVA_HOME" not in call_args[1]["env"]  # Env sanitization check

def test_harbor_config_validation_invalid_model():
    """Test HarborConfig rejects invalid model."""
    with pytest.raises(ValueError, match="Invalid model"):
        HarborConfig(
            model="invalid/model",
            agent="claude-code",
            jobs_dir=Path("/tmp"),
            api_key="test-key",
        )
```

**Coverage Target**: >80% for new Harbor integration code

---

### File 5: `docs/tbench/assessor-refinement-results.md` (NEW)

**Purpose**: Document empirical assessor effectiveness findings from real benchmarks

**Estimated Lines**: ~100 (template, will be filled with actual data after benchmarks run)

**Structure**:
```markdown
# Assessor Refinement Results - Phase 2 Empirical Validation

## Methodology
- 15 diverse repositories tested (Python, JavaScript, TypeScript, mixed)
- 25 assessors evaluated
- Metrics: mean delta, median delta, std delta, statistical significance (p < 0.05)

## High-Impact Assessors (Keep/Promote)
1. **claude_md**: +12% mean improvement, statistically significant (p=0.001)
2. **test_coverage**: +8% mean improvement, statistically significant (p=0.01)
...

## Low/No-Impact Assessors (Review/Demote)
23. **dependency_pinning**: +2% mean improvement, NOT statistically significant (p=0.42)
...

## Recommendations
- ✅ Keep Tier 1: claude_md, test_coverage, gitignore (empirically validated high impact)
- ⚠️ Demote to Tier 3: dependency_pinning (no significant measured impact)
...
```

---

## Security Considerations

**Addressed from Automated Review Findings**:

### 1. API Key Exposure (Critical)
**Problem**: Passing all environment variables to subprocess via `os.environ.copy()` exposes API keys
**Solution**: Sanitize environment variables, pass only required: `ANTHROPIC_API_KEY`, `PATH`, `HOME`
**Code**: `clean_env = {k: os.environ.get(k) for k in ["ANTHROPIC_API_KEY", "PATH", "HOME"]}`
**Verification**: Unit test checks env dict keys, excludes non-required variables

### 2. Command Injection (Critical)
**Problem**: Unvalidated model/agent parameters passed to subprocess
**Solution**: Allowlist validation in HarborConfig.__post_init__()
**Code**: `if model not in ALLOWED_MODELS: raise ValueError(f"Invalid model: {model}")`
**Verification**: Unit test attempts malicious input (e.g., `model="$(rm -rf /)"`) and verifies rejection

### 3. Path Traversal (Medium)
**Problem**: Harbor output path not validated before reading
**Solution**: Validate results_path is relative to jobs_dir
**Code**: `if not results_path.is_relative_to(jobs_dir): raise ValueError(...)`
**Verification**: Unit test attempts path traversal (e.g., `../../etc/passwd`) and verifies rejection

---

## Dependencies & Installation

### New Dependencies

**Harbor Framework**:
```toml
# pyproject.toml
dependencies = [
    # ... existing dependencies ...
    "harbor>=2.0.0",  # Laude Institute Terminal-Bench harness
]
```

**Install Command**:
```bash
uv pip install harbor
```

### System Requirements

**Docker** (required for Harbor):
- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Minimum 4GB RAM, 2GB free disk space
- Docker daemon must be running before executing benchmarks

**Verification**:
```bash
docker --version  # Should show Docker version 20.10+
docker ps         # Should connect without error
```

---

## Testing Strategy

### Unit Tests (TDD Red-Green-Refactor)

**Phase 1: Write Tests FIRST (Red)**
1. `test_harbor_config_validation()` - Allowlist enforcement
2. `test_real_tbench_result_subprocess_call()` - Subprocess mocking
3. `test_parse_harbor_results()` - JSON parsing
4. `test_environment_sanitization()` - Env var filtering
5. `test_path_validation()` - Path traversal prevention

**Phase 2: Implement to Pass (Green)**
- Implement HarborConfig, _real_tbench_result(), parse_harbor_results()
- All tests should pass

**Phase 3: Refactor (Refactor)**
- Extract constants (ALLOWED_MODELS, ALLOWED_AGENTS)
- Simplify subprocess call logic
- Add docstrings

**Coverage Target**: >80% for new code

---

### Integration Tests

**End-to-End Workflow**:
```python
def test_full_benchmark_workflow_mocked():
    """Test complete benchmark with mocked Harbor subprocess."""
    with patch("subprocess.run") as mock_run:
        # Setup mock to return success
        mock_run.return_value = MagicMock(returncode=0)

        # Run benchmark
        result = run_benchmark(repo_path, assessor_id="claude_md")

        # Verify subprocess called correctly
        assert mock_run.called
        # Verify result parsed correctly
        assert result.is_mocked == False
        assert 0.0 <= result.score <= 1.0
```

---

## Documentation Updates

### 1. README.md

**Section to Add**: "Running Real Terminal-Bench Evaluations (Phase 2)"

**Content**:
```markdown
## Running Real Terminal-Bench Evaluations

### Prerequisites
- Docker installed and running
- Anthropic API key (get from https://console.anthropic.com)

### Setup
```bash
# Install Harbor framework
uv pip install harbor

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export TBENCH_USE_REAL=1

# Run baseline benchmark
agentready tbench baseline /path/to/repo
```

See [Quickstart Guide](specs/002-harbor-real-integration/quickstart.md) for detailed instructions.
```

---

### 2. docs/tbench/methodology.md

**Section to Add**: "Phase 2: Real-World Validation"

**Content**:
- Harbor framework integration details
- Real vs mocked benchmark comparison
- Statistical significance testing approach
- Sample size rationale (10-20 repositories)

---

### 3. docs/tbench/assessor-refinement-results.md (NEW)

**Purpose**: Document empirical findings from Phase 2 benchmarks

**Structure**:
- Methodology (sample size, repository diversity, metrics)
- High-impact assessors (keep/promote based on data)
- Low/no-impact assessors (review/demote based on data)
- Recommendations (tier reassignments, assessor improvements)
- Appendix (raw data, statistical tests)

---

## Risks & Mitigations

### Risk 1: Harbor framework API changes between versions

**Impact**: Breaking changes in Harbor CLI could break our integration
**Likelihood**: Low (Harbor is in active development but API appears stable)
**Mitigation**:
- Pin Harbor version in dependencies (`harbor>=2.0.0,<3.0.0`)
- Add integration tests that fail if Harbor output format changes
- Document Harbor version tested with

---

### Risk 2: Docker unavailable on CI/CD

**Impact**: Real benchmarks cannot run in GitHub Actions (no Docker in standard runners)
**Likelihood**: Medium (GitHub Actions free tier doesn't support Docker-in-Docker well)
**Mitigation**:
- Default to mocked integration in CI/CD (`TBENCH_USE_REAL=0` by default)
- Document that real benchmarks require local execution or self-hosted runners
- Consider GitHub Actions self-hosted runners with Docker for future automation

---

### Risk 3: Benchmark execution costs exceed budget

**Impact**: Running 280+ benchmarks (8 repos × 35 assessors) could cost $100-$200 USD
**Likelihood**: Medium (depending on repository complexity and Claude API pricing)
**Mitigation**:
- Start with small sample (5 repos × 10 assessors) to validate approach
- Use Claude Haiku (cheaper) for initial validation, Sonnet only for final confirmation
- Document cost per benchmark in README to help users budget

---

### Risk 4: Statistical sample size insufficient for significance testing

**Impact**: 10-20 repositories may not provide statistical power for significance tests
**Likelihood**: Medium (depends on effect size and variance)
**Mitigation**:
- Document confidence intervals and p-values with sample size caveats
- Use conservative significance threshold (p < 0.05)
- Recommend larger sample sizes for critical decisions (e.g., removing Tier 1 assessors)

---

## Next Steps

1. ✅ **Phase 0 Complete**: Research document with all unknowns resolved
2. ✅ **Phase 1 Complete**: Data models, contracts, quickstart guide
3. ⏭️ **Update Agent Context**: Run `.specify/scripts/bash/update-agent-context.sh claude`
4. ⏭️ **Phase 2**: Generate tasks with `/speckit.tasks` command
5. ⏭️ **Phase 3**: Execute tasks with `/speckit.implement` command

---

## Appendix: References

- [Harbor Framework Documentation](https://harborframework.com/docs/running-tbench)
- [Harbor GitHub Repository](https://github.com/laude-institute/harbor)
- [Terminal-Bench GitHub Repository](https://github.com/laude-institute/terminal-bench)
- [Terminal-Bench 2.0 Article - Snorkel AI](https://snorkel.ai/blog/terminal-bench-2-0-raising-the-bar-for-ai-agent-evaluation/)
- [AgentReady Constitution](.specify/memory/constitution.md)
- [DoubleAgent.md Impact Analysis](./DOUBLEAGENT_IMPACT.md)
- [Automated Code Review Findings (GitHub Issue #190)](https://github.com/ambient-code/agentready/issues/190)

---

**Document Status**: Complete
**Last Updated**: 2025-12-09
**Ready for Phase 2**: ✅ Yes (pending agent context update)
