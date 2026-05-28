# AgentReady

Assess repositories against evidence-based attributes for AI-assisted development readiness.

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

# Local development (uses this checkout, not the installed package)
PYTHONPATH=src python -m agentready assess <repo>
```

## Data Flow

Repository -> Scanner -> Assessors -> Findings -> Scorer -> Reporters

## Scoring

**Certification levels**: Platinum (90+), Gold (75-89), Silver (60-74), Bronze (40-59)

## Adding Assessors

1. Create class inheriting `BaseAssessor` (`assessors/base.py`)
2. Implement `attribute_id` property and `assess(repository)` method
3. Register in `assessors/__init__.py:create_all_assessors()`
4. Add tests in `tests/unit/test_assessors_*.py`

## Key Patterns

**Proportional scoring**: Use `calculate_proportional_score()` for partial compliance

**Graceful degradation**: Return "skipped" if tools missing, never crash

**Finding creation**:
```python
Finding.create_pass(self.attribute, evidence="...", details="...")
Finding.create_fail(self.attribute, evidence="...", remediation="...")
```

## Conventions

**Commits**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`

**Tests**: All new assessors require unit tests. Maintain >80% coverage for new code.

**Linting**: Run `black . && isort . && ruff check .` before commits

**CI changes**: Always run `actionlint` before pushing workflow changes.

## Agent Guidelines

1. **Read before modifying**: understand existing assessors first
2. **Follow patterns**: use reference implementations (grep for `BaseAssessor` subclasses)
3. **Test thoroughly**: unit tests required for all assessors
4. **Backwards compatibility**: schema version bump for model changes
5. **Rich remediation**: actionable steps with tools, commands, examples
6. **Self-assign issues**: before starting work on a GitHub issue, check if it is already assigned. If it is, warn the user and ask for confirmation before continuing. If unassigned (or the user confirms), self-assign it immediately to prevent duplicate effort from other contributors
7. **Keep docs/attributes.md in sync**: when changing how an assessor scores (thresholds, partial credit rules, recognized paths, pass/fail conditions), update the corresponding entry in `docs/attributes.md` in the same PR
