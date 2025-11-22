# AgentReady - Repository Quality Assessment Tool

**Purpose**: Assess repositories against agent-ready best practices and generate actionable reports.

**Last Updated**: 2025-11-21

---

## Overview

AgentReady is a Python CLI tool that evaluates repositories against 25 carefully researched attributes that make codebases more effective for AI-assisted development. It generates interactive HTML reports, version-control friendly Markdown reports, and machine-readable JSON output.

**Current Status**: v1.0.0 - Core assessment engine complete, 10/25 attributes implemented, report schema versioning enabled

**Self-Assessment Score**: 75.4/100 (Gold) - See `examples/self-assessment/`

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

## Continuous Learning Loop (LLM-Powered)

**NEW in v1.1**: Extract high-quality skills from assessments using Claude API

The `learn` command analyzes assessment results to identify successful patterns and generates Claude Code skills. With `--enable-llm`, it uses Claude Sonnet 4.5 to create detailed, context-aware skill documentation.

### Basic Usage (Heuristic)

```bash
# Extract skills using heuristic pattern extraction
agentready learn .

# Generate SKILL.md files
agentready learn . --output-format skill_md

# Create GitHub issue templates
agentready learn . --output-format github_issues
```

### LLM-Powered Enrichment

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Extract skills with LLM enrichment (top 5 skills)
agentready learn . --enable-llm

# Enrich more skills with custom budget
agentready learn . --enable-llm --llm-budget 10

# Bypass cache for fresh analysis
agentready learn . --enable-llm --llm-no-cache

# Generate all formats with LLM enrichment
agentready learn . --enable-llm --output-format all
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

## Research Report Management (NEW)

**NEW in v1.1**: Utilities for maintaining the research report (agent-ready-codebase-attributes.md)

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
│   └── stub_assessors.py  # 15 not-yet-implemented assessors
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

- **Python 3.11+** (only N and N-1 versions supported)
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

1. **Stub Assessors**: 15/25 assessors return "not_applicable" - need implementation
2. **No Lock File**: Intentionally excluded for library project
3. **No Pre-commit Hooks**: Not yet configured (planned P0 fix)
4. **HTML Report Design**: Current color scheme needs improvement (P0 fix)
5. **Report Metadata**: Missing repository context in header (P0 fix)

---

## Roadmap

### v1.1 - Critical UX Fixes (Next Sprint)
- **P0**: Add report header with repository metadata
- **P0**: Redesign HTML report (larger fonts, better colors)

### v1.2 - Automation & Integration
- **P1**: Implement `agentready align` subcommand (automated remediation)
- **P2**: GitHub App integration (badges, status checks, PR comments)
- **P2**: Interactive dashboard (one-click remediation)

### v1.3 - Assessor Expansion
- Expand 15 stub assessors
- Add AI-powered assessors (type annotations, docstrings)
- Improve test coverage to >80%

### v2.0 - Enterprise Features
- ✅ Report schema versioning (v1.0.0)
- Customizable HTML themes with dark/light toggle
- Organization-wide dashboards
- Historical trend analysis

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
- **examples/self-assessment/** - AgentReady's own assessment (75.4/100 Gold)

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

**Last Updated**: 2025-11-21 by Jeremy Eder
**AgentReady Version**: 1.0.0
**Self-Assessment**: 75.4/100 (Gold) ✨
