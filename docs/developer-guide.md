---
layout: page
title: Developer Guide
---

Comprehensive guide for contributors and developers extending AgentReady.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Architecture Overview](#architecture-overview)
- [Implementing New Assessors](#implementing-new-assessors)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality Standards](#code-quality-standards)
- [Contributing Workflow](#contributing-workflow)
- [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- **Python 3.12 or 3.13**
- **Git**
- **uv** or **pip** (uv recommended for faster dependency management)
- **Make** (optional, for convenience commands)

### Fork and Clone

```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/agentready.git
cd agentready

# Add upstream remote
git remote add upstream https://github.com/ambient-code/agentready.git
```

### Install Development Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"

# Verify installation
pytest --version
black --version
ruff --version
```

---

## Development Environment

### Project Structure

```
agentready/
├── src/agentready/          # Source code
│   ├── cli/                 # Click-based CLI
│   │   └── main.py          # Entry point (assess, research-version, generate-config)
│   ├── models/              # Data models
│   │   ├── repository.py    # Repository representation
│   │   ├── attribute.py     # Attribute definition
│   │   ├── finding.py       # Assessment finding
│   │   └── assessment.py    # Complete assessment result
│   ├── services/            # Core business logic
│   │   ├── scanner.py       # Assessment orchestration
│   │   ├── scorer.py        # Score calculation
│   │   └── language_detector.py  # Language detection via git
│   ├── assessors/           # Attribute assessors
│   │   ├── base.py          # BaseAssessor abstract class
│   │   ├── documentation.py # CLAUDE.md, README assessors
│   │   ├── code_quality.py  # Type annotations, complexity
│   │   ├── testing.py       # Test coverage, pre-commit hooks
│   │   ├── structure.py     # Standard layout, gitignore
│   │   ├── repomix.py       # Repomix configuration assessor
│   │   └── stub_assessors.py # 9 stub assessors (22 implemented)
│   ├── reporters/           # Report generators
│   │   ├── html.py          # Interactive HTML with Jinja2
│   │   ├── markdown.py      # GitHub-Flavored Markdown
│   │   └── json.py          # Machine-readable JSON
│   ├── templates/           # Jinja2 templates
│   │   └── report.html.j2   # HTML report template
│   └── data/                # Bundled data
│       └── attributes.yaml  # Attribute definitions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests (fast, isolated)
│   │   ├── test_models.py
│   │   ├── test_assessors_documentation.py
│   │   ├── test_assessors_code_quality.py
│   │   └── ...
│   ├── integration/        # End-to-end tests
│   │   └── test_full_assessment.py
│   └── fixtures/           # Test data
│       └── sample_repos/   # Sample repositories for testing
├── docs/                    # GitHub Pages documentation
├── examples/               # Example reports
│   └── self-assessment/    # AgentReady's own assessment
├── pyproject.toml          # Python package configuration
├── CLAUDE.md              # Project context for AI agents
├── README.md              # User-facing documentation
└── BACKLOG.md             # Feature backlog
```

### Development Tools

AgentReady uses modern Python tooling:

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **pytest** | Testing framework | `pyproject.toml` |
| **black** | Code formatter | `pyproject.toml` |
| **isort** | Import sorter | `pyproject.toml` |
| **ruff** | Fast linter | `pyproject.toml` |
| **mypy** | Type checker | `pyproject.toml` (future) |

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/agentready --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v

# Run tests matching pattern
pytest -k "test_claude_md" -v

# Run with output (don't capture print statements)
pytest -s

# Fast fail (stop on first failure)
pytest -x
```

**Recent Test Infrastructure Improvements (v1.27.2)**:

1. **Shared Test Fixtures** (`tests/conftest.py`):
   - Reusable repository fixtures for consistent test data
   - Reduced test code duplication
   - Faster test development

2. **Model Validation Enhancements**:
   - Enhanced Assessment schema validation
   - Path sanitization for cross-platform compatibility
   - Proper handling of optional fields

3. **Comprehensive Coverage**:
   - CLI tests (Phase 4) complete
   - Service module tests (Phase 3) complete
   - All 35 pytest failures from v1.27.0 resolved

**Current test coverage**: Focused on core logic (models, scoring, critical assessors)

### Code Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Run all quality checks (recommended before committing)
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/
```

### Pre-commit Hooks (Recommended)

Install pre-commit hooks to automatically run quality checks:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## Architecture Overview

AgentReady follows a **library-first architecture** with clear separation of concerns.

### Data Flow

```
Repository → Scanner → Assessors → Findings → Assessment → Reporters → Reports
                ↓
         Language Detection
         (git ls-files)
```

### Core Components

#### 1. Models (`models/`)

Immutable data classes representing domain entities:

- **Repository**: Path, name, detected languages
- **Attribute**: ID, name, tier, weight, description
- **Finding**: Attribute, status (pass/fail/skip), score, evidence, remediation
- **Assessment**: Repository, overall score, certification level, findings list

**Design Principles**:

- Immutable (frozen dataclasses)
- Type-annotated
- No business logic (pure data)
- Factory methods for common patterns (`Finding.create_pass()`, etc.)

#### 2. Services (`services/`)

Orchestration and core algorithms:

- **Scanner**: Coordinates assessment flow, manages assessors
- **Scorer**: Calculates weighted scores, determines certification levels
- **LanguageDetector**: Detects repository languages via `git ls-files`

**Design Principles**:

- Stateless (pure functions or stateless classes)
- Single responsibility
- No external dependencies (file I/O, network)
- Testable with mocks

#### 3. Assessors (`assessors/`)

Strategy pattern implementations for each attribute:

- **BaseAssessor**: Abstract base class defining interface
- Concrete assessors: `CLAUDEmdAssessor`, `READMEAssessor`, etc.

**Design Principles**:

- Each assessor is independent
- Inherit from `BaseAssessor`
- Implement `assess(repository)` method
- Return `Finding` object
- Fail gracefully (return "skipped" if tools missing, don't crash)

#### 4. Reporters (`reporters/`)

Transform `Assessment` into report formats:

- **HTMLReporter**: Jinja2-based interactive report
- **MarkdownReporter**: GitHub-Flavored Markdown
- **JSONReporter**: Machine-readable JSON

**Design Principles**:

- Take `Assessment` as input
- Return formatted string
- Self-contained (HTML has inline CSS/JS, no CDN)
- Idempotent (same input → same output)

### Key Design Patterns

#### Strategy Pattern (Assessors)

Each assessor is a pluggable strategy implementing the same interface:

```python
from abc import ABC, abstractmethod

class BaseAssessor(ABC):
    @property
    @abstractmethod
    def attribute_id(self) -> str:
        """Unique attribute identifier."""
        pass

    @abstractmethod
    def assess(self, repository: Repository) -> Finding:
        """Assess repository for this attribute."""
        pass

    def is_applicable(self, repository: Repository) -> bool:
        """Check if this assessor applies to the repository."""
        return True
```

#### Factory Pattern (Finding Creation)

`Finding` class provides factory methods for common patterns:

```python
# Pass with full score
finding = Finding.create_pass(
    attribute=attribute,
    evidence="Found CLAUDE.md at repository root",
    remediation=None
)

# Fail with zero score
finding = Finding.create_fail(
    attribute=attribute,
    evidence="No CLAUDE.md file found",
    remediation=Remediation(steps=[...], tools=[...])
)

# Skip (not applicable)
finding = Finding.create_skip(
    attribute=attribute,
    reason="Not implemented yet"
)
```

#### Template Pattern (Reporters)

Reporters use Jinja2 templates for HTML generation:

```python
from jinja2 import Environment, FileSystemLoader

class HTMLReporter:
    def generate(self, assessment: Assessment) -> str:
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html.j2')
        return template.render(assessment=assessment)
```

---

## Bootstrap System Architecture

### Overview

The Bootstrap system automates infrastructure generation through template rendering and language-aware configuration.

### Data Flow

```
Repository → LanguageDetector → BootstrapGenerator → Templates → Generated Files
                     ↓                    ↓
              Primary Language    Template Variables
                                   (language, repo_name, etc.)
```

### Core Components

#### 1. Bootstrap Services (`services/bootstrap.py`)

**`BootstrapGenerator`** — Main orchestration class:

```python
class BootstrapGenerator:
    """Generate agent-ready infrastructure for repositories."""

    def __init__(self, template_dir: str):
        """Initialize with template directory path."""
        self.template_dir = template_dir
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def generate(
        self,
        repository: Repository,
        language: str = "auto",
        dry_run: bool = False
    ) -> List[GeneratedFile]:
        """
        Generate infrastructure files for repository.

        Args:
            repository: Repository object
            language: Primary language (auto-detected if "auto")
            dry_run: Preview only, don't create files

        Returns:
            List of GeneratedFile objects with paths and content
        """
```

**Key Methods**:

- `_detect_language()` — Auto-detect primary language via LanguageDetector
- `_render_template()` — Render Jinja2 template with context variables
- `_get_templates_for_language()` — Map language to template files
- `_write_file()` — Create file on disk (respects dry_run)
- `_file_exists()` — Check for conflicts (never overwrites)

#### 2. Bootstrap CLI (`cli/bootstrap.py`)

Command-line interface for Bootstrap:

```python
@click.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option("--dry-run", is_flag=True, help="Preview without creating files")
@click.option(
    "--language",
    type=click.Choice(["python", "javascript", "go", "auto"]),
    default="auto",
    help="Primary language override"
)
def bootstrap(repository, dry_run, language):
    """Bootstrap agent-ready infrastructure for repository."""
```

**Responsibilities**:

- Parse command-line arguments
- Create Repository object
- Instantiate BootstrapGenerator
- Display progress and results
- Handle errors gracefully

#### 3. Templates (`templates/bootstrap/`)

Jinja2 templates for generated files:

```
templates/bootstrap/
├── common/                          # Language-agnostic templates
│   ├── CODEOWNERS.j2
│   ├── CONTRIBUTING.md.j2
│   ├── CODE_OF_CONDUCT.md.j2
│   ├── bug_report.md.j2
│   ├── feature_request.md.j2
│   └── pull_request_template.md.j2
├── python/                          # Python-specific
│   ├── agentready-assessment.yml.j2
│   ├── tests.yml.j2
│   ├── security.yml.j2
│   ├── pre-commit-config.yaml.j2
│   └── dependabot.yml.j2
├── javascript/                      # JavaScript-specific
│   └── ... (similar structure)
└── go/                              # Go-specific
    └── ... (similar structure)
```

### Template Variables

All templates receive these context variables:

```python
context = {
    "repository_name": repository.name,
    "language": detected_language,
    "has_tests_directory": os.path.exists(f"{repo_path}/tests"),
    "has_src_directory": os.path.exists(f"{repo_path}/src"),
    "python_version": "3.11",  # Or detected version
    "node_version": "18",      # Or detected version
    "go_version": "1.21",      # Or detected version
    "year": datetime.now().year,
    "organization": extract_org_from_remote(repo_path)  # From git remote
}
```

### Language Detection Logic

```python
class LanguageDetector:
    """Detect primary language from repository files."""

    EXTENSION_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".java": "Java",
        # ... more extensions
    }

    def detect(self, repo_path: str) -> Dict[str, int]:
        """
        Count files by language.

        Returns:
            Dict mapping language name to file count
            Example: {"Python": 42, "JavaScript": 18}
        """

    def get_primary_language(self, languages: Dict[str, int]) -> str:
        """Return language with most files."""
        return max(languages, key=languages.get)
```

### File Generation Flow

1. **Detect Language**:

   ```python
   if language == "auto":
       languages = LanguageDetector().detect(repository.path)
       primary = LanguageDetector().get_primary_language(languages)
   else:
       primary = language
   ```

2. **Select Templates**:

   ```python
   templates = {
       "python": [
           "python/agentready-assessment.yml.j2",
           "python/tests.yml.j2",
           "python/pre-commit-config.yaml.j2",
           # ... common templates
       ],
       "javascript": [...],
       "go": [...]
   }
   selected = templates[primary]
   ```

3. **Render Each Template**:

   ```python
   for template_path in selected:
       template = jinja_env.get_template(template_path)
       content = template.render(**context)
       output_path = determine_output_path(template_path)
       if not os.path.exists(output_path):
           write_file(output_path, content)
   ```

4. **Return Results**:

   ```python
   return [
       GeneratedFile(
           path=".github/workflows/tests.yml",
           content=rendered_content,
           created=True
       ),
       # ... more files
   ]
   ```

### Error Handling

Bootstrap implements defensive programming:

```python
class BootstrapError(Exception):
    """Base exception for Bootstrap errors."""

class LanguageDetectionError(BootstrapError):
    """Raised when language detection fails."""

class TemplateRenderError(BootstrapError):
    """Raised when template rendering fails."""

class FileWriteError(BootstrapError):
    """Raised when file write fails (permissions, etc.)."""
```

**Error scenarios**:

- Not a git repository → Fail early with clear message
- Language detection fails → Require `--language` flag
- Template not found → Report missing template name
- File already exists → Skip gracefully, report in output
- Permission denied → Report path and suggest fix

### Dry Run Implementation

```python
def generate(self, repository, language="auto", dry_run=False):
    """Generate infrastructure."""

    generated_files = []

    for template_path in templates:
        content = self._render_template(template_path, context)
        output_path = self._determine_output_path(template_path)

        if dry_run:
            # Don't write, just report what would happen
            generated_files.append(
                GeneratedFile(
                    path=output_path,
                    content=content,
                    created=False,  # Would be created
                    dry_run=True
                )
            )
        else:
            if not os.path.exists(output_path):
                self._write_file(output_path, content)
                generated_files.append(
                    GeneratedFile(
                        path=output_path,
                        content=content,
                        created=True
                    )
                )

    return generated_files
```

---

## Creating Bootstrap Templates

### Template Structure

All Bootstrap templates follow consistent patterns for maintainability.

### 1. GitHub Actions Workflow Template

**Location**: `templates/bootstrap/python/agentready-assessment.yml.j2`

```yaml
name: AgentReady Assessment

on:
  pull_request:
  push:
    branches: [main, master]

jobs:
  assess:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '{{ python_version }}'

      - name: Install AgentReady
        run: pip install agentready

      - name: Run Assessment
        id: assessment
        run: |
          agentready assess . --output-dir .agentready
          score=$(jq '.overall_score' .agentready/assessment-latest.json)
          echo "score=$score" >> $GITHUB_OUTPUT

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: agentready-report
          path: .agentready/report-latest.html

      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.agentready/report-latest.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

      - name: Check Score Threshold
        run: |
          if (( $(echo "${{ steps.assessment.outputs.score }} < 60" | bc -l) )); then
            echo "Score below threshold: ${{ steps.assessment.outputs.score }}"
            exit 1
          fi
```

**Template variables used**:

- `{{ python_version }}` — Python version from context
- Could add: `{{ threshold }}`, `{{ branches }}` for customization

### 2. Pre-commit Config Template

**Location**: `templates/bootstrap/python/pre-commit-config.yaml.j2`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python{{ python_version }}

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 3. Issue Template

**Location**: `templates/bootstrap/common/bug_report.md.j2`

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- {% raw %}{% if language == "python" %}Python{% elsif language == "javascript" %}Node.js{% elsif language == "go" %}Go{% endif %} Version: [e.g., {{ python_version if language == "python" else node_version if language == "javascript" else go_version }}]
- {{ repository_name }} Version: [e.g., 1.0.0]{% endraw %}

**Additional context**
Add any other context about the problem here.
```

### 4. Conditional Template Logic

Templates can use Jinja2 conditionals:

```yaml
# In tests.yml.j2

{% if language == "python" %}
  - name: Run Tests
    run: |
      pip install pytest pytest-cov
      pytest --cov=src --cov-report=html
{% elsif language == "javascript" %}
  - name: Run Tests
    run: |
      npm install
      npm test -- --coverage
{% elsif language == "go" %}
  - name: Run Tests
    run: |
      go test -v -race -coverprofile=coverage.out ./...
{% endif %}
```

### Template Development Workflow

1. **Create template**:

   ```bash
   vim src/agentready/templates/bootstrap/python/mytemplate.yml.j2
   ```

2. **Add template variables**:

   ```jinja2
   name: {{ repository_name }} CI
   version: {{ python_version }}
   ```

3. **Register in BootstrapGenerator**:

   ```python
   TEMPLATES = {
       "python": [
           # ... existing templates
           "python/mytemplate.yml.j2",
       ]
   }
   ```

4. **Test with dry-run**:

   ```bash
   agentready bootstrap . --dry-run
   ```

5. **Verify rendered output**:

   ```bash
   # Check generated content
   cat .github/workflows/mytemplate.yml
   ```

### Template Best Practices

1. **Use descriptive variable names**:

   ```jinja2
   # Good
   {{ python_version }}
   {{ repository_name }}

   # Bad
   {{ ver }}
   {{ name }}
   ```

2. **Provide defaults**:

   ```jinja2
   {% raw %}python-version: '{{ python_version | default("3.11") }}'{% endraw %}
   ```

3. **Add comments**:

   ```yaml
   # This workflow runs on every PR to main
   # Generated by AgentReady Bootstrap
   name: Tests
   ```

4. **Handle optional sections**:

   ```jinja2
   {% if has_tests_directory %}
   - name: Run Tests
     run: pytest tests/
   {% else %}
   # No tests directory found - add tests to enable this step
   {% endif %}
   ```

5. **Include generation metadata**:

   ```yaml
   # Generated by AgentReady Bootstrap v{{ agentready_version }}
   # Date: {{ generation_date }}
   # Language: {{ language }}
   # Do not edit - regenerate with: agentready bootstrap .
   ```

---

## Implementing New Assessors

Follow this step-by-step guide to add a new assessor.

### Step 1: Choose an Attribute

Check `src/agentready/assessors/stub_assessors.py` for not-yet-implemented attributes:

```python
# Example stub assessor
class InlineDocumentationAssessor(BaseAssessor):
    @property
    def attribute_id(self) -> str:
        return "inline_documentation"

    def assess(self, repository: Repository) -> Finding:
        # TODO: Implement actual assessment logic
        return Finding.create_skip(
            self.attribute,
            reason="Assessor not yet implemented"
        )
```

### Step 2: Create Assessor Class

Create a new file or expand existing category file in `src/agentready/assessors/`:

```python
# src/agentready/assessors/documentation.py

from agentready.models import Repository, Finding, Attribute, Remediation
from agentready.assessors.base import BaseAssessor

class InlineDocumentationAssessor(BaseAssessor):
    @property
    def attribute_id(self) -> str:
        return "inline_documentation"

    def assess(self, repository: Repository) -> Finding:
        """
        Assess inline documentation coverage (docstrings/JSDoc).

        Checks:
        - Python: Presence of docstrings in .py files
        - JavaScript/TypeScript: JSDoc comments
        - Coverage: >80% of public functions documented
        """
        # Implement assessment logic here
        pass
```

### Step 3: Implement Assessment Logic

Use the `calculate_proportional_score()` helper for partial compliance:

```python
def assess(self, repository: Repository) -> Finding:
    # Example: Check Python docstrings
    if "Python" not in repository.languages:
        return Finding.create_skip(
            self.attribute,
            reason="No Python files detected"
        )

    # Count functions and docstrings
    total_functions = self._count_functions(repository)
    documented_functions = self._count_documented_functions(repository)

    if total_functions == 0:
        return Finding.create_skip(
            self.attribute,
            reason="No functions found"
        )

    # Calculate coverage
    coverage = documented_functions / total_functions
    score = self.calculate_proportional_score(coverage, 0.80)

    if score >= 80:  # Passes if >= 80% of target
        return Finding.create_pass(
            self.attribute,
            evidence=f"Documented {documented_functions}/{total_functions} functions ({coverage:.1%})",
            remediation=None
        )
    else:
        return Finding.create_fail(
            self.attribute,
            evidence=f"Only {documented_functions}/{total_functions} functions documented ({coverage:.1%})",
            remediation=self._create_remediation(coverage)
        )

def _count_functions(self, repository: Repository) -> int:
    """Count total functions in Python files."""
    # Implementation using ast or grep
    pass

def _count_documented_functions(self, repository: Repository) -> int:
    """Count functions with docstrings."""
    # Implementation using ast
    pass

def _create_remediation(self, current_coverage: float) -> Remediation:
    """Generate remediation guidance."""
    return Remediation(
        steps=[
            "Install pydocstyle: `pip install pydocstyle`",
            "Run docstring linter: `pydocstyle src/`",
            "Add docstrings to flagged functions",
            f"Target: {(0.80 - current_coverage) * 100:.0f}% more functions need documentation"
        ],
        tools=["pydocstyle", "pylint"],
        commands=[
            "pydocstyle src/",
            "pylint --disable=all --enable=missing-docstring src/"
        ],
        examples=[
            '''def calculate_total(items: List[Item]) -> float:
    """
    Calculate total price of items.

    Args:
        items: List of items to sum

    Returns:
        Total price in USD

    Example:
        >>> calculate_total([Item(5.0), Item(3.0)])
        8.0
    """
    return sum(item.price for item in items)'''
        ],
        citations=[
            "PEP 257 - Docstring Conventions",
            "Google Python Style Guide"
        ]
    )
```

### Step 4: Register Assessor

Add to scanner's assessor list in `src/agentready/services/scanner.py`:

```python
def __init__(self):
    self.assessors = [
        # Existing assessors...
        InlineDocumentationAssessor(),
    ]
```

### Step 5: Write Tests

Create comprehensive unit tests in `tests/unit/test_assessors_documentation.py`:

```python
import pytest
from agentready.models import Repository
from agentready.assessors.documentation import InlineDocumentationAssessor

class TestInlineDocumentationAssessor:
    def test_python_well_documented_passes(self, tmp_path):
        """Well-documented Python code should pass."""
        # Create test repository
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Create Python file with docstrings
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b
'''
        (repo_path / "main.py").write_text(code)

        # Create repository object
        repo = Repository(
            path=str(repo_path),
            name="test_repo",
            languages={"Python": 1}
        )

        # Run assessment
        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        # Verify result
        assert finding.status == "pass"
        assert finding.score == 100
        assert "2/2 functions" in finding.evidence

    def test_python_poorly_documented_fails(self, tmp_path):
        """Poorly documented Python code should fail."""
        # Create test repository
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Create Python file with no docstrings
        code = '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
'''
        (repo_path / "main.py").write_text(code)

        repo = Repository(
            path=str(repo_path),
            name="test_repo",
            languages={"Python": 1}
        )

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 80
        assert "0/2 functions" in finding.evidence
        assert finding.remediation is not None
        assert "pydocstyle" in finding.remediation.tools

    def test_non_python_skips(self, tmp_path):
        """Non-Python repositories should skip."""
        repo = Repository(
            path=str(tmp_path),
            name="test_repo",
            languages={"JavaScript": 10}
        )

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "skipped"
        assert "No Python files" in finding.reason
```

### Step 6: Test Manually

```bash
# Run your new tests
pytest tests/unit/test_assessors_documentation.py -v

# Run full assessment on AgentReady itself
agentready assess . --verbose

# Verify your assessor appears in output
```

### Best Practices for Assessors

1. **Fail Gracefully**: Return "skipped" if required tools missing, don't crash
2. **Provide Rich Remediation**: Include steps, tools, commands, examples, citations
3. **Use Proportional Scoring**: `calculate_proportional_score()` for partial compliance
4. **Language-Specific Logic**: Check `repository.languages` before assessing
5. **Avoid External Dependencies**: Use stdlib when possible (ast, re, pathlib)
6. **Performance**: Keep assessments fast (<1 second per assessor)
7. **Idempotent**: Same repository → same result
8. **Evidence**: Provide specific, actionable evidence (file paths, counts, examples)

---

## Testing Guidelines

AgentReady maintains high test quality standards.

### Test Organization

```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_models.py
│   ├── test_assessors_*.py
│   └── test_reporters.py
├── integration/           # End-to-end tests
│   └── test_full_assessment.py
└── fixtures/              # Shared test data
    └── sample_repos/
```

### Test Types

#### Unit Tests

- **Purpose**: Test individual components in isolation
- **Speed**: Very fast (<1s total)
- **Coverage**: Models, assessors, services, reporters
- **Mocking**: Use `pytest` fixtures and mocks

#### Integration Tests

- **Purpose**: Test complete workflows end-to-end
- **Speed**: Slower (acceptable up to 10s total)
- **Coverage**: Full assessment pipeline
- **Real Data**: Use fixture repositories

### Writing Good Tests

#### Test Naming

Use descriptive names following pattern: `test_<what>_<when>_<expected>`

```python
# Good
def test_claude_md_assessor_with_existing_file_passes():
    pass

def test_readme_assessor_missing_quick_start_fails():
    pass

def test_type_annotations_assessor_javascript_repo_skips():
    pass

# Bad
def test_assessor():
    pass

def test_pass_case():
    pass
```

#### Arrange-Act-Assert Pattern

```python
def test_finding_create_pass_sets_correct_attributes():
    # Arrange
    attribute = Attribute(
        id="test_attr",
        name="Test Attribute",
        tier=1,
        weight=0.10
    )

    # Act
    finding = Finding.create_pass(
        attribute=attribute,
        evidence="Test evidence",
        remediation=None
    )

    # Assert
    assert finding.status == "pass"
    assert finding.score == 100
    assert finding.evidence == "Test evidence"
    assert finding.remediation is None
```

#### Use Fixtures

```python
@pytest.fixture
def sample_repository(tmp_path):
    """Create a sample repository for testing."""
    repo_path = tmp_path / "sample_repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # Add files
    (repo_path / "README.md").write_text("# Sample Repo")
    (repo_path / "CLAUDE.md").write_text("# Tech Stack")

    return Repository(
        path=str(repo_path),
        name="sample_repo",
        languages={"Python": 5}
    )

def test_with_fixture(sample_repository):
    assert sample_repository.name == "sample_repo"
```

### Coverage Requirements

- **Target**: >80% line coverage for new code
- **Minimum**: >70% overall coverage
- **Critical Paths**: 100% coverage (scoring algorithm, finding creation)

```bash
# Generate coverage report
pytest --cov=src/agentready --cov-report=html

# View report
open htmlcov/index.html
```

---

## Code Quality Standards

### Formatting

**Black** (88 character line length, opinionated formatting):

```bash
black src/ tests/
```

Configuration in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py311', 'py312']
```

### Import Sorting

**isort** (consistent import organization):

```bash
isort src/ tests/
```

Configuration in `pyproject.toml`:

```toml
[tool.isort]
profile = "black"
line_length = 88
```

### Linting

**Ruff** (fast Python linter):

```bash
ruff check src/ tests/
```

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]
ignore = ["E501"]  # Line too long (handled by black)
```

### Type Checking (Future)

**mypy** (static type checking):

```bash
mypy src/
```

Configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### Documentation Standards

- **Docstrings**: All public functions, classes, methods
- **Format**: Google-style docstrings
- **Type hints**: All function parameters and return types

```python
def calculate_weighted_score(findings: List[Finding], weights: Dict[str, float]) -> float:
    """
    Calculate weighted average score from findings.

    Args:
        findings: List of assessment findings
        weights: Attribute ID to weight mapping

    Returns:
        Weighted score from 0.0 to 100.0

    Raises:
        ValueError: If weights don't sum to 1.0

    Example:
        >>> findings = [Finding(score=80), Finding(score=90)]
        >>> weights = {"attr1": 0.5, "attr2": 0.5}
        >>> calculate_weighted_score(findings, weights)
        85.0
    """
    pass
```

---

## Contributing Workflow

### 1. Create Feature Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/inline-documentation-assessor
```

### 2. Implement Changes

- Write code following style guide
- Add comprehensive tests
- Update documentation (CLAUDE.md, README.md if needed)

### 3. Run Quality Checks

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
ruff check src/ tests/

# Run tests
pytest --cov

# All checks must pass
```

### 4. Commit Changes

Use **conventional commits**:

```bash
git add .
git commit -m "feat(assessors): add inline documentation assessor

- Implement Python docstring coverage assessment
- Add test coverage for various documentation levels
- Include rich remediation guidance with examples
- Support JSDoc detection for JavaScript/TypeScript (future)"
```

**Commit types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/inline-documentation-assessor
```

Create pull request on GitHub with:

- **Title**: Clear, descriptive (e.g., "Add inline documentation assessor")
- **Description**:
  - What changed
  - Why (link to issue if applicable)
  - Testing performed
  - Screenshots/examples (if UI changes)
- **Checklist**:
  - [ ] Tests added and passing
  - [ ] Code formatted (black, isort)
  - [ ] Linting passes (ruff)
  - [ ] Documentation updated
  - [ ] Changelog entry (if user-facing)

### 6. Address Review Feedback

- Respond to comments
- Make requested changes
- Push updates to same branch
- Re-request review

---

## Release Process

AgentReady follows **semantic versioning** (SemVer):

- **Major (X.0.0)**: Breaking changes
- **Minor (x.Y.0)**: New features, backward-compatible
- **Patch (x.y.Z)**: Bug fixes, backward-compatible

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite**: `pytest --cov`
4. **Run quality checks**: `black . && isort . && ruff check .`
5. **Build package**: `python -m build`
6. **Test package locally**: `pip install dist/agentready-X.Y.Z.tar.gz`
7. **Create git tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
8. **Push tag**: `git push upstream vX.Y.Z`
9. **Upload to PyPI**: `twine upload dist/*`
10. **Create GitHub release** with changelog

---

## Additional Resources

- **[Attributes Reference](attributes.md)** — Detailed attribute definitions
- **[API Reference](api-reference.md)** — Public API documentation
- **[Examples](examples.md)** — Real-world assessment reports
- **CLAUDE.md** — Project context for AI agents
- **BACKLOG.md** — Planned features and enhancements

---

**Ready to contribute?** Check out [good first issues](https://github.com/ambient-code/agentready/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) on GitHub!
