# AgentReady Coldstart Implementation Prompts

**Generated**: 2025-11-21
**Last Updated**: 2025-12-03
**Total Prompts**: 13 (7 completed, removed from this directory)
**Source**: BACKLOG.md + Community Contributions

---

## Overview

This directory contains comprehensive coldstart prompts for implementing all features in the AgentReady backlog. Each prompt is a self-contained implementation guide that includes:

- Full context about AgentReady architecture
- Complete feature requirements from BACKLOG.md
- Implementation checklist with all steps
- Testing strategy and coverage requirements
- Key files to review before starting
- Getting started guide with exact commands
- Success criteria for completion

These prompts are designed to be "drop in and go" - an AI agent or developer can take any prompt and implement the feature independently without needing additional context.

---

## Priority-Based Index

### P0 (Critical) - 3 Items (3 completed ✅)

| # | File | Title | Size | Status |
|---|------|-------|------|--------|
| 01 | ~~01-create-automated-demo.md~~ | Create Automated Demo | - | 🟢 Completed |
| 02 | [02-fix-critical-security-logic-bugs-from-code-review.md](02-fix-critical-security-logic-bugs-from-code-review.md) | Fix Critical Security & Logic Bugs from Code Review | 7.4K | 🔴 Not Started |
| 03 | ~~03-bootstrap-agentready-repository-on-github.md~~ | Bootstrap AgentReady Repository on GitHub | - | 🟢 Completed |
| 04 | [04-report-header-with-repository-metadata.md](04-report-header-with-repository-metadata.md) | Report Header with Repository Metadata | 6.8K | 🔴 Not Started |
| 05 | [05-improve-html-report-design-font-size-color-scheme.md](05-improve-html-report-design-font-size-color-scheme.md) | Improve HTML Report Design (Font Size & Color Scheme) | 8.6K | 🔴 Not Started |
| 17 | ~~17-add-bootstrap-quickstart-to-readme.md~~ | Add Bootstrap Quickstart to README.md | - | 🟢 Completed |

### P1 (High) - 2 Items (1 completed ✅)

| # | File | Title | Size | Status |
|---|------|-------|------|--------|
| 11 | [11-fix-code-quality-issues-from-code-review.md](11-fix-code-quality-issues-from-code-review.md) | Fix Code Quality Issues from Code Review | 6.6K | 🔴 Not Started |
| 12 | [12-improve-test-coverage-and-edge-case-handling.md](12-improve-test-coverage-and-edge-case-handling.md) | Improve Test Coverage and Edge Case Handling | 6.5K | 🔴 Not Started |
| 14 | ~~14-align-subcommand-automated-remediation.md~~ | Align Subcommand (Automated Remediation) | - | 🟢 Completed |

### P2 (Medium) - 5 Items

| # | File | Title | Size | Status |
|---|------|-------|------|--------|
| 13 | [13-add-security-quality-improvements-from-code-review.md](13-add-security-quality-improvements-from-code-review.md) | Add Security & Quality Improvements from Code Review | 5.7K | 🔴 Not Started |
| 15 | [15-interactive-dashboard-with-automated-remediation.md](15-interactive-dashboard-with-automated-remediation.md) | Interactive Dashboard with Automated Remediation | 11K | 🔴 Not Started |
| 16 | [16-github-app-integration-badge-status-checks.md](16-github-app-integration-badge-status-checks.md) | GitHub App Integration (Badge & Status Checks) | 11K | 🔴 Not Started |
| 18 | [18-setup-release-pipeline.md](18-setup-release-pipeline.md) | Setup GitHub Release Pipeline | 24K | 🟡 In Progress |
| 19 | [19-github-pages-linter-integration.md](19-github-pages-linter-integration.md) | GitHub Pages Linter Integration | 13K | 🔴 Not Started |

### P3 (Important) - 1 Item (1 completed ✅)

| # | File | Title | Size | Status |
|---|------|-------|------|--------|
| 06 | ~~06-report-schema-versioning.md~~ | Report Schema Versioning | - | 🟢 Completed |
| 09 | [09-agentready-repository-agent.md](09-agentready-repository-agent.md) | AgentReady Repository Agent | 5.8K | 🔴 Not Started |

### P4 (Enhancement) - 1 Item (2 completed ✅)

| # | File | Title | Size | Status |
|---|------|-------|------|--------|
| 07 | ~~07-research-report-generatorupdater-utility.md~~ | Research Report Generator/Updater Utility | - | 🟢 Completed |
| 08 | ~~08-repomix-integration.md~~ | Repomix Integration | - | 🟢 Completed |
| 10 | [10-customizable-html-report-themes.md](10-customizable-html-report-themes.md) | Customizable HTML Report Themes | 6.1K | 🔴 Not Started |

---

## Recommended Implementation Order

Based on priority and dependencies:

1. **P0 #02**: Fix Critical Security & Logic Bugs (XSS, StandardLayoutAssessor)
2. **P0 #03**: Bootstrap AgentReady Repository on GitHub (enables GitHub workflow)
3. **P0 #04**: Report Header with Repository Metadata (blocking usability)
4. **P0 #05**: Improve HTML Report Design (blocking adoption)
5. **P0 #01**: Create Automated Demo (showcase value)
6. **P1 #11**: Fix Code Quality Issues (TOCTOU, type annotations)
7. **P1 #12**: Improve Test Coverage (>80% target)
8. **P1 #14**: Align Subcommand (automated remediation)
9. **P2 #13**: Add Security & Quality Improvements (CSP, validation)
10. **P2 #15**: Interactive Dashboard (high value feature)
11. **P2 #16**: GitHub App Integration (badges, status checks)
12. **P3 #06**: Report Schema Versioning
13. **P3 #09**: AgentReady Repository Agent
14. **P4 #07**: Research Report Generator
15. **P4 #08**: Repomix Integration
16. **P4 #10**: Customizable HTML Report Themes

---

## Using These Prompts

### For AI Agents (Claude Code, etc.)

```bash
# Copy prompt content to AI agent
cat .github/coldstart-prompts/01-create-automated-demo.md

# Or open in editor
code .github/coldstart-prompts/01-create-automated-demo.md
```

### For Human Developers

1. **Pick a feature** from the priority list above
2. **Read the coldstart prompt** for complete context
3. **Create feature branch**: `git checkout -b NNN-feature-name`
4. **Follow the implementation checklist** in the prompt
5. **Run tests and linters** before committing
6. **Create PR** when complete

### Creating GitHub Issues

When the repository is on GitHub, you can create issues with:

```bash
# Generate all prompts and create GitHub issues
python scripts/backlog_to_issues.py --all --create-issues

# Create issue manually using prompt
gh issue create \
  --title "[P0] Create Automated Demo" \
  --body-file .github/coldstart-prompts/01-create-automated-demo.md \
  --label "priority:p0,enhancement"
```

---

## Prompt Structure

Each coldstart prompt follows this structure:

1. **Context** - Repository overview, structure, technologies
2. **Feature Requirements** - Complete requirements from BACKLOG.md
3. **Implementation Checklist** - Step-by-step guide
4. **Key Files to Review** - What to read before starting
5. **Testing Strategy** - Coverage requirements and test types
6. **Success Criteria** - How to know when done
7. **Getting Started** - Exact commands to begin

---

## Maintenance

**Updating Prompts**: If BACKLOG.md changes, regenerate prompts:

```bash
# Regenerate all prompts
python scripts/backlog_to_issues.py --all
```

**Tracking Progress**: Update status column in tables above as features are completed:
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed

---

## Statistics

- **Total Features**: 19
- **Completed**: 7 features (removed from this directory)
- **Remaining**: 13 features
- **P0 (Critical)**: 3 remaining (3 completed)
- **P1 (High)**: 2 remaining (1 completed)
- **P2 (Medium)**: 5 remaining
- **P3 (Important)**: 1 remaining (1 completed)
- **P4 (Enhancement)**: 1 remaining (2 completed)
- **Total Prompt Size**: ~125 KB (after cleanup)
- **Avg Prompt Size**: ~9.6 KB

---

**Last Updated**: 2025-12-03
**Generator Script**: `scripts/backlog_to_issues.py`
**Source Backlog**: `BACKLOG.md`
