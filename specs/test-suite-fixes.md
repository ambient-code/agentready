# Test Suite Fixes - Cold Start Prompt

## Context

After merging PR #146 (Leaderboard feature), the CI shows 71 test failures. These are **pre-existing failures** unrelated to the leaderboard implementation, but they need to be fixed to maintain code quality and CI reliability.

## Test Failure Categories

### 1. Config Validation Tests (7 failures)
**Files**: `tests/unit/cli/test_main.py::TestConfigLoading`

**Issues**:
- `test_load_config_not_dict` - TypeError with Config() constructor
- `test_load_config_unknown_keys` - Not raising expected ValueError
- `test_load_config_invalid_weights_type` - SystemExit instead of validation
- `test_load_config_invalid_weight_value` - SystemExit instead of validation
- `test_load_config_invalid_excluded_attributes` - SystemExit instead of validation
- `test_load_config_sensitive_output_dir` - SystemExit instead of validation
- `test_load_config_invalid_report_theme` - SystemExit instead of validation

**Root Cause**: Config validation logic moved to Click callback validators, but tests expect model-level validation

**Fix Strategy**:
- Update tests to expect Click validation errors (SystemExit)
- Or add validation to Config model `__post_init__`
- Ensure consistency between CLI and model validation

### 2. Assessment Fixture Validation (15+ failures)
**Files**: Multiple test files creating mock Assessment objects

**Issues**:
- `ValueError: Findings count (0) must equal attributes total (1)`
- Mock assessments created without findings
- New validation added in `Assessment.validate()` enforces findings count

**Root Cause**: Assessment model now validates that `len(findings) == attributes_total`

**Fix Strategy**:
- Update all test fixtures to include proper findings array
- Or create a test-only Assessment factory that bypasses validation
- Example pattern:
```python
# Create valid mock finding
finding = Finding.create_pass(
    attribute=mock_attribute,
    evidence=["Test evidence"]
)

# Include in assessment
assessment = Assessment(
    repository=mock_repo,
    findings=[finding],
    attributes_total=1,
    # ...
)
```

### 3. CLI Align Command Tests (12 failures)
**Files**: `tests/unit/test_cli_align.py`

**Issue**: `AttributeError: <module 'agentready.cli.align'> does not have the attribute 'LanguageDetector'`

**Root Cause**: Tests trying to mock `align.LanguageDetector` but it's imported from `services.language_detector`

**Fix Strategy**:
- Update mocks to patch correct import path: `@patch('agentready.services.language_detector.LanguageDetector')`
- Or patch at usage site: `@patch('agentready.cli.align.LanguageDetector')` after ensuring import is at module level

### 4. Learning Service Tests (9 failures)
**Files**: `tests/unit/test_learning_service.py`

**Issue**: `ValueError: Not a git repository: /tmp/...`

**Root Cause**: LearningService expects git repository but test fixtures use plain temp directories

**Fix Strategy**:
- Initialize git repo in test fixtures:
```python
@pytest.fixture
def mock_repo(tmp_path):
    # Create .git directory
    (tmp_path / ".git").mkdir()
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    return tmp_path
```

### 5. Pattern Extractor Tests (8 failures)
**Files**: `tests/unit/learners/test_pattern_extractor.py`

**Issue**: `AttributeError: 'Attribute' object has no attribute 'attribute_id'`

**Root Cause**: Attribute model uses `id` not `attribute_id`, but pattern extractor expects old field name

**Fix Strategy**:
- Update PatternExtractor to use `attribute.id` instead of `attribute.attribute_id`
- Check all code for this pattern

### 6. GitHub Scanner Tests (5 failures)
**Files**: `tests/unit/test_github_scanner.py`

**Issue**: `AssertionError: assert 100 == 2` (expected 2 repos, got 100)

**Root Cause**: Mock pagination logic returning repos indefinitely (hitting max_repos limit)

**Fix Strategy**:
- Fix mock to properly simulate pagination exhaustion
- Ensure `side_effect` returns empty list after N calls
```python
mock_paginated.side_effect = [
    [MockRepo("repo1"), MockRepo("repo2")],  # First page
    []  # No more pages
]
```

### 7. Extract/Learn CLI Tests (18 failures)
**Files**: `tests/unit/test_cli_extract_skills.py`, `tests/unit/test_cli_learn.py`

**Issues**:
- `.skills-proposals` directory not created
- No JSON files generated
- Commands exiting with code 1

**Root Cause**: Commands expect valid assessment file in `.agentready/assessment-latest.json`

**Fix Strategy**:
- Create proper assessment fixtures in test setup
- Mock `LearningService` to avoid file I/O
- Use Click's `isolated_filesystem()` for temporary directories

### 8. LLM Enricher Tests (2 failures)
**Files**: `tests/unit/learners/test_llm_enricher.py`

**Issue**: `TypeError: APIStatusError.__init__() missing 2 required keyword-only arguments: 'response' and 'body'`

**Root Cause**: Anthropic SDK updated API error signatures

**Fix Strategy**:
- Update mock errors to match new Anthropic SDK signatures
```python
from anthropic import APIStatusError, APIError
# Update to include required params
mock_error = APIStatusError(
    message="Rate limited",
    response=mock_response,
    body={}
)
```

### 9. Other Model/Reporter Tests (5 failures)
**Files**: Various

**Issues**:
- CSV reporter validation errors
- Research formatter newline handling
- Skill generator string formatting

**Fix Strategy**: Address individually based on specific failure

## Implementation Plan

### Phase 1: Quick Wins (Low-hanging fruit)
1. Fix import path mocks (Align command tests)
2. Fix Anthropic SDK error signatures (LLM enricher)
3. Fix attribute.id vs attribute.attribute_id (Pattern extractor)
4. Fix GitHub scanner pagination mocks

### Phase 2: Fixture Updates (Medium effort)
1. Create reusable test fixture factories
2. Add git initialization to repo fixtures
3. Update assessment fixtures to include findings
4. Add proper CLI test isolation

### Phase 3: Config Validation (Requires design decision)
1. Decide: Model validation vs CLI validation
2. Update Config model or test expectations
3. Document validation strategy

## Testing Strategy

Run tests in isolation to verify fixes:
```bash
# Test specific categories
pytest tests/unit/test_cli_align.py -v
pytest tests/unit/learners/test_pattern_extractor.py -v
pytest tests/unit/test_github_scanner.py -v

# Full suite
pytest tests/ --no-cov -q
```

## Success Criteria

- All 71 failing tests pass
- No new test failures introduced
- Coverage maintained or improved
- Tests run in <2 minutes

## Files to Modify

1. `tests/unit/cli/test_main.py` - Config validation expectations
2. `tests/unit/test_cli_align.py` - Import path mocks
3. `tests/unit/learners/test_pattern_extractor.py` - Attribute field names
4. `tests/unit/test_github_scanner.py` - Pagination mocks
5. `tests/unit/test_learning_service.py` - Git repo fixtures
6. `tests/unit/test_cli_extract_skills.py` - Assessment fixtures
7. `tests/unit/test_cli_learn.py` - Assessment fixtures
8. `tests/unit/learners/test_llm_enricher.py` - Anthropic SDK errors
9. `tests/conftest.py` - Add shared fixtures (if needed)

## Notes

- These are **pre-existing failures**, not regressions from leaderboard PR
- Leaderboard-specific tests (metadata, reporters) are all passing
- Fix tests incrementally, commit after each category
- Use conventional commits: `test: fix config validation test expectations`
