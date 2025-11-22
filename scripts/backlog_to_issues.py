#!/usr/bin/env python3
"""
Script to convert BACKLOG.md items into coldstart prompts.

This script:
1. Parses BACKLOG.md to extract individual items
2. Generates comprehensive coldstart prompts for each item
3. Saves prompts as markdown files in .github/coldstart-prompts/
4. Optionally creates GitHub issues via gh CLI (if --create-issues flag set)
5. Pauses after first item for user review
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class BacklogItem:
    """Represents a single backlog item."""

    def __init__(self, title: str, priority: str, content: str, section_start: int):
        self.title = title
        self.priority = priority
        self.content = content
        self.section_start = section_start

    def __repr__(self):
        return f"BacklogItem(title={self.title}, priority={self.priority})"


def parse_backlog(backlog_path: Path) -> List[BacklogItem]:
    """Parse BACKLOG.md and extract all items."""

    with open(backlog_path, "r") as f:
        content = f.read()

    items = []

    # Split into sections by ###
    sections = re.split(r"\n### ", content)

    for i, section in enumerate(sections[1:], 1):  # Skip first section (header)
        lines = section.split("\n")
        title = lines[0].strip()

        # Find priority in next few lines
        priority = "P4"  # default
        for line in lines[1:5]:
            if match := re.search(r"\*\*Priority\*\*:\s*(P\d)", line):
                priority = match.group(1)
                break

        # Get full content until next ### or end
        full_content = "\n".join(lines)

        items.append(
            BacklogItem(
                title=title, priority=priority, content=full_content, section_start=i
            )
        )

    return items


def generate_coldstart_prompt(item: BacklogItem, repo_context: Dict) -> str:
    """Generate a comprehensive coldstart prompt for implementing the backlog item."""

    prompt = f"""# Coldstart Implementation Prompt: {item.title}

**Priority**: {item.priority}
**Repository**: agentready (https://github.com/{repo_context['owner']}/{repo_context['repo']})
**Branch Strategy**: Create feature branch from main

---

## Context

You are implementing a feature for AgentReady, a repository quality assessment tool for AI-assisted development.

### Repository Structure
```
agentready/
├── src/agentready/          # Source code
│   ├── models/              # Data models
│   ├── services/            # Scanner orchestration
│   ├── assessors/           # Attribute assessments
│   ├── reporters/           # Report generation (HTML, Markdown, JSON)
│   ├── templates/           # Jinja2 templates
│   └── cli/                 # Click-based CLI
├── tests/                   # Test suite (unit + integration)
├── examples/                # Example reports
└── specs/                   # Feature specifications
```

### Key Technologies
- Python 3.11+
- Click (CLI framework)
- Jinja2 (templating)
- Pytest (testing)
- Black, isort, ruff (code quality)

### Development Workflow
1. Create feature branch: `git checkout -b NNN-feature-name`
2. Implement changes with tests
3. Run linters: `black . && isort . && ruff check .`
4. Run tests: `pytest`
5. Commit with conventional commits
6. Create PR to main

---

## Feature Requirements

{item.content}

---

## Implementation Checklist

Before you begin:
- [ ] Read CLAUDE.md for project context
- [ ] Review existing similar features (if applicable)
- [ ] Understand the data model (src/agentready/models/)
- [ ] Check acceptance criteria in feature description

Implementation steps:
- [ ] Create feature branch
- [ ] Implement core functionality
- [ ] Add unit tests (target >80% coverage)
- [ ] Add integration tests (if applicable)
- [ ] Run linters and fix any issues
- [ ] Update documentation (README.md, CLAUDE.md if needed)
- [ ] Self-test the feature end-to-end
- [ ] Create PR with descriptive title and body

Code quality requirements:
- [ ] All code formatted with black (88 char lines)
- [ ] Imports sorted with isort
- [ ] No ruff violations
- [ ] All tests passing
- [ ] Type hints where appropriate
- [ ] Docstrings for public APIs

---

## Key Files to Review

Based on this feature, you should review:
- `src/agentready/models/` - Understand Assessment, Finding, Attribute models
- `src/agentready/services/scanner.py` - Scanner orchestration
- `src/agentready/assessors/base.py` - BaseAssessor pattern
- `src/agentready/reporters/` - Report generation
- `CLAUDE.md` - Project overview and guidelines
- `BACKLOG.md` - Full context of this feature

---

## Testing Strategy

For this feature, ensure:
1. **Unit tests** for core logic (80%+ coverage)
2. **Integration tests** for end-to-end workflows
3. **Edge case tests** (empty inputs, missing files, errors)
4. **Error handling tests** (graceful degradation)

Run tests:
```bash
# All tests
pytest

# With coverage
pytest --cov=src/agentready --cov-report=html

# Specific test file
pytest tests/unit/test_feature.py -v
```

---

## Success Criteria

This feature is complete when:
- ✅ All acceptance criteria from feature description are met
- ✅ Tests passing with >80% coverage for new code
- ✅ All linters passing (black, isort, ruff)
- ✅ Documentation updated
- ✅ PR created with clear description
- ✅ Self-tested end-to-end

---

## Questions to Clarify (if needed)

If anything is unclear during implementation:
1. Check CLAUDE.md for project patterns
2. Review similar existing features
3. Ask for clarification in PR comments
4. Reference the original backlog item

---

## Getting Started

```bash
# Clone and setup
git clone https://github.com/{repo_context['owner']}/{repo_context['repo']}.git
cd agentready

# Create virtual environment
uv venv && source .venv/bin/activate

# Install dependencies
uv pip install -e .
uv pip install pytest black isort ruff

# Create feature branch
git checkout -b {item.section_start:03d}-{item.title.lower().replace(' ', '-')[:50]}

# Start implementing!
```

---

**Note**: This is a coldstart prompt. You have all context needed to implement this feature independently. Read the linked files, follow the patterns, and deliver high-quality code with tests.
"""

    return prompt


def create_github_issue(
    item: BacklogItem, prompt: str, repo_context: Dict, dry_run: bool = False
) -> Optional[str]:
    """Create GitHub issue via gh CLI and attach coldstart prompt as comment."""

    # Prepare issue title
    issue_title = f"[{item.priority}] {item.title}"

    # Prepare issue body (extract description and requirements)
    # Get content up to "Implementation" section or similar
    body_parts = []
    body_parts.append(f"**Priority**: {item.priority}\n")

    # Extract description (first paragraph after Priority)
    lines = item.content.split("\n")
    in_description = False
    description_lines = []

    for line in lines:
        if "**Description**:" in line:
            in_description = True
            continue
        if in_description:
            if line.startswith("**") and ":" in line:
                break
            description_lines.append(line)

    if description_lines:
        body_parts.append("## Description\n")
        body_parts.append("\n".join(description_lines))

    # Add link to full context
    body_parts.append("\n\n## Full Context\n")
    body_parts.append(
        f"See [BACKLOG.md](https://github.com/{repo_context['owner']}/{repo_context['repo']}/blob/main/BACKLOG.md) for complete requirements.\n"
    )

    # Add acceptance criteria if present
    if "**Acceptance Criteria**:" in item.content:
        criteria_start = item.content.find("**Acceptance Criteria**:")
        criteria_section = item.content[criteria_start : criteria_start + 1000]
        body_parts.append("\n## Acceptance Criteria\n")
        body_parts.append(criteria_section.split("\n\n")[0])

    issue_body = "\n".join(body_parts)

    # Determine labels
    labels = [f"priority:{item.priority.lower()}"]

    # Add category labels based on title/content
    if "security" in item.title.lower() or "xss" in item.content.lower():
        labels.append("security")
    if "bug" in item.title.lower() or "fix" in item.title.lower():
        labels.append("bug")
    else:
        labels.append("enhancement")
    if "test" in item.title.lower():
        labels.append("testing")
    if "github" in item.title.lower():
        labels.append("github-integration")
    if "report" in item.title.lower():
        labels.append("reporting")

    labels_str = ",".join(labels)

    if dry_run:
        print(f"\n{'='*80}")
        print("DRY RUN: Would create issue:")
        print(f"Title: {issue_title}")
        print(f"Labels: {labels_str}")
        print(f"Body preview:\n{issue_body[:500]}...")
        print("\nColdstart prompt would be added as first comment")
        print(f"{'='*80}\n")
        return None

    # Create issue using gh CLI
    try:
        # Create the issue
        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                issue_title,
                "--body",
                issue_body,
                "--label",
                labels_str,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        issue_url = result.stdout.strip()
        print(f"✅ Created issue: {issue_url}")

        # Extract issue number from URL
        issue_number = issue_url.split("/")[-1]

        # Add coldstart prompt as first comment
        subprocess.run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                f"## 🤖 Coldstart Implementation Prompt\n\n{prompt}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Added coldstart prompt as comment")

        return issue_url

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {e.stderr}")
        return None


def get_repo_context() -> Dict:
    """Get repository context (owner, repo name) from git remote."""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "owner,name"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return {"owner": data["owner"]["login"], "repo": data["name"]}
    except Exception:
        # No git remote - ask user or use default
        print("⚠️  Warning: Could not get repo context from git remote")
        print("    This is expected if repository not yet on GitHub")
        print("    Using default values for now\n")
        # For agentready, we know the intended location
        return {"owner": "redhat", "repo": "agentready"}


def save_prompt_to_file(
    item: BacklogItem, prompt: str, output_dir: Path, item_number: int
) -> Path:
    """Save coldstart prompt to markdown file."""

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from item number and title
    safe_title = re.sub(r"[^\w\s-]", "", item.title.lower())
    safe_title = re.sub(r"[-\s]+", "-", safe_title)[:50]
    filename = f"{item_number:02d}-{safe_title}.md"

    filepath = output_dir / filename

    # Write prompt to file
    with open(filepath, "w") as f:
        f.write(prompt)

    return filepath


def main():
    """Main script execution."""

    # Parse command line args
    create_issues = "--create-issues" in sys.argv
    process_all = "--all" in sys.argv

    # Get repository root
    repo_root = Path(__file__).parent.parent
    backlog_path = repo_root / "BACKLOG.md"

    if not backlog_path.exists():
        print(f"❌ BACKLOG.md not found at {backlog_path}")
        sys.exit(1)

    # Create output directory
    output_dir = repo_root / ".github" / "coldstart-prompts"

    # Get repo context
    repo_context = get_repo_context()
    print(f"📦 Repository: {repo_context['owner']}/{repo_context['repo']}\n")

    # Parse backlog
    print("📖 Parsing BACKLOG.md...")
    items = parse_backlog(backlog_path)
    print(f"Found {len(items)} backlog items\n")

    # Show summary
    print("Backlog Items:")
    for i, item in enumerate(items, 1):
        print(f"  {i:2d}. [{item.priority}] {item.title}")
    print()

    # Process first item (or all if --all flag)
    items_to_process = items if process_all else [items[0]]

    for idx, item in enumerate(items_to_process, 1):
        print(f"{'='*80}")
        print(f"Processing item {idx}/{len(items_to_process)}: {item.title}")
        print(f"{'='*80}\n")

        # Generate coldstart prompt
        print("🤖 Generating coldstart prompt...")
        prompt = generate_coldstart_prompt(item, repo_context)
        print(f"✅ Generated {len(prompt)} character prompt\n")

        # Save to file
        print("💾 Saving prompt to file...")
        filepath = save_prompt_to_file(item, prompt, output_dir, item.section_start)
        print(f"✅ Saved to: {filepath}\n")

        # Optionally create GitHub issue
        if create_issues:
            print("🐙 Creating GitHub issue...")
            issue_url = create_github_issue(item, prompt, repo_context, dry_run=False)
            if issue_url:
                print(f"✅ Created issue: {issue_url}\n")
            else:
                print("❌ Failed to create issue\n")

        # Pause after first item unless --all specified
        if not process_all and idx == 1:
            print(f"\n{'='*80}")
            print("✅ FIRST PROMPT GENERATED")
            print(f"{'='*80}\n")
            print(f"Saved to: {filepath}")
            print("\nPlease review the prompt file.")
            print(
                f"Once approved, run with --all to process remaining {len(items) - 1} items:"
            )
            print("  python scripts/backlog_to_issues.py --all")
            if not create_issues:
                print("\nTo also create GitHub issues, add --create-issues flag:")
                print("  python scripts/backlog_to_issues.py --all --create-issues")
            return

    # All items processed
    print(f"\n{'='*80}")
    print(f"✅ PROCESSED {len(items_to_process)} ITEMS")
    print(f"{'='*80}\n")
    print(f"Coldstart prompts saved to: {output_dir}/")
    if create_issues:
        print("GitHub issues created (check repository)")
    print("\nNext steps:")
    print(f"  1. Review generated prompts in {output_dir}/")
    print("  2. Create GitHub issues manually, or run with --create-issues")
    print("  3. Start implementing features using the coldstart prompts!")


if __name__ == "__main__":
    main()
