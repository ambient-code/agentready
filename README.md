# AgentReady Repository Scorer

[![codecov](https://codecov.io/gh/ambient-code/agentready/branch/main/graph/badge.svg)](https://codecov.io/gh/ambient-code/agentready)
[![Tests](https://github.com/ambient-code/agentready/workflows/Tests/badge.svg)](https://github.com/ambient-code/agentready/actions/workflows/tests.yml)

Assess git repositories against evidence-based attributes for AI-assisted development readiness.

> **📚 Research-Based Assessment**: AgentReady's attributes are derived from [comprehensive research](agent-ready-codebase-attributes.md) analyzing 50+ authoritative sources including **Anthropic**, **Microsoft**, **Google**, **ArXiv**, and **IEEE/ACM**. Each attribute is backed by peer-reviewed research and industry best practices. [View full research report →](agent-ready-codebase-attributes.md)

## Overview

AgentReady evaluates your repository across multiple dimensions of code quality, documentation, testing, and infrastructure to determine how well-suited it is for AI-assisted development workflows. The tool generates comprehensive reports with:

- **Overall Score & Certification**: Platinum/Gold/Silver/Bronze based on comprehensive attribute assessment
- **Interactive HTML Reports**: Filter, sort, and explore findings with embedded guidance
- **Version-Control-Friendly Markdown**: Track progress over time with git-diffable reports
- **Actionable Remediation**: Specific tools, commands, and examples to improve each attribute
- **Schema Versioning**: Backwards-compatible report format with validation and migration tools

## Quick Start

### Bootstrap (Recommended)

Transform your repository with one command:

```bash
cd /path/to/your/repo
agentready bootstrap .
git add . && git commit -m "build: Bootstrap agent-ready infrastructure"
git push
```

**What you get:**

- ✅ GitHub Actions workflows (tests, security, AgentReady assessment)
- ✅ Pre-commit hooks (formatters, linters)
- ✅ Issue/PR templates
- ✅ Dependabot configuration
- ✅ Automated assessment on every PR

**Duration**: <60 seconds

[See detailed Bootstrap tutorial →](docs/user-guide.md#bootstrap-your-repository)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/agentready.git
cd agentready

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```
### Run Directly via uv (Optional, No Install Required)

If you use **uv**, you can run AgentReady directly from GitHub without cloning or installing:

```bash
uvx --from git+https://github.com/ambient-code/agentready agentready -- assess .
```

To install it as a reusable global tool:

```bash
uv tool install --from git+https://github.com/ambient-code/agentready agentready
```

After installing globally:

```bash
agentready assess .
```

### Assessment Only

For one-time analysis without infrastructure changes:

```bash
# Assess current repository
agentready assess .

# Assess another repository
agentready assess /path/to/your/repo

# Specify custom configuration
agentready assess /path/to/repo --config my-config.yaml

# Custom output directory
agentready assess /path/to/repo --output-dir ./reports
```

### Example Output

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

## Features

### Evidence-Based Attributes

Evaluated across 13 categories:

1. **Context Window Optimization**: CLAUDE.md files, concise docs, file size limits
2. **Documentation Standards**: README structure, inline docs, ADRs
3. **Code Quality**: Cyclomatic complexity, file length, type annotations, code smells
4. **Repository Structure**: Standard layouts, separation of concerns
5. **Testing & CI/CD**: Coverage, test naming, pre-commit hooks
6. **Dependency Management**: Lock files, freshness, security
7. **Git & Version Control**: Conventional commits, gitignore, templates
8. **Build & Development**: One-command setup, dev docs, containers
9. **Error Handling**: Clear messages, structured logging
10. **API Documentation**: OpenAPI/Swagger specs
11. **Modularity**: DRY principle, naming conventions
12. **CI/CD Integration**: Pipeline visibility, branch protection
13. **Security**: Scanning automation, secrets management

### Tier-Based Scoring

Attributes are weighted by importance:

- **Tier 1 (Essential)**: 50% of total score - CLAUDE.md, README, types, layouts, lock files
- **Tier 2 (Critical)**: 30% of total score - Tests, commits, build setup
- **Tier 3 (Important)**: 15% of total score - Complexity, logging, API docs
- **Tier 4 (Advanced)**: 5% of total score - Security scanning, performance benchmarks

Missing essential attributes (especially CLAUDE.md at 10% weight) has 10x the impact of missing advanced features.

### Interactive HTML Reports

- Filter by status (Pass/Fail/Skipped)
- Sort by score, tier, or category
- Search attributes by name
- Collapsible sections with detailed evidence
- Color-coded score indicators
- Certification ladder visualization
- Works offline (no CDN dependencies)

### Customization

Create `.agentready-config.yaml` to customize weights:

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

```bash
# Assessment commands
agentready assess PATH                   # Assess repository at PATH
agentready assess PATH --verbose         # Show detailed progress
agentready assess PATH --config FILE     # Use custom configuration
agentready assess PATH --output-dir DIR  # Custom report location

# Configuration commands
agentready --validate-config FILE        # Validate configuration
agentready --generate-config             # Create example config

# Research report management
agentready research-version              # Show bundled research version
agentready research validate FILE        # Validate research report
agentready research init                 # Generate new research report
agentready research add-attribute FILE   # Add attribute to report
agentready research bump-version FILE    # Update version
agentready research format FILE          # Format research report

# Utility commands
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

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/ --ignore=E501

# Run all checks
black . && isort . && flake8 .
```

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

## Research Foundation

All attributes are derived from evidence-based research with 50+ citations from:

- Anthropic (Claude Code documentation, engineering blog)
- Microsoft (Code metrics, Azure DevOps best practices)
- Google (SRE handbook, style guides)
- ArXiv (Software engineering research papers)
- IEEE/ACM (Academic publications on code quality)

See `src/agentready/data/agent-ready-codebase-attributes.md` for complete research report.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please ensure:

- All tests pass (`pytest`)
- Code is formatted (`black`, `isort`)
- Linting passes (`flake8`)
- Test coverage >80%

## Support

- Documentation: See `/docs` directory
- Issues: Report at GitHub Issues
- Questions: Open a discussion on GitHub

---

**Quick Start**: `pip install -e ".[dev]" && agentready assess .` - Ready in <5 minutes!
