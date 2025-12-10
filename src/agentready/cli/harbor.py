"""Harbor benchmark comparison CLI commands."""

import json
from datetime import datetime
from pathlib import Path

import click

from agentready.models.harbor import HarborComparison, HarborRunMetrics
from agentready.reporters.harbor_markdown import generate_markdown_report
from agentready.services.harbor.agent_toggler import AgentFileToggler
from agentready.services.harbor.comparer import compare_runs
from agentready.services.harbor.dashboard_generator import (
    DashboardGenerator,
    generate_dashboard,
)
from agentready.services.harbor.result_parser import parse_harbor_results
from agentready.services.harbor.runner import HarborNotInstalledError, HarborRunner


def _run_benchmark_phase(
    runner: HarborRunner,
    toggler: AgentFileToggler,
    phase_name: str,
    run_number: int,
    output_dir: Path,
    task_list: list,
    model: str,
    verbose: bool,
    disable_agent: bool,
) -> Path:
    """Run a single benchmark phase (with or without agent).

    Returns:
        Path to results directory
    """
    click.echo("=" * 60)
    click.echo(f"RUN {run_number}: {phase_name}")
    click.echo("=" * 60)
    click.echo()

    try:
        if disable_agent:
            with toggler.temporarily_disabled():
                click.echo("Agent file disabled. Running benchmark...")
                runner.run_benchmark(
                    task_names=task_list,
                    output_dir=output_dir,
                    model=model,
                    verbose=verbose,
                )
        else:
            click.echo("Agent file enabled. Running benchmark...")
            runner.run_benchmark(
                task_names=task_list,
                output_dir=output_dir,
                model=model,
                verbose=verbose,
            )
    except Exception as e:
        click.echo(f"❌ Benchmark failed: {e}", err=True)
        # Context manager automatically restores agent file in finally block
        raise click.Abort()

    click.echo(f"✓ Run {run_number} complete\n")
    return output_dir


def _generate_reports(
    comparison: HarborComparison,
    run_dir: Path,
    output_dir: Path,
    timestamp: str,
) -> dict:
    """Generate all report formats (JSON, Markdown, HTML).

    Returns:
        Dictionary of report paths
    """
    comparison_base = run_dir / f"comparison_{timestamp}"
    paths = {}

    # Generate JSON report
    paths["json"] = comparison_base.with_suffix(".json")
    with open(paths["json"], "w") as f:
        json.dump(comparison.to_dict(), f, indent=2)
    click.echo(f"  ✓ JSON:     {paths['json']}")

    # Generate Markdown report
    paths["markdown"] = comparison_base.with_suffix(".md")
    generate_markdown_report(comparison, paths["markdown"])
    click.echo(f"  ✓ Markdown: {paths['markdown']}")

    # Generate HTML dashboard
    paths["html"] = comparison_base.with_suffix(".html")
    generate_dashboard(comparison, paths["html"])
    click.echo(f"  ✓ HTML:     {paths['html']}")

    # Create 'latest' symlinks for easy access
    _create_latest_symlinks(paths, output_dir)

    return paths


def _create_latest_symlinks(paths: dict, output_dir: Path) -> None:
    """Create 'latest' symlinks to most recent comparison files."""
    try:
        for format_name, source_path in paths.items():
            extension = source_path.suffix
            latest_link = output_dir / f"comparison_latest{extension}"

            # Remove old symlink if exists
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()

            # Create new symlink
            latest_link.symlink_to(source_path.relative_to(output_dir))

        click.echo(f"\n  ✓ Latest:   {output_dir}/comparison_latest.*")
    except Exception:
        # Symlinks might fail on Windows, just skip
        pass


@click.group(name="harbor")
def harbor_cli():
    """Harbor benchmark comparison commands.

    Compare Claude Code performance with/without the doubleagent.md agent file
    using the Harbor benchmarking framework.
    """
    pass


@harbor_cli.command(name="compare")
@click.option(
    "-t",
    "--task",
    "tasks",
    multiple=True,
    help="Task name to benchmark (can be specified multiple times)",
)
@click.option(
    "--model",
    default="anthropic/claude-sonnet-4-5",
    help="Model identifier (default: anthropic/claude-sonnet-4-5)",
)
@click.option(
    "--agent-file",
    type=click.Path(exists=True, path_type=Path),
    default=".claude/agents/doubleagent.md",
    help="Path to agent file (default: .claude/agents/doubleagent.md)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=".agentready/harbor_comparisons",
    help="Output directory for results (default: .agentready/harbor_comparisons)",
)
@click.option("--verbose", is_flag=True, help="Print detailed Harbor output")
@click.option(
    "--open-dashboard", is_flag=True, help="Open HTML dashboard after comparison"
)
def compare(
    tasks: tuple,
    model: str,
    agent_file: Path,
    output_dir: Path,
    verbose: bool,
    open_dashboard: bool,
):
    """Compare Harbor benchmarks with/without agent file.

    Runs Terminal-Bench tasks twice:
    1. Without doubleagent.md (agent file disabled)
    2. With doubleagent.md (agent file enabled)

    Generates comprehensive comparison reports (JSON, Markdown, HTML).

    Example:
        agentready harbor compare -t adaptive-rejection-sampler -t async-http-client
    """
    click.echo("=" * 60)
    click.echo("Harbor Benchmark Comparison")
    click.echo("=" * 60)
    click.echo()

    # Validate agent file exists
    if not agent_file.exists():
        click.echo(f"❌ Error: Agent file not found: {agent_file}", err=True)
        click.echo(
            "   This comparison requires the doubleagent.md agent file.", err=True
        )
        raise click.Abort()

    # Validate tasks specified
    if not tasks:
        click.echo(
            "❌ Error: At least one task must be specified with -t/--task", err=True
        )
        click.echo(
            "   Example: agentready harbor compare -t adaptive-rejection-sampler",
            err=True,
        )
        raise click.Abort()

    task_list = list(tasks)
    click.echo(f"Tasks to benchmark: {', '.join(task_list)}")
    click.echo(f"Model: {model}")
    click.echo(f"Agent file: {agent_file}")
    click.echo()

    try:
        # Initialize Harbor runner
        click.echo("Checking Harbor installation...")
        runner = HarborRunner()
        click.echo("✓ Harbor installed\n")

    except HarborNotInstalledError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()

    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Initialize agent file toggler
    toggler = AgentFileToggler(agent_file)

    # Run benchmarks with and without agent file
    without_results_dir = _run_benchmark_phase(
        runner=runner,
        toggler=toggler,
        phase_name="WITHOUT doubleagent.md",
        run_number=1,
        output_dir=run_dir / "without_agent",
        task_list=task_list,
        model=model,
        verbose=verbose,
        disable_agent=True,
    )

    with_results_dir = _run_benchmark_phase(
        runner=runner,
        toggler=toggler,
        phase_name="WITH doubleagent.md",
        run_number=2,
        output_dir=run_dir / "with_agent",
        task_list=task_list,
        model=model,
        verbose=verbose,
        disable_agent=False,
    )

    # Parse results
    click.echo("Parsing results...")
    try:
        without_tasks = parse_harbor_results(without_results_dir)
        with_tasks = parse_harbor_results(with_results_dir)

        without_metrics = HarborRunMetrics.from_task_results(
            run_id=f"without_{timestamp}",
            agent_file_enabled=False,
            task_results=without_tasks,
        )

        with_metrics = HarborRunMetrics.from_task_results(
            run_id=f"with_{timestamp}", agent_file_enabled=True, task_results=with_tasks
        )

    except Exception as e:
        click.echo(f"❌ Failed to parse results: {e}", err=True)
        raise click.Abort()

    # Compare runs
    click.echo("Calculating comparison...")
    comparison = compare_runs(without_metrics, with_metrics)

    # Generate reports
    click.echo("Generating reports...")
    report_paths = _generate_reports(comparison, run_dir, output_dir, timestamp)

    # Print summary
    click.echo()
    click.echo("=" * 60)
    click.echo("SUMMARY")
    click.echo("=" * 60)

    generator = DashboardGenerator()
    summary = generator.generate_summary_text(comparison)
    click.echo(summary)

    # Open dashboard if requested
    if open_dashboard:
        import webbrowser

        html_path = report_paths.get("html")
        if html_path:
            click.echo(f"\nOpening dashboard: {html_path}")
            webbrowser.open(html_path.as_uri())


@harbor_cli.command(name="list")
@click.option(
    "--output-dir",
    type=click.Path(exists=True, path_type=Path),
    default=".agentready/harbor_comparisons",
    help="Output directory containing comparisons",
)
def list_comparisons(output_dir: Path):
    """List all Harbor comparisons."""
    click.echo(f"Harbor comparisons in {output_dir}:")
    click.echo()

    comparison_files = sorted(output_dir.glob("*/comparison_*.json"), reverse=True)

    if not comparison_files:
        click.echo("  No comparisons found.")
        return

    for comp_file in comparison_files:
        # Parse comparison to get summary
        with open(comp_file, "r") as f:
            data = json.load(f)
            comparison = HarborComparison.from_dict(data)

        created = comparison.created_at
        delta_success = comparison.deltas["success_rate_delta"]
        delta_duration = comparison.deltas["avg_duration_delta_pct"]

        click.echo(f"  {comp_file.parent.name}/")
        click.echo(f"    Created:      {created}")
        click.echo(f"    Success Δ:    {delta_success:+.1f}%")
        click.echo(f"    Duration Δ:   {delta_duration:+.1f}%")
        click.echo()


@harbor_cli.command(name="view")
@click.argument("comparison_file", type=click.Path(exists=True, path_type=Path))
@click.option("--format", type=click.Choice(["summary", "full"]), default="summary")
def view_comparison(comparison_file: Path, format: str):
    """View a Harbor comparison.

    COMPARISON_FILE: Path to comparison JSON file
    """
    with open(comparison_file, "r") as f:
        data = json.load(f)
        comparison = HarborComparison.from_dict(data)

    if format == "summary":
        generator = DashboardGenerator()
        summary = generator.generate_summary_text(comparison)
        click.echo(summary)
    else:
        # Full JSON output
        click.echo(json.dumps(data, indent=2))


if __name__ == "__main__":
    harbor_cli()
