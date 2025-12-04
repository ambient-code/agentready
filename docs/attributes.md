---
layout: page
title: Attributes Reference
---

# Attributes Reference

Complete reference for all 25 agent-ready attributes assessed by AgentReady.

<div class="feature" style="background-color: #dbeafe; border-left: 4px solid #2563eb; padding: 1rem; margin: 1rem 0;">
  <h3 style="margin-top: 0;">🤖 Bootstrap Automation</h3>
  <p><strong>AgentReady Bootstrap automatically implements many of these attributes.</strong> Look for the <strong>✅ Bootstrap Addresses This</strong> marker to see which infrastructure Bootstrap generates for you.</p>
  <p>Instead of manually implementing each attribute, run <code>agentready bootstrap .</code> to generate complete GitHub setup in seconds.</p>
  <p><a href="user-guide.html#bootstrap-your-repository">Learn about Bootstrap →</a></p>
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

AgentReady evaluates repositories against **25 evidence-based attributes** that improve AI agent effectiveness. Each attribute is:

- **Research-backed**: Derived from 50+ authoritative sources (Anthropic, Microsoft, Google, academic research)
- **Measurable**: Specific criteria with clear pass/fail thresholds
- **Actionable**: Concrete tools, commands, and examples for remediation
- **Weighted**: Importance reflected in tier-based scoring (50/30/15/5 distribution)

**Every attribute includes**:

- Definition and importance for AI agents
- Impact on agent behavior
- Measurable criteria
- Authoritative citations
- Good vs. bad examples
- Remediation guidance

---

## Tier System

Attributes are organized into four weighted tiers:

| Tier | Weight | Focus | Attribute Count |
|------|--------|-------|-----------------|
| **Tier 1: Essential** | 50% | Fundamentals enabling basic AI functionality | 5 attributes |
| **Tier 2: Critical** | 30% | Major quality improvements and safety nets | 6 attributes |
| **Tier 3: Important** | 15% | Significant improvements in specific areas | 9 attributes |
| **Tier 4: Advanced** | 5% | Refinement and optimization | 5 attributes |

**Impact**: Missing a Tier 1 attribute (10% weight) has **10x the impact** of missing a Tier 4 attribute (1% weight).

---

## Tier 1: Essential Attributes

*Fundamentals that enable basic AI agent functionality — 50% of total score*

### 1. CLAUDE.md Configuration File

**ID**: `claude_md_file`
**Weight**: 10%
**Category**: Context Window Optimization
**Status**: ✅ Implemented

#### Definition

Markdown file at repository root (`CLAUDE.md` or `.claude/CLAUDE.md`) automatically ingested by Claude Code at conversation start.

#### Why It Matters

CLAUDE.md files provide **immediate project context** without repeated explanations. Research shows they reduce prompt engineering time by ~40% and frame entire sessions with project-specific guidance.

#### Impact on AI Agents

- Immediate understanding of tech stack, repository structure, standard commands
- Consistent adherence to project conventions
- Reduced need for repeated context-setting
- Proper framing for all AI suggestions

#### Measurable Criteria

**Passes if**:

- File exists at `CLAUDE.md` or `.claude/CLAUDE.md`
- File size: <1000 lines (concise, focused)
- Contains essential sections:
  - Tech stack with versions
  - Repository map/structure
  - Standard commands (build, test, lint, format)
  - Testing strategy
  - Style/lint rules
  - Branch/PR workflow

**Bonus points** (not required for pass):

- "Do not touch" zones documented
- Security/compliance notes included
- Common gotchas and edge cases

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
**Weight**: 10%
**Category**: Documentation Standards
**Status**: ✅ Implemented

#### Definition

Standardized README.md with essential sections in predictable order, serving as primary entry point for understanding the project.

#### Why It Matters

Repositories with well-structured READMEs receive more engagement (GitHub data). README serves as AI agent's entry point for understanding project purpose, setup, and usage.

#### Impact on AI Agents

- Faster project comprehension
- Accurate answers to onboarding questions
- Better architectural understanding without exploring entire codebase
- Consistent expectations across projects

#### Measurable Criteria

**Passes if README.md contains (in order)**:

1. Project title and description
2. Installation/setup instructions
3. Quick start/usage examples
4. Core features
5. Dependencies and requirements
6. Testing instructions
7. Contributing guidelines
8. License

**Bonus sections**:

- Table of contents (for longer READMEs)
- Badges (build status, coverage, version)
- Screenshots or demos
- FAQ section
- Changelog link

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
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
**Weight**: 10%
**Category**: Code Quality
**Status**: ✅ Implemented

#### Definition

Explicit type declarations for variables, function parameters, and return values in statically-typed or optionally-typed languages.

#### Why It Matters

Type hints **significantly improve LLM code understanding**. Research shows higher-quality codebases have type annotations, directing LLMs toward higher-quality latent space regions—similar to how LaTeX-formatted math gets better results.

#### Impact on AI Agents

- Better input validation suggestions
- Type error detection before execution
- Structured output generation
- Improved autocomplete accuracy
- Enhanced refactoring safety
- More confident code modifications

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
**Weight**: 10%
**Category**: Repository Structure
**Status**: ✅ Implemented

#### Definition

Using community-recognized directory structures for each language/framework (e.g., Python's `src/` layout, Go's `cmd/` and `internal/`, Maven structure for Java).

#### Why It Matters

Standard layouts reduce cognitive overhead. AI models trained on open-source code recognize patterns and navigate predictably.

#### Impact on AI Agents

- Faster file location
- Accurate placement suggestions for new files
- Automatic adherence to established conventions
- Reduced confusion about file organization

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
**Weight**: 10%
**Category**: Dependency Management
**Status**: ✅ Implemented

#### Definition

Pinning exact dependency versions including transitive dependencies (e.g., `package-lock.json`, `poetry.lock`, `go.sum`).

#### Why It Matters

Lock files ensure **reproducible builds** across environments. Without them, "works on my machine" problems plague AI-generated code. Different dependency versions can break builds, fail tests, or introduce bugs.

#### Impact on AI Agents

- Confident dependency-related suggestions
- Accurate compatibility issue diagnosis
- Reproducible environment recommendations
- Version-specific API usage

#### Measurable Criteria

**Passes if lock file exists and committed**:

- **npm**: `package-lock.json` or `yarn.lock`
- **Python**: `poetry.lock`, `Pipfile.lock`, or `requirements.txt` from `pip freeze` (or `uv.lock`)
- **Go**: `go.sum` (automatically managed)
- **Ruby**: `Gemfile.lock`
- **Rust**: `Cargo.lock`

**Additional requirements**:

- Lock file updated with every dependency change
- CI/CD uses lock file for installation
- Lock file not in `.gitignore`

**Note**: Library projects may intentionally exclude lock files. AgentReady recognizes this pattern and adjusts scoring.

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

## Tier 2: Critical Attributes

*Major quality improvements and safety nets — 30% of total score*

### 6. Test Coverage

**ID**: `test_coverage`
**Weight**: 5%
**Category**: Testing & CI/CD
**Status**: ✅ Implemented

#### Definition

Percentage of code executed by automated tests, measured by line coverage, branch coverage, or function coverage.

#### Why It Matters

High test coverage enables **confident AI modifications**. Research shows AI tools can cut test coverage time by 85% while maintaining quality—but only when good tests exist as foundation.

#### Measurable Criteria

**Minimum thresholds**:

- 70% line coverage (Bronze)
- 80% line coverage (Silver/Gold)
- 90% line coverage (Platinum)

**Critical paths**: 100% coverage for core business logic

**Measured via**:

- pytest-cov (Python)
- Jest/Istanbul (JavaScript/TypeScript)
- go test -cover (Go)
- JaCoCo (Java)

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

### 7. Pre-commit Hooks & CI/CD Linting

**ID**: `precommit_hooks`
**Weight**: 5%
**Category**: Testing & CI/CD
**Status**: ✅ Implemented

**✅ Bootstrap Addresses This**: `agentready bootstrap` automatically creates `.pre-commit-config.yaml` with language-specific hooks and corresponding GitHub Actions workflow.

#### Definition

Automated code quality checks before commits (pre-commit hooks) and in CI/CD pipeline, ensuring consistent standards.

#### Why It Matters

Pre-commit hooks provide immediate feedback. Running same checks in CI/CD ensures enforcement (hooks can be bypassed). Prevents low-quality code from entering repository.

#### Measurable Criteria

**Passes if**:

- `.pre-commit-config.yaml` exists
- Hooks include formatters (black, prettier) and linters (flake8, eslint)
- Same checks run in CI/CD (GitHub Actions, GitLab CI, etc.)
- CI fails on linting errors

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

### 8. Conventional Commit Messages

**ID**: `conventional_commits`
**Weight**: 5%
**Category**: Git & Version Control
**Status**: 🔶 Partially Implemented

#### Definition

Structured commit messages following format: `<type>(<scope>): <description>`.

#### Why It Matters

Conventional commits enable **automated semantic versioning**, changelog generation, and commit intent understanding. AI can parse history to understand feature evolution.

#### Measurable Criteria

**Format**: `type(scope): description`

**Types**: feat, fix, docs, style, refactor, perf, test, chore, build, ci

**Enforcement**: commitlint in pre-commit hooks or CI

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

### 9. .gitignore Completeness

**ID**: `gitignore_completeness`
**Weight**: 5%
**Category**: Git & Version Control
**Status**: ✅ Implemented

#### Definition

Comprehensive `.gitignore` preventing build artifacts, dependencies, IDE files, OS files, secrets, and logs from version control.

#### Why It Matters

Incomplete `.gitignore` pollutes repository with irrelevant files, consuming context window space and creating security risks (accidentally committing `.env`, credentials).

#### Measurable Criteria

**Must exclude**:

- Build artifacts (`dist/`, `build/`, `*.pyc`, `*.class`)
- Dependencies (`node_modules/`, `venv/`, `vendor/`)
- IDE files (`.vscode/`, `.idea/`, `*.swp`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Environment variables (`.env`, `.env.local`)
- Credentials (`*.pem`, `*.key`, `credentials.json`)
- Logs (`*.log`, `logs/`)

**Best practice**: Use templates from [github/gitignore](https://github.com/github/gitignore)

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

### 10. One-Command Build/Setup

**ID**: `one_command_setup`
**Weight**: 5%
**Category**: Build & Development
**Status**: 🔶 Partially Implemented

#### Definition

Single command to set up development environment from fresh clone (`make setup`, `npm install`, `./bootstrap.sh`).

#### Why It Matters

One-command setup enables AI to quickly reproduce environments and test changes. Reduces "works on my machine" problems.

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

### 11. Development Environment Documentation

**ID**: `dev_environment_docs`
**Weight**: 5%
**Category**: Build & Development
**Status**: 🔶 Partially Implemented

#### Definition

Clear documentation of prerequisites, environment variables, and configuration requirements.

#### Measurable Criteria

**Must document**:

- Language/runtime version (Python 3.12+, Node.js 18+)
- System dependencies (PostgreSQL, Redis, etc.)
- Environment variables (`.env.example` with all variables)
- Optional: IDE setup, debugging config

#### Example: .env.example

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# API Keys (get from https://example.com/api)
API_KEY=your-key-here
API_SECRET=your-secret-here

# Feature Flags
ENABLE_FEATURE_X=false
```

**Citations**:

- Medium: "Creating Reproducible Development Environments"

---

## Tier 3: Important Attributes

*Significant improvements in specific areas — 15% of total score*

### 12. Cyclomatic Complexity Limits

**ID**: `cyclomatic_complexity`
**Weight**: 3%
**Category**: Code Quality
**Status**: ✅ Implemented

#### Definition

Measurement of linearly independent paths through code (decision point density). Target: <10 per function.

#### Why It Matters

High complexity confuses both humans and AI. Functions with complexity >25 are error-prone and hard to test.

#### Measurable Criteria

- Target: <10 per function
- Warning: 15
- Error: 25

**Tools**:

- radon (Python)
- complexity-report (JavaScript)
- gocyclo (Go)
- clang-tidy (C++)

#### Remediation

```bash
# Python
pip install radon
radon cc src/ -a -nb

# JavaScript
npm install -g complexity-report
cr src/**/*.js

# Refactor complex functions
# Break into smaller helper functions
# Extract conditional logic
# Use polymorphism instead of switch statements
```

**Citations**:

- Microsoft Learn: "Code metrics - Cyclomatic complexity"

---

### 13-20. Additional Tier 3 Attributes

**13. Function/Method Length Limits** (`function_length`) — Target: <50 lines per function
**14. Code Smell Elimination** (`code_smells`) — DRY violations, long methods, magic numbers
**15. Separation of Concerns** (`separation_of_concerns`) — SOLID principles adherence
**16. Inline Documentation** (`inline_documentation`) — Docstrings >80% coverage
**17. Architecture Decision Records** (`adrs`) — Document major decisions in `docs/adr/`
**18. Structured Logging** (`structured_logging`) — JSON logs with consistent fields
**19. OpenAPI/Swagger Specs** (`api_documentation`) — Machine-readable API docs
**20. DRY Principle** (`dry_principle`) — <5% duplicate code

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md).*

---

## Tier 4: Advanced Attributes

*Refinement and optimization — 5% of total score*

### 21-25. Tier 4 Attributes

**21. Issue & PR Templates** (`pr_issue_templates`) — `.github/` templates
**22. Container/Virtualization Setup** (`container_setup`) — Dockerfile, docker-compose.yml
**23. Dependency Security Scanning** (`dependency_security`) — Snyk, Dependabot, npm audit
**24. Secrets Management** (`secrets_management`) — No hardcoded secrets, use env vars
**25. Performance Benchmarks** (`performance_benchmarks`) — Automated perf tests in CI

*Full details for each attribute available in the [research document](https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md).*

---

## Implementation Status

AgentReady's assessor implementations are actively maintained across four tiers. Most essential and critical attributes (Tier 1 and Tier 2) are fully implemented with rich remediation guidance.

**Current State**:
- ✅ **Tier 1 (Essential)**: Fully implemented
- ✅ **Tier 2 (Critical)**: Majority implemented
- 🚧 **Tier 3 (Important)**: Active development
- 🚧 **Tier 4 (Advanced)**: Planned implementations

See the [GitHub repository](https://github.com/ambient-code/agentready) for current implementation details.

---

## Next Steps

- **[User Guide](user-guide.html)** — Learn how to run assessments
- **[Developer Guide](developer-guide.html)** — Implement new assessors
- **[API Reference](api-reference.html)** — Integrate AgentReady
- **[Examples](examples.html)** — View real assessment reports

---

**Complete attribute research**: See [agent-ready-codebase-attributes.md](https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md) for full citations, examples, and detailed criteria.
