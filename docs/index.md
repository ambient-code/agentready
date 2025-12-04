---
layout: home
title: Home
---

<div class="announcement-banner">
  <span class="announcement-icon">🚀</span>
  <span class="announcement-text">New: <a href="https://github.com/ambient-code/agentready#cli-reference">Enhanced CLI Reference</a> - Complete command documentation with interactive examples and visual guides</span>
</div>

# AgentReady

**Build and maintain agent-ready codebases with automated infrastructure generation and continuous quality assessment.**

<div class="hero">
  <p class="hero-tagline">One command to agent-ready infrastructure. Transform your repository with automated GitHub setup, pre-commit hooks, CI/CD workflows, and continuous quality tracking.</p>
  <div class="hero-buttons">
    <a href="user-guide.html#bootstrap-your-repository" class="button button-primary">Bootstrap Your Repo</a>
    <a href="user-guide.html#running-assessments" class="button button-secondary">Run Assessment</a>
    <a href="leaderboard.html" class="button button-tertiary">🏆 Leaderboard</a>
  </div>
</div>

## Why AgentReady?

AI-assisted development tools like Claude Code, GitHub Copilot, and Cursor AI work best with well-structured, documented codebases. AgentReady **builds the infrastructure** you need and **continuously assesses** your repository across **25 research-backed attributes** to ensure lasting AI effectiveness.

### Two Powerful Modes

<div class="feature-grid">
  <div class="feature">
    <h3>⚡ Bootstrap (Automated)</h3>
    <p><strong>One command to complete infrastructure.</strong> Generates GitHub Actions workflows, pre-commit hooks, issue/PR templates, Dependabot config, and development standards tailored to your language.</p>
    <p><strong>When to use:</strong> New projects, repositories missing automation, or when you want instant best practices.</p>
  </div>
  <div class="feature">
    <h3>📊 Assess (Diagnostic)</h3>
    <p><strong>Deep analysis of 25 attributes.</strong> Evaluates documentation, code quality, testing, structure, and security. Provides actionable remediation guidance with specific tools and commands.</p>
    <p><strong>When to use:</strong> Understanding current state, tracking improvements over time, or validating manual changes.</p>
  </div>
</div>

## Key Features

<div class="feature-grid">
  <div class="feature">
    <h3>🤖 Automated Infrastructure</h3>
    <p>Bootstrap generates complete GitHub setup: Actions workflows, issue/PR templates, pre-commit hooks, Dependabot config, and security scanning—all language-aware.</p>
  </div>
  <div class="feature">
    <h3>🎯 Language-Specific</h3>
    <p>Auto-detects your primary language (Python, JavaScript, Go) and generates appropriate workflows, linters, and test configurations.</p>
  </div>
  <div class="feature">
    <h3>📈 Continuous Assessment</h3>
    <p>Generated GitHub Actions run AgentReady on every PR, posting results as comments. Track improvements over time with Markdown reports.</p>
  </div>
  <div class="feature">
    <h3>🏆 Certification Levels</h3>
    <p>Platinum, Gold, Silver, Bronze levels validate your codebase quality. Bootstrap helps you achieve Gold (75+) immediately.</p>
  </div>
  <div class="feature">
    <h3>⚡ One Command Setup</h3>
    <p>From zero to production-ready infrastructure in seconds. Review generated files with --dry-run before committing.</p>
  </div>
  <div class="feature">
    <h3>🔬 Research-Backed</h3>
    <p>Every generated file and assessed attribute is backed by 50+ citations from Anthropic, Microsoft, Google, and academic research.</p>
  </div>
</div>

## Quick Start

### Bootstrap-First Workflow (Recommended)

```bash
# Install AgentReady
pip install agentready

# Bootstrap your repository (generates all infrastructure)
cd /path/to/your/repo
agentready bootstrap .

# Review generated files
ls -la .github/workflows/
ls -la .github/ISSUE_TEMPLATE/
cat .pre-commit-config.yaml

# Commit and push
git add .
git commit -m "build: Bootstrap agent-ready infrastructure"
git push

# Assessment runs automatically on next PR!
```

**What you get in <60 seconds:**

- ✅ GitHub Actions workflows (tests, security, AgentReady assessment)
- ✅ Pre-commit hooks (formatters, linters, language-specific)
- ✅ Issue & PR templates (bug reports, feature requests, CODEOWNERS)
- ✅ Dependabot automation (weekly dependency updates)
- ✅ Contributing guidelines and Code of Conduct
- ✅ Automatic AgentReady assessment on every PR

### Manual Assessment Workflow

```bash
# Or run one-time assessment without infrastructure changes
agentready assess .

# View interactive HTML report
open .agentready/report-latest.html
```

**Assessment output:**

- Overall score and certification level (Platinum/Gold/Silver/Bronze)
- Detailed findings for all 25 attributes
- Specific remediation steps with tools and examples
- Three report formats (HTML, Markdown, JSON)

[Read the complete user guide →](user-guide.html)

## CLI Reference

AgentReady provides a comprehensive CLI with multiple commands for different workflows:

```
Usage: agentready [OPTIONS] COMMAND [ARGS]...

  AgentReady Repository Scorer - Assess repositories for AI-assisted
  development.

  Evaluates repositories against 25 evidence-based attributes and generates
  comprehensive reports with scores, findings, and remediation guidance.

Options:
  --version  Show version information
  --help     Show this message and exit.

Commands:
  align             Align repository with best practices by applying fixes
  assess            Assess a repository against agent-ready criteria
  assess-batch      Assess multiple repositories in a batch operation
  bootstrap         Bootstrap repository with GitHub infrastructure
  demo              Run an automated demonstration of AgentReady
  experiment        SWE-bench experiment commands
  extract-skills    Extract reusable patterns and generate Claude Code skills
  generate-config   Generate example configuration file
  learn             Extract reusable patterns and generate skills (alias)
  migrate-report    Migrate assessment report to different schema version
  repomix-generate  Generate Repomix repository context for AI consumption
  research          Manage and validate research reports
  research-version  Show bundled research report version
  submit            Submit assessment results to AgentReady leaderboard
  validate-report   Validate assessment report against schema version
```

### Core Commands

<div class="command-grid">
  <div class="command-box">
    <h4>🚀 <a href="user-guide.html#bootstrap-your-repository">bootstrap</a></h4>
    <p>One-command infrastructure generation. Creates GitHub Actions, pre-commit hooks, issue/PR templates, and more.</p>
    <code>agentready bootstrap .</code>
  </div>

  <div class="command-box">
    <h4>🔧 <a href="user-guide.html#align-command">align</a></h4>
    <p>Automated remediation. Applies fixes to improve your score (create CLAUDE.md, add pre-commit hooks, update .gitignore).</p>
    <code>agentready align --dry-run .</code>
  </div>

  <div class="command-box">
    <h4>📊 <a href="user-guide.html#running-assessments">assess</a></h4>
    <p>Deep analysis of 25 attributes. Generates HTML, Markdown, and JSON reports with remediation guidance.</p>
    <code>agentready assess .</code>
  </div>

  <div class="command-box">
    <h4>🏆 <a href="leaderboard.html">submit</a></h4>
    <p>Submit your score to the public leaderboard. Track improvements and compare with other repositories.</p>
    <code>agentready submit</code>
  </div>
</div>

### Specialized Commands

- **`assess-batch`** - Assess multiple repositories in parallel ([batch documentation →](user-guide.html#batch-assessment))
- **`demo`** - Interactive demonstration mode showing AgentReady in action
- **`extract-skills`/`learn`** - Generate Claude Code skills from repository patterns
- **`repomix-generate`** - Create AI-optimized repository context files
- **`experiment`** - Run SWE-bench validation studies ([experiments →](developer-guide.html#experiments))
- **`research`** - Manage research report versions and validation
- **`migrate-report`/`validate-report`** - Schema management and migration tools

[View detailed command documentation →](user-guide.html#command-reference)

## Certification Levels

AgentReady scores repositories on a 0-100 scale with tier-weighted attributes:

<div class="certification-ladder">
  <div class="cert-level platinum">
    <div class="cert-badge">🏆 Platinum</div>
    <div class="cert-range">90-100</div>
    <div class="cert-desc">Exemplary agent-ready codebase</div>
  </div>
  <div class="cert-level gold">
    <div class="cert-badge">🥇 Gold</div>
    <div class="cert-range">75-89</div>
    <div class="cert-desc">Highly optimized for AI agents</div>
  </div>
  <div class="cert-level silver">
    <div class="cert-badge">🥈 Silver</div>
    <div class="cert-range">60-74</div>
    <div class="cert-desc">Well-suited for AI development</div>
  </div>
  <div class="cert-level bronze">
    <div class="cert-badge">🥉 Bronze</div>
    <div class="cert-range">40-59</div>
    <div class="cert-desc">Basic agent compatibility</div>
  </div>
  <div class="cert-level needs-improvement">
    <div class="cert-badge">📈 Needs Improvement</div>
    <div class="cert-range">0-39</div>
    <div class="cert-desc">Significant friction for AI agents</div>
  </div>
</div>

**AgentReady itself scores 80.0/100 (Gold)** — see our [self-assessment report](examples.html#agentready-self-assessment).

## What Gets Assessed?

AgentReady evaluates 25 attributes organized into four weighted tiers:

### Tier 1: Essential (50% of score)

The fundamentals that enable basic AI agent functionality:

- **CLAUDE.md File** — Project context for AI agents
- **README Structure** — Clear documentation entry point
- **Type Annotations** — Static typing for better code understanding
- **Standard Project Layout** — Predictable directory structure
- **Lock Files** — Reproducible dependency management

### Tier 2: Critical (30% of score)

Major quality improvements and safety nets:

- **Test Coverage** — Confidence for AI-assisted refactoring
- **Pre-commit Hooks** — Automated quality enforcement
- **Conventional Commits** — Structured git history
- **Gitignore Completeness** — Clean repository navigation
- **One-Command Setup** — Easy environment reproduction

### Tier 3: Important (15% of score)

Significant improvements in specific areas:

- **Cyclomatic Complexity** — Code comprehension metrics
- **Structured Logging** — Machine-parseable debugging
- **API Documentation** — OpenAPI/GraphQL specifications
- **Architecture Decision Records** — Historical design context
- **Semantic Naming** — Clear, descriptive identifiers

### Tier 4: Advanced (5% of score)

Refinement and optimization:

- **Security Scanning** — Automated vulnerability detection
- **Performance Benchmarks** — Regression tracking
- **Code Smell Elimination** — Quality baseline maintenance
- **PR/Issue Templates** — Consistent contribution workflow
- **Container Setup** — Portable development environments

[View complete attribute reference →](attributes.html)

## Report Formats

AgentReady generates three complementary report formats:

### Interactive HTML Report

- Color-coded findings with visual score indicators
- Search, filter, and sort capabilities
- Collapsible sections for detailed analysis
- Works offline (no CDN dependencies)
- **Use case**: Share with stakeholders, detailed exploration

### Version-Control Markdown

- GitHub-Flavored Markdown with tables and emojis
- Git-diffable format for tracking progress
- Certification ladder and next steps
- **Use case**: Commit to repository, track improvements over time

### Machine-Readable JSON

- Complete assessment data structure
- Timestamps and metadata
- Structured findings with evidence
- **Use case**: CI/CD integration, programmatic analysis

[See example reports →](examples.html)

## Evidence-Based Research

All 25 attributes are derived from authoritative sources:

- **Anthropic** — Claude Code best practices and engineering blog
- **Microsoft** — Code metrics and Azure DevOps guidance
- **Google** — SRE handbook and style guides
- **ArXiv** — Software engineering research papers
- **IEEE/ACM** — Academic publications on code quality

Every attribute includes specific citations and measurable criteria. No subjective opinions—just proven practices that improve AI effectiveness.

[Read the research document →](https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md)

## Use Cases

<div class="use-case-grid">
  <div class="use-case">
    <h4>🚀 New Projects</h4>
    <p>Start with best practices from day one. Use AgentReady's guidance to structure your repository for AI-assisted development from the beginning.</p>
  </div>
  <div class="use-case">
    <h4>🔄 Legacy Modernization</h4>
    <p>Identify high-impact improvements to make legacy codebases more AI-friendly. Prioritize changes with tier-based scoring.</p>
  </div>
  <div class="use-case">
    <h4>📊 Team Standards</h4>
    <p>Establish organization-wide quality baselines. Track adherence across multiple repositories with consistent, objective metrics.</p>
  </div>
  <div class="use-case">
    <h4>🎓 Education & Onboarding</h4>
    <p>Teach developers what makes code AI-ready. Use assessments as learning tools to understand best practices.</p>
  </div>
</div>

## What The AI Bubble Taught Us

> "Fired all our junior developers because 'AI can code now,' then spent $2M on GitHub Copilot Enterprise only to discover it works better with... documentation? And tests? Turns out you can't replace humans with spicy autocomplete and vibes."
> — *CTO, Currently Rehiring*

> "My AI coding assistant told me it was 'very confident' about a solution that would have deleted production. Running AgentReady revealed our codebase has the readability of a ransom note. The AI was confident because it had no idea what it was doing. Just like us!"
> — *Senior Developer, Trust Issues Intensifying*

> "We added 'AI-driven development' to the Series B deck before checking if our monolith had a README. AgentReady scored us 23/100. The AI couldn't figure out our codebase because *we* couldn't figure out our codebase. Investors were not impressed."
> — *VP Engineering, Learning About README Files The Hard Way*

> "Spent the year at conferences saying 'AI will 10x productivity' while our agents hallucinated imports, invented APIs, and confidently suggested `rm -rf /`. AgentReady showed us we're missing pre-commit hooks, type annotations, and basic self-awareness. The only thing getting 10x'd was our incident rate."
> — *Tech Lead, Reformed Hype Man*

> "Asked ChatGPT to refactor our auth system. It wrote beautiful code that compiled perfectly and had zero relation to our actual database schema. Turns out when you have no CLAUDE.md file, no ADRs, and variable names like `data2_final_FINAL`, even AGI would just be guessing. And AGI doesn't exist yet."
> — *Staff Engineer, Back to Documentation Basics*

> "My manager saw a demo where AI 'wrote an entire app' and asked why I'm still employed. I showed him our AgentReady score of 31/100, explained that missing lock files and zero test coverage make AI as useful as a Magic 8-Ball, and we spent the next quarter actually engineering instead of prompt-debugging. AI didn't replace me. Basic hygiene saved me."
> — *Developer, Still Employed, Surprisingly*

## Ready to Get Started?

<div class="cta-section">
  <h3>Assess your repository in 60 seconds</h3>
  <pre><code>pip install agentready
agentready assess .
</code></pre>
  <a href="user-guide.html" class="button button-primary button-large">Read the User Guide</a>
</div>

---

## What Bootstrap Generates

AgentReady Bootstrap creates production-ready infrastructure tailored to your language:

### GitHub Actions Workflows

**`agentready-assessment.yml`** — Runs assessment on every PR and push

- Posts interactive results as PR comments
- Tracks score progression over time
- Fails if score drops below configured threshold

**`tests.yml`** — Language-specific test automation

- Python: pytest with coverage reporting
- JavaScript: jest with coverage
- Go: go test with race detection

**`security.yml`** — Comprehensive security scanning

- CodeQL analysis for vulnerability detection
- Dependency scanning with GitHub Advisory Database
- SAST (Static Application Security Testing)

### GitHub Templates

**Issue Templates** — Structured bug reports and feature requests

- Bug report with reproduction steps template
- Feature request with use case template
- Auto-labeling and assignment

**PR Template** — Checklist-driven pull requests

- Testing verification checklist
- Documentation update requirements
- Breaking change indicators

**CODEOWNERS** — Automated code review assignments

### Development Infrastructure

**`.pre-commit-config.yaml`** — Language-specific quality gates

- Python: black, isort, ruff, mypy
- JavaScript: prettier, eslint
- Go: gofmt, golint

**`.github/dependabot.yml`** — Automated dependency management

- Weekly update checks
- Automatic PR creation for updates
- Security vulnerability patching

**`CONTRIBUTING.md`** — Contributing guidelines (if missing)

**`CODE_OF_CONDUCT.md`** — Red Hat standard code of conduct (if missing)

[See generated file examples →](examples.html#bootstrap-examples)

## Latest News

**Version 1.27.2 Released** (2025-11-23)
Stability improvements with comprehensive pytest fixes! Resolved 35 test failures through enhanced model validation and path sanitization. Added shared test fixtures and improved Assessment schema handling. Significantly improved test coverage with comprehensive CLI and service module tests.

**Version 1.0.0 Released** (2025-11-21)
Initial release with 10 implemented assessors, interactive HTML reports, and comprehensive documentation. AgentReady achieves Gold certification (80.0/100) on its own codebase.

[View full changelog →](https://github.com/ambient-code/agentready/releases)

## Community

- **GitHub**: [github.com/ambient-code/agentready](https://github.com/ambient-code/agentready)
- **Issues**: Report bugs or request features
- **Discussions**: Ask questions and share experiences
- **Contributing**: See the [Developer Guide](developer-guide.html)

## License

AgentReady is open source under the [MIT License](https://github.com/ambient-code/agentready/blob/main/LICENSE).
