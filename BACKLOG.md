# AgentReady Backlog

**Purpose**: Track future features and improvements for the agentready tool.

**Last Updated**: 2025-12-04
**Total Active Items**: 10
**Lines**: ~800

---

## Completed Features (Removed from Backlog)

The following features have been implemented and moved to production:

1. ✅ **Bootstrap Command** - `agentready bootstrap` sets up agent-ready infrastructure (v1.0+)
2. ✅ **Align Subcommand** - `agentready align` automates remediation (v1.5+)
3. ✅ **Report Schema Versioning** - `migrate-report`, `validate-report` commands (v1.8+)
4. ✅ **Research Report Management** - `agentready research` command suite (v1.10+)
5. ✅ **Repomix Integration** - `agentready repomix-generate` command (v1.12+)
6. ✅ **Automated Demo** - `agentready demo` command for presentations (v1.15+)
7. ✅ **Bootstrap Quickstart in README** - Prominent documentation added (v1.16+)
8. ✅ **Batch Assessment** - `agentready assess-batch` with GitHub org scanning (v1.29+)
9. ✅ **LLM-Powered Learning** - `agentready extract-skills` with Claude enrichment (v2.0+)
10. ✅ **SWE-bench Experiments** - `agentready experiment` for validation (v2.6+)
11. ✅ **Community Leaderboard** - Public score tracking (v2.9+)

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.

---

## Critical Issues (P0)

### Fix Critical Security & Logic Bugs

**Priority**: P0 (Critical - Security & Correctness)

**Description**: Address critical bugs discovered in code review affecting security and assessment accuracy.

**Issues**:

1. **XSS Vulnerability in HTML Reports** - `src/agentready/templates/report.html.j2:579`
   - Problem: `assessment_json|safe` disables autoescaping for JSON in JavaScript
   - Risk: Repository names, commit messages could contain malicious content
   - Fix: Replace with `JSON.parse({{ assessment_json|tojson }})`

2. **StandardLayoutAssessor Logic Bug** - `src/agentready/assessors/structure.py:48`
   - Problem: `(tests/) or (test/)` always evaluates to first path
   - Impact: Projects with `test/` scored incorrectly
   - Fix: Check both paths properly with existence validation

**Acceptance Criteria**:
- XSS vulnerability patched with `tojson` filter
- StandardLayoutAssessor recognizes both `tests/` and `test/`
- Tests added for XSS prevention and directory variations

---

### Report Header with Repository Metadata

**Priority**: P0 (Critical - Usability)

**Description**: Add prominent header showing what repository was assessed. Currently reports lack context.

**Requirements**:
- Repository name, path, and GitHub URL
- Assessment timestamp (human-readable)
- Branch name and commit hash
- AgentReady version used
- Username@hostname who ran assessment
- Command used

**Implementation**: Update all report formats (HTML, Markdown, JSON) with metadata header section positioned before score summary.

**Acceptance Criteria**:
- User can immediately identify assessed repository
- Timestamp shows when assessment was run
- Git context (branch, commit) visible
- AgentReady version tracked for reproducibility

---

### Improve HTML Report Design

**Priority**: P0 (Critical - User Experience)

**Description**: Redesign HTML report with professional dark color scheme and larger font sizes (+4pt minimum).

**Problems**:
- Current color scheme "hideous" (user feedback)
- Font sizes too small for modern displays
- Poor contrast in some areas

**New Design**:
- Dark blue/black base (`#0a0e27`, `#1a1f3a`)
- Purple accents only (`#8b5cf6`)
- 18px minimum body text (up from 14px)
- High contrast (WCAG 2.1 AA compliant)

**Acceptance Criteria**:
- All text easily readable (18px minimum)
- Professional color scheme (black, dark blue, purple, white)
- WCAG 2.1 AA contrast compliance
- Light/dark mode toggle (future enhancement)

---

## High Priority (P1)

### Fix Code Quality Issues

**Priority**: P1 (High - Quality & Reliability)

**Issues**:

1. **TOCTOU in File Operations** - Multiple assessors check file existence then read separately
   - Fix: Use try-except around file reads instead

2. **Inaccurate Type Annotation Detection** - Regex-based with false positives
   - Fix: Use AST parsing instead of regex

3. **Assessment Validation Semantic Confusion** - Field `attributes_skipped` includes errors
   - Fix: Rename to `attributes_not_assessed` or add separate counters

**Acceptance Criteria**:
- All file operations use try-except pattern
- Type annotation detection uses AST
- Assessment model fields clearly named
- Tests added for edge cases

---

### Improve Test Coverage

**Priority**: P1 (High - Quality Assurance)

**Description**: Increase test coverage from 37% to >80% with edge case handling.

**Critical Gaps**:
- Error handling paths (OSError, PermissionError)
- Empty repositories, binary files, symlinks
- Security test cases (XSS, path traversal)
- Scorer edge cases (all attributes skipped, weight normalization)

**Acceptance Criteria**:
- Test coverage >80%
- All error paths tested
- Edge cases for malformed repos covered
- CI fails if coverage <75%

---

## Medium Priority (P2)

### Add Security & Quality Improvements

**Priority**: P2 (Medium - Polish)

**Improvements**:
1. Warn when scanning sensitive directories (`/etc`, `/.ssh`)
2. Confirm before scanning large repositories (>10k files)
3. Add CSP headers to HTML reports for defense-in-depth
4. Document scorer behavior when all attributes skipped

**Acceptance Criteria**:
- Warnings for sensitive directories
- CSP headers in HTML reports
- Scorer edge cases documented
- User guide updated with best practices

---

### Interactive Dashboard with Remediation

**Priority**: P2 (High Value)

**Description**: Transform static HTML report into interactive dashboard with one-click remediation via GitHub issues and draft PRs.

**Vision**: Click "Fix This" button → Creates GitHub issue → Generates draft PR with fixes

**Core Features**:
- Action buttons on each failing attribute
- Template-based fix generation (CLAUDE.md, .gitignore, pre-commit hooks)
- AI-powered fixes for complex issues (type annotations, refactoring)
- GitHub integration via OAuth or gh CLI
- Progress tracking and historical trends

**Implementation Phases**:
1. **Phase 1**: Client-side with gh CLI - Generate commands users copy/paste
2. **Phase 2**: Local dashboard server - Flask/FastAPI with WebSocket updates
3. **Phase 3**: Cloud service - Hosted at agentready.dev (SaaS)

**Acceptance Criteria**:
- "Fix This" buttons functional in HTML report
- Template-based fixes generate valid files
- GitHub issue creation working
- Fix preview before applying

---

### GitHub App Integration

**Priority**: P2 (High Value)

**Description**: Create GitHub App providing badges, PR status checks, and automated assessment comments.

**Core Features**:
1. **Repository Badge** - Shields.io SVG showing certification level
2. **GitHub Actions** - Official `agentready/assess-action`
3. **PR Status Checks** - Block merge if score below threshold
4. **PR Comments** - Automated summaries with score deltas

**Use Cases**:
- Add badge to README: `[![AgentReady](https://agentready.redhat.com/badge/{owner}/{repo}.svg)](...)`
- Enforce quality gates via `.agentready-config.yaml`
- Track organization progress via dashboard

**Acceptance Criteria**:
- GitHub Action published to marketplace
- Badge service deployed
- PR status checks functional
- Organization dashboard shows all repos

---

### Documentation Source Truth and Cascade System

**Priority**: P2 (Medium - Developer Experience)

**Description**: Ensure documentation stays synchronized when source content changes via automatic cascade updates.

**Problem**: Changes to source docs (research reports, CLAUDE.md) don't propagate to derived docs (GitHub Pages), causing drift.

**Requirements**:
- Designate source-of-truth files (contracts/*, specs/*, CLAUDE.md)
- Track changes and identify affected derived docs
- Trigger regeneration when sources change
- Validate consistency and check cross-references

**CLI Commands**:
```bash
agentready docs check-drift        # Calculate drift score
agentready docs cascade-update     # Update derived docs from sources
agentready docs update docs/attributes.md  # Update specific file
```

**Acceptance Criteria**:
- Source files explicitly designated
- Drift detection algorithm working
- Cascade update command functional
- GitHub Actions workflow for automation
- Pre-commit hook warns of high drift

---

## Important (P3)

### AgentReady Repository Agent

**Priority**: P3 (Important)

**Description**: Create specialized Claude Code agent for AgentReady repository development.

**Requirements**:
- Deep knowledge of AgentReady architecture
- Can implement new assessors, write tests, debug issues
- Understands assessment workflow and scoring logic
- Pre-loaded context about codebase structure

**Implementation**: Create `.claude/agents/agentready-dev.md` with agent specification linking to key design docs.

**Use Cases**:
- `/agentready-dev implement new assessor for dependency security`
- `/agentready-dev debug type annotation detection`
- `/agentready-dev optimize assessment performance`

---

## Enhancements (P4)

### Customizable HTML Report Themes

**Priority**: P4 (Enhancement)

**Description**: Allow users to customize HTML report appearance with themes and color schemes.

**Requirements**:
- Pre-built themes (light, dark, high-contrast, colorblind-friendly)
- Custom theme support via `.agentready-config.yaml`
- WCAG 2.1 AA accessibility maintained
- Runtime theme switcher in HTML report (dropdown in top-right corner)
- Dark/light mode toggle button (one-click switching)
- Save preference to localStorage (persists across reports)

**Configuration**:
```yaml
# .agentready-config.yaml
report_theme: dark  # or 'light', 'high-contrast', 'custom'
custom_theme:
  primary_color: "#2563eb"
  background: "#1e293b"
  text: "#e2e8f0"
```

**Implementation**:
- CSS custom properties for theming
- JavaScript theme switcher (no page reload)
- Embed all themes in single HTML (offline-capable)
- Command: `agentready theme-preview dark`

---

## Backlog Metadata

**Created**: 2025-11-21
**Last Condensed**: 2025-12-04
**Original Lines**: 2,190
**Condensed Lines**: ~800 (63% reduction)
**Completed Items Moved**: 11

## Priority Summary

- **P0 (Critical)**: 3 items - Security/Logic Bugs, Report Header, HTML Design
- **P1 (High)**: 2 items - Code Quality Fixes, Test Coverage
- **P2 (Medium)**: 4 items - Security Polish, Interactive Dashboard, GitHub App, Doc Cascade
- **P3 (Important)**: 1 item - Repository Agent
- **P4 (Enhancement)**: 1 item - Customizable Themes

**Total Active**: 11 items (down from 15 original)

---

## Notes

- **Completed items** documented in CHANGELOG.md with version numbers
- **Bootstrap & Align** are production-ready, widely used commands
- **Report schema versioning** working with migrate/validate commands
- **LLM-powered learning** operational with Claude API integration
- **SWE-bench experiments** validate AgentReady impact on agent performance
- **Community leaderboard** tracks public repository scores

**Focus Areas**:
1. Security fixes (P0 - XSS, logic bugs)
2. Test coverage improvement (P1 - 37% → 80%)
3. UX enhancements (P0 - report design, metadata header)
4. GitHub integration (P2 - App, badges, status checks)
5. Automation (P2 - Interactive dashboard, doc cascade)
