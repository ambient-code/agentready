"""Experiment CLI commands."""

from pathlib import Path

import click

from ..services.attribute_analyzer import AttributeAnalyzer
from ..services.experiment_comparer import ExperimentComparer
from ..services.sweagent_runner import SWEAgentRunner
from ..services.swebench_evaluator import SWEBenchEvaluator


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

    with open(output, "w") as f:
        json.dump(
            {
                "dataset": result.dataset,
                "total": result.total_instances,
                "solved": result.resolved_instances,
                "pass_rate": result.pass_rate,
            },
            f,
            indent=2,
        )

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

    click.echo(
        f"Correlation: r={analysis['correlation']['overall']:.2f} (p={analysis['correlation']['p_value']:.4f})"
    )
    click.echo(f"\n✓ Analysis saved to: {output}")
    click.echo(f"✓ Heatmap saved to: {heatmap}")
