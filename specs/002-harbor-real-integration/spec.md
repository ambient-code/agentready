# Feature Specification: Harbor Framework Real Integration for Terminal-Bench Eval Harness

**Feature Branch**: `002-harbor-real-integration`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Review https://github.com/ambient-code/agentready/issues/190 and all comments and implement accordingly. Make sure to also consult .claude/agents/doubleagent.md as necessary. I want you to track and report on what the specific impact of doubleagent.md was in this implementation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Real Terminal-Bench Evaluations (Priority: P1)

A developer wants to run real Terminal-Bench evaluations on their repository to measure how well AgentReady assessors improve AI coding assistant performance using actual benchmark data from the Harbor framework, not mocked results.

**Why this priority**: This is the core value proposition of Phase 2 - replacing mocked integration with real empirical data. Without this, we cannot validate assessor effectiveness with real-world evidence.

**Independent Test**: Can be fully tested by running a single benchmark on one repository and verifying that real Harbor framework API is called, results are returned, and they differ from mocked results.

**Acceptance Scenarios**:

1. **Given** Harbor framework CLI is installed and API credentials are configured, **When** developer runs `agentready tbench baseline /path/to/repo`, **Then** system submits repository to real Terminal-Bench via Harbor framework and returns actual benchmark score
2. **Given** Harbor framework is installed, **When** developer runs `agentready tbench test-assessor --assessor claude_md /path/to/repo`, **Then** system runs real baseline and delta evaluation and reports actual score improvement
3. **Given** environment variable `TBENCH_USE_REAL=1` is set, **When** any tbench command executes, **Then** system uses real Harbor framework instead of mocked implementation
4. **Given** Harbor framework is not installed, **When** developer runs tbench command, **Then** system shows clear error message with installation instructions

---

### User Story 2 - Aggregate Multi-Repository Results (Priority: P2)

A researcher wants to run benchmarks across multiple diverse repositories (different languages, sizes, domains) and see aggregated statistics showing which assessors consistently improve benchmark scores and which have no measurable impact.

**Why this priority**: This enables the empirical assessor refinement goal - identifying high-impact vs low-impact assessors based on real data. This is valuable but depends on Story 1 being complete first.

**Independent Test**: Can be tested by running benchmarks on 3-5 repositories with different assessors and verifying that aggregation shows mean/median/std delta scores correctly grouped by assessor.

**Acceptance Scenarios**:

1. **Given** benchmark results exist for 10+ repositories, **When** developer runs `agentready tbench summarize`, **Then** system shows aggregated statistics (mean, median, std) for each assessor's delta impact
2. **Given** aggregated results are displayed, **When** developer reviews output, **Then** assessors are ranked by mean delta score with statistical significance indicators
3. **Given** multiple benchmark runs exist, **When** developer requests summary, **Then** system identifies assessors with consistently positive impact vs assessors with no significant impact
4. **Given** aggregated data exists, **When** developer views results, **Then** recommendations are provided for which assessors to keep/promote and which to remove/demote

---

### User Story 3 - Secure API Integration (Priority: P1)

A developer wants to run real benchmarks without exposing their API credentials to subprocesses or command injection vulnerabilities, ensuring that sensitive data is properly sanitized and validated.

**Why this priority**: Security is critical when integrating with external APIs. The automated review identified critical vulnerabilities (API key exposure, command injection) that must be fixed before production use. This has same priority as P1 because it blocks safe deployment.

**Independent Test**: Can be tested by attempting to pass malicious input to model/agent parameters and verifying rejection, and by checking that only required environment variables are passed to subprocesses.

**Acceptance Scenarios**:

1. **Given** API credentials are in environment variables, **When** Harbor framework subprocess is called, **Then** only required variables (API key, PATH, HOME) are passed, not all environment variables
2. **Given** user provides model parameter, **When** system validates input, **Then** only allowlisted models (claude-haiku-4-5, claude-sonnet-4-5) are accepted
3. **Given** user provides agent parameter, **When** system validates input, **Then** only allowlisted agents (claude-code) are accepted
4. **Given** malicious input is provided for model/agent parameters, **When** system validates, **Then** input is rejected with clear error message before subprocess call

---

### User Story 4 - Resource-Limited Parallel Execution (Priority: P2)

A developer wants to run benchmarks on multiple repositories in parallel without exhausting system resources (memory, CPU, file handles), ensuring stable execution even when processing large batches.

**Why this priority**: Running 8 repositories × 35 assessor combinations (280 total runs) requires careful resource management to avoid system crashes. Important for production use but not blocking MVP.

**Independent Test**: Can be tested by running 20+ parallel benchmark jobs and verifying that system respects worker pool limits (max 4 concurrent) and handles timeouts gracefully.

**Acceptance Scenarios**:

1. **Given** developer runs benchmarks on 10 repositories, **When** execution starts, **Then** no more than 4 benchmarks run concurrently regardless of total queue size
2. **Given** parallel execution is running, **When** one benchmark times out (1 hour limit), **Then** that job is terminated and next job starts without blocking other workers
3. **Given** resource limits are in place, **When** running large batch (50+ repos), **Then** system remains stable and does not exhaust file handles or memory
4. **Given** parallel execution completes, **When** developer reviews results, **Then** all successful results are aggregated and failures are clearly logged

---

### Edge Cases

- What happens when Harbor framework is installed but API credentials are missing or invalid?
- How does system handle network failures during long-running benchmark submissions (30+ minutes)?
- What happens when a benchmark times out after the Harbor framework's internal timeout (not our timeout)?
- How does system handle repositories that are too large for Terminal-Bench (>100k files)?
- What happens when Harbor CLI returns non-JSON output (error messages, warnings)?
- How does system handle partial results when some repositories succeed and others fail in batch mode?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace `_real_tbench_result()` NotImplementedError with functional Harbor framework subprocess integration
- **FR-002**: System MUST validate model parameter against allowlist (anthropic/claude-haiku-4-5, anthropic/claude-sonnet-4-5) before subprocess call
- **FR-003**: System MUST validate agent parameter against allowlist (claude-code) before subprocess call
- **FR-004**: System MUST pass only required environment variables (API key, PATH, HOME) to Harbor subprocess, not all environment variables
- **FR-005**: System MUST parse Harbor framework JSON output and validate file paths before reading
- **FR-006**: System MUST return TbenchResult with is_mocked=False when using real Harbor framework
- **FR-007**: System MUST support environment variable `TBENCH_USE_REAL=1` to toggle between mocked and real integration
- **FR-008**: System MUST limit parallel execution to 4 concurrent workers using ProcessPoolExecutor
- **FR-009**: System MUST enforce 1-hour timeout per individual benchmark run
- **FR-010**: System MUST aggregate results across multiple repositories showing mean, median, standard deviation for each assessor's delta score
- **FR-011**: System MUST indicate statistical significance when aggregating results (e.g., confidence intervals, p-values)
- **FR-012**: System MUST handle Harbor framework errors gracefully with clear error messages and installation guidance
- **FR-013**: System MUST document aggregated results in `docs/tbench/assessor-refinement-results.md` with recommendations for assessor list changes
- **FR-014**: System MUST preserve backward compatibility with existing mocked integration for testing/development

### Key Entities

- **TbenchResult**: Represents benchmark output with score, task_solved boolean, and is_mocked flag indicating real vs mocked execution
- **BenchmarkRun**: Represents single benchmark execution with repository path, assessor ID (or None for baseline), timestamp, result, and execution metadata (duration, errors)
- **AggregatedResult**: Represents statistical summary across multiple repositories for a specific assessor including mean/median/std delta scores, sample size, and significance indicators
- **HarborConfig**: Represents Harbor framework configuration including API credentials, model selection, agent selection, and timeout settings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can successfully run real Terminal-Bench evaluations on at least 10 diverse repositories with 100% success rate for repositories under 50k files
- **SC-002**: Benchmark results from real Harbor framework differ measurably from mocked results (validate by comparing scores on same repository)
- **SC-003**: System blocks invalid model/agent parameters with 100% accuracy before subprocess execution (security validation)
- **SC-004**: System exposes zero API credentials to subprocess environment beyond required variables (verified via process inspection)
- **SC-005**: Parallel execution of 20+ repositories completes without resource exhaustion (memory stays under 2GB, file handles under 1024)
- **SC-006**: Aggregated results clearly identify top 5 assessors with highest mean delta improvement and bottom 5 with no measurable impact
- **SC-007**: Documentation deliverable (`docs/tbench/assessor-refinement-results.md`) provides actionable recommendations for assessor tier changes based on empirical data
- **SC-008**: 95% of Harbor framework errors result in clear, actionable error messages for users (not stack traces)
- **SC-009**: Complete benchmark suite (8 repos × 35 assessors = 280 runs) completes in under 24 hours with 4-worker parallelism
- **SC-010**: System maintains 100% backward compatibility with existing mocked integration for automated testing

## Assumptions

- Harbor framework Python package exists and is installable via pip/uv (package name to be confirmed during implementation)
- Terminal-Bench API access is available via tbench.ai with API key authentication
- Benchmark execution time averages 5-10 minutes per repository (informing timeout and parallelism decisions)
- Developers have Harbor CLI installed locally before using real integration (installation documented in README)
- Standard session-based authentication is sufficient for Harbor framework API (no OAuth required)
- JSON is the standard output format for Harbor framework results
- Repositories under 50k files are supported by Terminal-Bench (larger repositories may fail or timeout)
- Statistical significance can be determined with 10-20 repository samples per assessor (adequate sample size)
- Default behavior remains mocked integration unless explicitly toggled with environment variable (safe default for CI/CD)

## Scope

### In Scope

- Replace NotImplementedError in `_real_tbench_result()` with functional Harbor framework integration
- Add input validation (allowlist) for model and agent parameters
- Sanitize environment variables passed to Harbor subprocess
- Add parallel execution limits (4 workers) with timeouts (1 hour per job)
- Add pandas-based aggregation to existing `summarize` command for cross-repo statistics
- Document empirical findings in `docs/tbench/assessor-refinement-results.md`
- Update `README.md` with Harbor setup instructions
- Add environment variable toggle (`TBENCH_USE_REAL=1`) for real vs mocked integration
- Add integration tests with subprocess mocking for Harbor calls

### Out of Scope

- Custom exception classes (7 classes) - use RuntimeError instead per simplified approach
- Pre-flight check methods (3 methods) - trust Harbor's validation
- Separate `CrossRepoAggregator` service class - inline with pandas in CLI
- Docker installation validation - trust Harbor framework's Docker checks
- Public leaderboard submission features (Phase 3)
- Real-time progress UI during long-running benchmarks
- Retry logic for transient network failures (rely on Harbor's internal retry)
- Custom timeout configurations per repository size
- Automated assessor tier reassignment based on results (manual review required)

## Dependencies

- Harbor framework Python package (exact package name TBD during implementation research)
- Terminal-Bench API access via tbench.ai
- API credentials (environment variable: `TBENCH_API_KEY`)
- Harbor CLI installed locally
- Pandas library for aggregation (already in dependencies)
- Network access to tbench.ai submission endpoints
- Docker (required by Harbor framework for containerized benchmarks)

## Non-Functional Requirements

- **Performance**: Individual benchmark runs complete within 1 hour timeout (assuming 5-10 minute average)
- **Reliability**: System handles network failures and timeouts gracefully without crashing
- **Security**: API credentials never exposed beyond required subprocess environment
- **Usability**: Error messages provide clear guidance with installation instructions
- **Maintainability**: Implementation adds ~120 lines of code (not 507) following simplified approach
- **Compatibility**: Maintains 100% backward compatibility with existing mocked integration

## Risks & Mitigations

**Risk**: Harbor framework package name or API may differ from documentation
**Mitigation**: Begin with research phase to confirm package installation and basic API usage before full implementation

**Risk**: Real benchmarks may be significantly slower than estimated (5-10 min), causing 24-hour goal to slip
**Mitigation**: Implement configurable worker pool size and timeout values for tuning based on empirical data

**Risk**: Statistical sample size (10-20 repos) may be insufficient for confident significance testing
**Mitigation**: Document confidence intervals and p-values in results; note sample size limitations in recommendations

**Risk**: Command injection may still be possible through repository paths or other inputs
**Mitigation**: Add path validation and sanitization alongside model/agent allowlists

**Risk**: Parallel execution may still exhaust resources despite 4-worker limit on systems with limited memory
**Mitigation**: Document minimum system requirements (4GB RAM, 2GB free disk) in README

## Open Questions

None - all critical decisions have been made based on issue #190 requirements and automated review feedback. Simplified approach removes uncertainty around over-engineered components.
