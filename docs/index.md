---
layout: default
title: AgentReady Leaderboard
description: Community-submitted repository assessments ranked by agent-readiness
---

# 🏆 AgentReady Leaderboard

Community-driven rankings of agent-ready repositories.

{% if site.data.leaderboard.total_repositories == 0 %}

## No Submissions Yet

Be the first to submit your repository to the leaderboard!

```bash
# 1. Run assessment
agentready assess .

# 2. Submit to leaderboard (requires GITHUB_TOKEN)
export GITHUB_TOKEN=ghp_your_token_here
agentready submit
```

[Learn more about submission →](user-guide.html#leaderboard)

{% else %}

{% assign sorted = site.data.leaderboard.overall %}

## 🥇 Top 10 Repositories

<div class="leaderboard-top10">
{% for entry in sorted limit:10 %}
  <div class="leaderboard-card tier-{{ entry.tier | downcase }}">
    <div class="rank">#{{ forloop.index }}</div>
    <div class="repo-info">
      <h3><a href="{{ entry.url }}">{{ entry.repo }}</a></h3>
      <div class="meta">
        <span class="language">{{ entry.language }}</span>
        <span class="size">{{ entry.size }}</span>
      </div>
    </div>
    <div class="score-badge">
      <span class="score">{{ entry.score | round: 1 }}</span>
      <span class="tier">{{ entry.tier }}</span>
    </div>
  </div>
{% endfor %}
</div>

## 📊 All Repositories

<table class="leaderboard-table">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Repository</th>
      <th>Score</th>
      <th>Tier</th>
      <th>Ruleset</th>
      <th>Language</th>
      <th>Size</th>
      <th>Last Updated</th>
    </tr>
  </thead>
  <tbody>
    {% for entry in sorted %}
    <tr class="tier-{{ entry.tier | downcase }}">
      <td class="rank">{{ entry.rank }}</td>
      <td class="repo-name">
        <a href="{{ entry.url }}">{{ entry.repo }}</a>
      </td>
      <td class="score">{{ entry.score | round: 1 }}</td>
      <td>
        <span class="badge {{ entry.tier | downcase }}">{{ entry.tier }}</span>
      </td>
      <td class="version">{{ entry.research_version }}</td>
      <td>{{ entry.language }}</td>
      <td>{{ entry.size }}</td>
      <td>{{ entry.last_updated }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

{% if site.data.leaderboard.total_repositories > 0 %}
<p style="margin-top: 1rem; color: #666; font-size: 0.9rem;">
<em>Leaderboard updated: {{ site.data.leaderboard.generated_at }}</em><br>
<em>Total repositories: {{ site.data.leaderboard.total_repositories }}</em>
</p>
{% endif %}

{% endif %}

---

## Key Features

<div class="feature-list">
  <!-- Feature 1: Research-Backed -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="implementation-status.html#complete-attribute-table">🔬 Research-Backed</a></h3>
      <p>Every generated file and assessed attribute is backed by <a href="implementation-status.html#complete-attribute-table">50+ citations</a> from Anthropic, Microsoft, Google, and academic research.</p>
    </div>
    <div class="feature-example">
      <table style="width: 100%; font-size: var(--text-xs); border-collapse: collapse;">
        <thead>
          <tr style="background-color: var(--color-gray-100);">
            <th style="padding: var(--space-2); text-align: left;">Tier</th>
            <th style="padding: var(--space-2); text-align: left;">Attribute</th>
            <th style="padding: var(--space-2); text-align: center;">Citations</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: var(--space-2);"><span class="tier-badge tier-1">T1</span></td>
            <td style="padding: var(--space-2);">CLAUDE.md File</td>
            <td style="padding: var(--space-2); text-align: center;">6</td>
          </tr>
          <tr>
            <td style="padding: var(--space-2);"><span class="tier-badge tier-2">T2</span></td>
            <td style="padding: var(--space-2);">Type Annotations</td>
            <td style="padding: var(--space-2); text-align: center;">8</td>
          </tr>
          <tr>
            <td colspan="3" style="padding: var(--space-2); text-align: center; font-style: italic;">
              <a href="implementation-status.html#complete-attribute-table">View all 25 attributes →</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Feature 2: CI-Friendly -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="user-guide.html#bootstrap-your-repository">📈 CI-Friendly</a></h3>
      <p>Generated GitHub Actions run AgentReady on every PR, posting results as comments. Track improvements over time with Markdown reports.</p>
    </div>
    <div class="feature-example">
      <div style="text-align: center;">
        <img src="https://img.shields.io/badge/AgentReady-85.3%25-gold?style=for-the-badge" alt="AgentReady Score" style="margin-bottom: var(--space-3);"/>
        <p style="margin: 0; color: var(--color-gray-600); font-size: var(--text-xs);">
          ✓ Auto-assess on every PR<br>
          ✓ Markdown report comments<br>
          ✓ Track improvements over time
        </p>
      </div>
    </div>
  </div>

  <!-- Feature 3: One Command Setup -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="user-guide.html#bootstrap-your-repository">⚡ One Command Setup</a></h3>
      <p>From zero to production-ready infrastructure in seconds. Review generated files with --dry-run before committing.</p>
    </div>
    <div class="feature-example">
      <div style="width: 100%;">
        <code>$ agentready bootstrap .</code>
        <div style="margin-top: var(--space-2); font-size: var(--text-xs); color: var(--color-success); font-family: var(--font-mono);">
          ✓ Detected language: Python<br>
          ✓ Generated 12 files (0.8s)<br>
          ✓ Ready for git commit
        </div>
      </div>
    </div>
  </div>

  <!-- Feature 4: Language-Specific -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="user-guide.html#bootstrap-your-repository">🎯 Language-Specific</a></h3>
      <p>Auto-detects your primary language (Python, JavaScript, Go) and generates appropriate workflows, linters, and test configurations.</p>
    </div>
    <div class="feature-example">
      <ul style="list-style-type: none; padding: 0; margin: 0;">
        <li>✓ Python (black, isort, ruff, pytest)</li>
        <li>✓ JavaScript/TypeScript (prettier, eslint)</li>
        <li>✓ Go (gofmt, golint)</li>
        <li style="margin-top: var(--space-3); font-style: italic; color: var(--color-gray-500);">
          Auto-detected via git ls-files
        </li>
      </ul>
    </div>
  </div>

  <!-- Feature 5: Automated Infrastructure -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="user-guide.html#bootstrap-your-repository">🤖 Automated Infrastructure</a></h3>
      <p>Bootstrap generates complete GitHub setup: Actions workflows, issue/PR templates, pre-commit hooks, Dependabot config, and security scanning—all language-aware.</p>
    </div>
    <div class="feature-example">
      <div style="font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-gray-700);">
        <div>📁 .github/</div>
        <div style="padding-left: var(--space-3);">├── workflows/ (3 files)</div>
        <div style="padding-left: var(--space-3);">├── ISSUE_TEMPLATE/</div>
        <div style="padding-left: var(--space-3);">├── PULL_REQUEST_TEMPLATE.md</div>
        <div style="padding-left: var(--space-3);">└── CODEOWNERS</div>
        <div style="margin-top: var(--space-2);">📄 .pre-commit-config.yaml</div>
        <div>📄 .github/dependabot.yml</div>
      </div>
    </div>
  </div>

  <!-- Feature 6: Readiness Tiers -->
  <div class="feature-item">
    <div class="feature-tile">
      <h3><a href="attributes.html">🏆 Readiness Tiers</a></h3>
      <p>Platinum, Gold, Silver, Bronze levels validate your codebase quality. Bootstrap helps you achieve Gold (75+) immediately.</p>
    </div>
    <div class="feature-example">
      <div class="badge-list">
        <span class="tier-badge-large platinum">Platinum 90+</span>
        <span class="tier-badge-large gold">Gold 75+</span>
        <span class="tier-badge-large silver">Silver 60+</span>
        <span class="tier-badge-large bronze">Bronze 40+</span>
      </div>
      <p style="margin-top: var(--space-3); text-align: center; font-size: var(--text-xs); color: var(--color-gray-600);">
        Bootstrap targets Gold (75+) immediately
      </p>
    </div>
  </div>
</div>

---

## 📈 Submit Your Repository

```bash
# 1. Run assessment
agentready assess .

# 2. Submit to leaderboard (requires GITHUB_TOKEN)
export GITHUB_TOKEN=ghp_your_token_here
agentready submit

# 3. Wait for validation and PR merge
```

**Requirements**:
- GitHub repository (public)
- Commit access to repository
- `GITHUB_TOKEN` environment variable

[Learn more about submission →](user-guide.html#leaderboard)

---

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

[View detailed command documentation →](user-guide.html#command-reference)
