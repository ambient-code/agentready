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

<div class="feature-grid">
  <div class="feature">
    <h3><a href="https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md">🔬 Research-Backed</a></h3>
    <p>Every generated file and assessed attribute is backed by <a href="https://github.com/ambient-code/agentready/blob/main/agent-ready-codebase-attributes.md">50+ citations</a> from Anthropic, Microsoft, Google, and academic research.</p>
  </div>
  <div class="feature">
    <h3><a href="user-guide.html#bootstrap-your-repository">📈 CI-Friendly</a></h3>
    <p>Generated GitHub Actions run AgentReady on every PR, posting results as comments. Track improvements over time with Markdown reports.</p>
  </div>
  <div class="feature">
    <h3><a href="user-guide.html#bootstrap-your-repository">⚡ One Command Setup</a></h3>
    <p>From zero to production-ready infrastructure in seconds. Review generated files with --dry-run before committing.</p>
  </div>
  <div class="feature">
    <h3><a href="user-guide.html#bootstrap-your-repository">🎯 Language-Specific</a></h3>
    <p>Auto-detects your primary language (Python, JavaScript, Go) and generates appropriate workflows, linters, and test configurations.</p>
  </div>
  <div class="feature">
    <h3><a href="user-guide.html#bootstrap-your-repository">🤖 Automated Infrastructure</a></h3>
    <p>Bootstrap generates complete GitHub setup: Actions workflows, issue/PR templates, pre-commit hooks, Dependabot config, and security scanning—all language-aware.</p>
  </div>
  <div class="feature">
    <h3><a href="attributes.html">🏆 Readiness Tiers</a></h3>
    <p>Platinum, Gold, Silver, Bronze levels validate your codebase quality. Bootstrap helps you achieve Gold (75+) immediately.</p>
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
