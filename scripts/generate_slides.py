#!/usr/bin/env python3
"""Generate reveal.js presentation with proper slide design

Transforms demo content into clean, visual presentation slides:
- One key point per slide
- Minimal text, maximum impact
- Visual hierarchy with proper formatting
- Speaker notes for details
"""

from pathlib import Path
from typing import Dict, List

import click
from jinja2 import Environment, FileSystemLoader


def create_presentation_slides() -> List[Dict[str, str]]:
    """Create properly designed presentation slides.

    Returns slides optimized for presentation, not just content dump.
    """
    return [
        # Title Slide
        {
            "type": "title",
            "title": "Terminal-Bench Eval Harness",
            "subtitle": "Empirically Measuring AgentReady Impact",
            "author": "Jeremy Eder",
            "date": "2025-12-07",
        },
        # Problem Statement
        {
            "type": "statement",
            "title": "The Question",
            "content": """
**Do AgentReady recommendations actually improve agentic development performance?**

<div class="fragment">We needed proof.</div>
            """,
            "notes": "AgentReady provides 25 assessors with recommendations. But do they work? We built an eval harness to find out.",
        },
        # Solution Overview
        {
            "type": "content",
            "title": "The Approach",
            "content": """
# A/B Testing at Scale

- **Baseline**: Measure performance before fixes
- **Remediate**: Apply single assessor fixes
- **Re-measure**: Run benchmark again
- **Compare**: Calculate statistical significance
            """,
            "notes": "Systematic empirical testing - test each assessor independently",
        },
        # Architecture - Visual
        {
            "type": "diagram",
            "title": "Eval Harness Architecture",
            "content": """
```mermaid
graph LR
    A[Repository] -->|Run 3x| B[Baseline: 58.35]
    B --> C[Apply Fixes]
    C -->|Run 3x| D[Post-Fix Score]
    D --> E{Compare}
    E -->|p-value + Cohen's d| F[Statistical Significance]

    style B fill:#e1f5ff
    style D fill:#d4edda
    style F fill:#fff3cd
```
            """,
            "notes": "Four phases: baseline, fix, re-measure, analyze with statistics",
        },
        # Demo Results - Big Numbers
        {
            "type": "big-stat",
            "title": "Demo Results",
            "stat": "58.35",
            "label": "Baseline Score",
            "sublabel": "(3 iterations, σ=0.00)",
            "notes": "Ran eval harness on AgentReady repository itself",
        },
        # Why Zero Delta
        {
            "type": "content",
            "title": "Why +0.00 Delta?",
            "content": """
### AgentReady Already Passes! ✅

Tested 5 Tier 1 assessors:
- Type Annotations
- CLAUDE.md File
- Standard Layout
- Lock Files (intentionally excluded)
- README Structure

**All already compliant** → No fixes needed
            """,
            "notes": "This proves the system works - it correctly identifies repos that already follow best practices",
        },
        # Expected Results
        {
            "type": "content",
            "title": "Expected Results (Typical Repo)",
            "content": """
| Assessor | Delta | Significant? |
|----------|-------|--------------|
| CLAUDE.md | **+8.7** | ✅ Yes |
| README | **+5.2** | ✅ Yes |
| Layout | **+3.4** | ✅ Yes |
| Type Hints | +2.1 | ❌ No |
| Lock Files | +1.8 | ❌ No |

*Hypothetical results on non-compliant repository*
            """,
            "notes": "What we expect to see when testing repos that need improvements",
        },
        # Statistical Rigor
        {
            "type": "content",
            "title": "Statistical Significance",
            "content": """
## Two-Factor Test

**BOTH required for significance:**

1. **P-value < 0.05**
   *95% confidence not due to chance*

2. **|Cohen's d| > 0.2**
   *Meaningful effect size*

<div class="fragment">Prevents false positives from noise</div>
            """,
            "notes": 'We use proper statistics - not just "looks better"',
        },
        # File Structure
        {
            "type": "content",
            "title": "Generated Artifacts",
            "content": """
```
.agentready/eval_harness/
├── baseline/summary.json
├── assessors/
│   └── claude_md_file/
│       ├── impact.json ← Delta, p-value, effect size
│       └── run_*.json
└── summary.json ← Ranked results

docs/_data/tbench/ ← Dashboard data
```
            """,
            "notes": "All results stored as JSON for reproducibility and dashboard generation",
        },
        # Dashboard
        {
            "type": "content",
            "title": "Interactive Dashboard",
            "content": """
## GitHub Pages Visualization

- **Overview Cards**: Total tested, significant improvements
- **Tier Impact Chart**: Chart.js bar chart by tier
- **Top Performers**: Ranked by delta score
- **Complete Results**: Sortable table with all metrics

👉 *Live at `/agentready/tbench`*
            """,
            "notes": "Jekyll + Chart.js for interactive data exploration",
        },
        # Testing Status
        {
            "type": "big-stat",
            "title": "Test Coverage",
            "stat": "56/56",
            "label": "Tests Passing",
            "sublabel": "CLI • Models • Services • Integration",
            "notes": "6 CLI + 13 model + 32 service + 5 integration tests",
        },
        # Commands
        {
            "type": "code",
            "title": "Quick Start",
            "content": """
```bash
# 1. Establish baseline
agentready eval-harness baseline . --iterations 3

# 2. Test single assessor
agentready eval-harness test-assessor \\
  --assessor-id claude_md_file --iterations 3

# 3. Aggregate all results
agentready eval-harness summarize

# 4. Generate dashboard
agentready eval-harness dashboard
```
            """,
            "notes": "Four simple commands - takes about 5 minutes for full workflow",
        },
        # Current Status
        {
            "type": "content",
            "title": "Implementation Status",
            "content": """
### Phase 1 (MVP): ✅ Complete

- Mocked Terminal-Bench integration
- Statistical analysis (p-values, Cohen's d)
- CLI with 5 commands
- Dashboard with Chart.js
- 56/56 tests passing

### Phase 2: 🔜 Next

- **Real Terminal-Bench integration**
- Harbor framework client
- Actual benchmark submissions
            """,
            "notes": "Working system with mocked benchmarks - ready for real integration",
        },
        # Key Insight
        {
            "type": "statement",
            "title": "Key Insight",
            "content": """
**Empirical validation > theoretical claims**

We can now **prove** which assessors
have the biggest impact on agentic
development performance.

<div class="fragment">**Data-driven decisions for AI-assisted development**</div>
            """,
            "notes": "This is the value prop - move from opinions to evidence",
        },
        # Closing
        {
            "type": "closing",
            "title": "Thank You",
            "content": """
### Terminal-Bench Eval Harness

**Empirically measure AgentReady impact**

---

📊 **Dashboard**: `/agentready/tbench`
📖 **Docs**: `docs/tbench/methodology.md`
🧪 **Tests**: `pytest tests/`

---

**Questions?**
            """,
            "notes": "Links to more information and next steps",
        },
    ]


@click.command()
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("docs/demos/slides.html"),
    help="Output HTML file path",
)
@click.option("--verbose", is_flag=True, help="Verbose output")
def generate_slides(output: Path, verbose: bool):
    """Generate reveal.js presentation with proper slide design."""

    if verbose:
        click.echo("🎨 Creating presentation slides...")

    # Get properly designed slides
    slides = create_presentation_slides()

    if verbose:
        click.echo(f"Generated {len(slides)} slides")

    # Load template
    template_dir = Path("src/agentready/templates")
    if not template_dir.exists():
        click.secho(f"Template directory not found: {template_dir}", fg="red", err=True)
        raise click.Abort()

    env = Environment(loader=FileSystemLoader(str(template_dir)))

    try:
        tmpl = env.get_template("slides.html.j2")
    except Exception as e:
        click.secho(f"Failed to load template: {e}", fg="red", err=True)
        raise click.Abort()

    if verbose:
        click.echo("Loaded template: slides.html.j2")

    # Render
    html = tmpl.render(title="Terminal-Bench Eval Harness", slides=slides)

    # Write output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)

    # Success
    file_size = len(html)
    click.secho(
        f"✅ Generated {output} ({file_size:,} bytes, {len(slides)} slides)", fg="green"
    )


if __name__ == "__main__":
    generate_slides()
