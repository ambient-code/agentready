# Follow-up Issues from Score Analysis (Issue #121)

These issues represent the prioritized remediation plan from the agentready score analysis.

## High-Impact Assessor Implementations (P1)

### Issue 1: Implement One-Command Setup Assessor

**Priority**: P1 (High-Impact, Easy Win)
**Impact**: +3 points (Tier 2, 3% weight)
**Effort**: Medium
**Labels**: `enhancement`, `assessor`, `tier-2`

**Description**:

Implement the `OneCommandSetupAssessor` to replace the current stub. This project already has one-command setup (`uv pip install -e .`), so implementing this assessor would immediately add +3 points to the score.

**Acceptance Criteria**:
- Check for setup.py, pyproject.toml, package.json, Cargo.toml, Makefile
- Parse README for setup instructions (look for "Quick Start", "Installation", "Setup" sections)
- Verify single commands like: `pip install -e .`, `npm install`, `cargo build`, `make install`
- Return partial score if multi-step setup exists
- Provide language-specific remediation

**Implementation Pattern**:
```python
# Check manifest files
has_pyproject = (repo.path / "pyproject.toml").exists()
has_package_json = (repo.path / "package.json").exists()

# Parse README for setup commands
readme_patterns = [
    r'pip install -e \.?',
    r'npm install',
    r'cargo build',
]
```

**References**:
- `src/agentready/assessors/stub_assessors.py:272-278`
- Pattern: `CLAUDEmdAssessor` in `assessors/documentation.py`

---

### Issue 2: Implement Inline Documentation Assessor

**Priority**: P1 (High-Impact)
**Impact**: +3 points (Tier 2, 3% weight)
**Effort**: Medium
**Labels**: `enhancement`, `assessor`, `tier-2`

**Description**:

Implement assessor to check for inline documentation (docstrings). Given that agentready has 96% type annotation coverage, it likely has good docstring coverage too.

**Acceptance Criteria**:
- Count docstrings in Python files (functions, classes, modules)
- Calculate percentage of documented entities
- Use `pydocstyle` or similar if available
- Pass if ≥80% of public entities have docstrings
- Provide remediation with tools and examples

**Implementation Notes**:
```python
import ast

def count_docstrings(file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())

    total = 0
    documented = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            total += 1
            if ast.get_docstring(node):
                documented += 1

    return documented, total
```

**Scoring**:
- 100 points: ≥80% documented
- Proportional: 50-79% documented
- 0 points: <50% documented

---

### Issue 3: Implement File Size Limits Assessor

**Priority**: P1 (Easy Win)
**Impact**: +3 points (Tier 2, 3% weight)
**Effort**: Low
**Labels**: `enhancement`, `assessor`, `tier-2`

**Description**:

Implement assessor to check for files >500 lines (context window optimization). This is a simple file scanner.

**Acceptance Criteria**:
- Scan source files (exclude tests, vendor, node_modules)
- Count lines per file
- Flag files >500 lines
- Provide list of offending files in evidence
- Suggest refactoring strategies in remediation

**Implementation**:
```python
def assess(self, repository: Repository) -> Finding:
    large_files = []
    threshold = 500

    for root, dirs, files in os.walk(repository.path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file.endswith(SOURCE_EXTENSIONS):
                path = Path(root) / file
                line_count = sum(1 for _ in open(path))
                if line_count > threshold:
                    large_files.append((path.relative_to(repository.path), line_count))

    if not large_files:
        return Finding.create_pass(...)

    # Calculate proportional score
    score = max(0, 100 - (len(large_files) * 10))
    return Finding(..., score=score, evidence=[f"{path}: {lines} lines" for path, lines in large_files])
```

**References**:
- Threshold: 500 lines (based on research report)
- Pattern: `CyclomaticComplexityAssessor` for file scanning

---

### Issue 4: Implement Dependency Freshness Assessor

**Priority**: P1 (High-Impact)
**Impact**: +3 points (Tier 2, 3% weight)
**Effort**: Medium
**Labels**: `enhancement`, `assessor`, `tier-2`

**Description**:

Implement assessor to check for outdated dependencies (security and compatibility).

**Acceptance Criteria**:
- Parse pyproject.toml, package.json, Cargo.toml, Gemfile
- Check dependencies against registries (PyPI, npm, crates.io)
- Use `pip list --outdated`, `npm outdated`, or API calls
- Calculate % of dependencies that are up-to-date
- Flag major version updates available
- Provide remediation with upgrade commands

**Implementation Notes**:
```python
import subprocess

def check_python_outdated(repo_path):
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        outdated = json.loads(result.stdout)
        return outdated
    except Exception:
        return None
```

**Scoring**:
- 100 points: ≥90% dependencies up-to-date
- Proportional: 70-89% up-to-date
- 0 points: <70% up-to-date

**Graceful Degradation**:
- Skip if no internet access
- Skip if package manager not installed
- Return "skipped" instead of crashing

---

### Issue 5: Implement Architecture Decision Records Assessor

**Priority**: P1 (Easy Win)
**Impact**: +3 points (Tier 3, 3% weight)
**Effort**: Low
**Labels**: `enhancement`, `assessor`, `tier-3`

**Description**:

Implement assessor to check for ADR files. Agentready already has `specs/` directory with design docs, so this would likely pass!

**Acceptance Criteria**:
- Check for `docs/adr/`, `docs/decisions/`, `specs/`, `architecture/` directories
- Look for files matching ADR patterns (`NNNN-title.md`, `adr-NNNN.md`)
- Count number of ADR files
- Pass if ≥3 ADR files found
- Provide remediation with ADR template and tools

**Implementation**:
```python
def assess(self, repository: Repository) -> Finding:
    adr_dirs = ["docs/adr", "docs/decisions", "specs", "architecture"]
    adr_patterns = [r'^\d{4}-.*\.md$', r'^adr-\d+\.md$', r'.*-decision\.md$']

    found_adrs = []
    for adr_dir in adr_dirs:
        path = repository.path / adr_dir
        if path.exists():
            for file in path.glob("**/*.md"):
                if any(re.match(pattern, file.name) for pattern in adr_patterns):
                    found_adrs.append(file.relative_to(repository.path))

    count = len(found_adrs)
    if count >= 3:
        return Finding.create_pass(self.attribute, measured_value=f"{count} ADRs", evidence=found_adrs)
    # ... etc
```

**References**:
- ADR format: https://adr.github.io/
- Tool: `adr-tools` (https://github.com/npryce/adr-tools)

---

## Ruleset Calibration (P0)

### Issue 6: Recalibrate Ruleset for Language-Specific Projects

**Priority**: P0 (Critical - Affects All Assessments)
**Impact**: Better accuracy across Python, Node.js, Rust, Go projects
**Effort**: Medium
**Labels**: `bug`, `calibration`, `architecture`

**Description**:

The assessment ruleset currently has language-specific assumptions that cause false negatives. The lock files and conventional commits fixes (from this PR) are just two examples.

**Problems Identified**:
1. **Language-specific assumptions**: Assessors assume Node.js tooling (npm, husky, commitlint) for all projects
2. **Application vs. library distinction**: Lock files penalized universally (but libraries shouldn't require them)
3. **Project type awareness**: OpenAPI specs expected for CLI tools
4. **Tool detection vs. behavior**: Check for config files, not actual compliance

**Recommendations**:

1. **Detect language first, then check language-appropriate tools**:
   - Python: conventional-pre-commit, pre-commit, pytest
   - Node.js: husky, commitlint, jest
   - Go: go.sum, go test
   - Rust: Cargo.lock, cargo test

2. **Different rules for applications vs. libraries**:
   - Applications: Lock files required (reproducible deployments)
   - Libraries: Lock files optional (flexible dependency resolution)
   - Detection: Check for [project.scripts], executable entry points, Docker files

3. **Detect project type and adjust expectations**:
   - API servers: OpenAPI required
   - CLI tools: OpenAPI not applicable
   - Libraries: OpenAPI not applicable
   - Detection: Check for FastAPI/Flask, Click/Typer, setuptools

4. **Check actual behavior where possible**:
   - Conventional commits: Analyze recent commit messages, not just config
   - Type annotations: Count actual annotations in code ✅ (already does this!)
   - Test coverage: Check actual coverage reports ✅ (already does this!)

**Implementation Plan**:
1. Create `LanguageDetector` service to identify project type
2. Create `ProjectTypeDetector` service (application vs. library vs. CLI vs. API)
3. Update all assessors to use these services
4. Update research report with language-specific guidance

**References**:
- Fixes in this PR serve as examples (lock files, conventional commits)
- See: `specs/issue-121-score-analysis.md` for full analysis

---

## Documentation Updates (P2)

### Issue 7: Update Research Report with Calibration Learnings

**Priority**: P2
**Impact**: Better guidance for users and contributors
**Effort**: Low
**Labels**: `documentation`, `research`

**Description**:

Update `agent-ready-codebase-attributes.md` to include language-specific guidance and clarifications from the score analysis calibration.

**Updates Needed**:

1. **Lock Files attribute** - Add note about libraries:
   > **Note for Libraries**: Python libraries distributed via PyPI should use `pyproject.toml` with version constraints but may omit lock files to allow flexible dependency resolution. Applications and services should always use lock files.

2. **Conventional Commits attribute** - List language-specific tools:
   > **Tools by Language**:
   > - Python: `conventional-pre-commit` hook
   > - Node.js: `commitlint` + `husky`
   > - Any: Git hooks, CI checks

3. **OpenAPI Specs attribute** - Clarify applicability:
   > **Applicability**: This attribute applies only to projects that expose HTTP APIs. CLI tools, libraries, and batch processors should be marked "not_applicable".

4. **Add "Language-Specific Considerations" section** to research report explaining how criteria vary by ecosystem.

---

## Nice-to-Have (P3)

### Issue 8: Add Attribute Applicability Detection

**Priority**: P3
**Impact**: More accurate scores (don't penalize CLIs for missing OpenAPI specs)
**Effort**: Medium
**Labels**: `enhancement`, `architecture`

**Description**:

Implement `is_applicable()` method for assessors to properly detect when attributes don't apply to a project.

**Examples**:
- OpenAPI specs → Not applicable for CLI tools
- Container setup → Not applicable for libraries
- Performance benchmarks → Not applicable for documentation-only repos

**Implementation**:
```python
class OpenAPIAssessor(BaseAssessor):
    def is_applicable(self, repository: Repository) -> bool:
        # Check for API framework imports
        has_api_framework = any([
            (repository.path / "requirements.txt").exists() and "fastapi" in (repository.path / "requirements.txt").read_text(),
            # ... check for Flask, Express, Rocket, etc.
        ])
        return has_api_framework
```

**Benefits**:
- More accurate scores
- Better user experience (don't show irrelevant failures)
- Aligns with research report intent

---

## Summary

**Quick Wins** (implement first):
1. ✅ Lock Files Assessor - Fixed in this PR (+10 points for agentready)
2. ✅ Conventional Commits Assessor - Fixed in this PR (+3 points for agentready)
3. One-Command Setup - Easy, agentready already has it (+3 points)
4. File Size Limits - Simple scanner (+3 points)
5. Architecture Decision Records - Check for specs/ directory (+3 points)

**Expected Score After Quick Wins**: 80.0 → 93.0 (from fixes) → 102.0 (from remaining quick wins, capped at **Platinum 100/100**)

**Medium-Term** (implement after quick wins):
- Inline Documentation Assessor
- Dependency Freshness Assessor
- Ruleset Calibration (critical for accuracy)

**Long-Term**:
- Applicability detection
- Documentation updates

---

**Generated from**: Issue #121 Score Analysis
**Branch**: claude/issue-121-20251124-0349
**Author**: Claude
**Date**: 2025-11-24
