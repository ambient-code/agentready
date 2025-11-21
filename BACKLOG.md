# AgentReady Backlog

**Purpose**: Track future features and improvements for the agentready tool.

---

## Critical Issues (P0)

### Create Automated Demo

**Priority**: P0 (Critical - Showcase Value)

**Description**: Create an automated, self-contained demonstration of AgentReady that shows the tool assessing a sample repository, generating reports, and providing remediation guidance. This should be runnable with a single command and suitable for demos, presentations, and onboarding.

**Requirements**:
- Single command to run: `agentready demo`
- Self-contained sample repository (embedded in package or generated on-the-fly)
- Demonstrates full workflow:
  1. Repository analysis
  2. Attribute assessment
  3. Score calculation
  4. HTML/Markdown report generation
  5. Remediation suggestions
- Interactive terminal output showing progress
- Opens generated HTML report automatically in browser
- Reusable for presentations and stakeholder demos

**Implementation**:

```bash
# Run automated demo
agentready demo

# Output:
# 🤖 AgentReady Demo
# ===================
#
# Creating sample repository...
# Analyzing structure...
# Running 25 assessments...
#   ✅ claude_md_file (100/100)
#   ❌ precommit_hooks (0/100)
#   ... [progress indicators]
#
# Assessment complete!
# Score: 67.3/100 (Silver)
#
# Generating reports...
#   📄 demo-report.html (generated)
#   📄 demo-report.md (generated)
#   📄 demo-assessment.json (generated)
#
# Opening HTML report in browser...
```

**Sample Repository Options**:

**Option 1: Embedded Examples** (Ship with package)
```
src/agentready/demo/
├── sample-python-repo/      # Python project (minimal)
│   ├── src/myapp/
│   ├── tests/
│   ├── README.md
│   ├── pyproject.toml
│   └── .gitignore
├── sample-js-repo/          # JavaScript project
│   ├── src/
│   ├── package.json
│   └── README.md
└── sample-go-repo/          # Go project
```

**Option 2: Generate On-the-Fly** (Dynamic)
```python
def create_demo_repo(tmp_path: Path, language: str = "python") -> Path:
    """Create sample repository for demo."""
    repo = tmp_path / "demo-repo"
    repo.mkdir()

    if language == "python":
        # Create minimal Python project
        create_file(repo / "README.md", "# Demo Project\n\nSample Python project.")
        create_file(repo / "src/main.py", "def main(): pass")
        create_file(repo / ".gitignore", "*.pyc\n__pycache__/")
        # Missing: CLAUDE.md, tests/, pre-commit hooks (intentional for demo)

    return repo
```

**Demo Script Features**:
- **Progress indicators**: Show assessment running in real-time
- **Color-coded output**: Green for pass, red for fail, yellow for warnings
- **Simulated delays**: Add realistic pauses for "dramatic effect" in demos
- **Narration mode**: Optional verbose output explaining each step
- **Screenshot mode**: Generate high-quality terminal screenshots for docs
- **Record mode**: Save terminal session as GIF/video for presentations

**Configuration**:

```yaml
# Demo config embedded in package
demo:
  sample_repo: python  # or javascript, go, minimal
  show_progress: true
  auto_open_browser: true
  output_dir: ./demo-output
  narration: true  # Explain each step
  delay_ms: 500    # Pause between steps for visibility
```

**Use Cases**:

**Use Case 1: Stakeholder Demo**
```bash
# Quick 2-minute demo for leadership
agentready demo --narration
# Shows: What AgentReady does, how it scores, what reports look like
```

**Use Case 2: Onboarding New Users**
```bash
# Help new users understand the tool
agentready demo --tutorial
# Interactive walkthrough with explanations
```

**Use Case 3: Generate Demo Content for Docs**
```bash
# Create screenshots and videos for documentation
agentready demo --screenshot --record demo.gif
```

**Acceptance Criteria**:
- [ ] `agentready demo` runs without any setup
- [ ] Creates sample repository automatically
- [ ] Runs full assessment workflow
- [ ] Generates all report formats (HTML, Markdown, JSON)
- [ ] Opens HTML report in browser
- [ ] Colorful, engaging terminal output
- [ ] Completes in < 5 seconds
- [ ] No external dependencies required
- [ ] Works offline
- [ ] Includes narration mode for presentations

**Priority Justification**:
- Critical for showcasing tool value to stakeholders
- Needed for Red Hat internal demos and presentations
- Helps with user onboarding and adoption
- Low effort, high impact for visibility
- Required before pitching to other Red Hat teams

**Related**: Onboarding, documentation, marketing

**Notes**:
- Keep demo simple and fast (< 5 seconds)
- Focus on visual impact (colors, progress bars)
- Make it suitable for screenshots/videos
- Consider adding "failure scenario" demo too
- Could expand to multiple language demos
- Add to bootstrap command as part of repo setup

---

### Fix Critical Security & Logic Bugs from Code Review

**Priority**: P0 (Critical - Security & Correctness)

**Description**: Address critical bugs discovered in code review that affect security and assessment accuracy.

**Issues to Fix**:

1. **XSS Vulnerability in HTML Reports** (CRITICAL - Security)
   - **Location**: `src/agentready/templates/report.html.j2:579`
   - **Problem**: `assessment_json|safe` disables autoescaping for JSON embedded in JavaScript
   - **Risk**: Repository names, commit messages, file paths from git could contain malicious content
   - **Fix**: Replace with `JSON.parse({{ assessment_json|tojson }})`
   - **Add**: Content Security Policy headers to HTML reports

2. **StandardLayoutAssessor Logic Bug** (CRITICAL - Incorrect Scoring)
   - **Location**: `src/agentready/assessors/structure.py:48`
   - **Problem**: `(repository.path / "tests") or (repository.path / "test")` always evaluates to first path
   - **Impact**: Projects with `test/` instead of `tests/` scored incorrectly
   - **Fix**: Check both paths properly:
     ```python
     tests_path = repository.path / "tests"
     if not tests_path.exists():
         tests_path = repository.path / "test"
     has_tests = tests_path.exists()
     ```

**Implementation**:

**File 1**: `src/agentready/templates/report.html.j2`
```jinja2
<!-- BEFORE (VULNERABLE): -->
const ASSESSMENT = {{ assessment_json|safe }};

<!-- AFTER (SECURE): -->
const ASSESSMENT = JSON.parse({{ assessment_json|tojson }});
```

**File 2**: `src/agentready/assessors/structure.py`
```python
# BEFORE (BUGGY):
standard_dirs = {
    "src": repository.path / "src",
    "tests": (repository.path / "tests") or (repository.path / "test"),  # BUG!
}

# AFTER (CORRECT):
standard_dirs = {
    "src": repository.path / "src",
}

# Check for tests directory (either tests/ or test/)
tests_path = repository.path / "tests"
if not tests_path.exists():
    tests_path = repository.path / "test"
standard_dirs["tests"] = tests_path
```

**Test Cases to Add**:
```python
def test_xss_in_repository_name():
    """Test that malicious repo names are escaped in HTML."""
    repo = Repository(
        name="<script>alert('xss')</script>",
        # ...
    )
    html = HTMLReporter().generate(assessment, output)
    assert "<script>" not in html  # Should be escaped

def test_standard_layout_with_test_dir():
    """Test that 'test/' directory is recognized (not just 'tests/')."""
    # Create repo with test/ directory only
    repo_path = tmp_path / "repo"
    (repo_path / "test").mkdir(parents=True)

    assessor = StandardLayoutAssessor()
    finding = assessor.assess(Repository(...))
    assert finding.status == "pass"  # Should recognize test/ dir
```

**Acceptance Criteria**:
- [ ] XSS vulnerability patched with `tojson` filter
- [ ] CSP headers added to HTML reports (future)
- [ ] StandardLayoutAssessor recognizes both `tests/` and `test/`
- [ ] Tests added for XSS prevention
- [ ] Tests added for both test directory naming patterns
- [ ] All existing tests still pass

**Priority Justification**:
- **Security**: XSS is a P0 vulnerability
- **Correctness**: Incorrect scoring undermines tool credibility
- **Quick fixes**: Both are 5-10 minute changes

**Related**: Issue #2 (Report improvements), Bootstrap (#1 - needs secure reports)

---

### Bootstrap AgentReady Repository on GitHub

**Priority**: P0 (Critical - Dogfooding)

**Description**: Implement `agentready bootstrap` command to set up the agentready repository itself on GitHub with all best practices. This is the FIRST feature to implement - we'll dogfood our own tool!

**Vision**: Use AgentReady to bootstrap the AgentReady repository - demonstrating the tool's value while setting up our own infrastructure.

**Why P0**:
- Demonstrates tool value immediately (dogfooding)
- Sets up critical GitHub infrastructure (Actions, badges, PR templates)
- Validates bootstrap command design before external users
- Creates the foundation for GitHub App integration

**Requirements**:

1. **GitHub Repository Setup**
   - Create/update repository on GitHub via `gh` CLI
   - Set repository description and topics
   - Configure repository settings (PR requirements, branch protection)

2. **GitHub Actions Workflows**
   - `.github/workflows/agentready-assessment.yml` - Run assessment on PR/push
   - `.github/workflows/tests.yml` - Run pytest, linters
   - `.github/workflows/release.yml` - Publish to PyPI (future)

3. **GitHub Templates**
   - `.github/ISSUE_TEMPLATE/bug_report.md`
   - `.github/ISSUE_TEMPLATE/feature_request.md`
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.github/CODEOWNERS`

4. **Pre-commit Hooks**
   - `.pre-commit-config.yaml` with black, isort, ruff
   - Conventional commit linting (commitlint)
   - Auto-run tests before commit

5. **Dependency Management**
   - Dependabot configuration (`.github/dependabot.yml`)
   - Security scanning (`.github/workflows/security.yml`)

6. **Documentation Updates**
   - Update README.md with badges
   - Add CONTRIBUTING.md
   - Add CODE_OF_CONDUCT.md (Red Hat standard)
   - Add LICENSE (Apache 2.0 or MIT)

**Command Interface**:

```bash
# Bootstrap current repository on GitHub
agentready bootstrap .

# Bootstrap with specific language
agentready bootstrap . --language python

# Bootstrap and create GitHub repo
agentready bootstrap . --create-repo redhat/agentready

# Dry run (show what would be created)
agentready bootstrap . --dry-run

# Interactive mode (confirm each file)
agentready bootstrap . --interactive
```

**What Gets Created**:

```
.github/
├── workflows/
│   ├── agentready-assessment.yml  # Run assessment on PR
│   ├── tests.yml                  # Run tests and linters
│   └── dependabot.yml            # Dependency updates
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   └── feature_request.md
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS
└── dependabot.yml

.pre-commit-config.yaml
CONTRIBUTING.md
CODE_OF_CONDUCT.md
LICENSE
```

**GitHub Actions Workflow Example**:

```yaml
# .github/workflows/agentready-assessment.yml
name: AgentReady Assessment

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install AgentReady
        run: |
          pip install agentready

      - name: Run Assessment
        run: |
          agentready assess . --verbose

      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: agentready-reports
          path: .agentready/

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.agentready/report-latest.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

**Implementation Phases**:

**Phase 1: Core Bootstrap** (This Sprint)
- Implement `agentready bootstrap` command
- Create template files for GitHub Actions, pre-commit, templates
- Test on agentready repository itself
- Commit all generated files

**Phase 2: GitHub Integration** (Next Sprint)
- Use `gh` CLI to create/update repository
- Set up branch protection rules
- Configure repository settings
- Add repository badges

**Phase 3: Language-Specific Templates** (Future)
- Python-specific templates (pytest, black, mypy)
- JavaScript-specific (eslint, prettier, jest)
- Go-specific (golangci-lint, gotestsum)

**Files to Create**:

```
src/agentready/
├── cli/bootstrap.py           # Bootstrap CLI command
├── bootstrap/
│   ├── __init__.py
│   ├── generator.py          # File generator
│   ├── github_setup.py       # GitHub integration
│   └── templates/            # Template files
│       ├── github/
│       │   ├── workflows/
│       │   │   ├── agentready.yml.j2
│       │   │   └── tests.yml.j2
│       │   ├── ISSUE_TEMPLATE/
│       │   └── PULL_REQUEST_TEMPLATE.md.j2
│       ├── precommit.yaml.j2
│       ├── CONTRIBUTING.md.j2
│       └── CODE_OF_CONDUCT.md.j2
tests/unit/test_bootstrap.py
```

**Acceptance Criteria**:

- [ ] `agentready bootstrap .` creates all required files
- [ ] GitHub Actions workflows are valid and functional
- [ ] Pre-commit hooks install and run successfully
- [ ] Repository badges added to README.md
- [ ] Dry-run mode shows what would be created
- [ ] Interactive mode prompts for confirmation
- [ ] Successfully bootstrap agentready repository itself
- [ ] All generated files committed to agentready repo
- [ ] GitHub Actions runs assessment on every PR

**Success Metrics**:

- AgentReady repository on GitHub has:
  - ✅ GitHub Actions running assessments
  - ✅ PR template with checklist
  - ✅ Issue templates for bugs/features
  - ✅ Pre-commit hooks configured
  - ✅ Dependabot enabled
  - ✅ Repository badge showing score
  - ✅ All linters passing in CI

**Priority Justification**:

This is P0 because:
1. **Dogfooding** - We need this for our own repository first
2. **Demonstrates value** - Shows AgentReady in action on itself
3. **Foundation** - Required before GitHub App integration
4. **Credibility** - Can't tell others to use it if we don't use it ourselves

**Related**: GitHub App Integration (#5), Align Command (#3)

**Notes**:
- Start with Python-specific templates (our use case)
- Keep templates simple and focused
- Use Jinja2 for template rendering
- Integrate with `gh` CLI for GitHub operations
- All templates should pass AgentReady assessment!

---

### Report Header with Repository Metadata

**Priority**: P0 (Critical - Blocking Usability)

**Description**: Add prominent report header showing what repository/agent/code was scanned. Currently reports lack context about what was assessed.

**Problem**: Users cannot identify what the report is about without digging into the details. No repository name, path, timestamp, or assessment context visible at the top.

**Requirements**:
- **Prominent header section** at the top of all report formats (HTML, Markdown, JSON)
- Repository name (bold, large font)
- Repository path (absolute path on filesystem or GitHub URL)
- Assessment timestamp (human-readable: "November 21, 2025 at 2:11 AM")
- Branch name and commit hash
- AgentReady version used for assessment
- Who ran the assessment (username@hostname)
- Command used: `agentready assess /path/to/repo --verbose`

**HTML Report Header Design**:
```html
<header class="report-header">
  <div class="repo-info">
    <h1>AgentReady Assessment Report</h1>
    <div class="repo-name">Repository: agentready</div>
    <div class="repo-path">/Users/jeder/repos/sk/agentready</div>
    <div class="repo-git">Branch: 001-agentready-scorer | Commit: d49947c</div>
  </div>
  <div class="meta-info">
    <div>Assessed: November 21, 2025 at 2:11 AM</div>
    <div>AgentReady Version: 1.0.0</div>
    <div>Run by: jeder@macbook</div>
  </div>
</header>
```

**Markdown Report Header**:
```markdown
# 🤖 AgentReady Assessment Report

**Repository**: agentready
**Path**: `/Users/jeder/repos/sk/agentready`
**Branch**: `001-agentready-scorer` | **Commit**: `d49947c`
**Assessed**: November 21, 2025 at 2:11 AM
**AgentReady Version**: 1.0.0
**Run by**: jeder@macbook

---
```

**JSON Report Metadata**:
```json
{
  "metadata": {
    "agentready_version": "1.0.0",
    "assessment_timestamp": "2025-11-21T02:11:05Z",
    "assessment_timestamp_human": "November 21, 2025 at 2:11 AM",
    "executed_by": "jeder@macbook",
    "command": "agentready assess . --verbose",
    "working_directory": "/Users/jeder/repos/sk/agentready"
  },
  "repository": { ... }
}
```

**Implementation**:
- Add metadata collection to Scanner
- Update all reporter templates (HTML, Markdown)
- Enhance Assessment model with metadata field
- Position header prominently (before score summary)

**Acceptance Criteria**:
- ✅ User can immediately identify what repository was assessed
- ✅ Timestamp shows when assessment was run
- ✅ Git context (branch, commit) visible
- ✅ AgentReady version tracked for reproducibility

**Related**: Report generation, usability, debugging

**Notes**:
- This is blocking adoption - users confused about report context
- Critical for multi-repository workflows
- Needed for CI/CD integration (track which build)

---

### Improve HTML Report Design (Font Size & Color Scheme)

**Priority**: P0 (Critical - Poor User Experience)

**Description**: Completely redesign HTML report color scheme and increase all font sizes by at least 4 points for readability.

**Problems**:
1. **Color scheme is "hideous"** (user feedback) - current purple gradient doesn't work
2. **Font sizes too small** - hard to read on modern displays
3. **Poor contrast** - some text hard to distinguish

**New Color Scheme** (Dark/Professional):
```css
:root {
  /* Base colors - mostly black, dark blue, purple, white */
  --background: #0a0e27;           /* Almost black with blue tint */
  --surface: #1a1f3a;              /* Dark blue surface */
  --surface-elevated: #252b4a;     /* Slightly lighter surface */

  /* Primary colors */
  --primary: #8b5cf6;              /* Purple (accent) */
  --primary-light: #a78bfa;        /* Light purple */
  --primary-dark: #6d28d9;         /* Dark purple */

  /* Text colors */
  --text-primary: #f8fafc;         /* Almost white */
  --text-secondary: #cbd5e1;       /* Light gray */
  --text-muted: #94a3b8;           /* Muted gray */

  /* Status colors */
  --success: #10b981;              /* Green (pass) */
  --warning: #f59e0b;              /* Amber (warning) */
  --danger: #ef4444;               /* Red (fail) */
  --neutral: #64748b;              /* Gray (skipped) */

  /* UI elements */
  --border: #334155;               /* Dark border */
  --shadow: rgba(0, 0, 0, 0.5);   /* Deep shadows */
}
```

**Font Size Increases** (+4pt minimum):
```css
/* Current → New */
body { font-size: 14px → 18px; }
h1 { font-size: 28px → 36px; }
h2 { font-size: 24px → 30px; }
h3 { font-size: 20px → 26px; }
.score { font-size: 48px → 56px; }
.attribute-name { font-size: 16px → 22px; }
.evidence { font-size: 13px → 17px; }
code { font-size: 13px → 16px; }
```

**Design Mockup**:
```
┌─────────────────────────────────────────────────────┐
│ [Dark navy blue background #1a1f3a]                │
│                                                     │
│  🤖 AgentReady Assessment Report                   │
│  Repository: agentready                            │
│  /Users/jeder/repos/sk/agentready                  │
│  [White text #f8fafc, 18px base font]             │
│                                                     │
├─────────────────────────────────────────────────────┤
│ [Purple accent card #8b5cf6]                       │
│                                                     │
│           75.4 / 100                               │
│           [56px, bold, white]                      │
│           🥇 Gold                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Implementation Checklist**:
- [ ] Replace gradient backgrounds with dark blue/black
- [ ] Update all font sizes (+4pt minimum)
- [ ] Use purple (#8b5cf6) sparingly as accent color
- [ ] Ensure white text on dark backgrounds (WCAG AA)
- [ ] Update certification level colors
- [ ] Redesign score cards with new scheme
- [ ] Test with colorblind simulators
- [ ] Add light mode as alternative (with same professional palette)

**Before/After Color Comparison**:
```
Current (Problems):
- Purple gradient everywhere: #667eea → #764ba2 ❌
- Small text: 14px base ❌
- Busy, overwhelming ❌

New (Professional):
- Dark blue/black base: #0a0e27, #1a1f3a ✅
- Purple accents only: #8b5cf6 ✅
- Large text: 18px base ✅
- Clean, readable ✅
```

**Acceptance Criteria**:
- ✅ All text easily readable (18px minimum body text)
- ✅ Color scheme uses black, dark blue, purple, white palette
- ✅ High contrast (WCAG 2.1 AA compliant)
- ✅ Professional appearance suitable for Red Hat engineering
- ✅ Purple used as accent, not dominant color

**Related**: HTML report generation, UX, accessibility

**Notes**:
- Current design blocks user adoption (visual issues)
- This is the first thing users see - must be excellent
- Consider adding screenshot to docs after redesign
- Font size critical for presentations and stakeholder reviews

---

## Schema & Configuration

### Report Schema Versioning

**Priority**: P3 (Important)

**Description**: Define and version the JSON/HTML/Markdown report schemas to ensure backwards compatibility and enable schema evolution.

**Requirements**:
- JSON schema for assessment reports (contracts/assessment-schema.json exists)
- HTML schema for interactive reports (contracts/report-html-schema.md exists)
- Markdown schema for version control reports (contracts/report-markdown-schema.md exists)
- Schema versioning strategy (semantic versioning)
- Backwards compatibility testing
- Schema migration tools for major version changes

**Use Case**:
```bash
# Validate report against schema
agentready validate-report assessment-2025-11-20.json

# Migrate old report to new schema version
agentready migrate-report --from 1.0.0 --to 2.0.0 old-report.json
```

**Related**: Report generation, data model evolution

**Notes**:
- Schemas exist in contracts/ directory but need formal versioning
- Consider using JSON Schema Draft 2020-12
- Tool should validate generated reports against bundled schema
- Breaking schema changes should trigger major version bump

---

### Research Report Generator/Updater Utility

**Priority**: P4 (Enhancement)

**Description**: Create a utility tool to help maintain and update the research report (agent-ready-codebase-attributes.md) following the validation schema defined in contracts/research-report-schema.md.

**Requirements**:
- Generate new research reports from templates
- Validate existing reports against schema (contracts/research-report-schema.md)
- Update/add attributes while maintaining schema compliance
- Automatically format citations and references
- Extract tier assignments and metadata
- Verify 25 attributes, 4 tiers, 20+ references
- Check for required sections (Definition, Measurable Criteria, Impact on Agent Behavior)

**Use Case**:
```bash
# Validate existing research report
agentready research validate agent-ready-codebase-attributes.md

# Generate new research report from template
agentready research init --output new-research.md

# Add new attribute to research report
agentready research add-attribute \
  --id "attribute_26" \
  --name "New Attribute" \
  --tier 2 \
  --file research.md

# Update metadata (version, date)
agentready research bump-version --type minor

# Lint and format research report
agentready research format research.md
```

**Features**:
- Schema validation (errors vs warnings per research-report-schema.md)
- Automated metadata header generation (version, date in YAML frontmatter)
- Attribute numbering consistency checks (1.1, 1.2, ..., 15.1)
- Citation deduplication and formatting
- Tier distribution balance warnings
- Category coverage analysis
- Markdown formatting enforcement (consistent structure)
- Reference URL reachability checks

**Related**: Research report maintenance, schema compliance, documentation quality

**Notes**:
- Must follow contracts/research-report-schema.md validation rules
- Should prevent invalid reports from being committed
- Could integrate with pre-commit hooks for research report changes
- Consider CLI commands under `agentready research` subcommand
- Tool should be self-documenting (help users fix validation errors)
- Future: Could use LLMs to help generate attribute descriptions from academic papers

---

### Repomix Integration

**Priority**: P4 (Enhancement)

**Description**: Integrate with Repomix (https://github.com/yamadashy/repomix) to generate AI-optimized repository context files for both new and existing repositories.

**Requirements**:
- Generate Repomix output for existing repositories
- Include Repomix configuration in bootstrapped new repositories
- Optional GitHub Actions integration for automatic regeneration
- Support Repomix configuration customization
- Integrate with agentready assessment workflow

**Use Case**:
```bash
# Generate Repomix output for current repository
agentready repomix-generate

# Bootstrap new repo with Repomix integration
agentready init --repo my-project --language python --repomix

# This would:
# 1. Set up Repomix configuration
# 2. Add GitHub Action for automatic regeneration
# 3. Generate initial repository context file
# 4. Include Repomix output in .gitignore appropriately
```

**Features**:
- Automatic Repomix configuration based on repository language
- GitHub Actions workflow for CI/CD integration
- Custom ignore patterns aligned with agentready assessment
- Support for both markdown and XML output formats
- Integration with agentready bootstrap command

**Related**: Repository initialization, AI-assisted development workflows

**Notes**:
- Repomix generates optimized repository context for LLMs
- Could enhance CLAUDE.md with reference to Repomix output
- Should align with existing .gitignore patterns
- Consider adding Repomix freshness check to assessment attributes
- May improve agentready's own repository understanding

---

### AgentReady Repository Agent

**Priority**: P3 (Important)

**Description**: Create a specialized Claude Code agent for the AgentReady repository to assist with development, testing, and maintenance tasks.

**Requirements**:
- Agent with deep knowledge of AgentReady architecture
- Understands assessment workflow, scoring logic, and report generation
- Can help with:
  - Implementing new assessors
  - Enhancing existing assessors
  - Writing tests for new features
  - Debugging assessment issues
  - Improving report templates
  - Optimizing performance

**Use Case**:
```bash
# In Claude Code, use the agentready-dev agent
/agentready-dev implement new assessor for dependency security scanning
/agentready-dev debug why Python type annotation detection is failing
/agentready-dev optimize assessment performance for large repositories
```

**Features**:
- Pre-loaded context about AgentReady codebase structure
- Knowledge of assessment attributes and scoring algorithm
- Understanding of tier-based weighting system
- Familiar with reporter implementations (HTML, Markdown)
- Can generate new assessors following established patterns

**Implementation**:
- Create `.claude/agents/agentready-dev.md` with agent specification
- Include links to key design documents (data-model.md, plan.md, research.md)
- Provide common development patterns and examples
- Reference test structure and coverage requirements

**Related**: Development workflow, code generation, testing

**Notes**:
- Agent should follow constitution principles (library-first, TDD when requested)
- Should know about stub assessors and how to expand them
- Can help with performance benchmarking and optimization
- Should understand the research report structure and attribute definitions

---

### Customizable HTML Report Themes

**Priority**: P4 (Enhancement)

**Description**: Allow users to customize the appearance of HTML reports with themes, color schemes, and layout options.

**Requirements**:
- Theme system for HTML reports
- Pre-built themes (default, dark mode, high contrast, colorblind-friendly)
- Custom theme support via configuration
- Maintain accessibility standards (WCAG 2.1 AA)
- Preview themes before applying

**Use Case**:
```yaml
# .agentready-config.yaml
report_theme: dark  # or 'light', 'high-contrast', 'custom'

custom_theme:
  primary_color: "#2563eb"
  success_color: "#10b981"
  warning_color: "#f59e0b"
  danger_color: "#ef4444"
  background: "#1e293b"
  text: "#e2e8f0"
  font_family: "Inter, sans-serif"
```

**Features**:
- **Theme dropdown in top-right corner of HTML report** (runtime switching)
- **Quick dark/light mode toggle button** (one-click switching between dark and light)
- Multiple built-in themes (light, dark, high-contrast, solarized, dracula)
- Dark mode support with proper color inversion
- Custom color palettes
- Font selection (system fonts + web-safe fonts)
- Layout density options (compact, comfortable, spacious)
- Logo/branding customization
- Export theme as reusable configuration
- Save theme preference to localStorage (persists across reports)

**Implementation**:
- CSS custom properties (variables) for theming
- JavaScript theme switcher in HTML report (no page reload)
- Theme loader in HTMLReporter
- Validate theme configurations
- Preserve accessibility in all themes (WCAG 2.1 AA)
- Add theme preview command: `agentready theme-preview dark`
- Embed all theme CSS in single HTML file (offline-capable)

**Related**: HTML report generation, user experience

**Notes**:
- All themes must maintain WCAG 2.1 AA contrast ratios
- Dark mode should invert appropriately, not just be dark
- Consider colorblind-friendly palettes (Viridis, ColorBrewer)
- Custom themes should be shareable (export/import)
- Could add theme gallery in documentation

---

### Fix Code Quality Issues from Code Review

**Priority**: P1 (High - Quality & Reliability)

**Description**: Address P1 issues discovered in code review that affect reliability, accuracy, and code quality.

**Issues to Fix**:

1. **TOCTOU (Time-of-Check-Time-of-Use) in File Operations**
   - **Location**: Multiple assessors (`documentation.py:46-50`, `documentation.py:174-191`)
   - **Problem**: Check if file exists, then read in separate operation - file could be deleted in between
   - **Impact**: Crashes instead of graceful degradation
   - **Fix**: Use try-except around file reads instead of existence checks
   ```python
   # BEFORE:
   if claude_md_path.exists():
       size = claude_md_path.stat().st_size

   # AFTER:
   try:
       with open(claude_md_path, "r") as f:
           size = len(f.read())
   except FileNotFoundError:
       return Finding(...status="fail"...)
   except OSError as e:
       return Finding.error(self.attribute, f"Could not read: {e}")
   ```

2. **Inaccurate Type Annotation Detection**
   - **Location**: `src/agentready/assessors/code_quality.py:98-102`
   - **Problem**: Regex-based detection has false positives (string literals, dict literals)
   - **Impact**: Inflated type annotation coverage scores
   - **Fix**: Use AST parsing instead of regex:
   ```python
   import ast
   tree = ast.parse(content)
   for node in ast.walk(tree):
       if isinstance(node, ast.FunctionDef):
           total_functions += 1
           has_annotations = (node.returns is not None or
                            any(arg.annotation for arg in node.args.args))
           if has_annotations:
               typed_functions += 1
   ```

3. **Assessment Validation Semantic Confusion**
   - **Location**: `src/agentready/models/assessment.py:54-59`
   - **Problem**: Field named `attributes_skipped` but includes `error` and `not_applicable` statuses
   - **Impact**: Confusing API, unclear semantics
   - **Fix**: Rename to `attributes_not_assessed` OR add separate counters

**Acceptance Criteria**:
- [ ] All file operations use try-except pattern
- [ ] Type annotation detection uses AST parsing
- [ ] Assessment model fields clearly named
- [ ] Tests added for TOCTOU edge cases
- [ ] Tests added for type annotation false positives
- [ ] Documentation updated

**Priority Justification**: These affect reliability and measurement accuracy - critical for a quality assessment tool.

**Related**: Testing improvements, code quality

---

### Improve Test Coverage and Edge Case Handling

**Priority**: P1 (High - Quality Assurance)

**Description**: Increase test coverage from 37% to >80% and add tests for critical edge cases discovered in code review.

**Critical Test Gaps**:

1. **Error Handling Paths** (Currently 0% coverage)
   - OSError, PermissionError in file operations
   - MissingToolError in assessors
   - Invalid repository paths
   - Malformed git repositories

2. **Edge Cases** (No tests)
   - Empty repositories
   - Binary files instead of text
   - Symlinks in repository
   - Very large repositories (>10k files)
   - Repositories with `test/` vs `tests/` directories

3. **Security Test Cases**
   - XSS in repository names, commit messages
   - Path traversal attempts
   - Malicious file names

4. **Scorer Edge Cases**
   - All attributes skipped (score should be 0.0)
   - Config weights don't sum to 1.0
   - Division by zero scenarios

**Implementation**:
```python
# tests/unit/test_edge_cases.py
def test_empty_repository(tmp_path):
    """Test assessment of completely empty repository."""
    # Create empty git repo
    repo = Repository(path=tmp_path, ...)
    scanner = Scanner(repo, config=None)
    assessment = scanner.scan(assessors)
    # Should not crash, should have valid score
    assert 0.0 <= assessment.overall_score <= 100.0

def test_permission_denied_file(tmp_path):
    """Test graceful handling of permission errors."""
    # Create unreadable file
    restricted = tmp_path / "CLAUDE.md"
    restricted.write_text("test")
    restricted.chmod(0o000)

    assessor = CLAUDEmdAssessor()
    finding = assessor.assess(Repository(...))
    assert finding.status == "error"
    assert "permission" in finding.error_message.lower()

def test_binary_file_as_readme(tmp_path):
    """Test handling of binary files."""
    readme = tmp_path / "README.md"
    readme.write_bytes(b"\x00\x01\x02\x03")

    assessor = READMEAssessor()
    finding = assessor.assess(Repository(...))
    # Should not crash
```

**Acceptance Criteria**:
- [ ] Test coverage increased to >80%
- [ ] All error handling paths tested
- [ ] Edge cases for empty/malformed repos covered
- [ ] Security test cases added
- [ ] Integration tests for complete workflows
- [ ] CI runs coverage report and fails <75%

**Priority Justification**: Quality assessment tool must be thoroughly tested. Current 37% coverage is unacceptable.

**Related**: CI/CD improvements, reliability

---

### Add Security & Quality Improvements from Code Review

**Priority**: P2 (Medium - Polish)

**Description**: Address P2 improvements from code review for better UX and robustness.

**Improvements**:

1. **Input Validation Warnings**
   - Warn when scanning sensitive directories (`/etc`, `/.ssh`, `/var`)
   - Confirm before scanning large repositories (>10k files)

2. **Scorer Semantic Clarity**
   - Document behavior when all attributes skipped (returns 0.0)
   - Consider returning `None` or special value for "not assessable"
   - Add explicit documentation of edge cases

3. **Content Security Policy Headers**
   - Add CSP to HTML reports for defense-in-depth
   - Prevent inline script execution
   - Whitelist only necessary sources

**Implementation**:
```python
# In CLI
sensitive_dirs = ['/etc', '/sys', '/proc', '/.ssh', '/var']
if any(str(repo_path).startswith(p) for p in sensitive_dirs):
    click.confirm(
        f"Warning: Scanning sensitive directory {repo_path}. Continue?",
        abort=True
    )

# In HTMLReporter
csp_header = (
    "<meta http-equiv='Content-Security-Policy' "
    "content=\"default-src 'self'; script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline'\">"
)
```

**Acceptance Criteria**:
- [ ] Warnings for sensitive directories
- [ ] CSP headers in HTML reports
- [ ] Scorer edge cases documented
- [ ] User guide updated with best practices

**Priority Justification**: UX polish and defense-in-depth, not critical bugs.

**Related**: User experience, security hardening

---

### Align Subcommand (Automated Remediation)

**Priority**: P1 (Critical)

**Description**: Implement `agentready align` subcommand that automatically fixes failing attributes by generating and applying changes to the repository.

**Vision**: One command to align your repository with best practices - automatically create missing files, configure tooling, and improve code quality.

**Core Command**:

```bash
# Align repository to best practices
agentready align .

# Preview changes without applying
agentready align . --dry-run

# Apply specific attributes only
agentready align . --attributes claude_md_file,precommit_hooks

# Create GitHub PR instead of direct changes
agentready align . --create-pr

# Interactive mode (confirm each change)
agentready align . --interactive
```

**Supported Fixes**:

1. **Template-Based Fixes** (Auto-applicable):
   - `claude_md_file`: Generate CLAUDE.md from repository analysis
   - `gitignore_completeness`: Add missing patterns to .gitignore
   - `precommit_hooks`: Create .pre-commit-config.yaml with language-specific hooks
   - `readme_structure`: Scaffold missing README sections
   - `lock_files`: Generate lock files (package-lock.json, requirements.txt, etc.)
   - `issue_pr_templates`: Create .github/ISSUE_TEMPLATE and PULL_REQUEST_TEMPLATE
   - `conventional_commits`: Add commitlint configuration

2. **Command-Based Fixes** (Execute commands):
   - `lock_files`: Run `npm install`, `poetry lock`, `go mod tidy`
   - `precommit_hooks`: Run `pre-commit install`
   - `dependency_freshness`: Run `npm update`, `pip install --upgrade`

3. **AI-Powered Fixes** (Require LLM, optional):
   - `type_annotations`: Add type hints to Python functions
   - `inline_documentation`: Generate docstrings from function signatures
   - `cyclomatic_complexity`: Refactor high-complexity functions
   - `file_size_limits`: Split large files into smaller modules

**Workflow**:

```bash
# User runs alignment
$ agentready align . --dry-run

AgentReady Alignment Preview
============================

Repository: /Users/jeder/my-project
Current Score: 62.4/100 (Silver)
Projected Score: 84.7/100 (Gold) 🎯

Changes to be applied:

  ✅ claude_md_file (10 points)
     CREATE CLAUDE.md (1.2 KB)

  ✅ precommit_hooks (3 points)
     CREATE .pre-commit-config.yaml (845 bytes)
     RUN pre-commit install

  ✅ gitignore_completeness (3 points)
     MODIFY .gitignore (+15 patterns)

  ⚠️  type_annotations (10 points) - requires AI
     MODIFY 23 Python files (add type hints)
     Use --ai to enable AI-powered fixes

Total: 3 automatic fixes, 1 AI fix available
Apply changes? [y/N]
```

**Implementation**:

```python
# src/agentready/fixers/base.py
class BaseFixer(ABC):
    """Base class for attribute fixers."""

    @abstractmethod
    def can_fix(self, finding: Finding) -> bool:
        """Check if this fixer can fix the finding."""
        pass

    @abstractmethod
    def generate_fix(self, repository: Repository, finding: Finding) -> Fix:
        """Generate fix for the finding."""
        pass

# src/agentready/fixers/template_fixer.py
class TemplateFixer(BaseFixer):
    """Fixer that generates files from templates."""

    def generate_fix(self, repository: Repository, finding: Finding) -> Fix:
        template = self.load_template(finding.attribute.id)
        content = self.render_template(template, repository)
        return FileCreationFix(path="CLAUDE.md", content=content)

# src/agentready/cli/align.py
@cli.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--create-pr", is_flag=True, help="Create GitHub PR instead of direct changes")
@click.option("--interactive", is_flag=True, help="Confirm each change")
@click.option("--attributes", help="Comma-separated attribute IDs to fix")
@click.option("--ai", is_flag=True, help="Enable AI-powered fixes (requires API key)")
def align(repository, dry_run, create_pr, interactive, attributes, ai):
    """Align repository with best practices by applying automatic fixes."""

    # Run assessment first
    assessment = run_assessment(repository)

    # Identify fixable failures
    failures = [f for f in assessment.findings if f.status == "fail"]
    fixable = identify_fixable_failures(failures, enable_ai=ai)

    # Generate fixes
    fixes = [fixer.generate_fix(repo, finding) for finding in fixable]

    # Preview changes
    show_fix_preview(fixes, assessment.overall_score, projected_score)

    if dry_run:
        return

    if interactive and not confirm_each_fix(fixes):
        return

    # Apply fixes
    if create_pr:
        create_github_pr_with_fixes(fixes)
    else:
        apply_fixes(fixes)

    # Re-run assessment to show improvement
    new_assessment = run_assessment(repository)
    show_improvement(assessment.overall_score, new_assessment.overall_score)
```

**Fix Types**:

```python
class Fix(ABC):
    """Base class for fixes."""
    attribute_id: str
    description: str

class FileCreationFix(Fix):
    """Create a new file."""
    path: Path
    content: str

class FileModificationFix(Fix):
    """Modify existing file."""
    path: Path
    changes: List[TextChange]

class CommandFix(Fix):
    """Execute command."""
    command: str
    working_dir: Path

class MultiStepFix(Fix):
    """Combination of multiple fixes."""
    steps: List[Fix]
```

**GitHub PR Integration**:

```bash
# Create PR with fixes
$ agentready align . --create-pr

Creating fix branch: agentready-align-20251121
Applying 3 fixes...
  ✅ Created CLAUDE.md
  ✅ Created .pre-commit-config.yaml
  ✅ Modified .gitignore

Committing changes...
Pushing to origin...

Created PR: https://github.com/redhat/my-project/pull/42
  Title: "Improve AgentReady score from 62.4 to 84.7 (Silver → Gold)"
  Score improvement: +22.3 points
  Attributes fixed: 3
```

**Configuration**:

```yaml
# .agentready-config.yaml
align:
  enabled: true

  auto_fix:
    # Attributes to automatically fix without confirmation
    - claude_md_file
    - gitignore_completeness
    - precommit_hooks

  confirm_before_fix:
    # Attributes requiring confirmation
    - type_annotations
    - cyclomatic_complexity

  never_fix:
    # Attributes to skip (user will fix manually)
    - container_setup
    - openapi_specs

  ai_fixes:
    enabled: false  # Require --ai flag
    provider: "anthropic"  # or "openai"
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 4096
```

**Use Cases**:

**Use Case 1: New Repository Setup**
```bash
# Clone new project
git clone github.com/redhat/new-project
cd new-project

# Align to best practices
agentready align . --interactive

# Review and commit changes
git add .
git commit -m "chore: Align repository with AgentReady best practices"
```

**Use Case 2: Continuous Improvement**
```bash
# Weekly CI job to check and create alignment PRs
agentready align . --create-pr --dry-run
# If score < threshold, create PR automatically
```

**Use Case 3: Pre-commit Hook**
```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: agentready-align
      name: AgentReady Alignment Check
      entry: agentready align --dry-run
      language: system
      pass_filenames: false
```

**Safety Features**:

- **Dry-run by default** for destructive operations
- **Git worktree** for isolated changes (optional)
- **Backup creation** before modifying files
- **Rollback support** if fixes fail
- **Validation** of generated files before writing
- **Interactive confirmation** for AI-powered fixes

**Related**: Automated remediation, repository improvement, onboarding

**Notes**:
- Start with template-based fixes (highest ROI, lowest risk)
- AI-powered fixes require API key and user consent
- Some attributes cannot be automatically fixed (requires human judgment)
- Consider integration with `git stash` for safety
- Could generate shell script of changes for manual review
- Align with Red Hat's AI-assisted development workflow

---

### Interactive Dashboard with Automated Remediation

**Priority**: P2 (High Value)

**Description**: Transform the static HTML report into an interactive dashboard that enables one-click remediation via automated GitHub issue creation and draft PR generation.

**Vision**: "How to Align Your Repo with Best Practices" - Click a button → Open GitHub issue with draft PR containing fixes.

**Core Features**:

1. **Interactive Dashboard Mode**
   - Real-time assessment (WebSocket updates)
   - Live filtering and sorting (already have this)
   - Action buttons on each failing attribute
   - Progress tracking across multiple runs
   - Historical trend visualization

2. **One-Click Remediation Actions**
   - "Fix This" button on each failing attribute
   - Generates GitHub issue automatically
   - Creates draft PR with proposed changes
   - Links issue to PR
   - Assigns to repository owner/team

3. **Automated Fix Generation**
   - Template-based fixes for common issues:
     - Missing .gitignore → Generate language-specific .gitignore
     - No CLAUDE.md → Generate template with repo analysis
     - Missing pre-commit hooks → Add .pre-commit-config.yaml
     - No lock files → Generate appropriate lock file
     - Missing README sections → Scaffold missing sections
   - AI-powered fixes for complex issues:
     - Refactor high-complexity functions
     - Add type annotations to functions
     - Generate docstrings from function signatures
     - Split large files

4. **GitHub Integration**
   - OAuth authentication with GitHub
   - gh CLI integration for seamless workflow
   - Create issues via GitHub API
   - Create draft PRs via GitHub API
   - Auto-label issues (e.g., `agentready`, `automated-fix`, `tier-1-essential`)
   - Link to AgentReady assessment report

**Technical Architecture**:

```yaml
# New components needed:

Backend (Optional - could be fully client-side with gh CLI):
  - GitHub OAuth app for authentication
  - Issue/PR template generator
  - Fix generator service (template-based + AI-powered)
  - Assessment history tracker

Frontend (Enhanced HTML report):
  - Action buttons with loading states
  - GitHub auth flow UI
  - Progress indicators
  - Toast notifications for actions
  - Modal dialogs for fix preview

CLI Extensions:
  - agentready dashboard .  # Launch local web server
  - agentready fix <attribute-id>  # Generate fix for specific attribute
  - agentready create-issue <attribute-id>  # Create GitHub issue
  - agentready create-pr <attribute-id>  # Create draft PR
```

**Use Cases**:

**Use Case 1: Quick Fixes**
```bash
# User runs assessment
agentready assess . --dashboard

# Opens dashboard in browser at http://localhost:8000
# User clicks "Fix This" on "Missing CLAUDE.md"
# → Creates issue: "Add CLAUDE.md configuration file"
# → Creates draft PR with generated CLAUDE.md template
# → PR includes: project analysis, detected languages, suggested structure
```

**Use Case 2: Batch Remediation**
```bash
# Dashboard shows all failures
# User selects multiple attributes
# Clicks "Fix All Selected"
# → Creates single issue: "Improve AgentReady Score from Silver to Gold"
# → Creates draft PR with all fixes
# → PR description includes before/after score projection
```

**Use Case 3: CI/CD Integration**
```bash
# GitHub Action runs assessment
# Posts comment on PR with assessment results
# Includes links to create remediation issues
# Can auto-create draft PR for improvements
```

**Implementation Approach**:

**Phase 1: Client-Side with gh CLI** (Simplest, no backend needed)
- Use JavaScript in HTML report to call gh CLI via local proxy
- Generate fix files locally
- Use `gh issue create` and `gh pr create`
- Works for users with gh CLI installed

**Phase 2: Dashboard Server** (Enhanced UX)
- Flask/FastAPI server serving dashboard
- WebSocket for live updates
- GitHub OAuth for authentication
- Background workers for fix generation

**Phase 3: Cloud Service** (SaaS offering)
- Hosted dashboard at agentready.dev
- GitHub App installation
- Webhook integration for continuous monitoring
- Team collaboration features

**Fix Templates by Attribute**:

```yaml
claude_md_file:
  type: template
  generates:
    - file: CLAUDE.md
      content: |
        # {repository_name}

        ## Overview
        {auto_generated_description}

        ## Architecture
        {detected_patterns}

        ## Development
        {build_commands}

lock_files:
  type: command
  commands:
    - condition: has_package_json
      run: npm install
    - condition: has_pyproject_toml
      run: poetry lock || pip freeze > requirements.txt

precommit_hooks:
  type: template
  generates:
    - file: .pre-commit-config.yaml
      content: {language_specific_hooks}

readme_structure:
  type: enhancement
  modifies: README.md
  adds_sections:
    - Installation
    - Usage
    - Development
    - Contributing

type_annotations:
  type: ai_powered
  uses: ast_analysis + llm
  modifies: "*.py"
  adds: type_hints
```

**Dashboard vs Report Decision**:

**Keep Both**:
- Static reports for CI/CD, documentation, archiving
- Dashboard for interactive development workflow
- Reports can link to dashboard for remediation
- Dashboard can export static reports

**Benefits of Dashboard**:
- ✅ Interactive remediation workflow
- ✅ Live assessment updates
- ✅ Progress tracking over time
- ✅ Team collaboration (comments, assignments)
- ✅ Automated fix preview before applying
- ✅ Integration with existing tools (GitHub, IDEs)

**Challenges**:
- Authentication complexity (GitHub OAuth)
- Fix generation quality (need good templates + AI)
- PR review overhead (lots of automated PRs)
- Maintaining fix templates as best practices evolve

**Recommended Approach**:

1. **Start with enhanced static report**:
   - Add "Create Issue" buttons that generate gh CLI commands
   - Users copy/paste commands to create issues
   - Include fix templates in issue descriptions

2. **Add local dashboard** (Phase 2):
   - Flask server with WebSocket updates
   - GitHub integration via gh CLI
   - Generate fixes, preview diffs, create PRs

3. **Consider hosted service** (Phase 3+):
   - If adoption is high
   - SaaS model for teams
   - Continuous monitoring and recommendations

**Related**: GitHub integration, automation, remediation, UX

**Notes**:
- This is a MAJOR feature that could become a standalone product
- Consider MVP: "Copy this gh command" buttons in HTML report
- AI-powered fix generation requires careful validation
- Some fixes (like refactoring) need human review
- Could integrate with existing tools (Dependabot, Renovate)
- May want to partner with GitHub for official integration

---

### GitHub App Integration (Badge & Status Checks)

**Priority**: P2 (High Value)

**Description**: Create a GitHub App that provides badge integration, PR status checks, and automated assessment comments to help Red Hat engineering teams track and improve repository quality.

**Core Features**:

1. **Repository Badge**
   - Shields.io-compatible SVG badge showing certification level
   - Endpoint: `https://agentready.redhat.com/badge/{owner}/{repo}.svg`
   - Dynamic color based on certification (Platinum=purple, Gold=yellow, Silver=silver, Bronze=brown)
   - Include score: "AgentReady: 85.2 (Gold)"
   - Click badge to view latest assessment report

2. **GitHub Actions Integration**
   - Create official `agentready/assess-action` GitHub Action
   - Run assessment on PR events (opened, synchronized, reopened)
   - Run assessment on push to main/master
   - Support custom triggers via workflow_dispatch

3. **PR Status Checks**
   - Use GitHub Commit Status API to report assessment results
   - Set check status: success (>90), warning (75-89), failure (<75)
   - Configurable thresholds via `.agentready-config.yaml`
   - Block PR merge if score below threshold (optional)
   - Link to detailed HTML report in check details

4. **PR Comments**
   - Automated bot comments on PRs with assessment summary
   - Show score delta: "Score changed: 72.4 → 78.3 (+5.9)"
   - List new failures and fixes
   - Collapsible sections for full findings
   - Trend chart showing last 10 assessments (ASCII or embedded image)
   - Include remediation suggestions for new failures

**Technical Implementation**:

**Phase 1: GitHub Actions Integration**
```yaml
# .github/workflows/agentready.yml
name: AgentReady Assessment
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, master]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: agentready/assess-action@v1
        with:
          threshold: 75
          post-comment: true
          update-status: true
```

**Phase 2: Badge Service**
```python
# FastAPI endpoint for badge generation
@app.get("/badge/{owner}/{repo}.svg")
async def get_badge(owner: str, repo: str):
    # Fetch latest assessment from GitHub Actions artifacts
    # Or run quick assessment on-demand
    score, level = get_latest_assessment(owner, repo)
    color = LEVEL_COLORS[level]
    return SVGResponse(generate_badge(score, level, color))
```

**Phase 3: GitHub App**
- App permissions: Contents (read), Checks (write), Pull requests (write)
- Webhook events: push, pull_request
- Installed via GitHub Marketplace (Red Hat internal)
- Dashboard at agentready.redhat.com showing:
  - Repository list with scores
  - Historical trends
  - Organization-wide statistics
  - Top repositories by improvement

**Integration Points**:

1. **GitHub Actions Artifacts**
   - Store assessment reports as workflow artifacts
   - Keep last 30 days of reports for trend analysis
   - Generate downloadable HTML/JSON/Markdown reports

2. **GitHub Status API**
   ```python
   POST /repos/{owner}/{repo}/statuses/{commit_sha}
   {
     "state": "success",  # or "pending", "failure", "error"
     "target_url": "https://agentready.redhat.com/reports/{run_id}",
     "description": "AgentReady: 85.2 (Gold)",
     "context": "agentready/assessment"
   }
   ```

3. **GitHub Checks API** (preferred over Status API)
   ```python
   POST /repos/{owner}/{repo}/check-runs
   {
     "name": "AgentReady Assessment",
     "status": "completed",
     "conclusion": "success",
     "output": {
       "title": "Score: 85.2/100 (Gold)",
       "summary": "Passed 20/25 attributes",
       "text": "Detailed findings..."
     }
   }
   ```

**Use Cases**:

**Use Case 1: Add Badge to README**
```markdown
# My Project

[![AgentReady](https://agentready.redhat.com/badge/redhat/my-project.svg)](https://agentready.redhat.com/reports/redhat/my-project)
```

**Use Case 2: Enforce Quality Gates**
```yaml
# .agentready-config.yaml
github:
  status_checks:
    enabled: true
    min_score: 75  # Block merge if score < 75
    require_improvement: true  # Block if score decreased
```

**Use Case 3: Track Organization Progress**
- Dashboard shows all repos in Red Hat org
- Filter by team, language, certification level
- Identify repos needing attention
- Celebrate improvements (score increases)

**Configuration**:

```yaml
# .agentready-config.yaml
github:
  badge:
    enabled: true
    style: flat-square  # or flat, plastic, for-the-badge
    label: "AgentReady"

  actions:
    enabled: true
    trigger_on: [pull_request, push]
    post_comment: true
    update_status: true
    upload_artifacts: true

  status_checks:
    enabled: true
    min_score: 75
    require_improvement: false

  comments:
    enabled: true
    show_delta: true
    show_trend: true
    collapse_details: true
```

**Implementation Checklist**:

- [ ] Create `agentready/assess-action` GitHub Action
- [ ] Implement badge generation service
- [ ] Add GitHub Status API integration
- [ ] Add GitHub Checks API integration
- [ ] Implement PR comment generation
- [ ] Add score delta calculation
- [ ] Create assessment artifact storage
- [ ] Build organization dashboard
- [ ] Add Red Hat SSO authentication
- [ ] Deploy to Red Hat infrastructure
- [ ] Create documentation for Red Hat teams
- [ ] Add to Red Hat developer onboarding

**Related**: CI/CD integration, automation, visibility, quality gates

**Notes**:
- Focus on internal Red Hat adoption first
- Badge service could be hosted on Red Hat infrastructure
- Dashboard should integrate with Red Hat IdM for authentication
- Consider integration with Red Hat's existing code quality tools
- GitHub App should be installable via Red Hat GitHub Enterprise
- All data stays within Red Hat infrastructure (no external services)
- Align with Red Hat's OpenShift AI strategy for agentic development
- Could become part of Red Hat's AI-assisted development workflow

---

### Documentation Source Truth and Cascade System

**Priority**: P2 (Medium - Developer Experience)

**Description**: Implement a system to ensure documentation stays synchronized when source content changes, with automatic cascade updates from authoritative sources to derived documentation.

**Problem**: When substantial changes are made to source documentation (like research reports, specifications, or CLAUDE.md), there's currently no mechanism to ensure those changes propagate to derived documentation (GitHub Pages, API docs, tutorials, etc.). This leads to documentation drift and inconsistency.

**Requirements**:

1. **Source-of-Truth Designation**
   - Designate authoritative source files (contracts/*, specs/*, CLAUDE.md, research reports)
   - Mark derived documentation files that depend on sources
   - Document source → derived relationships explicitly

2. **Change Detection**
   - Track content changes in source files via git hooks or CI
   - Identify which derived docs are affected by source changes
   - Calculate "documentation drift score" (how out of sync derived docs are)

3. **Automatic Cascade Updates**
   - Trigger documentation regeneration when sources change
   - Update affected GitHub Pages content
   - Regenerate API documentation if models change
   - Update code examples if interfaces change
   - Refresh tutorial content if workflows change

4. **Validation & Consistency**
   - Validate that derived docs accurately reflect sources
   - Check for broken cross-references after updates
   - Ensure code examples still compile/run
   - Verify attribute definitions match research report

**Implementation Approach**:

```yaml
# .agentready/doc-sources.yaml
documentation_sources:
  # Source of truth files
  sources:
    - path: contracts/assessment-schema.json
      type: json_schema
      affects:
        - docs/api-reference.md
        - README.md (Data Models section)

    - path: agent-ready-codebase-attributes.md
      type: research_report
      affects:
        - docs/attributes.md
        - docs/index.md (Features section)
        - README.md (Overview)

    - path: CLAUDE.md
      type: project_guide
      affects:
        - docs/developer-guide.md
        - docs/user-guide.md

    - path: specs/plan.md
      type: design_spec
      affects:
        - docs/developer-guide.md (Architecture)
        - docs/api-reference.md

  # Cascade rules
  cascade_rules:
    - source: contracts/assessment-schema.json
      trigger: schema_version_change
      actions:
        - regenerate_api_docs
        - update_model_documentation
        - validate_code_examples

    - source: agent-ready-codebase-attributes.md
      trigger: attribute_definition_change
      actions:
        - update_attributes_page
        - regenerate_tier_summaries
        - update_scoring_documentation
```

**CLI Commands**:

```bash
# Check for documentation drift
agentready docs check-drift

# Output:
# Documentation Drift Report
# =========================
#
# ⚠️  agent-ready-codebase-attributes.md changed (5 days ago)
#     Affected: docs/attributes.md (not updated)
#     Affected: docs/index.md (not updated)
#
# ⚠️  contracts/assessment-schema.json changed (2 days ago)
#     Affected: docs/api-reference.md (not updated)
#
# Drift Score: 45/100 (needs attention)

# Update derived docs from sources
agentready docs cascade-update

# Output:
# Cascading Documentation Updates
# ================================
#
# ✓ Updated docs/attributes.md from agent-ready-codebase-attributes.md
# ✓ Updated docs/index.md from agent-ready-codebase-attributes.md
# ✓ Regenerated docs/api-reference.md from contracts/assessment-schema.json
# ✓ Validated all code examples
#
# 3 files updated, 0 errors

# Preview what would be updated (dry-run)
agentready docs cascade-update --dry-run

# Update specific derived doc
agentready docs update docs/attributes.md
```

**GitHub Actions Integration**:

```yaml
# .github/workflows/doc-cascade.yml
name: Documentation Cascade

on:
  push:
    paths:
      - 'contracts/**'
      - 'specs/**'
      - 'CLAUDE.md'
      - 'agent-ready-codebase-attributes.md'

jobs:
  cascade-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check Documentation Drift
        run: agentready docs check-drift --fail-threshold 30

      - name: Cascade Updates
        run: agentready docs cascade-update

      - name: Create PR if Changes
        if: changes detected
        uses: peter-evans/create-pull-request@v5
        with:
          title: "docs: Cascade updates from source changes"
          body: |
            Automated documentation updates triggered by source changes.

            This PR contains documentation updates cascaded from:
            - Contract/schema changes
            - Research report updates
            - Specification changes
```

**Pre-commit Hook Integration**:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: doc-drift-check
      name: Check Documentation Drift
      entry: agentready docs check-drift --fail-threshold 50
      language: system
      pass_filenames: false
      # Warns if drift > 50%, fails if drift > 80%
```

**Cascade Update Strategies**:

1. **Template-Based Regeneration**
   - Keep templates for derived docs
   - Re-render templates when sources change
   - Example: docs/attributes.md regenerated from research report + template

2. **Section Replacement**
   - Identify sections in derived docs sourced from elsewhere
   - Replace only those sections, preserve custom content
   - Use HTML comments or YAML frontmatter to mark auto-generated sections

3. **Code Example Validation**
   - Extract code examples from derived docs
   - Validate against current codebase/schemas
   - Update if broken, flag if unfixable

4. **Link Validation**
   - Check all cross-references between docs
   - Update broken links after renames/moves
   - Report dead external links

**Marking Auto-Generated Sections**:

```markdown
<!-- BEGIN AUTO-GENERATED: source=agent-ready-codebase-attributes.md section=tier-1-attributes -->

## Tier 1 Attributes (Essential)

These are the foundational attributes...

[Content auto-generated from research report]

<!-- END AUTO-GENERATED -->

<!-- Custom content below is preserved during cascade updates -->

## Additional Notes

These are custom notes that won't be overwritten...
```

**Use Cases**:

**Use Case 1: Research Report Updated**
- Researcher adds new attribute to research report
- Pre-commit hook detects drift
- Developer runs `agentready docs cascade-update`
- GitHub Pages attributes page automatically updated
- Homepage feature count updated
- API reference regenerated

**Use Case 2: Schema Version Bump**
- Assessment schema updated (v1.0 → v2.0)
- CI detects schema change
- Automatically creates PR with:
  - Updated API reference
  - Updated data model documentation
  - Validated code examples
  - Migration guide

**Use Case 3: Spec Changes During Development**
- Developer updates plan.md with architecture changes
- Local pre-commit hook warns of documentation drift
- Developer runs cascade update
- Developer guide automatically synchronized

**Acceptance Criteria**:
- [ ] Source-of-truth files explicitly designated
- [ ] Drift detection algorithm implemented
- [ ] Cascade update command working for all doc types
- [ ] GitHub Actions workflow for automatic cascade
- [ ] Pre-commit hook warns of high drift
- [ ] Documentation explains source/derived relationships
- [ ] Preserves custom content in derived docs
- [ ] Validates code examples after updates

**Priority Justification**:
- Currently experiencing documentation drift (GitHub Pages may not match CLAUDE.md)
- Will worsen as project grows without automation
- Essential for maintaining documentation quality
- Aligns with "agent-ready" principles (machine-readable sources of truth)

**Related**: Documentation maintenance, automation, consistency, DRY principle

**Notes**:
- Start with simple template-based regeneration
- Expand to intelligent section replacement
- Consider using LLMs to help with content transformation
- Could become a reusable tool for other projects
- Document the documentation architecture (meta!)

---

## Backlog Metadata

**Created**: 2025-11-21
**Last Updated**: 2025-11-21
**Total Items**: 15 (11 original + 3 from code review + 1 documentation cascade)

## Priority Summary

- **P0 (Critical)**: 4 items - Security/Logic Bugs (FIX FIRST!), Bootstrap Command, Report Header Metadata, HTML Design Improvements
- **P1 (Critical)**: 4 items - Code Quality Fixes, Test Coverage Improvements, Align Subcommand
- **P2 (High Value)**: 3 items - Security Polish, Interactive Dashboard, GitHub App Integration
- **P3 (Important)**: 2 items - Report Schema Versioning, AgentReady Repository Agent
- **P4 (Enhancement)**: 3 items - Research Report Utility, Repomix Integration, Customizable Themes
