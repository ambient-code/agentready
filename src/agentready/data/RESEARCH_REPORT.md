---
version: "2.0.0"
date: "2026-05-03"
focus: "AI coding agent optimization (Claude Code, Copilot, Cursor, Codex, and cross-tool)"
attribute_count: 41
tier_count: 4
reference_count: 55
---

# Agent-Ready Codebase Attributes: Comprehensive Research
*Optimizing Codebases for AI-Assisted Development*

**Version:** 2.0.0
**Date:** 2026-05-03
**Focus:** AI coding agent optimization (cross-tool: Claude Code, GitHub Copilot, Cursor, Codex, Gemini CLI)
**Sources:** 55+ authoritative sources including Anthropic, ETH Zurich, Red Hat, GitHub, Microsoft, Google, ArXiv

---

## Executive Summary

This document catalogs 27 assessed attributes (across 41 sub-topics) that make codebases optimal for AI-assisted development across tools (Claude Code, GitHub Copilot, Cursor, Codex, Gemini CLI). Each attribute includes:
- Definition and importance for AI agents
- Impact on agent behavior (context window, comprehension, task success)
- Measurable criteria and tooling
- Authoritative citations
- Good vs. bad examples

**Key Research Findings (2025-2026):**
- Auto-generated context files **reduce** agent success by ~3% and increase cost by 20-23% (ETH Zurich, Feb 2026)
- The same model scores 52.8% vs 66.5% depending on surrounding infrastructure — scaffolding matters more than the model (LangChain Terminal-Bench)
- Anthropic identifies "giving agents a way to verify their work" as the single highest-leverage practice
- Human-written context files help only marginally (+4%) — only include what agents can't discover on their own (ETH Zurich)

**Top 10 Critical Attributes** (highest ROI, evidence-based):
1. Single-command test execution (verification is #1 leverage)
2. CI quality gates (lint + type-check + tests on every PR)
3. Single-file verification (fast feedback loops for lint/type-check)
4. CLAUDE.md/AGENTS.md configuration files (minimal, hand-written, <150 lines)
5. Type annotations (structural signals for agent navigation)
6. Standard project layouts
7. Dependency lock files
8. README with quick start commands
9. Deterministic enforcement (hooks + lint rules > advisory instructions)
10. Pattern references for common changes

---

## 1. CONTEXT WINDOW OPTIMIZATION

### 1.1 CLAUDE.md Configuration Files

**Definition:** Markdown file at repository root automatically ingested by Claude at conversation start.

**Why It Matters:** CLAUDE.md files are "naively dropped into context up front," providing immediate project context without repeated explanations. Reduces prompt engineering time by ~40%.

**Impact on Agent Behavior:**
- Immediate understanding of tech stack, repository structure, standard commands
- Consistent adherence to project conventions
- Reduced need for repeated context-setting
- Frames entire session with project-specific guidance

**Critical Research Finding:** The ETH Zurich study (Feb 2026) tested context files across 138 real tasks. Auto-generated files (e.g., from `/init`) **reduced** agent success by ~3% and increased costs by 20-23%. Human-written files helped only marginally (+4%). The takeaway: only include information agents can't discover by reading the code.

**Measurable Criteria:**
- File size: <150 lines recommended, hard cap at 300 lines
- Only include what agents **cannot infer** from the codebase
- The 6 core areas (per GitHub analysis of 2,500+ repos):
  1. Commands — executable build/test/lint commands with flags
  2. Testing — framework specifics and test execution patterns
  3. Project structure — only non-obvious file locations
  4. Code style — real examples of good vs. poor output
  5. Git workflow — commit format, branch naming, PR conventions
  6. Boundaries — "always do," "ask first," "never do"
- Cross-tool compatibility: AGENTS.md supported by 60,000+ repos across Claude Code, Copilot, Cursor, Codex, Gemini CLI
- Maintenance: update when code review catches agent mistakes

**Anti-patterns to Avoid:**
- Auto-generated context shipped as-is (-3% success rate, +20% cost)
- File-by-file descriptions (bloat context, go stale fast)
- Standard language conventions the agent already knows
- Context files >300 lines (adherence drops, context diluted)

**Litmus test for every line:** "Would removing this cause the agent to make a mistake it wouldn't otherwise make?" If not, delete it.

**Citations:**
- ETH Zurich: "Are Repository-Level Context Files Helpful for Coding Agents?" (Feb 2026) — arxiv.org/html/2602.11988v1
- Anthropic: Claude Code Best Practices — code.claude.com/docs/en/best-practices
- GitHub Blog: "How to write a great agents.md — lessons from over 2,500 repositories" (2026)
- Addy Osmani: "Stop Using /init for AGENTS.md" (Feb 2026)
- AGENTS.md Official Specification — agents.md

**Example:**
```markdown
# Good CLAUDE.md
# Tech Stack
- Python 3.11+, pytest, black + isort

# Standard Commands
- Run tests: `pytest tests/`
- Format: `black . && isort .`
- Build: `make build`

# Repository Structure
- src/ - Main application code
- tests/ - Test files mirror src/
- docs/ - Documentation

# Boundaries
- Never modify files in legacy/
- Require approval before changing config.yaml
```

---

### 1.2 Concise, Structured Documentation

**Definition:** Documentation maximizing information density while minimizing token consumption.

**Why It Matters:** Despite expanding context windows (1M+ tokens), attention mechanisms have quadratic complexity growth. Performance drops significantly on long-context tasks: 29%→3% (Claude 3.5 Sonnet) or 70.2%→40% (Qwen2.5).

**Impact on Agent Behavior:**
- Faster information retrieval through clear headings
- Reduced context pollution
- Improved response accuracy
- Better navigation across documentation

**Measurable Criteria:**
- Use standard Markdown headings (#, ##, ###)
- README <500 lines; use wiki/docs for extensive content
- Table of contents for documents >100 lines
- Bullet points over prose paragraphs
- One concept per section

**Citations:**
- ArXiv: "LongCodeBench: Evaluating Coding LLMs at 1M Context Windows" (2025)
- IBM Research: "Why larger LLM context windows are all the rage"

---

### 1.3 File Size Limits

**Definition:** Individual source files <200-300 lines.

**Why It Matters:** Working memory handles ~4 objects simultaneously. Large files exceed cognitive capacity for both humans and AI.

**Impact on Agent Behavior:**
- More precise file selection
- Reduced irrelevant context in responses
- Safer targeted modifications
- Better understanding of module boundaries

**Measurable Criteria:**
- Target: <200-300 lines per file
- Warning threshold: 500 lines
- Exception: Generated code, data files
- Enforce via linters (e.g., pylint max-module-lines)

**Citations:**
- Stack Overflow: "At what point/range is a code file too big?"
- Medium: "Psychology of Code Readability" by Egon Elbre

---

## 2. DOCUMENTATION STANDARDS

### 2.1 README Structure

**Definition:** Standardized README with essential sections in predictable order.

**Why It Matters:** Repositories with well-structured READMEs receive more engagement (GitHub data). README serves as agent's entry point for understanding project purpose, setup, and usage.

**Impact on Agent Behavior:**
- Faster project comprehension
- Accurate answers to onboarding questions
- Better architectural understanding without exploring entire codebase
- Consistent expectations across projects

**Measurable Criteria:**
Essential sections (in order):
1. Project title and description
2. Quick start/usage examples (front-load actionable commands)
3. Installation/setup instructions
4. Core features
5. Testing instructions (how to run tests)
6. Dependencies and requirements
7. Contributing guidelines
8. License
- Root-level placement
- Hierarchical organization with clear section headers
- README <500 lines; use wiki/docs for extensive content

**Citations:**
- GitHub Blog: "How to write a great agents.md — lessons from over 2,500 repositories" (2026)
- Make a README project documentation
- Augment Code: "How to Build Your AGENTS.md" (2025)

---

### 2.2 Inline Documentation (Docstrings/Comments)

**Definition:** Function, class, and module-level documentation using language-specific conventions (Python docstrings, JSDoc/TSDoc).

**Why It Matters:** Type hints significantly improve LLM experience. Well-typed code directs LLMs into latent space regions corresponding to higher code quality—similar to how LaTeX-formatted math problems get better results.

**Impact on Agent Behavior:**
- Understanding function purpose without reading implementation
- Better parameter validation suggestions
- More accurate return type predictions
- Improved test generation
- Enhanced refactoring confidence

**Measurable Criteria:**
- All public functions/methods have docstrings
- Docstrings include: description, parameters, return values, exceptions, examples
- Python: PEP 257 compliant
- JavaScript/TypeScript: JSDoc or TSDoc
- Coverage: >80% of public API documented
- Tools: pydocstyle, documentation-js

**Citations:**
- Medium: "LLM Coding Concepts: Static Typing, Structured Output, and AsyncIO"
- ArXiv: "TypyBench: Evaluating LLM Type Inference for Untyped Python Repositories"
- TypeScript Documentation: JSDoc Reference

**Example:**
```python
# Good: Comprehensive docstring
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculate discounted price.

    Args:
        price: Original price in USD
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price

    Raises:
        ValueError: If discount_percent not in 0-100 range

    Example:
        >>> calculate_discount(100.0, 20.0)
        80.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be 0-100")
    return price * (1 - discount_percent / 100)

# Bad: No documentation
def calc_disc(p, d):
    return p * (1 - d / 100)
```

---

### 2.3 Architecture Decision Records (ADRs)

**Definition:** Lightweight documents capturing architectural decisions with context, decision, and consequences.

**Why It Matters:** ADRs provide historical context for "why" decisions were made. When AI encounters patterns or constraints, ADRs explain rationale, preventing counter-productive suggestions.

**Impact on Agent Behavior:**
- Understanding project evolution and design philosophy
- Avoiding proposing previously rejected alternatives
- Aligning suggestions with established architectural principles
- Better context for refactoring recommendations

**Measurable Criteria:**
- Store in `docs/adr/` or `.adr/` directory
- Use consistent template (Michael Nygard or MADR)
- Each ADR includes: Title, Status, Context, Decision, Consequences
- Status values: Proposed, Accepted, Deprecated, Superseded
- One decision per ADR
- Sequential numbering (ADR-001, ADR-002...)

**Citations:**
- AWS Prescriptive Guidance: "ADR process"
- GitHub: joelparkerhenderson/architecture-decision-record
- Microsoft Azure Well-Architected Framework

**Template:**
```markdown
# ADR-001: Use PostgreSQL for Primary Database

Status: Accepted

## Context
Need persistent storage supporting ACID transactions, complex queries, and JSON data.

## Decision
Use PostgreSQL 14+ as primary database.

## Consequences
Positive:
- Strong ACID guarantees
- Rich query capabilities (joins, window functions)
- JSON support via jsonb

Negative:
- More operational complexity than managed NoSQL
- Requires schema migration planning
- Horizontal scaling more complex
```

---

## 3. CODE QUALITY METRICS

### 3.1 Cyclomatic Complexity Thresholds

**Definition:** Measurement of linearly independent paths through code, indicating decision point density.

**Why It Matters:** High cyclomatic complexity confuses both humans and AI. While not perfect (doesn't capture cognitive complexity), it correlates strongly with testing difficulty and error potential.

**Impact on Agent Behavior:**
- Functions with complexity >25 are harder to understand
- Reduced confidence in safe modifications
- More difficult to generate comprehensive tests
- Increased likelihood of introducing bugs during refactoring

**Measurable Criteria:**
- Target: Cyclomatic complexity <10 per function
- Warning threshold: 15
- Error threshold: 25
- Tools: clang-tidy (C++), radon (Python), complexity-report (JavaScript), gocyclo (Go)

**Citations:**
- Microsoft Learn: "Code metrics - Cyclomatic complexity"
- Checkstyle Documentation
- LinearB Blog: "Cyclomatic Complexity explained"

---

### 3.2 Function/Method Length Limits

**Definition:** Keeping functions/methods small (typically <50 lines, ideally <20).

**Why It Matters:** Working memory handles ~4 objects simultaneously. Long functions exceed cognitive capacity. Research on reading comprehension shows lines >50-75 characters reduce comprehension; code has higher cognitive load per line.

**Impact on Agent Behavior:**
- Easier holistic function understanding
- Better isolation for testing
- Safer modifications without unintended side effects
- Clearer single responsibility principle adherence

**Measurable Criteria:**
- Target: <20 lines per function
- Warning: 50 lines
- Hard limit: 100 lines
- Exception: Complex algorithms with extensive explanatory comments
- Tools: pylint (max-function-lines), eslint (max-lines-per-function)

**Citations:**
- Medium: "Psychology of Code Readability" by Egon Elbre
- UX Stack Exchange: Line length readability research
- Clang-Tidy: readability-function-cognitive-complexity

---

### 3.3 Type Annotations (Static Typing)

**Definition:** Explicit type declarations for variables, parameters, and return values.

**Why It Matters:** Type hints significantly improve LLM code understanding. Higher-quality codebases have type annotations, directing LLMs toward higher-quality latent space regions. Creates synergistic improvement: LLMs generate better typed code, which helps future LLM interactions.

**Impact on Agent Behavior:**
- Better input validation and type error detection before execution
- Structured output generation
- Improved autocomplete suggestions
- Enhanced refactoring safety
- Type signatures serve as semantic anchors for agent reasoning about code dependencies

**Measurable Criteria:**
- Python: All public functions have parameter and return type hints
- TypeScript: `strict` mode enabled in tsconfig.json
- JavaScript: JSDoc type annotations at minimum
- Go: Inherently typed
- Coverage: >80% of functions typed
- Tools: mypy (Python), pyright (Python), tsc --strict (TypeScript)

**Citations:**
- Cursor: "Use typed languages, configure linters, and write tests. Give the agent clear signals for whether changes are correct." — cursor.com/blog/agent-best-practices
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 2.4 (April 2026)
- Medium: "LLM Coding Concepts: Static Typing, Structured Output"
- Dropbox Tech Blog: "Our journey to type checking 4 million lines of Python"
- ArXiv: "TypyBench: Evaluating LLM Type Inference for Untyped Python Repositories"


**Example:**
```python
# Good: Full type annotations
from typing import List, Optional

def find_users(
    role: str,
    active: bool = True,
    limit: Optional[int] = None
) -> List[User]:
    """Find users matching criteria."""
    query = User.query.filter_by(role=role, active=active)
    if limit:
        query = query.limit(limit)
    return query.all()

# Bad: No type hints
def find_users(role, active=True, limit=None):
    query = User.query.filter_by(role=role, active=active)
    if limit:
        query = query.limit(limit)
    return query.all()
```

---

### 3.4 Code Smell Elimination

**Definition:** Removing indicators of deeper problems: long methods, large classes, duplicate code, dead code, magic numbers.

**Why It Matters:** Research shows AI-generated code increases "code churn" (copy/paste vs. refactoring) and DRY principle violations. Clean baseline prevents AI from perpetuating anti-patterns.

**Impact on Agent Behavior:**
- Better intent understanding
- More accurate refactoring suggestions
- Avoidance of anti-pattern propagation
- Improved code quality over time

**Measurable Criteria:**
- Tools: SonarQube, PMD, Checkstyle, pylint, eslint
- Zero critical smells
- <5 major smells per 1000 lines of code
- Common smells monitored:
  - Duplicate code (DRY violations)
  - Long methods (>50 lines)
  - Large classes (>500 lines)
  - Long parameter lists (>5 params)
  - Divergent change (one class changing for multiple reasons)

**Citations:**
- GitClear: "Coding on Copilot" whitepaper
- Codacy Blog: "Code Smells and Anti-Patterns"
- ScienceDirect: "Code smells and refactoring: A tertiary systematic review"

---

## 4. REPOSITORY STRUCTURE

### 4.1 Standard Project Layouts

**Definition:** Using community-recognized directory structures for each language/framework.

**Why It Matters:** Standard layouts reduce cognitive overhead. AI models trained on open-source code recognize patterns (Python's src/, Go's cmd/ and internal/, Java's Maven structure).

**Impact on Agent Behavior:**
- Faster navigation
- Accurate location assumptions for new files
- Automatic adherence to established conventions
- Reduced confusion about file placement

**Measurable Criteria:**

**Python (src layout):**
```
project/
├── src/
│   └── package/
│       ├── __init__.py
│       └── module.py
├── tests/
├── docs/
├── README.md
├── pyproject.toml
└── requirements.txt
```

**Go:**
```
project/
├── cmd/           # Main applications
│   └── app/
│       └── main.go
├── internal/      # Private code
├── pkg/           # Public libraries
├── go.mod
└── go.sum
```

**JavaScript/TypeScript (Node.js):**
```
project/
├── src/
├── test/
├── dist/
├── package.json
├── package-lock.json
└── tsconfig.json
```

**Citations:**
- Real Python: "Python Application Layouts"
- GitHub: golang-standards/project-layout
- Stack Overflow: "Best project structure for Python application"

---

### 4.2 Separation of Concerns

**Definition:** Organizing code so each module/file/function has single, well-defined responsibility (SOLID principles).

**Why It Matters:** 2 of 5 SOLID principles derive directly from separation of concerns. Clear boundaries improve testability, maintainability, and reduce cognitive load.

**Impact on Agent Behavior:**
- Targeted modifications without affecting unrelated code
- Better refactoring suggestions
- Clearer module purpose understanding
- Reduced side effect risk

**Measurable Criteria:**
- Each module/class has one reason to change
- High cohesion within modules (related functions together)
- Low coupling between modules (minimal dependencies)
- Organize by feature/domain, not technical layer (avoid separate "controllers", "services", "models" directories)

**Citations:**
- Wikipedia: "Separation of concerns"
- DevIQ: "Separation of Concerns"
- Medium: "Single responsibility and Separation of concerns principles"

---

## 5. TESTING & CI/CD

### 5.1 Test Execution & Coverage

**Definition:** Ability to run tests with a single command, with adequate code coverage.

**Why It Matters:** Anthropic identifies test execution as "the single highest-leverage thing you can do" for AI agent effectiveness. Agents succeed through tight feedback loops: change code, run tests, see failures, iterate. Without runnable tests, agents fly blind. The DORA 2025 report confirms AI amplifies existing good testing practices — TDD is more critical than ever.

**Impact on Agent Behavior:**
- Enables self-correction through test-driven iteration
- Safety net enabling aggressive refactoring
- Tests document expected behavior
- Immediate feedback on breaking changes
- Higher confidence in suggested modifications

**Measurable Criteria:**
- Single-command test runner that works without external dependencies (no cluster access, no cloud credentials)
- Single-file/module test execution supported (e.g., `make test-unit PACKAGE=./pkg/...`)
- Clear separation of unit tests (agent can run) from integration tests (need infrastructure)
- Minimum: 70% line coverage
- Target: 80-90% line coverage
- Critical paths: 100% coverage
- Tools: pytest-cov (Python), Jest/Istanbul (JavaScript), go test -cover (Go)
- Coverage reports in CI/CD with failure threshold
- One real test per major code path is infinitely more valuable than zero tests

**Citations:**
- Anthropic: Claude Code Best Practices — "giving agents a way to verify their work" — code.claude.com/docs/en/best-practices
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 1.1 (April 2026)
- DORA 2025 (Google Cloud): "AI amplifies existing good practices. TDD is more critical than ever."
- LangChain Terminal-Bench: same model scored 52.8% vs 66.5% depending on scaffolding (+26%)
- Salesforce Engineering: "How Cursor AI Cut Legacy Code Coverage Time by 85%"

---

### 5.2 Test Naming Conventions

**Definition:** Descriptive test names following patterns like `test_should_<expected>_when_<condition>`.

**Why It Matters:** Clear test names help AI understand intent without reading implementation. When tests fail, AI diagnoses issues faster with self-documenting names.

**Impact on Agent Behavior:**
- Generation of similar test patterns
- Faster edge case understanding
- More accurate fix proposals aligned with intent
- Better test coverage gap identification

**Measurable Criteria:**
- Pattern: `test_<method>_<scenario>_<expected_outcome>`
- Example: `test_create_user_with_invalid_email_raises_value_error`
- Avoid: `test1`, `test_edge_case`, `test_bug_fix`, `test_method_name`
- Test names should be readable as sentences

**Citations:**
- pytest documentation: Test naming best practices
- JUnit best practices
- Go testing conventions

**Example:**
```python
# Good: Self-documenting test names
def test_create_user_with_valid_data_returns_user_instance():
    user = create_user(email="test@example.com", name="Test")
    assert isinstance(user, User)

def test_create_user_with_invalid_email_raises_value_error():
    with pytest.raises(ValueError, match="Invalid email"):
        create_user(email="not-an-email", name="Test")

def test_create_user_with_duplicate_email_raises_integrity_error():
    create_user(email="test@example.com", name="Test 1")
    with pytest.raises(IntegrityError):
        create_user(email="test@example.com", name="Test 2")

# Bad: Unclear test names
def test_user1():
    user = create_user(email="test@example.com", name="Test")
    assert user

def test_user2():
    with pytest.raises(ValueError):
        create_user(email="invalid", name="Test")
```

---

### 5.3 Pre-commit Hooks & CI/CD Linting

**Definition:** Automated code quality checks before commits (pre-commit hooks) and in CI/CD pipeline.

**Why It Matters:** Pre-commit hooks provide immediate feedback but can be bypassed. Running same checks in CI/CD ensures enforcement. Linting errors prevent successful CI runs, wasting time and compute.

**Impact on Agent Behavior:**
- Ensures AI-generated code meets quality standards
- Immediate feedback loop for improvements
- Consistent code style across all contributions
- Prevents low-quality code from entering repository

**Measurable Criteria:**
- Pre-commit framework installed and configured
- Hooks include:
  - Formatters: black/autopep8 (Python), prettier (JS/TS), gofmt (Go)
  - Linters: flake8/pylint (Python), eslint (JS/TS), golint (Go)
  - Type checkers: mypy/pyright (Python), tsc (TypeScript)
- **Critical:** Same checks run in CI/CD (non-skippable)
- CI fails on any linting error
- Fast execution: <30 seconds total

**Citations:**
- Memfault Blog: "Automatically format and lint code with pre-commit"
- Medium: "Elevate Your CI: Mastering Pre-commit Hooks and GitHub Actions"
- GitHub: pre-commit/pre-commit

---

## 6. DEPENDENCY MANAGEMENT

### 6.1 Lock Files for Reproducibility

**Definition:** Pinning exact dependency versions including transitive dependencies.

**Why It Matters:** Lock files ensure reproducible builds across environments. Without them, "works on my machine" problems plague AI-generated code. Different dependency versions can break builds, fail tests, or introduce bugs.

**Impact on Agent Behavior:**
- Confident dependency-related suggestions
- Accurate compatibility issue diagnosis
- Reproducible environment recommendations
- Version-specific API usage

**Measurable Criteria:**
- Lock file committed to repository
- **npm:** package-lock.json or yarn.lock
- **Python:** requirements.txt (from pip freeze), poetry.lock, or uv.lock
- **Go:** go.sum (automatically managed)
- **Ruby:** Gemfile.lock
- Lock file updated with every dependency change
- CI/CD uses lock file for installation

**Citations:**
- npm Blog: "Why Keep package-lock.json?"
- DEV Community: "Dependency management: package.json and package-lock.json explained"
- Python Packaging User Guide

---

### 6.2 Dependency Freshness & Security Scanning

**Definition:** Regularly updating dependencies and scanning for known vulnerabilities.

**Why It Matters:** Outdated dependencies introduce security risks and compatibility issues. AI-generated code may use deprecated APIs if dependencies are stale. Security vulnerabilities in dependencies can compromise entire application.

**Impact on Agent Behavior:**
- Suggestions use modern, non-deprecated APIs
- Awareness of security considerations
- Better library feature recommendations
- Avoidance of known vulnerability patterns

**Measurable Criteria:**
- Automated dependency updates: Dependabot, Renovate, or equivalent
- Security scanning in CI/CD: Snyk, npm audit, safety (Python), govulncheck (Go)
- Update cadence:
  - Patch versions: Weekly/automated
  - Minor versions: Monthly
  - Major versions: Quarterly with testing
- Zero known high/critical vulnerabilities in production
- Vulnerability response SLA: High severity within 7 days

**Citations:**
- GitHub Dependabot documentation
- OWASP Dependency-Check
- Snyk best practices
- npm audit documentation

---

## 7. GIT & VERSION CONTROL

### 7.1 Conventional Commit Messages

**Definition:** Structured commit messages following format: `<type>(<scope>): <description>`.

**Why It Matters:** Conventional commits enable automated semantic versioning, changelog generation, and commit intent understanding. AI can parse history to understand feature evolution and impact.

**Impact on Agent Behavior:**
- Generates properly formatted commit messages
- Understands which changes are breaking
- Appropriate version bump suggestions
- Better git history comprehension
- Automated changelog contribution

**Measurable Criteria:**
- Format: `type(scope): description`
- **Types:** feat, fix, docs, style, refactor, perf, test, chore, build, ci
- **Breaking changes:** `BREAKING CHANGE:` footer or `!` after type
- **Tools:** commitlint, commitizen, semantic-release
- **Enforcement:** Pre-commit hook or CI check
- All commits follow convention (enforce in CI)

**Citations:**
- Conventional Commits specification v1.0.0
- Medium: "GIT — Semantic versioning and conventional commits"
- CMU SEI Blog: "Versioning with Git Tags and Conventional Commits"

**Example:**
```
# Good commits
feat(auth): add OAuth2 login support
fix(api): handle null values in user response
docs(readme): update installation instructions
perf(database): add index on user_email column

# Breaking change
feat(api)!: change user endpoint from /user to /users

BREAKING CHANGE: User endpoint URL has changed from /user to /users.
Update all API clients accordingly.

# Bad commits
update stuff
fixed bug
changes
wip
asdf
```

---

### 7.2 .gitignore Completeness

**Definition:** Comprehensive .gitignore preventing sensitive files, build artifacts, and environment-specific files from version control.

**Why It Matters:** Incomplete .gitignore pollutes repository with irrelevant files, consuming context window space and creating security risks (accidentally committing .env files, credentials).

**Impact on Agent Behavior:**
- Focus on source code, not build artifacts
- Security files excluded prevent accidental exposure
- Cleaner repository navigation
- Reduced context pollution

**Measurable Criteria:**
- Use language-specific templates from github/gitignore
- **Exclude:**
  - Build artifacts (dist/, build/, *.pyc, *.class)
  - Dependencies (node_modules/, venv/, vendor/)
  - IDE files (.vscode/, .idea/, *.swp)
  - OS files (.DS_Store, Thumbs.db)
  - Environment variables (.env, .env.local)
  - Credentials (*.pem, *.key, credentials.json)
  - Logs (*.log, logs/)
- One .gitignore at repository root (avoid multiple nested)
- Review when adding new tools/frameworks

**Citations:**
- GitHub: github/gitignore template collection
- Medium: "Mastering .gitignore: A Comprehensive Guide"
- Git documentation

---

### 7.3 Issue & Pull Request Templates

**Definition:** Standardized templates for issues and PRs in .github/ directory.

**Why It Matters:** Templates provide structure for AI when creating issues or PRs. Ensures all necessary context is provided consistently.

**Impact on Agent Behavior:**
- Automatically fills templates when creating PRs
- Ensures checklist completion
- Consistent issue reporting format
- Better context for understanding existing issues/PRs

**Measurable Criteria:**
- `PULL_REQUEST_TEMPLATE.md` in .github/ or root
- Issue templates in `.github/ISSUE_TEMPLATE/`
- **PR template includes:**
  - Summary of changes
  - Related issues (Fixes #123)
  - Testing performed
  - Checklist (tests added, docs updated, etc.)
- **Issue templates for:**
  - Bug reports (with reproduction steps)
  - Feature requests (with use case)
  - Questions/discussions

**Citations:**
- GitHub Docs: "About issue and pull request templates"
- GitHub Blog: "Multiple issue and pull request templates"
- Embedded Artistry: "A GitHub Pull Request Template for Your Projects"

---

## 8. BUILD & DEVELOPMENT SETUP

### 8.1 One-Command Build/Setup

**Definition:** Single command to set up development environment from fresh clone.

**Why It Matters:** Lengthy setup documentation increases friction and errors. One-command setup enables AI to quickly reproduce environments and test changes. Reduces "works on my machine" problems.

**Impact on Agent Behavior:**
- Confident environment setup suggestions
- Quick validation of proposed changes
- Easy onboarding recommendations
- Reduced setup-related debugging

**Measurable Criteria:**
- Single command documented prominently in README
- **Examples:** `make setup`, `npm install`, `poetry install`, `./bootstrap.sh`
- **Command handles:**
  - Dependency installation
  - Virtual environment creation
  - Database setup/migrations
  - Configuration file creation (.env from .env.example)
  - Pre-commit hooks installation
- **Success criteria:** Working development environment in <5 minutes
- Idempotent (safe to run multiple times)

**Citations:**
- npm Blog: "Using Npm Scripts as a Build Tool"
- freeCodeCamp: "Want to know the easiest way to save time? Use make!"
- Medium: "Creating Reproducible Development Environments"

**Example:**
```makefile
# Good: Comprehensive Makefile
.PHONY: setup
setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	pre-commit install
	cp .env.example .env
	python manage.py migrate
	@echo "✓ Setup complete! Run 'make test' to verify."

.PHONY: test
test:
	pytest tests/ -v --cov

.PHONY: lint
lint:
	black --check .
	isort --check .
	flake8 .
	mypy .

.PHONY: format
format:
	black .
	isort .
```

---

### 8.2 Development Environment Documentation

**Definition:** Clear documentation of prerequisites, environment variables, and configuration.

**Why It Matters:** Environment differences cause "works on my machine" problems. Comprehensive docs enable reproducibility and faster debugging.

**Impact on Agent Behavior:**
- Accurate environment troubleshooting
- Better setup assistance for new contributors
- Environment-specific bug diagnosis
- Configuration recommendation accuracy

**Measurable Criteria:**
- **Prerequisites documented:**
  - Language/runtime version (Python 3.11+, Node.js 18+)
  - System dependencies (PostgreSQL, Redis, etc.)
  - Operating system requirements
- **Environment variables documented:**
  - .env.example file with all variables
  - Description of each variable
  - Required vs. optional clearly marked
  - Safe default values where applicable
- **Optional but helpful:**
  - IDE/editor setup (VS Code extensions, etc.)
  - Debugging configuration
  - Performance optimization tips

**Citations:**
- Medium: "Creating Reproducible Development Environments"
- InfoQ: "Reproducible Development with Containers"
- The Turing Way: "Reproducible Environments"

---

### 8.3 Container/Virtualization Setup

**Definition:** Docker/Podman configurations for consistent development environments.

**Why It Matters:** Containers provide portable, reproducible environments across operating systems. Development containers (devcontainers) are fully functional, batteries-included environments that are shared, versioned, and self-documenting.

**Impact on Agent Behavior:**
- Dockerfile improvement suggestions
- Container debugging assistance
- Consistent build recommendations
- Cross-platform development support

**Measurable Criteria:**
- Dockerfile or Containerfile in repository root
- docker-compose.yml for multi-service setups
- .devcontainer/devcontainer.json for VS Code/GitHub Codespaces
- **Dockerfile best practices:**
  - Multi-stage builds for smaller images
  - Non-root user
  - .dockerignore file
  - Explicit version tags (not :latest)
- Documentation on running containers
- Health checks defined

**Citations:**
- InfoQ: "Reproducible Development with Containers"
- Developer.com: "Creating a Reproducible and Portable Development Environment"
- Docker best practices documentation

---

## 9. ERROR HANDLING & DEBUGGING

### 9.1 Error Message Clarity

**Definition:** Descriptive error messages with context, remediation guidance, and relevant data.

**Why It Matters:** Clear errors enable AI to diagnose issues and suggest fixes. Vague errors ("Error 500", "Something went wrong") provide no actionable information.

**Impact on Agent Behavior:**
- Accurate root cause analysis
- Targeted solution proposals
- Faster debugging cycles
- Better user error handling suggestions

**Measurable Criteria:**
- **Include in error messages:**
  - What failed (operation/function)
  - Why it failed (validation, network, etc.)
  - How to fix it (actionable guidance)
  - Context: Request IDs, user IDs, timestamps, relevant parameters
- **Avoid:**
  - Generic messages ("Invalid input", "Error occurred")
  - Exposing internal stack traces to end users
  - Sensitive information in error messages
- **Provide:** Error codes for categorization
- Consistent error format across application

**Citations:**
- Honeycomb: "Engineers Checklist: Logging Best Practices"
- Paul Serban: "Error Logging Standards: A Practical Guide"
- Stack Overflow Blog: "Best practices for writing code comments"

**Example:**
```python
# Good: Descriptive error with context and guidance
raise ValueError(
    f"Invalid discount percentage: {discount_percent}. "
    f"Expected value between 0 and 100. "
    f"Received: {discount_percent} (type: {type(discount_percent).__name__}). "
    f"Fix: Ensure discount_percent is a number in range [0, 100]."
)

# Bad: Vague error
raise ValueError("Invalid input")

# Good: API error with context
{
    "error": {
        "code": "INVALID_DISCOUNT",
        "message": "Discount percentage must be between 0 and 100",
        "details": {
            "field": "discount_percent",
            "value": 150,
            "constraint": "0 <= value <= 100"
        },
        "request_id": "req_abc123"
    }
}
```

---

### 9.2 Structured Logging

**Definition:** Logging in structured format (JSON) with consistent field names and types.

**Why It Matters:** Structured logs are machine-parseable. AI can analyze logs to diagnose issues, identify patterns, suggest optimizations, and correlate events across distributed systems.

**Impact on Agent Behavior:**
- Log query and analysis capabilities
- Event correlation across services
- Pattern identification for debugging
- Data-driven optimization suggestions
- Anomaly detection

**Measurable Criteria:**
- Use structured logging library: structlog (Python), winston (Node.js), zap (Go)
- **Standard fields across all logs:**
  - timestamp (ISO 8601 format)
  - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - message (human-readable)
  - context: request_id, user_id, session_id, trace_id
- Consistent naming convention (snake_case or camelCase, not both)
- Log levels used appropriately
- **Never log sensitive data:** passwords, tokens, credit cards, PII (without anonymization)
- JSON format for production

**Citations:**
- Daily.dev: "12 Logging Best Practices: Do's & Don'ts"
- Dataset Blog: "Logging Best Practices: The 13 You Should Know"
- Technogise Medium: "Logging Practices: Guidelines for Developers"

**Example:**
```python
# Good: Structured logging
import structlog

logger = structlog.get_logger()

logger.info(
    "user_login_success",
    user_id="user_123",
    request_id="req_abc",
    duration_ms=45,
    ip_address="192.168.1.1"
)

# Output:
# {"timestamp": "2025-01-20T10:30:00Z", "level": "info", "event": "user_login_success",
#  "user_id": "user_123", "request_id": "req_abc", "duration_ms": 45, "ip_address": "192.168.1.1"}

# Bad: Unstructured logging
print("User user_123 logged in from 192.168.1.1 in 45ms")
```

---

## 10. API & INTERFACE DOCUMENTATION

### 10.1 OpenAPI/Swagger Specifications

**Definition:** Machine-readable API documentation in OpenAPI format (formerly Swagger).

**Why It Matters:** OpenAPI specs define everything needed to integrate with an API: authentication, endpoints, HTTP methods, request/response schemas, error codes. AI can read specs to generate client code, tests, and integration code automatically.

**Impact on Agent Behavior:**
- Auto-generation of SDKs and client libraries
- Request/response validation
- API mocking for testing
- Contract compliance verification
- Interactive API exploration

**Measurable Criteria:**
- OpenAPI 3.0+ specification file (openapi.yaml or openapi.json)
- **All endpoints documented with:**
  - Description and purpose
  - HTTP method (GET, POST, PUT, DELETE, PATCH)
  - Parameters (path, query, header)
  - Request body schema
  - Response schemas (success and error cases)
  - Authentication requirements
  - Example requests/responses
- Validation: Use Swagger Editor or Spectral
- Auto-generate from code annotations OR keep manually in sync
- Hosted documentation (Swagger UI, ReDoc)

**Citations:**
- Swagger Blog: "API Documentation Best Practices"
- APItoolkit: "OpenAPI Specification for API Development"
- APImatic: "14 Best Practices to Write OpenAPI for Better API Consumption"

**Example:**
```yaml
# Good: Comprehensive OpenAPI spec
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users/{userId}:
    get:
      summary: Get user by ID
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: string
        email:
          type: string
          format: email
        name:
          type: string
```

---

### 10.2 GraphQL Schemas

**Definition:** Type definitions for GraphQL APIs using Schema Definition Language (SDL).

**Why It Matters:** GraphQL schemas are self-documenting and introspectable. AI can understand available queries, mutations, types, and relationships without exploring implementation code.

**Impact on Agent Behavior:**
- Generate type-safe queries
- Schema validation
- Performance optimization suggestions (N+1 query detection)
- Type-safe client generation
- API evolution guidance

**Measurable Criteria:**
- schema.graphql file in repository
- All types, queries, mutations include descriptions
- Use directives for:
  - Deprecation (@deprecated)
  - Authorization (@auth)
  - Field resolution hints
- Schema validation in CI/CD
- SDL-first approach (schema-first, not code-first)

**Citations:**
- GraphQL documentation: "Schema Definition Language"
- Apollo GraphQL: "Schema design best practices"
- Hasura GraphQL best practices

**Example:**
```graphql
# Good: Well-documented GraphQL schema
"""
Represents a user in the system
"""
type User {
  """
  Unique identifier for the user
  """
  id: ID!

  """
  User's email address (unique)
  """
  email: String!

  """
  User's display name
  """
  name: String

  """
  Posts created by this user
  """
  posts: [Post!]!
}

type Query {
  """
  Find a user by their unique ID
  """
  user(id: ID!): User

  """
  List all users with optional filtering
  """
  users(role: String, active: Boolean): [User!]!
}
```

---

## 11. MODULARITY & CODE ORGANIZATION

### 11.1 DRY Principle (Don't Repeat Yourself)

**Definition:** Every piece of knowledge has single, authoritative representation in the system.

**Why It Matters:** Research shows AI-generated code increases code churn and DRY violations (copy-paste instead of refactoring). Enforcing DRY in codebase teaches AI to refactor rather than duplicate.

**Impact on Agent Behavior:**
- Learns to extract shared logic
- Suggests refactorings instead of duplication
- Avoids creating duplicate implementations
- Better abstraction identification

**Measurable Criteria:**
- "Three Strikes" rule: Third duplicate occurrence triggers refactoring
- Tools detect duplication: SonarQube, PMD (Java), jscpd (JavaScript), pylint (Python)
- Shared logic extracted to:
  - Utility functions/modules
  - Base classes
  - Mixins/traits
  - Libraries
- **Balance:** Avoid premature abstraction ("prefer duplication over wrong abstraction")
- Target: <5% duplicate code

**Citations:**
- Wikipedia: "Don't repeat yourself"
- The Pragmatic Programmer by Hunt & Thomas
- Medium: "The DRY Principle and Incidental Duplication"
- Sandi Metz: "The Wrong Abstraction"

---

### 11.2 Consistent Naming Conventions

**Definition:** Systematic naming patterns for variables, functions, classes, files following language/framework conventions.

**Why It Matters:** Research shows identifier style affects recall and precision. Consistency reduces cognitive load. AI models recognize naming patterns from training on open-source code.

**Impact on Agent Behavior:**
- Accurate intent inference
- Appropriate name suggestions
- Code structure understanding
- Pattern recognition

**Measurable Criteria:**
- Follow language conventions:
  - **Python:** PEP 8 (snake_case functions, PascalCase classes, UPPER_CASE constants)
  - **JavaScript/TypeScript:** camelCase functions/variables, PascalCase classes
  - **Go:** mixedCaps (exported: UpperCase, unexported: lowerCase)
  - **Java:** camelCase methods, PascalCase classes, UPPER_CASE constants
- Use paired opposites consistently: add/remove, start/stop, begin/end, open/close
- Avoid abbreviations unless widely understood (HTTP, API, URL, ID)
- Enforce via linters: pylint, eslint, golint

**Citations:**
- Wikipedia: "Naming convention (programming)"
- Microsoft Learn: "General Naming Conventions"
- PEP 8 - Style Guide for Python Code
- Google Style Guides (Java, Python, JavaScript, Go)

**Example:**
```python
# Good: Consistent naming
class UserService:
    MAX_LOGIN_ATTEMPTS = 5

    def create_user(self, email: str) -> User:
        """Create new user."""
        pass

    def delete_user(self, user_id: str) -> None:
        """Delete existing user."""
        pass

# Bad: Inconsistent naming
class userservice:
    maxLoginAttempts = 5

    def CreateUser(self, e: str) -> User:
        pass

    def removeUser(self, uid: str) -> None:
        pass
```

---

### 11.3 Semantic File & Directory Naming

**Definition:** File names and directory structures that convey purpose and content clearly.

**Why It Matters:** Semantic organization helps AI locate relevant code quickly. Clear names reduce cognitive overhead and enable predictable file location.

**Impact on Agent Behavior:**
- Faster relevant file location
- Accurate placement suggestions for new code
- Better repository organization understanding
- Reduced search time

**Measurable Criteria:**
- **Feature-based organization:** Group related files by feature/domain, not technical layer
- **Clear, descriptive names:** `user_service.py` not `us.py`
- **Avoid abbreviations** unless standard in domain
- **Mirror test structure** to source structure:
  - `src/services/user_service.py` → `tests/services/test_user_service.py`
- **Consistent file extensions:** .py, .js, .ts, .go
- **Module files:** `__init__.py`, index.js for package entry points

**Citations:**
- GitHub: kriasoft/Folder-Structure-Conventions
- Iterators: "Comprehensive Guide on Project Codebase Organization"
- Medium: "A Front-End Application Folder Structure that Makes Sense"

**Example:**
```
# Good: Feature-based, semantic organization
src/
├── auth/
│   ├── __init__.py
│   ├── login_service.py
│   ├── oauth_provider.py
│   └── session_manager.py
├── users/
│   ├── __init__.py
│   ├── user_model.py
│   ├── user_service.py
│   └── user_repository.py
└── billing/
    ├── __init__.py
    ├── payment_processor.py
    └── invoice_generator.py

# Bad: Technical layer organization, unclear names
src/
├── models/
│   ├── u.py
│   └── o.py
├── services/
│   ├── svc1.py
│   └── svc2.py
└── utils/
    └── helpers.py
```

---

## 12. CI/CD INTEGRATION

### 12.1 CI/CD Pipeline Visibility

> **Note:** This section provides background research context. The assessed attribute is **16.2 CI Quality Gates** (`ci_quality_gates`), which elevated CI enforcement to Tier 1 at 5% weight.

**Definition:** Clear, well-documented CI/CD configuration files committed to repository.

**Why It Matters:** AI can understand build/test/deploy processes by reading CI configs. When builds fail, AI can suggest targeted fixes. Visible pipelines enable collaboration and debugging.

**Impact on Agent Behavior:**
- CI improvement proposals
- Pipeline failure debugging
- Workflow optimization suggestions
- Better understanding of deployment process

**Measurable Criteria:**
- CI config file in repository:
  - GitHub Actions: `.github/workflows/`
  - GitLab CI: `.gitlab-ci.yml`
  - CircleCI: `.circleci/config.yml`
- **Clear job/step names** (not "step1", "step2")
- **Comments explaining complex logic**
- **Fast feedback:** Tests complete <10 minutes
- **Fail fast:** Stop on first failure to save compute
- **Parallelization:** Run independent jobs concurrently
- **Caching:** Dependencies, build artifacts
- **Artifacts:** Test results, coverage reports, logs

**Citations:**
- CircleCI: "Monorepo dev practices"
- GitHub Actions documentation
- GitLab CI best practices
- Martin Fowler: "Continuous Integration"

---

### 12.2 Branch Protection & Status Checks

**Definition:** Required status checks and review approvals before merging to main/production branches.

**Why It Matters:** Prevents broken code from reaching production. Provides safety net for AI-generated code. Ensures quality gates are enforced.

**Impact on Agent Behavior:**
- Understanding of merge requirements
- Awareness of quality gates
- Suggestions aligned with branch policies
- Better PR creation (ensuring checks pass)

**Measurable Criteria:**
- Branch protection enabled for main/master/production
- **Required status checks:**
  - All tests passing
  - Linting/formatting passing
  - Code coverage threshold met
  - Security scanning passing
- **Required reviews:** At least 1 approval
- **No force pushes** to protected branches
- **No direct commits** to protected branches
- **Up-to-date branch** requirement (rebase/merge before merging)

**Citations:**
- GitHub Docs: "About protected branches"
- GitLab: "Protected branches"
- Industry best practices

---

## 13. SECURITY & COMPLIANCE

### 13.1 Security Scanning Automation

**Definition:** Automated security scans for vulnerabilities, secrets, and compliance issues in CI/CD.

**Why It Matters:** AI can accidentally introduce vulnerabilities (SQL injection, XSS, etc.). Research shows LLM-generated code has security weaknesses, particularly around outdated practices. Automated scanning provides safety net.

**Impact on Agent Behavior:**
- Security pattern learning
- Vulnerability avoidance
- Secure coding practice adoption
- Failed scans provide improvement feedback

**Measurable Criteria:**
- **Dependency scanning:** Snyk, Dependabot, npm audit, safety (Python)
- **Secret scanning:** GitLeaks, TruffleHog, detect-secrets
- **Static analysis:** Semgrep, CodeQL, Bandit (Python), gosec (Go)
- **Scans run on:**
  - Every PR (pre-merge)
  - Every commit to main
  - Scheduled (weekly/nightly)
- **Zero tolerance:** No high/critical vulnerabilities allowed to merge
- **SLA:** High severity vulnerabilities fixed within 7 days

**Citations:**
- ArXiv: "Security and Quality in LLM-Generated Code"
- ArXiv: "Security Degradation in Iterative AI Code Generation"
- GitHub Advanced Security documentation
- OWASP Top 10

---

### 13.2 Secrets Management

**Definition:** Proper handling of sensitive data (API keys, passwords, tokens) using secret management tools, not hardcoded values.

**Why It Matters:** Hardcoded secrets in code create security vulnerabilities. AI might accidentally suggest or expose secrets. Proper secrets management is critical security practice.

**Impact on Agent Behavior:**
- Avoids suggesting hardcoded secrets
- Recommends environment variables
- Identifies potential secret exposure
- Suggests secure alternatives

**Measurable Criteria:**
- **No secrets in code:** Use environment variables, secret managers
- **Tools:**
  - Development: .env files (not committed), direnv
  - Production: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager
- **.env.example** committed (without real values)
- **.env** in .gitignore
- **Secret rotation** documented and automated
- **Pre-commit hook:** Detect-secrets or similar

**Citations:**
- OWASP: "Secrets Management Cheat Sheet"
- GitHub: "Removing sensitive data from a repository"
- HashiCorp Vault documentation

---

## 14. DOCUMENTATION PHILOSOPHY

### 14.1 "Why, Not What" Comments

**Definition:** Comments explain rationale and context, not behavior (which code already shows).

**Why It Matters:** AI can read code to understand "what" it does. Comments providing "why" give context for decisions, workarounds, constraints, and edge cases that aren't obvious from code alone.

**Impact on Agent Behavior:**
- Understanding of constraints and limitations
- Avoidance of "obvious" refactorings that break assumptions
- Preservation of original intent during modifications
- Better context for debugging and optimization

**Measurable Criteria:**
- **Comments explain:**
  - Why this approach was chosen (vs. alternatives)
  - Edge cases and gotchas
  - Performance considerations
  - Historical context (why workaround exists)
  - TODOs with context and rationale
- **Avoid:**
  - Redundant comments duplicating code
  - Commented-out code (use version control)
  - Obvious statements
- **Keep comments in sync** with code during changes

**Citations:**
- Stack Overflow Blog: "Best practices for writing code comments"
- Stepsize: "The Engineer's Guide to Writing Meaningful Code Comments"
- Boot.dev: "Best Practices for Commenting Code"

**Example:**
```python
# Good: Explains "why"
# Using binary search instead of hash table because dataset is
# read-once and memory-constrained (< 100MB available).
# Hash table would require 150MB for this dataset size.
result = binary_search(sorted_data, target)

# API returns 202 Accepted for async processing, but we need
# synchronous behavior for consistency. Poll until completion.
response = api.start_job()
while response.status == 202:
    time.sleep(1)
    response = api.check_status(response.job_id)

# Bad: Redundant, explains "what"
# Search for target in sorted_data
result = binary_search(sorted_data, target)

# Call the API
response = api.start_job()
```

---

## 15. PERFORMANCE & OBSERVABILITY

### 15.1 Performance Benchmarks

**Definition:** Automated performance tests tracking metrics like response time, throughput, memory usage.

**Why It Matters:** Performance regressions can slip in unnoticed. Benchmarks provide objective measurements. AI can suggest optimizations based on benchmark results.

**Impact on Agent Behavior:**
- Performance-aware optimization suggestions
- Regression detection
- Data-driven refactoring decisions
- Bottleneck identification

**Measurable Criteria:**
- Benchmark suite in repository
- **Tools:** pytest-benchmark (Python), Benchmark.js (JavaScript), testing.B (Go)
- Run benchmarks in CI for critical paths
- Track metrics over time
- Alert on regressions (>10% slowdown)

**Citations:**
- Google: "Benchmarking Best Practices"
- Python performance benchmarking docs
- Go benchmarking documentation

---

## 16. VERIFICATION & FEEDBACK LOOPS

### 16.1 Single-File Verification

**Definition:** Ability to lint and type-check individual files quickly without a full build step.

**Why It Matters:** Fast feedback loops separate agents that self-correct from agents that spiral. If linting the whole project takes 2 minutes, the agent won't lint after each change. If linting a single file takes 2 seconds, it will. This is the foundation of agent self-correction.

**Impact on Agent Behavior:**
- Enables rapid iteration after each code change
- Agent can verify its own work in real-time
- Catches errors before they compound
- Reduces wasted compute on broken intermediate states

**Measurable Criteria:**
- Single-file lint command documented (e.g., `npx eslint --fix path/to/file.tsx`)
- Single-file type-check command available (e.g., `npx tsc --noEmit`)
- Commands work without a full build step first
- Commands execute in <5 seconds per file
- Documented in CLAUDE.md/AGENTS.md or README

**Citations:**
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 1.3 (April 2026)
- Anthropic: Claude Code Best Practices — code.claude.com/docs/en/best-practices
- Factory.ai: "Using Linters to Direct Agents"

---

### 16.2 CI Quality Gates

**Definition:** CI/CD pipelines that run lint, type-check, and tests on every PR as mandatory quality gates.

**Why It Matters:** "Lint passing" becomes a machine-verifiable proxy for "conforms to architecture and best practices." Agents read CI output and iterate on failures. Without enforceable gates, advisory instructions in context files may be ignored.

**Impact on Agent Behavior:**
- Provides definitive pass/fail signal for agent-generated code
- CI failure messages guide agent self-correction
- Prevents low-quality code from entering repository
- Creates a feedback loop that improves agent output over time

**Measurable Criteria:**
- CI runs lint, type-check, and tests on every PR
- CI output is readable (not buried in noise)
- Failure messages point directly to the problem
- Fast feedback: tests complete in <10 minutes
- Fail fast: stop on first failure to save compute
- Quality gates are mandatory (not optional/advisory)

**Citations:**
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 1.4 (April 2026)
- Factory.ai: "Agents write the code; linters write the law."
- Stack Overflow: "Coding Guidelines for AI Agents" (March 2026)

---

## 17. AGENT PATTERNS & KNOWLEDGE

### 17.1 Pattern References for Common Changes

**Definition:** Documented reference implementations and examples for the most common types of changes in a codebase.

**Why It Matters:** Pattern references turn novel changes into copy-modify changes, which agents handle far more reliably. The Stack Overflow team found that explicit examples (both correct and incorrect) dramatically improved agent output quality.

**Impact on Agent Behavior:**
- Reduces agent from "creating from scratch" to "adapting a known pattern"
- Higher consistency across agent-generated changes
- Fewer architectural violations
- Faster task completion

**Measurable Criteria:**
- 3-5 pattern references for most common change types (e.g., new API endpoint, new UI component, new adapter)
- Each pattern points to a real example in the codebase
- Patterns documented as SKILL.md files in `.claude/skills/` or equivalent
- Each pattern includes: reference file path, step-by-step instructions, key invariants

**Example:**
```
.claude/skills/
  add-api-endpoint/
    SKILL.md        # Points to src/api/handlers/users.ts as reference
  add-adapter/
    SKILL.md
  add-migration/
    SKILL.md
```

**Citations:**
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 2.1 (April 2026)
- Stack Overflow: "Coding Guidelines for AI Agents" (March 2026)
- Anthropic: Claude Code Skills Documentation — code.claude.com/docs/en/skills

---

### 17.2 Design Intent Documentation

**Definition:** Documentation of architectural intent, preconditions, invariants, and design rationale that cannot be inferred from code alone.

**Why It Matters:** Agents can discover *what* code does by reading it, but not *why* it was designed that way, what invariants must hold, or what preconditions are assumed. Without this, agents make changes that pass tests but violate design contracts — subtle breakage that surfaces later.

**Impact on Agent Behavior:**
- Prevents changes that pass tests but violate design contracts
- Understanding of constraints and limitations
- Avoidance of "obvious" refactorings that break assumptions
- Preservation of architectural intent during modifications

**Measurable Criteria:**
- `docs/design/` or `docs/architecture/` directory exists
- Design docs include:
  - Preconditions ("assumes auth middleware has validated token")
  - Invariants ("event log is append-only; never mutate or delete")
  - Design rationale ("polling instead of webhooks because upstream SLA is 5s")
- Design docs are referenced from context file
- Design docs updated when architectural changes are made

**Citations:**
- Red Hat: Repository Scaffolding for AI Coding Agents, Section 2.3 (April 2026)
- Martin Fowler: "Context Engineering for Coding Agents" (Feb 2026)

---

### 17.3 Progressive Disclosure

**Definition:** Hierarchical context organization where root-level files provide orientation and component-level files provide detail, loading only when relevant.

**Why It Matters:** For repos exceeding ~100K lines, a single root context file cannot provide module-level orientation without becoming too long. Progressive disclosure keeps context lean while providing depth where needed. Once context files exceed ~150 lines, you pay a context tax on every session for rarely-needed information.

**Impact on Agent Behavior:**
- Reduces context pollution from irrelevant information
- Module-specific guidance loads only when working in that area
- Enables large repos to provide rich agent context without bloat
- Skills load on-demand rather than consuming context every session

**Measurable Criteria:**
- Root CLAUDE.md/AGENTS.md <150 lines, acting as routing layer
- `.claude/rules/` directory with path-scoped frontmatter for module-specific rules
- Subdirectory context files for frequently-changed modules
- `.claude/skills/` directory for on-demand knowledge (loads only when relevant)
- Skills have YAML frontmatter (~100 tokens) for relevance scanning

**Example:**
```markdown
# .claude/rules/api-module.md
---
paths:
  - "src/api/**/*.ts"
---

# API Module Rules
- All endpoints use middleware chain in src/api/middleware/
- Request validation uses zod schemas in src/api/schemas/
- Response types generated from OpenAPI spec — don't edit types.generated.ts
```

**Citations:**
- Red Hat: Repository Scaffolding for AI Coding Agents, Sections 3.1 and 4.1 (April 2026)
- Anthropic: Claude Code Skills Documentation — code.claude.com/docs/en/skills
- ETH Zurich: "Are Repository-Level Context Files Helpful for Coding Agents?" (Feb 2026) — context efficiency findings

---

## IMPLEMENTATION PRIORITIES

### Tier 1: Essential (Must-Have) — 55% of score
**Highest impact. Verification and fast feedback loops first, then context and structure:**

1. **Test execution** (10%) — Single-command test runner. "The single highest-leverage thing." (Anthropic)
2. **Type annotations** (8%) — Structural signals for agent navigation and correctness
3. **CLAUDE.md/AGENTS.md** (7%) — Minimal, hand-written, <150 lines, 6 core areas
4. **CI quality gates** (5%) — Lint + type-check + tests on every PR
5. **Single-file verification** (5%) — Fast lint/type-check per file for tight feedback loops
6. **README with quick start** (5%) — Entry point with actionable commands
7. **Standard project layout** (5%) — Language-specific directory conventions
8. **Dependency lock files** (5%) — Reproducible builds
9. **Dependency security** (5%) — Vulnerability scanning and updates

### Tier 2: Critical (Should-Have) — 27% of score
**Quality improvements, enforcement, and patterns (3% each):**

10. **Deterministic enforcement** — Hooks + lint rules > advisory instructions
11. **Conventional commits** — Semantic versioning, history understanding
12. **Complete .gitignore** — Reduced context pollution
13. **One-command setup** — Single command for build, test, lint
14. **Concise documentation** — Information-dense, structured docs
15. **Inline documentation** — Docstrings >80% public API
16. **File size limits** — <200-300 lines per file
17. **Separation of concerns** — Feature-based organization
18. **Pattern references** — 3-5 reference implementations for common changes

### Tier 3: Important (Nice-to-Have) — 14% of score
**Significant improvements in specific areas (2-3% each):**

19. **Design intent documentation** — Preconditions, invariants, rationale
20. **Cyclomatic complexity limits** — Better code comprehension
21. **Structured logging** — Machine-parseable debugging
22. **OpenAPI/GraphQL specs** — Machine-readable API surfaces
23. **Architecture Decision Records** — Architectural context

### Tier 4: Advanced (Optimization) — 4% of score
**Refinement for teams at scale (1% each):**

24. **Code smell elimination** — Higher quality baseline
25. **Issue & PR templates** — Consistent contributions
26. **Container setup** — Reproducible environments
27. **Progressive disclosure** — Path-scoped rules and skills for large repos

---

## QUICKSTART: Making Your Codebase Agent-Ready

**The meta-lesson:** Teams shipping reliable AI-generated code invest in fast verification loops, minimal context files, and deterministic enforcement. Not clever prompts.

### Week 1: Verification First (Highest Impact)
```bash
# 1. Ensure tests run with a single command (no external deps)
pytest tests/               # Python
npm test                    # JavaScript
go test ./...               # Go

# 2. Ensure single-file lint commands work
npx eslint --fix path/to/file.ts   # JavaScript/TypeScript
ruff check path/to/file.py         # Python
golangci-lint run path/to/file.go  # Go

# 3. Ensure CI runs lint + type-check + tests on every PR
# Check .github/workflows/ or equivalent

# 4. Write minimal CLAUDE.md (hand-written, <150 lines)
cat > CLAUDE.md << 'EOF'
# Project Name

## Build & Test Commands
- Test all: `pytest tests/`
- Test single: `pytest tests/path/to/test.py`
- Lint: `ruff check .`
- Type check: `mypy src/`

## Key Conventions
- [3-5 rules the agent can't infer from code]

## Boundaries
- Never modify files in legacy/
EOF
```

### Week 2: Enforcement & Types
```bash
# Add type annotations to public APIs
mypy --install-types  # Python
tsc --init            # TypeScript

# Set up hooks for deterministic enforcement
# Auto-format on edit, block destructive operations
# Configure in .claude/settings.json for team-wide sharing

# Set up pre-commit
pip install pre-commit
pre-commit install
```

### Week 3: Dependencies & Patterns
```bash
# Generate lock file
pip freeze > requirements.txt  # Python
npm install                    # Generates package-lock.json
go mod tidy                    # Updates go.sum

# Add Dependabot or Renovate
# Create .github/dependabot.yml

# Add 3-5 pattern references for common changes
mkdir -p .claude/skills
# Point to real reference implementations in the codebase
```

### Week 4: Documentation & Structure
```bash
# Update README with testing instructions
# Create PR/Issue templates
mkdir -p .github/ISSUE_TEMPLATE

# Audit design docs against codebase
# Reverse-engineer missing design docs for critical modules
mkdir -p docs/design
```

### Ongoing
- When a code review catches an agent mistake, add a rule to CLAUDE.md or a lint rule
- Periodically audit context file: is every line still preventing a real failure?
- Addy Osmani: "Treat AGENTS.md as a living list of codebase smells you haven't fixed yet"

---

## MEASUREMENT & VALIDATION

### Agent-Ready Score Formula

```
Score = (
    Documentation * 0.25 +
    Code Quality * 0.20 +
    Testing * 0.20 +
    Structure * 0.15 +
    CI/CD * 0.10 +
    Security * 0.10
) * 100

Where each category is 0.0-1.0 based on attribute completion.
```

### Certification Levels

- **Platinum (90-100):** Exemplary agent-ready codebase
- **Gold (75-89):** Highly optimized for agents
- **Silver (60-74):** Well-suited for agent development
- **Bronze (40-59):** Basic agent compatibility
- **Needs Improvement (<40):** Significant agent friction

### Validation Checklist

**Verification & Feedback Loops (Tier 1 priorities):**
- [ ] Tests run with a single command (no external dependencies)
- [ ] Single-file lint command available and documented
- [ ] CI runs lint + type-check + tests on every PR
- [ ] CI failure messages point to the problem

**Context & Documentation:**
- [ ] CLAUDE.md/AGENTS.md exists, hand-written, <150 lines
- [ ] Covers 6 core areas: commands, testing, structure, style, git, boundaries
- [ ] README with quick start and testing instructions
- [ ] Inline documentation (docstrings) >80%

**Code Quality:**
- [ ] Type annotations >80%
- [ ] Cyclomatic complexity <10
- [ ] File size <300 lines
- [ ] Separation of concerns (feature-based organization)

**Structure & Dependencies:**
- [ ] Standard project layout
- [ ] Dependency lock files committed
- [ ] Dependency security scanning configured
- [ ] Complete .gitignore

**Enforcement & Patterns:**
- [ ] Hooks for auto-format and safety (deterministic enforcement)
- [ ] 3-5 pattern references for common changes
- [ ] Conventional commit enforcement
- [ ] Design intent documented for critical modules

---

## ANTI-PATTERNS TO AVOID

| Anti-Pattern | Why It Fails | Do This Instead |
|---|---|---|
| Auto-generate context file and ship it | -3% success rate, +20% cost (ETH Zurich) | Hand-write, keep minimal |
| Exhaustive architecture narratives in context file | Agents discover structure on their own | Document only non-obvious decisions |
| Context file > 300 lines | Adherence drops, context diluted | Split into skills and path-scoped rules |
| No way to verify changes | Agent flies blind, can't self-correct | Provide runnable tests and lint commands |
| Advisory-only conventions | Agent may not follow them | Enforce with lint rules and hooks |
| Static context file, never updated | Context rot as codebase evolves | Treat review comments as update signals |
| No tests or minimal coverage (<30%) | No safety net for agent changes | One real test per code path minimum |
| Slow test suite (>30 min) | Agent can't iterate | Provide single-module test command |

### Additional Anti-Patterns
- ❌ God objects/functions (>500 lines)
- ❌ No type hints
- ❌ Magic numbers without explanation
- ❌ Unclear variable names (x, tmp, data)
- ❌ Test names like test1, test2
- ❌ Flat file structure with mixed concerns
- ❌ Inconsistent naming conventions
- ❌ Incomplete .gitignore
- ❌ No CI/CD or manual-only quality checks
- ❌ Direct commits to main without branch protection

---

## REFERENCES & CITATIONS

### Key Research (2025-2026)
- [ETH Zurich: "Are Repository-Level Context Files Helpful for Coding Agents?"](https://arxiv.org/html/2602.11988v1) (Feb 2026) — the landmark study on context file effectiveness
- [Anthropic: Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/2026-agentic-coding-trends-report)
- Red Hat: Repository Scaffolding for AI Coding Agents (April 2026) — internal guide, evidence-based
- LangChain: Terminal-Bench — scaffolding impact measurement (+26% accuracy from infrastructure alone)
- [DORA 2025 (Google Cloud): TDD and AI Quality](https://cloud.google.com/discover/how-test-driven-development-amplifies-ai-success)
- [AGENTS.md Empirical Study: Agent READMEs](https://arxiv.org/html/2511.12884v1) — analysis of 2,303 context files
- [Configuring Agentic AI Coding Tools](https://arxiv.org/html/2602.14690v3) — systematic study across 2,923 repos

### Industry Guidance
- [GitHub Blog: "How to write a great agents.md — lessons from over 2,500 repositories"](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [Addy Osmani: "Stop Using /init for AGENTS.md"](https://addyosmani.com/blog/agents-md/) (Feb 2026)
- [Martin Fowler: Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html) (Feb 2026)
- [Factory.ai: Using Linters to Direct Agents](https://factory.ai/news/using-linters-to-direct-agents)
- [Stack Overflow: Coding Guidelines for AI Agents](https://stackoverflow.blog/2026/03/26/coding-guidelines-for-ai-agents-and-people-too/) (Mar 2026)
- [Cursor: Agent Best Practices](https://cursor.com/blog/agent-best-practices)
- [OpenAI Codex: AGENTS.md Guide](https://developers.openai.com/codex/guides/agents-md)
- [Augment Code: How to Build Your AGENTS.md](https://www.augmentcode.com/guides/how-to-build-agents-md)
- [AGENTS.md Official Site](https://agents.md/)
- [Microsoft Learn: "Code metrics - Cyclomatic complexity"](https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity)
- [GitHub: github/gitignore template collection](https://github.com/github/gitignore)
- [Google SRE Book: Logging and monitoring best practices](https://sre.google/sre-book/monitoring-distributed-systems/)

### Security
- [OpenSSF: Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) (Sep 2025)
- OWASP: Top 10 for Agentic Applications (Dec 2025)

### Engineering Blogs
- [Dropbox Tech Blog: "Our journey to type checking 4 million lines of Python"](https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python)
- [Salesforce Engineering: "How Cursor AI Cut Legacy Code Coverage Time by 85%"](https://engineering.salesforce.com/)
- [GitClear: "Coding on Copilot" whitepaper](https://www.gitclear.com/coding_on_copilot_data_shows_ais_downward_pressure_on_code_quality)

### Standards & Specifications
- [Conventional Commits specification v1.0.0](https://www.conventionalcommits.org/)
- [OpenAPI Specification 3.0+](https://spec.openapis.org/oas/v3.0.0)
- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [MCP Specification v2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)

### Community Resources
- [Real Python: "Python Application Layouts"](https://realpython.com/python-application-layouts/)
- [GitHub: golang-standards/project-layout](https://github.com/golang-standards/project-layout)
- [GitHub: joelparkerhenderson/architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record)
- [GitHub: pre-commit/pre-commit](https://github.com/pre-commit/pre-commit)
- [GitHub: agentsmd/agents.md](https://github.com/agentsmd/agents.md)

### Tool Documentation
- Python: [pytest](https://docs.pytest.org/), [mypy](https://mypy.readthedocs.io/), [black](https://black.readthedocs.io/), [isort](https://pycqa.github.io/isort/) documentation
- JavaScript/TypeScript: [ESLint](https://eslint.org/docs/), [Prettier](https://prettier.io/docs/), [TSDoc](https://tsdoc.org/) documentation
- Go: [Official style guide](https://go.dev/doc/effective_go), [testing documentation](https://go.dev/doc/tutorial/add-a-test)
- Docker: [Best practices documentation](https://docs.docker.com/develop/dev-best-practices/)

---

## VERSION HISTORY

- **v2.0.0 (2026-05-03):** Major research update based on 2025-2026 evidence
  - Rebalanced priorities: verification/testing elevated to #1 (was #6)
  - Added 4 new attributes: single-file verification, CI quality gates, pattern references, design intent, progressive disclosure
  - Updated all citations — removed fabricated LLM-generated citations, added verified sources
  - Removed duplicated content from 5 attribute sections
  - Added YAML frontmatter for structured metadata parsing
  - Incorporated ETH Zurich study findings (context file effectiveness)
  - Incorporated Red Hat best practices guide (April 2026)
  - Incorporated AGENTS.md cross-tool standard (60,000+ repos)
  - Updated Implementation Priorities and Quickstart Guide
  - Total: 29 attributes, 55+ verified sources

- **v1.0.0 (2025-01-20):** Initial comprehensive research compilation
  - 25 attributes identified and documented
  - 50+ authoritative sources cited
  - Measurement framework established
  - Implementation guide created

---

**Document prepared for:** agentready tool development
**Primary use case:** Scanning repositories for AI agent optimization
**Target agents:** Claude Code, GitHub Copilot, Cursor, Codex, Gemini CLI, and cross-tool
**Methodology:** Evidence-based, cited research from authoritative sources
