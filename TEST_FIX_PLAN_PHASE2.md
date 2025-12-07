# Test Fix Plan - Phase 2

**Created**: 2025-12-07
**Branch**: `feature/eval-harness-mvp`
**PR**: https://github.com/ambient-code/agentready/pull/178

## Phase 1 Summary (COMPLETED)

✅ **27 tests fixed** across 3 commits:
- Config loading tests: 9 fixed
- CLI validation tests: 6 fixed
- Align command tests: 12 fixed

**Current Status**: 48 failed, 737 passed, 2 skipped, 4 errors

---

## Remaining Failures Breakdown

### Category 1: Learning Service Tests (7 failures)

**File**: `tests/unit/test_learning_service.py`

**Failures**:
1. `test_extract_patterns_filters_by_confidence`
2. `test_extract_patterns_with_llm_enrichment`
3. `test_extract_patterns_missing_assessment_keys`
4. `test_extract_patterns_with_old_schema_key`
5. `test_extract_patterns_empty_findings`
6. `test_extract_patterns_multiple_attribute_ids`
7. `test_extract_patterns_llm_budget_zero`

**Likely Root Cause**: LearningService API changes or mock mismatches

**Fix Strategy**:
1. Run one test with full output to see actual error
2. Check LearningService implementation for method signatures
3. Update mocks to match current API
4. Likely need to mock PatternExtractor and LLMEnricher correctly

**Commands**:
```bash
# Investigate first failure
pytest tests/unit/test_learning_service.py::TestLearningService::test_extract_patterns_filters_by_confidence -xvs --no-cov

# Read implementation
cat src/agentready/services/learning_service.py
```

**Estimated Effort**: 30-45 minutes

---

### Category 2: CSV Reporter Tests (4 errors)

**File**: `tests/unit/test_csv_reporter.py`

**Errors** (not failures):
1. `test_generate_csv_success`
2. `test_generate_tsv_success`
3. `test_csv_formula_injection_in_repo_name`
4. `test_csv_formula_injection_in_error_message`

**Likely Root Cause**: CSVReporter module doesn't exist or import path changed

**Fix Strategy**:
1. Check if CSVReporter exists: `find src/ -name "*csv*"`
2. If missing, check git history: was it removed?
3. Options:
   - If removed: Delete test file or skip tests
   - If renamed: Update import paths
   - If moved: Update module path

**Commands**:
```bash
# Check if CSV reporter exists
find src/ -name "*csv*" -o -name "*reporter*"

# Check git history
git log --all --full-history -- "*csv*"

# Run one error to see details
pytest tests/unit/test_csv_reporter.py::TestCSVReporter::test_generate_csv_success -xvs --no-cov
```

**Estimated Effort**: 15-20 minutes

---

### Category 3: Research Formatter Tests (2 failures)

**File**: `tests/unit/test_research_formatter.py`

**Failures**:
1. `test_ensures_single_newline_at_end`
2. `test_detects_invalid_format`

**Likely Root Cause**: ResearchFormatter implementation changed

**Fix Strategy**:
1. Check actual vs expected behavior
2. Update test expectations or fix implementation
3. Verify research report schema compliance

**Commands**:
```bash
# Run failing tests
pytest tests/unit/test_research_formatter.py -xvs --no-cov

# Check implementation
cat src/agentready/services/research_formatter.py
```

**Estimated Effort**: 15-20 minutes

---

### Category 4: Config Model Test (1 failure)

**File**: `tests/unit/test_models.py`

**Failure**: `test_config_invalid_weights_sum`

**Likely Root Cause**: Config validation logic changed (we modified it in Phase 1)

**Fix Strategy**:
1. Check what validation this test expects
2. Verify if validation still exists after Pydantic migration
3. Update test or restore validation if needed

**Commands**:
```bash
# Run test
pytest tests/unit/test_models.py::TestConfig::test_config_invalid_weights_sum -xvs --no-cov

# Check Config model
cat src/agentready/models/config.py
```

**Estimated Effort**: 10 minutes

---

### Category 5: Other Test Files (Still need investigation)

**Files with potential failures** (from TEST_FIX_PROGRESS.md):
- `learners/test_pattern_extractor.py` (8 failures)
- `test_cli_extract_skills.py` (8 failures)
- `test_cli_learn.py` (8 failures)
- `test_github_scanner.py` (5 failures)
- `learners/test_llm_enricher.py` (2 failures)
- `test_fixer_service.py` (1 failure)
- `test_code_sampler.py` (1 failure)
- `learners/test_skill_generator.py` (1 failure)

**Note**: These weren't in the latest test output summary, need to verify if they still exist.

**Action Required**: Run full test suite to get current breakdown

---

## Recommended Fix Order

### Quick Wins (30-45 minutes)

1. **CSV Reporter Tests** (4 errors) - 15-20 min
   - Likely simple: module missing or renamed
   - Fast to identify and fix

2. **Config Model Test** (1 failure) - 10 min
   - Single test, likely validation logic change
   - We know this code well from Phase 1

3. **Research Formatter Tests** (2 failures) - 15-20 min
   - Small surface area
   - Likely simple assertion updates

### Medium Effort (45-60 minutes)

4. **Learning Service Tests** (7 failures) - 30-45 min
   - Related to a single service
   - Likely systematic mock updates
   - Fix pattern will apply to all 7

### Investigation Required

5. **Verify remaining test files** - 15 min
   - Run full test suite
   - Update failure counts
   - Re-categorize if needed

---

## Success Criteria

**Phase 2 Goal**: Reduce failures to < 20

**Target breakdown after Phase 2**:
- CSV Reporter: 0 errors (from 4)
- Config Model: 0 failures (from 1)
- Research Formatter: 0 failures (from 2)
- Learning Service: 0 failures (from 7)

**Total improvement**: ~14 tests fixed

**Remaining for Phase 3**: ~34 tests (mostly in learners/ and CLI commands)

---

## Commands Reference

```bash
# Run full test suite with summary
source .venv/bin/activate
python -m pytest tests/unit/ --no-cov -q | tail -20

# Run specific test file
pytest tests/unit/test_csv_reporter.py -xvs --no-cov

# Check for CSV reporter
find src/ -name "*csv*" -type f

# Update progress
git add TEST_FIX_PLAN_PHASE2.md
git commit -m "docs: add Phase 2 test fix plan"
git push upstream feature/eval-harness-mvp
```

---

## Notes

- All Phase 1 work committed and pushed
- TEST_FIX_PROGRESS.md contains historical context
- This plan focuses on quick wins first
- Will create Phase 3 plan if needed after completion
