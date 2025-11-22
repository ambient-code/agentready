# AgentReady GitHub Integrations

This module provides GitHub integration functionality for AgentReady, including badge generation, API clients, and PR comment formatters.

## Modules

### `badge.py` - Badge Generation

Generate repository badges showing certification levels:

```python
from agentready.integrations import BadgeGenerator

# Get certification level
level = BadgeGenerator.get_certification_level(85.0)  # "gold"

# Generate Shields.io URL
url = BadgeGenerator.generate_shields_url(85.0, style="flat-square")

# Generate Markdown badge
markdown = BadgeGenerator.generate_markdown_badge(
    85.0,
    report_url="https://example.com/report.html"
)

# Generate custom SVG
svg = BadgeGenerator.generate_svg(85.0, width=200)
```

### `github_api.py` - GitHub API Client

Interact with GitHub Status API, Checks API, and comments:

```python
from agentready.integrations import GitHubAPIClient, GitHubStatus

# Initialize client
client = GitHubAPIClient()

# Create status check
status = GitHubStatus(
    state="success",
    description="AgentReady: 85.0/100 (Gold)",
    target_url="https://example.com/report"
)
client.create_commit_status(commit_sha, status)

# Post PR comment
client.create_pr_comment(pr_number, comment_body)
```

### `pr_comment.py` - PR Comment Generator

Format assessment results for PR comments:

```python
from agentready.integrations import PRCommentGenerator

# Generate detailed comment
comment = PRCommentGenerator.generate_summary_comment(
    assessment,
    previous_score=80.0,
    show_details=True
)

# Generate compact comment
compact = PRCommentGenerator.generate_compact_comment(assessment)

# Generate check output
title, summary, text = PRCommentGenerator.generate_check_output(
    assessment,
    include_remediation=True
)
```

## Configuration

See `agentready.models.github_config` for configuration schema:

```python
from agentready.models.github_config import GitHubIntegrationConfig

config = GitHubIntegrationConfig.from_dict({
    "badge": {"enabled": True, "style": "flat-square"},
    "status_checks": {"enabled": True, "min_score": 75.0}
})
```

## Documentation

Full documentation: [docs/github-integration.md](../../../docs/github-integration.md)

## Examples

### Add Badge to README

```markdown
[![AgentReady](https://img.shields.io/badge/AgentReady-85.0%20(Gold)-eab308?style=flat-square)](https://github.com/owner/repo)
```

### GitHub Actions Workflow

```yaml
- name: Run Assessment
  run: agentready assess .

- name: Create Status Check
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    python -c "
    from agentready.integrations import GitHubAPIClient, GitHubStatus
    client = GitHubAPIClient()
    status = GitHubStatus(state='success', description='Passed')
    client.create_commit_status('${{ github.sha }}', status)
    "
```

## Testing

Run tests:

```bash
pytest tests/unit/test_integrations_*.py -v
```
