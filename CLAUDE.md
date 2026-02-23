# AgentReady - Repository Quality Assessment Tool

**Purpose**: Assess repositories against agent-ready best practices and generate actionable reports.

**Last Updated**: 2026-02-20

---

## Overview

AgentReady is a Python CLI tool that evaluates repositories against a comprehensive set of carefully researched attributes that make codebases more effective for AI-assisted development. It generates interactive HTML reports, version-control friendly Markdown reports, and machine-readable JSON output.

**Current Status**: v2.29.1 - Core assessment engine complete, most essential assessors implemented, LLM-powered learning, research report management

**Self-Assessment Score**: 80.0/100 (Gold) - See `examples/self-assessment/`

**For User Documentation**: See `README.md` for installation, usage examples, and feature tutorials.

---

## Architecture

### Core Components

```
src/agentready/
├── models/          # Data models (Repository, Attribute, Finding, Assessment)
├── services/        # Scanner orchestration and language detection
│   ├── llm_cache.py         # LLM response caching (7-day TTL)
│   ├── research_loader.py   # Research report loading and validation
│   └── research_formatter.py # Research report formatting utilities
├── assessors/       # Attribute assessment implementations
│   ├── base.py      # BaseAssessor abstract class
│   ├── documentation.py   # CLAUDE.md, README assessors
│   ├── code_quality.py    # Type annotations, complexity
│   ├── testing.py         # Test coverage, pre-commit hooks
│   ├── structure.py       # Standard layout, gitignore
│   ├── repomix.py         # Repomix configuration assessor
│   └── stub_assessors.py  # Remaining assessors in development
├── learners/        # Pattern extraction and LLM enrichment
│   ├── pattern_extractor.py  # Heuristic skill extraction
│   ├── skill_generator.py    # SKILL.md generation
│   ├── code_sampler.py       # Repository code sampling
│   ├── llm_enricher.py       # Claude API integration
│   └── prompt_templates.py   # LLM prompt engineering
├── reporters/       # Report generation (HTML, Markdown, JSON)
│   ├── html.py      # Interactive HTML with Jinja2
│   └── markdown.py  # GitHub-Flavored Markdown
├── prompts/        # LLM prompt .md templates; load_prompt(name) from loader.py
├── templates/       # Jinja2 templates
│   └── report.html.j2  # Self-contained HTML report (73KB)
└── cli/             # Click-based CLI
    ├── main.py      # assess, research-version, generate-config commands
    ├── learn.py     # Continuous learning loop with LLM enrichment
    └── research.py  # Research report management commands
```

### Data Flow

```
Repository → Scanner → Assessors → Findings → Assessment → Reporters → Reports
                ↓
         Language Detection
         (git ls-files)
```

### Scoring Algorithm

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

---

## Development

### Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Install development tools
uv pip install pytest black isort ruff
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/agentready --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v
```

**Current Coverage**: 37% (focused on core logic, targeting >80%)

### Code Quality

```bash
# Pre-push linting workflow
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/
```

### Cold-Start Prompts Pattern

Enable context-free agent handoff by creating self-contained prompts in `plans/` (gitignored).

**Include**: Requirements, implementation approach, code patterns, test guidance, dependencies

**Workflow**: Planning → `plans/feature-name.md` → GitHub issue (copy prompt) → Future agent implements

**Benefits**: Asynchronous development, complete context without chat history, standardized knowledge transfer

### Adding New Assessors

1. **Expand a stub assessor** in `src/agentready/assessors/stub_assessors.py`
2. **Create new assessor class** inheriting from `BaseAssessor`
3. **Implement required methods**:
   - `attribute_id` property
   - `assess(repository)` method
   - `is_applicable(repository)` method (optional)
4. **Add tests** in `tests/unit/test_assessors_*.py`
5. **Register** in scanner's assessor list

**Example**:

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
```

**Reference Implementations**:

- Simple: `CLAUDEmdAssessor` (file existence check)
- Complex: `TypeAnnotationsAssessor` (proportional scoring)
- Language-aware: `TestCoverageAssessor` (conditional logic)

---

## Project Structure

```
agentready/
├── src/agentready/          # Source code
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # End-to-end tests
├── examples/               # Example reports
│   └── self-assessment/    # AgentReady's own assessment
├── specs/                  # Feature specifications
├── plans/                  # Cold-start prompts (gitignored)
├── experiments/            # SWE-bench validation studies
├── contracts/              # Data schemas and validation rules
├── pyproject.toml          # Python package configuration
├── CLAUDE.md              # This file (developer guide)
├── README.md              # User-facing documentation
├── BACKLOG.md             # Future features and enhancements
└── GITHUB_ISSUES.md       # GitHub-ready issue templates
```

---

## Harbor Benchmark Comparison

Empirically measure Claude Code performance impact of `.claude/agents/doubleagent.md` using Harbor's Terminal-Bench.

The Harbor comparison feature automates A/B testing by running Terminal-Bench tasks with/without agent files, calculating deltas and statistical significance, and generating comprehensive reports (JSON, Markdown, HTML).

### Quick Start

```bash
# Install Harbor
uv tool install harbor

# Run comparison (3 tasks, ~30-60 min)
agentready harbor compare \
  -t adaptive-rejection-sampler \
  -t async-http-client \
  -t terminal-file-browser \
  --verbose \
  --open-dashboard
```

### Key Metrics

- **Success Rate**: Percentage of tasks completed successfully
- **Duration**: Average time to complete tasks
- **Statistical Significance**: T-tests (p<0.05) and Cohen's d effect sizes
- **Per-Task Impact**: Individual task improvements/regressions

### Output Files

Results stored in `.agentready/harbor_comparisons/` (gitignored):

- **JSON**: Machine-readable comparison data
- **Markdown**: GitHub-friendly report (commit this for PRs)
- **HTML**: Interactive dashboard with Chart.js visualizations

### CLI Commands

**Compare**:

```bash
agentready harbor compare -t task1 -t task2 [--verbose] [--open-dashboard]
```

**List comparisons**:

```bash
agentready harbor list
```

**View comparison**:

```bash
agentready harbor view .agentready/harbor_comparisons/comparison_latest.json
```

### Architecture

| Component | Location | Purpose |
|-----------|----------|---------|
| **Data Models** | `models/harbor.py` | HarborTaskResult, HarborRunMetrics, HarborComparison |
| **Services** | `services/harbor/` | HarborRunner, AgentFileToggler, ResultParser, HarborComparer |
| **Reporters** | `reporters/` | HarborMarkdownReporter, DashboardGenerator |

### Statistical Analysis

- **Significance**: P-value < 0.05 (t-test) AND Cohen's d effect size (Small: 0.2-0.5, Medium: 0.5-0.8, Large: ≥0.8)
- **Sample Sizes**: Minimum 3 tasks, Recommended 5-10, Comprehensive 20+

### Documentation

- **User Guide**: `docs/harbor-comparison-guide.md`
- **Implementation Plan**: `.claude/plans/vivid-knitting-codd.md`
- **Harbor Docs**: <https://harborframework.com/docs>

---

## Technologies

- **Python 3.11+** (only N and N-1 versions supported)
- **Click** - CLI framework
- **Jinja2** - HTML template engine
- **Anthropic** - Claude API client (for LLM enrichment)
- **Pytest** - Testing framework
- **Black** - Code formatter
- **isort** - Import sorter
- **Ruff** - Fast Python linter
- **Harbor** - Evaluation framework (optional, for benchmarks)

---

## Preflight Checks

AgentReady validates dependencies before running benchmarks:

- **Harbor CLI**: Checked automatically before Terminal-Bench runs
- **Interactive installation**: Prompts user with `uv tool install harbor` (or `pip install harbor` fallback)
- **Opt-out**: Use `--skip-preflight` flag to bypass checks for advanced users
- **Package manager fallback**: Prefers `uv`, falls back to `pip` if `uv` not available
- **Security**: Uses `safe_subprocess_run()` with 5-minute timeout

**Implementation**:

- Module: `src/agentready/utils/preflight.py`
- Tests: `tests/unit/utils/test_preflight.py` (100% coverage)
- Integration: `src/agentready/cli/benchmark.py`

**Usage Examples**:

```bash
# Normal usage (preflight check runs automatically)
agentready benchmark --subset smoketest

# Skip preflight (advanced users)
agentready benchmark --subset smoketest --skip-preflight
```

---

## Contributing

### Workflow

1. **Create feature branch** from `main`
2. **Implement changes** with tests
3. **Run linters**: `black . && isort . && ruff check .`
4. **Run tests**: `pytest`
5. **Commit** with conventional commit messages
6. **Push** and create PR

### Conventional Commits

```
feat: Add new assessor for dependency freshness
fix: Correct type annotation detection in Python 3.12
docs: Update CLAUDE.md with architecture details
test: Add integration test for HTML report generation
refactor: Extract common assessor logic to base class
chore: Update dependencies
```

### Test Requirements

- All new assessors must have unit tests
- Integration tests for new reporters
- Maintain >80% coverage for new code
- All tests must pass before merge

---

## CI/CD

**GitHub Actions**:

- Run tests on PR
- Run linters (black, isort, ruff)
- Generate coverage report
- Run AgentReady self-assessment
- Post assessment results as PR comment

**Current**: Manual workflow (tests run locally before push)

---

## Known Issues & Limitations

1. **Stub Assessors**: 9/31 assessors still return "not_applicable" - need implementation
2. **No Lock File**: Intentionally excluded for library project (assessed as deliberate choice)
3. **Test Coverage**: Currently at ~37%, targeting >80% for production readiness

---

## Roadmap

### v2.x - Current Development (In Progress)

- **In Progress**: Expand remaining stub assessors
- **In Progress**: Improve test coverage to >80%
- **Planned**: Bootstrap command (automated remediation)
- **Planned**: Align command (automated alignment)

### v3.0 - Enterprise Features (Future)

- Customizable HTML themes with dark/light toggle
- Organization-wide dashboards
- Historical trend analysis
- AI-powered assessors with deeper code analysis

See `BACKLOG.md` for complete feature list.

---

## Notes for Claude Code Agents

**When working on AgentReady**:

1. **Read before modifying**: Always read existing assessors before implementing new ones
2. **Follow patterns**: Use `CLAUDEmdAssessor` and `READMEAssessor` as reference implementations
3. **Test thoroughly**: Add unit tests for all new assessors
4. **Maintain backwards compatibility**: Don't change Assessment model without schema version bump
5. **Stub assessors first**: Check if attribute already has stub before creating new class
6. **Proportional scoring**: Use `calculate_proportional_score()` for partial compliance
7. **Graceful degradation**: Return "skipped" if tools missing, don't crash
8. **Rich remediation**: Provide actionable steps, tools, commands, examples, citations

**Key Principles**:

- Library-first architecture (no global state)
- Strategy pattern for assessors (each is independent)
- Fail gracefully (missing tools → skip, don't crash)
- User-focused (actionable remediation over theoretical guidance)

**Command Reference**:

- User tutorials → See `README.md`
- CLI help → Run `agentready --help`
- SWE-bench experiments → See `experiments/README.md`
- Research report schema → See `contracts/research-report-schema.md`

### Documentation Workflow

**CRITICAL: Proactive Documentation Agent Usage**

Use the `github-pages-docs` agent for documentation updates after:

| Trigger | Action |
|---------|--------|
| New features implemented | Update user guide, developer guide, API reference, examples |
| Source-of-truth files modified | Cascade updates: CLAUDE.md → developer-guide.md, attributes.md → attributes.md |
| Bugs fixed or issues addressed | Update troubleshooting, known issues, migration guides |
| Project status changes | Update certification levels, versions, roadmap, milestones |

**Documentation Sources of Truth** (priority order):

1. CLAUDE.md - Project guide
2. RESEARCH_REPORT.md - Research report
3. contracts/ - Schemas and validation
4. specs/ - Feature specifications
5. Source code - Actual implementation

**Automation**: Manual trigger via `.github/workflows/update-docs.yml` (workflow_dispatch)

---

## Related Documents

- **.github/CLAUDE_INTEGRATION.md** - Dual Claude integration guide (automated + interactive)
- **BACKLOG.md** - Future features and enhancements
- **GITHUB_ISSUES.md** - GitHub-ready issue templates
- **README.md** - User-facing documentation
- **specs/** - Feature specifications and design documents
- **experiments/README.md** - SWE-bench validation workflow
- **examples/self-assessment/** - AgentReady's own assessment (80.0/100 Gold)

---

**Last Updated**: 2026-02-20 by Jeremy Eder
**AgentReady Version**: 2.29.1
**Self-Assessment**: 80.0/100 (Gold) ✨

### GitHub Actions Guidelines

- **ALWAYS run actionlint and fix any issues before pushing changes to GitHub Actions workflows**
- All workflows must pass actionlint validation with zero errors/warnings
- Use proper shell quoting and combined redirects for efficiency
