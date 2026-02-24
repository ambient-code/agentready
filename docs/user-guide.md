---
layout: page
title: User Guide
---

Quick reference for installing and using AgentReady to assess and bootstrap your repositories.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Bootstrap Your Repository](#bootstrap-your-repository)
- [Running Assessments](#running-assessments)
- [Batch Assessment](#batch-assessment)
- [Understanding Reports](#understanding-reports)
- [Configuration](#configuration)
  - ⚙️ [Custom Configuration](#custom-configuration)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **Python 3.12 or 3.13**
- **Git**
- **pip** or **uv**

### Install from PyPI

```bash
pip install agentready
# Or: uv pip install agentready (recommended)

# Verify
agentready --version
```

---

## Quick Start

### Bootstrap-First Approach (Recommended)

Transform your repository with complete CI/CD infrastructure:

```bash
cd /path/to/your/repo
agentready bootstrap .
git status  # Review generated files
git add .
git commit -m "build: Bootstrap agent-ready infrastructure"
git push
```

Generates GitHub Actions workflows (tests, security, assessment), pre-commit hooks, issue/PR templates, and Dependabot configuration. **Duration**: <60 seconds.

### Assess-Only Approach

For one-time analysis without infrastructure:

```bash
cd /path/to/your/repo
agentready assess .
open .agentready/report-latest.html
```

**Duration**: <5 seconds for most repositories.

### Batch Assessment

Assess multiple repositories for organizational insights:

```bash
cd /path/to/repos
agentready batch repo1/ repo2/ repo3/ --output-dir ./batch-reports
open batch-reports/comparison-summary.html
```
---

## Bootstrap Your Repository

### What is Bootstrap?

Bootstrap is AgentReady's automated infrastructure generator. One command creates:

- **GitHub Actions workflows** — Tests, security scanning, assessment
- **Pre-commit hooks** — Language-specific formatters and linters
- **Issue/PR templates** — Structured bug reports, feature requests
- **CODEOWNERS** — Automated review assignments
- **Dependabot** — Weekly dependency updates
- **Contributing guidelines** — If not present
- **Code of Conduct** — Red Hat standard (if not present)

**Language Detection**: Automatically detects your primary language (Python, JavaScript, Go) via `git ls-files`.

**Safe by Design**:

- Use `--dry-run` to preview changes
- Never overwrites existing files
- Review with `git status` before committing

### When to Use Bootstrap vs Assess

| Scenario | Use Bootstrap | Use Assess |
|----------|---------------|------------|
| **New project** | ✅ Start with best practices | Later, to track progress |
| **Missing GitHub Actions** | ✅ Generate workflows instantly | Shows it's missing |
| **Understanding current state** | Use after bootstrapping | ✅ Detailed analysis |
| **Tracking improvements** | One-time setup | ✅ Run repeatedly |
| **CI/CD integration** | Generates the workflows | ✅ Runs in CI |

**Recommended workflow**: Bootstrap first → Review and commit → Assess automatically on PRs → Manual assess when validating improvements

### Basic Usage

```bash
# Preview changes (recommended first step)
agentready bootstrap . --dry-run

# Generate infrastructure
agentready bootstrap .

# Force specific language
agentready bootstrap . --language python

# Bootstrap different directory
agentready bootstrap /path/to/repo
```

### Post-Bootstrap Steps

1. **Review generated files**:

   ```bash
   git status
   cat .github/workflows/agentready-assessment.yml
   cat .pre-commit-config.yaml
   ```

2. **Customize CODEOWNERS**: Replace placeholder usernames with actual team members
3. **Install pre-commit hooks locally**:

   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

4. **Enable GitHub Actions**: Settings → Actions → General → Allow all actions
5. **Commit and push**:

   ```bash
   git add .
   git commit -m "build: Bootstrap agent-ready infrastructure"
   git push
   ```

6. **Test with PR**:

   ```bash
   git checkout -b test-bootstrap
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: Verify AgentReady workflow"
   git push origin test-bootstrap
   gh pr create --title "Test: AgentReady Bootstrap" --body "Testing assessment"
   ```

### Generated Files

- **Workflows**: Assessment, tests, security (CodeQL)
- **Pre-commit hooks**: black/isort/ruff (Python), prettier/eslint (JS), gofmt/golint (Go)
- **Templates**: Bug reports, feature requests, PR template, CODEOWNERS, Dependabot

---

## Running Assessments

### Basic Usage

```bash
# Assess current directory
agentready assess .

# Assess specific repository
agentready assess /path/to/repo

# Custom output directory
agentready assess . --output-dir ./custom-reports
```

### Assessment Output

Reports are saved in `.agentready/` directory:

```
.agentready/
├── assessment-YYYYMMDD-HHMMSS.json    # Machine-readable data
├── report-YYYYMMDD-HHMMSS.html        # Interactive web report
├── report-YYYYMMDD-HHMMSS.md          # Markdown report
├── assessment-latest.json             # Symlink to latest
├── report-latest.html                 # Symlink to latest
└── report-latest.md                   # Symlink to latest
```

---

## Batch Assessment

Assess multiple repositories for organizational insights:

```bash
# Assess all repos in a directory
agentready batch /path/to/repos --output-dir ./reports

# Assess specific repos
agentready batch /path/repo1 /path/repo2 /path/repo3

# Generate comparison report
agentready batch . --compare
```

### Batch Output

```
reports/
├── comparison-summary.html      # Interactive comparison table
├── comparison-summary.md        # Markdown summary
├── aggregate-stats.json         # Machine-readable statistics
├── repo1/
│   ├── assessment-latest.json
│   └── report-latest.html
└── repo2/
    └── ...
```

### Interactive Heatmap Visualization

Generate interactive Plotly heatmap showing attribute scores across repositories:

```bash
# Generate heatmap with batch assessment
agentready assess-batch --repos /path/repo1 --repos /path/repo2 --generate-heatmap

# Custom heatmap output
agentready assess-batch --repos-file repos.txt --generate-heatmap --heatmap-output ./heatmap.html
```

---

## Understanding Reports

### HTML Report (Interactive)

**File**: `report-YYYYMMDD-HHMMSS.html`

Interactive web report with score card, tier breakdown, sortable attribute table, and expandable findings. Self-contained (no CDN), safe to share via email or wikis. Open in browser to explore ✅/❌/⊘ findings, filter by status, and copy remediation commands.

### Markdown Report (Version Control)

**File**: `report-YYYYMMDD-HHMMSS.md`

GitHub-Flavored Markdown for tracking progress over time. Commit after each assessment to see improvements in git diffs.

### JSON Report (Machine-Readable)

**File**: `assessment-YYYYMMDD-HHMMSS.json`

Complete data for CI/CD integration. Example:

```bash
# Fail build if score < 70
score=$(jq '.overall_score' .agentready/assessment-latest.json)
(( $(echo "$score < 70" | bc -l) )) && exit 1
```

---

## Configuration

### Default Behavior

AgentReady works out-of-the-box with sensible defaults. No configuration required for basic usage.

### Custom Configuration

Create `.agentready-config.yaml` to customize:

```yaml
# Custom attribute weights (must sum to 1.0)
weights:
  claude_md_file: 0.15      # Increase from default 0.10
  readme_structure: 0.12
  type_annotations: 0.08

# Exclude specific attributes
excluded_attributes:
  - performance_benchmarks
  - container_setup

# Custom output directory
output_dir: ./reports
```

### Generate/Validate Configuration

```bash
# Generate example configuration
agentready generate-config

# Validate configuration
agentready --validate-config .agentready-config.yaml
```

---

## Troubleshooting

### Common Issues

**"No module named 'agentready'"** — `pip install agentready`

**"Permission denied"** — `agentready assess . --output-dir ~/reports`

**"Repository not found"** — `git init` to initialize repository

**"Assessment taking too long"** — AgentReady warns before scanning >10,000 files. Check: `agentready assess . --verbose`

**"File already exists" (Bootstrap)** — Bootstrap never overwrites files by design. Remove existing files first if regenerating.

**"Language detection failed" (Bootstrap)** — `agentready bootstrap . --language python` to force language

**"GitHub Actions not running"** — Enable in Settings → Actions → General. Set "Read and write permissions" in Workflow permissions.

**"Pre-commit hooks not running"** — `pip install pre-commit && pre-commit install`

**"CODEOWNERS not assigning reviewers"** — Edit `.github/CODEOWNERS` with valid usernames (`* @alice @bob`)

### Report Issues

[GitHub Issues](https://github.com/ambient-code/agentready/issues) — Include AgentReady/Python version, OS, error message, and steps to reproduce.

---

## Next Steps

- **[Developer Guide](developer-guide.md)** — Learn how to contribute and extend AgentReady
- **[Attributes Reference](attributes.md)** — Understand each of the 25 attributes
- **[API Reference](api-reference.md)** — Integrate AgentReady into your tools
- **[Examples](examples.md)** — See real-world assessment reports

---

**Questions?** Join the discussion on [GitHub](https://github.com/ambient-code/agentready/issues).
