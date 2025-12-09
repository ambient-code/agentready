# Terminal-Bench Eval Harness - Formal Plan Document

**Feature**: Terminal-Bench Evaluation Harness for Systematic A/B Testing
**Status**: Phase 1 Complete (MVP) ✅ | Phase 2 Planned (Real Integration) 🔜
**Branch**: feature/eval-harness-mvp
**Version**: 2.14.1
**Last Updated**: 2025-12-08
**Test Coverage**: 56/56 passing (100%)

**Purpose**: Empirically measure the impact of each AgentReady assessor on Terminal-Bench performance through systematic A/B testing with statistical rigor.

---

## Executive Summary

The Terminal-Bench Eval Harness provides systematic A/B testing to measure whether AgentReady's best practices actually improve agentic development performance. **Phase 1 (complete)** delivers a fully functional MVP with mocked Terminal-Bench integration, 4 CLI commands, interactive GitHub Pages dashboard, and comprehensive test coverage (56 tests). **Phase 2** will integrate with real Terminal-Bench via the Harbor framework for actual benchmark submissions.

**Research Question**: Do AgentReady's best practices improve Terminal-Bench scores? Which attributes matter most?

---

## Current Implementation Status (Phase 1)

### ✅ What's Complete

**Components**:
1. **CLI Commands** (`src/agentready/cli/eval_harness.py` - 787 LOC):
   - `baseline` - Establish baseline performance (N iterations)
   - `test-assessor` - Test individual assessor impact (A/B test)
   - `summarize` - Aggregate and rank results
   - `dashboard` - Generate interactive GitHub Pages visualization

2. **Data Models** (`src/agentready/models/eval_harness.py`):
   - `TbenchResult` - Single benchmark run (score, completion rate, pytest pass rate)
   - `BaselineMetrics` - Statistical baseline (mean, std dev, median)
   - `AssessorImpact` - A/B test result (delta, p-value, effect size, significance)
   - `EvalSummary` - Aggregated results (ranked impacts, tier statistics)

3. **Services** (`src/agentready/services/eval_harness/`):
   - `TbenchRunner` - Mocked Terminal-Bench integration (deterministic, seeded)
   - `BaselineEstablisher` - Baseline performance measurement
   - `AssessorTester` - Core A/B testing logic (clone → fix → measure)
   - `ResultsAggregator` - Statistical aggregation and ranking
   - `DashboardGenerator` - JSON export for GitHub Pages

4. **Dashboard** (`docs/tbench.md`, `docs/_data/tbench/*.json`):
   - Interactive Chart.js visualizations
   - Sortable ranked assessor table
   - Tier impact bar chart
   - Methodology documentation

5. **Test Suite** (56 tests):
   - 6 CLI tests (all commands + help)
   - 13 model tests (serialization, statistics)
   - 32 service tests (determinism, A/B logic, aggregation)
   - 5 E2E integration tests (full workflow)

### ⚠️ Current Limitations

1. **Mocked Terminal-Bench**: Uses deterministic scores, not real tbench.ai runs
2. **Limited Test Set**: Only 5 assessors tested on AgentReady repository
3. **Zero Deltas**: AgentReady already passes all assessments (+0.00 everywhere)
4. **No Real Integration**: Harbor framework integration pending

---

## Architecture Overview

### Workflow

```
1. Baseline → Run Terminal-Bench N times on unmodified repo
2. A/B Testing → For each assessor:
   - Clone repo to temp directory
   - Run Scanner with ONLY this assessor
   - Apply remediation via FixerService (align command)
   - Run Terminal-Bench N times post-remediation
   - Calculate delta, p-value, Cohen's d
3. Aggregation → Rank assessors by impact, calculate tier statistics
4. Dashboard → Generate interactive visualization for GitHub Pages
```

### Statistical Rigor

- **Significance Criteria**: P-value < 0.05 AND |Cohen's d| > 0.2
- **T-test**: Two-sample comparison (baseline vs post-remediation)
- **Effect Size**: Cohen's d interpretation (small: 0.2-0.5, medium: 0.5-0.8, large: >0.8)

### Component Architecture

```
┌─────────────────┐
│   CLI Layer     │  eval_harness.py (4 commands)
└────────┬────────┘
         │
┌────────▼────────┐
│  Service Layer  │  BaselineEstablisher, AssessorTester,
└────────┬────────┘  ResultsAggregator, DashboardGenerator
         │
┌────────▼────────┐
│  Integration    │  TbenchRunner (mock=True/False)
└────────┬────────┘
         │
┌────────▼────────┐
│  External API   │  Harbor Framework (Phase 2)
└─────────────────┘
```

---

## File Structure

### Source Code

```
src/agentready/
├── cli/eval_harness.py              # 4 CLI commands (787 LOC)
├── models/eval_harness.py           # Data models with serialization
└── services/eval_harness/
    ├── __init__.py                  # Public API exports
    ├── tbench_runner.py             # Mocked + real integration
    ├── baseline.py                  # BaselineEstablisher
    ├── assessor_tester.py           # AssessorTester (core A/B logic)
    ├── aggregator.py                # ResultsAggregator
    └── dashboard_generator.py       # Dashboard data generation
```

### Tests

```
tests/
├── unit/
│   ├── test_eval_harness_cli.py     # 6 CLI tests
│   ├── test_eval_harness_models.py  # 13 model tests
│   └── test_eval_harness_services.py # 32 service tests
└── integration/
    └── test_eval_harness_e2e.py     # 5 E2E workflow tests
```

### Dashboard & Documentation

```
docs/
├── tbench.md                        # Interactive dashboard (Chart.js)
├── tbench/methodology.md            # Statistical methodology
└── _data/tbench/                    # Dashboard JSON data (generated)
    ├── summary.json                 # Complete summary
    ├── ranked_assessors.json        # Pre-sorted list
    ├── tier_impacts.json            # For bar chart
    ├── baseline.json                # Baseline metrics
    └── stats.json                   # Overview stats
```

### Results Storage (gitignored)

```
.agentready/eval_harness/
├── baseline/
│   ├── run_001.json → run_00N.json
│   └── summary.json
├── assessors/{assessor_id}/
│   ├── run_001.json → run_00N.json
│   └── impact.json
└── summary.json
```

---

## Key Design Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Test assessors individually** | Isolates specific impact, enables ranking | Doesn't capture synergies between assessors |
| **Mocked Phase 1** | Validates workflow without external dependencies | Must re-test with real Harbor integration |
| **Deterministic mocking** | Reproducible results (seeded from commit hash) | Not representative of real variance |
| **Statistical significance** | P-value + Cohen's d prevents false positives | More conservative (fewer "significant" results) |
| **GitHub Pages dashboard** | Leverages existing Jekyll infrastructure | Limited to static JSON data (no backend) |

---

## Usage Examples

### Basic Workflow

```bash
# 1. Establish baseline on your repository
cd /path/to/your/repo
agentready eval-harness baseline . --iterations 5 --verbose

# 2. Test high-priority assessors
agentready eval-harness test-assessor --assessor-id claude_md_file --iterations 5
agentready eval-harness test-assessor --assessor-id type_annotations --iterations 5

# 3. Or test entire tier
agentready eval-harness run-tier --tier 1 --iterations 5

# 4. View ranked results
agentready eval-harness summarize --verbose

# 5. Generate dashboard
agentready eval-harness dashboard --verbose

# 6. View in browser
open docs/tbench.md  # (after Jekyll build)
```

### Expected Output (with actual impact)

**Baseline**:
```
📊 Baseline Performance:
  Mean Score: 73.4
  Std Dev: 2.5
  Iterations: 5
```

**Assessor Test**:
```
📊 Results:
  Assessor:          CLAUDE.md Configuration Files (Tier 1)
  Baseline Score:    73.4
  Post-Fix Score:    81.2
  Delta:             +7.8 points
  P-value:           0.003
  Effect Size (d):   1.23
  Significant:       ✅ YES
  Effect Magnitude:  large
```

**Summary**:
```
🏆 Assessors Ranked by Impact:
   1. CLAUDE.md Configuration Files      +7.8 | ✅ Significant
   2. Type Annotations                   +5.2 | ✅ Significant
   3. Standard Project Layouts           +3.1 | ❌ Not significant
   ...
```

---

## Phase 2 Roadmap: Assessor Refinement via Terminal-Bench Feedback

### Objectives

1. **Replace Mocked TbenchRunner** with real Harbor framework API calls
2. **Run Real Benchmarks** on diverse repositories to get empirical feedback
3. **Refine Assessor List** based on Terminal-Bench impact measurements
4. **Optimize Assessor Configurations** using real-world performance data

**Note**: Submission features (leaderboard integration, public submissions) moved to Phase 3

### Implementation Tasks

#### 1. Research Harbor Framework

**File**: Research notes in `plans/eval-harness-harbor-research.md`

**Questions to Answer**:
- What is the Harbor framework API structure?
- How does authentication work (API keys, OAuth)?
- What's the repository submission format?
- How do we poll for completion?
- What are rate limits and quotas?

**Resources**:
- **Harbor Framework Documentation**: https://harborframework.com/docs (PRIMARY)
- tbench.ai documentation
- Harbor framework GitHub repository
- Terminal-Bench API documentation

#### 2. Implement Real TbenchRunner

**Primary File**: `src/agentready/services/eval_harness/tbench_runner.py`

**Current State**:
```python
def _real_tbench_result(self, repo_path: Path) -> TbenchResult:
    """Execute real Terminal-Bench via Harbor framework."""
    raise NotImplementedError("Phase 2: Harbor framework integration pending")
```

**Implementation Steps**:
1. Add Harbor framework client initialization
2. Implement authentication (API key from environment)
3. Submit repository to Terminal-Bench
4. Poll for completion (async/retry logic)
5. Parse result and return `TbenchResult` with `is_mocked=False`
6. Add error handling (rate limits, timeouts, failures)

**Reference**: See `_mock_tbench_result()` method for expected return type

#### 3. Update CLI with --mock Flag

**File**: `src/agentready/cli/eval_harness.py`

**Changes**:
```python
@click.option("--mock/--no-mock", default=False, help="Use mocked Terminal-Bench (default: real)")
def baseline(repo_path, iterations, mock, verbose):
    runner = TbenchRunner(mock=mock)
    # ...
```

**Rationale**: Allow users to toggle between real and mocked benchmarks (dev vs prod)

#### 4. Update Tests

**File**: `tests/unit/test_eval_harness_services.py`

**New Tests**:
- Test Harbor API integration with mocked responses (VCR cassettes)
- Test both `mock=True` and `mock=False` paths
- Test authentication failure handling
- Test rate limit handling
- Test timeout/retry logic

**Tools**: Consider using `vcrpy` for recording/replaying Harbor API responses

#### 5. Assessor Refinement via Real Benchmarks

**Tasks**:
1. Run eval harness on 10-20 diverse repositories (different languages, sizes, domains)
2. Measure actual delta impact for all 25 assessors using real Terminal-Bench results
3. Identify high-impact assessors (statistically significant deltas observed)
4. Identify low/no-impact assessors (consider removing or demoting tier)
5. Tune assessor configurations based on real-world feedback
6. Document actual delta ranges, effectiveness patterns, and recommendations

**Success Criteria**:
- At least 10 successful benchmark runs on diverse repositories
- Reproducible results (re-run same repo → similar scores ±5%)
- Clear empirical ranking of assessors by measured impact
- Actionable recommendations for assessor list refinement (which to keep/remove/retune)
- Evidence-based tier assignments validated by real data

**Deliverable**: `docs/tbench/assessor-refinement-results.md` documenting:
- Which assessors showed significant impact (keep/promote)
- Which assessors showed no impact (consider removing)
- Recommended configuration changes
- Suggested tier reassignments based on empirical data

#### 6. Documentation Updates

**Files**:
- `README.md` - Add Harbor setup guide (API key configuration)
- `CLAUDE.md` - Update eval harness section with Phase 2 status
- `docs/tbench/methodology.md` - Add real-world validation section with refinement criteria
- `DEMO_EVAL_HARNESS.md` - Update with Phase 2 results
- **NEW**: `docs/tbench/assessor-refinement-results.md` - Document empirical assessor effectiveness

---

## Phase 2 Critical Files

**Primary Implementation Target**:
1. **`src/agentready/services/eval_harness/tbench_runner.py`** - Implement `_real_tbench_result()`

**Supporting Files**:
2. `src/agentready/cli/eval_harness.py` - Add `--mock` flag
3. `tests/unit/test_eval_harness_services.py` - Add Harbor API tests
4. `CLAUDE.md` - Update eval harness section with Phase 2 status
5. `docs/tbench/methodology.md` - Document real-world validation

---

## Phase 2 Dependencies

**Required**:
- **Harbor framework** (Python package or API client)
- **tbench.ai API key** (authentication)
- **Network access** to tbench.ai submission endpoints
- **Increased timeouts** (real benchmarks take minutes, not seconds)

**Installation** (Phase 2):
```bash
# Add to pyproject.toml
dependencies = [
    # existing...
    "harbor-framework>=1.0.0",  # TBD: actual package name
]

# Environment configuration
export TBENCH_API_KEY="your_api_key"
agentready eval-harness baseline . --mock=false  # Use real benchmarks
```

---

## Known Issues & Future Enhancements

### Phase 1 Limitations

1. **Mocked Results**: Not representative of real Terminal-Bench variance
2. **Deterministic Scores**: Same repo always produces same score
3. **Limited Testing**: Only 5 assessors tested on AgentReady itself
4. **Zero Deltas**: AgentReady already passes all assessments

### Design Limitations

1. **No Synergy Detection**: Tests assessors individually (doesn't capture combinations)
2. **No Historical Trends**: Single-point measurement (no time series)
3. **No Multi-Repo Analysis**: Dashboard shows one repo at a time
4. **Static Dashboard**: No backend, can't query/filter dynamically

### Phase 3: Submission & Leaderboard Integration (Future)

**Note**: This phase begins after Phase 2 assessor refinement is complete.

**Objectives**:
- **Leaderboard Integration**: Connect eval harness results to AgentReady leaderboard
- **Public Submissions**: Allow users to submit their results publicly
- **GitHub App Integration**: Badges, PR status checks, automated comments

**Tasks** (Future):
- Add `agentready eval-harness submit` command
- Generate leaderboard-compatible JSON
- Create PR submission workflow to public leaderboard repo
- Dashboard includes "Submit to Leaderboard" link
- Badge generation for repositories

### Future Enhancements (Phase 4-5)

- **GitHub Actions Automation**: Auto-run eval harness on PRs
- **Synergy Detection**: Test assessor pairs/triplets for combined impact
- **Trend Analysis**: Track impact over time as repo evolves
- **Predictive Modeling**: ML models to predict assessor impact
- **Multi-Repo Dashboard**: Compare impact across repository types

---

## Integration Points

### Existing AgentReady Features

| Feature | Integration | Status |
|---------|-------------|--------|
| **FixerService** | Uses `align` command for remediation | ✅ Complete |
| **Scanner** | Runs single-assessor assessments | ✅ Complete |
| **GitHub Pages** | Dashboard hosted at `/agentready/tbench` | ✅ Complete |
| **Assessors** | All 25 assessors testable | ⚠️ Only 5 tested in demo |

### External Dependencies

| Dependency | Purpose | Phase |
|------------|---------|-------|
| **git** | Repository cloning | Phase 1 ✅ |
| **scipy** | T-test, statistics | Phase 1 ✅ |
| **Chart.js** | Interactive charts | Phase 1 ✅ |
| **Harbor framework** | Real Terminal-Bench API | Phase 2 🔜 |
| **tbench.ai** | Benchmark execution | Phase 2 🔜 |

---

## References

**Internal Documentation**:
- `DEMO_EVAL_HARNESS.md` - Working demonstration (Phase 1)
- `docs/tbench/methodology.md` - Statistical methodology
- `CLAUDE.md` - Developer guide (eval harness section)
- `specs/leaderboard-feature-spec.md` - Related leaderboard feature

**External Resources**:
- **Harbor Framework Documentation**: https://harborframework.com/docs
- Terminal-Bench: https://tbench.ai
- Cohen's d Calculator: https://www.statisticshowto.com/cohens-d/
- Chart.js Documentation: https://www.chartjs.org/docs/latest/

---

## Cold-Start Prompt for Phase 2 (Future Agent)

**Task**: Implement Phase 2 of the Terminal-Bench eval harness - use real Harbor framework to refine assessor list.

**Context**: Phase 1 (complete) uses mocked Terminal-Bench results. Phase 2 replaces the mock with real API calls to tbench.ai via Harbor framework, then uses empirical data to refine which assessors are most effective.

**Primary Goal**: Use Terminal-Bench feedback to identify which assessors actually improve performance and should be kept/promoted vs which have no impact and should be removed/demoted.

**Primary File**: `/Users/jeder/repos/agentready/src/agentready/services/eval_harness/tbench_runner.py`

**Implementation Steps**:
1. Research Harbor framework API at https://harborframework.com/docs (authentication, submission, polling)
2. Implement `_real_tbench_result(repo_path)` method (currently raises NotImplementedError)
3. Add authentication configuration (API keys, environment variables)
4. Add retry logic and error handling
5. Update tests with VCR cassettes or Harbor mocks
6. Add `--mock` CLI flag for backward compatibility
7. Run eval harness on 10-20 diverse repositories (different languages, sizes, domains)
8. Measure actual delta impact for all 25 assessors
9. Create `docs/tbench/assessor-refinement-results.md` documenting which assessors work

**Reference Implementation**: See `_mock_tbench_result()` method in same file for expected return type (`TbenchResult`).

**Success Criteria**:
- Real benchmark runs work end-to-end
- Tests pass with both mock=True and mock=False
- At least 10-20 successful benchmark runs on diverse repositories
- Clear empirical ranking of assessors by measured impact
- Actionable recommendations documented for assessor list refinement
- Evidence-based tier assignments validated by real data

**Deliverable**: Document in `docs/tbench/assessor-refinement-results.md` showing:
- Which assessors showed significant impact (keep/promote)
- Which assessors showed no impact (consider removing)
- Recommended configuration changes
- Suggested tier reassignments

**Note**: Submission features (leaderboard integration) are Phase 3, not Phase 2. Focus on using Terminal-Bench for internal refinement feedback, not public submissions.

**Related Files**: See "Phase 2 Critical Files" section above

---

## Next Steps

### Immediate Actions (Current Session)

1. **Create this plan document** ✅
2. **Switch to feature/eval-harness-mvp branch**
3. **Review existing implementation** (read critical files)
4. **Begin Harbor framework research** (API documentation)

### Phase 2 Milestones

- **M1**: Harbor API integration complete (real benchmarks work)
- **M2**: Assessor refinement complete (10-20 successful benchmark runs on diverse repos)
- **M3**: Refinement results documented (assessor-refinement-results.md published)
- **M4**: Merge to main and update assessor list based on empirical data

---

**Plan Created**: 2025-12-08
**Plan Author**: Claude Code (Sonnet 4.5)
**Branch**: feature/eval-harness-mvp
**Status**: Ready for Phase 2 implementation

---

# COLD-START PROMPT (EXTRACT)

**Use this section to hand off to a fresh agent without conversation history**

---

## Task: Complete Terminal-Bench Eval Harness Phase 2

Implement real Harbor framework integration and use Terminal-Bench feedback to refine the assessor list.

### Context

**Feature**: Eval harness systematically measures the impact of each AgentReady assessor on Terminal-Bench (tbench.ai) performance through A/B testing.

**Phase 1 Status (Complete)** ✅:
- 4 CLI commands implemented: `baseline`, `test-assessor`, `summarize`, `dashboard`
- 56 tests passing (100% coverage)
- Mocked Terminal-Bench integration (deterministic, seeded from commit hash)
- Interactive GitHub Pages dashboard with Chart.js
- Statistical rigor: P-value < 0.05 AND |Cohen's d| > 0.2

**Phase 2 Goal**: Replace mocked TbenchRunner with real Harbor framework API, then use empirical Terminal-Bench data to refine which assessors are most effective and should be kept vs removed/demoted.

### Primary Implementation Target

**File**: `/Users/jeder/repos/agentready/src/agentready/services/eval_harness/tbench_runner.py`

**Current State**:
```python
def _real_tbench_result(self, repo_path: Path) -> TbenchResult:
    """Execute real Terminal-Bench via Harbor framework."""
    raise NotImplementedError("Phase 2: Harbor framework integration pending")
```

**Task**: Implement this method to submit real benchmarks to tbench.ai via Harbor framework.

### Implementation Steps

1. **Research Harbor Framework API**: https://harborframework.com/docs
   - Authentication (API keys, OAuth)
   - Repository submission format
   - Polling for completion
   - Rate limits and quotas

2. **Implement `_real_tbench_result()` method**:
   - Initialize Harbor framework client
   - Add authentication (API key from environment variable)
   - Submit repository to Terminal-Bench
   - Poll for completion (async/retry logic)
   - Parse result and return `TbenchResult` with `is_mocked=False`
   - Add error handling (rate limits, timeouts, failures)

3. **Update CLI with `--mock` flag**:
   - File: `/Users/jeder/repos/agentready/src/agentready/cli/eval_harness.py`
   - Add `--mock/--no-mock` option (default: False for real benchmarks)
   - Allow users to toggle between real and mocked for dev/prod

4. **Update Tests**:
   - File: `/Users/jeder/repos/agentready/tests/unit/test_eval_harness_services.py`
   - Add Harbor API integration tests with mocked responses (consider VCR cassettes)
   - Test both `mock=True` and `mock=False` paths
   - Test authentication failure, rate limits, timeouts

5. **Assessor Refinement via Real Benchmarks**:
   - Run eval harness on 10-20 diverse repositories (different languages, sizes, domains)
   - Measure actual delta impact for all 25 assessors using real Terminal-Bench results
   - Identify high-impact assessors (statistically significant deltas observed)
   - Identify low/no-impact assessors (consider removing or demoting tier)
   - Tune assessor configurations based on real-world feedback
   - Document actual delta ranges, effectiveness patterns, and recommendations

6. **Update Documentation**:
   - `README.md` - Add Harbor setup guide (API key configuration)
   - `CLAUDE.md` - Update eval harness section with Phase 2 status
   - `docs/tbench/methodology.md` - Add real-world validation section with refinement criteria
   - `DEMO_EVAL_HARNESS.md` - Update with Phase 2 results
   - **NEW**: `docs/tbench/assessor-refinement-results.md` - Document empirical assessor effectiveness

### Critical Files

**Implementation**:
1. `/Users/jeder/repos/agentready/src/agentready/services/eval_harness/tbench_runner.py` - PRIMARY
2. `/Users/jeder/repos/agentready/src/agentready/cli/eval_harness.py` - Add `--mock` flag

**Tests**:
3. `/Users/jeder/repos/agentready/tests/unit/test_eval_harness_services.py` - Add Harbor tests

**Documentation**:
4. `/Users/jeder/repos/agentready/CLAUDE.md` - Update status
5. `/Users/jeder/repos/agentready/docs/tbench/methodology.md` - Real-world validation

### Expected Data Model

**Reference**: See `_mock_tbench_result()` method for expected return type.

```python
TbenchResult(
    score: float,              # Overall completion rate (0-100)
    completion_rate: float,    # Task completion percentage
    pytest_pass_rate: float,   # Pytest pass percentage
    latency_ms: float,         # Average latency in milliseconds
    timestamp: datetime,       # When this run was executed
    is_mocked: bool           # Set to False for real Harbor results
)
```

### Dependencies

**Required**:
- Harbor framework Python package (research actual package name)
- tbench.ai API key (environment variable: `TBENCH_API_KEY`)
- Network access to tbench.ai submission endpoints
- Increased timeouts (real benchmarks take minutes, not seconds)

**Installation** (update `pyproject.toml`):
```toml
dependencies = [
    # existing...
    "harbor-framework>=1.0.0",  # TBD: confirm actual package name
]
```

### Success Criteria

✅ Real benchmark runs work end-to-end
✅ Tests pass with both `mock=True` and `mock=False`
✅ At least 10-20 successful benchmark runs on diverse repositories
✅ Clear empirical ranking of assessors by measured impact
✅ Actionable recommendations documented for assessor list refinement (which to keep/remove/retune)
✅ Evidence-based tier assignments validated by real data
✅ Deliverable: `docs/tbench/assessor-refinement-results.md` documenting empirical assessor effectiveness

**Note**: Submission features (leaderboard integration, public submissions) are Phase 3, not Phase 2. Phase 2 focuses on using Terminal-Bench for internal refinement feedback.

### Resources

**Primary**:
- Harbor Framework Documentation: https://harborframework.com/docs

**Supporting**:
- Terminal-Bench: https://tbench.ai
- Full plan document: `/Users/jeder/.claude/plans/adaptive-tickling-star.md`
- Demo: `/Users/jeder/repos/agentready/DEMO_EVAL_HARNESS.md`
- Methodology: `/Users/jeder/repos/agentready/docs/tbench/methodology.md`

### Current Branch

```bash
git checkout feature/eval-harness-mvp
git pull origin feature/eval-harness-mvp
```

**Tests**: Run `pytest tests/unit/test_eval_harness*.py tests/integration/test_eval_harness*.py -v` to verify Phase 1 baseline.

---

**Cold-Start Prompt Created**: 2025-12-08
**Ready For**: Phase 2 Harbor integration implementation
