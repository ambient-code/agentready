# AgentReady - Repository Quality Assessment Tool

**Purpose**: Assess repositories against agent-ready best practices and generate actionable reports.

**Last Updated**: 2025-12-05

---

## Overview

AgentReady is a Python CLI tool that evaluates repositories against a comprehensive set of carefully researched attributes that make codebases more effective for AI-assisted development. It generates interactive HTML reports, version-control friendly Markdown reports, and machine-readable JSON output.

**Current Status**: v2.14.1 - Core assessment engine complete, most essential assessors implemented, LLM-powered learning, research report management

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
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Run all linters (pre-push)
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/
```

### Cold-Start Prompts Pattern

**Purpose**: Enable context-free agent handoff for feature implementation.

**Structure**:
- **Directory**: `plans/` (gitignored, never committed)
- **Content**: Self-contained implementation prompts with complete context
- **Usage**: Create GitHub issues or hand off work to future agents

**What to Include**:
- Requirements and acceptance criteria
- Implementation approach and architectural decisions
- Code patterns to follow (with file paths)
- Test guidance and edge cases
- Related files and dependencies

**Example Workflow**:
1. During planning → Generate cold-start prompt in `plans/feature-name.md`
2. Create GitHub issue → Copy prompt content as issue body
3. Future agent → Reads issue, implements feature without conversation history
4. Local reference → Prompt stays in `plans/` for quick lookup

**Benefits**:
- Enables asynchronous development across multiple sessions
- Provides complete context without requiring chat history
- Standardizes knowledge transfer between agents
- Supports incremental feature development

**Note**: Also see `coldstart-prompts/` directory for legacy prompts (being migrated to `plans/`).

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

## Terminal-Bench Eval Harness

**Purpose**: Empirically measure the impact of AgentReady assessors on Terminal-Bench performance through systematic A/B testing.

### Overview

The eval harness tests each assessor independently to measure its specific impact on agentic development benchmarks. This provides evidence-based validation of AgentReady's recommendations.

**Architecture**:
1. **Baseline**: Run Terminal-Bench on unmodified repository (5 iterations)
2. **Per-Assessor Test**: Apply single assessor remediation → measure delta
3. **Aggregate**: Rank assessors by impact, calculate tier statistics
4. **Dashboard**: Generate interactive visualization for GitHub Pages

**Components**:
- `src/agentready/services/eval_harness/` - Core services (TbenchRunner, BaselineEstablisher, AssessorTester, ResultsAggregator, DashboardGenerator)
- `src/agentready/models/eval_harness.py` - Data models (TbenchResult, BaselineMetrics, AssessorImpact, EvalSummary)
- `src/agentready/cli/eval_harness.py` - CLI commands (baseline, test-assessor, run-tier, summarize, dashboard)
- `docs/tbench.md` - Interactive dashboard with Chart.js
- `docs/tbench/methodology.md` - Detailed statistical methodology

### Running Evaluations

```bash
# 1. Establish baseline (run Terminal-Bench 5 times on unmodified repo)
agentready eval-harness baseline --repo . --iterations 5

# 2. Test single assessor
agentready eval-harness test-assessor \
  --assessor-id claude_md_file \
  --iterations 5

# 3. Test all Tier 1 assessors
agentready eval-harness run-tier --tier 1 --iterations 5

# 4. Aggregate results (rank by impact, calculate statistics)
agentready eval-harness summarize --verbose

# 5. Generate dashboard data files for GitHub Pages
agentready eval-harness dashboard --verbose
```

### File Structure

```
.agentready/eval_harness/          # Results storage (gitignored)
├── baseline/
│   ├── run_001.json              # Individual tbench runs
│   ├── run_002.json
│   ├── ...
│   └── summary.json              # BaselineMetrics
├── assessors/
│   ├── claude_md_file/
│   │   ├── finding.json          # Assessment result
│   │   ├── fixes_applied.log     # Remediation log
│   │   ├── run_001.json          # Post-remediation runs
│   │   ├── ...
│   │   └── impact.json           # AssessorImpact metrics
│   └── ...
└── summary.json                   # EvalSummary (ranked impacts)

docs/_data/tbench/                 # Dashboard data (committed)
├── summary.json
├── ranked_assessors.json
├── tier_impacts.json
├── baseline.json
└── stats.json
```

### Statistical Methods

**Significance Criteria** (both required):
- **P-value < 0.05**: 95% confidence (two-sample t-test)
- **|Cohen's d| > 0.2**: Meaningful effect size

**Effect Size Interpretation**:
- **0.2 ≤ |d| < 0.5**: Small effect
- **0.5 ≤ |d| < 0.8**: Medium effect
- **|d| ≥ 0.8**: Large effect

### Current Status

**Phase 1 (MVP)**: Mocked Terminal-Bench integration ✅
- All core services implemented and tested
- CLI commands functional
- Dashboard with Chart.js visualizations
- 6 CLI unit tests + 5 integration tests passing

**Phase 2 (Planned)**: Real Terminal-Bench integration
- Harbor framework client
- Actual benchmark submissions
- Leaderboard integration

### Testing

```bash
# Run eval harness tests
pytest tests/unit/test_eval_harness*.py -v
pytest tests/integration/test_eval_harness_e2e.py -v
```

**Test Coverage**:
- Models: 90-95%
- Services: 85-90%
- CLI: 100% (help commands validated)
- Integration: End-to-end workflow tested

### Troubleshooting

**Issue**: `FileNotFoundError: Baseline directory not found`
**Solution**: Run `agentready eval-harness baseline` first

**Issue**: `No assessor results found`
**Solution**: Run `agentready eval-harness test-assessor` or `run-tier` first

**Issue**: Mocked scores seem unrealistic
**Solution**: This is expected in Phase 1 (mocked mode) - real integration coming in Phase 2

### Documentation

- **User Guide**: `docs/eval-harness-guide.md` - Step-by-step tutorials
- **Methodology**: `docs/tbench/methodology.md` - Statistical methods explained
- **Dashboard**: `docs/tbench.md` - Interactive results visualization
- **Plan**: `.claude/plans/quirky-squishing-plum.md` - Implementation roadmap

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

## Technologies

- **Python 3.12+** (only N and N-1 versions supported)
- **Click** - CLI framework
- **Jinja2** - HTML template engine
- **Anthropic** - Claude API client (for LLM enrichment)
- **Pytest** - Testing framework
- **Black** - Code formatter
- **isort** - Import sorter
- **Ruff** - Fast Python linter

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

When working with documentation in this repository, **ALWAYS** use the `github-pages-docs` agent for any documentation updates, revisions, or additions. This ensures consistency, quality, and adherence to the established documentation structure.

**Trigger the github-pages-docs agent when**:

1. **After implementing new features** (e.g., Bootstrap, new assessors, new commands)
   - Update user guide with new feature documentation
   - Update developer guide with architecture changes
   - Update API reference with new classes/methods
   - Update examples with new use cases

2. **After modifying source-of-truth files**:
   - `CLAUDE.md` changes → Update developer-guide.md and user-guide.md
   - `agent-ready-codebase-attributes.md` changes → Update attributes.md
   - `README.md` changes → Sync with docs/index.md
   - Bootstrap implementation changes → Update bootstrap documentation sections

3. **When fixing bugs or addressing issues**:
   - Update troubleshooting sections
   - Update known issues documentation
   - Update migration guides if breaking changes

4. **When updating project status**:
   - Certification level changes (e.g., Silver → Gold)
   - Version bumps (v1.0 → v1.1)
   - Roadmap updates
   - New milestone achievements

**Agent Invocation Pattern**:
```
Use the @agent-github-pages-docs to [action] based on:
- [Source of truth file] updates
- [Feature/bug/change] implementation
- [Specific sections] that need updating
```

**Documentation Sources of Truth** (in priority order):
1. `CLAUDE.md` - Complete project guide (architecture, development, workflows)
2. `agent-ready-codebase-attributes.md` - Research report (25 attributes, tier system)
3. `contracts/` - Schemas and contracts (data models, validation rules)
4. `specs/` - Feature specifications (design documents, plans)
5. `README.md` - User-facing overview
6. Source code - Actual implementation (CLI, services, assessors)

**Documentation Automation**:
- Manual trigger: `.github/workflows/update-docs.yml` (workflow_dispatch)
- Future: Automatic cascade updates on source file changes (see BACKLOG.md - P2 item)
- Always review agent-generated docs before committing
- Ensure Bootstrap documentation is kept prominent and up-to-date

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

**Last Updated**: 2025-12-05 by Jeremy Eder
**AgentReady Version**: 2.14.1
**Self-Assessment**: 80.0/100 (Gold) ✨
