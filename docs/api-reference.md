---
layout: page
title: API Reference
---

Complete reference for AgentReady's Python API. Use these APIs to integrate AgentReady into your own tools, CI/CD pipelines, or custom workflows.

## Table of Contents

- [Installation](#installation)
- [Core Models](#core-models)
- [Services](#services)
- [Assessors](#assessors)
- [Reporters](#reporters)
- [Usage Examples](#usage-examples)

---

## Installation

```bash
pip install agentready
```

Import the library:

```python
from agentready.models import Repository, Assessment, Finding, Attribute
from agentready.services import Scanner, Scorer, LanguageDetector
from agentready.reporters import HTMLReporter, MarkdownReporter, JSONReporter
```

---

## Core Models

### Repository

Represents a git repository being assessed.

```python
from agentready.models import Repository

class Repository:
    """Immutable representation of a repository."""

    path: str                    # Absolute path to repository
    name: str                    # Repository name
    languages: Dict[str, int]    # Language → file count mapping
```

#### Constructor

```python
Repository(
    path: str,
    name: str,
    languages: Dict[str, int]
)
```

#### Example

```python
repo = Repository(
    path="/home/user/myproject",
    name="myproject",
    languages={"Python": 42, "JavaScript": 18}
)
```

---

### Attribute

Defines a single agent-ready attribute to assess.

```python
from agentready.models import Attribute

class Attribute:
    """Immutable attribute definition."""

    id: str              # Unique identifier (e.g., "claude_md_file")
    name: str            # Display name
    tier: int            # Tier 1-4 (1 = most important)
    weight: float        # Weight in scoring (0.0-1.0, sum to 1.0 across all)
    category: str        # Category (e.g., "Documentation", "Testing")
    description: str     # What this attribute measures
    rationale: str       # Why it matters for AI agents
```

#### Constructor

```python
Attribute(
    id: str,
    name: str,
    tier: int,
    weight: float,
    category: str = "",
    description: str = "",
    rationale: str = ""
)
```

#### Example

```python
attribute = Attribute(
    id="claude_md_file",
    name="CLAUDE.md File",
    tier=1,
    weight=0.10,
    category="Context Window Optimization",
    description="CLAUDE.md file at repository root",
    rationale="Provides immediate project context to AI agents"
)
```

---

### Finding

Result of assessing a single attribute.

```python
from agentready.models import Finding, Remediation

class Finding:
    """Assessment finding for a single attribute."""

    attribute: Attribute      # Attribute being assessed
    status: str              # "pass", "fail", or "skipped"
    score: float             # 0.0-100.0
    evidence: str            # What was found (specific details)
    remediation: Optional[Remediation]  # How to fix (if failed)
    reason: Optional[str]    # Why skipped (if status="skipped")
```

#### Factory Methods

```python
# Create passing finding
Finding.create_pass(
    attribute: Attribute,
    evidence: str,
    remediation: Optional[Remediation] = None
) -> Finding

# Create failing finding
Finding.create_fail(
    attribute: Attribute,
    evidence: str,
    remediation: Remediation
) -> Finding

# Create skipped finding
Finding.create_skip(
    attribute: Attribute,
    reason: str
) -> Finding
```

#### Example

```python
# Pass
finding = Finding.create_pass(
    attribute=claude_md_attr,
    evidence="Found CLAUDE.md at repository root (245 lines)"
)

# Fail
finding = Finding.create_fail(
    attribute=readme_attr,
    evidence="README.md missing quick start section",
    remediation=Remediation(
        steps=["Add Quick Start section to README.md"],
        tools=["text editor"],
        examples=["# Quick Start\n\nInstall: `pip install myproject`"]
    )
)

# Skip
finding = Finding.create_skip(
    attribute=container_attr,
    reason="Assessor not yet implemented"
)
```

---

### Remediation

Actionable guidance for fixing a failed attribute.

```python
from agentready.models import Remediation

class Remediation:
    """Remediation guidance for failed findings."""

    steps: List[str]           # Ordered steps to fix
    tools: List[str]           # Required tools
    commands: List[str]        # Shell commands (optional)
    examples: List[str]        # Code/config examples (optional)
    citations: List[str]       # Reference documentation (optional)
```

#### Example

```python
remediation = Remediation(
    steps=[
        "Install pre-commit framework",
        "Create .pre-commit-config.yaml",
        "Add black and isort hooks",
        "Install git hooks: pre-commit install"
    ],
    tools=["pre-commit", "black", "isort"],
    commands=[
        "pip install pre-commit",
        "pre-commit install",
        "pre-commit run --all-files"
    ],
    examples=[
        '''repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black'''
    ],
    citations=[
        "https://pre-commit.com/",
        "Memfault: Automatically format and lint code with pre-commit"
    ]
)
```

---

### Assessment

Complete assessment result for a repository.

```python
from agentready.models import Assessment

class Assessment:
    """Complete assessment result."""

    repository: Repository           # Repository assessed
    overall_score: float            # 0.0-100.0
    certification_level: str        # "Platinum", "Gold", "Silver", "Bronze", "Needs Improvement"
    findings: List[Finding]         # Individual attribute findings
    tier_scores: Dict[str, float]   # Tier 1-4 scores
    metadata: Dict[str, Any]        # Timestamp, version, duration, etc.
```

#### Properties

```python
assessment.passing_count -> int      # Number of passing attributes
assessment.failing_count -> int      # Number of failing attributes
assessment.skipped_count -> int      # Number of skipped attributes
```

---

## Services

### Scanner

Orchestrates repository assessment by running all assessors.

```python
from agentready.services import Scanner

class Scanner:
    """Assessment orchestration."""

    def __init__(self):
        """Initialize scanner with all assessors."""

    def scan(self, repository: Repository) -> Assessment:
        """
        Run all assessors and generate assessment.

        Args:
            repository: Repository to assess

        Returns:
            Complete Assessment object
        """
```

#### Example

```python
from agentready.services import Scanner, LanguageDetector
from agentready.models import Repository

# Detect languages
detector = LanguageDetector()
languages = detector.detect("/path/to/repo")

# Create repository object
repo = Repository(
    path="/path/to/repo",
    name="myproject",
    languages=languages
)

# Run assessment
scanner = Scanner()
assessment = scanner.scan(repo)

print(f"Score: {assessment.overall_score}/100")
print(f"Certification: {assessment.certification_level}")
print(f"Passing: {assessment.passing_count}/25")
```

---

### Scorer

Calculates weighted scores and certification levels.

```python
from agentready.services import Scorer

class Scorer:
    """Score calculation and certification determination."""

    @staticmethod
    def calculate_overall_score(findings: List[Finding]) -> float:
        """
        Calculate weighted average score.

        Args:
            findings: List of assessment findings

        Returns:
            Overall score (0.0-100.0)
        """

    @staticmethod
    def determine_certification(score: float) -> str:
        """
        Determine certification level from score.

        Args:
            score: Overall score (0.0-100.0)

        Returns:
            Certification level string
        """

    @staticmethod
    def calculate_tier_scores(findings: List[Finding]) -> Dict[str, float]:
        """
        Calculate scores by tier.

        Args:
            findings: List of assessment findings

        Returns:
            Dict mapping tier (e.g., "tier_1") to score
        """
```

#### Example

```python
from agentready.services import Scorer

# Calculate overall score
score = Scorer.calculate_overall_score(findings)
print(f"Score: {score}/100")

# Determine certification
cert = Scorer.determine_certification(score)
print(f"Certification: {cert}")

# Calculate tier scores
tier_scores = Scorer.calculate_tier_scores(findings)
for tier, score in tier_scores.items():
    print(f"{tier}: {score:.1f}/100")
```

---

### LanguageDetector

Detects programming languages in repository via `git ls-files`.

```python
from agentready.services import LanguageDetector

class LanguageDetector:
    """Detect repository languages via git."""

    def detect(self, repo_path: str) -> Dict[str, int]:
        """
        Detect languages by file extensions.

        Args:
            repo_path: Path to git repository

        Returns:
            Dict mapping language name to file count

        Raises:
            ValueError: If not a git repository
        """
```

#### Example

```python
from agentready.services import LanguageDetector

detector = LanguageDetector()
languages = detector.detect("/path/to/repo")

for lang, count in languages.items():
    print(f"{lang}: {count} files")

# Output:
# Python: 42 files
# JavaScript: 18 files
# TypeScript: 12 files
```

---

### BatchScanner

Assess multiple repositories in parallel for organizational insights.

```python
from agentready.services import BatchScanner

class BatchScanner:
    """Batch assessment across multiple repositories."""

    def __init__(self):
        """Initialize batch scanner."""

    def scan_batch(
        self,
        repository_paths: List[str],
        parallel: bool = True,
        max_workers: int = 4
    ) -> List[Assessment]:
        """
        Scan multiple repositories.

        Args:
            repository_paths: List of repository paths to assess
            parallel: Use parallel processing (default: True)
            max_workers: Maximum parallel workers (default: 4)

        Returns:
            List of Assessment objects, one per repository
        """
```

#### Example

```python
from agentready.services import BatchScanner

# Initialize batch scanner
batch_scanner = BatchScanner()

# Assess multiple repositories
assessments = batch_scanner.scan_batch([
    "/path/to/repo1",
    "/path/to/repo2",
    "/path/to/repo3"
], parallel=True, max_workers=4)

# Process results
for assessment in assessments:
    print(f"{assessment.repository.name}: {assessment.overall_score}/100 ({assessment.certification_level})")

# Calculate aggregate statistics
total_score = sum(a.overall_score for a in assessments)
average_score = total_score / len(assessments)
print(f"Average score across {len(assessments)} repos: {average_score:.1f}/100")
```

---

### SchemaValidator

Validate assessment reports against JSON schemas.

```python
from agentready.services import SchemaValidator

class SchemaValidator:
    """Validates assessment reports against JSON schemas."""

    def __init__(self):
        """Initialize validator with default schema."""

    def validate_report(
        self,
        report_data: dict,
        strict: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Validate report data against schema.

        Args:
            report_data: Assessment report as dictionary
            strict: Strict validation mode (disallow extra fields)

        Returns:
            Tuple of (is_valid, errors)
            - is_valid: True if report passes validation
            - errors: List of validation error messages
        """

    def validate_report_file(
        self,
        report_path: str,
        strict: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Validate report file against schema.

        Args:
            report_path: Path to JSON assessment report file
            strict: Strict validation mode

        Returns:
            Tuple of (is_valid, errors)
        """
```

#### Example

```python
from agentready.services import SchemaValidator
import json

validator = SchemaValidator()

# Validate report file
is_valid, errors = validator.validate_report_file(
    ".agentready/assessment-latest.json",
    strict=True
)

if is_valid:
    print("✅ Report is valid!")
else:
    print("❌ Validation failed:")
    for error in errors:
        print(f"  - {error}")

# Validate report data
with open(".agentready/assessment-latest.json") as f:
    report_data = json.load(f)

is_valid, errors = validator.validate_report(report_data, strict=False)
print(f"Lenient validation: {'PASS' if is_valid else 'FAIL'}")
```

---

### SchemaMigrator

Migrate assessment reports between schema versions.

```python
from agentready.services import SchemaMigrator

class SchemaMigrator:
    """Migrates assessment reports between schema versions."""

    def __init__(self):
        """Initialize migrator with supported versions."""

    def migrate_report(
        self,
        report_data: dict,
        to_version: str
    ) -> dict:
        """
        Migrate report data to target schema version.

        Args:
            report_data: Assessment report as dictionary
            to_version: Target schema version (e.g., "2.0.0")

        Returns:
            Migrated report data

        Raises:
            ValueError: If migration path not found
        """

    def migrate_report_file(
        self,
        input_path: str,
        output_path: str,
        to_version: str
    ) -> None:
        """
        Migrate report file to target schema version.

        Args:
            input_path: Path to source report file
            output_path: Path to save migrated report
            to_version: Target schema version

        Raises:
            ValueError: If migration path not found
            FileNotFoundError: If input file doesn't exist
        """

    def get_migration_path(
        self,
        from_version: str,
        to_version: str
    ) -> list[tuple[str, str]]:
        """
        Get migration path from source to target version.

        Args:
            from_version: Source schema version
            to_version: Target schema version

        Returns:
            List of (from_version, to_version) tuples representing migration steps

        Raises:
            ValueError: If no migration path exists
        """
```

#### Example

```python
from agentready.services import SchemaMigrator
import json

migrator = SchemaMigrator()

# Migrate report file
migrator.migrate_report_file(
    input_path="old-assessment.json",
    output_path="new-assessment.json",
    to_version="2.0.0"
)

# Migrate report data
with open("old-assessment.json") as f:
    old_data = json.load(f)

new_data = migrator.migrate_report(old_data, to_version="2.0.0")

# Check migration path
migration_steps = migrator.get_migration_path("1.0.0", "2.0.0")
print(f"Migration requires {len(migration_steps)} step(s):")
for from_ver, to_ver in migration_steps:
    print(f"  {from_ver} → {to_ver}")
```

---

## Assessors

### BaseAssessor

Abstract base class for all assessors. Implement this to create custom assessors.

```python
from abc import ABC, abstractmethod
from agentready.assessors.base import BaseAssessor
from agentready.models import Repository, Finding

class BaseAssessor(ABC):
    """Abstract base class for assessors."""

    @property
    @abstractmethod
    def attribute_id(self) -> str:
        """Unique attribute identifier."""

    @abstractmethod
    def assess(self, repository: Repository) -> Finding:
        """
        Assess repository for this attribute.

        Args:
            repository: Repository to assess

        Returns:
            Finding with pass/fail/skip status
        """

    def is_applicable(self, repository: Repository) -> bool:
        """
        Check if this assessor applies to repository.

        Override to skip assessment for irrelevant repositories
        (e.g., JavaScript-only repo for Python-specific assessor).

        Args:
            repository: Repository being assessed

        Returns:
            True if assessor should run, False to skip
        """
        return True

    def calculate_proportional_score(
        self,
        actual: float,
        target: float
    ) -> float:
        """
        Calculate proportional score for partial compliance.

        Args:
            actual: Actual value (e.g., 0.65 for 65% coverage)
            target: Target value (e.g., 0.80 for 80% target)

        Returns:
            Score (0-100)

        Example:
            >>> calculate_proportional_score(0.70, 0.80)
            87.5  # 70/80 = 87.5%
        """
```

#### Example: Custom Assessor

```python
from agentready.assessors.base import BaseAssessor
from agentready.models import Repository, Finding, Remediation

class MyCustomAssessor(BaseAssessor):
    """Assess my custom attribute."""

    @property
    def attribute_id(self) -> str:
        return "my_custom_attribute"

    def assess(self, repository: Repository) -> Finding:
        # Check if attribute is satisfied
        if self._check_condition(repository):
            return Finding.create_pass(
                self.attribute,
                evidence="Condition met",
                remediation=None
            )
        else:
            return Finding.create_fail(
                self.attribute,
                evidence="Condition not met",
                remediation=self._create_remediation()
            )

    def is_applicable(self, repository: Repository) -> bool:
        # Only apply to Python repositories
        return "Python" in repository.languages

    def _check_condition(self, repository: Repository) -> bool:
        # Custom assessment logic
        pass

    def _create_remediation(self) -> Remediation:
        return Remediation(
            steps=["Step 1", "Step 2"],
            tools=["tool1", "tool2"]
        )
```

---

## Reporters

### HTMLReporter

Generate interactive HTML reports.

```python
from agentready.reporters import HTMLReporter

class HTMLReporter:
    """Generate interactive HTML reports."""

    def generate(self, assessment: Assessment) -> str:
        """
        Generate HTML report.

        Args:
            assessment: Complete assessment result

        Returns:
            HTML string (self-contained, no external dependencies)
        """
```

#### Example

```python
from agentready.reporters import HTMLReporter

reporter = HTMLReporter()
html = reporter.generate(assessment)

# Save to file
with open("report.html", "w") as f:
    f.write(html)

print(f"HTML report saved: {len(html)} bytes")
```

---

### MarkdownReporter

Generate GitHub-Flavored Markdown reports.

```python
from agentready.reporters import MarkdownReporter

class MarkdownReporter:
    """Generate Markdown reports."""

    def generate(self, assessment: Assessment) -> str:
        """
        Generate Markdown report.

        Args:
            assessment: Complete assessment result

        Returns:
            Markdown string (GitHub-Flavored Markdown)
        """
```

#### Example

```python
from agentready.reporters import MarkdownReporter

reporter = MarkdownReporter()
markdown = reporter.generate(assessment)

# Save to file
with open("report.md", "w") as f:
    f.write(markdown)
```

---

### JSONReporter

Generate machine-readable JSON reports.

```python
from agentready.reporters import JSONReporter

class JSONReporter:
    """Generate JSON reports."""

    def generate(self, assessment: Assessment) -> str:
        """
        Generate JSON report.

        Args:
            assessment: Complete assessment result

        Returns:
            JSON string (formatted with indentation)
        """
```

#### Example

```python
from agentready.reporters import JSONReporter
import json

reporter = JSONReporter()
json_str = reporter.generate(assessment)

# Save to file
with open("assessment.json", "w") as f:
    f.write(json_str)

# Parse for programmatic access
data = json.loads(json_str)
print(f"Score: {data['overall_score']}")
print(f"Certification: {data['certification_level']}")
```

---

## Usage Examples

### Complete Assessment Workflow

```python
from agentready.services import Scanner, LanguageDetector
from agentready.models import Repository
from agentready.reporters import HTMLReporter, MarkdownReporter, JSONReporter

# 1. Detect languages
detector = LanguageDetector()
languages = detector.detect("/path/to/repo")

# 2. Create repository object
repo = Repository(
    path="/path/to/repo",
    name="myproject",
    languages=languages
)

# 3. Run assessment
scanner = Scanner()
assessment = scanner.scan(repo)

# 4. Generate reports
html_reporter = HTMLReporter()
md_reporter = MarkdownReporter()
json_reporter = JSONReporter()

html = html_reporter.generate(assessment)
markdown = md_reporter.generate(assessment)
json_str = json_reporter.generate(assessment)

# 5. Save reports
with open("report.html", "w") as f:
    f.write(html)

with open("report.md", "w") as f:
    f.write(markdown)

with open("assessment.json", "w") as f:
    f.write(json_str)

# 6. Print summary
print(f"Assessment complete!")
print(f"Score: {assessment.overall_score}/100")
print(f"Certification: {assessment.certification_level}")
print(f"Passing: {assessment.passing_count}/{len(assessment.findings)}")
```

---

### CI/CD Integration

```python
import sys
from agentready.services import Scanner, LanguageDetector
from agentready.models import Repository

# Assess repository
detector = LanguageDetector()
languages = detector.detect(".")

repo = Repository(path=".", name="myproject", languages=languages)
scanner = Scanner()
assessment = scanner.scan(repo)

# Fail build if score < 70
if assessment.overall_score < 70:
    print(f"❌ AgentReady score too low: {assessment.overall_score}/100")
    print(f"Minimum required: 70/100")
    sys.exit(1)
else:
    print(f"✅ AgentReady score: {assessment.overall_score}/100")
    sys.exit(0)
```

---

### Custom Filtering

```python
# Filter findings by status
passing = [f for f in assessment.findings if f.status == "pass"]
failing = [f for f in assessment.findings if f.status == "fail"]
skipped = [f for f in assessment.findings if f.status == "skipped"]

print(f"Passing: {len(passing)}")
print(f"Failing: {len(failing)}")
print(f"Skipped: {len(skipped)}")

# Find Tier 1 failures (highest priority)
tier1_failures = [
    f for f in failing
    if f.attribute.tier == 1
]

for finding in tier1_failures:
    print(f"❌ {finding.attribute.name}")
    print(f"   {finding.evidence}")
    if finding.remediation:
        print(f"   Fix: {finding.remediation.steps[0]}")
```

---

### Historical Tracking

```python
import json
import glob
from datetime import datetime

# Load all historical assessments
assessments = []
for file in sorted(glob.glob(".agentready/assessment-*.json")):
    with open(file) as f:
        data = json.load(f)
        assessments.append(data)

# Track score progression
print("Score history:")
for a in assessments:
    timestamp = a["metadata"]["timestamp"]
    score = a["overall_score"]
    cert = a["certification_level"]
    print(f"{timestamp}: {score:.1f}/100 ({cert})")

# Calculate improvement
if len(assessments) >= 2:
    initial = assessments[0]["overall_score"]
    latest = assessments[-1]["overall_score"]
    improvement = latest - initial
    print(f"\nTotal improvement: +{improvement:.1f} points")
```

---

### Custom Weight Configuration

```python
from agentready.services import Scanner
from agentready.models import Repository

# Override default weights programmatically
custom_weights = {
    "claude_md_file": 0.15,      # Increase from 0.10
    "readme_structure": 0.12,    # Increase from 0.10
    "type_annotations": 0.08,    # Decrease from 0.10
    # ... other attributes
}

# Note: Full weight customization requires modifying
# attribute definitions before scanner initialization.
# Typically done via .agentready-config.yaml file.

# For programmatic use, you can filter/reweight findings
# after assessment:
assessment = scanner.scan(repo)

# Custom scoring logic
def custom_score(findings, weights):
    total = 0.0
    for finding in findings:
        attr_id = finding.attribute.id
        weight = weights.get(attr_id, finding.attribute.weight)
        total += finding.score * weight
    return total

score = custom_score(assessment.findings, custom_weights)
print(f"Custom weighted score: {score}/100")
```

---

## Type Annotations

All AgentReady APIs include full type annotations for excellent IDE support:

```python
from agentready.models import Repository, Assessment, Finding
from agentready.services import Scanner

def assess_repository(repo_path: str) -> Assessment:
    """Assess repository and return results."""
    # Type hints enable autocomplete and type checking
    detector: LanguageDetector = LanguageDetector()
    languages: Dict[str, int] = detector.detect(repo_path)

    repo: Repository = Repository(
        path=repo_path,
        name=Path(repo_path).name,
        languages=languages
    )

    scanner: Scanner = Scanner()
    assessment: Assessment = scanner.scan(repo)

    return assessment
```

Use with mypy for static type checking:

```bash
mypy your_script.py
```

---

## Error Handling

AgentReady follows defensive programming principles:

```python
from agentready.services import LanguageDetector

try:
    detector = LanguageDetector()
    languages = detector.detect("/path/to/repo")
except ValueError as e:
    print(f"Error: {e}")
    # Typically: "Not a git repository"

except FileNotFoundError as e:
    print(f"Error: {e}")
    # Path does not exist

except Exception as e:
    print(f"Unexpected error: {e}")
```

**Best practices**:

- Assessors fail gracefully (return "skipped" if tools missing)
- Scanner continues on individual assessor errors
- Reports always generated (even with partial results)

---

## Next Steps

- **[User Guide](user-guide.md)** — CLI usage and configuration
- **[Developer Guide](developer-guide.md)** — Implementing custom assessors
- **[Attributes](attributes.md)** — Complete attribute reference
- **[Examples](examples.md)** — Real-world integration examples

---

**Questions?** Open an issue on [GitHub](https://github.com/ambient-code/agentready/issues).
