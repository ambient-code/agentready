# AgentReady Repository Scorer

[![codecov](https://codecov.io/gh/ambient-code/agentready/branch/main/graph/badge.svg)](https://codecov.io/gh/ambient-code/agentready)
[![Tests](https://github.com/ambient-code/agentready/workflows/Tests/badge.svg)](https://github.com/ambient-code/agentready/actions/workflows/tests.yml)

Assess git repositories against evidence-based attributes for AI-assisted development readiness.

> **📚 Research-Driven**: All attributes backed by [50+ peer-reviewed sources](#research-foundation) from Anthropic, Microsoft, Google, ArXiv, and IEEE/ACM.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
  - [Using uv (Recommended)](#using-uv-recommended)
  - [Container](#container)
  - [Python Package](#python-package)
  - [Harbor CLI (for Benchmarks)](#harbor-cli-for-benchmarks)
- [Example Output](#example-output)
- [Research Foundation](#research-foundation)
- [Tier-Based Scoring](#tier-based-scoring)
- [Customization](#customization)
- [CLI Reference](#cli-reference)
- [Architecture](#architecture)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [GitHub Actions Workflows](#github-actions-workflows)

## Overview

AgentReady evaluates your repository across multiple dimensions of code quality, documentation, testing, and infrastructure to determine how well-suited it is for AI-assisted development workflows. The tool generates comprehensive reports with:

- **Overall Score & Certification**: Platinum/Gold/Silver/Bronze based on comprehensive attribute assessment
- **Interactive HTML Reports**: Filter, sort, and explore findings with embedded guidance
- **Version-Control-Friendly Markdown**: Track progress over time with git-diffable reports
- **Actionable Remediation**: Specific tools, commands, and examples to improve each attribute
- **Schema Versioning**: Backwards-compatible report format with validation and migration tools

## Quick Start

### Using uv (Recommended)

Run AgentReady directly without installation:

```bash
# Run once without installing
uvx --from git+https://github.com/ambient-code/agentready agentready -- assess .

# Install as reusable global tool
uv tool install --from git+https://github.com/ambient-code/agentready agentready

# Use after global install
agentready assess .
```

### Container

```bash
# Pull container
podman pull ghcr.io/ambient-code/agentready:latest

# Create output directory
mkdir -p ~/agentready-reports

# Assess a repository
podman run --rm \
  -v /path/to/your/repo:/repo:ro \
  -v ~/agentready-reports:/reports \
  ghcr.io/ambient-code/agentready:latest \
  assess /repo --output-dir /reports

# Open reports
open ~/agentready-reports/report-latest.html
```

[See full container documentation →](CONTAINER.md)

### Python Package

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Assess a repository
agentready assess /path/to/repo
```

### Harbor CLI (for Benchmarks)

Harbor is required for running Terminal-Bench evaluations:

```bash
# AgentReady will prompt to install automatically, or install manually:
uv tool install harbor

# Verify installation
harbor --version

# Skip automatic checks (advanced users)
agentready benchmark --skip-preflight --subset smoketest
```

## Example Output

**CLI Output:**

```
Assessing repository: myproject
Repository: /Users/username/myproject
Languages detected: Python (42 files), JavaScript (18 files)

Evaluating attributes...
[████████████████████████░░░░░░░░] 23/25 (2 skipped)

Overall Score: 72.5/100 (Silver)
Attributes Assessed: 23/25
Duration: 2m 7s

Reports generated:
  HTML: .agentready/report-latest.html
  Markdown: .agentready/report-latest.md
```

**Interactive HTML Report:**

See [examples/self-assessment/report-latest.html](examples/self-assessment/report-latest.html) for AgentReady's own assessment (80.0/100 Gold).

## Research Foundation

All attributes are derived from comprehensive evidence-based research analyzing 50+ authoritative sources:

### Primary Sources

- **Anthropic**
  - [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
  - [Anthropic Engineering Blog](https://www.anthropic.com/research)

- **Microsoft**
  - [Code Metrics and Maintainability](https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-values)
  - [Azure DevOps Best Practices](https://learn.microsoft.com/en-us/azure/devops/repos/git/git-branching-guidance)

- **Google**
  - [SRE Handbook](https://sre.google/sre-book/table-of-contents/)
  - [Google Engineering Practices](https://google.github.io/eng-practices/)
  - [Google Style Guides](https://google.github.io/styleguide/)

- **Academic Research**
  - [ArXiv Software Engineering Papers](https://arxiv.org/list/cs.SE/recent)
  - [IEEE Transactions on Software Engineering](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=32)
  - [ACM Digital Library](https://dl.acm.org/)

**Complete Research Report**: [agent-ready-codebase-attributes.md](agent-ready-codebase-attributes.md)

## Tier-Based Scoring

Attributes are weighted by importance:

- **Tier 1 (Essential)**: 50% of total score - CLAUDE.md, README, type annotations, standard layouts, lock files
- **Tier 2 (Critical)**: 30% of total score - Test coverage, conventional commits, build setup
- **Tier 3 (Important)**: 15% of total score - Cyclomatic complexity, structured logging, API documentation
- **Tier 4 (Advanced)**: 5% of total score - Security scanning, performance benchmarks

Missing essential attributes (especially CLAUDE.md at 10% weight) has 10x the impact of missing advanced features.

## Customization

Create `.agentready-config.yaml` to customize weights and exclusions:

```yaml
weights:
  claude_md_file: 0.15      # Increase importance (default: 0.10)
  test_coverage: 0.05       # Increase importance (default: 0.03)
  conventional_commits: 0.01  # Decrease importance (default: 0.03)
  # Other attributes use defaults, rescaled to sum to 1.0

excluded_attributes:
  - performance_benchmarks  # Skip this attribute

output_dir: ./custom-reports
```

## CLI Reference

### Core Commands

```bash
# Assess a repository
agentready assess PATH                   # Assess repository at PATH
agentready assess PATH --verbose         # Show detailed progress
agentready assess PATH --config FILE     # Use custom configuration
agentready assess PATH --output-dir DIR  # Custom report location

# Bootstrap repository with agent-ready improvements
agentready bootstrap PATH                # Add CLAUDE.md, .gitignore, etc.
agentready bootstrap PATH --dry-run      # Preview changes without applying

# Align repository to best practices
agentready align PATH                    # Auto-fix common issues
agentready align PATH --attribute ID     # Fix specific attribute

# Run benchmarks
agentready benchmark --subset smoketest  # Quick validation (3 tasks)
agentready benchmark --subset full       # Comprehensive evaluation (20+ tasks)
agentready benchmark --skip-preflight    # Skip dependency checks

# Continuous learning
agentready learn PATH                    # Extract patterns and skills from repo
agentready learn PATH --llm-enrich       # Use Claude API for enrichment
```

### Configuration Commands

```bash
agentready --validate-config FILE        # Validate configuration
agentready --generate-config             # Create example config
```

### Research Report Management

```bash
agentready research-version              # Show bundled research version
agentready research validate FILE        # Validate research report
agentready research init                 # Generate new research report
agentready research add-attribute FILE   # Add attribute to report
agentready research bump-version FILE    # Update version
agentready research format FILE          # Format research report
```

### Utility Commands

```bash
agentready --version                     # Show tool version
agentready --help                        # Show help message
```

## Architecture

AgentReady follows a library-first design:

- **Models**: Data entities (Repository, Assessment, Finding, Attribute)
- **Assessors**: Independent evaluators for each attribute category
- **Services**: Scanner (orchestration), Scorer (calculation), LanguageDetector
- **Reporters**: HTML and Markdown report generators
- **CLI**: Thin wrapper orchestrating assessment workflow

### Project Structure

```
src/agentready/
├── cli/              # Click-based CLI entry point
├── assessors/        # Attribute evaluators (13 categories)
├── models/           # Data entities
├── services/         # Core logic (Scanner, Scorer)
├── reporters/        # HTML and Markdown generators
├── templates/        # Jinja2 HTML template
└── data/             # Bundled research report and defaults

tests/
├── unit/             # Unit tests for individual components
├── integration/      # End-to-end workflow tests
├── contract/         # Schema validation tests
└── fixtures/         # Test repositories
```

## Development

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run with verbose output
pytest -v -s
```

## Contributing

Contributions welcome! Before submitting a PR:

- [Run tests](https://docs.pytest.org/) with `pytest` (all must pass)
- [Format code](https://black.readthedocs.io/) with `black src/ tests/`
- [Sort imports](https://pycqa.github.io/isort/) with `isort src/ tests/`
- [Lint code](https://flake8.pycqa.org/) with `flake8 src/ tests/ --ignore=E501`
- Maintain test coverage >80%

**Support**:
- Documentation: See [`/docs`](docs/) directory
- Issues: [Report at GitHub Issues](https://github.com/ambient-code/agentready/issues)
- Questions: [Open a discussion](https://github.com/ambient-code/agentready/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## GitHub Actions Workflows

AgentReady uses 13 automated workflows organized by purpose:

| Name | Description | Schedule/Triggers | Purpose |
|------|-------------|-------------------|---------|
| **ci.yml** | Tests + coverage + linting + platform checks | PR, push to main | Testing & Quality |
| **security.yml** | CodeQL + Safety dependency scanning | Weekly, PR | Testing & Quality |
| **docs.yml** | Link checking (markdown lint, spell-check) | PR (docs/**), weekly (Sundays 2am UTC) | Documentation |
| **update-docs.yml** | Automated documentation updates via @agentready-dev | Manual trigger | Documentation |
| **release.yml** | Semantic-release + PyPI + container publishing | Push to main | Release & Publishing |
| **agentready-dev.yml** | Codebase agent automation via @mentions | @agentready-dev mentions | Agent Automation |
| **pr-review-auto-fix.yml** | Automated PR code reviews | PR (code changes) | Agent Automation |
| **agentready-assessment.yml** | On-demand repository assessment | `/agentready assess` command | AgentReady Features |
| **leaderboard.yml** | Validate + update leaderboard submissions | PR (submissions/), push to main | AgentReady Features |
| **continuous-learning.yml** | Weekly skill extraction with LLM | Weekly, release | AgentReady Features |
| **research-update.yml** | Weekly research report updates | Weekly (Mondays 9am UTC) | AgentReady Features |
| **stale-issues.yml** | Auto-close stale issues/PRs | Daily | Maintenance |
| **dependabot-auto-merge.yml** | Auto-merge dependency updates (patch/minor) | Dependabot PRs | Maintenance |

All workflows pass `actionlint` validation with zero errors.
