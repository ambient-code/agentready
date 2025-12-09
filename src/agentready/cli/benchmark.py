"""Benchmark command for running agent coding evaluations."""

import os
import tempfile
from pathlib import Path

import click

from ..services.eval_harness.harbor_config import HarborConfig
from ..services.eval_harness.tbench_runner import _real_tbench_result


@click.command()
@click.argument("repository", type=click.Path(exists=True), required=False, default=".")
@click.option(
    "--harness",
    type=click.Choice(["tbench"]),
    default="tbench",
    help="Evaluation harness to use (tbench=Terminal-Bench)",
)
@click.option(
    "--subset",
    type=str,
    default=None,
    help="Benchmark subset (tbench: smoketest/full)",
)
@click.option(
    "--model",
    type=click.Choice(["claude-haiku-4-5", "claude-sonnet-4-5"]),
    default="claude-haiku-4-5",
    help="Model for evaluation",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--timeout",
    type=int,
    default=3600,
    help="Timeout in seconds (default: 3600)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory for results (default: .agentready/benchmarks/tbench/)",
)
def benchmark(repository, harness, subset, model, verbose, timeout, output_dir):
    """Run agent coding benchmarks.

    Evaluates agent performance on standardized coding benchmarks.
    Currently supports Terminal-Bench (89 tasks).

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Quick Terminal-Bench smoketest (1-2 tasks, ~2-5 min)
        agentready benchmark --harness tbench --subset smoketest

        \b
        # Full Terminal-Bench with Sonnet (~30-40 min)
        agentready benchmark --harness tbench --subset full --model claude-sonnet-4-5

        \b
        # Default harness is tbench, so you can omit it
        agentready benchmark --subset smoketest
    """
    repo_path = Path(repository).resolve()

    # Route to appropriate harness
    if harness == "tbench":
        _run_tbench(repo_path, subset, model, verbose, timeout, output_dir)
    else:
        click.echo(f"Unknown harness: {harness}", err=True)
        raise click.Abort()


def _run_tbench(repo_path, subset, model, verbose, timeout, output_dir):
    """Run Terminal-Bench evaluation."""
    # Default subset to 'full' if not specified
    if subset is None:
        subset = "full"

    # Validate subset
    if subset not in ["smoketest", "full"]:
        click.echo(
            f"Invalid subset '{subset}' for tbench. Use: smoketest, full", err=True
        )
        raise click.Abort()

    smoketest = subset == "smoketest"

    if verbose:
        click.echo("AgentReady Terminal-Bench Benchmark")
        click.echo(f"{'=' * 50}\n")
        click.echo(f"Repository: {repo_path}")
        click.echo(f"Model: {model}")
        click.echo(f"Subset: {subset} ({'1-2 tasks' if smoketest else '89 tasks'})")
        click.echo(f"Timeout: {timeout}s\n")

    # Create HarborConfig
    harbor_config = HarborConfig(
        model=f"anthropic/{model}",
        agent="claude-code",
        jobs_dir=Path(tempfile.mkdtemp()),
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        timeout=timeout,
        n_concurrent=1,
        smoketest=smoketest,
    )

    # Validate API key
    if not harbor_config.api_key:
        click.echo(
            "Error: ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it with: export ANTHROPIC_API_KEY=your-key-here",
            err=True,
        )
        raise click.Abort()

    try:
        # Run benchmark
        if verbose:
            click.echo("Starting Terminal-Bench evaluation...\n")

        result = _real_tbench_result(repo_path, harbor_config)

        # Display results
        click.echo(f"\n{'=' * 50}")
        click.echo("Terminal-Bench Benchmark Complete")
        click.echo(f"{'=' * 50}\n")
        click.echo(f"Score: {result.score:.2f}")
        click.echo(f"Task Solved: {result.task_solved}")
        click.echo(f"Resolved Trials: {result.resolved_trials}")
        click.echo(f"Unresolved Trials: {result.unresolved_trials}")
        click.echo(f"Pass@1: {result.pass_at_1:.2f}")

        # Save results if output dir specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            # TODO: Save results to JSON file

    except Exception as e:
        click.echo(f"\nBenchmark failed: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()
