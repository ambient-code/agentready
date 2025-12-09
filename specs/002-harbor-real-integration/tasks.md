# Implementation Tasks: Harbor Framework Real Integration for Terminal-Bench Eval Harness

**Feature Branch**: `002-harbor-real-integration`
**Created**: 2025-12-09
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Overview

This document breaks down the Harbor Framework Real Integration feature into executable, dependency-ordered tasks. Tasks are organized by user story to enable independent implementation and testing following TDD (Test-Driven Development) red-green-refactor workflow.

**Total Tasks**: 35
**Estimated Implementation**: ~120 lines of new code (76% reduction from original plan)
**TDD Approach**: MANDATORY - Tests written FIRST (red phase) before implementation (green phase)

---

## Task Format Legend

```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

- **[TaskID]**: Sequential number (T001, T002, ...) in execution order
- **[P]**: Parallelizable (can run simultaneously with other [P] tasks in same phase)
- **[Story]**: User story label ([US1], [US2], [US3], [US4]) for tracking
- **File Path**: Exact location for implementation

---

## Phase 1: Setup & Dependencies

**Goal**: Prepare project environment and install Harbor framework dependency.

**Tasks**:

- [X] T001 Add `harbor>=2.0.0` dependency to `pyproject.toml` under dependencies section
- [X] T002 Install Harbor framework package via `uv pip install harbor` and verify installation with `harbor --version`
- [X] T003 Update `.gitignore` to exclude temporary benchmark output directories (`**/tbench-results/`, `**/.harbor-cache/`)
- [X] T004 Create `src/agentready/services/eval_harness/harbor_config.py` file stub (empty file with module docstring)

**Completion Criteria**: Harbor package installed, project dependencies updated, file structure ready for implementation.

---

## Phase 2: Foundational Infrastructure (Blocking Prerequisites)

**Goal**: Implement core configuration and validation infrastructure needed by all user stories.

**Independent Test**: HarborConfig validation can be tested independently with unit tests before any Harbor subprocess integration.

### 2.1 TDD: Write Tests for HarborConfig (Red Phase)

- [X] T005 [P] Create `tests/unit/test_harbor_config.py` with test structure and imports
- [X] T006 [P] Write test `test_harbor_config_valid_model_haiku` - verify haiku-4-5 model accepted in `tests/unit/test_harbor_config.py`
- [X] T007 [P] Write test `test_harbor_config_valid_model_sonnet` - verify sonnet-4-5 model accepted in `tests/unit/test_harbor_config.py`
- [X] T008 [P] Write test `test_harbor_config_invalid_model_rejected` - verify invalid model raises ValueError in `tests/unit/test_harbor_config.py`
- [X] T009 [P] Write test `test_harbor_config_invalid_agent_rejected` - verify invalid agent raises ValueError in `tests/unit/test_harbor_config.py`
- [X] T010 [P] Write test `test_harbor_config_empty_api_key_rejected` - verify empty API key raises ValueError in `tests/unit/test_harbor_config.py`
- [X] T011 [P] Write test `test_harbor_config_negative_timeout_rejected` - verify negative timeout raises ValueError in `tests/unit/test_harbor_config.py`
- [X] T012 [P] Write test `test_harbor_config_path_resolution` - verify jobs_dir resolved to absolute path in `tests/unit/test_harbor_config.py`

**Checkpoint**: Run tests, verify all FAIL (red phase complete) - `pytest tests/unit/test_harbor_config.py`

### 2.2 Implement HarborConfig (Green Phase)

- [X] T013 Define `ALLOWED_MODELS` constant set in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T014 Define `ALLOWED_AGENTS` constant set in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T015 Implement `HarborConfig` dataclass with all fields (model, agent, jobs_dir, api_key, timeout, n_concurrent) in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T016 Implement `HarborConfig.__post_init__()` with model allowlist validation in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T017 Implement `HarborConfig.__post_init__()` with agent allowlist validation in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T018 Implement `HarborConfig.__post_init__()` with API key non-empty validation in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T019 Implement `HarborConfig.__post_init__()` with timeout positive validation in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T020 Implement `HarborConfig.__post_init__()` with jobs_dir path resolution to absolute path in `src/agentready/services/eval_harness/harbor_config.py`

**Checkpoint**: Run tests, verify all PASS (green phase complete) - `pytest tests/unit/test_harbor_config.py`

### 2.3 Refactor & Document (Refactor Phase)

- [X] T021 Add docstrings to `HarborConfig` class and `__post_init__` method in `src/agentready/services/eval_harness/harbor_config.py`
- [X] T022 Add module-level docstring explaining Harbor framework configuration in `src/agentready/services/eval_harness/harbor_config.py`

**Completion Criteria**: HarborConfig fully tested and implemented with >80% coverage, all tests passing.

---

## Phase 3: User Story 1 + User Story 3 (P1 - MVP)

**Combined Stories**: US1 (Run Real Terminal-Bench Evaluations) + US3 (Secure API Integration)

**Why Combined**: Security is integral to Harbor subprocess calls, not a separate feature. US3 requirements are implemented directly within US1's Harbor integration code.

**Goal**: Replace `_real_tbench_result()` NotImplementedError with functional, secure Harbor framework subprocess integration.

**Independent Test**: Run single benchmark on one repository, verify real Harbor framework subprocess called with sanitized environment variables, results parsed correctly, and differ from mocked results.

### 3.1 TDD: Write Tests for Harbor Subprocess Integration (Red Phase)

- [X] T023 [P] [US1] Write test `test_real_tbench_result_subprocess_called` - verify `harbor run` command constructed correctly in `tests/unit/test_eval_harness_services.py`
- [X] T024 [P] [US1] [US3] Write test `test_environment_variable_sanitization` - verify only ANTHROPIC_API_KEY, PATH, HOME passed to subprocess in `tests/unit/test_eval_harness_services.py`
- [X] T025 [P] [US1] Write test `test_harbor_subprocess_timeout_enforced` - verify subprocess.run called with timeout=3600 in `tests/unit/test_eval_harness_services.py`
- [X] T026 [P] [US1] Write test `test_harbor_subprocess_timeout_exception` - verify RuntimeError raised when subprocess times out in `tests/unit/test_eval_harness_services.py`
- [X] T027 [P] [US1] Write test `test_harbor_subprocess_failure_exception` - verify RuntimeError raised when subprocess fails in `tests/unit/test_eval_harness_services.py`

**Checkpoint**: Run tests, verify all FAIL (red phase complete) - `pytest tests/unit/test_eval_harness_services.py -k "real_tbench"`

### 3.2 TDD: Write Tests for JSON Parsing with Path Validation (Red Phase)

- [X] T028 [P] [US1] [US3] Write test `test_parse_harbor_results_valid_json` - verify results.json parsed correctly in `tests/unit/test_eval_harness_services.py`
- [X] T029 [P] [US1] Write test `test_parse_harbor_results_creates_tbench_result` - verify TbenchResult created with is_mocked=False in `tests/unit/test_eval_harness_services.py`
- [X] T030 [P] [US1] [US3] Write test `test_parse_harbor_results_path_validation` - verify path traversal attack (../../etc/passwd) rejected in `tests/unit/test_eval_harness_services.py`
- [X] T031 [P] [US1] Write test `test_parse_harbor_results_invalid_json_exception` - verify JSONDecodeError handled gracefully in `tests/unit/test_eval_harness_services.py`

**Checkpoint**: Run tests, verify all FAIL (red phase complete) - `pytest tests/unit/test_eval_harness_services.py -k "parse_harbor"`

### 3.3 Implement TbenchResult Extension (Green Phase)

- [X] T032 [US1] Extend `TbenchResult` dataclass with new optional fields (resolved_trials, unresolved_trials, pass_at_1, pass_at_3) with default values in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T033 [US1] Add `TbenchResult.__post_init__()` validation for score range [0.0, 1.0] in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T034 [US1] Add `TbenchResult.__post_init__()` validation for non-negative trial counts in `src/agentready/services/eval_harness/tbench_runner.py`

### 3.4 Implement Harbor Subprocess Integration (Green Phase)

- [X] T035 [US1] Import `HarborConfig`, `subprocess`, `tempfile`, `os`, `json` at top of `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T036 [US1] Replace `_real_tbench_result()` NotImplementedError with HarborConfig initialization in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T037 [US1] Implement `_real_tbench_result()` - build `harbor run` command list with all parameters in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T038 [US1] [US3] Implement `_real_tbench_result()` - create clean_env dict with only ANTHROPIC_API_KEY, PATH, HOME in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T039 [US1] Implement `_real_tbench_result()` - call subprocess.run() with cmd, env, timeout, check=True in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T040 [US1] Implement `_real_tbench_result()` - handle subprocess.TimeoutExpired exception, raise RuntimeError in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T041 [US1] Implement `_real_tbench_result()` - handle subprocess.CalledProcessError exception, raise RuntimeError in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T042 [US1] [US3] Implement `_real_tbench_result()` - validate results_path.is_relative_to(jobs_dir), raise ValueError if path traversal detected in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T043 [US1] Implement `_real_tbench_result()` - call parse_harbor_results() and return TbenchResult in `src/agentready/services/eval_harness/tbench_runner.py`

### 3.5 Implement JSON Parsing Function (Green Phase)

- [X] T044 [US1] Create `parse_harbor_results(results_path: Path) -> TbenchResult` function in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T045 [US1] Implement `parse_harbor_results()` - open and load results.json with json.load() in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T046 [US1] Implement `parse_harbor_results()` - extract summary dict from data["summary"] in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T047 [US1] Implement `parse_harbor_results()` - create TbenchResult with all fields mapped from summary in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T048 [US1] Implement `parse_harbor_results()` - set is_mocked=False, task_solved=resolved_trials>0 in `src/agentready/services/eval_harness/tbench_runner.py`

**Checkpoint**: Run all tests, verify PASS (green phase complete) - `pytest tests/unit/test_eval_harness_services.py tests/unit/test_harbor_config.py`

### 3.6 Integration Test (Red-Green)

- [X] T049 [US1] Write integration test `test_full_real_benchmark_workflow_mocked_subprocess` in `tests/integration/test_eval_harness_e2e.py` - mock subprocess.run, verify end-to-end flow
- [X] T050 [US1] Implement fix if integration test fails, verify test passes

**Checkpoint**: Run integration test, verify PASS - `pytest tests/integration/test_eval_harness_e2e.py -k "real_benchmark"`

### 3.7 Refactor & Document (Refactor Phase)

- [X] T051 [US1] Add docstrings to `_real_tbench_result()` and `parse_harbor_results()` functions in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T052 [US1] [US3] Add inline security comments explaining env sanitization and path validation in `src/agentready/services/eval_harness/tbench_runner.py`
- [X] T053 [US1] Extract magic numbers (timeout=3600, n_concurrent=1) to constants at module level in `src/agentready/services/eval_harness/tbench_runner.py`

**Completion Criteria**:
- ✅ User Story 1 complete: Real benchmarks run successfully via Harbor framework
- ✅ User Story 3 complete: Security validations prevent API key exposure and command injection
- ✅ Tests passing with >80% coverage for new Harbor integration code
- ✅ Independent test verified: Single benchmark on one repository succeeds with real Harbor subprocess

**MVP Milestone**: This phase completes the minimum viable product - real, secure Harbor framework integration.

---

## Phase 4: User Story 2 (P2 - Aggregation)

**Goal**: Implement pandas-based aggregation to summarize assessor effectiveness across multiple repositories.

**Independent Test**: Run benchmarks on 3-5 repositories with different assessors, verify aggregation shows mean/median/std delta scores correctly grouped by assessor.

### 4.1 TDD: Write Tests for Aggregation Logic (Red Phase)

- [X] T054 [P] [US2] Write test `test_summarize_aggregates_by_assessor` - verify pandas groupby on assessor_id in `tests/unit/test_eval_harness_cli.py`
- [X] T055 [P] [US2] Write test `test_summarize_calculates_mean_median_std` - verify correct aggregation functions in `tests/unit/test_eval_harness_cli.py`
- [X] T056 [P] [US2] Write test `test_summarize_adds_significance_indicator` - verify boolean significant column added in `tests/unit/test_eval_harness_cli.py`
- [X] T057 [P] [US2] Write test `test_summarize_sorts_by_mean_delta_descending` - verify results sorted correctly in `tests/unit/test_eval_harness_cli.py`
- [X] T058 [P] [US2] Write test `test_summarize_exports_json` - verify JSON file written with correct schema in `tests/unit/test_eval_harness_cli.py`

**Checkpoint**: Run tests, verify all FAIL (red phase complete) - `pytest tests/unit/test_eval_harness_cli.py -k "summarize"` ✅

### 4.2 Implement Aggregation Logic (Green Phase)

**Note**: Implemented in `src/agentready/services/eval_harness/aggregator.py` (separate module following "generic interface first" principle) instead of CLI file. CLI integration deferred to future task.

- [X] T059 [US2] Import `pandas as pd` in aggregator module
- [X] T060 [US2] Create `aggregate_results()` function signature with generic interface
- [X] T061 [US2] Implement `aggregate_results()` - create DataFrame from results list
- [X] T062 [US2] Implement `aggregate_results()` - groupby aggregation (mean, median, std, count)
- [X] T063 [US2] Implement `aggregate_results()` - rename columns to mean_delta, median_delta, std_delta, sample_size
- [X] T064 [US2] Implement `aggregate_results()` - add significant column with abs(mean_delta) > 0.05 placeholder
- [X] T065 [US2] Implement `aggregate_results()` - sort by mean_delta descending
- [X] T066 [US2] Handle edge cases (empty results, NaN std for single values)
- [X] T067 [US2] Round numeric values to 2 decimal places for readability

**Checkpoint**: Run tests, verify all PASS (green phase complete) - `pytest tests/unit/test_eval_harness_cli.py` ✅

### 4.3 Refactor & Document (Refactor Phase)

- [X] T068 [US2] Add comprehensive docstrings to `aggregate_results()` function with Args/Returns/Examples
- [X] T069 [US2] Add module-level docstring explaining aggregation purpose and usage

**Completion Criteria**:
- ✅ User Story 2 complete: Aggregation summarizes assessor effectiveness across repositories
- ✅ Tests passing with >80% coverage for aggregation logic
- ✅ Independent test verified: Aggregation on 3-5 repositories produces correct statistics

---

## Phase 5: User Story 4 (P2 - Parallel Execution)

**Goal**: Implement resource-limited parallel execution with ProcessPoolExecutor to handle large batches without exhausting system resources.

**Independent Test**: Run 20+ parallel benchmark jobs, verify system respects 4-worker limit and handles timeouts gracefully.

### 5.1 TDD: Write Tests for Parallel Execution (Red Phase)

- [X] T070 [P] [US4] Write test `test_parallel_execution_max_4_workers` - verify ProcessPoolExecutor initialized with max_workers=4 in `tests/unit/test_eval_harness_services.py`
- [X] T071 [P] [US4] Write test `test_parallel_execution_timeout_per_job` - verify each job has 3600s timeout in `tests/unit/test_eval_harness_services.py`
- [X] T072 [P] [US4] Write test `test_parallel_execution_handles_partial_failures` - verify some jobs can fail without blocking others in `tests/unit/test_eval_harness_services.py`
- [X] T073 [P] [US4] Write test `test_parallel_execution_aggregates_successful_results` - verify only successful results aggregated in `tests/unit/test_eval_harness_services.py`

**Checkpoint**: Run tests, verify all FAIL (red phase complete) - `pytest tests/unit/test_eval_harness_services.py -k "parallel"` ✅

### 5.2 Implement Parallel Execution (Green Phase)

- [X] T074 [US4] Import `concurrent.futures.ProcessPoolExecutor`, `concurrent.futures.as_completed` in `src/agentready/services/eval_harness/batch_runner.py` (new file)
- [X] T075 [US4] Create `run_batch_benchmarks()` function with repositories list parameter in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T076 [US4] Implement `run_batch_benchmarks()` - initialize ProcessPoolExecutor with max_workers=4 in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T077 [US4] Implement `run_batch_benchmarks()` - submit futures for each repository in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T078 [US4] Implement `run_batch_benchmarks()` - use as_completed() to handle futures as they finish in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T079 [US4] Implement `run_batch_benchmarks()` - catch exceptions from future.result(timeout=3600) in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T080 [US4] Implement `run_batch_benchmarks()` - log failures, aggregate successes, return results list in `src/agentready/services/eval_harness/batch_runner.py`

**Checkpoint**: Run tests, verify all PASS (green phase complete) - `pytest tests/unit/test_eval_harness_services.py -k "parallel"` ✅

### 5.3 Refactor & Document (Refactor Phase)

- [X] T081 [US4] Add docstrings to `run_batch_benchmarks()` function in `src/agentready/services/eval_harness/batch_runner.py`
- [X] T082 [US4] Extract worker count (4) and job timeout (3600) to module-level constants in `src/agentready/services/eval_harness/batch_runner.py`

**Completion Criteria**:
- ✅ User Story 4 complete: Parallel execution handles large batches without resource exhaustion
- ✅ Tests passing with >80% coverage for parallel execution logic
- ✅ Independent test verified: 20+ jobs execute with max 4 concurrent workers

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Complete documentation, run linters, verify coverage, and ensure production readiness.

### 6.1 Documentation Updates

- [ ] T083 [P] Update `README.md` - add "Running Real Terminal-Bench Evaluations (Phase 2)" section with Harbor setup instructions
- [ ] T084 [P] Update `README.md` - add prerequisites (Docker, Anthropic API key), setup commands, quickstart example
- [ ] T085 [P] Create `docs/tbench/assessor-refinement-results.md` template with methodology, high-impact assessors, low-impact assessors, recommendations sections (structure only, data to be filled after benchmarks run)
- [ ] T086 [P] Update `docs/tbench/methodology.md` - add "Phase 2: Real-World Validation" section explaining Harbor integration, real vs mocked comparison, statistical significance approach

### 6.2 Linting & Code Quality

- [ ] T087 Run `black src/agentready/services/eval_harness/ src/agentready/cli/eval_harness.py tests/` to format all modified files
- [ ] T088 Run `isort src/agentready/services/eval_harness/ src/agentready/cli/eval_harness.py tests/` to sort imports
- [ ] T089 Run `flake8 src/agentready/services/eval_harness/ src/agentready/cli/eval_harness.py tests/ --ignore=E501,E203,W503` to verify linting (no line length enforcement)
- [ ] T090 Fix any linting errors reported by flake8

### 6.3 Testing & Coverage

- [ ] T091 Run full test suite: `pytest tests/unit/test_harbor_config.py tests/unit/test_eval_harness_services.py tests/unit/test_eval_harness_cli.py tests/integration/test_eval_harness_e2e.py`
- [ ] T092 Run coverage report: `pytest --cov=src/agentready/services/eval_harness --cov=src/agentready/cli/eval_harness --cov-report=html --cov-report=term`
- [ ] T093 Verify coverage >80% for new Harbor integration code (harbor_config.py, tbench_runner.py modifications, eval_harness.py modifications, batch_runner.py)
- [ ] T094 Add additional tests if coverage gaps identified (target missing branches, edge cases)

### 6.4 Final Integration Verification

- [ ] T095 Manually test: `export TBENCH_USE_REAL=1 && export ANTHROPIC_API_KEY=<key> && agentready tbench baseline /path/to/test/repo` - verify real Harbor subprocess called
- [ ] T096 Manually test: Verify results differ from mocked integration (run same repo with TBENCH_USE_REAL=0 vs =1, compare scores)
- [ ] T097 Manually test: Verify error handling - run without ANTHROPIC_API_KEY, verify clear error message with installation instructions
- [ ] T098 Manually test: Verify security - inspect subprocess call with process monitor, confirm only required env vars passed

**Completion Criteria**:
- ✅ All documentation updated
- ✅ All linters pass (black, isort, flake8)
- ✅ All tests pass with >80% coverage
- ✅ Manual integration tests verify real Harbor framework integration works end-to-end
- ✅ Security validations confirmed via manual testing

---

## Dependencies & Execution Order

### User Story Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Setup & Dependencies                           │
│ (T001-T004)                                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Foundational Infrastructure                    │
│ (T005-T022) - HarborConfig implementation               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: US1 + US3 (P1 MVP)                            │
│ (T023-T053) - Real Harbor integration + Security       │
│ ✓ Independent - Can deploy alone                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├──────────────────┬─────────────────────┐
                 │                  │                     │
                 ▼                  ▼                     ▼
┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ Phase 4: US2 (P2)    │  │ Phase 5: US4 (P2)│  │ Phase 6: Polish    │
│ (T054-T069)          │  │ (T070-T082)      │  │ (T083-T098)        │
│ Aggregation          │  │ Parallel Exec    │  │ Documentation      │
│ ✓ Independent of US4 │  │ ✓ Independent of US2│ │ ⚠️ Requires US1-4 │
└──────────────────────┘  └──────────────────┘  └────────────────────┘
```

**Blocking Dependencies**:
- Phase 1 blocks all other phases (setup required first)
- Phase 2 blocks Phase 3, 4, 5 (HarborConfig needed for Harbor integration and aggregation config)
- Phase 3 blocks Phase 6 (MVP must be complete before polish)
- Phase 4 and Phase 5 are independent of each other (can be implemented in parallel)

**Story Independence**:
- ✅ **US1 (Real Benchmarks)**: Fully independent, can deploy alone after Phase 2
- ✅ **US2 (Aggregation)**: Independent of US4, depends only on US1 for benchmark results
- ✅ **US3 (Security)**: Integrated into US1 (not separate implementation)
- ✅ **US4 (Parallel Execution)**: Independent of US2, depends only on US1 for benchmark runner

---

## Parallel Execution Opportunities

### Within Each Phase

**Phase 2 (Foundational)**:
- Tests T005-T012 can run in parallel (all are test writing, no shared state)
- Implementation tasks T013-T020 are sequential (shared file modifications)

**Phase 3 (US1 + US3 MVP)**:
- Tests T023-T031 can run in parallel (different test files/functions)
- Implementation tasks T032-T053 are mostly sequential (shared file modifications)

**Phase 4 (US2 Aggregation)**:
- Tests T054-T058 can run in parallel (independent test cases)
- Implementation tasks T059-T069 are sequential (shared file modifications)

**Phase 5 (US4 Parallel Execution)**:
- Tests T070-T073 can run in parallel (independent test cases)
- Implementation tasks T074-T082 are sequential (new file, but sequential logic)

**Phase 6 (Polish)**:
- Documentation tasks T083-T086 can run in parallel (different files)
- Linting tasks T087-T090 must run sequentially (formatter output affects linter input)
- Testing tasks T091-T094 are sequential (coverage depends on all tests running)
- Manual verification T095-T098 are sequential (depends on implementation complete)

### Parallelization Summary

**Estimated Parallelization Gains**:
- ~40% of tasks marked [P] can run in parallel
- Most parallelism in test writing phases (TDD red phase)
- Implementation phases are mostly sequential due to shared file modifications

---

## Implementation Strategy

### Recommended Approach: Incremental Delivery

**Week 1: MVP (Phase 1-3)**
1. Complete Setup & Dependencies (Phase 1): ~1 hour
2. Complete Foundational Infrastructure (Phase 2): ~1 day
   - TDD: Write all tests (red) → Implement HarborConfig (green) → Refactor
3. Complete US1 + US3 MVP (Phase 3): ~2-3 days
   - TDD: Write all tests (red) → Implement Harbor integration (green) → Refactor
   - **Milestone**: MVP deployable - real, secure Harbor benchmarks work

**Week 2: Enhancement Features (Phase 4-5)**
4. Complete US2 Aggregation (Phase 4): ~1 day
   - TDD: Write tests → Implement pandas aggregation → Refactor
5. Complete US4 Parallel Execution (Phase 5): ~1 day
   - TDD: Write tests → Implement ProcessPoolExecutor → Refactor

**Week 3: Polish & Production Readiness (Phase 6)**
6. Complete Documentation, Linting, Coverage (Phase 6): ~1 day
7. Manual integration testing and verification: ~1 day

**Total Estimated Duration**: 2-3 weeks (10-15 working days)

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 6 (Documentation)

**Suggested MVP Scope**: Phase 1-3 only (real, secure Harbor benchmarks) - delivers core value, can release independently.

---

## Testing Strategy Summary

**Test-Driven Development (TDD)**: MANDATORY per Constitution Principle IV

**Red-Green-Refactor Workflow**:
1. **Red Phase**: Write tests FIRST, verify they FAIL
2. **Green Phase**: Implement code to make tests PASS
3. **Refactor Phase**: Improve code quality, add docs, extract constants

**Test Coverage Goals**:
- >80% line coverage for new code (per Constitution)
- >90% branch coverage for security-critical code (env sanitization, allowlist validation, path validation)
- 100% coverage for HarborConfig validation logic

**Test Types**:
- **Unit Tests**: Test individual functions/classes in isolation (mocked dependencies)
- **Integration Tests**: Test full workflow with mocked subprocess calls
- **Manual Tests**: Verify real Harbor subprocess integration end-to-end

**Test Count by Phase**:
- Phase 2: 8 unit tests (HarborConfig validation)
- Phase 3: 13 unit tests + 1 integration test (Harbor integration, JSON parsing, security)
- Phase 4: 5 unit tests (pandas aggregation)
- Phase 5: 4 unit tests (parallel execution)
- **Total**: 30+ tests for 120 lines of implementation code (~4:1 test-to-code ratio)

---

## Risk Mitigation During Implementation

**Risk 1: Harbor framework behavior differs from documentation**
- **Mitigation Task**: T049 (integration test) catches this early
- **Response**: Update implementation based on actual Harbor output format

**Risk 2: Test coverage falls below 80%**
- **Mitigation Task**: T093-T094 (coverage verification and gap filling)
- **Response**: Add missing tests before declaring phase complete

**Risk 3: Security validations insufficient**
- **Mitigation Tasks**: T024, T030, T042, T098 (security-focused tests and manual verification)
- **Response**: Enhance allowlists or validation logic if vulnerabilities found

**Risk 4: Performance slower than estimated (>10 min per benchmark)**
- **Mitigation**: MVP (Phase 3) deployment allows real-world performance measurement
- **Response**: Adjust timeout values or add performance optimization tasks if needed

---

## Next Steps

1. ✅ Tasks generated and organized by user story
2. ⏭️ Begin Phase 1: Setup & Dependencies (T001-T004)
3. ⏭️ Begin Phase 2: TDD for HarborConfig (T005-T022)
4. ⏭️ Track progress: Use task checkboxes to mark completion
5. ⏭️ After MVP (Phase 3): Deploy and test with real repositories
6. ⏭️ After all phases: Run empirical benchmarks on 10-20 repositories, document findings in `docs/tbench/assessor-refinement-results.md`

---

**Document Status**: Complete
**Last Updated**: 2025-12-09
**Ready for Implementation**: ✅ Yes
**Estimated Effort**: 10-15 working days (120 lines of code, 30+ tests, following TDD)
