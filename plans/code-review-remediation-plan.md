# AgentReady Code Review - Detailed Remediation Plan

**Date**: 2025-11-22
**Reviewed by**: Claude Code feature-dev:code-reviewer agent
**Total Issues**: 7 (3 Critical P0, 4 Important P1)

---

## Table of Contents

1. [P0-1: Command Execution Timeout Missing](#p0-1-command-execution-timeout-missing)
2. [P0-2: Coverage Threshold Mismatch](#p0-2-coverage-threshold-mismatch)
3. [P0-3: LLM Retry Infinite Loop Risk](#p0-3-llm-retry-infinite-loop-risk)
4. [P1-1: Division by Zero Edge Case](#p1-1-division-by-zero-edge-case)
5. [P1-2: Path Traversal Defense Gap](#p1-2-path-traversal-defense-gap)
6. [P1-3: Inconsistent File I/O Patterns](#p1-3-inconsistent-file-io-patterns)
7. [P1-4: Missing API Key Sanitization](#p1-4-missing-api-key-sanitization)

---

## P0-1: Command Execution Timeout Missing

### Severity
**Critical** - DoS vulnerability, security issue

### Impact
- Malicious or buggy commands can hang indefinitely
- Blocks entire assessment process
- Resource exhaustion on CI/CD systems
- Inconsistent with project's security patterns (all other subprocess calls use timeouts)

### Location
- **File**: `src/agentready/models/fix.py`
- **Lines**: 165-172
- **Function**: `CommandFix.apply()`

### Current Code
```python
subprocess.run(
    cmd_list,
    cwd=cwd,
    check=True,
    capture_output=True,
    text=True,
    # Security: Never use shell=True - explicitly removed
)
```

### Root Cause
Direct use of `subprocess.run()` instead of the project's `safe_subprocess_run()` wrapper which enforces timeouts.

### Remediation Steps

#### Step 1: Import safe_subprocess_run
```python
# At top of fix.py (around line 10)
from ..utils.subprocess_utils import safe_subprocess_run, SUBPROCESS_TIMEOUT
```

#### Step 2: Replace subprocess.run() call
```python
# Replace lines 165-172 with:
try:
    result = safe_subprocess_run(
        cmd_list,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,  # 120 seconds default
    )

    return FixResult(
        success=True,
        message=f"Command executed successfully: {' '.join(cmd_list)}",
        details=result.stdout if result.stdout else None,
    )
except subprocess.TimeoutExpired as e:
    return FixResult(
        success=False,
        message=f"Command timed out after {SUBPROCESS_TIMEOUT}s: {' '.join(cmd_list)}",
        details=f"Timeout limit: {SUBPROCESS_TIMEOUT}s. Command may be hanging or taking too long.",
    )
except subprocess.CalledProcessError as e:
    return FixResult(
        success=False,
        message=f"Command failed with exit code {e.returncode}: {' '.join(cmd_list)}",
        details=e.stderr if e.stderr else str(e),
    )
```

#### Step 3: Add unit test for timeout behavior
```python
# In tests/unit/test_models.py or new tests/unit/test_fix.py

def test_command_fix_timeout():
    """Test that CommandFix respects subprocess timeout."""
    from agentready.models import CommandFix, Repository
    from pathlib import Path

    # Create a command that will hang
    fix = CommandFix(
        attribute_id="test",
        priority=1,
        description="Test timeout",
        command="sleep 300",  # Sleep for 5 minutes
        auto_apply=False,
    )

    repo = Repository(path=Path.cwd())
    result = fix.apply(repo)

    assert not result.success
    assert "timed out" in result.message.lower()
    assert "120" in result.details  # Should mention the timeout limit
```

### Testing
```bash
# 1. Run unit tests
pytest tests/unit/test_fix.py -v

# 2. Test with actual hanging command (manual test)
cat > /tmp/test_timeout.json <<'EOF'
{
  "command": "sleep 300",
  "description": "Test timeout handling"
}
EOF

# 3. Verify timeout triggers (should fail after 120s, not hang forever)
python -c "
from agentready.models import CommandFix, Repository
from pathlib import Path
import time

fix = CommandFix.from_dict({
    'attribute_id': 'test',
    'priority': 1,
    'description': 'Timeout test',
    'command': 'sleep 300',
    'auto_apply': False
})

repo = Repository(path=Path.cwd())
start = time.time()
result = fix.apply(repo)
duration = time.time() - start

print(f'Duration: {duration:.1f}s')
print(f'Success: {result.success}')
print(f'Message: {result.message}')
assert duration < 130, 'Should timeout around 120s'
assert not result.success
"
```

### Verification Checklist
- [ ] Import `safe_subprocess_run` added
- [ ] Direct `subprocess.run()` call removed
- [ ] Timeout exception handling added
- [ ] Unit test for timeout added
- [ ] Manual timeout test passes (completes in ~120s)
- [ ] Regular commands still work (e.g., `echo "test"`)
- [ ] Error messages are user-friendly

### References
- Project pattern: `src/agentready/utils/subprocess_utils.py` (SUBPROCESS_TIMEOUT = 120)
- Similar usage: All other subprocess calls in codebase use `safe_subprocess_run()`

---

## P0-2: Coverage Threshold Mismatch

### Severity
**Critical** - Blocks all test runs

### Impact
- `pytest` fails immediately due to coverage threshold
- Developers cannot run tests locally
- CI/CD pipeline broken
- Documentation (CLAUDE.md) contradicts configuration

### Location
- **File**: `pyproject.toml`
- **Line**: 85
- **Config**: `[tool.pytest.ini_options]`

### Current State
```toml
# pyproject.toml line 85
addopts = "-v --cov=agentready --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=90"
```

```markdown
# CLAUDE.md line 212
**Current Coverage**: 37% (focused on core logic)
```

### Root Cause
Coverage threshold set to 90% but actual coverage is 37%. Likely copied from template or aspirational goal without adjustment.

### Remediation Steps

#### Step 1: Update pytest configuration to match reality
```toml
# pyproject.toml line 85
# Option A: Match current reality (recommended)
addopts = "-v --cov=agentready --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=40"

# Option B: Remove threshold entirely until coverage improves
addopts = "-v --cov=agentready --cov-report=term-missing --cov-report=html --cov-report=xml"

# Option C: Set progressive goal (requires immediate work)
addopts = "-v --cov=agentready --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=50"
```

**Recommendation**: Use Option A (40% threshold) to allow tests to pass while establishing minimum quality bar.

#### Step 2: Update CLAUDE.md documentation
```markdown
# CLAUDE.md - Update coverage section

**Current Coverage**: 37% (focused on core logic)
**Coverage Threshold**: 40% (enforced in pytest)
**Coverage Goal**: 80% by v1.2 (see BACKLOG.md)

### Coverage Roadmap
- v1.0: 37% (current - core assessment logic)
- v1.1: 50% (add assessor tests)
- v1.2: 80% (comprehensive coverage)
```

#### Step 3: Add coverage tracking issue to BACKLOG.md
```markdown
## Testing & Quality

### Improve Test Coverage to 80%
**Priority**: P1 | **Effort**: Medium | **Version**: v1.2

Current coverage is 37%. Need comprehensive tests for:
- All 25 assessors (currently only ~10 have tests)
- Error handling paths (exception branches)
- LLM enrichment failure scenarios
- Config validation edge cases
- CLI error handling

**Acceptance Criteria**:
- [ ] Coverage ≥80% overall
- [ ] All assessors have unit tests
- [ ] All public API methods tested
- [ ] Error paths covered
- [ ] Update pytest threshold to 80%
```

#### Step 4: Create .coveragerc for better exclusions (optional)
```ini
# .coveragerc
[run]
source = src/agentready
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Testing
```bash
# 1. Verify tests pass with new threshold
pytest

# 2. Check actual coverage
pytest --cov=agentready --cov-report=term

# 3. Generate HTML report for detailed view
pytest --cov=agentready --cov-report=html
open htmlcov/index.html

# 4. Verify threshold enforcement
pytest --cov=agentready --cov-fail-under=40  # Should pass
pytest --cov=agentready --cov-fail-under=90  # Should fail
```

### Verification Checklist
- [ ] pytest runs successfully without threshold errors
- [ ] CLAUDE.md updated with accurate coverage stats
- [ ] Coverage roadmap added to documentation
- [ ] BACKLOG.md includes coverage improvement task
- [ ] Coverage reports generated successfully (HTML, XML, term)
- [ ] CI/CD pipeline updated (if applicable)

### Long-term Plan
1. **v1.1**: Increase threshold to 50%, add assessor tests
2. **v1.2**: Increase threshold to 80%, comprehensive coverage
3. **Ongoing**: Require new code to have ≥80% coverage in PR reviews

---

## P0-3: LLM Retry Infinite Loop Risk

### Severity
**Critical** - Infinite loop, resource exhaustion

### Impact
- API key revoked → retry forever → stack overflow or hang
- User cannot interrupt (no max retry parameter)
- Recursive calls consume stack space
- Production systems could hang indefinitely
- Each retry incurs API costs (if quota not completely exhausted)

### Location
- **File**: `src/agentready/learners/llm_enricher.py`
- **Lines**: 93-99
- **Function**: `LLMEnricher.enrich_skill()`

### Current Code
```python
except RateLimitError as e:
    logger.warning(f"Rate limit hit for {skill.skill_id}: {e}")
    # Exponential backoff
    retry_after = int(getattr(e, "retry_after", 60))
    logger.info(f"Retrying after {retry_after} seconds...")
    sleep(retry_after)
    return self.enrich_skill(skill, repository, finding, use_cache)
```

### Root Cause
Unbounded recursion without retry counter. Assumes rate limit errors are transient, but they could be permanent (quota exhausted, API key revoked).

### Remediation Steps

#### Step 1: Add retry parameters to function signature
```python
def enrich_skill(
    self,
    skill: DiscoveredSkill,
    repository: Repository,
    finding: Finding,
    use_cache: bool = True,
    max_retries: int = 3,
    _retry_count: int = 0,
) -> DiscoveredSkill:
    """Enrich skill with LLM-generated content.

    Args:
        skill: Skill to enrich
        repository: Repository context
        finding: Assessment finding
        use_cache: Use cached responses if available (default: True)
        max_retries: Maximum retry attempts for rate limits (default: 3)
        _retry_count: Internal retry counter (do not set manually)

    Returns:
        Enriched skill with LLM content, or original skill if enrichment fails

    Raises:
        APIError: If API call fails after all retries (non-rate-limit errors)
    """
```

#### Step 2: Update retry logic with bounds
```python
except RateLimitError as e:
    # Check if max retries exceeded
    if _retry_count >= max_retries:
        logger.error(
            f"Max retries ({max_retries}) exceeded for {skill.skill_id}. "
            f"Falling back to heuristic skill. "
            f"Check API quota: https://console.anthropic.com/settings/limits"
        )
        return skill  # Graceful fallback to heuristic

    # Calculate backoff with jitter
    retry_after = int(getattr(e, "retry_after", 60))
    jitter = random.uniform(0, min(retry_after * 0.1, 5))  # Max 5s jitter
    total_wait = retry_after + jitter

    logger.warning(
        f"Rate limit hit for {skill.skill_id} "
        f"(retry {_retry_count + 1}/{max_retries}): {e}"
    )
    logger.info(f"Retrying after {total_wait:.1f} seconds...")

    sleep(total_wait)

    return self.enrich_skill(
        skill, repository, finding, use_cache, max_retries, _retry_count + 1
    )
```

#### Step 3: Add import for random jitter
```python
# At top of llm_enricher.py (around line 5)
import random
from time import sleep
```

#### Step 4: Update CLI to expose max_retries parameter
```python
# In src/agentready/cli/learn.py

@click.option(
    "--llm-max-retries",
    type=int,
    default=3,
    help="Maximum retry attempts for LLM rate limits (default: 3)",
)
def learn(
    repository_path: str,
    output_format: str,
    enable_llm: bool,
    llm_budget: int,
    llm_no_cache: bool,
    llm_max_retries: int,  # New parameter
) -> None:
    """Extract learnings from assessment."""
    # ... existing code ...

    if enable_llm:
        enricher = LLMEnricher(api_key=api_key)
        # Pass max_retries to enrich_skill calls
```

#### Step 5: Add unit tests for retry behavior
```python
# In tests/unit/test_llm_enricher.py

def test_llm_enricher_max_retries(mocker):
    """Test that enricher respects max retry limit."""
    from agentready.learners.llm_enricher import LLMEnricher
    from anthropic import RateLimitError

    # Mock API to always return rate limit
    mock_create = mocker.patch("anthropic.Anthropic.messages.create")
    mock_create.side_effect = RateLimitError("Rate limited", retry_after=1)

    enricher = LLMEnricher(api_key="test-key")

    # Mock sleep to avoid waiting
    mocker.patch("time.sleep")

    skill = DiscoveredSkill(
        skill_id="test",
        name="Test Skill",
        description="Test",
        category="test",
        tier=1,
    )

    # Should retry 3 times then fallback
    result = enricher.enrich_skill(
        skill, repository, finding, use_cache=False, max_retries=3
    )

    # Should return original skill (fallback)
    assert result == skill
    assert mock_create.call_count == 4  # Initial + 3 retries


def test_llm_enricher_successful_retry(mocker):
    """Test that enricher succeeds after transient rate limit."""
    from agentready.learners.llm_enricher import LLMEnricher
    from anthropic import RateLimitError

    # Mock API to fail once then succeed
    mock_create = mocker.patch("anthropic.Anthropic.messages.create")
    mock_create.side_effect = [
        RateLimitError("Rate limited", retry_after=1),
        mocker.Mock(content=[mocker.Mock(text='{"instructions": ["step1"]}')])
    ]

    enricher = LLMEnricher(api_key="test-key")
    mocker.patch("time.sleep")

    skill = DiscoveredSkill(skill_id="test", name="Test", ...)
    result = enricher.enrich_skill(skill, repository, finding, use_cache=False)

    # Should succeed on second attempt
    assert mock_create.call_count == 2
    assert result.llm_enriched is True
```

### Testing
```bash
# 1. Unit tests
pytest tests/unit/test_llm_enricher.py -v

# 2. Manual test with invalid API key (should fail gracefully)
export ANTHROPIC_API_KEY="invalid-key"
agentready extract-skills . --enable-llm --llm-max-retries 2

# Expected: Retries 2 times, then falls back to heuristic

# 3. Test with valid key but small budget (normal operation)
export ANTHROPIC_API_KEY="sk-ant-..."
agentready extract-skills . --enable-llm --llm-budget 1 --llm-max-retries 3
```

### Verification Checklist
- [ ] max_retries parameter added to function signature
- [ ] Retry counter checked before recursive call
- [ ] Graceful fallback to heuristic skill on max retries
- [ ] Jitter added to prevent thundering herd
- [ ] CLI option for max_retries added
- [ ] Unit tests for retry limit added
- [ ] Unit tests for successful retry added
- [ ] Documentation updated with retry behavior
- [ ] Error messages include helpful context (API quota link)

### Best Practices Applied
1. **Exponential backoff with jitter**: Prevents thundering herd
2. **Bounded retries**: Prevents infinite loops
3. **Graceful degradation**: Falls back to heuristic on failure
4. **User control**: CLI option for retry limit
5. **Helpful errors**: Links to API quota page

---

## P1-1: Division by Zero Edge Case

### Severity
**Important** - Semantic ambiguity in scoring

### Impact
- Score of 0/100 is ambiguous (failed all tests vs. no tests configured)
- Users cannot distinguish between poor performance and inapplicable assessment
- Reports misleading when all attributes excluded via config
- No programmatic way to detect invalid scoring

### Location
- **File**: `src/agentready/services/scorer.py`
- **Lines**: 143-146
- **Function**: `calculate_weighted_score()`

### Current Code
```python
if total_weight > 0:
    normalized_score = total_score / total_weight
else:
    normalized_score = 0.0
```

### Root Cause
The function returns 0.0 both when repository fails all checks AND when no checks are applicable. Docstring acknowledges ambiguity (lines 115-120) but doesn't resolve it.

### Remediation Steps

#### Step 1: Update Assessment model to include scoring validity
```python
# In src/agentready/models/assessment.py

@dataclass
class Assessment:
    """Assessment results for a repository."""

    # ... existing fields ...

    scoring_valid: bool = True
    """Whether the score is meaningful (False if no attributes were weighted)."""

    scoring_metadata: dict[str, Any] = field(default_factory=dict)
    """Additional scoring context (total_weight, excluded_count, etc.)."""
```

#### Step 2: Update scorer to set validity flag
```python
# In src/agentready/services/scorer.py (around line 143)

def calculate_weighted_score(
    findings: list[Finding],
    config: Config | None = None,
) -> tuple[float, dict[str, Any]]:
    """Calculate weighted score and return metadata.

    Returns:
        Tuple of (normalized_score, metadata_dict)
        - normalized_score: 0-100 score
        - metadata: dict with 'valid', 'total_weight', 'excluded_count', etc.
    """
    # ... existing weight calculation ...

    metadata = {
        "total_weight": total_weight,
        "total_score": total_score,
        "findings_count": len(findings),
        "excluded_count": sum(1 for f in findings if not should_include(f)),
    }

    if total_weight > 0:
        normalized_score = total_score / total_weight
        metadata["valid"] = True
    else:
        normalized_score = 0.0
        metadata["valid"] = False
        metadata["reason"] = "No applicable attributes (all excluded or skipped)"

    return normalized_score, metadata


# Update callers to use new signature
def create_assessment(...) -> Assessment:
    score, metadata = calculate_weighted_score(findings, config)

    return Assessment(
        repository=repository,
        findings=findings,
        score=score,
        scoring_valid=metadata["valid"],
        scoring_metadata=metadata,
        # ... other fields ...
    )
```

#### Step 3: Update reports to show scoring validity
```python
# In src/agentready/reporters/html.py

def generate(self, assessment: Assessment) -> str:
    """Generate HTML report."""

    # Add scoring validity warning
    if not assessment.scoring_valid:
        metadata = assessment.scoring_metadata
        reason = metadata.get("reason", "Unknown")
        validity_warning = f"""
        <div class="alert alert-warning">
            <strong>Note:</strong> Score may not be meaningful. {reason}
            <br>
            Excluded attributes: {metadata.get("excluded_count", 0)}
            Total findings: {metadata.get("findings_count", 0)}
        </div>
        """
    else:
        validity_warning = ""

    # Pass to template
    return template.render(
        assessment=assessment,
        validity_warning=validity_warning,
        # ... other context ...
    )
```

#### Step 4: Update markdown reporter similarly
```python
# In src/agentready/reporters/markdown.py

def generate(self, assessment: Assessment) -> str:
    """Generate markdown report."""

    sections = []

    # Add validity warning if needed
    if not assessment.scoring_valid:
        metadata = assessment.scoring_metadata
        sections.append(
            f"⚠️  **Scoring Note**: Score may not be meaningful. "
            f"{metadata.get('reason', 'No applicable attributes')}. "
            f"Excluded: {metadata.get('excluded_count', 0)} attributes."
        )

    # ... rest of report ...
```

#### Step 5: Add tests for edge cases
```python
# In tests/unit/test_scorer.py

def test_scoring_invalid_when_all_excluded():
    """Test that scoring is marked invalid when all attributes excluded."""
    from agentready.services.scorer import calculate_weighted_score
    from agentready.models import Finding, Config

    # Create findings for 3 attributes
    findings = [
        Finding(attribute_id="1.1", status="pass", ...),
        Finding(attribute_id="1.2", status="pass", ...),
        Finding(attribute_id="1.3", status="pass", ...),
    ]

    # Exclude all attributes via config
    config = Config(excluded_attributes=["1.1", "1.2", "1.3"])

    score, metadata = calculate_weighted_score(findings, config)

    assert score == 0.0
    assert metadata["valid"] is False
    assert "excluded" in metadata["reason"].lower()
    assert metadata["excluded_count"] == 3


def test_scoring_valid_when_some_excluded():
    """Test that scoring is valid when only some attributes excluded."""
    findings = [
        Finding(attribute_id="1.1", status="pass", score=100, ...),
        Finding(attribute_id="1.2", status="fail", score=0, ...),
    ]

    config = Config(excluded_attributes=["1.2"])

    score, metadata = calculate_weighted_score(findings, config)

    assert score == 100.0  # Only 1.1 counted
    assert metadata["valid"] is True
    assert metadata["excluded_count"] == 1


def test_scoring_valid_zero_when_all_fail():
    """Test that 0 score is valid when tests run but all fail."""
    findings = [
        Finding(attribute_id="1.1", status="fail", score=0, ...),
        Finding(attribute_id="1.2", status="fail", score=0, ...),
    ]

    score, metadata = calculate_weighted_score(findings)

    assert score == 0.0
    assert metadata["valid"] is True  # Valid but poor performance
    assert metadata["excluded_count"] == 0
```

### Testing
```bash
# 1. Unit tests
pytest tests/unit/test_scorer.py -v

# 2. Test with excluded attributes config
cat > /tmp/exclude-all.json <<'EOF'
{
  "excluded_attributes": [
    "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7",
    "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10"
  ]
}
EOF

agentready assess . --config /tmp/exclude-all.json

# Expected: Report shows warning about invalid scoring

# 3. Check HTML report for warning
open .agentready/report-latest.html
# Should see warning banner about scoring validity
```

### Verification Checklist
- [ ] Assessment model updated with `scoring_valid` field
- [ ] Scorer returns validity metadata
- [ ] HTML report shows warning when invalid
- [ ] Markdown report shows warning when invalid
- [ ] Tests for all edge cases added (all excluded, some excluded, all fail)
- [ ] JSON report includes validity metadata
- [ ] Documentation updated with scoring validity explanation

### User-Facing Changes
- Reports now clearly distinguish "no applicable tests" from "failed all tests"
- JSON output includes `scoring_valid` and `scoring_metadata` fields
- HTML/Markdown reports show warning banners when scoring is invalid
- Programmatic users can check `assessment.scoring_valid` flag

---

## P1-2: Path Traversal Defense Gap

### Severity
**Important** - Security defense-in-depth issue

### Impact
- URL-encoded path separators (`%2f`, `%5c`) bypass validation
- Unicode lookalike characters could bypass validation
- Relies on downstream `.relative_to()` check as only real defense
- Defense-in-depth principle violated (should fail fast)

### Location
- **File**: `src/agentready/services/llm_cache.py`
- **Lines**: 104-110
- **Function**: `_get_safe_cache_path()`

### Current Code
```python
# Reject keys with path separators (/, \)
if "/" in cache_key or "\\" in cache_key:
    return None

# Reject keys with null bytes or other dangerous characters
if "\0" in cache_key or ".." in cache_key:
    return None
```

### Root Cause
Validation checks for literal `/` and `\` but doesn't decode URL-encoded variants or check for Unicode lookalikes before validation.

### Remediation Steps

#### Step 1: Add URL decoding check
```python
# In src/agentready/services/llm_cache.py (around line 100)

import urllib.parse

def _get_safe_cache_path(self, cache_key: str) -> Path | None:
    """Validate cache key and return safe path.

    Security: Prevents path traversal by validating key doesn't contain:
    - Path separators (/, \, or URL-encoded variants)
    - Null bytes or control characters
    - Relative path components (..)
    - Unicode lookalikes for path separators

    Args:
        cache_key: Cache key to validate

    Returns:
        Safe path to cache file, or None if key is invalid
    """
    # Reject empty or overly long keys
    if not cache_key or len(cache_key) > 255:
        logger.warning(f"Rejected invalid cache key length: {len(cache_key)}")
        return None

    # Reject URL-encoded content (defense against %2f, %5c, etc.)
    decoded = urllib.parse.unquote(cache_key)
    if decoded != cache_key:
        logger.warning(
            f"Rejected URL-encoded cache key. "
            f"Original: {cache_key}, Decoded: {decoded}"
        )
        return None

    # Reject path separators (/, \)
    # Note: Check after URL decode to catch encoded variants
    if "/" in cache_key or "\\" in cache_key:
        logger.warning(f"Rejected cache key with path separator: {cache_key}")
        return None

    # Reject null bytes, control characters, or relative paths
    if "\0" in cache_key or ".." in cache_key:
        logger.warning(f"Rejected cache key with dangerous characters: {cache_key}")
        return None

    # Reject Unicode lookalikes for path separators
    # U+2044: FRACTION SLASH (⁄)
    # U+2215: DIVISION SLASH (∕)
    # U+29F8: BIG SOLIDUS (⧸)
    # U+FF0F: FULLWIDTH SOLIDUS (／)
    unicode_lookalikes = ["\u2044", "\u2215", "\u29f8", "\uff0f", "\uff3c"]
    if any(char in cache_key for char in unicode_lookalikes):
        logger.warning(f"Rejected cache key with Unicode lookalike: {cache_key}")
        return None

    # Construct path
    cache_file = self.cache_dir / f"{cache_key}.json"

    # Resolve symlinks and verify path is within cache directory
    try:
        resolved = cache_file.resolve(strict=False)
    except (OSError, ValueError) as e:
        logger.warning(f"Path resolution failed for {cache_key}: {e}")
        return None

    # Final safety check: ensure resolved path is within cache dir
    try:
        resolved.relative_to(self.cache_dir.resolve())
    except ValueError:
        logger.error(
            f"Path traversal attempt detected: {cache_key} "
            f"resolved to {resolved}, outside {self.cache_dir}"
        )
        return None

    return resolved
```

#### Step 2: Add comprehensive security tests
```python
# In tests/unit/test_llm_cache.py

def test_cache_rejects_url_encoded_paths():
    """Test that URL-encoded path separators are rejected."""
    from agentready.services.llm_cache import LLMCache
    from pathlib import Path

    cache = LLMCache(cache_dir=Path("/tmp/test-cache"))

    # Test various URL-encoded attacks
    attacks = [
        "skill%2f..%2f..%2fetc%2fpasswd",  # %2f = /
        "skill%5c..%5cwindows%5csystem32",  # %5c = \
        "test%2e%2e%2fparent",  # %2e = .
    ]

    for attack in attacks:
        path = cache._get_safe_cache_path(attack)
        assert path is None, f"Should reject URL-encoded attack: {attack}"


def test_cache_rejects_unicode_lookalikes():
    """Test that Unicode lookalike characters are rejected."""
    from agentready.services.llm_cache import LLMCache

    cache = LLMCache(cache_dir=Path("/tmp/test-cache"))

    # Test Unicode lookalikes for /
    attacks = [
        "skill⁄etc⁄passwd",  # U+2044 FRACTION SLASH
        "skill∕windows∕system",  # U+2215 DIVISION SLASH
        "skill⧸parent⧸child",  # U+29F8 BIG SOLIDUS
        "skill／fullwidth／test",  # U+FF0F FULLWIDTH SOLIDUS
    ]

    for attack in attacks:
        path = cache._get_safe_cache_path(attack)
        assert path is None, f"Should reject Unicode lookalike: {attack!r}"


def test_cache_accepts_safe_keys():
    """Test that legitimate cache keys are accepted."""
    from agentready.services.llm_cache import LLMCache

    cache = LLMCache(cache_dir=Path("/tmp/test-cache"))

    safe_keys = [
        "skill-1.1-pre-commit-hooks",
        "attribute_2.3_type_annotations",
        "test-coverage-v1",
        "CLAUDE.md-documentation",
    ]

    for key in safe_keys:
        path = cache._get_safe_cache_path(key)
        assert path is not None, f"Should accept safe key: {key}"
        assert path.name == f"{key}.json"


def test_cache_path_traversal_defense_in_depth():
    """Test that even if validation fails, relative_to() catches traversal."""
    from agentready.services.llm_cache import LLMCache
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        cache_dir.mkdir()

        cache = LLMCache(cache_dir=cache_dir)

        # Even if a key somehow bypasses validation,
        # the relative_to() check should catch it
        # (This tests defense-in-depth)

        # Directly construct a malicious path
        # (simulating validation bypass)
        malicious = cache_dir / ".." / "etc" / "passwd"

        # The relative_to() check should catch this
        try:
            malicious.resolve().relative_to(cache_dir.resolve())
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
```

### Testing
```bash
# 1. Run security-focused tests
pytest tests/unit/test_llm_cache.py::test_cache_rejects_url_encoded_paths -v
pytest tests/unit/test_llm_cache.py::test_cache_rejects_unicode_lookalikes -v

# 2. Manual penetration test
python -c "
from agentready.services.llm_cache import LLMCache
from pathlib import Path

cache = LLMCache(cache_dir=Path('/tmp/test-cache'))

attacks = [
    'skill%2f..%2fetc%2fpasswd',
    'skill/../../../etc/passwd',
    'skill⁄etc⁄passwd',
]

for attack in attacks:
    result = cache._get_safe_cache_path(attack)
    print(f'{attack}: {\"BLOCKED\" if result is None else \"LEAKED\"}')
"

# Expected output: All attacks should be BLOCKED

# 3. Verify legitimate keys still work
python -c "
from agentready.services.llm_cache import LLMCache
from pathlib import Path

cache = LLMCache(cache_dir=Path('/tmp/test-cache'))

legitimate = [
    'skill-1.1-pre-commit',
    'attribute_2.3_types',
]

for key in legitimate:
    result = cache._get_safe_cache_path(key)
    print(f'{key}: {\"ALLOWED\" if result else \"BLOCKED\"}')
"

# Expected: All legitimate keys ALLOWED
```

### Verification Checklist
- [ ] URL decoding check added before validation
- [ ] Unicode lookalike characters validated
- [ ] Comprehensive security tests added
- [ ] Legitimate keys still accepted
- [ ] Error logging includes helpful context
- [ ] Documentation updated with security considerations
- [ ] Defense-in-depth maintained (relative_to still enforced)

### Security Best Practices Applied
1. **Fail fast**: Reject malicious input at earliest point
2. **Defense-in-depth**: Multiple validation layers
3. **Comprehensive coverage**: Handle URL encoding, Unicode, control chars
4. **Logging**: Security events logged for monitoring
5. **Testing**: Dedicated security test suite

---

## P1-3: Inconsistent File I/O Patterns

### Severity
**Important** - Maintainability and error handling consistency

### Impact
- Different error exceptions in different parts of codebase
- Harder to predict error behavior
- Exception handling inconsistent (some catch OSError, some don't catch UnicodeDecodeError)
- Code review burden (need to check which pattern each file uses)

### Location
Multiple files, primarily in `src/agentready/assessors/`

### Current Patterns

**Pattern A: Context manager with try-except**
```python
# documentation.py:52-54
try:
    with open(claude_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
except (FileNotFoundError, OSError):
    # Handle error
```

**Pattern B: Path.read_text() shorthand**
```python
# Used in many assessors
try:
    content = path.read_text(encoding='utf-8')
except FileNotFoundError:
    # Handle error - but what about UnicodeDecodeError?
```

### Root Cause
Mix of old-style file I/O (open + context manager) and modern Path methods (read_text). Both work, but mixing creates inconsistency.

### Remediation Steps

#### Step 1: Define standard file I/O utility functions
```python
# Create new file: src/agentready/utils/file_io.py

"""File I/O utilities with consistent error handling."""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileReadError(Exception):
    """Raised when file reading fails for any reason."""

    def __init__(self, path: Path, original_error: Exception):
        self.path = path
        self.original_error = original_error
        super().__init__(f"Failed to read {path}: {original_error}")


def read_text_file(
    path: Path,
    encoding: str = "utf-8",
    fallback_encodings: Optional[list[str]] = None,
) -> str:
    """Read text file with consistent error handling.

    Args:
        path: Path to file
        encoding: Primary encoding (default: utf-8)
        fallback_encodings: Encodings to try if primary fails

    Returns:
        File contents as string

    Raises:
        FileReadError: If file cannot be read with any encoding
    """
    if fallback_encodings is None:
        fallback_encodings = ["latin-1", "cp1252"]

    encodings_to_try = [encoding] + fallback_encodings

    for enc in encodings_to_try:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError as e:
            if enc == encodings_to_try[-1]:
                # Last encoding failed
                logger.error(f"All encodings failed for {path}")
                raise FileReadError(path, e)
            else:
                # Try next encoding
                logger.debug(f"Encoding {enc} failed for {path}, trying next")
                continue
        except (FileNotFoundError, OSError) as e:
            raise FileReadError(path, e)

    # Should never reach here
    raise FileReadError(path, Exception("Unknown error"))


def safe_read_text(path: Path, encoding: str = "utf-8") -> Optional[str]:
    """Read text file, returning None on any error (lenient version).

    Use this when file is optional or when you'll check None return.
    Use read_text_file() when file is required.

    Args:
        path: Path to file
        encoding: Text encoding

    Returns:
        File contents or None if read failed
    """
    try:
        return read_text_file(path, encoding)
    except FileReadError as e:
        logger.debug(f"Could not read {path}: {e.original_error}")
        return None


def file_exists_and_readable(path: Path) -> bool:
    """Check if file exists and is readable.

    More reliable than path.exists() for error handling.
    """
    try:
        path.read_bytes()  # Just check if readable
        return True
    except (FileNotFoundError, OSError, PermissionError):
        return False
```

#### Step 2: Refactor assessors to use standard utilities
```python
# Example: documentation.py

from ..utils.file_io import read_text_file, safe_read_text, FileReadError

class CLAUDEmdAssessor(BaseAssessor):
    def assess(self, repository: Repository) -> Finding:
        claude_md_path = repository.path / "CLAUDE.md"

        # Old pattern:
        # try:
        #     with open(claude_md_path, 'r', encoding='utf-8') as f:
        #         content = f.read()
        # except (FileNotFoundError, OSError):
        #     return Finding.create_fail(...)

        # New pattern:
        try:
            content = read_text_file(claude_md_path)
        except FileReadError as e:
            return Finding.create_fail(
                self.attribute,
                evidence={"error": str(e.original_error)},
                message=f"CLAUDE.md not found or unreadable: {e.original_error}",
            )

        # ... rest of assessment logic ...


# For optional files (like .gitignore), use safe_read_text:
class GitignoreAssessor(BaseAssessor):
    def assess(self, repository: Repository) -> Finding:
        gitignore_path = repository.path / ".gitignore"

        # Old pattern:
        # if not gitignore_path.exists():
        #     return Finding.create_fail(...)
        # content = gitignore_path.read_text()

        # New pattern:
        content = safe_read_text(gitignore_path)
        if content is None:
            return Finding.create_fail(
                self.attribute,
                message=".gitignore not found or unreadable",
            )

        # ... parse content ...
```

#### Step 3: Add tests for file I/O utilities
```python
# tests/unit/test_file_io.py

from pathlib import Path
import pytest
from agentready.utils.file_io import (
    read_text_file,
    safe_read_text,
    FileReadError,
)


def test_read_text_file_success(tmp_path):
    """Test successful file read."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")

    content = read_text_file(test_file)
    assert content == "Hello, World!"


def test_read_text_file_not_found(tmp_path):
    """Test FileReadError on missing file."""
    missing = tmp_path / "missing.txt"

    with pytest.raises(FileReadError) as exc_info:
        read_text_file(missing)

    assert exc_info.value.path == missing
    assert isinstance(exc_info.value.original_error, FileNotFoundError)


def test_read_text_file_encoding_fallback(tmp_path):
    """Test encoding fallback for non-UTF8 files."""
    test_file = tmp_path / "latin1.txt"
    # Write Latin-1 encoded content
    test_file.write_bytes("Café".encode("latin-1"))

    # Should succeed with fallback encoding
    content = read_text_file(test_file, encoding="utf-8")
    assert "Caf" in content  # Should decode something


def test_safe_read_text_returns_none_on_error(tmp_path):
    """Test safe_read_text returns None instead of raising."""
    missing = tmp_path / "missing.txt"

    result = safe_read_text(missing)
    assert result is None
```

#### Step 4: Create migration guide for developers
```markdown
# File I/O Pattern Migration Guide

## When to Use Each Function

### read_text_file(path)
Use when the file is REQUIRED for assessment:
- CLAUDE.md (must exist)
- pyproject.toml (must be parseable)
- Required config files

**Behavior**: Raises FileReadError if file missing or unreadable

**Example**:
```python
try:
    content = read_text_file(required_path)
except FileReadError:
    return Finding.create_fail(...)
```

### safe_read_text(path)
Use when the file is OPTIONAL:
- .gitignore (nice to have)
- Optional config files
- Documentation files (README variants)

**Behavior**: Returns None if file missing or unreadable

**Example**:
```python
content = safe_read_text(optional_path)
if content is None:
    return Finding.create_fail(...)  # or skip
```

## Migration Steps

1. Replace `open()` context managers:
```python
# Before
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
except (FileNotFoundError, OSError):
    # handle error

# After
try:
    content = read_text_file(path)
except FileReadError:
    # handle error
```

2. Replace `Path.read_text()` direct calls:
```python
# Before
try:
    content = path.read_text(encoding='utf-8')
except FileNotFoundError:
    # handle error

# After (required file)
try:
    content = read_text_file(path)
except FileReadError:
    # handle error

# After (optional file)
content = safe_read_text(path)
if content is None:
    # handle error
```

3. Replace existence checks:
```python
# Before
if not path.exists():
    return Finding.create_fail(...)
content = path.read_text()

# After
content = safe_read_text(path)
if content is None:
    return Finding.create_fail(...)
```
```

### Testing
```bash
# 1. Run file I/O utility tests
pytest tests/unit/test_file_io.py -v

# 2. Run full test suite to ensure no regressions
pytest

# 3. Test with actual repository
agentready assess . --verbose

# 4. Test with repository with weird encodings
# (Create test repo with Latin-1 README)
```

### Verification Checklist
- [ ] File I/O utilities created in utils/file_io.py
- [ ] Comprehensive tests for utilities added
- [ ] Migration guide documented
- [ ] At least 3 assessors refactored to use new pattern
- [ ] All tests pass after refactoring
- [ ] No regressions in assessment behavior
- [ ] Documentation updated

### Rollout Plan
1. **Phase 1**: Create utilities and tests (this PR)
2. **Phase 2**: Migrate documentation assessors (CLAUDEmd, README)
3. **Phase 3**: Migrate structure assessors (Gitignore, StandardLayout)
4. **Phase 4**: Migrate remaining assessors
5. **Phase 5**: Remove old patterns, enforce in code review

---

## P1-4: Missing API Key Sanitization

### Severity
**Important** - Potential secret leakage in logs

### Impact
- If Anthropic error messages contain API key fragments, they could leak to logs
- Error truncation doesn't remove sensitive data, just limits length
- GDPR/compliance risk if logs are aggregated or shipped
- Difficult to audit/detect leakage after the fact

### Location
- **File**: `src/agentready/learners/llm_enricher.py`
- **Lines**: 102-106
- **Function**: `enrich_skill()` error handler

### Current Code
```python
except APIError as e:
    # Security: Sanitize error message to prevent API key exposure
    error_msg = str(e)
    # Anthropic errors shouldn't contain keys, but sanitize to be safe
    safe_error = error_msg if len(error_msg) < 200 else error_msg[:200]
    logger.error(f"Anthropic API error enriching {skill.skill_id}: {safe_error}")
    return skill
```

### Root Cause
Comment says "sanitize" but implementation only truncates. No actual scrubbing of API key patterns (`sk-ant-*`).

### Remediation Steps

#### Step 1: Create security utility for secret sanitization
```python
# Create new file: src/agentready/utils/security.py

"""Security utilities for sanitizing sensitive data."""

import re
from typing import Any

# Regex patterns for sensitive data
API_KEY_PATTERNS = [
    r"sk-ant-[a-zA-Z0-9-]{10,}",  # Anthropic keys
    r"sk-[a-zA-Z0-9]{32,}",  # OpenAI-style keys
    r"ghp_[a-zA-Z0-9]{36}",  # GitHub PATs
    r"gho_[a-zA-Z0-9]{36}",  # GitHub OAuth tokens
]

# Compile patterns for performance
COMPILED_PATTERNS = [re.compile(pattern) for pattern in API_KEY_PATTERNS]


def sanitize_api_key(text: str, replacement: str = "<API_KEY_REDACTED>") -> str:
    """Remove API keys from text using pattern matching.

    Args:
        text: Text potentially containing API keys
        replacement: String to replace keys with

    Returns:
        Text with API keys replaced

    Examples:
        >>> sanitize_api_key("Error with key sk-ant-abc123")
        'Error with key <API_KEY_REDACTED>'
    """
    result = text
    for pattern in COMPILED_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_error_message(
    error: Exception | str,
    max_length: int = 200,
    redact_keys: bool = True,
) -> str:
    """Sanitize error message for safe logging.

    Combines API key redaction with length truncation.

    Args:
        error: Exception or error string
        max_length: Maximum length of output (default: 200)
        redact_keys: Whether to redact API keys (default: True)

    Returns:
        Sanitized error message safe for logging
    """
    # Convert to string
    if isinstance(error, Exception):
        error_str = str(error)
    else:
        error_str = error

    # Redact API keys first
    if redact_keys:
        error_str = sanitize_api_key(error_str)

    # Truncate if too long
    if len(error_str) > max_length:
        error_str = error_str[:max_length] + "... (truncated)"

    return error_str


def sanitize_dict(
    data: dict[str, Any],
    sensitive_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Recursively sanitize dictionary for logging.

    Redacts values for sensitive keys (api_key, password, token, etc.)
    and sanitizes string values for API key patterns.

    Args:
        data: Dictionary to sanitize
        sensitive_keys: Additional keys to redact (beyond defaults)

    Returns:
        Sanitized copy of dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = []

    # Default sensitive keys
    default_sensitive = ["api_key", "apikey", "password", "token", "secret"]
    all_sensitive = set(default_sensitive + sensitive_keys)

    sanitized = {}
    for key, value in data.items():
        # Redact if key is sensitive
        if key.lower() in all_sensitive:
            sanitized[key] = "<REDACTED>"

        # Recursively sanitize nested dicts
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, sensitive_keys)

        # Sanitize string values
        elif isinstance(value, str):
            sanitized[key] = sanitize_api_key(value)

        # Keep other values as-is
        else:
            sanitized[key] = value

    return sanitized
```

#### Step 2: Update LLM enricher to use sanitization
```python
# In src/agentready/learners/llm_enricher.py

from ..utils.security import sanitize_error_message

class LLMEnricher:
    def enrich_skill(...) -> DiscoveredSkill:
        # ... existing code ...

        except APIError as e:
            # Sanitize error message (redact keys + truncate)
            safe_error = sanitize_error_message(e, max_length=200)
            logger.error(
                f"Anthropic API error enriching {skill.skill_id}: {safe_error}"
            )
            return skill

        except RateLimitError as e:
            # Also sanitize rate limit errors
            safe_error = sanitize_error_message(e, max_length=200)
            logger.warning(
                f"Rate limit hit for {skill.skill_id} "
                f"(retry {_retry_count + 1}/{max_retries}): {safe_error}"
            )
            # ... retry logic ...
```

#### Step 3: Add security tests
```python
# tests/unit/test_security.py

from agentready.utils.security import (
    sanitize_api_key,
    sanitize_error_message,
    sanitize_dict,
)


def test_sanitize_anthropic_key():
    """Test Anthropic API key redaction."""
    text = "Error: Invalid key sk-ant-abc123xyz456"
    result = sanitize_api_key(text)

    assert "sk-ant-" not in result
    assert "abc123xyz456" not in result
    assert "<API_KEY_REDACTED>" in result


def test_sanitize_multiple_keys():
    """Test multiple API key patterns in one string."""
    text = "Keys: sk-ant-111 and ghp_222222222222222222222222222222222222"
    result = sanitize_api_key(text)

    assert "sk-ant-" not in result
    assert "ghp_" not in result
    assert result.count("<API_KEY_REDACTED>") == 2


def test_sanitize_error_message_combines_redaction_and_truncation():
    """Test that error sanitization redacts AND truncates."""
    long_error = f"Error with key sk-ant-secret123: {'x' * 300}"
    result = sanitize_error_message(long_error, max_length=100)

    assert "sk-ant-" not in result
    assert len(result) <= 120  # 100 + "... (truncated)"
    assert "<API_KEY_REDACTED>" in result


def test_sanitize_dict_redacts_sensitive_keys():
    """Test dictionary sanitization redacts sensitive keys."""
    data = {
        "api_key": "sk-ant-secret",
        "username": "alice",
        "password": "hunter2",
        "nested": {
            "token": "ghp_secret",
            "safe_value": "visible",
        },
    }

    result = sanitize_dict(data)

    assert result["api_key"] == "<REDACTED>"
    assert result["password"] == "<REDACTED>"
    assert result["username"] == "alice"
    assert result["nested"]["token"] == "<REDACTED>"
    assert result["nested"]["safe_value"] == "visible"


def test_sanitize_dict_handles_api_keys_in_values():
    """Test that API keys in string values are redacted."""
    data = {
        "error_message": "Failed with key sk-ant-abc123",
        "user": "alice",
    }

    result = sanitize_dict(data)

    assert "sk-ant-" not in result["error_message"]
    assert "<API_KEY_REDACTED>" in result["error_message"]
    assert result["user"] == "alice"


def test_sanitize_preserves_safe_content():
    """Test that sanitization doesn't over-redact safe content."""
    safe_texts = [
        "This is a normal error message",
        "File not found: /path/to/file",
        "Rate limit exceeded, retry after 60s",
    ]

    for text in safe_texts:
        result = sanitize_api_key(text)
        assert result == text, f"Should not modify safe text: {text}"
```

#### Step 4: Audit codebase for other logging of sensitive data
```bash
# Search for other places where error messages are logged
rg "logger\.(error|warning|info).*\bstr\(e\)" --type py

# Search for API key usage in logging
rg "logger.*api.*key" --type py -i

# Search for direct exception logging
rg "logger.*\{e\}" --type py
```

#### Step 5: Add pre-commit hook for secret detection (optional)
```yaml
# .pre-commit-config.yaml (create if doesn't exist)

repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json
```

### Testing
```bash
# 1. Run security tests
pytest tests/unit/test_security.py -v

# 2. Test API key redaction manually
python -c "
from agentready.utils.security import sanitize_api_key

test_cases = [
    'Error: sk-ant-abc123def456',
    'Multiple keys: sk-ant-111 and sk-ant-222',
    'GitHub token: ghp_abcdefghijklmnopqrstuvwxyz123456',
    'Safe message with no keys',
]

for test in test_cases:
    result = sanitize_api_key(test)
    print(f'Input:  {test}')
    print(f'Output: {result}')
    print()
"

# 3. Test with actual LLM enricher
export ANTHROPIC_API_KEY="invalid-key-sk-ant-test123"
agentready extract-skills . --enable-llm --llm-budget 1

# Check logs - should see <API_KEY_REDACTED> not actual key

# 4. Audit codebase for other sensitive logging
rg "logger\.(error|warning).*str\(e\)" --type py
```

### Verification Checklist
- [ ] Security utility module created (utils/security.py)
- [ ] Comprehensive tests for all sanitization functions
- [ ] LLM enricher updated to use sanitization
- [ ] Codebase audited for other sensitive logging
- [ ] All API key patterns tested (Anthropic, GitHub, etc.)
- [ ] Performance tested (regex compilation cached)
- [ ] Documentation updated with security best practices
- [ ] Optional: pre-commit hook for secret detection added

### Security Best Practices Applied
1. **Defense-in-depth**: Redact first, then truncate
2. **Pattern matching**: Use regex to catch multiple key formats
3. **Comprehensive**: Handle exceptions, strings, and dictionaries
4. **Performance**: Compile regex patterns once
5. **Testing**: Dedicated security test suite
6. **Auditing**: Search codebase for other sensitive logging

---

## Summary & Prioritization

### Immediate Action Items (P0 - Block Release)

1. **Fix CommandFix timeout** - 30 minutes
   - Add timeout parameter
   - Add exception handling
   - Add unit test

2. **Fix coverage threshold** - 15 minutes
   - Update pyproject.toml
   - Update CLAUDE.md
   - Add roadmap to BACKLOG.md

3. **Fix LLM retry loop** - 45 minutes
   - Add max_retries parameter
   - Update retry logic
   - Add retry tests

**Total P0 effort**: ~1.5 hours

### Next Sprint Items (P1 - Important)

4. **Fix scorer ambiguity** - 2 hours
   - Update Assessment model
   - Update scorer logic
   - Update all reporters
   - Add tests

5. **Strengthen path validation** - 1.5 hours
   - Add URL decoding check
   - Add Unicode lookalike check
   - Add security tests

6. **Standardize file I/O** - 4 hours
   - Create utilities
   - Migrate assessors (phased)
   - Add tests

7. **Add API key sanitization** - 2 hours
   - Create security utilities
   - Update LLM enricher
   - Audit codebase
   - Add tests

**Total P1 effort**: ~9.5 hours

### Total Remediation Effort
**~11 hours** (1.5 days of focused work)

---

## Testing Strategy

### Unit Tests
Each fix includes dedicated unit tests covering:
- Happy path
- Error conditions
- Edge cases
- Security scenarios

### Integration Tests
- Full assessment with timeout scenarios
- LLM enrichment with rate limiting
- File I/O with various encodings
- End-to-end report generation

### Security Testing
- Penetration testing for path traversal
- API key leakage detection
- Malicious input handling

### Regression Testing
```bash
# Full test suite before any changes
pytest --cov=agentready > baseline.txt

# Full test suite after each fix
pytest --cov=agentready > after_fix_N.txt

# Compare coverage (should not decrease)
diff baseline.txt after_fix_N.txt
```

---

## Documentation Updates

Each remediation includes:
- [ ] Code comments explaining security considerations
- [ ] Docstrings for new functions
- [ ] CLAUDE.md updates (if applicable)
- [ ] Migration guides (for P1-3)
- [ ] Security best practices documentation

---

## Success Criteria

### P0 Fixes Complete When:
- [ ] All pytest runs pass without threshold errors
- [ ] CommandFix has timeout and passes security audit
- [ ] LLM enricher respects max_retries and falls back gracefully
- [ ] No infinite loops possible in codebase

### P1 Fixes Complete When:
- [ ] Scorer clearly distinguishes invalid vs. poor scores
- [ ] Path validation blocks all known traversal techniques
- [ ] File I/O is consistent across all assessors
- [ ] No API keys can leak through error logging

### Overall Success:
- [ ] All tests pass
- [ ] Coverage ≥40% (matches threshold)
- [ ] No security vulnerabilities in audit
- [ ] Code review checklist clean
- [ ] Documentation complete

---

**Created**: 2025-11-22
**Author**: Claude Code feature-dev:code-reviewer agent
**AgentReady Version**: 1.23.0
**Next Steps**: Convert to GitHub issues → Prioritize → Execute
