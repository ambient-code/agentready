---
layout: page
title: User Guide
---

# User Guide

Complete guide to installing, configuring, and using AgentReady to assess your repositories.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Bootstrap Your Repository](#bootstrap-your-repository) ⭐ **NEW**
  - [What is Bootstrap?](#what-is-bootstrap)
  - [When to Use Bootstrap vs Assess](#when-to-use-bootstrap-vs-assess)
  - [Step-by-Step Tutorial](#step-by-step-tutorial)
  - [Generated Files Explained](#generated-files-explained)
  - [Post-Bootstrap Checklist](#post-bootstrap-checklist)
- [Running Assessments](#running-assessments)
- [Understanding Reports](#understanding-reports)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **Python 3.11 or 3.12** (AgentReady supports versions N and N-1)
- **Git** (for repository analysis)
- **pip** or **uv** (Python package manager)

### Install from PyPI

```bash
# Using pip
pip install agentready

# Using uv (recommended)
uv pip install agentready

# Verify installation
agentready --version
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/ambient-code/agentready.git
cd agentready

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Or using uv
uv pip install -e .
```

### Development Installation

If you plan to contribute or modify AgentReady:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"

# Verify installation
pytest --version
black --version
```

---

## Quick Start

### Bootstrap-First Approach (Recommended)

Transform your repository with one command:

```bash
# Navigate to your repository
cd /path/to/your/repo

# Bootstrap infrastructure
agentready bootstrap .

# Review generated files
git status

# Commit and push
git add .
git commit -m "build: Bootstrap agent-ready infrastructure"
git push
```

**What happens:**

- ✅ GitHub Actions workflows created (tests, security, assessment)
- ✅ Pre-commit hooks configured
- ✅ Issue/PR templates added
- ✅ Dependabot enabled
- ✅ Assessment runs automatically on next PR

**Duration**: <60 seconds including review time.

[See detailed Bootstrap tutorial →](#bootstrap-your-repository)

### Batch Assessment Approach

Assess multiple repositories at once for organizational insights:

```bash
# Navigate to directory containing multiple repos
cd /path/to/repos

# Run batch assessment
agentready batch repo1/ repo2/ repo3/ --output-dir ./batch-reports

# View comparison report
open batch-reports/comparison-summary.html
```

**What you get:**

- ✅ Individual reports for each repository
- ✅ Comparison table showing scores side-by-side
- ✅ Aggregate statistics across all repositories
- ✅ Trend analysis for multi-repo projects

**Duration**: Varies by number of repositories (~5 seconds per repo).

[See detailed batch assessment guide →](#batch-assessment)

### Manual Assessment Approach

For one-time analysis without infrastructure changes:

```bash
# Navigate to your repository
cd /path/to/your/repo

# Run assessment
agentready assess .

# View the HTML report
open .agentready/report-latest.html  # macOS
xdg-open .agentready/report-latest.html  # Linux
start .agentready/report-latest.html  # Windows
```

**Output location**: `.agentready/` directory in your repository root.

**Duration**: Most assessments complete in under 5 seconds.

---

## Bootstrap Your Repository

### What is Bootstrap?

**Bootstrap is AgentReady's automated infrastructure generator.** Instead of manually implementing recommendations from assessment reports, Bootstrap creates complete GitHub setup in one command:

**Generated Infrastructure:**

- **GitHub Actions workflows** — Tests, security scanning, AgentReady assessment
- **Pre-commit hooks** — Language-specific formatters and linters
- **Issue/PR templates** — Structured bug reports, feature requests, PR checklist
- **CODEOWNERS** — Automated review assignments
- **Dependabot** — Weekly dependency updates
- **Contributing guidelines** — If not present
- **Code of Conduct** — Red Hat standard (if not present)

**Language Detection:**
Bootstrap automatically detects your primary language (Python, JavaScript, Go) via `git ls-files` and generates appropriate configurations.

**Safe to Use:**

- Use `--dry-run` to preview changes without creating files
- All files are created, never overwritten
- Review with `git status` before committing

---

### When to Use Bootstrap vs Assess

<table>
<thead>
<tr>
<th>Scenario</th>
<th>Use Bootstrap</th>
<th>Use Assess</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>New project</strong></td>
<td>✅ Start with best practices</td>
<td>Later, to track progress</td>
</tr>
<tr>
<td><strong>Missing GitHub Actions</strong></td>
<td>✅ Generate workflows instantly</td>
<td>Shows it's missing</td>
</tr>
<tr>
<td><strong>No pre-commit hooks</strong></td>
<td>✅ Configure automatically</td>
<td>Shows it's missing</td>
</tr>
<tr>
<td><strong>Understanding current state</strong></td>
<td>Use after bootstrapping</td>
<td>✅ Detailed analysis</td>
</tr>
<tr>
<td><strong>Existing infrastructure</strong></td>
<td>Safe (won't overwrite)</td>
<td>✅ Validate setup</td>
</tr>
<tr>
<td><strong>Tracking improvements</strong></td>
<td>One-time setup</td>
<td>✅ Run repeatedly</td>
</tr>
<tr>
<td><strong>CI/CD integration</strong></td>
<td>Generates the workflows</td>
<td>✅ Runs in CI (via Bootstrap)</td>
</tr>
</tbody>
</table>

**Recommended workflow:**

1. **Bootstrap first** — Generate infrastructure
2. **Review and commit** — Inspect generated files
3. **Assess automatically** — Every PR via GitHub Actions
4. **Manual assess** — When validating improvements

---

### Step-by-Step Tutorial

#### Step 1: Preview Changes (Dry Run)

Always start with `--dry-run` to see what will be created:

```bash
cd /path/to/your/repo
agentready bootstrap . --dry-run
```

**Example output:**

```
Detecting primary language...
✓ Detected: Python (42 files)

Files that will be created:
  .github/workflows/agentready-assessment.yml
  .github/workflows/tests.yml
  .github/workflows/security.yml
  .github/ISSUE_TEMPLATE/bug_report.md
  .github/ISSUE_TEMPLATE/feature_request.md
  .github/PULL_REQUEST_TEMPLATE.md
  .github/CODEOWNERS
  .github/dependabot.yml
  .pre-commit-config.yaml
  CONTRIBUTING.md (not present, will create)
  CODE_OF_CONDUCT.md (not present, will create)

Run without --dry-run to create these files.
```

**Review the list carefully:**

- Files marked "(not present, will create)" are new
- Existing files are never overwritten
- Check for conflicts with existing workflows

---

#### Step 2: Run Bootstrap

If dry-run output looks good, run without flag:

```bash
agentready bootstrap .
```

**Example output:**

```
Detecting primary language...
✓ Detected: Python (42 files)

Creating infrastructure...
  ✓ .github/workflows/agentready-assessment.yml
  ✓ .github/workflows/tests.yml
  ✓ .github/workflows/security.yml
  ✓ .github/ISSUE_TEMPLATE/bug_report.md
  ✓ .github/ISSUE_TEMPLATE/feature_request.md
  ✓ .github/PULL_REQUEST_TEMPLATE.md
  ✓ .github/CODEOWNERS
  ✓ .github/dependabot.yml
  ✓ .pre-commit-config.yaml
  ✓ CONTRIBUTING.md
  ✓ CODE_OF_CONDUCT.md

Bootstrap complete! 11 files created.

Next steps:
1. Review generated files: git status
2. Customize as needed (CODEOWNERS, workflow triggers, etc.)
3. Commit: git add . && git commit -m "build: Bootstrap infrastructure"
4. Enable GitHub Actions in repository settings
5. Push and create PR to see assessment in action!
```

---

#### Step 3: Review Generated Files

Inspect what was created:

```bash
# View all new files
git status

# Inspect key files
cat .github/workflows/agentready-assessment.yml
cat .pre-commit-config.yaml
cat .github/CODEOWNERS
```

**What to check:**

- **CODEOWNERS** — Add actual team member GitHub usernames
- **Workflows** — Adjust triggers (e.g., only main branch, specific paths)
- **Pre-commit hooks** — Add/remove tools based on your stack
- **Issue templates** — Customize labels and assignees

---

#### Step 4: Install Pre-commit Hooks (Local)

Bootstrap creates `.pre-commit-config.yaml`, but you must install locally:

```bash
# Install pre-commit (if not already)
pip install pre-commit

# Install git hooks
pre-commit install

# Test hooks on all files
pre-commit run --all-files
```

**Expected output:**

```
black....................................................................Passed
isort....................................................................Passed
ruff.....................................................................Passed
```

**If failures occur:**

- Review suggested fixes
- Run formatters: `black .` and `isort .`
- Fix linting errors: `ruff check . --fix`
- Re-run: `pre-commit run --all-files`

---

#### Step 5: Commit and Push

```bash
# Stage all generated files
git add .

# Commit with conventional commit message
git commit -m "build: Bootstrap agent-ready infrastructure

- Add GitHub Actions workflows (tests, security, assessment)
- Configure pre-commit hooks (black, isort, ruff)
- Add issue and PR templates
- Enable Dependabot for weekly updates
- Add CONTRIBUTING.md and CODE_OF_CONDUCT.md"

# Push to repository
git push origin main
```

---

#### Step 6: Enable GitHub Actions

If this is the first time using Actions:

1. **Navigate to repository on GitHub**
2. **Go to Settings → Actions → General**
3. **Enable Actions** (select "Allow all actions")
4. **Set workflow permissions** to "Read and write permissions"
5. **Save**

---

#### Step 7: Test with a PR

Create a test PR to see Bootstrap in action:

```bash
# Create feature branch
git checkout -b test-agentready-bootstrap

# Make trivial change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: Verify AgentReady assessment workflow"
git push origin test-agentready-bootstrap

# Create PR on GitHub
gh pr create --title "Test: AgentReady Bootstrap" --body "Testing automated assessment"
```

**What happens automatically:**

1. **Tests workflow** runs pytest (Python) or appropriate tests
2. **Security workflow** runs CodeQL analysis
3. **AgentReady assessment workflow** runs assessment and posts results as PR comment

**PR comment example:**

```
## AgentReady Assessment

**Score:** 75.4/100 (🥇 Gold)

**Tier Breakdown:**
- Tier 1 (Essential): 80/100
- Tier 2 (Critical): 70/100
- Tier 3 (Important): 65/100
- Tier 4 (Advanced): 50/100

**Passing:** 15/25 | **Failing:** 8/25 | **Skipped:** 2/25

[View full HTML report](link-to-artifact)
```

---

### Generated Files Explained

#### GitHub Actions Workflows

**`.github/workflows/agentready-assessment.yml`**

```yaml
# Runs on every PR and push to main
# Posts assessment results as PR comment
# Fails if score drops below configured threshold (default: 60)

Triggers: pull_request, push (main branch)
Duration: ~30 seconds
Artifacts: HTML report, JSON data
```

**`.github/workflows/tests.yml`**

```yaml
# Language-specific test workflow

Python:
  - Runs pytest with coverage
  - Coverage report posted as PR comment
  - Requires test/ directory

JavaScript:
  - Runs jest with coverage
  - Generates lcov report

Go:
  - Runs go test with race detection
  - Coverage profiling enabled
```

**`.github/workflows/security.yml`**

```yaml
# Comprehensive security scanning

CodeQL:
  - Analyzes code for vulnerabilities
  - Runs on push to main and PR
  - Supports 10+ languages

Dependency Scanning:
  - GitHub Advisory Database
  - Fails on high/critical vulnerabilities
```

---

#### Pre-commit Configuration

**`.pre-commit-config.yaml`**

Language-specific hooks configured:

**Python:**

- `black` — Code formatter (88 char line length)
- `isort` — Import sorter
- `ruff` — Fast linter
- `trailing-whitespace` — Remove trailing spaces
- `end-of-file-fixer` — Ensure newline at EOF

**JavaScript/TypeScript:**

- `prettier` — Code formatter
- `eslint` — Linter
- `trailing-whitespace`
- `end-of-file-fixer`

**Go:**

- `gofmt` — Code formatter
- `golint` — Linter
- `go-vet` — Static analysis

**To customize:**
Edit `.pre-commit-config.yaml` and adjust hook versions or add new repos.

---

#### GitHub Templates

**`.github/ISSUE_TEMPLATE/bug_report.md`**

- Structured bug report with reproduction steps
- Environment details (OS, version)
- Expected vs actual behavior
- Auto-labels as `bug`

**`.github/ISSUE_TEMPLATE/feature_request.md`**

- Structured feature proposal
- Use case and motivation
- Proposed solution
- Auto-labels as `enhancement`

**`.github/PULL_REQUEST_TEMPLATE.md`**

- Checklist for PR authors:
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] Passes all checks
  - [ ] Breaking changes documented
- Links to related issues
- Change description

**`.github/CODEOWNERS`**

```
# Auto-assign reviewers based on file paths
# CUSTOMIZE: Replace with actual GitHub usernames

* @yourteam/maintainers
/docs/ @yourteam/docs
/.github/ @yourteam/devops
```

**`.github/dependabot.yml`**

```yaml
# Weekly dependency update checks
# Creates PRs for outdated dependencies
# Supports Python, npm, Go modules

Updates:
  - package-ecosystem: pip (or npm, gomod)
    schedule: weekly
    labels: [dependencies]
```

---

#### Development Guidelines

**`CONTRIBUTING.md`** (created if missing)

- Setup instructions
- Development workflow
- Code style guidelines
- PR process
- Testing requirements

**`CODE_OF_CONDUCT.md`** (created if missing)

- Red Hat standard Code of Conduct
- Community guidelines
- Reporting process
- Enforcement policy

---

### Post-Bootstrap Checklist

After running `agentready bootstrap`, complete these steps:

#### 1. Customize CODEOWNERS

```bash
# Edit .github/CODEOWNERS
vim .github/CODEOWNERS

# Replace placeholder usernames with actual team members
# * @yourteam/maintainers  →  * @alice @bob
# /docs/ @yourteam/docs    →  /docs/ @carol
```

#### 2. Review Workflow Triggers

```bash
# Check if workflow triggers match your branching strategy
cat .github/workflows/*.yml | grep "on:"

# Common adjustments:
# - Change 'main' to 'master' or 'develop'
# - Add path filters (e.g., only run tests when src/ changes)
# - Adjust schedule (e.g., nightly instead of push)
```

#### 3. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Test on existing code
```

#### 4. Enable GitHub Actions

- Repository Settings → Actions → General
- Enable "Allow all actions"
- Set "Read and write permissions" for workflows

#### 5. Configure Branch Protection (Recommended)

- Settings → Branches → Add rule for `main`
- Require status checks: `tests`, `security`, `agentready-assessment`
- Require PR reviews (at least 1 approval)
- Require branches to be up to date

#### 6. Test the Workflows

Create a test PR to verify:

```bash
git checkout -b test-workflows
echo "# Test" >> README.md
git add README.md
git commit -m "test: Verify automated workflows"
git push origin test-workflows
gh pr create --title "Test: Verify workflows" --body "Testing Bootstrap"
```

**Verify:**

- ✅ All workflows run successfully
- ✅ AgentReady posts PR comment with assessment results
- ✅ Test coverage report appears
- ✅ Security scan completes without errors

#### 7. Update Documentation

Add Badge to README.md:

```markdown
# MyProject

![AgentReady](https://img.shields.io/badge/AgentReady-Bootstrap-blue)
![Tests](https://github.com/yourusername/repo/workflows/tests/badge.svg)
![Security](https://github.com/yourusername/repo/workflows/security/badge.svg)
```

Mention Bootstrap in README:

```markdown
## Development Setup

This repository uses AgentReady Bootstrap for automated quality assurance.

All PRs are automatically assessed for agent-readiness. See the PR comment
for detailed findings and remediation guidance.
```

---

### Language-Specific Notes

#### Python Projects

Bootstrap generates:

- `pytest` workflow with coverage (`pytest-cov`)
- Pre-commit hooks: `black`, `isort`, `ruff`, `mypy`
- Dependabot for pip dependencies

**Customizations:**

- Adjust `pytest` command in `tests.yml` if using different test directory
- Add `mypy` configuration in `pyproject.toml` if type checking required
- Modify `black` line length in `.pre-commit-config.yaml` if needed

#### JavaScript/TypeScript Projects

Bootstrap generates:

- `jest` or `npm test` workflow
- Pre-commit hooks: `prettier`, `eslint`
- Dependabot for npm dependencies

**Customizations:**

- Update test command in `tests.yml` to match `package.json` scripts
- Adjust `prettier` config (`.prettierrc`) if different style
- Add TypeScript type checking (`tsc --noEmit`) to workflow

#### Go Projects

Bootstrap generates:

- `go test` workflow with race detection
- Pre-commit hooks: `gofmt`, `golint`, `go-vet`
- Dependabot for Go modules

**Customizations:**

- Add build step to workflow if needed (`go build ./...`)
- Configure `golangci-lint` for advanced linting
- Add coverage reporting (`go test -coverprofile=coverage.out`)

---

### Bootstrap Command Reference

```bash
agentready bootstrap [REPOSITORY] [OPTIONS]
```

**Arguments:**

- `REPOSITORY` — Path to repository (default: current directory)

**Options:**

- `--dry-run` — Preview files without creating
- `--language TEXT` — Override auto-detection: `python|javascript|go|auto` (default: auto)

**Examples:**

```bash
# Bootstrap current directory (auto-detect language)
agentready bootstrap .

# Preview without creating files
agentready bootstrap . --dry-run

# Force Python configuration
agentready bootstrap . --language python

# Bootstrap different directory
agentready bootstrap /path/to/repo

# Combine dry-run and language override
agentready bootstrap /path/to/repo --dry-run --language go
```

**Exit codes:**

- `0` — Success
- `1` — Error (not a git repository, permission denied, etc.)

---

## Running Assessments

### Basic Usage

```bash
# Assess current directory
agentready assess .

# Assess specific repository
agentready assess /path/to/repo

# Assess with verbose output
agentready assess . --verbose

# Custom output directory
agentready assess . --output-dir ./custom-reports
```

### Assessment Output

AgentReady creates a `.agentready/` directory containing:

```
.agentready/
├── assessment-YYYYMMDD-HHMMSS.json    # Machine-readable data
├── report-YYYYMMDD-HHMMSS.html        # Interactive web report
├── report-YYYYMMDD-HHMMSS.md          # Markdown report
├── assessment-latest.json             # Symlink to latest
├── report-latest.html                 # Symlink to latest
└── report-latest.md                   # Symlink to latest
```

**Timestamps**: All files are timestamped for historical tracking.

**Latest links**: Symlinks always point to the most recent assessment.

### Verbose Mode

Get detailed progress information during assessment:

```bash
agentready assess . --verbose
```

**Output includes**:

- Repository path and detected languages
- Each assessor's execution status
- Finding summaries (pass/fail/skip)
- Final score calculation breakdown
- Report generation progress

---

## Batch Assessment

Assess multiple repositories in one command to gain organizational insights and identify patterns across projects.

### Basic Usage

```bash
# Assess all repos in a directory
agentready batch /path/to/repos --output-dir ./reports

# Assess specific repos
agentready batch /path/repo1 /path/repo2 /path/repo3

# Generate comparison report
agentready batch . --compare
```

### Batch Output

AgentReady batch assessment creates:

```
reports/
├── comparison-summary.html      # Interactive comparison table
├── comparison-summary.md        # Markdown summary
├── aggregate-stats.json         # Machine-readable statistics
├── repo1/
│   ├── assessment-latest.json
│   ├── report-latest.html
│   └── report-latest.md
├── repo2/
│   └── ...
└── repo3/
    └── ...
```

### Comparison Report Features

**comparison-summary.html** includes:

- Side-by-side score comparison table
- Certification level distribution (Platinum/Gold/Silver/Bronze)
- Average scores by tier
- Outlier detection (repos significantly above/below average)
- Sortable columns (by score, name, certification)
- Filterable view (show only failing repos)

**Example comparison table:**

| Repository | Overall Score | Cert Level | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------------|---------------|------------|--------|--------|--------|--------|
| agentready | 80.0/100 | Gold | 90.0 | 75.0 | 70.0 | 60.0 |
| project-a | 75.2/100 | Gold | 85.0 | 70.0 | 65.0 | 55.0 |
| project-b | 62.5/100 | Silver | 70.0 | 60.0 | 55.0 | 45.0 |

### Aggregate Statistics

**aggregate-stats.json** provides:

```json
{
  "total_repositories": 3,
  "average_score": 72.6,
  "median_score": 75.2,
  "certification_distribution": {
    "Platinum": 0,
    "Gold": 2,
    "Silver": 1,
    "Bronze": 0,
    "Needs Improvement": 0
  },
  "tier_averages": {
    "tier_1": 81.7,
    "tier_2": 68.3,
    "tier_3": 63.3,
    "tier_4": 53.3
  },
  "common_failures": [
    {"attribute": "pre_commit_hooks", "failure_rate": 0.67},
    {"attribute": "lock_files", "failure_rate": 0.33}
  ]
}
```

### Use Cases

**Organization-wide assessment**:

```bash
# Clone all org repos, then batch assess
gh repo list myorg --limit 100 --json name --jq '.[].name' | \
  xargs -I {} gh repo clone myorg/{}

agentready batch repos/* --output-dir ./org-assessment
```

**Multi-repo project**:

```bash
# Assess all microservices
agentready batch services/* --compare
```

**Trend tracking**:

```bash
# Monthly assessment
agentready batch repos/* --output-dir ./assessments/2025-11
```

---

## Report Validation & Migration

AgentReady v1.27.2 includes schema versioning for backwards compatibility and evolution.

### Validate Reports

Verify assessment reports conform to their schema version:

```bash
# Strict validation (default)
agentready validate-report .agentready/assessment-latest.json

# Lenient validation (allow extra fields)
agentready validate-report --no-strict .agentready/assessment-latest.json
```

**Output examples:**

**Valid report:**

```
✅ Report is valid!
Schema version: 1.0.0
Repository: agentready
Overall score: 80.0/100
```

**Invalid report:**

```
❌ Validation failed! 3 errors found:
  - Missing required field: 'schema_version'
  - Invalid type for 'overall_score': expected number, got string
  - Extra field not allowed in strict mode: 'custom_field'
```

### Migrate Reports

Convert reports between schema versions:

```bash
# Migrate to specific version
agentready migrate-report old-report.json --to 2.0.0

# Custom output path
agentready migrate-report old.json --to 2.0.0 --output new.json

# Explicit source version (auto-detected by default)
agentready migrate-report old.json --from 1.0.0 --to 2.0.0
```

**Migration output:**

```
🔄 Migrating report...
Source version: 1.0.0
Target version: 2.0.0

✅ Migration successful!
Migrated report saved to: assessment-20251123-migrated.json
```

### Schema Compatibility

**Current schema version**: 1.0.0

**Supported versions**:

- 1.0.0 (current)

**Future versions** will maintain backwards compatibility:

- Read old versions via migration
- Write new versions with latest schema
- Migration paths provided for all versions

[Learn more about schema versioning →](schema-versioning.html)

---

## Understanding Reports

AgentReady generates three complementary report formats.

### HTML Report (Interactive)

**File**: `report-YYYYMMDD-HHMMSS.html`

The HTML report provides an interactive, visual interface:

#### Features

- **Overall Score Card**: Certification level, score, and visual gauge
- **Tier Summary**: Breakdown by attribute tier (Essential/Critical/Important/Advanced)
- **Attribute Table**: Sortable, filterable list of all attributes
- **Detailed Findings**: Expandable sections for each attribute
- **Search**: Find specific attributes by name or ID
- **Filters**: Show only passed, failed, or skipped attributes
- **Copy Buttons**: One-click code example copying
- **Offline**: No CDN dependencies, works anywhere

#### How to Use

1. **Open in browser**: Double-click the HTML file
2. **Review overall score**: Check certification level and tier breakdown
3. **Explore findings**:
   - Green ✅ = Passed
   - Red ❌ = Failed (needs remediation)
   - Gray ⊘ = Skipped (not applicable or not yet implemented)
4. **Click to expand**: View detailed evidence and remediation steps
5. **Filter results**: Focus on specific attribute statuses
6. **Copy remediation commands**: Use one-click copy for code examples

#### Security

HTML reports include Content Security Policy (CSP) headers for defense-in-depth:

- Prevents unauthorized script execution
- Mitigates XSS attack vectors
- Safe to share and view in any browser

The CSP policy allows only inline styles and scripts needed for interactivity.

#### Sharing

The HTML report is self-contained and can be:

- Emailed to stakeholders
- Uploaded to internal wikis
- Viewed on any device with a browser
- Archived for compliance/audit purposes

### Markdown Report (Version Control Friendly)

**File**: `report-YYYYMMDD-HHMMSS.md`

The Markdown report is optimized for git tracking:

#### Features

- **GitHub-Flavored Markdown**: Renders beautifully on GitHub
- **Git-Diffable**: Track score improvements over time
- **ASCII Tables**: Attribute summaries without HTML
- **Emoji Indicators**: ✅❌⊘ for visual status
- **Certification Ladder**: Visual progress chart
- **Prioritized Next Steps**: Highest-impact improvements first

#### How to Use

1. **Commit to repository**:

   ```bash
   git add .agentready/report-latest.md
   git commit -m "docs: Add AgentReady assessment report"
   ```

2. **Track progress**:

   ```bash
   # Run new assessment
   agentready assess .

   # Compare to previous
   git diff .agentready/report-latest.md
   ```

3. **Review on GitHub**: Push and view formatted Markdown

4. **Share in PRs**: Reference in pull request descriptions

#### Recommended Workflow

```bash
# Initial baseline
agentready assess .
git add .agentready/report-latest.md
git commit -m "docs: AgentReady baseline (Score: 65.2)"

# Make improvements
# ... implement recommendations ...

# Re-assess
agentready assess .
git add .agentready/report-latest.md
git commit -m "docs: AgentReady improvements (Score: 72.8, +7.6)"
```

### JSON Report (Machine-Readable)

**File**: `assessment-YYYYMMDD-HHMMSS.json`

The JSON report contains complete assessment data:

#### Structure

```json
{
  "metadata": {
    "timestamp": "2025-11-21T10:30:00Z",
    "repository_path": "/path/to/repo",
    "agentready_version": "1.0.0",
    "duration_seconds": 2.35
  },
  "repository": {
    "path": "/path/to/repo",
    "name": "myproject",
    "languages": {"Python": 42, "JavaScript": 18}
  },
  "overall_score": 75.4,
  "certification_level": "Gold",
  "tier_scores": {
    "tier_1": 85.0,
    "tier_2": 70.0,
    "tier_3": 65.0,
    "tier_4": 50.0
  },
  "findings": [
    {
      "attribute_id": "claude_md_file",
      "attribute_name": "CLAUDE.md File",
      "tier": 1,
      "weight": 0.10,
      "status": "pass",
      "score": 100,
      "evidence": "Found CLAUDE.md at repository root",
      "remediation": null
    }
  ]
}
```

#### Use Cases

**CI/CD Integration**:

```bash
# Fail build if score < 70
score=$(jq '.overall_score' .agentready/assessment-latest.json)
if (( $(echo "$score < 70" | bc -l) )); then
  echo "AgentReady score too low: $score"
  exit 1
fi
```

**Trend Analysis**:

```python
import json
import glob

# Load all historical assessments
assessments = []
for file in sorted(glob.glob('.agentready/assessment-*.json')):
    with open(file) as f:
        assessments.append(json.load(f))

# Track score over time
for a in assessments:
    print(f"{a['metadata']['timestamp']}: {a['overall_score']}")
```

**Custom Reporting**:

```python
import json

with open('.agentready/assessment-latest.json') as f:
    assessment = json.load(f)

# Extract failed attributes
failed = [
    f for f in assessment['findings']
    if f['status'] == 'fail'
]

# Create custom report
for finding in failed:
    print(f"❌ {finding['attribute_name']}")
    print(f"   {finding['evidence']}")
    print()
```

---

## Configuration

### Default Behavior

AgentReady works out-of-the-box with sensible defaults. No configuration required for basic usage.

### Custom Configuration File

Create `.agentready-config.yaml` to customize:

```yaml
# Custom attribute weights (must sum to 1.0)
weights:
  claude_md_file: 0.15      # Increase from default 0.10
  readme_structure: 0.12    # Increase from default 0.10
  type_annotations: 0.08    # Decrease from default 0.10
  # ... other 22 attributes

# Exclude specific attributes
excluded_attributes:
  - performance_benchmarks  # Skip this assessment
  - container_setup         # Not applicable to our project

# Custom output directory
output_dir: ./reports

# Verbosity (true/false)
verbose: false
```

### Weight Customization Rules

1. **Must sum to 1.0**: Total weight across all attributes (excluding excluded ones)
2. **Minimum weight**: 0.01 (1%)
3. **Maximum weight**: 0.20 (20%)
4. **Automatic rebalancing**: Excluded attributes' weights redistribute proportionally

### Example: Security-Focused Configuration

```yaml
# Emphasize security attributes
weights:
  dependency_security: 0.15    # Default: 0.05
  secrets_management: 0.12     # Default: 0.05
  security_scanning: 0.10      # Default: 0.03
  # Other weights adjusted to sum to 1.0

excluded_attributes:
  - performance_benchmarks
```

### Example: Documentation-Focused Configuration

```yaml
# Emphasize documentation quality
weights:
  claude_md_file: 0.20         # Default: 0.10
  readme_structure: 0.15       # Default: 0.10
  inline_documentation: 0.12   # Default: 0.08
  api_documentation: 0.10      # Default: 0.05
  # Other weights adjusted to sum to 1.0
```

### Validate Configuration

```bash
# Validate configuration file
agentready --validate-config .agentready-config.yaml

# Generate example configuration
agentready --generate-config > .agentready-config.yaml
```

---

## CLI Reference

### Main Commands

#### `agentready assess PATH`

Assess a repository at the specified path.

**Arguments**:

- `PATH` — Repository path to assess (required)

**Options**:

- `--verbose, -v` — Show detailed progress information
- `--config FILE, -c FILE` — Use custom configuration file
- `--output-dir DIR, -o DIR` — Custom report output directory

**Examples**:

```bash
agentready assess .
agentready assess /path/to/repo
agentready assess . --verbose
agentready assess . --config custom.yaml
agentready assess . --output-dir ./reports
```

### Configuration Commands

#### `agentready --generate-config`

Generate example configuration file.

**Output**: Prints YAML configuration to stdout.

**Example**:

```bash
agentready --generate-config > .agentready-config.yaml
```

#### `agentready --validate-config FILE`

Validate configuration file syntax and weights.

**Example**:

```bash
agentready --validate-config .agentready-config.yaml
```

### Research Commands

#### `agentready --research-version`

Show bundled research document version.

**Example**:

```bash
agentready --research-version
# Output: Research version: 1.0.0 (2025-11-20)
```

### Utility Commands

#### `agentready --version`

Show AgentReady version.

#### `agentready --help`

Show help message with all commands.

---

## Troubleshooting

### Common Issues

#### "No module named 'agentready'"

**Cause**: AgentReady not installed or wrong Python environment.

**Solution**:

```bash
# Verify Python version
python --version  # Should be 3.11 or 3.12

# Check installation
pip list | grep agentready

# Reinstall if missing
pip install agentready
```

#### "Permission denied: .agentready/"

**Cause**: No write permissions in repository directory.

**Solution**:

```bash
# Use custom output directory
agentready assess . --output-dir ~/agentready-reports

# Or fix permissions
chmod u+w .
```

#### "Repository not found"

**Cause**: Path does not point to a git repository.

**Solution**:

```bash
# Verify git repository
git status

# If not a git repo, initialize one
git init
```

#### "Assessment taking too long"

**Cause**: Large repository with many files.

**Solution**:
AgentReady should complete in <10 seconds for most repositories. If it hangs:

1. **Check verbose output**:

   ```bash
   agentready assess . --verbose
   ```

2. **Verify git performance**:

   ```bash
   time git ls-files
   ```

3. **Report issue** with repository size and language breakdown.

**Note**: AgentReady will now warn you before scanning repositories with more than 10,000 files:

```
⚠️  Warning: Large repository detected (12,543 files).
Assessment may take several minutes. Continue? [y/N]:
```

#### "Warning: Scanning sensitive directory"

**Cause**: Attempting to scan system directories like `/etc`, `/sys`, `/proc`, `/.ssh`, or `/var`.

**Solution**:
AgentReady includes safety checks to prevent accidental scanning of sensitive system directories:

```
⚠️  Warning: Scanning sensitive directory /etc. Continue? [y/N]:
```

**Best practices**:

- Only scan your own project repositories
- Never scan system directories or sensitive configuration folders
- If you need to assess a project in `/var/www`, copy it to a user directory first
- Use `--output-dir` to avoid writing reports to sensitive locations

#### "Invalid configuration file"

**Cause**: Malformed YAML or incorrect weight values.

**Solution**:

```bash
# Validate configuration
agentready --validate-config .agentready-config.yaml

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.agentready-config.yaml'))"

# Regenerate from template
agentready --generate-config > .agentready-config.yaml
```

---

### Bootstrap-Specific Issues

#### "File already exists" error

**Cause**: Bootstrap refuses to overwrite existing files.

**Solution**:
Bootstrap is safe by design—it never overwrites existing files. This is expected behavior:

```bash
# Review what files already exist
ls -la .github/workflows/
ls -la .pre-commit-config.yaml

# If you want to regenerate, manually remove first
rm .github/workflows/agentready-assessment.yml
agentready bootstrap .

# Or keep existing and only add missing files
agentready bootstrap .  # Safely skips existing
```

---

#### "Language detection failed"

**Cause**: No recognizable language files in repository.

**Solution**:

```bash
# Check what files git tracks
git ls-files

# If empty, add some files first
git add *.py  # or *.js, *.go

# Force specific language
agentready bootstrap . --language python

# Or if mixed language project
agentready bootstrap . --language auto  # Uses majority language
```

---

#### "GitHub Actions not running"

**Cause**: Actions not enabled or insufficient permissions.

**Solution**:

1. **Enable Actions**:
   - Repository Settings → Actions → General
   - Select "Allow all actions"
   - Save

2. **Check workflow permissions**:
   - Settings → Actions → General → Workflow permissions
   - Select "Read and write permissions"
   - Save

3. **Verify workflow files**:

   ```bash
   # Check files were created
   ls -la .github/workflows/

   # Validate YAML syntax
   cat .github/workflows/agentready-assessment.yml
   ```

4. **Trigger manually**:
   - Actions tab → Select workflow → "Run workflow"

---

#### "Pre-commit hooks not running"

**Cause**: Hooks not installed locally.

**Solution**:

```bash
# Install pre-commit framework
pip install pre-commit

# Install git hooks
pre-commit install

# Verify installation
ls -la .git/hooks/
# Should see pre-commit file

# Test hooks
pre-commit run --all-files
```

**If hooks fail:**

```bash
# Update hook versions
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit uninstall
pre-commit install
```

---

#### "Dependabot PRs not appearing"

**Cause**: Dependabot not enabled for repository or incorrect config.

**Solution**:

1. **Check Dependabot is enabled**:
   - Repository Settings → Security & analysis
   - Enable "Dependabot alerts" and "Dependabot security updates"

2. **Verify config**:

   ```bash
   cat .github/dependabot.yml

   # Should have correct package-ecosystem:
   # - pip (for Python)
   # - npm (for JavaScript)
   # - gomod (for Go)
   ```

3. **Check for existing dependency issues**:
   - Security tab → Dependabot
   - View pending updates

4. **Manual trigger**:
   - Wait up to 1 week for first scheduled run
   - Or manually trigger via GitHub API

---

#### "CODEOWNERS not assigning reviewers"

**Cause**: Invalid usernames or team names in CODEOWNERS.

**Solution**:

```bash
# Edit CODEOWNERS
vim .github/CODEOWNERS

# Use valid GitHub usernames (check they exist)
* @alice @bob

# Or use teams (requires org ownership)
* @myorg/team-name

# Verify syntax
# Each line: <file pattern> <owner1> <owner2>
*.py @python-experts
/docs/ @documentation-team
```

**Common mistakes:**

- Using email instead of GitHub username
- Typo in username
- Team name without org prefix (@myorg/team)
- Missing @ symbol

---

#### "Assessment workflow failing"

**Cause**: Various potential issues with workflow execution.

**Solution**:

1. **Check workflow logs**:
   - Actions tab → Select failed run → View logs

2. **Common failures**:

   **Python not found:**

   ```yaml
   # In .github/workflows/agentready-assessment.yml
   # Ensure correct Python version
   - uses: actions/setup-python@v4
     with:
       python-version: '3.11'  # Or '3.12'
   ```

   **AgentReady not installing:**

   ```yaml
   # Check pip install step
   - run: pip install agentready

   # Or use specific version
   - run: pip install agentready==1.1.0
   ```

   **Permission denied:**

   ```yaml
   # Add permissions to workflow
   permissions:
     contents: read
     pull-requests: write  # For PR comments
   ```

3. **Test locally**:

   ```bash
   # Run same commands as workflow
   pip install agentready
   agentready assess .
   ```

---

### Report Issues

If you encounter issues not covered here:

1. **Check GitHub Issues**: [github.com/ambient-code/agentready/issues](https://github.com/ambient-code/agentready/issues)
2. **Search Discussions**: Someone may have encountered similar problems
3. **Create New Issue**: Use the bug report template with:
   - AgentReady version (`agentready --version`)
   - Python version (`python --version`)
   - Operating system
   - Complete error message
   - Steps to reproduce

---

## Next Steps

- **[Developer Guide](developer-guide.html)** — Learn how to contribute and extend AgentReady
- **[Attributes Reference](attributes.html)** — Understand each of the 25 attributes
- **[API Reference](api-reference.html)** — Integrate AgentReady into your tools
- **[Examples](examples.html)** — See real-world assessment reports

---

**Questions?** Join the discussion on [GitHub](https://github.com/ambient-code/agentready/discussions).
