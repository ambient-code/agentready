---
layout: page
title: Attributes Reference
---

Complete reference for all 25 agent-ready attributes assessed by AgentReady.

<div class="feature" style="background-color: #dbeafe; border-left: 4px solid #2563eb; padding: 1rem; margin: 1rem 0;">
  <h3 style="margin-top: 0;">🤖 Bootstrap Automation</h3>
  <p><strong>AgentReady Bootstrap automatically implements many of these attributes.</strong> Look for the <strong>✅ Bootstrap Addresses This</strong> marker to see which infrastructure Bootstrap generates for you.</p>
  <p>Instead of manually implementing each attribute, run <code>agentready bootstrap .</code> to generate complete GitHub setup in seconds.</p>
  <p><a href="user-guide#bootstrap-your-repository">Learn about Bootstrap →</a></p>
</div>

## Table of Contents

- [Overview](#overview)
- [Tier System](#tier-system)
- [Tier 1: Essential Attributes](#tier-1-essential-attributes)
- [Tier 2: Critical Attributes](#tier-2-critical-attributes)
- [Tier 3: Important Attributes](#tier-3-important-attributes)
- [Tier 4: Advanced Attributes](#tier-4-advanced-attributes)
- [Implementation Status](#implementation-status)

---

## Overview

AgentReady evaluates repositories against 25 attributes derived from research by Anthropic, Microsoft, Google, ETH Zurich, and Red Hat. Each attribute has specific pass/fail criteria, a tier-based weight, and concrete remediation steps.

Each entry below covers: what the assessor checks, the scoring breakdown, and how to fix a failing result.

---

## Tier System

Attributes are organized into four weighted tiers:

| Tier | Weight | Focus | Attribute Count |
|------|--------|-------|-----------------|
| **Tier 1: Essential** | 59% | Fundamentals enabling basic AI functionality | 9 attributes |
| **Tier 2: Critical** | 27% | Major quality improvements and safety nets | 9 attributes |
| **Tier 3: Important** | 12% | Significant improvements in specific areas | 5 attributes |
| **Tier 4: Advanced** | 2% | Refinement and optimization | 2 attributes |

Missing a Tier 1 attribute (up to 12% weight) has up to 12x the score impact of missing a Tier 4 attribute (1% weight).

---

## Tier 1: Essential Attributes

*Fundamentals that enable basic AI agent functionality — 55% of total score*

### 1. Agent Instruction Files

**ID**: `agent_instructions`
**Weight**: 7%
**Category**: Context Window Optimization
**Status**: ✅ Implemented

#### Definition

Markdown file at repository root (`CLAUDE.md` or `.claude/CLAUDE.md`) automatically ingested by Claude Code at conversation start.

#### Why It Matters

Claude Code reads `CLAUDE.md` at the start of every session. Without it, agents ask for context that is already in the repo — or guess wrong. A well-written file cuts repeated explanations and keeps the agent from violating conventions it wasn't told about.

#### Measurable Criteria

**Two-phase scoring:**

1. **Presence (up to 70 points)**: File exists at `CLAUDE.md`, `.claude/CLAUDE.md`, or `AGENTS.md` with at least 50 bytes (direct, symlink, or `@` file reference). `AGENTS.md` is a fully equivalent alternative.

2. **Length (up to 30 points)**: Context file line count determines length credit:

| Lines | Length Credit | Total Score |
|-------|-------------|-------------|
| <=150 | 30 (full) | 100 |
| 151-300 | 15 (partial) | 85 |
| >300 | 0 (none) | 70 |

For symlinks and `@` references, line count is measured on the resolved target file.

**Agent access documentation** (substantiating evidence): The assessor also checks for agent access sections documenting platform, CLI tool, and authentication requirements. This is recorded as evidence but does not affect the score.

#### Example: Good CLAUDE.md

```markdown
# Tech Stack
- Python 3.12+, pytest, black + isort
- FastAPI, PostgreSQL, Redis

# Standard Commands
- Setup: `make setup` (installs deps, runs migrations)
- Test: `pytest tests/` (requires Redis running)
- Format: `black . && isort .`
- Lint: `ruff check .`
- Build: `docker build -t myapp .`

# Repository Structure
- src/myapp/ - Main application code
- tests/ - Test files mirror src/
- docs/ - Sphinx documentation
- migrations/ - Database migrations

# Boundaries
- Never modify files in legacy/ (deprecated, scheduled for removal)
- Require approval before changing config.yaml
- All database changes must have reversible migrations

# Testing Strategy
- Unit tests: Fast, isolated, no external dependencies
- Integration tests: Require PostgreSQL and Redis
- Run integration tests: `make test-integration`
```

#### Remediation

**If missing**:

1. **Create CLAUDE.md** in repository root
2. **Add tech stack** section with language/framework versions
3. **Document standard commands** (essential: setup, test, build)
4. **Map repository structure** (key directories and their purpose)
5. **Define boundaries** (files/areas not to modify)

**Tools**: Any text editor

**Time**: 15-30 minutes for initial creation

**Citations**:

- Anthropic Engineering Blog: "Claude Code Best Practices" (2025)
- AgentReady Research: "Context Window Optimization"

---

### 2. README Structure

**ID**: `readme_structure`
**Weight**: 5%
**Category**: Documentation Standards
**Status**: ✅ Implemented

#### Definition

Standardized README.md with essential sections in predictable order, serving as primary entry point for understanding the project.

#### Why It Matters

The README is the first file an agent reads when dropped into an unfamiliar repo. Missing an installation section means the agent has to hunt through CI config or pyproject.toml to figure out how to run the code. Missing a development/contributing section means it may not know where tests live or how builds work.

#### Measurable Criteria

The assessor checks for three key sections using keyword matching:

1. **Installation** (keywords: install, setup, getting started)
2. **Usage** (keywords: usage, quickstart, example)
3. **Development** (keywords: development, contributing, build)

**Pass threshold**: Score of 75 or higher (at least 2 of 3 sections present).

#### Example: Well-Structured README

```markdown
# MyProject

Brief description of what this project does and why it exists.

## Installation

\```bash
pip install myproject
\```

## Quick Start

\```python
from myproject import Client

client = Client(api_key="your-key")
result = client.do_something()
print(result)
\```

## Features

- Feature 1: Does X efficiently
- Feature 2: Supports Y protocol
- Feature 3: Integrates with Z

## Requirements

- Python 3.12+
- PostgreSQL 14+
- Redis 7+ (optional, for caching)

## Testing

\```bash
# Run all tests
pytest

# Run with coverage
pytest --cov
\```

## Contributing

See [CONTRIBUTING.md](https://github.com/ambient-code/agentready/blob/main/CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](https://github.com/ambient-code/agentready/blob/main/LICENSE) for details.
```

#### Remediation

**If missing sections**:

1. **Audit current README**: Check which required sections are present
2. **Add missing sections**: Use template above as guide
3. **Reorder if needed**: Follow standard section order
4. **Add examples**: Include code snippets for quick start
5. **Keep concise**: Aim for <500 lines, link to detailed docs

**Tools**: Any text editor, Markdown linters

**Commands**:

```bash
# Validate Markdown syntax
markdownlint README.md

# Check for common issues
npx markdown-link-check README.md
```

**Citations**:

- GitHub Blog: "How to write a great README"
- Make a README project documentation

---

### 3. Type Annotations (Static Typing)

**ID**: `type_annotations`
**Weight**: 8%
**Category**: Code Quality
**Status**: ✅ Implemented

#### Definition

Explicit type declarations for variables, function parameters, and return values in statically-typed or optionally-typed languages.

#### Why It Matters

Type annotations give agents reliable information about what a function expects and returns, without reading the implementation. An untyped function that accepts "a user" and returns "something" forces the agent to infer types from usage — which it will sometimes get wrong. Annotated code is also easier to refactor safely, since type errors surface before execution.

#### Measurable Criteria

**Python**:

- All public functions have parameter and return type hints
- Generic types from `typing` module used appropriately
- Coverage: >80% of functions typed
- Tools: mypy, pyright

**TypeScript**:

- `strict` mode enabled in tsconfig.json
- No `any` types (use `unknown` if needed)
- Interfaces for complex objects

**Go**:

- Inherently typed (always passes)

**JavaScript**:

- JSDoc type annotations OR migrate to TypeScript

#### Example: Good Type Annotations (Python)

```python
from typing import List, Optional, Dict

def find_users(
    role: str,
    active: bool = True,
    limit: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Find users matching criteria.

    Args:
        role: User role to filter by
        active: Include only active users
        limit: Maximum number of results

    Returns:
        List of user dictionaries
    """
    # Implementation
    pass

# Complex types
from dataclasses import dataclass

@dataclass
class User:
    id: str
    email: str
    role: str
    active: bool = True

def create_user(email: str, role: str) -> User:
    """Create new user with validation."""
    return User(id=generate_id(), email=email, role=role)
```

#### Example: Bad (No Type Hints)

```python
def find_users(role, active=True, limit=None):
    # What types? AI must guess
    pass

def create_user(email, role):
    # Return type unclear
    pass
```

#### Remediation

**Python**:

1. **Install type checker**:

   ```bash
   pip install mypy
   ```

2. **Add type hints** to public functions:

   ```bash
   # Use tool to auto-generate hints
   pip install monkeytype
   monkeytype run pytest tests/
   monkeytype apply module_name
   ```

3. **Run type checker**:

   ```bash
   mypy src/
   ```

4. **Fix errors iteratively**

**TypeScript**:

1. **Enable strict mode** in `tsconfig.json`:

   ```json
   {
     "compilerOptions": {
       "strict": true,
       "noImplicitAny": true
     }
   }
   ```

2. **Fix type errors**:

   ```bash
   tsc --noEmit
   ```

**Tools**: mypy, pyright, pytype (Python); tsc (TypeScript)

**Citations**:

- Medium: "LLM Coding Concepts: Static Typing"
- ArXiv: "Automated Type Annotation in Python Using LLMs"
- Dropbox: "Our journey to type checking 4 million lines of Python"

---

### 4. Standard Project Layout

**ID**: `standard_layout`
**Weight**: 5%
**Category**: Repository Structure
**Status**: ✅ Implemented

#### Definition

Using community-recognized directory structures for each language/framework (e.g., Python's `src/` layout, Go's `cmd/` and `internal/`, Maven structure for Java).

#### Why It Matters

Models trained on open-source code have seen the standard layouts thousands of times. When a repo uses the Python `src/` layout or Go's `cmd/internal/pkg` structure, the agent knows where to look for things and where to put new ones. Non-standard layouts force it to explore, and it may still place files in the wrong location.

#### Measurable Criteria

**Python (src/ layout)**:

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

**Go**:

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

**JavaScript/TypeScript**:

```
project/
├── src/
├── test/
├── dist/
├── package.json
├── package-lock.json
└── tsconfig.json (if TypeScript)
```

**Java (Maven)**:

```
project/
├── src/
│   ├── main/java/
│   └── test/java/
├── pom.xml
└── target/
```

#### Remediation

**If non-standard layout**:

1. **Identify target layout** for your language
2. **Create migration plan** (avoid breaking changes)
3. **Move files incrementally**:

   ```bash
   # Python: Migrate to src/ layout
   mkdir -p src/mypackage
   git mv mypackage/* src/mypackage/
   ```

4. **Update imports/references**
5. **Update build configuration** (setup.py, pyproject.toml, etc.)
6. **Test thoroughly**

**Tools**: IDE refactoring tools, git mv

**Citations**:

- Real Python: "Python Application Layouts"
- GitHub: golang-standards/project-layout
- Maven standard directory layout

---

### 5. Dependency Lock Files

**ID**: `lock_files`
**Weight**: 5%
**Category**: Dependency Management
**Status**: ✅ Implemented

#### Definition

Pinning exact dependency versions including transitive dependencies (e.g., `package-lock.json`, `poetry.lock`, `go.sum`).

#### Why It Matters

Without a lock file, two installs of the same repo can get different dependency versions. An agent suggesting a fix against one version may generate broken code for someone on another. Lock files make the environment deterministic, which makes agent-generated dependency changes testable.

#### Measurable Criteria

**Passes if** a recognized lock file is present (score >= 75):

- **Auto-managed lock files** (always fully pinned): `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `uv.lock`, `Cargo.lock`, `Gemfile.lock`, `go.sum`
- **Manual lock files** (`requirements.txt`): validated for version pinning quality; counts `==` (pinned) vs `>=`/unpinned usage and scores proportionally

**Freshness check**: Lock files older than 6 months incur a 15-point deduction.

**For `requirements.txt`**: The assessor validates version pinning quality by counting lines with `==` (exact pins) versus `>=`, `~=`, or no specifier (unpinned). Score reflects the ratio of pinned to total dependencies.

**Pass threshold**: 75 points or higher.

#### Remediation

**Python (poetry)**:

```bash
# Install poetry
pip install poetry

# Create lock file
poetry lock

# Install from lock file
poetry install
```

**Python (pip)**:

```bash
# Create requirements with exact versions
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

**npm**:

```bash
# Generate lock file
npm install

# Commit package-lock.json
git add package-lock.json
```

**Go**:

```bash
# Lock file auto-generated
go mod download
go mod tidy
```

**Citations**:

- npm Blog: "Why Keep package-lock.json?"
- Python Packaging User Guide
- Go Modules documentation

---

### 6. Test Execution & Coverage

**ID**: `test_execution`
**Weight**: 10%
**Category**: Testing & CI/CD
**Status**: ✅ Implemented

**✅ Bootstrap Addresses This**: `agentready bootstrap` generates a language-specific `tests.yml` GitHub Actions workflow with test runner, coverage, and reporting configured.

#### Definition

Test infrastructure configured and present: test files, a test runner, coverage tooling, and enforcement thresholds.

#### Why It Matters

Agents modifying code need a way to verify their changes didn't break anything. Without a configured test suite, the only signal is "it still runs" — which catches very little. The assessor checks whether the infrastructure is in place, not whether tests are well-written.

#### Measurable Criteria

The assessor scores a repository on a 100-point scale (capped) based on test infrastructure:

- **Test files exist** (40 pts): `tests/` or `test/` directory with test files present
- **Test runner configured** (20 pts): pytest, unittest, or similar configured in `pyproject.toml`, `setup.cfg`, `tox.ini`, or `Makefile`
- **Coverage config present** (20 pts): coverage settings in config files (e.g., `[tool.coverage]`)
- **Coverage enforcement configured** (20 pts): coverage thresholds or fail-under settings present
- **Test command documented** (10 pts bonus): test command mentioned in CLAUDE.md, AGENTS.md, or README.md. Agents need to *find* the command, not just have one available

**Test organization** (substantiating evidence): The assessor also checks for unit/integration test separation (separate directories, pytest markers, Makefile targets, filtered test scripts). This is recorded as evidence but does not affect the score.

**Pass threshold**: Score of 60 or higher.

#### Remediation

```bash
# Python
pip install pytest pytest-cov
pytest --cov=src --cov-report=html

# JavaScript
npm install --save-dev jest
jest --coverage

# Go
go test -cover ./...
go test -coverprofile=coverage.out
go tool cover -html=coverage.out
```

**Citations**:

- Salesforce Engineering: "How Cursor AI Cut Legacy Code Coverage Time by 85%"

---

### 7. CI Quality Gates

**ID**: `ci_quality_gates`
**Weight**: 5%
**Category**: Testing & CI/CD
**Status**: Implemented

**✅ Bootstrap Addresses This**: `agentready bootstrap` generates `.github/workflows/tests.yml` and a `security.yml` workflow, covering test and security gate enforcement on every PR.

#### Definition

Continuous integration enforces lint, type-check, and test steps on every pull request, blocking merges that fail any gate.

#### Why It Matters

CI is the one check that can't be skipped. Pre-commit hooks can be bypassed; CI cannot. When lint, type-check, and tests all run on every PR, an agent's changes get validated by the same standard as a human's.

#### Measurable Criteria

The assessor scores on a 100-point scale:

- **CI config exists** (50 pts): A workflow file in `.github/workflows/`, `.gitlab-ci.yml`, `.tekton` or similar
- **Quality gates present** (30 pts): lint, type-check, and test steps detected in CI config. For compiled languages (Go, Rust), the build step (`go build`, `make build`, `cargo build`) counts as the type-check gate since the compiler is the type checker. `golangci-lint` also satisfies the type-check gate as it bundles type-checking linters.
- **Config quality** (15 pts): PR trigger configured, fail-fast enabled
- **Best practices** (5 pts): matrix testing, caching, or other optimizations

**Pass threshold**: 60 points or higher.

#### Remediation

```bash
# Create a basic GitHub Actions CI workflow
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy src/
      - run: pytest
EOF
```

---

### 8. Single-File Verification

**ID**: `single_file_verification`
**Weight**: 5%
**Category**: Context Window Optimization
**Status**: Implemented

#### Definition

Documentation of commands that lint and type-check a single file quickly, without running the full test suite. These commands are documented in `CLAUDE.md`, `AGENTS.md`, `.claude/CLAUDE.md`, or `README.md`.

#### Why It Matters

Running the full test suite after every edit is slow. A documented single-file check (`ruff check path/to/file.py`, `mypy path/to/file.py`) gives an agent signal in seconds instead of minutes, which matters when it's iterating on a specific function.

#### Measurable Criteria

**Passes if**: At least one of `CLAUDE.md`, `AGENTS.md`, `.claude/CLAUDE.md`, or `README.md` documents single-file lint or type-check commands.

The assessor looks for patterns like:
- `ruff check <file>`
- `mypy <file>`
- `eslint <file>`
- `tsc --noEmit <file>`

#### Remediation

Add a section to your `CLAUDE.md`:

```markdown
# Single-File Verification

To quickly check a single file without running the full test suite:

\```bash
# Lint a single file
ruff check src/mypackage/module.py

# Type-check a single file
mypy src/mypackage/module.py
\```
```

---

### 9. Dependency Security

**ID**: `dependency_security`
**Weight**: 5%
**Category**: Security
**Status**: Implemented

**✅ Bootstrap Addresses This**: `agentready bootstrap` generates `.github/dependabot.yml` for automated dependency updates and a `security.yml` workflow for vulnerability scanning.

#### Definition

Vulnerability scanning tools configured for dependencies and code, including automated dependency updates and static analysis security testing (SAST).

#### Why It Matters

Dependency vulnerabilities are reliably caught by automated scanners and reliably missed by manual review. Dependabot and pip-audit check against known CVE databases on every update — something no agent or developer is going to do by hand.

#### Measurable Criteria

The assessor checks for recognized security tools:

- **Dependency update tools** (Dependabot or Renovate) — 30 pts + 5 pts bonus for meaningful config
- **CodeQL / GitHub Security Scanning** — 25 pts
- **Python scanners** (pip-audit, safety) — 10 pts; Bandit SAST — 10 pts
- **JavaScript scanners** (npm/yarn audit in scripts) — 10 pts; Snyk — 10 pts
- **Secret detection in pre-commit** (detect-secrets, gitleaks, truffleHog) — 20 pts
- **Semgrep** (multi-language SAST) — 15 pts
- **SECURITY.md** present — 5 pts bonus

**Pass threshold**: 60 points.

**Tools checked**: pip-audit, safety, dependabot, snyk, trivy, grype, osvscanner, bandit (Python); npm audit, yarn audit (JavaScript/TypeScript); CodeQL, Semgrep, gitleaks, detect-secrets (multi-language).

#### Remediation

```bash
# Enable Dependabot (create .github/dependabot.yml)
cat > .github/dependabot.yml << 'EOF'
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
EOF

# Add secret detection to pre-commit
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

**Citations**:

- OWASP: "Dependency-Check Project"
- GitHub: "Dependabot Documentation"

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/RESEARCH_REPORT.md).*

---

## Tier 2: Critical Attributes

*Major quality improvements and safety nets — 27% of total score*

### 10. Deterministic Enforcement (Hooks & Lint Rules)

**ID**: `deterministic_enforcement`
**Weight**: 3%
**Category**: Testing & CI/CD
**Status**: ✅ Implemented

**✅ Bootstrap Addresses This**: `agentready bootstrap` automatically creates `.pre-commit-config.yaml` with language-specific hooks and corresponding GitHub Actions workflow.

#### Definition

Automated code quality checks before commits (pre-commit hooks) and in CI/CD pipeline, ensuring consistent standards.

#### Why It Matters

Pre-commit hooks give immediate local feedback. They can be bypassed with `--no-verify`, which is why CI matters too — but for agent-generated commits that go through a normal PR flow, hooks are the first line of defense. Catching a lint error before a commit beats catching it in CI review.

#### Measurable Criteria

The assessor scores on a 100-point scale:

- **`.pre-commit-config.yaml` present** (60 pts): pre-commit hooks configured
- **`.husky` directory with hook scripts** (60 pts): Husky git hooks configured (e.g., pre-commit, commit-msg)
- **`.husky` directory without hook scripts** (10 pts): Husky directory exists but no hooks defined
- **`.claude/settings.json` with hooks** (30 pts): Claude Code hook configuration present

**Pass threshold**: 60 points or higher. Either `.pre-commit-config.yaml` or `.husky` with hook scripts is sufficient to pass.

#### Remediation

**Automated** (recommended):

```bash
agentready bootstrap .  # Generates .pre-commit-config.yaml + GitHub Actions
pre-commit install      # Install git hooks locally
```

**Manual**:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
EOF

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Citations**:

- Memfault: "Automatically format and lint code with pre-commit"
- GitHub: pre-commit/pre-commit

---

### 11. Conventional Commit Messages

**ID**: `conventional_commits`
**Weight**: 3%
**Category**: Git & Version Control
**Status**: ✅ Implemented

#### Definition

Structured commit messages following format: `<type>(<scope>): <description>`.

#### Why It Matters

Structured commit messages make history parseable. Tools like `semantic-release` use them for automated versioning and changelog generation. For agents, a consistent format also makes git history a reliable source of truth about what changed and why.

#### Measurable Criteria

**Passes if** conventional commit enforcement tooling is configured:

- commitlint config file (`.commitlintrc*`, `commitlint.config.*`)
- commitlint key in `package.json`
- `.husky` directory with commit-msg hook
- conventional commits hook in `.pre-commit-config.yaml`

The assessor checks for tooling presence, not actual commit history. Pass is binary: configured or not.

**Format enforced**: `type(scope): description`

**Types**: feat, fix, docs, style, refactor, perf, test, chore, build, ci

**Examples**:

- ✅ `feat(auth): add OAuth2 login support`
- ✅ `fix(api): handle null values in user response`
- ✅ `docs(readme): update installation instructions`
- ❌ `update stuff`
- ❌ `fixed bug`

#### Remediation

```bash
# Install commitlint
npm install -g @commitlint/cli @commitlint/config-conventional

# Create commitlint.config.js
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Add to pre-commit hooks
cat >> .pre-commit-config.yaml << 'EOF'
  - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
    rev: v9.5.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
EOF
```

**Citations**:

- Conventional Commits specification v1.0.0
- Medium: "GIT — Semantic versioning and conventional commits"

---

### 12. .gitignore Completeness

**ID**: `gitignore_completeness`
**Weight**: 3%
**Category**: Git & Version Control
**Status**: ✅ Implemented

#### Definition

Comprehensive `.gitignore` preventing build artifacts, dependencies, IDE files, OS files, secrets, and logs from version control.

#### Why It Matters

A missing `.gitignore` entry for `__pycache__/` or `node_modules/` means those directories show up in `git status` and context scans. The more serious risk is accidentally committing `.env` files or credentials, which a complete `.gitignore` prevents by default.

#### Measurable Criteria

The assessor checks for specific language-specific patterns from a hardcoded list based on the repository's detected languages:

- **Python**: `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `.pytest_cache/`, `venv/`, `.venv/`, `.env`
- **JavaScript**: `node_modules/`, `dist/`, `build/`, `.npm/`, `*.log`
- **TypeScript**: `node_modules/`, `dist/`, `*.tsbuildinfo`, `.npm/`
- **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
- **Ruby**: `*.gem`, `.bundle/`, `vendor/bundle/`, `.ruby-version`
- **Rust**: `target/`, `Cargo.lock`, `**/*.rs.bk`
- **General** (always checked): `.DS_Store`, `.vscode/`, `.idea/`, `*.swp`, `*.swo`

**Pass threshold**: 70% or more of the expected patterns for detected languages must be present.

**Reference**: [github/gitignore](https://github.com/github/gitignore)

#### Remediation

```bash
# Download language-specific template
curl https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore > .gitignore

# Or generate with gitignore.io
curl -sL https://www.toptal.com/developers/gitignore/api/python,node,visualstudiocode > .gitignore

# Add custom patterns
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
```

**Citations**:

- GitHub: github/gitignore
- Medium: "Mastering .gitignore"

---

### 13. One-Command Build/Setup

**ID**: `one_command_setup`
**Weight**: 3%
**Category**: Build & Development
**Status**: ✅ Implemented

#### Definition

Single command to set up development environment from fresh clone (`make setup`, `npm install`, `./bootstrap.sh`). Recognized Makefile variants: `Makefile`, `GNUmakefile`, `makefile`.

#### Why It Matters

Without a setup command, getting a fresh clone to a working state requires reading through README, installing dependencies manually, copying config files, and hoping nothing was missed. One documented command eliminates that ambiguity for both humans and agents.

#### Measurable Criteria

**Passes if**:

- Single command documented in README
- Command handles:
  - Dependency installation
  - Virtual environment creation
  - Database setup/migrations
  - Configuration file creation
  - Pre-commit hooks installation
- Success in <5 minutes on fresh clone
- Idempotent (safe to run multiple times)

#### Example: Makefile

```makefile
.PHONY: setup
setup:
 python -m venv venv
 . venv/bin/activate && pip install -r requirements.txt
 pre-commit install
 cp .env.example .env
 python manage.py migrate
 @echo "✓ Setup complete! Run 'make test' to verify."
```

#### Remediation

1. **Create setup script** (Makefile, package.json script, or shell script)
2. **Document in README** quick start section
3. **Test on fresh clone**
4. **Automate common setup steps**

**Citations**:

- freeCodeCamp: "Using Make as a Build Tool"

---

### Additional Tier 2 Attributes

**Inline Documentation** (`inline_documentation`, 3%) — Comments and docstrings for functions, classes, modules
**File Size Limits** (`file_size_limits`, 3%) — Files under threshold to keep context manageable
**Separation of Concerns** (`separation_of_concerns`, 3%) — Clean module boundaries and single-responsibility
**Pattern References** (`pattern_references`, 3%) — Documented patterns for common changes. Skills scoring is tiered: 1-2 SKILL.md files earn partial credit (30 pts), 3+ earn full credit (60 pts). Context files >150 lines without skills trigger a warning
**Design Intent Documentation** (`design_intent`, 3%) — Preconditions, invariants, and rationale in design docs (moved from T3)

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/RESEARCH_REPORT.md).*

---

## Tier 3: Important Attributes

*Significant improvements in specific areas — 12% of total score*

### 14. Cyclomatic Complexity Limits

**ID**: `cyclomatic_complexity`
**Weight**: 2%
**Category**: Code Quality
**Status**: ✅ Implemented

#### Definition

Measurement of linearly independent paths through code (decision point density). Target: <10 per function.

#### Why It Matters

A function with 20 branches is hard to reason about whether you're human or an agent. High-complexity functions are also harder to test exhaustively, which means bugs hide in untested paths. Keeping complexity under 10 makes functions easier to understand, test, and modify safely.

#### Measurable Criteria

**Python** (via radon): runs `radon cc` and measures average cyclomatic complexity across all functions. Pass threshold: average < 10.

**Other languages**: returns `not_applicable` (lizard integration not yet implemented).

**Pass threshold**: proportional score >= 75 (average complexity well below 10).

#### Remediation

```bash
# Install radon
pip install radon

# Check complexity
radon cc src/ -s -a

# Identify high-complexity functions (>10)
radon cc src/ -s -nb

# Refactor: break complex functions into smaller ones
# Use early returns to reduce nesting
# Extract conditional logic into separate functions
```

**Citations**:

- Microsoft Learn: "Code metrics - Cyclomatic complexity"

---

### Additional Tier 3 Attributes

**Structured Logging** (`structured_logging`, 2%) — JSON logs with consistent fields
**OpenAPI/Swagger Specs** (`openapi_specs`, 3%) — Machine-readable API docs
**Progressive Disclosure** (`progressive_disclosure`, 2%) — Path-scoped rules, skills for focused context (moved from T4)
### Architecture Decision Records

**ID**: `architecture_decisions`
**Tier**: Tier 3
**Weight**: 3%
**Category**: Documentation Standards
**Status**: ✅ Implemented

#### Definition

Lightweight documents (ADRs) that record why significant architectural choices were made, not just what was chosen.

#### Why It Matters

Agents can read current code but cannot infer the constraints, failed alternatives, or tradeoffs that shaped it. Without ADRs, agents confidently suggest changes that were already tried and rejected.

#### Measurable Criteria

Scoring is based on directory presence, ADR count, and template compliance:

| State | Score | Status |
|-------|-------|--------|
| No ADR directory, no agent context file reference | 0 | fail |
| Architecture section AND external link in CLAUDE.md/AGENTS.md | 60 | fail |
| ADR directory found, empty | 40 | fail |
| ADR directory + 1-4 ADRs | 40-72 | fail/pass |
| ADR directory + 5+ ADRs + template compliance | up to 100 | pass |

**Recognized directory locations** (case-insensitive):

- `docs/adr/`, `docs/adrs/`, `docs/ADRs/`
- `docs/architecture/`, `docs/design/`, `docs/specs/`
- `adr/`, `specs/`, `.adr/`

**Partial credit (60/100)** is awarded when no inline ADR directory exists but `CLAUDE.md` or `AGENTS.md` contains both an architecture/decisions section heading and a link to an external ADR/RFC repository. Both conditions are required — a heading alone is too common a false positive, and a link alone provides insufficient signal. Inline ADRs are more agent-ready because agents cannot follow external links.

**Template compliance** checks for the four Michael Nygard sections: Status, Context, Decision, Consequences.

#### Remediation

```bash
mkdir -p docs/adr

cat > docs/adr/0001-use-python.md << 'EOF'
# 1. Use Python as primary language

## Status
Accepted

## Context
Team has strong Python expertise; data science integrations are Python-first.

## Decision
Python 3.12+ is the primary implementation language.

## Consequences
Strong ML/data library access. Type annotations required to compensate for
dynamic typing risks.
EOF
```

**Tools**: [adr-tools](https://github.com/npryce/adr-tools), [log4brains](https://github.com/thomvaill/log4brains)

---

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/RESEARCH_REPORT.md).*

---

## Tier 4: Advanced Attributes

*Refinement and optimization — 2% of total score*

### Tier 4 Attributes

**Issue & PR Templates** (`issue_pr_templates`, 1%) — PR template (50 pts) + issue templates in `.github/ISSUE_TEMPLATE/` (25 pts for 1, 50 pts for 2+); pass threshold 75. ✅ Bootstrap generates these automatically.
**Container/Virtualization Setup** (`container_setup`, 1%) — Dockerfile or Containerfile (40 pts), multi-stage build bonus (10 pts), docker-compose (30 pts), .dockerignore/.containerignore (20 pts); pass threshold 40. Returns not_applicable if no Dockerfile/Containerfile found.

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/RESEARCH_REPORT.md).*

---

## Implementation Status

All 24 assessors are fully implemented across all four tiers.

**Current State**:
- ✅ **Tier 1 (Essential)**: Fully implemented (9 attributes)
- ✅ **Tier 2 (Critical)**: Fully implemented (9 attributes)
- ✅ **Tier 3 (Important)**: Fully implemented (5 attributes)
- ✅ **Tier 4 (Advanced)**: Fully implemented (2 attributes)

See the [GitHub repository](https://github.com/ambient-code/agentready) for current implementation details.

---

## Next Steps

- **[User Guide](user-guide.md)** — Learn how to run assessments
- **[Developer Guide](developer-guide.md)** — Implement new assessors
- **[API Reference](api-reference.md)** — Integrate AgentReady
- **[Examples](examples.md)** — View real assessment reports

---

**Complete attribute research**: See [RESEARCH_REPORT.md](https://github.com/ambient-code/agentready/blob/main/RESEARCH_REPORT.md) for full citations, examples, and detailed criteria.
