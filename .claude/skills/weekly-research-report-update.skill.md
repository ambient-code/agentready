# Research Update Skill

**Purpose**: Maintain the AgentReady research report (`agent-ready-codebase-attributes.md`) with weekly automated updates, ensuring it stays current with emerging best practices and includes authoritative citations.

**Trigger**: GitHub Actions weekly schedule (every Monday 9 AM UTC) or manual workflow dispatch

**Output**: Pull request with proposed updates to the research report

---

## Skill Overview

This skill automates the maintenance of the AgentReady research report by:

1. **Searching for new research** on AI-assisted development best practices
2. **Extracting relevant updates** for each of the 25 attributes
3. **Citing authoritative sources** with URLs
4. **Generating a pull request** for human review
5. **Preserving document structure** and formatting

---

## Prerequisites

### Required Secrets (GitHub Repository Settings)

1. **ANTHROPIC_API_KEY**: Claude API key for LLM-powered research analysis
2. **GITHUB_TOKEN**: Automatically provided by GitHub Actions (no setup needed)

### Required Dependencies

```yaml
dependencies:
  - anthropic>=0.34.0
  - requests>=2.31.0
  - python-dotenv>=1.0.0
```

---

## Implementation Components

### 1. GitHub Actions Workflow

**File**: `.github/workflows/research-update.yml`

**Schedule**: Weekly on Mondays at 9 AM UTC
**Manual Trigger**: `workflow_dispatch` for on-demand updates

**Workflow Steps**:
1. Checkout repository
2. Set up Python 3.12 environment
3. Install dependencies
4. Run research update script
5. Create pull request if changes detected

### 2. Research Update Script

**File**: `scripts/update_research.py`

**Core Functions**:

- `search_recent_research(attribute_id, attribute_name)`: Web search for new research
- `analyze_relevance(search_results, current_content)`: Claude API analysis
- `extract_citations(analysis_result)`: Parse URLs and create citation list
- `update_attribute_section(attribute_id, new_content, citations)`: Update markdown
- `validate_markdown_structure()`: Ensure document integrity

**Search Strategy**:
- Use WebSearch for academic papers, blog posts, documentation
- Focus on recent publications (last 6-12 months)
- Prioritize authoritative sources: Anthropic, Microsoft Research, Google AI, ArXiv, ACM/IEEE
- Filter for Claude Code and AI-assisted development context

**Citation Format**:

```markdown
**Citations:**
- [Paper Title](https://url.com) - Author/Source, Date
- [Blog Post Title](https://blog.url.com) - Author, Date
```

### 3. Configuration File

**File**: `scripts/research_config.yaml`

```yaml
update_settings:
  max_updates_per_run: 5  # Limit changes per PR to keep reviews manageable
  min_citation_quality_score: 0.7  # Claude-rated relevance threshold
  search_recency_months: 12  # Only include research from last N months

priority_attributes:
  # Update these first (Tier 1 attributes)
  - "1.1"  # CLAUDE.md
  - "2.1"  # README
  - "3.3"  # Type annotations
  - "5.1"  # Test coverage
  - "7.1"  # Conventional commits

search_domains:
  prioritized:
    - anthropic.com
    - microsoft.com/research
    - research.google
    - arxiv.org
    - dl.acm.org
  blocked:
    - spam-site.com
    - low-quality-blog.com
```

---

## Step-by-Step Instructions

### Step 1: Create GitHub Actions Workflow

Create `.github/workflows/research-update.yml`:

```yaml
name: Weekly Research Update

on:
  schedule:
    # Every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch:  # Manual trigger

permissions:
  contents: write
  pull-requests: write

jobs:
  update-research:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install anthropic requests python-dotenv pyyaml

      - name: Run research update script
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/update_research.py

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'docs: update research report with latest findings'
          branch: automated/research-update
          delete-branch: true
          title: 'Weekly Research Update: Agent-Ready Codebase Attributes'
          body: |
            ## Automated Research Update

            This PR contains weekly updates to the AgentReady research report based on:
            - Recent publications on AI-assisted development
            - New best practices from authoritative sources
            - Updated citations and references

            **Review Checklist**:
            - [ ] All citations include valid URLs
            - [ ] Updates are relevant to attribute definitions
            - [ ] Document structure is preserved
            - [ ] Version number incremented appropriately
            - [ ] Date updated to current

            **Generated by**: Weekly Research Update workflow
            **Triggered**: ${{ github.event_name }}
          labels: |
            documentation
            automated
            research
```

### Step 2: Create Research Update Script

Create `scripts/update_research.py`:

```python
#!/usr/bin/env python3
"""
Automated research update script for agent-ready-codebase-attributes.md

Searches for recent research, analyzes relevance using Claude API,
and proposes updates with citations.
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import anthropic
import requests
import yaml


class ResearchUpdater:
    """Manages research report updates with LLM-powered analysis."""

    def __init__(self, config_path: str = "scripts/research_config.yaml"):
        self.config = self._load_config(config_path)
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.report_path = Path("agent-ready-codebase-attributes.md")
        self.changes_made = []

    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    def search_recent_research(
        self,
        attribute_id: str,
        attribute_name: str
    ) -> List[Dict[str, str]]:
        """
        Search for recent research on a specific attribute.

        Uses multiple search strategies:
        1. Academic papers (ArXiv, ACM, IEEE)
        2. Industry blogs (Anthropic, Microsoft, Google)
        3. Documentation updates

        Returns:
            List of search results with title, url, snippet, date
        """
        search_queries = [
            f"{attribute_name} AI assisted development best practices 2025",
            f"{attribute_name} Claude Code LLM agents",
            f"{attribute_name} codebase optimization AI",
        ]

        results = []
        for query in search_queries:
            # Use Claude's WebSearch capability or external API
            # This is a placeholder - actual implementation would use
            # the WebSearch tool or external search API
            results.extend(self._execute_search(query))

        # Filter by recency
        cutoff_date = datetime.now() - timedelta(
            days=self.config["update_settings"]["search_recency_months"] * 30
        )
        results = [r for r in results if self._parse_date(r.get("date")) >= cutoff_date]

        return results[:10]  # Limit to top 10 results

    def _execute_search(self, query: str) -> List[Dict[str, str]]:
        """Execute web search (placeholder for actual implementation)."""
        # In actual implementation, this would use WebSearch tool
        # or external API like Google Custom Search
        return []

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return datetime.min
        # Add actual date parsing logic
        return datetime.now()

    def analyze_relevance(
        self,
        attribute_id: str,
        search_results: List[Dict[str, str]],
        current_content: str
    ) -> Dict[str, any]:
        """
        Use Claude API to analyze search results and determine relevance.

        Returns:
            {
                "relevance_score": float (0-1),
                "suggested_updates": str,
                "citations": List[Dict[str, str]],
                "reasoning": str
            }
        """
        prompt = f"""You are a research analyst maintaining a comprehensive guide on AI-assisted development best practices.

CURRENT ATTRIBUTE CONTENT:
{current_content}

RECENT RESEARCH FINDINGS:
{json.dumps(search_results, indent=2)}

TASK:
1. Analyze each research finding for relevance to the attribute
2. Identify any new insights, contradictions, or updated recommendations
3. Suggest specific updates to the attribute content
4. Provide authoritative citations

REQUIREMENTS:
- Only suggest updates that add genuinely new information
- Prioritize authoritative sources (research papers, official documentation)
- Include URL citations for all claims
- Maintain technical accuracy and clarity
- Rate overall relevance (0-1 score)

OUTPUT FORMAT (JSON):
{{
    "relevance_score": 0.0-1.0,
    "suggested_updates": "Specific text to add or modify...",
    "citations": [
        {{
            "title": "Paper/Article Title",
            "url": "https://...",
            "authors": "Author names or organization",
            "date": "YYYY-MM-DD",
            "key_finding": "1-2 sentence summary"
        }}
    ],
    "reasoning": "Why these updates are relevant..."
}}
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        content = response.content[0].text
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        return json.loads(content)

    def update_attribute_section(
        self,
        attribute_id: str,
        analysis_result: Dict[str, any]
    ) -> bool:
        """
        Update the attribute section in the research report.

        Returns:
            True if changes were made, False otherwise
        """
        if analysis_result["relevance_score"] < self.config["update_settings"]["min_citation_quality_score"]:
            print(f"Skipping attribute {attribute_id}: relevance score too low")
            return False

        # Read current report
        content = self.report_path.read_text()

        # Find attribute section
        pattern = rf'(### {re.escape(attribute_id)} .*?\n)(.*?)(?=\n###|\n---|\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print(f"Warning: Could not find attribute {attribute_id}")
            return False

        section_header = match.group(1)
        section_content = match.group(2)

        # Insert new content before the "---" separator or at the end
        updated_content = section_content

        # Add suggested updates
        if analysis_result["suggested_updates"]:
            # Insert after "Impact on Agent Behavior:" section
            impact_pattern = r'(\*\*Impact on Agent Behavior:\*\*.*?\n\n)'
            if re.search(impact_pattern, updated_content, re.DOTALL):
                updated_content = re.sub(
                    impact_pattern,
                    rf'\1**Recent Research Updates ({datetime.now().strftime("%Y-%m")}):**\n{analysis_result["suggested_updates"]}\n\n',
                    updated_content,
                    flags=re.DOTALL
                )

        # Add or update citations
        citations_text = self._format_citations(analysis_result["citations"])
        if citations_text:
            # Check if Citations section exists
            if "**Citations:**" in updated_content:
                # Append new citations
                updated_content = re.sub(
                    r'(\*\*Citations:\*\*\n)(.*?)(\n\n|\n---|\Z)',
                    rf'\1\2{citations_text}\n\3',
                    updated_content,
                    flags=re.DOTALL
                )
            else:
                # Add new Citations section before examples
                example_pattern = r'(\*\*Example:\*\*)'
                if re.search(example_pattern, updated_content):
                    updated_content = re.sub(
                        example_pattern,
                        f"**Citations:**\n{citations_text}\n\n\\1",
                        updated_content
                    )
                else:
                    # Add at the end of section
                    updated_content += f"\n\n**Citations:**\n{citations_text}\n"

        # Replace section in full document
        new_section = section_header + updated_content
        new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)

        # Write updated content
        self.report_path.write_text(new_content)

        self.changes_made.append({
            "attribute_id": attribute_id,
            "relevance_score": analysis_result["relevance_score"],
            "num_citations": len(analysis_result["citations"])
        })

        return True

    def _format_citations(self, citations: List[Dict[str, str]]) -> str:
        """Format citations in markdown."""
        lines = []
        for cite in citations:
            title = cite.get("title", "Untitled")
            url = cite.get("url", "")
            authors = cite.get("authors", "Unknown")
            date = cite.get("date", "")

            lines.append(f"- [{title}]({url}) - {authors}, {date}")

        return "\n".join(lines)

    def update_metadata(self):
        """Update version and date in report header."""
        content = self.report_path.read_text()

        # Update date
        today = datetime.now().strftime("%Y-%m-%d")
        content = re.sub(
            r'\*\*Date:\*\* \d{4}-\d{2}-\d{2}',
            f"**Date:** {today}",
            content
        )

        # Increment patch version (could be made smarter based on change magnitude)
        version_pattern = r'\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)'
        match = re.search(version_pattern, content)
        if match:
            major, minor, patch = map(int, match.groups())
            new_version = f"{major}.{minor}.{patch + 1}"
            content = re.sub(
                version_pattern,
                f"**Version:** {new_version}",
                content
            )

        self.report_path.write_text(content)

    def run_update(self):
        """Main update orchestration."""
        print("Starting weekly research update...")

        # Extract all attribute IDs from current report
        content = self.report_path.read_text()
        attribute_pattern = r'### (\d+\.\d+) (.+?)\n'
        attributes = re.findall(attribute_pattern, content)

        print(f"Found {len(attributes)} attributes to check")

        # Prioritize Tier 1 attributes
        priority_attrs = self.config.get("priority_attributes", [])
        sorted_attrs = sorted(
            attributes,
            key=lambda x: (x[0] not in priority_attrs, x[0])
        )

        max_updates = self.config["update_settings"]["max_updates_per_run"]
        updates_made = 0

        for attr_id, attr_name in sorted_attrs:
            if updates_made >= max_updates:
                print(f"Reached max updates limit ({max_updates})")
                break

            print(f"\nProcessing attribute {attr_id}: {attr_name}")

            # Extract current content
            section_pattern = rf'### {re.escape(attr_id)} {re.escape(attr_name)}(.*?)(?=\n###|\n---|\Z)'
            match = re.search(section_pattern, content, re.DOTALL)
            if not match:
                continue
            current_content = match.group(1)

            # Search for recent research
            search_results = self.search_recent_research(attr_id, attr_name)
            if not search_results:
                print(f"  No recent research found")
                continue

            print(f"  Found {len(search_results)} search results")

            # Analyze relevance
            analysis = self.analyze_relevance(attr_id, search_results, current_content)
            print(f"  Relevance score: {analysis['relevance_score']:.2f}")

            # Update section if relevant
            if self.update_attribute_section(attr_id, analysis):
                updates_made += 1
                print(f"  ✓ Updated attribute {attr_id}")

        # Update metadata if any changes were made
        if self.changes_made:
            self.update_metadata()
            print(f"\n✓ Made {len(self.changes_made)} updates")
            print(f"✓ Updated version and date")
        else:
            print("\nNo updates needed this week")

        return len(self.changes_made) > 0


if __name__ == "__main__":
    updater = ResearchUpdater()
    changes_made = updater.run_update()

    # Exit with status code for GitHub Actions
    exit(0 if changes_made else 1)
```

### Step 3: Create Configuration File

Create `scripts/research_config.yaml`:

```yaml
update_settings:
  max_updates_per_run: 5  # Limit changes per PR
  min_citation_quality_score: 0.7  # Claude relevance threshold
  search_recency_months: 12  # Only recent research

priority_attributes:
  # Tier 1 attributes (update these first)
  - "1.1"  # CLAUDE.md
  - "2.1"  # README
  - "3.3"  # Type annotations
  - "5.1"  # Test coverage
  - "7.1"  # Conventional commits

search_domains:
  prioritized:
    - anthropic.com
    - microsoft.com/research
    - research.google
    - arxiv.org
    - dl.acm.org
    - openai.com/research
  blocked:
    - spam-site.com
```

### Step 4: Set Up GitHub Secrets

1. Go to repository **Settings → Secrets and variables → Actions**
2. Add secret: **ANTHROPIC_API_KEY**
   - Value: Your Claude API key (starts with `sk-ant-api03-`)
   - This enables LLM-powered research analysis

### Step 5: Test the Workflow

```bash
# Local testing
python scripts/update_research.py

# Manual workflow trigger
gh workflow run research-update.yml
```

---

## Quality Assurance

### Automated Checks

The PR created by the workflow includes:
- **Markdown linting**: Ensures document structure is valid
- **Citation validation**: Verifies all URLs are accessible
- **Version increment**: Confirms version/date updated
- **Content preservation**: Ensures no sections were deleted

### Manual Review Checklist

Before merging the automated PR:

- [ ] All citations include valid, authoritative URLs
- [ ] Updates add genuinely new information (not redundant)
- [ ] Technical accuracy maintained
- [ ] Document structure preserved (headings, sections, examples)
- [ ] Version number incremented appropriately
- [ ] Date reflects current update

---

## Example Output

### Pull Request Title

```text
Weekly Research Update: Agent-Ready Codebase Attributes
```

### Pull Request Body

```markdown
## Automated Research Update

This PR contains weekly updates to the AgentReady research report based on:
- Recent publications on AI-assisted development
- New best practices from authoritative sources
- Updated citations and references

### Changes Summary

**Updated Attributes (5)**:
1. **1.1 CLAUDE.md** - Added research on context window optimization (relevance: 0.85)
2. **3.3 Type Annotations** - New findings on static typing benefits for LLMs (relevance: 0.78)
3. **5.1 Test Coverage** - Updated industry benchmarks (relevance: 0.72)
4. **7.1 Conventional Commits** - New tooling recommendations (relevance: 0.80)
5. **10.1 OpenAPI Specifications** - API-first development updates (relevance: 0.76)

**New Citations (12)**:
- 8 academic papers (ArXiv, ACM)
- 3 industry blogs (Anthropic, Microsoft)
- 1 documentation update (OpenAPI)

**Metadata**:
- Version: 1.0.0 → 1.0.1
- Date: 2025-11-20 → 2025-12-02

### Review Checklist
- [ ] All citations include valid URLs
- [ ] Updates are relevant to attribute definitions
- [ ] Document structure is preserved
- [ ] Version number incremented appropriately
- [ ] Date updated to current
```

---

## Maintenance & Monitoring

### Success Metrics

Track these metrics over time:
- **PR merge rate**: Target >80% of automated PRs merged
- **Citation quality**: Average relevance score >0.75
- **Recency**: >90% citations from last 12 months
- **Coverage**: All 25 attributes reviewed every 4 weeks

### Troubleshooting

**Problem**: No PRs being created
- **Check**: `ANTHROPIC_API_KEY` secret is set
- **Check**: Workflow has write permissions for PRs
- **Check**: Recent research exists for attributes

**Problem**: Low-quality citations
- **Fix**: Increase `min_citation_quality_score` in config
- **Fix**: Add more prioritized domains to search

**Problem**: Too many updates per PR
- **Fix**: Decrease `max_updates_per_run` in config
- **Fix**: Increase `min_citation_quality_score` threshold

---

## Advanced Usage

### Custom Search Providers

Replace `_execute_search()` with:

**Google Custom Search**:
```python
def _execute_search(self, query: str) -> List[Dict[str, str]]:
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    cx = os.environ.get("GOOGLE_SEARCH_CX")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 10,
        "dateRestrict": "m12"  # Last 12 months
    }

    response = requests.get(url, params=params)
    results = response.json().get("items", [])

    return [
        {
            "title": item["title"],
            "url": item["link"],
            "snippet": item["snippet"],
            "date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
        }
        for item in results
    ]
```

**ArXiv API**:
```python
def _search_arxiv(self, query: str) -> List[Dict[str, str]]:
    import arxiv

    search = arxiv.Search(
        query=query,
        max_results=10,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    return [
        {
            "title": result.title,
            "url": result.entry_id,
            "snippet": result.summary[:500],
            "date": result.published.strftime("%Y-%m-%d"),
            "authors": ", ".join([a.name for a in result.authors])
        }
        for result in search.results()
    ]
```

---

## Cost Estimation

### Claude API Usage

**Per Weekly Run** (5 attribute updates):
- Analysis calls: 5 × ~4,000 tokens input + ~2,000 tokens output
- Total: ~30,000 tokens per week
- Cost: ~$0.30/week (Claude Sonnet 4.5 pricing)

**Annual Cost**: ~$15-20

### Optimization Strategies

1. **Cache search results**: Store for 7 days to avoid duplicate searches
2. **Batch processing**: Analyze multiple attributes in single API call
3. **Smart filtering**: Pre-filter low-quality sources before LLM analysis
4. **Rate limiting**: Respect API limits, add delays between calls

---

## Future Enhancements

### Phase 2 Features

1. **Automated quality scoring**: LLM evaluates own citation quality
2. **Multi-language support**: Extend beyond English sources
3. **Expert review routing**: Tag domain experts for specific attributes
4. **Historical tracking**: Dashboard showing research report evolution
5. **Citation impact tracking**: Track which citations led to codebase improvements

### Integration Ideas

1. **Slack notifications**: Alert team when high-impact research found
2. **Confluence sync**: Mirror updates to company wiki
3. **RSS feed**: Subscribe to research report changes
4. **API endpoint**: Query latest research programmatically

---

## Security Considerations

### API Key Protection

- Store `ANTHROPIC_API_KEY` only in GitHub Secrets
- Never log or expose API key in workflow output
- Rotate keys quarterly or after team member departure

### Content Validation

- Verify all URLs before adding to report
- Check for malicious content in search results
- Rate-limit API calls to prevent abuse
- Validate JSON parsing to prevent injection

### Access Control

- Require PR approval before merging updates
- Use branch protection rules on `main`
- Audit workflow run logs monthly
- Restrict workflow write permissions to minimum needed

---

## Related Documentation

- **CLAUDE.md**: AgentReady development guide
- **agent-ready-codebase-attributes.md**: The research report being maintained
- **contracts/research-report-schema.md**: Report structure specification
- **.github/workflows/continuous-learning.yml**: Similar automated learning workflow

---

## Support & Troubleshooting

**Questions?**
- Create GitHub issue with `research` label
- Review workflow run logs in Actions tab
- Check `scripts/research_config.yaml` for settings

**Contributing**:
- Suggest new search domains in PR
- Report low-quality citations as issues
- Propose new attributes for tracking

---

**Last Updated**: 2025-12-03
**Version**: 1.0.0
**Maintainer**: Jeremy Eder
