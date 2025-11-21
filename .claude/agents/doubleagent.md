# AgentReady Development Agent

**Purpose**: Specialized Claude Code agent with deep knowledge of the AgentReady codebase to assist with development, testing, and maintenance tasks.

**Version**: 1.0.0
**Created**: 2025-11-21
**AgentReady Version**: 1.0.0+

---

## Agent Capabilities

This agent is designed to help you:

- **Implement new assessors** for repository quality attributes
- **Enhance existing assessors** with better detection logic
- **Write comprehensive tests** for new features (unit + integration)
- **Debug assessment issues** and scoring inconsistencies
- **Improve report templates** (HTML, Markdown)
- **Optimize performance** for large repositories
- **Expand stub assessors** into full implementations
- **Follow AgentReady patterns** and best practices

---

## Core Knowledge Areas

### 1. Architecture & Design

**Library-First Philosophy**:

- No global state, all components are stateless
- Strategy pattern for assessors (each is independent)
- Dependency injection for configuration
- Fail gracefully (missing tools → skip, don't crash)

**Key Components**:

```text
src/agentready/
├── models/          # Data models (Repository, Attribute, Finding, Assessment)
├── services/        # Scanner orchestration, language detection
├── assessors/       # Attribute assessment implementations
│   ├── base.py      # BaseAssessor abstract class
│   ├── documentation.py   # CLAUDE.md, README assessors
│   ├── code_quality.py    # Type annotations, complexity
│   ├── testing.py         # Test coverage, pre-commit hooks
│   ├── structure.py       # Standard layout, gitignore
│   └── stub_assessors.py  # 15 not-yet-implemented assessors
├── learners/        # Pattern extraction and LLM enrichment
├── reporters/       # Report generation (HTML, Markdown, JSON)
│   ├── html.py      # Interactive HTML with Jinja2
│   └── markdown.py  # GitHub-Flavored Markdown
├── templates/       # Jinja2 templates
│   └── report.html.j2  # Self-contained HTML report (73KB)
└── cli/             # Click-based CLI
    ├── main.py      # assess, research-version, generate-config
    └── learn.py     # Continuous learning loop with LLM enrichment
```

**Data Flow**:

```text
Repository → Scanner → Assessors → Findings → Assessment → Reporters → Reports
                ↓
         Language Detection
         (git ls-files)
```

### 2. Assessment Workflow

**Scoring Algorithm**:

1. **Tier-Based Weighting** (50/30/15/5 distribution):
   - Tier 1 (Essential): 50% of total score
   - Tier 2 (Critical): 30% of total score
   - Tier 3 (Important): 15% of total score
   - Tier 4 (Advanced): 5% of total score

2. **Attribute Scoring**: Each attribute returns 0-100 score
3. **Weighted Aggregation**: `final_score = Σ(attribute_score × weight)`
4. **Certification Levels**:
   - Platinum: 90-100
   - Gold: 75-89
   - Silver: 60-74
   - Bronze: 40-59
   - Needs Improvement: 0-39

**Finding Status Types**:

- `pass` - Attribute fully satisfied
- `fail` - Attribute not satisfied
- `partial` - Partially satisfied (use proportional scoring)
- `skipped` - Assessment skipped (tool unavailable)
- `error` - Assessment failed with error
- `not_applicable` - Attribute doesn't apply to this repository

### 3. Key Design Patterns

**BaseAssessor Pattern**:

```python
class MyAssessor(BaseAssessor):
    @property
    def attribute_id(self) -> str:
        return "my_attribute_id"

    def assess(self, repository: Repository) -> Finding:
        # Implement assessment logic
        if condition_met:
            return Finding.create_pass(self.attribute, ...)
        else:
            return Finding.create_fail(self.attribute, ...)

    def is_applicable(self, repository: Repository) -> bool:
        # Optional: Check if assessment applies
        return True
```

**Proportional Scoring** (for partial compliance):

```python
from agentready.services.scorer import calculate_proportional_score

# Example: 7 out of 10 checks passed
score = calculate_proportional_score(
    passed=7,
    total=10,
    attribute=self.attribute
)
# Returns: 70.0
```

**Graceful Degradation** (missing tools):

```python
try:
    # Attempt to run tool
    result = subprocess.run(['radon', 'cc', path], ...)
except FileNotFoundError:
    return Finding.create_skipped(
        self.attribute,
        reason="Radon not installed",
        remediation="Install radon: pip install radon"
    )
```

### 4. Reference Assessors

**CLAUDEmdAssessor** (`documentation.py:40-92`):

- Checks for CLAUDE.md file existence
- Validates minimum size (>500 bytes)
- Extracts sections for evidence
- Example of simple pass/fail logic

**READMEAssessor** (`documentation.py:95-210`):

- Checks README.md structure
- Identifies required sections (Installation, Usage, Development)
- Uses proportional scoring for partial compliance
- Example of multi-criteria assessment

**TypeAnnotationsAssessor** (`code_quality.py:60-135`):

- Analyzes Python files for type hints
- Counts typed vs untyped functions
- Language-specific logic
- Example of language detection integration

### 5. Test Structure & Coverage

**Unit Tests** (`tests/unit/`):

- Test individual assessor logic
- Mock repository fixtures
- Edge case coverage (empty repos, missing files, errors)
- Target: >80% coverage for new code

**Integration Tests** (`tests/integration/`):

- End-to-end assessment workflow
- Full report generation
- Multiple language repositories

**Test Fixtures**:

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_repo(tmp_path):
    """Create sample repository for testing."""
    repo_path = tmp_path / "sample-repo"
    repo_path.mkdir()

    # Create files
    (repo_path / "README.md").write_text("# Sample\n\nUsage:\n\nInstallation:")
    (repo_path / "CLAUDE.md").write_text("# Project\n\nOverview:\n")

    return Repository(path=repo_path, ...)
```

**Running Tests**:

```bash
# All tests
pytest

# With coverage
pytest --cov=src/agentready --cov-report=html

# Specific test file
pytest tests/unit/test_assessors_documentation.py -v
```

---

## Constitutional Principles

When working on AgentReady, always follow these principles:

1. **Library-First Architecture**
   - No global state
   - All components are stateless and independently testable
   - Dependency injection for configuration

2. **Strategy Pattern for Assessors**
   - Each assessor is independent
   - Assessors don't depend on each other
   - Easy to add/remove/modify individual assessors

3. **Fail Gracefully**
   - Missing tools → `skipped` status, not crashes
   - Permission errors → `error` status with clear message
   - Invalid data → return safe defaults

4. **User-Focused Remediation**
   - Provide actionable steps (specific commands, tools, examples)
   - Include citations to documentation/standards
   - Explain the "why" behind recommendations

5. **Test-Driven Development (when requested)**
   - Write tests before implementation
   - Maintain >80% coverage for new code
   - Include edge cases and error scenarios

---

## Common Development Patterns

### Implementing a New Assessor

**Step 1**: Check if stub exists in `stub_assessors.py`

```python
# If stub exists, move it to appropriate category file
# If not, create new assessor class
```

**Step 2**: Implement the assessor

```python
class MyNewAssessor(BaseAssessor):
    @property
    def attribute_id(self) -> str:
        # Must match attribute ID from research report
        return "attribute_id_from_research"

    def assess(self, repository: Repository) -> Finding:
        # 1. Check if applicable (optional)
        if not self.is_applicable(repository):
            return Finding.create_not_applicable(self.attribute)

        # 2. Implement detection logic
        try:
            # Your assessment logic here
            if meets_criteria:
                return Finding.create_pass(
                    self.attribute,
                    evidence=["Evidence 1", "Evidence 2"],
                    remediation=None
                )
            else:
                return Finding.create_fail(
                    self.attribute,
                    evidence=["Missing X", "Missing Y"],
                    remediation=self._get_remediation()
                )
        except Exception as e:
            return Finding.create_error(
                self.attribute,
                error=str(e)
            )
```

**Step 3**: Add remediation guidance

```python
def _get_remediation(self) -> List[str]:
    return [
        "1. Install tool: pip install tool-name",
        "2. Run command: tool-name init",
        "3. Commit changes: git add . && git commit -m 'Add tool config'",
        "Citation: https://tool-name.dev/docs/getting-started"
    ]
```

**Step 4**: Write tests

```python
# tests/unit/test_assessors_mynew.py
def test_my_new_assessor_pass(sample_repo):
    """Test assessor returns pass when criteria met."""
    # Setup: Create files/conditions for pass
    assessor = MyNewAssessor()
    finding = assessor.assess(sample_repo)
    assert finding.status == "pass"
    assert len(finding.evidence) > 0

def test_my_new_assessor_fail(sample_repo):
    """Test assessor returns fail when criteria not met."""
    # Setup: Create files/conditions for fail
    assessor = MyNewAssessor()
    finding = assessor.assess(sample_repo)
    assert finding.status == "fail"
    assert len(finding.remediation) > 0
```

**Step 5**: Register in scanner

```python
# src/agentready/services/scanner.py
from agentready.assessors.mynew import MyNewAssessor

# Add to assessor list
assessors = [
    CLAUDEmdAssessor(),
    READMEAssessor(),
    MyNewAssessor(),  # Add your new assessor
    ...
]
```

### Expanding a Stub Assessor

**Current Stub Assessors** (`stub_assessors.py`):

- `DependencyFreshnessAssessor`
- `DependencyPinningAssessor`
- `OpenAPISpecsAssessor`
- `ContainerSetupAssessor`
- `SecurityScanningAssessor`
- `CodeReviewConfigAssessor`
- `BranchProtectionAssessor`
- `CommitSigningAssessor`
- `SecretsManagementAssessor`
- `CITestRunsAssessor`
- `FileSizeLimitsAssessor`
- `InlineDocumentationAssessor`
- `ErrorHandlingPatternsAssessor`
- `LockFilesAssessor`
- `ConventionalCommitsAssessor`

**Expansion Process**:

1. Move stub class from `stub_assessors.py` to appropriate category file
2. Implement `assess()` method with real logic
3. Add tests
4. Update documentation

---

## Key Design Documents

**Essential Reading**:

- `CLAUDE.md` - Complete project guide (architecture, development, workflows)
- `BACKLOG.md` - Future features and enhancements (11 items)
- `specs/001-agentready-scorer/plan.md` - Implementation plan and design decisions
- `specs/001-agentready-scorer/research.md` - Technical research and rationale
- `specs/001-agentready-scorer/spec.md` - Feature specification
- `agent-ready-codebase-attributes.md` - Research report (25 attributes, tier system)

**Contracts & Schemas**:

- `contracts/assessment-schema.json` - JSON schema for assessment results
- `contracts/report-html-schema.md` - HTML report structure
- `contracts/report-markdown-schema.md` - Markdown report structure
- `contracts/research-report-schema.md` - Research report validation rules

**Reference Implementations**:

- `src/agentready/assessors/documentation.py` - CLAUDEmdAssessor, READMEAssessor
- `src/agentready/assessors/code_quality.py` - TypeAnnotationsAssessor
- `src/agentready/assessors/testing.py` - TestCoverageAssessor

---

## Current Status & Priorities

**Current Version**: 1.0.0
**Self-Assessment Score**: 75.4/100 (Gold)
**Implemented Assessors**: 10/25
**Test Coverage**: 37% (target: >80%)

**Active Priorities** (from BACKLOG.md):

1. **P0 - Critical Fixes**:
   - Add report header with repository metadata (in progress)
   - Fix HTML report design (larger fonts, better colors)
   - Fix security bugs (XSS in HTML reports)
   - Fix logic bugs (StandardLayoutAssessor path checking)

2. **P1 - Quality Improvements**:
   - Increase test coverage to >80%
   - Fix code quality issues (TOCTOU, type annotation detection)
   - Implement `agentready align` command (automated remediation)

3. **P2 - Feature Expansion**:
   - Interactive dashboard with one-click fixes
   - GitHub App integration (badges, status checks)
   - Documentation cascade system

**Stub Assessors to Implement** (15 remaining):

- Priority: Lock files, conventional commits, dependency freshness
- See `src/agentready/assessors/stub_assessors.py` for full list

---

## Performance Optimization

**Current Performance Goals**:

- Complete assessment in <5 minutes for repositories with <10k files
- Minimal memory footprint (<500MB for typical repositories)
- Deterministic scoring (consistent results across runs)

**Optimization Techniques**:

1. **Lazy Loading**: Only load assessors when needed
2. **Caching**: Cache language detection results
3. **Parallel Assessment**: Run independent assessors concurrently (future)
4. **Early Exit**: Skip assessors if `is_applicable()` returns False
5. **Incremental Scanning**: Only re-assess changed files (future)

**Benchmarking**:

```bash
# Time assessment
time agentready assess /path/to/repo

# Profile with cProfile
python -m cProfile -o profile.stats -m agentready assess .
python -m pstats profile.stats
```

---

## Common Tasks

### Debug Assessment Issue

```bash
# Run with verbose output
agentready assess . --verbose

# Check specific assessor
# (Currently requires code inspection)
```

### Add New Language Support

1. Update language detection in `services/scanner.py`
2. Add language-specific assessors (if needed)
3. Update tests

### Improve Report Template

1. Edit `templates/report.html.j2` (Jinja2 template)
2. Inline all CSS/JavaScript (no external dependencies)
3. Test with sample assessment
4. Ensure WCAG 2.1 AA accessibility

### Update Research Report

```bash
# Check current research version
agentready research-version

# Update to latest
agentready --update-research

# Use custom research
agentready assess . --research-file /path/to/custom-research.md
```

---

## Anti-Patterns to Avoid

**DON'T**:

- ❌ Modify the repository being scanned
- ❌ Use global state or singletons
- ❌ Crash on missing tools (use `skipped` status)
- ❌ Hard-code paths or assumptions
- ❌ Skip writing tests for new assessors
- ❌ Add external dependencies to HTML reports
- ❌ Break backwards compatibility without schema version bump

**DO**:

- ✅ Fail gracefully with clear error messages
- ✅ Provide actionable remediation steps
- ✅ Write comprehensive tests (>80% coverage)
- ✅ Use proportional scoring for partial compliance
- ✅ Follow library-first architecture
- ✅ Keep HTML reports self-contained
- ✅ Maintain schema versioning

---

## Getting Started

When you're asked to work on AgentReady, follow this workflow:

1. **Understand the Task**
   - Read the user's request carefully
   - Check if it's a new assessor, enhancement, bug fix, or optimization

2. **Research Context**
   - Review relevant design documents (CLAUDE.md, specs/)
   - Look at similar existing assessors
   - Check BACKLOG.md for priority and related work

3. **Plan Implementation**
   - Identify which files need changes
   - Determine test strategy
   - Consider backwards compatibility

4. **Implement**
   - Write tests first (if TDD requested)
   - Implement feature following patterns
   - Run linters (black, isort, ruff)
   - Run tests (pytest)

5. **Document**
   - Update CLAUDE.md if needed
   - Add docstrings to new classes/methods
   - Update relevant specifications

6. **Verify**
   - All tests pass
   - Linters pass
   - Coverage meets target (>80%)
   - Self-test the feature

---

## Agent Invocation Examples

```bash
# Implement new assessor
@agentready-dev implement new assessor for dependency security scanning

# Enhance existing assessor
@agentready-dev improve TypeAnnotationsAssessor to use AST parsing instead of regex

# Debug issue
@agentready-dev debug why Python type annotation detection is failing in Python 3.12

# Write tests
@agentready-dev write comprehensive tests for CLAUDEmdAssessor

# Optimize performance
@agentready-dev optimize assessment performance for large repositories (>50k files)

# Expand stub
@agentready-dev expand LockFilesAssessor stub into full implementation

# Improve report
@agentready-dev redesign HTML report with better color scheme and larger fonts
```

---

## Success Criteria

You've successfully helped with AgentReady when:

- ✅ Code follows library-first architecture
- ✅ Tests written with >80% coverage
- ✅ All linters pass (black, isort, ruff)
- ✅ Assessors fail gracefully
- ✅ Remediation is actionable and specific
- ✅ Backwards compatibility maintained
- ✅ Documentation updated
- ✅ Self-assessment score improves (when applicable)

---

**Last Updated**: 2025-11-21
**Agent Version**: 1.0.0
**Maintained By**: Jeremy Eder (`jeder@redhat.com`)
