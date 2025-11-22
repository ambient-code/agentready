# GitHub Integration Guide

This guide explains how to use AgentReady's GitHub integration features including badges, status checks, and automated PR comments.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Workflow Templates](#workflow-templates)
- [Badge Generation](#badge-generation)
- [API Usage](#api-usage)
- [Examples](#examples)

## Overview

AgentReady provides comprehensive GitHub integration to help teams track and improve repository quality:

- **Repository Badges**: Display certification level in README
- **GitHub Actions**: Automated assessments on PRs and pushes
- **Status Checks**: Pass/fail checks based on quality scores
- **PR Comments**: Formatted assessment results with trends
- **Checks API**: Rich check runs with detailed output

## Features

### 1. Repository Badges

Generate badges showing your repository's AgentReady certification level:

```python
from agentready.integrations import BadgeGenerator

# Generate Shields.io badge URL
badge_url = BadgeGenerator.generate_shields_url(
    score=85.0,
    style="flat-square"
)

# Generate Markdown badge with link
markdown = BadgeGenerator.generate_markdown_badge(
    score=85.0,
    report_url="https://example.com/report.html"
)
```

**Badge Styles:**
- `flat` - Flat design
- `flat-square` - Flat with square edges (default)
- `plastic` - Plastic 3D style
- `for-the-badge` - Large badge format
- `social` - Social media style

**Certification Levels:**
- 🟣 **Platinum** (90-100): `#9333ea`
- 🟡 **Gold** (75-89): `#eab308`
- ⚪ **Silver** (60-74): `#94a3b8`
- 🟤 **Bronze** (40-59): `#92400e`
- 🔴 **Needs Improvement** (0-39): `#dc2626`

### 2. GitHub Actions Workflows

Two workflow templates are provided:

#### Basic Workflow

Simple assessment with artifact upload:

```yaml
# .github/workflows/agentready.yml
name: AgentReady Assessment

on:
  pull_request:
  push:
    branches: [main]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install agentready
      - run: agentready assess .
      - uses: actions/upload-artifact@v4
        with:
          name: agentready-reports
          path: .agentready/
```

#### Full Integration Workflow

Complete integration with status checks and PR comments. See `src/agentready/templates/workflows/agentready-full.yml.j2` for the full template.

### 3. Status Checks

Add quality gates to your repository:

```python
from agentready.integrations import GitHubAPIClient, GitHubStatus

client = GitHubAPIClient()

# Create commit status
status = GitHubStatus(
    state="success",  # or "failure", "error", "pending"
    description="AgentReady: 85.0/100 (Gold) - 20/25 passed",
    context="agentready/assessment",
    target_url="https://example.com/report"
)

client.create_commit_status(commit_sha, status)
```

### 4. PR Comments

Generate formatted PR comments:

```python
from agentready.integrations import PRCommentGenerator

# Generate summary comment
comment = PRCommentGenerator.generate_summary_comment(
    assessment=assessment,
    previous_score=80.0,  # Show delta
    report_url="https://example.com/report.html",
    show_details=True  # Include collapsible details
)

# Generate compact one-liner
compact = PRCommentGenerator.generate_compact_comment(
    assessment=assessment,
    report_url="https://example.com/report.html"
)
```

## Configuration

Create `.agentready-config.yaml` in your repository root:

```yaml
github:
  # Badge configuration
  badge:
    enabled: true
    style: flat-square
    label: AgentReady

  # GitHub Actions integration
  actions:
    enabled: true
    trigger_on:
      - pull_request
      - push
    post_comment: true
    update_status: true
    upload_artifacts: true
    retention_days: 30

  # Status checks configuration
  status_checks:
    enabled: true
    min_score: 75.0  # Fail if below this score
    require_improvement: false  # Require score to increase
    use_checks_api: true  # Use Checks API vs Status API

  # PR comments configuration
  comments:
    enabled: true
    show_delta: true  # Show score change
    show_trend: false  # Show ASCII trend chart
    collapse_details: true  # Collapse detailed findings
    compact_mode: false  # Use compact format
```

## Workflow Templates

### Using Templates

The workflow templates are available in `src/agentready/templates/workflows/`:

1. **agentready-basic.yml.j2** - Minimal workflow
2. **agentready-full.yml.j2** - Complete integration

Copy the appropriate template to `.github/workflows/agentready.yml` and customize as needed.

### Template Variables

Templates support Jinja2 variables:

```yaml
python_version: "3.11"
main_branch: "main"
retention_days: 30
verbose: true
```

## Badge Generation

### Add Badge to README

1. Run assessment to get your score:
   ```bash
   agentready assess .
   ```

2. Add badge to `README.md`:
   ```markdown
   # My Project

   [![AgentReady](https://img.shields.io/badge/AgentReady-85.0%20(Gold)-eab308?style=flat-square)](https://github.com/owner/repo/actions)

   Your project description...
   ```

3. Update badge URL whenever your score changes

### Generate Badge Programmatically

```python
from agentready.integrations import BadgeGenerator

# From assessment
score = 85.0
level = BadgeGenerator.get_certification_level(score)

# Generate Markdown
markdown = BadgeGenerator.generate_markdown_badge(
    score=score,
    level=level,
    report_url="https://example.com/report.html",
    style="for-the-badge"
)

# Output: [![AgentReady](https://img.shields.io/badge/...)](https://example.com/report.html)
```

## API Usage

### GitHub API Client

```python
from agentready.integrations import GitHubAPIClient
import os

# Initialize client (uses GITHUB_TOKEN and GITHUB_REPOSITORY env vars)
client = GitHubAPIClient()

# Or provide explicitly
client = GitHubAPIClient(
    token=os.getenv("GITHUB_TOKEN"),
    repo="owner/repo"
)
```

### Create Status Check

```python
from agentready.integrations import GitHubStatus

status = GitHubStatus(
    state="success",
    description="AgentReady: 85.0/100 (Gold)",
    context="agentready/assessment",
    target_url="https://example.com/report"
)

client.create_commit_status(commit_sha, status)
```

### Create Check Run

```python
from agentready.integrations import GitHubCheckRun

check = GitHubCheckRun(
    name="AgentReady Assessment",
    status="completed",
    conclusion="success",
    output_title="Score: 85.0/100 (Gold)",
    output_summary="Passed 20/25 attributes",
    output_text="## Detailed Results\n...",
    details_url="https://example.com/report"
)

client.create_check_run(commit_sha, check)
```

### Post PR Comment

```python
# Create new comment
client.create_pr_comment(
    pr_number=42,
    body="## AgentReady Assessment\n\nScore: 85.0/100"
)

# Update existing comment
comment_id = client.find_existing_comment(
    pr_number=42,
    search_text="AgentReady Assessment"
)

if comment_id:
    client.update_pr_comment(comment_id, updated_body)
```

## Examples

### Example 1: Basic Workflow

```yaml
# .github/workflows/agentready.yml
name: AgentReady

on: [pull_request, push]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install agentready
      - run: agentready assess . --verbose
      - uses: actions/upload-artifact@v4
        with:
          name: reports
          path: .agentready/
```

### Example 2: PR Comment Bot

```yaml
# Add to workflow after assessment
- name: Comment on PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const report = fs.readFileSync('.agentready/report-latest.md', 'utf8');

      await github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: report
      });
```

### Example 3: Quality Gate

```yaml
# Fail workflow if score below threshold
- name: Check Quality Gate
  run: |
    SCORE=$(python -c "import json; print(json.load(open('.agentready/assessment-latest.json'))['score'])")
    if (( $(echo "$SCORE < 75.0" | bc -l) )); then
      echo "Score $SCORE below threshold 75.0"
      exit 1
    fi
```

### Example 4: Custom Badge Service

For organizations wanting to host their own badge service:

```python
from fastapi import FastAPI
from agentready.integrations import BadgeGenerator

app = FastAPI()

@app.get("/badge/{owner}/{repo}.svg")
async def get_badge(owner: str, repo: str):
    # Fetch latest assessment (from storage or run on-demand)
    score, level = get_latest_assessment(owner, repo)

    # Generate SVG
    svg = BadgeGenerator.generate_svg(score, level)

    return Response(content=svg, media_type="image/svg+xml")
```

## Environment Variables

The GitHub API client uses these environment variables:

- `GITHUB_TOKEN` - GitHub personal access token or Actions token
- `GITHUB_REPOSITORY` - Repository in "owner/name" format
- `GITHUB_SHA` - Commit SHA (for status checks)

These are automatically available in GitHub Actions.

## Permissions

### Required Permissions

For GitHub Actions workflows:

```yaml
permissions:
  contents: read       # Read repository code
  pull-requests: write # Post PR comments
  checks: write        # Create check runs
  statuses: write      # Create commit statuses
```

### GitHub App Permissions

For a GitHub App integration:

- **Contents**: Read
- **Checks**: Write
- **Pull Requests**: Write
- **Commit Statuses**: Write

## Troubleshooting

### Badge Not Updating

Badges are cached by Shields.io. To bypass cache:
- Add query parameter: `?nocache=1`
- Or wait ~5 minutes for cache to expire

### Status Check Not Appearing

1. Verify `GITHUB_TOKEN` has `statuses: write` permission
2. Check commit SHA is correct
3. Ensure API request succeeded (check logs)

### PR Comment Failed

1. Verify `GITHUB_TOKEN` has `pull-requests: write` permission
2. Ensure PR number is correct
3. Check comment body is valid Markdown

## Future Enhancements

Planned features (see BACKLOG.md):

- **Dashboard**: Organization-wide quality dashboard
- **Trend Analysis**: Historical score tracking
- **Automated Remediation**: One-click fixes
- **GitHub App**: Installable GitHub Marketplace app
- **Slack Integration**: Notifications for score changes

## Support

For issues or questions:
- GitHub Issues: https://github.com/redhat/agentready/issues
- Documentation: https://github.com/redhat/agentready/tree/main/docs

---

_Last updated: 2025-11-22_
