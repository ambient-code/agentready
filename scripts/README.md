# Research Update Scripts

Automated maintenance scripts for the AgentReady research report.

## Overview

The `update_research.py` script runs weekly via GitHub Actions to:
1. Search for recent research on AI-assisted development
2. Analyze relevance using Claude API
3. Update `agent-ready-codebase-attributes.md` with new citations
4. Create a pull request for review

## Setup

### 1. Install Dependencies

```bash
pip install anthropic pyyaml requests python-dotenv
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### 3. Configure Settings

Edit `research_config.yaml` to customize:
- `max_updates_per_run`: How many attributes to update per week
- `min_citation_quality_score`: Threshold for including updates
- `priority_attributes`: Which attributes get updated first

## Manual Usage

### Run Full Update

```bash
python scripts/update_research.py
```

### Test Configuration

```bash
# Verify config loads correctly
python -c "import yaml; print(yaml.safe_load(open('scripts/research_config.yaml')))"
```

## GitHub Actions Integration

The workflow runs automatically every Monday at 9 AM UTC.

**Manual trigger**:

```bash
gh workflow run research-update.yml
```

**View recent runs**:

```bash
gh run list --workflow=research-update.yml
```

## Output

### Exit Codes

- `0`: Changes made, PR should be created
- `1`: No changes needed or error occurred

### Files Modified

- `agent-ready-codebase-attributes.md`: Research report content
  - Updated attribute sections with new findings
  - New citations added
  - Version incremented
  - Date updated to current

## Configuration Reference

### `research_config.yaml`

```yaml
update_settings:
  max_updates_per_run: 5          # Limit changes per PR
  min_citation_quality_score: 0.7  # Claude relevance threshold
  search_recency_months: 12        # Only recent research

priority_attributes:
  - "1.1"  # CLAUDE.md
  - "2.1"  # README
  # ... Tier 1 attributes processed first

search_domains:
  prioritized:
    - anthropic.com
    - arxiv.org
    # ... High-authority sources
  blocked:
    - spam-site.com
    # ... Low-quality sources to avoid
```

## Development

### Test Search Functionality

```python
from update_research import ResearchUpdater

updater = ResearchUpdater()
results = updater.search_recent_research("1.1", "CLAUDE.md Configuration Files")
print(f"Found {len(results)} results")
```

### Test Relevance Analysis

```python
from update_research import ResearchUpdater

updater = ResearchUpdater()
analysis = updater.analyze_relevance(
    "1.1",
    search_results,
    "Current attribute content..."
)
print(f"Relevance score: {analysis['relevance_score']}")
```

### Dry Run (No File Modifications)

```python
# Comment out the write operations in update_attribute_section()
# to test without modifying files
```

## Troubleshooting

### No Updates Generated

**Possible causes**:
- `min_citation_quality_score` too high
- No recent research found
- Search API issues

**Solutions**:
- Lower threshold in config
- Check search functionality manually
- Verify API credentials

### PR Not Created

**Possible causes**:
- Script exited with code 1 (no changes)
- GitHub Actions permissions issue
- Branch conflicts

**Solutions**:
- Check workflow logs: `gh run view --log`
- Verify repository permissions
- Delete stale `automated/research-update` branch

### API Rate Limits

**Claude API**:
- Default: 1,000 requests/minute
- Cost: ~$0.30 per weekly run
- Caching: Search results cached 7 days

**Mitigation**:
- Reduce `max_updates_per_run`
- Increase `search_recency_months` (fewer new results)

## Cost Estimation

### Weekly Run (5 Updates)

- Search generation: 5 × ~2K tokens = 10K tokens
- Relevance analysis: 5 × ~6K tokens = 30K tokens
- Total: ~40K tokens/week ≈ $0.30/week

### Annual Cost

- ~$15-20/year for weekly automation
- Scales linearly with `max_updates_per_run`

## Security

### API Key Protection

- Store only in GitHub Secrets (never commit)
- Rotate quarterly or after team changes
- Use least-privilege API keys

### Content Validation

- All URLs verified before adding
- Malicious content filtered
- JSON parsing validated to prevent injection

## Related Documentation

- `research-update.skill.md`: Complete skill documentation
- `.github/workflows/research-update.yml`: GitHub Actions workflow
- `agent-ready-codebase-attributes.md`: The research report

---

**Last Updated**: 2025-12-03
**Maintainer**: Jeremy Eder
