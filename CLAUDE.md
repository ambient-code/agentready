# AgentReady

Assess repositories against evidence-based attributes for AI-assisted development readiness.

## Quick Reference

| Item | Value |
|------|-------|
| **Version** | 2.29.6 |
| **Python** | >=3.12 |
| **Entry Point** | `agentready.cli.main:cli` |
| **Self-Score** | 80.0/100 (Gold) |
| **Test Coverage** | 37% (target: >80%) |

## Commands

```bash
# Core
agentready assess <repo>           # Assess repository
agentready bootstrap <repo>        # Setup agent-ready infrastructure
agentready align <repo>            # Automated remediation

# Development
pytest                             # Run tests
pytest --cov=src/agentready        # With coverage
black . && isort . && ruff check . # Lint

# Benchmarks (requires: uv tool install harbor)
agentready harbor compare -t task1 -t task2
```

## Architecture

```
src/agentready/
├── assessors/    # 25 attribute evaluators (see assessors/__init__.py:49-93)
├── cli/          # Click commands with LazyGroup optimization
├── data/         # default-weights.yaml, RESEARCH_REPORT.md
├── fixers/       # Automated remediation strategies
├── github/       # PR review formatting
├── learners/     # LLM-powered pattern extraction
├── models/       # Repository, Assessment, Finding, Attribute
├── prompts/      # LLM prompt templates
├── reporters/    # HTML, Markdown, JSON output
├── services/     # Scanner orchestration, scoring, caching
├── templates/    # Jinja2 HTML templates
└── utils/        # preflight, privacy, security, subprocess
```

**Data Flow**: Repository -> Scanner -> Assessors -> Findings -> Scorer -> Reporters

## Scoring

**Tier weights** (from `data/default-weights.yaml:6-9`):
- Tier 1 (Essential): 55%
- Tier 2 (Critical): 27%
- Tier 3 (Important): 15%
- Tier 4 (Advanced): 3%

**Certification**: Platinum (90+), Gold (75-89), Silver (60-74), Bronze (40-59)

## Adding Assessors

1. Create class inheriting `BaseAssessor` (`assessors/base.py`)
2. Implement `attribute_id` property and `assess(repository)` method
3. Register in `assessors/__init__.py:create_all_assessors()`
4. Add tests in `tests/unit/test_assessors_*.py`

**Reference implementations**:
- Simple: `CLAUDEmdAssessor` at `assessors/documentation.py`
- Complex: `TypeAnnotationsAssessor` at `assessors/code_quality.py`
- Conditional: `ContainerSetupAssessor` at `assessors/containers.py`

## Key Patterns

**Proportional scoring**: Use `calculate_proportional_score()` for partial compliance

**Graceful degradation**: Return "skipped" if tools missing, never crash

**Finding creation**:
```python
Finding.create_pass(self.attribute, evidence="...", details="...")
Finding.create_fail(self.attribute, evidence="...", remediation="...")
```

## CI/CD

16 GitHub Actions workflows in `.github/workflows/`:
- `ci.yml` - Tests (Py 3.12/3.13), linting, coverage
- `release.yml` - Semantic versioning, PyPI publish
- `agentready-assessment.yml` - Self-assessment on commits
- `pr-review.yml` - Automated PR review

**Note for agents**: Always run `actionlint` before pushing workflow changes.

## Conventions

**Commits**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`

**Tests**: All new assessors require unit tests. Maintain >80% coverage for new code.

**Linting**: Run `black . && isort . && ruff check .` before commits

## Key Files

| Purpose | Location |
|---------|----------|
| Weight config | `src/agentready/data/default-weights.yaml` |
| Research report | `src/agentready/data/RESEARCH_REPORT.md` |
| HTML template | `src/agentready/templates/report.html.j2` |
| Schemas | `specs/001-agentready-scorer/contracts/` |
| Issue templates | `.github/ISSUE_TEMPLATE/` |

## Agent Guidelines

1. **Read before modifying** - Understand existing assessors first
2. **Follow patterns** - Use reference implementations above
3. **Test thoroughly** - Unit tests required for all assessors
4. **Backwards compatibility** - Schema version bump for model changes
5. **Rich remediation** - Actionable steps with tools, commands, examples

## Related Docs

See `BOOKMARKS.md` for navigation to:
- Harbor benchmarks guide
- SWE-bench experiments
- Research report schema
- Feature specifications
- API reference (docs/)

---

