# Blocking Test Strategy - Follow-Up Tasks

**Created**: 2025-12-09
**Context**: Code review findings from commit 4f3d554

---

## Important Improvements (Moderate Priority)

### 1. Make E2E Test Timeouts Configurable

**Issue**: All E2E subprocess tests use hardcoded `timeout=60`, but on slower CI runners legitimate tests could timeout.

**Current Code** (`tests/e2e/test_critical_paths.py:37, 59, 88, 150, 170`):
```python
result = subprocess.run(
    ["agentready", "assess", ".", "--output-dir", str(output_dir)],
    capture_output=True,
    text=True,
    timeout=60,  # Fixed timeout
)
```

**Recommendation**:
```python
import os
DEFAULT_TIMEOUT = int(os.getenv("AGENTREADY_TEST_TIMEOUT", "90"))

result = subprocess.run(
    [...],
    timeout=DEFAULT_TIMEOUT,
)
```

**Why**: Prevents flaky test failures on slower CI runners or when system is under load.

**Estimated Effort**: 1 hour (simple find/replace across test file)

---

### 2. Add E2E Test for Sensitive Directory Blocking

**Issue**: Tests don't verify the actual sensitive directory blocking works end-to-end.

**Recommendation**:
```python
def test_assess_blocks_sensitive_directories(self):
    """E2E: Verify sensitive directory scanning is blocked."""
    result = subprocess.run(
        ["agentready", "assess", "/etc"],
        capture_output=True,
        text=True,
        timeout=10,
        input="n\n",  # Decline to continue
    )
    assert result.returncode != 0
    assert "sensitive" in result.stdout.lower() or "sensitive" in result.stderr.lower()
```

**Why**: Validates critical security feature works correctly in production.

**Estimated Effort**: 30 minutes

---

## Code Simplification Opportunities (Low Priority)

The code-simplifier agent identified several opportunities to reduce code size while preserving functionality:

### 3. Simplify E2E Tests (37% Reduction)

**Current**: 310 lines
**Simplified**: 195 lines

**Approach**:
- Extract `AssessmentTestHelper` class to eliminate duplication
- Combine 5 separate assessment tests into 1 comprehensive test
- Use `@pytest.mark.parametrize` for CLI command tests

**Files**:
- Reference: `tests/e2e/test_critical_paths_simplified.py` (created by agent)

**Why**: Easier maintenance, faster execution, clearer test intent.

**Estimated Effort**: 2-3 hours (careful refactoring to preserve coverage)

---

### 4. Simplify Config Error Handling (67% Reduction)

**Current**: ~60 lines of if/elif chains
**Simplified**: ~20 lines with dictionary-based dispatch

**Approach**:
- Replace lengthy if/elif chains with dictionary-based error mapping
- Use lambdas for dynamic error message generation
- Maintain all user-friendly error messages

**Files**:
- Reference: `src/agentready/cli/main_simplified.py` (created by agent)

**Why**: More maintainable, clearer logic, easier to extend.

**Estimated Effort**: 1-2 hours

---

### 5. Simplify CI Workflow (40% Reduction)

**Current**: 150 lines, 4 jobs
**Simplified**: 91 lines, 3 jobs

**Approach**:
- Combine blocking tests and linting into single job
- Reduce job startup overhead by consolidating steps
- Run linting only once instead of per Python version

**Files**:
- Reference: `.github/workflows/tests_simplified.yml` (created by agent)

**Why**: Faster CI execution, clearer job purposes, reduced complexity.

**Estimated Effort**: 1-2 hours (careful testing to ensure no regressions)

---

## Detailed Simplification Analysis

See `docs/simplification-analysis.md` (created by code-simplifier agent) for:
- Line-by-line comparison of original vs simplified code
- Rationale for each simplification
- Performance impact analysis
- Migration testing strategy

---

## Success Criteria

**For Items #1-2 (Important)**:
- All tests pass
- No flaky test failures on CI
- Security features validated end-to-end

**For Items #3-5 (Simplification)**:
- 100% test coverage maintained
- All existing tests pass
- No behavioral changes
- Code is more maintainable (subjective but measurable via code review)

---

## Implementation Priority

1. **Immediate** (Already Fixed in commit 4f3d554):
   - ✅ TOCTOU path traversal vulnerability
   - ✅ macOS path boundary checking
   - ✅ Centralized sensitive directory lists
   - ✅ Job-level CI timeouts

2. **Important** (Next PR):
   - Item #1: Configurable E2E test timeouts
   - Item #2: E2E test for sensitive directory blocking

3. **Nice-to-Have** (Future PRs, when time permits):
   - Item #3: Simplify E2E tests
   - Item #4: Simplify config error handling
   - Item #5: Simplify CI workflow

---

## Related Documents

- `plans/blocking-tests-strategy.md` - Complete strategy document
- `docs/simplification-analysis.md` - Detailed simplification analysis (created by agent)
- Agent reviews:
  - feature-dev:code-reviewer (agent ID: 027604dd)
  - pr-review-toolkit:code-simplifier (agent ID: 2d9a17cb)

---

**Last Updated**: 2025-12-09
**Status**: Ready for GitHub issue creation
