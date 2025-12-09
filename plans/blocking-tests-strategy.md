# Blocking Tests Strategy for AgentReady

**Created**: 2025-12-09
**Purpose**: Define reliable, fast tests that must pass before merging PRs

---

## Problem Statement

Current test suite has flakiness issues:
- 23 tests fail on macOS due to platform-specific paths
- Mock-heavy tests are brittle and hard to maintain
- No clear separation between critical and nice-to-have tests
- 90% coverage requirement blocks all PRs even for minor doc changes

## Blocking Test Strategy

### Tier 1: Critical Path Tests (Must Pass - CI Blocker)

These tests cover the primary user journeys and must always pass:

#### 1. Core Assessment Flow
**File**: `tests/e2e/test_critical_paths.py` (new)

```python
def test_assess_self_repository():
    """E2E test: Assess AgentReady repository itself."""
    # Run assessment on current repo
    result = subprocess.run(
        ["agentready", "assess", "."],
        capture_output=True,
        text=True
    )

    # Verify success
    assert result.returncode == 0
    assert "Assessment complete" in result.stdout
    assert "Score:" in result.stdout

    # Verify output files exist
    assert Path(".agentready/assessment-latest.json").exists()
    assert Path(".agentready/report-latest.html").exists()
    assert Path(".agentready/report-latest.md").exists()


def test_assess_generates_valid_json():
    """E2E test: JSON output is valid and complete."""
    result = subprocess.run(
        ["agentready", "assess", "."],
        capture_output=True,
        text=True
    )

    # Load and validate JSON
    with open(".agentready/assessment-latest.json") as f:
        data = json.load(f)

    # Verify required fields
    assert "overall_score" in data
    assert "certification_level" in data
    assert "findings" in data
    assert len(data["findings"]) > 0
```

#### 2. CLI Interface Tests
**File**: `tests/unit/cli/test_main.py` (existing - keep all 41 tests)

All existing CLI tests are already reliable and should remain blocking:
- Command parsing ✅
- Config loading ✅
- Error handling ✅
- Path validation ✅

#### 3. Core Models
**File**: `tests/unit/test_models.py` (existing)

Basic data model tests:
- Assessment creation
- Finding status values
- Repository metadata
- JSON serialization

### Tier 2: Important Tests (Should Pass - Warning on Fail)

These tests are important but may have platform-specific behavior:

#### 1. Platform-Specific Validations
**File**: `tests/unit/test_cli_validation.py` (existing)

Mark platform-specific tests with skip decorators:

```python
@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Sensitive dir paths are Linux-specific"
)
def test_warns_on_sensitive_directories(sensitive_path):
    """Test sensitive directory warnings (Linux only)."""
    ...
```

#### 2. Reporter Tests
**File**: `tests/unit/reporters/test_*.py` (existing)

HTML/Markdown generation tests - important but not critical path.

### Tier 3: Development Tests (Optional - Coverage Only)

These tests help during development but don't block merges:

- Stub assessor tests
- LLM enrichment tests (require API keys)
- Experimental feature tests

## CI/CD Implementation

### GitHub Actions Workflow Changes

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [pull_request, push]

jobs:
  critical-tests:
    name: Critical Path Tests (Blocking)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          source .venv/bin/activate
          uv pip install -e .
          uv pip install pytest

      - name: Run Tier 1 critical tests
        run: |
          source .venv/bin/activate
          pytest tests/e2e/test_critical_paths.py -v
          pytest tests/unit/cli/test_main.py -v
          pytest tests/unit/test_models.py -v

      - name: Fail PR if critical tests fail
        if: failure()
        run: exit 1

  full-test-suite:
    name: Full Test Suite (Warning)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          source .venv/bin/activate
          uv pip install -e .
          uv pip install pytest pytest-cov

      - name: Run all tests with coverage
        run: |
          source .venv/bin/activate
          pytest tests/unit/ --cov=src/agentready --cov-report=html
        continue-on-error: true  # Don't block on failures

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/

  platform-tests:
    name: Platform Tests (macOS)
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          source .venv/bin/activate
          uv pip install -e .
          uv pip install pytest

      - name: Run platform-specific tests
        run: |
          source .venv/bin/activate
          pytest tests/unit/cli/test_main.py -v
        continue-on-error: true  # macOS tests are informational
```

### Branch Protection Rules

Configure GitHub repository settings:

**Required Status Checks**:
- ✅ `critical-tests` - Must pass
- ⚠️ `full-test-suite` - Warning only
- ⚠️ `platform-tests` - Informational

**Merge Requirements**:
- Require status checks to pass: `critical-tests` only
- Require branches to be up to date: Yes
- Require conversation resolution: Yes

## Test Reliability Guidelines

### 1. Avoid Platform-Specific Paths

❌ **Bad**:
```python
def test_sensitive_dir():
    result = runner.invoke(cli, ["assess", "/etc"])
    assert "Warning" in result.output
```

✅ **Good**:
```python
@pytest.mark.skipif(not Path("/etc").exists(), reason="Platform specific")
def test_sensitive_dir():
    result = runner.invoke(cli, ["assess", "/etc"])
    assert "Warning" in result.output
```

### 2. Use Temp Directories for File Tests

❌ **Bad**:
```python
def test_writes_file():
    Path("output.json").write_text("{}")
    # Leaves files behind, conflicts with parallel tests
```

✅ **Good**:
```python
def test_writes_file(tmp_path):
    output_file = tmp_path / "output.json"
    output_file.write_text("{}")
    assert output_file.exists()
```

### 3. Mock External Dependencies

❌ **Bad**:
```python
def test_llm_enrichment():
    # Makes real API call - slow, requires key, costs money
    result = enrich_skill(skill, api_key=os.environ["ANTHROPIC_API_KEY"])
```

✅ **Good**:
```python
def test_llm_enrichment(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = mock_response
    result = enrich_skill(skill)
```

### 4. Test Behavior, Not Implementation

❌ **Bad**:
```python
def test_internal_method():
    scanner = Scanner(repo)
    # Testing private method
    assert scanner._validate_config(config) == True
```

✅ **Good**:
```python
def test_scanner_with_valid_config():
    scanner = Scanner(repo, config)
    assessment = scanner.scan()
    # Testing public behavior
    assert assessment.overall_score > 0
```

## Coverage Strategy

### Current: 90% coverage required globally
**Problem**: Blocks all PRs, even trivial ones

### Proposed: Differentiated coverage requirements

1. **Critical Path Code**: 100% coverage required
   - `src/agentready/cli/main.py`
   - `src/agentready/services/scanner.py`
   - `src/agentready/models/*.py`

2. **Core Logic**: 80% coverage required
   - `src/agentready/assessors/*.py`
   - `src/agentready/services/*.py`

3. **Optional Features**: 50% coverage acceptable
   - `src/agentready/learners/*.py` (LLM enrichment)
   - `src/agentready/services/bootstrap.py` (experimental)

### Implementation

Use `pytest-cov` with path-specific coverage:

```bash
# Critical path - must be 100%
pytest tests/e2e/ tests/unit/cli/ tests/unit/test_models.py \
  --cov=src/agentready/cli \
  --cov=src/agentready/models \
  --cov=src/agentready/services/scanner.py \
  --cov-fail-under=100

# Core logic - must be 80%
pytest tests/unit/ \
  --cov=src/agentready/assessors \
  --cov=src/agentready/services \
  --cov-fail-under=80
```

## Migration Plan

### Phase 1: Implement Critical Tests (Week 1)
- [ ] Create `tests/e2e/test_critical_paths.py`
- [ ] Verify all 41 CLI tests pass reliably
- [ ] Update CI workflow with tiered jobs

### Phase 2: Platform-Specific Fixes (Week 2)
- [ ] Add platform skip markers to flaky tests
- [ ] Run tests on Linux/macOS to verify
- [ ] Document platform requirements in test docstrings

### Phase 3: Coverage Adjustment (Week 3)
- [ ] Configure differentiated coverage requirements
- [ ] Update `pyproject.toml` coverage settings
- [ ] Remove global 90% requirement

### Phase 4: Branch Protection (Week 4)
- [ ] Update GitHub branch protection rules
- [ ] Require only `critical-tests` job
- [ ] Make other jobs informational

## Success Metrics

After implementation, we should see:

1. **Zero false positives**: Critical tests never fail spuriously
2. **Fast feedback**: Critical tests run in <2 minutes
3. **Clear failures**: When tests fail, root cause is obvious
4. **No platform issues**: Tests pass on all supported platforms
5. **Higher PR velocity**: Trivial PRs don't get blocked by flaky tests

## Rollback Plan

If blocking tests cause issues:

1. Temporarily disable branch protection
2. Run full test suite manually before merge
3. Fix identified issues
4. Re-enable branch protection

## Questions for Review

1. Should we require 100% coverage on critical path or 80%?
2. Should macOS tests be blocking or informational?
3. Should we auto-skip platform-specific tests or require manual markers?
4. What's the acceptable runtime for critical tests? (2 min? 5 min?)

---

**Next Steps**: Review this strategy, then implement Phase 1 (critical tests + CI workflow).
