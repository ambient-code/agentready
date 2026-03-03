---
layout: page
title: Examples
---

Real-world AgentReady assessments demonstrating report formats, interpretation guidance, and remediation patterns.

## Table of Contents

- [AgentReady Self-Assessment](#agentready-self-assessment)
- [Report Interpretation Guide](#report-interpretation-guide)
- [Common Remediation Patterns](#common-remediation-patterns)
- [Integration Examples](#integration-examples)

---

## AgentReady Self-Assessment

AgentReady assesses itself to validate the scoring algorithm and demonstrate expected output.

### Assessment Summary

**Date**: 2025-11-23
**Score**: 80.0/100
**Certification**: 🥇 Gold
**Version**: v1.27.2

**Breakdown**:

- Attributes Assessed: 19/31 (22 implemented, 9 stubs, 12 not applicable to AgentReady)
- Passing: 8/10
- Failing: 2/10
- Skipped: 15/25

### Tier Scores

| Tier | Score | Weighted Contribution |
|------|-------|----------------------|
| Tier 1 (Essential) | 85.0/100 | 42.5/50 points |
| Tier 2 (Critical) | 75.0/100 | 22.5/30 points |
| Tier 3 (Important) | 100.0/100 | 15.0/15 points |
| Tier 4 (Advanced) | 0.0/100 | 0.0/5 points |

**Analysis**: Excellent essential attributes (Tier 1), strong documentation and code quality. Recent v1.27.2 improvements resolved 35 pytest failures and enhanced model validation. Tier 4 attributes not yet implemented.

### Passing Attributes (7)

#### 1. ✅ CLAUDE.md File (Tier 1, 10%)

**Evidence**: Found CLAUDE.md at repository root (482 lines)

**Why it passes**: Comprehensive project documentation covering:

- Tech stack (Python 3.12+, pytest, black, isort, ruff)
- Repository structure (src/, tests/, docs/, examples/)
- Standard commands (setup, test, lint, format)
- Development workflow (GitHub Flow, feature branches)
- Testing strategy (unit, integration, contract tests)

**Impact**: Immediate project context for AI agents, ~40% reduction in prompt engineering.

---

#### 2. ✅ README Structure (Tier 1, 10%)

**Evidence**: Well-structured README.md with all essential sections

**Sections present**:

- ✅ Project title and description
- ✅ Installation instructions (pip install)
- ✅ Quick start with code examples
- ✅ Feature overview (25 attributes, tier-based scoring)
- ✅ CLI reference
- ✅ Architecture overview
- ✅ Development setup
- ✅ License (MIT)

**Impact**: Fast project comprehension for both users and AI agents.

---

#### 3. ✅ Type Annotations (Tier 1, 10%)

**Evidence**: Python type hints present in 95% of functions

**Examples from codebase**:

```python
def assess(self, repository: Repository) -> Finding:
    """Assess repository for this attribute."""

def calculate_overall_score(findings: List[Finding]) -> float:
    """Calculate weighted average score."""

class Repository:
    path: str
    name: str
    languages: Dict[str, int]
```

**Impact**: Better AI comprehension, type-safe refactoring, improved autocomplete.

---

#### 4. ✅ Standard Layout (Tier 2, 3%)

**Evidence**: Follows Python src/ layout convention

**Structure**:

```
agentready/
├── src/agentready/    # Source code
├── tests/             # Tests mirror src/
├── docs/              # Documentation
├── examples/          # Example reports
├── pyproject.toml     # Package config
└── README.md          # Entry point
```

**Impact**: Predictable file locations, AI navigates efficiently.

---

#### 5. ✅ Test Coverage (Tier 2, 3%)

**Evidence**: 37% coverage with focused unit tests

**Coverage details**:

- Unit tests for models: 95% coverage
- Assessor tests: 60% coverage
- Integration tests: End-to-end workflow
- Total lines covered: 890/2400

**Note**: While below 80% target, core logic (models, scoring) has excellent coverage. Future work: expand assessor coverage.

**Impact**: Safety net for AI-assisted refactoring of critical paths.

---

#### 6. ✅ Gitignore Completeness (Tier 2, 3%)

**Evidence**: Comprehensive .gitignore covering all necessary patterns

**Excluded**:

- ✅ Python artifacts (\_\_pycache\_\_, \*.pyc, \*.pyo, .pytest\_cache)
- ✅ Virtual environments (.venv, venv, env)
- ✅ IDE files (.vscode/, .idea/, \*.swp)
- ✅ OS files (.DS\_Store, Thumbs.db)
- ✅ Build artifacts (dist/, build/, \*.egg-info)
- ✅ Reports (.agentready/)

**Impact**: Clean repository, no context pollution for AI.

---

#### 7. ✅ Cyclomatic Complexity (Tier 3, 1.5%)

**Evidence**: Low complexity across codebase (average: 4.2, max: 12)

**Analysis** (via radon):

- Functions with complexity >10: 2/180 (1%)
- Average complexity: 4.2 (excellent)
- Most complex function: `Scanner.scan()` (12)

**Impact**: Easy comprehension for AI, low cognitive load.

---

### Failing Attributes (3)

#### 1. ❌ Lock Files (Tier 2, 3%)

**Evidence**: No requirements.txt, poetry.lock, or uv.lock present

**Why it fails**: Intentional decision for library projects (libraries specify version ranges, not exact pins). Applications should have lock files.

**Remediation** (if this were an application):

```bash
# Using poetry
poetry lock

# Using pip
pip freeze > requirements.txt

# Using uv
uv pip compile pyproject.toml -o requirements.txt
```

**Note**: This is acceptable for libraries. AgentReady recognizes this pattern and adjusts scoring accordingly in future versions.

---

#### 2. ❌ Pre-commit Hooks (Tier 2, 3%)

**Evidence**: No .pre-commit-config.yaml found

**Why it fails**: Missing automation for code quality enforcement. Currently relying on manual `black`, `isort`, `ruff` runs.

**Remediation**:

1. **Install pre-commit**:

   ```bash
   pip install pre-commit
   ```

2. **Create .pre-commit-config.yaml**:

   ```yaml
   repos:
     - repo: https://github.com/psf/black
       rev: 23.12.0
       hooks:
         - id: black

     - repo: https://github.com/pycqa/isort
       rev: 5.13.0
       hooks:
         - id: isort

     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.9
       hooks:
         - id: ruff
   ```

3. **Install hooks**:

   ```bash
   pre-commit install
   ```

4. **Test**:

   ```bash
   pre-commit run --all-files
   ```

**Impact**: +3 points (78.4/100 total, still Gold)

**Priority**: P0 fix (identified in BACKLOG.md)

---

#### 3. ❌ Conventional Commits (Tier 3, 1.5%)

**Evidence**: Git history uses conventional commits, but not enforced via tooling

**Sample commits**:

- ✅ `feat(assessors): add inline documentation assessor`
- ✅ `fix: correct type annotation detection in Python 3.12`
- ✅ `docs: update CLAUDE.md with architecture details`

**Why it fails**: No commitlint or automated enforcement (could be bypassed).

**Remediation**:

1. **Install commitlint**:

   ```bash
   npm install -g @commitlint/cli @commitlint/config-conventional
   ```

2. **Create commitlint.config.js**:

   ```javascript
   module.exports = {extends: ['@commitlint/config-conventional']};
   ```

3. **Add to pre-commit hooks**:

   ```yaml
   - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
     rev: v9.5.0
     hooks:
       - id: commitlint
         stages: [commit-msg]
   ```

**Impact**: +1.5 points (76.9/100 total)

**Priority**: P1 enhancement

---

### Next Steps for AgentReady

**Immediate improvements** (would reach 79.9/100):

1. Add pre-commit hooks (+3 points)
2. Enforce conventional commits (+1.5 points)

**Path to Platinum (90+)**:

1. Expand 9 remaining stub assessors to full implementations
2. Increase test coverage to 80%+
3. Add GitHub Actions CI/CD workflow
4. Implement remaining Tier 4 attributes

---

## Batch Assessment Example

**Scenario**: Assess 5 microservices in a multi-repo project.

### Setup

```bash
# Directory structure
projects/
├── service-auth/
├── service-api/
├── service-data/
├── service-web/
└── service-worker/
```

### Running Batch Assessment

```bash
cd projects/
agentready batch service-*/ --output-dir ./batch-reports
```

### Results

**comparison-summary.md excerpt:**

```markdown
# Batch Assessment Summary

**Date**: 2025-11-23
**Repositories Assessed**: 5
**Average Score**: 73.4/100
**Certification Distribution**:
- Gold: 3 repositories
- Silver: 2 repositories

## Comparison Table

| Repository | Overall Score | Cert Level | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------------|---------------|------------|--------|--------|--------|--------|
| service-auth | 82.5/100 | Gold | 90.0 | 80.0 | 75.0 | 60.0 |
| service-api | 78.0/100 | Gold | 85.0 | 75.0 | 70.0 | 55.0 |
| service-web | 76.2/100 | Gold | 80.0 | 75.0 | 72.0 | 58.0 |
| service-data | 68.5/100 | Silver | 75.0 | 65.0 | 60.0 | 50.0 |
| service-worker | 61.8/100 | Silver | 70.0 | 60.0 | 55.0 | 45.0 |

## Common Failures

- **pre_commit_hooks** (4/5 repos): Missing .pre-commit-config.yaml
- **lock_files** (3/5 repos): No dependency lock files
- **conventional_commits** (3/5 repos): No commitlint enforcement

## Recommendations

1. **High Priority**: Add pre-commit hooks to all services (+3-5 points each)
2. **Medium Priority**: Add lock files to services without them (+3 points each)
3. **Quick Win**: Run `agentready bootstrap .` in each service for automated setup
```

**aggregate-stats.json:**

```json
{
  "total_repositories": 5,
  "average_score": 73.4,
  "median_score": 76.2,
  "score_range": {
    "min": 61.8,
    "max": 82.5,
    "spread": 20.7
  },
  "certification_distribution": {
    "Platinum": 0,
    "Gold": 3,
    "Silver": 2,
    "Bronze": 0,
    "Needs Improvement": 0
  },
  "tier_averages": {
    "tier_1": 80.0,
    "tier_2": 71.0,
    "tier_3": 66.4,
    "tier_4": 53.6
  },
  "common_failures": [
    {
      "attribute": "pre_commit_hooks",
      "failure_count": 4,
      "failure_rate": 0.80
    },
    {
      "attribute": "lock_files",
      "failure_count": 3,
      "failure_rate": 0.60
    },
    {
      "attribute": "conventional_commits",
      "failure_count": 3,
      "failure_rate": 0.60
    }
  ],
  "outliers": {
    "high_performers": ["service-auth"],
    "low_performers": ["service-worker"]
  }
}
```

### Action Plan

Based on batch assessment results:

**Week 1**: Fix common failures across all repos

```bash
# Add pre-commit hooks to all services
for service in service-*/; do
  cd $service
  agentready bootstrap . --dry-run  # Preview changes
  agentready bootstrap .            # Generate infrastructure
  pre-commit install
  cd ..
done
```

**Week 2**: Focus on low-performers (service-data, service-worker)

- Add lock files (poetry.lock or requirements.txt)
- Improve README structure
- Add type annotations to core modules

**Week 3**: Re-assess and track improvement

```bash
agentready batch service-*/ --output-dir ./batch-reports-week3
# Compare with initial assessment
```

**Expected Impact**: +8-12 points average score improvement

---

## Report Interpretation Guide

### Understanding Your Score

#### Certification Levels

| Level | Range | Meaning |
|-------|-------|---------|
| 🏆 Platinum | 90-100 | Exemplary agent-ready codebase |
| 🥇 Gold | 75-89 | Highly optimized for AI agents |
| 🥈 Silver | 60-74 | Well-suited for AI development |
| 🥉 Bronze | 40-59 | Basic agent compatibility |
| 📈 Needs Improvement | 0-39 | Significant friction for AI agents |

**What the ranges mean**:

- **90+**: World-class. Few improvements possible.
- **75-89**: Excellent foundation. Some gaps in advanced areas.
- **60-74**: Good baseline. Missing some critical attributes.
- **40-59**: Functional but friction-heavy. Major improvements needed.
- **<40**: Difficult for AI agents. Focus on essential attributes first.

---

### Reading the HTML Report

#### 1. Score Card (Top Section)

**Overall Score**: Weighted average across all attributes
**Certification Level**: Your badge (Platinum/Gold/Silver/Bronze)
**Visual Gauge**: Color-coded progress bar

**Tier Breakdown Table**:

- Shows score for each tier
- Weighted contribution to overall score
- Quickly identifies weak areas

**Example interpretation**:

- Tier 1: 80/100 → Contributing 40/50 points (good)
- Tier 2: 50/100 → Contributing 15/30 points (needs work)
- Tier 3: 100/100 → Contributing 15/15 points (perfect)
- Tier 4: 0/100 → Contributing 0/5 points (not critical)

**Analysis**: Focus on Tier 2 for highest impact (+15 points possible).

---

#### 2. Attribute Table (Middle Section)

**Columns**:

- **Status**: ✅ Pass, ❌ Fail, ⊘ Skipped
- **Attribute**: Name and ID
- **Tier**: 1-4 (importance)
- **Weight**: Percentage contribution to score
- **Score**: 0-100 for this attribute
- **Evidence**: What was found

**Sorting**:

- By score (ascending): See worst attributes first
- By tier: Focus on high-tier failures
- By weight: Maximize point gains

**Filtering**:

- "Failed only": Focus on remediation opportunities
- "Tier 1 only": Essential attributes
- Search: Find specific attribute by name

---

#### 3. Detailed Findings (Expandable Sections)

Click any attribute to expand:

**For passing attributes**:

- Evidence of compliance
- Examples from your codebase
- Why this matters for AI agents

**For failing attributes**:

- Specific evidence of what's missing
- **Remediation section**:
  - Ordered steps to fix
  - Required tools
  - Copy-paste ready commands
  - Code/config examples
  - Reference citations

**For skipped attributes**:

- Reason (not applicable, not implemented, or tool missing)

---

### Prioritizing Improvements

#### Strategy 1: Maximize Points (Tier × Weight)

Focus on high-tier, high-weight failures:

1. **Calculate potential gain**: `weight × (100 - current_score)`
2. **Sort by potential gain** (descending)
3. **Fix top 3-5 attributes**

**Example**:

- ❌ CLAUDE.md (Tier 1, 10%, score 0) → +10 points
- ❌ Pre-commit hooks (Tier 2, 3%, score 0) → +3 points
- ❌ Type annotations (Tier 1, 10%, score 50) → +5 points

**Best ROI**: Fix CLAUDE.md first (+10), then type annotations (+5).

---

#### Strategy 2: Quick Wins (<1 hour)

Some attributes are fast to fix:

**<15 minutes**:

- Create CLAUDE.md (outline version)
- Add .gitignore from template
- Create .env.example

**<30 minutes**:

- Add README sections
- Configure pre-commit hooks
- Add PR/issue templates

**<1 hour**:

- Write initial tests
- Add type hints to 10 key functions
- Create ADR template

---

#### Strategy 3: Foundational First (Tier 1)

Ensure all Tier 1 attributes pass before moving to Tier 2:

**Tier 1 checklist**:

- [ ] CLAUDE.md exists and comprehensive
- [ ] README has all essential sections
- [ ] Type annotations >80% coverage
- [ ] Standard project layout
- [ ] Lock file committed

**Why**: Tier 1 = 50% of score. Missing one Tier 1 attribute (-10 points) hurts more than missing five Tier 4 attributes (-5 points total).

---

## Common Remediation Patterns

### Pattern 1: Documentation Gaps

**Symptoms**:

- Missing CLAUDE.md
- Incomplete README
- No inline documentation

**Solution Template**:

1. **Create CLAUDE.md** (15 min):

   ```markdown
   # Tech Stack
   - [Language] [Version]
   - [Framework] [Version]

   # Standard Commands
   - Setup: [command]
   - Test: [command]
   - Build: [command]

   # Repository Structure
   - src/ - [description]
   - tests/ - [description]
   ```

2. **Enhance README** (30 min):
   - Add Quick Start section
   - Include code examples
   - Document installation steps

3. **Add docstrings** (ongoing):

   ```python
   def function_name(param: Type) -> ReturnType:
       """
       Brief description.

       Args:
           param: Description

       Returns:
           Description
       """
   ```

---

### Pattern 2: Missing Automation

**Symptoms**:

- No pre-commit hooks
- No CI/CD
- Manual testing only

**Solution Template**:

1. **Pre-commit hooks** (15 min):

   ```bash
   pip install pre-commit
   pre-commit sample-config > .pre-commit-config.yaml
   # Edit to add language-specific hooks
   pre-commit install
   ```

2. **GitHub Actions** (30 min):

   ```yaml
   # .github/workflows/ci.yml
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v4
         - run: pip install -e ".[dev]"
         - run: pytest --cov
         - run: black --check .
   ```

3. **Automated dependency updates** (10 min):

   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

---

### Pattern 3: Code Quality Deficits

**Symptoms**:

- No type annotations
- High cyclomatic complexity
- Code smells

**Solution Template**:

1. **Add type hints incrementally**:

   ```bash
   # Install mypy
   pip install mypy

   # Check current state
   mypy src/

   # Add hints to 5 functions per day
   # Focus on public APIs first
   ```

2. **Reduce complexity**:

   ```bash
   # Measure complexity
   pip install radon
   radon cc src/ -a -nb

   # Refactor functions with CC >10
   # Extract helper functions
   # Replace nested ifs with early returns
   ```

3. **Eliminate code smells**:

   ```bash
   # Install SonarQube or use pylint
   pip install pylint
   pylint src/

   # Fix critical/high issues first
   # DRY violations: extract shared code
   # Long functions: split into smaller functions
   ```

---

## Integration Examples

### Example 1: GitHub Actions CI

Fail builds if AgentReady score drops below threshold:

```yaml
# .github/workflows/agentready.yml
name: AgentReady Assessment

on:
  pull_request:
  push:
    branches: [main]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install AgentReady
        run: pip install agentready

      - name: Run Assessment
        run: |
          agentready assess . --output-dir ./reports

      - name: Check Score Threshold
        run: |
          score=$(jq '.overall_score' .agentready/assessment-latest.json)
          echo "AgentReady Score: $score/100"

          if (( $(echo "$score < 70" | bc -l) )); then
            echo "❌ Score below threshold (70)"
            exit 1
          fi

          echo "✅ Score meets threshold"

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: agentready-report
          path: .agentready/report-latest.html
```

---

### Example 2: Pre-commit Hook

Run AgentReady assessment before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: agentready
        name: AgentReady Assessment
        entry: agentready assess .
        language: system
        pass_filenames: false
        always_run: true
```

**Note**: This runs on every commit (slow). Better to run in CI/CD and use pre-commit for formatting/linting only.

---

### Example 3: Badge in README

Display AgentReady score badge:

```markdown
# MyProject

![AgentReady Score](https://img.shields.io/badge/AgentReady-75.4%2F100-gold)

<!-- Update badge after each assessment -->
```

**Automation** (via GitHub Actions):

```yaml
- name: Update Badge
  run: |
    score=$(jq '.overall_score' .agentready/assessment-latest.json)
    cert=$(jq -r '.certification_level' .agentready/assessment-latest.json)

    # Update README badge via script
    ./scripts/update-badge.sh $score $cert
```

---

### Example 4: Historical Tracking

Track score improvements over time:

```python
# scripts/track-improvements.py
import json
import glob
import matplotlib.pyplot as plt
from datetime import datetime

# Load all assessments
assessments = []
for file in sorted(glob.glob('.agentready/assessment-*.json')):
    with open(file) as f:
        data = json.load(f)
        timestamp = datetime.fromisoformat(data['metadata']['timestamp'])
        score = data['overall_score']
        assessments.append((timestamp, score))

# Plot trend
timestamps, scores = zip(*assessments)
plt.plot(timestamps, scores, marker='o')
plt.xlabel('Date')
plt.ylabel('AgentReady Score')
plt.title('AgentReady Score Progression')
plt.ylim(0, 100)
plt.grid(True)
plt.savefig('agentready-trend.png')
print("Trend chart saved: agentready-trend.png")
```

---

## Next Steps

- **[User Guide](user-guide.md)** — Learn how to run assessments
- **[Developer Guide](developer-guide.md)** — Implement custom assessors
- **[Attributes](attributes.md)** — Complete attribute reference
- **[API Reference](api-reference.md)** — Integrate AgentReady programmatically

---

**View full reports**: Check out [`examples/self-assessment/`](https://github.com/ambient-code/agentready/tree/main/examples/self-assessment) in the repository for complete HTML, Markdown, and JSON reports.
