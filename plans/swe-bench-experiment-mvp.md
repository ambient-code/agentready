# AgentReady SWE-bench Experiment System - MVP Implementation

**Status**: Ready for implementation
**Timeline**: 5 days
**Goal**: Quantify AgentReady settings against SWE-bench baseline using both SWE-agent and Claude Code

---

## Context

AgentReady assesses repositories against 25 attributes that make codebases more effective for AI-assisted development. We need to validate which attributes actually improve AI agent performance by running controlled experiments with SWE-bench.

**SWE-bench** is an established benchmark with 2,294 real-world GitHub issues that AI agents attempt to solve. Results are measured as pass rate (% of issues successfully resolved).

**Experiment Design**: Run SWE-bench with different AgentReady configurations to measure which attributes provide the best ROI.

---

## MVP Scope

### What We're Building

1. **Agent Runners**: Execute SWE-bench tasks with SWE-agent or Claude Code
2. **Evaluation**: Score predictions using SWE-bench evaluation harness
3. **Comparison**: Compare results across configurations and agents
4. **Analysis**: Calculate correlation between AgentReady attributes and SWE-bench performance
5. **Visualization**: Generate interactive Plotly Express heatmap (HTML export)

### What's Out of Scope (Phase 2)

- Automatic git worktree management
- Parallel execution
- Real-time progress tracking
- Dash app with click drill-down
- Per-task analysis
- Statistical significance testing beyond Pearson correlation

---

## Implementation Plan

### Day 1-2: Agent Runners

**File**: `src/agentready/services/sweagent_runner.py`

```python
"""SWE-agent batch execution wrapper."""

import subprocess
import json
from pathlib import Path
from typing import Optional


class SWEAgentRunner:
    """Run SWE-bench tasks using SWE-agent."""

    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4.5",
        max_iterations: int = 30,
        config_file: str = "config/default.yaml"
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.config_file = config_file

    def run_batch(
        self,
        repo_path: Path,
        dataset: str = "lite",
        max_instances: Optional[int] = None,
        output_file: Path = None
    ) -> Path:
        """
        Run SWE-agent on SWE-bench tasks.

        Args:
            repo_path: Path to repository
            dataset: "lite" (300 tasks) or "full" (2,294 tasks)
            max_instances: Optional limit on number of tasks
            output_file: Where to save predictions.jsonl

        Returns:
            Path to predictions.jsonl file
        """
        if output_file is None:
            output_file = Path(f"predictions_sweagent_{dataset}.jsonl")

        cmd = [
            "sweagent", "run-batch",
            "--config", self.config_file,
            "--agent.model.name", self.model,
            "--instances.type", "swe_bench",
            "--instances.subset", dataset,
            "--repo_path", str(repo_path),
            "--output_dir", str(output_file.parent),
        ]

        if max_instances:
            cmd += ["--instances.slice", f":{max_instances}"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"SWE-agent failed: {result.stderr}")

        return output_file
```

**File**: `src/agentready/services/claudecode_runner.py`

```python
"""Claude Code headless mode execution wrapper."""

import subprocess
import json
from pathlib import Path
from typing import Optional


class ClaudeCodeRunner:
    """Run SWE-bench tasks using Claude Code headless mode."""

    def __init__(
        self,
        model: str = "claude-sonnet-4.5",
        max_turns: int = 30,
        timeout_minutes: int = 60
    ):
        self.model = model
        self.max_turns = max_turns
        self.timeout_minutes = timeout_minutes

    def _get_swebench_system_prompt(self) -> str:
        """System prompt for SWE-bench task execution."""
        return """
You are solving a GitHub issue from a real repository.

TOOLS AVAILABLE:
- Bash Tool: Execute shell commands (no internet access, persistent state)
- Edit Tool: View, create, edit files using string replacement

INSTRUCTIONS:
1. Analyze the problem statement thoroughly
2. Explore the codebase to understand context
3. Implement a solution that passes existing unit tests
4. Create a git commit with your changes when done
5. Generate a unified diff patch (git diff HEAD~1)

COMPLETION:
Signal task completion by running: git diff HEAD~1 > /tmp/solution.patch
"""

    def run_task(
        self,
        instance_id: str,
        problem_statement: str,
        repo_path: Path
    ) -> dict:
        """
        Run single SWE-bench task using Claude Code.

        Args:
            instance_id: SWE-bench instance ID (e.g., "django__django-12345")
            problem_statement: GitHub issue description
            repo_path: Path to repository

        Returns:
            Prediction dict with instance_id, model, and patch
        """
        cmd = [
            "claude",
            "--print",
            "--output-format", "json",
            "--allowedTools", "Bash(*)", "Edit(*)",
            "--append-system-prompt", self._get_swebench_system_prompt(),
            "--cwd", str(repo_path),
            problem_statement
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_minutes * 60
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Code failed: {result.stderr}")

        # Extract git patch from repository
        patch_result = subprocess.run(
            ["git", "diff", "HEAD~1"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        return {
            "instance_id": instance_id,
            "model_name_or_path": f"claude-code-{self.model}",
            "model_patch": patch_result.stdout
        }

    def run_batch(
        self,
        tasks_file: Path,
        output_file: Path = None
    ) -> Path:
        """
        Run batch of tasks.

        Args:
            tasks_file: JSONL file with tasks (instance_id, problem_statement, repo_path)
            output_file: Where to save predictions.jsonl

        Returns:
            Path to predictions.jsonl file
        """
        if output_file is None:
            output_file = Path("predictions_claudecode.jsonl")

        with open(tasks_file) as f:
            tasks = [json.loads(line) for line in f]

        predictions = []
        for task in tasks:
            try:
                prediction = self.run_task(
                    instance_id=task["instance_id"],
                    problem_statement=task["problem_statement"],
                    repo_path=Path(task["repo_path"])
                )
                predictions.append(prediction)
            except Exception as e:
                print(f"Error on {task['instance_id']}: {e}")
                continue

        # Save predictions in SWE-bench JSONL format
        with open(output_file, 'w') as f:
            for pred in predictions:
                f.write(json.dumps(pred) + '\n')

        return output_file
```

---

### Day 3: Evaluation & Comparison

**File**: `src/agentready/services/swebench_evaluator.py`

```python
"""SWE-bench evaluation harness wrapper."""

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """SWE-bench evaluation results."""
    dataset: str
    total_instances: int
    resolved_instances: int
    pass_rate: float
    predictions_file: Path
    results_file: Path


class SWEBenchEvaluator:
    """Run SWE-bench evaluation harness."""

    def evaluate(
        self,
        predictions_file: Path,
        dataset: str = "lite",
        output_dir: Path = None
    ) -> EvaluationResult:
        """
        Evaluate predictions using SWE-bench harness.

        Args:
            predictions_file: Path to predictions.jsonl
            dataset: "lite" or "full"
            output_dir: Where to save evaluation results

        Returns:
            EvaluationResult with scores
        """
        if output_dir is None:
            output_dir = predictions_file.parent / "evaluation"
        output_dir.mkdir(parents=True, exist_ok=True)

        dataset_name = f"princeton-nlp/SWE-bench_{dataset.capitalize()}"

        cmd = [
            "python", "-m", "swebench.harness.run_evaluation",
            "--dataset_name", dataset_name,
            "--predictions_path", str(predictions_file),
            "--max_workers", "8",
            "--cache_level", "env",
            "--run_id", predictions_file.stem,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=output_dir,
            timeout=14400  # 4 hour timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"Evaluation failed: {result.stderr}")

        # Parse results
        results_file = output_dir / "results.json"
        with open(results_file) as f:
            results = json.load(f)

        total = results["total_instances"]
        resolved = results["resolved_instances"]

        return EvaluationResult(
            dataset=dataset,
            total_instances=total,
            resolved_instances=resolved,
            pass_rate=resolved / total * 100,
            predictions_file=predictions_file,
            results_file=results_file
        )
```

**File**: `src/agentready/services/experiment_comparer.py`

```python
"""Compare experiment results."""

import json
from pathlib import Path
from typing import List
from dataclasses import dataclass, asdict


@dataclass
class ExperimentResult:
    """Single experiment result."""
    config_name: str
    agent: str
    agentready_score: float
    swebench_score: float
    solved: int
    total: int


class ExperimentComparer:
    """Compare multiple experiment results."""

    def load_result(self, result_file: Path) -> ExperimentResult:
        """Load single experiment result."""
        with open(result_file) as f:
            data = json.load(f)

        return ExperimentResult(**data)

    def compare(
        self,
        result_files: List[Path],
        output_file: Path = None
    ) -> dict:
        """
        Compare multiple experiment results.

        Args:
            result_files: List of result JSON files
            output_file: Where to save comparison

        Returns:
            Comparison dict with summary and deltas
        """
        results = [self.load_result(f) for f in result_files]

        # Find baseline (config_name="baseline")
        baseline = next((r for r in results if r.config_name == "baseline"), None)

        # Calculate deltas from baseline
        comparison = {
            "experiments": [asdict(r) for r in results],
            "summary": {},
            "deltas": {}
        }

        for result in results:
            key = f"{result.config_name}_{result.agent}"
            comparison["summary"][key] = result.swebench_score

            if baseline:
                baseline_score = baseline.swebench_score if result.agent == baseline.agent else None
                if baseline_score:
                    delta = result.swebench_score - baseline_score
                    comparison["deltas"][f"{key}_vs_baseline"] = delta

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(comparison, f, indent=2)

        return comparison
```

---

### Day 4: Attribute Analysis & Plotly Heatmap

**File**: `src/agentready/services/attribute_analyzer.py`

```python
"""Attribute correlation analysis with Plotly Express heatmap."""

import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from typing import List
from scipy.stats import pearsonr


class AttributeAnalyzer:
    """Analyze correlation between AgentReady attributes and SWE-bench performance."""

    def analyze(
        self,
        result_files: List[Path],
        output_file: Path = None,
        heatmap_file: Path = None
    ) -> dict:
        """
        Analyze correlation and generate heatmap.

        Args:
            result_files: List of experiment result JSON files
            output_file: Where to save analysis.json
            heatmap_file: Where to save heatmap.html

        Returns:
            Analysis dict with correlation and top attributes
        """
        # Load all results
        results = []
        for f in result_files:
            with open(f) as fp:
                results.append(json.load(fp))

        # Calculate overall correlation
        agentready_scores = [r["agentready_score"] for r in results]
        swebench_scores = [r["swebench_score"] for r in results]

        correlation, p_value = pearsonr(agentready_scores, swebench_scores)

        # Create DataFrame for heatmap
        heatmap_data = {}
        for result in results:
            config = result["config_name"]
            agent = result["agent"]
            score = result["swebench_score"]

            if config not in heatmap_data:
                heatmap_data[config] = {}
            heatmap_data[config][agent] = score

        df = pd.DataFrame(heatmap_data)

        # Generate interactive heatmap
        if heatmap_file:
            self._create_heatmap(df, heatmap_file)

        # Prepare analysis output
        analysis = {
            "correlation": {
                "overall": round(correlation, 3),
                "p_value": round(p_value, 6)
            },
            "top_attributes": self._rank_attributes(results),
            "heatmap_path": str(heatmap_file) if heatmap_file else None
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)

        return analysis

    def _create_heatmap(self, df: pd.DataFrame, output_path: Path):
        """Create interactive Plotly Express heatmap."""

        # Calculate deltas from baseline
        if "baseline" in df.columns:
            baseline = df["baseline"].values
            delta_df = df.copy()
            for col in df.columns:
                delta_df[col] = df[col] - baseline
        else:
            delta_df = df.copy()

        # Transpose: configs as rows, agents as columns
        df_t = df.T
        delta_t = delta_df.T

        # Create heatmap
        fig = px.imshow(
            df_t,
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=45,
            labels=dict(x="Agent", y="Configuration", color="Pass Rate (%)"),
            text_auto='.1f',
            aspect="auto",
            zmin=35,
            zmax=55
        )

        # Add custom hover with deltas
        hover_text = []
        for i, config in enumerate(df_t.index):
            row_text = []
            for j, agent in enumerate(df_t.columns):
                score = df_t.iloc[i, j]
                delta = delta_t.iloc[i, j]
                text = (
                    f"<b>Agent:</b> {agent}<br>"
                    f"<b>Config:</b> {config}<br>"
                    f"<b>Score:</b> {score:.1f}%<br>"
                    f"<b>Delta from baseline:</b> {delta:+.1f}pp"
                )
                row_text.append(text)
            hover_text.append(row_text)

        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text
        )

        # Customize layout
        fig.update_layout(
            title='SWE-bench Performance: AgentReady Configurations',
            xaxis_title='Agent',
            yaxis_title='Configuration',
            width=900,
            height=600,
            font=dict(size=12),
        )

        # Save standalone HTML
        fig.write_html(output_path)
        print(f"✓ Interactive heatmap saved to: {output_path}")

    def _rank_attributes(self, results: List[dict]) -> List[dict]:
        """Rank attributes by impact (simplified for MVP)."""
        # This is a placeholder - would need per-attribute data
        # For MVP, just return top attributes based on config names

        config_impacts = {}
        baseline_scores = {}

        for result in results:
            agent = result["agent"]
            config = result["config_name"]
            score = result["swebench_score"]

            if config == "baseline":
                baseline_scores[agent] = score
            elif agent in baseline_scores:
                delta = score - baseline_scores[agent]
                if config not in config_impacts:
                    config_impacts[config] = []
                config_impacts[config].append(delta)

        # Calculate average improvement per config
        ranked = []
        for config, deltas in config_impacts.items():
            avg_delta = sum(deltas) / len(deltas)
            ranked.append({
                "config": config,
                "avg_improvement": round(avg_delta, 1)
            })

        ranked.sort(key=lambda x: x["avg_improvement"], reverse=True)
        return ranked[:5]
```

---

### Day 5: CLI & Automation

**File**: `src/agentready/cli/experiment.py`

```python
"""Experiment CLI commands."""

import click
from pathlib import Path
from ..services.sweagent_runner import SWEAgentRunner
from ..services.claudecode_runner import ClaudeCodeRunner
from ..services.swebench_evaluator import SWEBenchEvaluator
from ..services.experiment_comparer import ExperimentComparer
from ..services.attribute_analyzer import AttributeAnalyzer


@click.group()
def experiment():
    """SWE-bench experiment commands."""
    pass


@experiment.command()
@click.option("--agent", type=click.Choice(["sweagent", "claudecode"]), required=True)
@click.option("--repo-path", type=Path, required=True)
@click.option("--dataset", default="lite", help="lite or full")
@click.option("--output", type=Path, required=True, help="Output predictions.jsonl")
def run_agent(agent, repo_path, dataset, output):
    """Run single agent on SWE-bench."""

    if agent == "sweagent":
        runner = SWEAgentRunner()
        runner.run_batch(repo_path, dataset, output_file=output)
    else:
        # For Claude Code, need tasks file
        click.echo("Claude Code requires tasks file. Use run-batch instead.")
        raise SystemExit(1)

    click.echo(f"✓ Predictions saved to: {output}")


@experiment.command()
@click.option("--predictions", type=Path, required=True)
@click.option("--dataset", default="lite")
@click.option("--output", type=Path, required=True)
def evaluate(predictions, dataset, output):
    """Evaluate predictions using SWE-bench harness."""

    evaluator = SWEBenchEvaluator()
    result = evaluator.evaluate(predictions, dataset)

    # Save result
    import json
    with open(output, 'w') as f:
        json.dump({
            "dataset": result.dataset,
            "total": result.total_instances,
            "solved": result.resolved_instances,
            "pass_rate": result.pass_rate
        }, f, indent=2)

    click.echo(f"✓ Pass rate: {result.pass_rate:.1f}%")
    click.echo(f"✓ Results saved to: {output}")


@experiment.command()
@click.argument("result_files", nargs=-1, type=Path)
@click.option("--output", type=Path, default="comparison.json")
def compare(result_files, output):
    """Compare multiple experiment results."""

    comparer = ExperimentComparer()
    comparison = comparer.compare(list(result_files), output)

    click.echo("Comparison Summary:")
    for key, score in comparison["summary"].items():
        click.echo(f"  {key}: {score:.1f}%")

    click.echo(f"\n✓ Comparison saved to: {output}")


@experiment.command()
@click.option("--results-dir", type=Path, required=True)
@click.option("--output", type=Path, default="analysis.json")
@click.option("--heatmap", type=Path, default="heatmap.html")
def analyze(results_dir, output, heatmap):
    """Analyze correlation and generate heatmap."""

    result_files = list(results_dir.glob("*.json"))

    analyzer = AttributeAnalyzer()
    analysis = analyzer.analyze(result_files, output, heatmap)

    click.echo(f"Correlation: r={analysis['correlation']['overall']:.2f} (p={analysis['correlation']['p_value']:.4f})")
    click.echo(f"\n✓ Analysis saved to: {output}")
    click.echo(f"✓ Heatmap saved to: {heatmap}")
```

---

## Configuration Templates

**File**: `experiments/configs/baseline.yaml`

```yaml
name: baseline
description: "No AgentReady changes (control)"
agentready_changes:
  enabled: false
```

**File**: `experiments/configs/claude-md.yaml`

```yaml
name: claude-md
description: "CLAUDE.md only (Tier 1 essential)"
agentready_changes:
  align:
    enabled: true
    attributes:
      - claude_md_file
```

**File**: `experiments/configs/types-docs.yaml`

```yaml
name: types-docs
description: "Type annotations + inline documentation"
agentready_changes:
  align:
    enabled: true
    attributes:
      - type_annotations
      - inline_documentation
```

**File**: `experiments/configs/tier1.yaml`

```yaml
name: tier1-attrs
description: "All Tier 1 attributes"
agentready_changes:
  align:
    enabled: true
    attributes:
      - claude_md_file
      - readme_structure
      - type_annotations
      - standard_layout
      - lock_files
```

**File**: `experiments/configs/full-bootstrap.yaml`

```yaml
name: full-bootstrap
description: "All AgentReady best practices"
agentready_changes:
  bootstrap: true
```

---

## Usage Workflow

### Manual Workflow (Step by Step)

```bash
# 1. Prepare repositories
mkdir -p experiments/repos
cp -r /path/to/repo experiments/repos/baseline
cp -r /path/to/repo experiments/repos/claude-md

# 2. Apply AgentReady changes
cd experiments/repos/claude-md
agentready align . --attributes claude_md_file
cd ../../..

# 3. Run agents
agentready experiment run-agent sweagent \
  --repo-path experiments/repos/baseline \
  --dataset lite \
  --output experiments/results/baseline_sweagent.jsonl

agentready experiment run-agent sweagent \
  --repo-path experiments/repos/claude-md \
  --dataset lite \
  --output experiments/results/claudemd_sweagent.jsonl

# 4. Evaluate
agentready experiment evaluate \
  --predictions experiments/results/baseline_sweagent.jsonl \
  --output experiments/results/baseline_sweagent.json

agentready experiment evaluate \
  --predictions experiments/results/claudemd_sweagent.jsonl \
  --output experiments/results/claudemd_sweagent.json

# 5. Analyze
agentready experiment analyze \
  --results-dir experiments/results/ \
  --output experiments/analysis.json \
  --heatmap experiments/heatmap.html

# 6. Open heatmap
open experiments/heatmap.html
```

---

## Data Models

**ExperimentResult JSON**:
```json
{
  "config_name": "claude-md",
  "agent": "sweagent",
  "agentready_score": 78.3,
  "swebench_score": 45.2,
  "solved": 136,
  "total": 300
}
```

**Analysis JSON**:
```json
{
  "correlation": {
    "overall": 0.87,
    "p_value": 0.0001
  },
  "top_attributes": [
    {"config": "claude-md", "avg_improvement": 7.0},
    {"config": "types-docs", "avg_improvement": 10.5}
  ],
  "heatmap_path": "heatmap.html"
}
```

---

## Dependencies

Install with:
```bash
uv pip install swebench sweagent plotly pandas scipy
```

Required packages:
- `swebench` - Evaluation harness
- `sweagent` - Agent execution
- `plotly` - Interactive visualizations
- `pandas` - DataFrame manipulation
- `scipy` - Statistical correlation

---

## Testing Validation

**Manual tests before production**:

1. Run SWE-agent on 2-3 SWE-bench tasks
2. Verify predictions.jsonl format
3. Run evaluation on predictions
4. Verify scores are calculated
5. Generate heatmap with sample data
6. Verify HTML export works

---

## Success Criteria

- ✅ Can run SWE-bench Lite with both agents
- ✅ Can evaluate predictions and get pass rates
- ✅ Can compare 5 configs × 2 agents = 10 experiments
- ✅ Can generate correlation analysis
- ✅ Can generate interactive Plotly Express heatmap
- ✅ Can export standalone HTML for sharing
- ✅ Can identify top-performing AgentReady attributes

---

## Implementation Notes

### Code Patterns

**Use dataclasses for models**:
```python
from dataclasses import dataclass

@dataclass
class ExperimentResult:
    config_name: str
    agent: str
    swebench_score: float
```

**Use subprocess for external tools**:
```python
result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
if result.returncode != 0:
    raise RuntimeError(f"Command failed: {result.stderr}")
```

**Use Click for CLI**:
```python
@click.command()
@click.option("--output", type=Path, required=True)
def analyze(output):
    # Implementation
    pass
```

**Use Plotly Express for heatmaps**:
```python
import plotly.express as px

fig = px.imshow(
    df.T,
    color_continuous_scale='RdYlGn',
    text_auto='.1f'
)
fig.write_html("heatmap.html")
```

### Error Handling

**Graceful failures**:
```python
try:
    prediction = run_task(instance_id, problem, repo_path)
except Exception as e:
    print(f"Error on {instance_id}: {e}")
    continue  # Continue with next task
```

**Timeouts**:
```python
subprocess.run(cmd, timeout=3600)  # 1 hour timeout
```

---

## Expected Output

**Console output**:
```
Correlation: r=0.87 (p=0.0001)

✓ Analysis saved to: analysis.json
✓ Heatmap saved to: heatmap.html
```

**heatmap.html**: Interactive visualization with:
- Hover tooltips showing scores and deltas
- Zoom/pan capability
- RdYlGn colormap
- Standalone HTML (shareable without Python)

---

## Timeline

- **Day 1**: SWE-agent runner (~100 LOC)
- **Day 2**: Claude Code runner (~150 LOC)
- **Day 3**: Evaluator + Comparer (~200 LOC)
- **Day 4**: Analyzer + Plotly heatmap (~200 LOC)
- **Day 5**: CLI + configs + docs (~200 LOC)

**Total**: ~850 LOC, 5 days

---

## Next Steps After MVP

Once MVP is working:

1. **Phase 2 Features**:
   - Automatic git worktree management
   - Parallel execution (run multiple experiments concurrently)
   - Dash app with click drill-down
   - Per-task analysis (which tasks benefit most from which attributes)

2. **Research**:
   - Run full experiment suite (5 configs × 2 agents on SWE-bench Lite)
   - Analyze correlation
   - Publish findings internally at Red Hat
   - Use results to refine AgentReady attribute weights

3. **Integration**:
   - Add to AgentReady CI/CD
   - Automated regression testing (new AgentReady version → re-run experiments)
   - Dashboard for tracking experiments over time

---

**This prompt is self-contained and ready for a fresh agent to implement the MVP without additional context.**
