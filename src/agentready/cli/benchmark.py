"""Benchmark command for running agent coding evaluations."""

import json
import os
import tempfile
from pathlib import Path

import click

from ..services.eval_harness.harbor_config import HarborConfig
from ..services.eval_harness.tbench_runner import _real_tbench_result
from ..services.harbor.agent_toggler import AssessorStateToggler
from ..services.harbor.comparer import compare_assessor_impact


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
@click.option(
    "--skip-preflight",
    is_flag=True,
    help="Skip dependency checks (for advanced users)",
)
def benchmark(
    repository, harness, subset, model, verbose, timeout, output_dir, skip_preflight
):
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
        _run_tbench(
            repo_path, subset, model, verbose, timeout, output_dir, skip_preflight
        )
    else:
        click.echo(f"Unknown harness: {harness}", err=True)
        raise click.Abort()


def _run_tbench(repo_path, subset, model, verbose, timeout, output_dir, skip_preflight):
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

    # Preflight: Check Harbor CLI availability and dataset
    task_path = None
    if not skip_preflight:
        try:
            from ..utils.preflight import (
                PreflightError,
                check_harbor_cli,
                ensure_terminal_bench_dataset,
            )

            if verbose:
                click.echo("Checking dependencies...\n")

            check_harbor_cli(interactive=True)

            # For smoketest, ensure dataset is downloaded
            if smoketest:
                task_path = ensure_terminal_bench_dataset()

        except PreflightError as e:
            click.echo(f"\nPreflight check failed:\n{e}\n", err=True)
            raise click.Abort()

    # Validate API key BEFORE creating HarborConfig
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        click.echo(
            "Error: ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it with: export ANTHROPIC_API_KEY=your-key-here",
            err=True,
        )
        raise click.Abort()

    # Create HarborConfig (will not raise ValueError now)
    harbor_config = HarborConfig(
        model=f"anthropic/{model}",
        agent="claude-code",
        jobs_dir=Path(tempfile.mkdtemp()),
        api_key=api_key,
        timeout=timeout,
        n_concurrent=1,
        smoketest=smoketest,
        task_path=task_path,
    )

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

        # Display trajectory file path if available
        if result.trajectory_path:
            click.echo(f"\nTrajectory: {result.trajectory_path}")

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


# Default Phase 1 task subset (8 diverse tasks, ~2-3 hours per assessor)
DEFAULT_PHASE1_TASKS = [
    "adaptive-rejection-sampler",  # Math/algorithms
    "async-http-client",  # Networking
    "terminal-file-browser",  # File I/O
    "markdown-parser",  # Text processing
    "json-validator",  # Data structures
    "cli-calculator",  # User interaction
    "log-analyzer",  # String manipulation
    "sudoku-solver",  # Logic
]


@click.command()
@click.option(
    "--assessor",
    "-a",
    required=False,
    help="Assessor ID to validate (e.g., claude_md_file, readme_structure, test_coverage)",
)
@click.option(
    "--tasks",
    "-t",
    multiple=True,
    help="Terminal-Bench task names (default: Phase 1 subset of 8 tasks)",
)
@click.option(
    "--runs",
    "-r",
    type=int,
    default=3,
    help="Number of runs per task (default: 3, recommended: 5+)",
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["claude-haiku-4-5", "claude-sonnet-4-5"]),
    default="claude-haiku-4-5",
    help="Claude model to use (default: haiku-4-5 for speed)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory (default: .agentready/validations/{assessor_id}/)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--list-assessors",
    is_flag=True,
    help="List supported assessors and exit",
)
@click.option(
    "--concurrent",
    "-c",
    type=int,
    default=1,
    help="Number of concurrent tasks to run in parallel (default: 1, recommended: 3-5)",
)
@click.option(
    "--smoketest",
    is_flag=True,
    help="Run smoketest with single task for quick validation (~2 minutes)",
)
def validate_assessor(
    assessor,
    tasks,
    runs,
    model,
    output_dir,
    verbose,
    list_assessors,
    concurrent,
    smoketest,
):
    """Validate single assessor impact using Terminal-Bench A/B testing.

    This command empirically measures the impact of a specific AgentReady assessor
    on Claude Code's Terminal-Bench performance by running an A/B test:

    \b
    1. Baseline: Force assessor to FAIL (manipulate repo state)
    2. Treatment: Restore repo to normal state (assessor PASSES)
    3. Compare success rates with statistical significance testing

    Examples:

        \b
        # Quick smoketest with 1 task (~2 minutes)
        agentready validate-assessor --assessor claude_md_file --smoketest

        \b
        # Validate CLAUDE.md impact (8 tasks, 3 runs each = 48 trials)
        agentready validate-assessor --assessor claude_md_file

        \b
        # Test README with custom tasks and 5 runs for higher statistical power
        agentready validate-assessor --assessor readme_structure \\
            --tasks adaptive-rejection-sampler \\
            --tasks async-http-client \\
            --runs 5

        \b
        # List all supported assessors
        agentready validate-assessor --list-assessors
    """
    repo_root = Path.cwd()

    # Handle --list-assessors
    if list_assessors:
        toggler = AssessorStateToggler(repo_root=repo_root)
        supported = toggler.list_supported_assessors()

        click.echo("Supported Assessors for Validation:")
        click.echo(f"{'=' * 60}")
        for assessor_id in supported:
            click.echo(f"  - {assessor_id}")
        click.echo(f"\nTotal: {len(supported)} assessors")
        click.echo("\nUsage: agentready validate-assessor --assessor {assessor_id}")
        return

    # Validate that --assessor is provided if not listing
    if not assessor:
        click.echo(
            "Error: Missing required option '--assessor' / '-a'.\n"
            "Use --list-assessors to see available assessors.",
            err=True,
        )
        raise click.Abort()

    # Validate ANTHROPIC_API_KEY
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        click.echo(
            "Error: ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it with: export ANTHROPIC_API_KEY=your-key-here",
            err=True,
        )
        raise click.Abort()

    # Use default Phase 1 tasks if not specified
    if not tasks:
        if smoketest:
            # Smoketest: just 1 simple task for quick validation
            tasks = ["adaptive-rejection-sampler"]
            if verbose:
                click.echo("Using smoketest mode (1 task, ~2 minutes total)\n")
        else:
            tasks = DEFAULT_PHASE1_TASKS
            if verbose:
                click.echo(f"Using default Phase 1 task subset ({len(tasks)} tasks)\n")

    # Convert model name to full identifier
    model_id = f"anthropic/{model}"

    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(".agentready") / "validations" / assessor

    try:
        # Run A/B comparison
        comparison = compare_assessor_impact(
            assessor_id=assessor,
            task_names=list(tasks),
            repo_root=repo_root,
            runs_per_task=runs,
            output_dir=output_path,
            model=model_id,
            n_concurrent=concurrent,
            verbose=verbose,
        )

        # Save JSON results
        json_file = output_path / f"{assessor}.json"
        with open(json_file, "w") as f:
            json.dump(
                {
                    "assessor_id": assessor,
                    "tasks": list(tasks),
                    "runs_per_task": runs,
                    "baseline": comparison.without_agent.to_dict(),
                    "treatment": comparison.with_agent.to_dict(),
                    "deltas": comparison.deltas,
                    "statistical_significance": comparison.statistical_significance,
                },
                f,
                indent=2,
            )

        # Generate Markdown report
        md_file = output_path / f"{assessor}.md"
        with open(md_file, "w") as f:
            f.write(f"# Assessor Impact Validation: {assessor}\n\n")
            f.write(f"**Date**: {comparison.created_at}\n")
            f.write(f"**Tasks**: {len(tasks)}\n")
            f.write(f"**Runs per Task**: {runs}\n\n")

            f.write("## Results Summary\n\n")
            f.write(
                "| Metric | Baseline (Assessor Fails) | Treatment (Assessor Passes) | Delta |\n"
            )
            f.write(
                "|--------|---------------------------|----------------------------|-------|\n"
            )

            delta = comparison.deltas["success_rate_delta"]
            sign = "+" if delta >= 0 else ""
            f.write(
                f"| Success Rate | {comparison.without_agent.success_rate:.1f}% | "
                f"{comparison.with_agent.success_rate:.1f}% | **{sign}{delta:.1f} pp** |\n"
            )

            duration_delta = comparison.deltas.get("avg_duration_delta_sec", 0)
            sign = "+" if duration_delta >= 0 else ""
            f.write(
                f"| Avg Duration | {comparison.without_agent.avg_duration_sec:.1f}s | "
                f"{comparison.with_agent.avg_duration_sec:.1f}s | {sign}{duration_delta:.1f}s |\n"
            )

            f.write("\n## Statistical Significance\n\n")
            is_sig = comparison.statistical_significance.get(
                "success_rate_significant", False
            )
            p_val = comparison.statistical_significance.get("success_rate_p_value")
            f.write(f"- **Significant**: {'YES ✓' if is_sig else 'NO'}\n")
            if p_val is not None:
                f.write(f"- **P-value**: {p_val:.4f}\n")

            f.write("\n## Files\n\n")
            f.write(f"- JSON: `{json_file}`\n")
            f.write(f"- Markdown: `{md_file}`\n")

        click.echo("\nResults saved:")
        click.echo(f"  - JSON: {json_file}")
        click.echo(f"  - Markdown: {md_file}\n")

    except ValueError as e:
        click.echo(f"\nError: {e}\n", err=True)
        click.echo("Use --list-assessors to see supported assessors.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"\nValidation failed: {e}\n", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.Abort()
