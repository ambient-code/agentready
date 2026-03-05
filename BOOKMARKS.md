# AgentReady Bookmarks

Quick navigation to detailed documentation for specific tasks.

## Core Documentation

| Topic | Location | When to Use |
|-------|----------|-------------|
| User Guide | `README.md` | Installation, basic usage, CLI examples |
| Developer Guide | `docs/developer-guide.md` | In-depth development patterns |
| API Reference | `docs/api-reference.md` | Module and class documentation |
| Attributes | `docs/attributes.md` | All 25 assessed attributes explained |

## Assessors

| Topic | Location | When to Use |
|-------|----------|-------------|
| All Assessors | `src/agentready/assessors/__init__.py:49-93` | See full assessor list |
| Base Class | `src/agentready/assessors/base.py` | Creating new assessors |
| Documentation | `src/agentready/assessors/documentation.py` | CLAUDE.md, README assessors |
| Code Quality | `src/agentready/assessors/code_quality.py` | Type annotations, complexity |
| Testing | `src/agentready/assessors/testing.py` | Coverage, pre-commit hooks |
| Security | `src/agentready/assessors/security.py` | Dependency vulnerabilities |

## Scoring & Weights

| Topic | Location | When to Use |
|-------|----------|-------------|
| Default Weights | `src/agentready/data/default-weights.yaml` | Tier weight configuration |
| Scorer Logic | `src/agentready/services/scorer.py` | Score calculation algorithm |
| Research Report | `src/agentready/data/RESEARCH_REPORT.md` | Evidence for attribute selection |

## CLI Commands

| Topic | Location | When to Use |
|-------|----------|-------------|
| Main Entry | `src/agentready/cli/main.py` | Core CLI orchestration |
| Bootstrap | `src/agentready/cli/bootstrap.py` | Infrastructure setup command |
| Align | `src/agentready/cli/align.py` | Automated remediation command |
| Benchmark | `src/agentready/cli/benchmark.py` | Terminal-Bench integration |
| Learn | `src/agentready/cli/learn.py` | LLM-powered skill extraction |

## Benchmarks & Experiments

| Topic | Location | When to Use |
|-------|----------|-------------|
| Harbor Guide | `docs/harbor-comparison-guide.md` | A/B testing with Terminal-Bench |
| Harbor Models | `src/agentready/models/harbor.py` | HarborTaskResult, HarborComparison |
| Harbor Services | `src/agentready/services/harbor/` | Runner, comparer, result parser |
| SWE-bench | `experiments/README.md` | Validation workflow |

## Reports & Templates

| Topic | Location | When to Use |
|-------|----------|-------------|
| HTML Reporter | `src/agentready/reporters/html.py` | HTML report generation |
| Markdown Reporter | `src/agentready/reporters/markdown.py` | Markdown report generation |
| HTML Template | `src/agentready/templates/report.html.j2` | Jinja2 HTML template (73KB) |
| Example Reports | `examples/self-assessment/` | Sample output files |

## Schemas & Contracts

| Topic | Location | When to Use |
|-------|----------|-------------|
| Assessment Schema | `specs/001-agentready-scorer/contracts/assessment-schema.json` | JSON validation |
| Research Schema | `specs/001-agentready-scorer/contracts/research-report-schema.md` | Research format |
| Report Schemas | `specs/001-agentready-scorer/contracts/report-*.md` | HTML/Markdown format |

## CI/CD & Automation

| Topic | Location | When to Use |
|-------|----------|-------------|
| Main CI | `.github/workflows/ci.yml` | Test/lint pipeline |
| Release | `.github/workflows/release.yml` | Publishing workflow |
| Self-Assessment | `.github/workflows/agentready-assessment.yml` | Auto-assessment |
| PR Review | `.github/workflows/pr-review.yml` | Automated review |
| Claude Integration | `.github/CLAUDE_INTEGRATION.md` | Bot configuration |

## Testing

| Topic | Location | When to Use |
|-------|----------|-------------|
| Unit Tests | `tests/unit/` | Assessor and model tests |
| Integration Tests | `tests/integration/` | End-to-end tests |
| E2E Tests | `tests/e2e/` | Full workflow tests |
| Fixtures | `tests/fixtures/` | Test data |

## LLM Integration

| Topic | Location | When to Use |
|-------|----------|-------------|
| LLM Cache | `src/agentready/services/llm_cache.py` | Response caching (7-day TTL) |
| LLM Enricher | `src/agentready/learners/llm_enricher.py` | Claude API integration |
| Prompt Templates | `src/agentready/prompts/` | LLM prompt .md files |
| Skill Generator | `src/agentready/learners/skill_generator.py` | SKILL.md generation |

## Project Planning

| Topic | Location | When to Use |
|-------|----------|-------------|
| Backlog | `BACKLOG.md` | Future features |
| Changelog | `CHANGELOG.md` | Release history |
| Feature Specs | `specs/` | Design documents |
| Cold-Start Prompts | `plans/` (gitignored) | Agent handoff prompts |

---

*Use `Ctrl+F` or `Cmd+F` to search this file for keywords.*
