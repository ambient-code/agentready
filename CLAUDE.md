# AgentReady - Repository Quality Assessment Tool

**Purpose**: Assess repositories against agent-ready best practices and generate actionable reports.

**Last Updated**: 2025-12-04

---

## Overview

AgentReady is a Python CLI tool that evaluates repositories against 25 carefully researched attributes that make codebases more effective for AI-assisted development. It generates interactive HTML reports, version-control friendly Markdown reports, and machine-readable JSON output.

**Current Status**: v2.11.1 - Core assessment engine complete, 22/31 attributes implemented (9 stubs), LLM-powered learning, research report management

**Self-Assessment Score**: 80.0/100 (Gold) - See `examples/self-assessment/`

---

## Quick Start

```bash
# Install in virtual environment
uv venv && source .venv/bin/activate
uv pip install -e .

# Run assessment on current directory
agentready assess .

# Run with verbose output
agentready assess . --verbose

# Assess different repository
agentready assess /path/to/repo --output-dir ./reports

# Validate assessment report
agentready validate-report .agentready/assessment-latest.json

# Migrate report to new schema version
agentready migrate-report old-report.json --to 2.0.0
```

**Outputs**:
- `.agentready/assessment-YYYYMMDD-HHMMSS.json` - Machine-readable results (with schema version)
- `.agentready/report-YYYYMMDD-HHMMSS.html` - Interactive web report
- `.agentready/report-YYYYMMDD-HHMMSS.md` - Git-friendly markdown report

---

## Batch Assessment & GitHub Integration

**Feature**: Assess multiple repositories in a single operation, including scanning entire GitHub organizations.

The `assess-batch` command enables bulk repository assessment with support for file-based lists, inline arguments, and direct GitHub organization scanning.

### Basic Usage

```bash
# Assess repositories from a file
agentready assess-batch --repos-file repos.txt

# Assess specific repositories
agentready assess-batch \
  --repos https://github.com/user/repo1 \
  --repos https://github.com/user/repo2

# Combine multiple sources
agentready assess-batch \
  --repos-file my-repos.txt \
  --repos https://github.com/user/extra-repo
```

### GitHub Organization Scanning

Assess all repositories in a GitHub organization:

```bash
# Set GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# Scan public repos only (default)
agentready assess-batch --github-org anthropics

# Include private repos
agentready assess-batch --github-org myorg --include-private

# Limit number of repos
agentready assess-batch --github-org myorg --max-repos 50

# Combine with other sources
agentready assess-batch \
  --github-org myorg \
  --repos-file additional-repos.txt \
  --verbose
```

**Token Setup**:
1. Create personal access token: https://github.com/settings/tokens
2. Required scopes: `repo:status`, `public_repo`
3. For private repos: `repo` (full control)
4. Set environment variable: `export GITHUB_TOKEN=ghp_...`

**Security Features**:
- Token stored in environment only (never in files)
- Token redacted in all logs and errors
- Public repos scanned by default (safe)
- Private repos require explicit `--include-private` flag
- Organization name validated to prevent injection attacks
- Repository limit enforced (default: 100)
- Rate limiting implemented (0.2s between API requests)

**Output**:
- Batch reports saved to `.agentready/batch/` by default
- Individual repository assessments cached
- Summary statistics across all repositories
- Aggregate scoring and failure analysis

---

## SWE-bench Experiments (MVP)

**Feature**: Quantify AgentReady settings against SWE-bench baseline using both SWE-agent and Claude Code.

The `experiment` commands enable controlled experiments to validate which AgentReady attributes improve AI agent performance on real-world coding tasks.

### Quick Start

```bash
# 1. Run agent on repository
agentready experiment run-agent sweagent \
  --repo-path /path/to/repo \
  --dataset lite \
  --output predictions_baseline.jsonl

# 2. Evaluate predictions
agentready experiment evaluate \
  --predictions predictions_baseline.jsonl \
  --output results_baseline.json

# 3. Analyze and generate interactive heatmap
agentready experiment analyze \
  --results-dir results/ \
  --heatmap heatmap.html

# 4. View results
open heatmap.html
```

### Pre-configured Experiments

Five configurations in `experiments/configs/`:

1. **baseline.yaml** - No AgentReady changes (control)
2. **claude-md.yaml** - CLAUDE.md only (Tier 1 essential)
3. **types-docs.yaml** - Type annotations + inline documentation
4. **tier1.yaml** - All 5 Tier 1 attributes
5. **full-bootstrap.yaml** - All AgentReady best practices

### Supported Agents

- **SWE-agent**: Production-ready, built-in SWE-bench support
- **Claude Code**: Headless mode execution (requires task file)

### SWE-bench Datasets

- **Lite**: 300 tasks (~15-30 min with cache)
- **Full**: 2,294 tasks (~2-4 hours)

### Interactive Visualization

Generates Plotly Express heatmap with:
- Hover tooltips (config, agent, score, delta from baseline)
- Zoom/pan capability
- RdYlGn colormap (seaborn-style)
- Standalone HTML export (shareable without Python)

### Expected Results

Based on sample data:
- **Baseline**: ~38-39% pass rate
- **CLAUDE.md only**: +7-8pp improvement
- **Full bootstrap**: +14pp improvement
- **Correlation**: r ≈ 0.87 between AgentReady score and SWE-bench performance

### Dependencies

```bash
uv pip install swebench sweagent plotly pandas scipy
```

See `experiments/README.md` for detailed workflow and manual steps.

---

## Continuous Learning Loop (LLM-Powered)

**Feature**: Extract high-quality skills from assessments using Claude API

The `extract-skills` command analyzes assessment results to identify successful patterns and generates Claude Code skills. With `--enable-llm`, it uses Claude Sonnet 4.5 to create detailed, context-aware skill documentation.

### Basic Usage (Heuristic)

```bash
# Extract skills using heuristic pattern extraction
agentready extract-skills .

# Generate SKILL.md files
agentready extract-skills . --output-format skill_md

# Create GitHub issue templates
agentready extract-skills . --output-format github_issues
```

### LLM-Powered Enrichment

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Extract skills with LLM enrichment (top 5 skills)
agentready extract-skills . --enable-llm

# Enrich more skills with custom budget
agentready extract-skills . --enable-llm --llm-budget 10

# Bypass cache for fresh analysis
agentready extract-skills . --enable-llm --llm-no-cache

# Generate all formats with LLM enrichment
agentready extract-skills . --enable-llm --output-format all
```

### LLM Enrichment Features

**What it does**:
- Analyzes repository code samples for real examples
- Generates 5-10 step detailed instructions
- Extracts file paths and code snippets from actual implementation
- Derives best practices from high-scoring attributes
- Identifies anti-patterns to avoid

**How it works**:
1. Heuristics extract basic skills from assessment findings
2. Top N skills (default: 5) are sent to Claude API
3. Code sampler provides relevant files from repository
4. Claude analyzes patterns and generates structured JSON
5. Enriched skills merged with detailed instructions/examples
6. Results cached for 7 days to reduce API costs

**Caching**:
- Responses cached in `.agentready/llm-cache/`
- 7-day TTL (time-to-live)
- Cache key based on attribute + score + evidence hash
- Use `--llm-no-cache` to force fresh API calls

**Cost Control**:
- `--llm-budget N` limits enrichment to top N skills
- Default: 5 skills (approximately 5-10 API calls)
- Each enrichment: ~2-6 seconds, ~2000-4000 tokens
- Caching prevents redundant calls on repeated assessments

**Graceful Fallback**:
- Missing API key → falls back to heuristic skills
- API errors → uses original heuristic skill
- Rate limits → retries with exponential backoff

---

## Research Report Management

**Feature**: Utilities for maintaining the research report (agent-ready-codebase-attributes.md)

The `research` command group provides tools to validate, update, and format research reports following the schema defined in `contracts/research-report-schema.md`.

### Commands

```bash
# Validate research report against schema
agentready research validate agent-ready-codebase-attributes.md

# Generate new research report from template
agentready research init --output new-research.md

# Add new attribute to research report
agentready research add-attribute research.md \
  --attribute-id "1.4" \
  --name "New Attribute" \
  --tier 2 \
  --category "Documentation"

# Update version (major.minor.patch)
agentready research bump-version research.md --type minor

# Set explicit version
agentready research bump-version research.md --version 2.0.0

# Lint and format research report
agentready research format research.md

# Check formatting without changes
agentready research format research.md --check
```

### Validation Rules

**Errors** (block usage):
- Missing metadata header (version, date)
- Incorrect attribute count (not 25)
- Missing "Measurable Criteria" sections
- Fewer than 4 tiers defined
- Invalid version/date format

**Warnings** (non-critical):
- Missing "Impact on Agent Behavior" sections
- Fewer than 20 references
- Unbalanced tier distribution
- Non-sequential attribute numbering

### Use Cases

1. **Maintain consistency**: Validate before committing changes
2. **Add new attributes**: Use `add-attribute` for proper structure
3. **Version tracking**: Bump version after significant updates
4. **Code quality**: Format ensures consistent markdown style
5. **Pre-commit integration**: Run `validate` in pre-commit hooks

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
│   └── stub_assessors.py  # 9 stub assessors (22 implemented)
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

**Current Coverage**: 37% (focused on core logic)

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Run all linters
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/
```

### Cold-Start Prompts Pattern

**Gitignored Planning Directory**: `.plans/`

When creating cold-start prompts for features or assessors:
- Store in `.plans/` directory (gitignored, never committed)
- Each prompt is self-contained for implementation handoff
- Prompts include: requirements, implementation approach, code patterns, test guidance
- Use for creating GitHub issues with full context
- Allows LLM agents to pick up work without conversation history

**Example workflow**:
1. Generate cold-start prompt → `.plans/assessor-name.md`
2. Create GitHub issue with prompt content as body
3. Future agent reads issue → implements feature
4. Prompt stays in `.plans/` for local reference only

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
├── pyproject.toml          # Python package configuration
├── CLAUDE.md              # This file
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

**GitHub Actions** (planned):
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

### v1.x - Current Development (In Progress)
- ✅ LLM-powered learning and skill extraction
- ✅ Research report management commands
- ✅ Lock files, conventional commits, gitignore assessors
- ✅ Repomix configuration assessor
- **In Progress**: Expand remaining 9 stub assessors (22/31 currently implemented)
- **In Progress**: Improve test coverage to >80%

### v2.0 - Automation & Integration (Next)
- **P1**: Implement `agentready bootstrap` subcommand (automated remediation)
- **P1**: Implement `agentready align` subcommand (automated alignment)
- **P2**: GitHub App integration (badges, status checks, PR comments)
- **P2**: Interactive dashboard (one-click remediation)

### v3.0 - Enterprise Features (Future)
- ✅ Report schema versioning
- Customizable HTML themes with dark/light toggle
- Organization-wide dashboards
- Historical trend analysis
- AI-powered assessors with deeper code analysis

See `BACKLOG.md` for full feature list.

---

## Getting Help

- **Issues**: Create GitHub issue using templates in `GITHUB_ISSUES.md`
- **Documentation**: See `README.md` for user guide
- **Examples**: View `examples/self-assessment/` for reference reports
- **Research**: Read `agent-ready-codebase-attributes.md` for attribute definitions

---

## Related Documents

- **.github/CLAUDE_INTEGRATION.md** - Dual Claude integration guide (automated + interactive)
- **BACKLOG.md** - Future features and enhancements (11 items)
- **GITHUB_ISSUES.md** - GitHub-ready issue templates
- **README.md** - User-facing documentation
- **specs/** - Feature specifications and design documents
- **examples/self-assessment/** - AgentReady's own assessment (80.0/100 Gold)

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

**Example**:
```
Use the @agent-github-pages-docs to revise all documentation in docs/ based on:
- Bootstrap feature now fully implemented
- New CLI commands (bootstrap, align)
- Updated architecture in CLAUDE.md
- Self-assessment score improvement (75.4 → 82.1)
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

**Last Updated**: 2025-12-04 by Jeremy Eder
**AgentReady Version**: 2.11.1
**Self-Assessment**: 80.0/100 (Gold) ✨
