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

{% endif %}

---

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

[Learn more about AgentReady →](about.html)

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

{% if site.data.leaderboard.total_repositories > 0 %}
*Leaderboard updated: {{ site.data.leaderboard.generated_at }}*
*Total repositories: {{ site.data.leaderboard.total_repositories }}*
{% endif %}
