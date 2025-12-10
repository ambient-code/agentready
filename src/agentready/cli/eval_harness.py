"""CLI commands for Terminal-Bench eval harness.

Provides commands to establish baseline, test assessors, aggregate results,
and generate dashboard data for empirical assessment validation.
"""

import sys
from pathlib import Path

import click

from ..assessors import create_all_assessors
from ..services.eval_harness import (
    AssessorTester,
    BaselineEstablisher,
    DashboardGenerator,
    ResultsAggregator,
    TbenchRunner,
)


@click.group("eval-harness")
def eval_harness():
    """Terminal-Bench eval harness for measuring assessor impact.

    Systematically measures the impact of each AgentReady assessor
    on Terminal-Bench (tbench.ai) performance through A/B testing.

    Workflow:
        1. Establish baseline: agentready eval-harness baseline
        2. Test assessors: agentready eval-harness run-tier --tier 1
        3. View summary: agentready eval-harness summarize
        4. Generate dashboard: agentready eval-harness dashboard

    Examples:

        \b
        # Establish baseline (5 runs)
        agentready eval-harness baseline

        \b
        # Test single assessor
        agentready eval-harness test-assessor --assessor-id claude_md_file

        \b
        # Test all Tier 1 assessors
        agentready eval-harness run-tier --tier 1
    """
    pass


@eval_harness.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=5,
    help="Number of tbench runs to perform (default: 5)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory (default: .agentready/eval_harness/baseline)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed progress information",
)
def baseline(repository, iterations, output_dir, verbose):
    """Establish baseline Terminal-Bench performance.

    Runs tbench multiple times on an unmodified repository to establish
    the starting point for measuring assessor impact. Calculates mean,
    standard deviation, median, min, and max scores.

    REPOSITORY: Path to git repository (default: current directory)
    """
    repo_path = Path(repository).resolve()

    # Validate repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    click.echo("🔬 AgentReady Eval Harness - Baseline Establishment")
    click.echo("=" * 60)
    click.echo(f"\nRepository: {repo_path}")
    click.echo(f"Iterations: {iterations}")
    if output_dir:
        click.echo(f"Output: {output_dir}")
    click.echo()

    # Create establisher
    tbench_runner = TbenchRunner(mock=True)
    establisher = BaselineEstablisher(tbench_runner=tbench_runner)

    # Set output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = repo_path / ".agentready" / "eval_harness" / "baseline"

    # Run baseline establishment with progress
    click.echo("Running Terminal-Bench baseline...")
    click.echo("[Mocked mode - using deterministic scores for workflow validation]\n")

    try:
        with click.progressbar(
            range(iterations), label="Progress", show_pos=True
        ) as bar:
            # We can't actually update during iteration with current API
            # So we'll run all at once and show completion
            baseline_metrics = establisher.establish_baseline(
                repo_path, iterations=iterations, output_dir=out_path
            )
            # Advance progress bar to completion
            for _ in bar:
                pass

        # Show results
        click.echo("\n✅ Baseline established successfully!")
        click.echo("\nResults:")
        click.echo(f"  Mean Score:   {baseline_metrics.mean_score:.2f}")
        click.echo(f"  Std Dev:      {baseline_metrics.std_dev:.2f}")
        click.echo(f"  Median:       {baseline_metrics.median_score:.2f}")
        click.echo(f"  Min:          {baseline_metrics.min_score:.2f}")
        click.echo(f"  Max:          {baseline_metrics.max_score:.2f}")
        click.echo(f"  Iterations:   {baseline_metrics.iterations}")

        click.echo("\nResults saved to:")
        click.echo(f"  {out_path / 'summary.json'}")
        click.echo(f"  {out_path / 'run_001.json'} (and {iterations-1} more)")

        if verbose:
            click.echo("\n📊 Individual Run Scores:")
            for i, result in enumerate(baseline_metrics.raw_results, 1):
                click.echo(
                    f"  Run {i:2d}: {result.score:.2f} (completion: {result.completion_rate:.1f}%, pytest: {result.pytest_pass_rate:.1f}%)"
                )

        click.echo("\nNext step:")
        click.echo(
            "  agentready eval-harness test-assessor --assessor-id claude_md_file"
        )

    except Exception as e:
        click.echo(f"\n❌ Error during baseline establishment: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@eval_harness.command()
@click.option(
    "--baseline-dir",
    type=click.Path(exists=True),
    default=".agentready/eval_harness/baseline",
    help="Directory containing baseline results",
)
def show_baseline(baseline_dir):
    """Display previously established baseline metrics.

    Loads and displays baseline results from a previous run.
    """
    baseline_path = Path(baseline_dir).resolve()

    click.echo("🔬 AgentReady Eval Harness - Baseline Results")
    click.echo("=" * 60)

    try:
        establisher = BaselineEstablisher()
        baseline_metrics = establisher.load_baseline(baseline_path)

        click.echo(f"\nBaseline loaded from: {baseline_path}")
        click.echo("\nResults:")
        click.echo(f"  Mean Score:   {baseline_metrics.mean_score:.2f}")
        click.echo(f"  Std Dev:      {baseline_metrics.std_dev:.2f}")
        click.echo(f"  Median:       {baseline_metrics.median_score:.2f}")
        click.echo(f"  Min:          {baseline_metrics.min_score:.2f}")
        click.echo(f"  Max:          {baseline_metrics.max_score:.2f}")
        click.echo(f"  Iterations:   {baseline_metrics.iterations}")

        click.echo("\n📊 Individual Run Scores:")
        for i, result in enumerate(baseline_metrics.raw_results, 1):
            click.echo(
                f"  Run {i:2d}: {result.score:.2f} (completion: {result.completion_rate:.1f}%, pytest: {result.pytest_pass_rate:.1f}%)"
            )

    except FileNotFoundError as e:
        click.echo(f"\n❌ {str(e)}", err=True)
        click.echo(
            "\nRun 'agentready eval-harness baseline' first to establish baseline."
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Error loading baseline: {str(e)}", err=True)
        sys.exit(1)


@eval_harness.command()
@click.option(
    "--assessor-id",
    required=True,
    help="Assessor attribute ID to test (e.g., claude_md_file)",
)
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--baseline-dir",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing baseline results (default: .agentready/eval_harness/baseline)",
)
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=5,
    help="Number of tbench runs post-remediation (default: 5)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory (default: .agentready/eval_harness/<assessor-id>)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed progress information",
)
def test_assessor(
    assessor_id, repository, baseline_dir, iterations, output_dir, verbose
):
    """Test a single assessor's impact on Terminal-Bench performance.

    Runs A/B testing workflow:
    1. Clone repository to temp directory
    2. Run assessment with single assessor
    3. Apply remediation using FixerService
    4. Run tbench post-remediation
    5. Calculate delta, p-value, and Cohen's d effect size

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Test claude_md_file assessor
        agentready eval-harness test-assessor --assessor-id claude_md_file

        \b
        # Test with custom baseline location
        agentready eval-harness test-assessor \\
            --assessor-id readme_structure \\
            --baseline-dir /path/to/baseline
    """
    repo_path = Path(repository).resolve()

    # Validate repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    click.echo("🧪 AgentReady Eval Harness - Assessor Testing")
    click.echo("=" * 60)
    click.echo(f"\nAssessor: {assessor_id}")
    click.echo(f"Repository: {repo_path}")
    click.echo(f"Iterations: {iterations}")
    click.echo()

    # Load baseline
    if baseline_dir:
        baseline_path = Path(baseline_dir)
    else:
        baseline_path = repo_path / ".agentready" / "eval_harness" / "baseline"

    try:
        establisher = BaselineEstablisher()
        baseline_metrics = establisher.load_baseline(baseline_path)
        click.echo(
            f"📊 Baseline loaded: {baseline_metrics.mean_score:.2f} ± {baseline_metrics.std_dev:.2f}"
        )
    except FileNotFoundError:
        click.echo(f"❌ Baseline not found at {baseline_path}", err=True)
        click.echo("\nRun 'agentready eval-harness baseline' first.")
        sys.exit(1)

    # Set output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = (
            repo_path / ".agentready" / "eval_harness" / "assessors" / assessor_id
        )

    # Create tester
    tbench_runner = TbenchRunner(mock=True)
    tester = AssessorTester(tbench_runner=tbench_runner)

    # Run test
    click.echo("\n🔬 Testing assessor impact...")
    click.echo("[Mocked mode - using deterministic scores for workflow validation]")
    click.echo("\nSteps:")
    click.echo("  1. Clone repository to temp directory")
    click.echo(f"  2. Run assessment with {assessor_id} only")
    click.echo("  3. Apply remediation (if applicable)")
    click.echo(f"  4. Run Terminal-Bench {iterations} times")
    click.echo("  5. Calculate statistical significance\n")

    try:
        with click.progressbar(
            range(iterations), label="Progress", show_pos=True
        ) as bar:
            impact = tester.test_assessor(
                assessor_id,
                repo_path,
                baseline_metrics,
                iterations=iterations,
                output_dir=out_path,
            )
            # Advance progress bar to completion
            for _ in bar:
                pass

        # Show results
        click.echo("\n✅ Assessor testing complete!")

        # Delta interpretation
        delta_sign = "+" if impact.delta_score >= 0 else ""
        delta_color = "green" if impact.delta_score > 0 else "red"

        click.echo("\n📊 Results:")
        click.echo(f"  Assessor:          {impact.assessor_name} (Tier {impact.tier})")
        click.echo(f"  Baseline Score:    {impact.baseline_score:.2f}")
        click.echo(f"  Post-Fix Score:    {impact.post_remediation_score:.2f}")
        click.echo(
            f"  Delta:             {delta_sign}{impact.delta_score:.2f} points",
            color=delta_color if impact.delta_score != 0 else None,
        )
        click.echo(f"  P-value:           {impact.p_value:.4f}")
        click.echo(f"  Effect Size (d):   {impact.effect_size:.3f}")

        # Significance interpretation
        if impact.is_significant:
            click.echo("  Significant:       ✅ YES (p < 0.05, |d| > 0.2)")
        else:
            click.echo("  Significant:       ❌ NO")

        # Effect size interpretation
        abs_d = abs(impact.effect_size)
        if abs_d >= 0.8:
            effect_label = "large"
        elif abs_d >= 0.5:
            effect_label = "medium"
        elif abs_d >= 0.2:
            effect_label = "small"
        else:
            effect_label = "negligible"
        click.echo(f"  Effect Magnitude:  {effect_label}")

        # Remediation summary
        click.echo("\n🔧 Remediation:")
        click.echo(f"  Fixes Applied:     {impact.fixes_applied}")
        if verbose and impact.remediation_log:
            click.echo("\n  Actions taken:")
            for log_entry in impact.remediation_log:
                click.echo(f"    - {log_entry}")

        click.echo("\n💾 Results saved to:")
        click.echo(f"  {out_path / 'impact.json'}")
        click.echo(f"  {out_path / 'run_001.json'} (and {iterations-1} more)")

        # Next steps
        click.echo("\n📈 Next steps:")
        click.echo("  agentready eval-harness run-tier --tier 1")

    except ValueError as e:
        click.echo(f"\n❌ {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Error during assessor testing: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@eval_harness.command()
@click.option(
    "--tier",
    type=int,
    required=True,
    help="Tier to test (1=Essential, 2=Critical, 3=Important, 4=Advanced)",
)
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--baseline-dir",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing baseline results (default: .agentready/eval_harness/baseline)",
)
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=5,
    help="Number of tbench runs per assessor (default: 5)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed progress information",
)
def run_tier(tier, repository, baseline_dir, iterations, verbose):
    """Run all assessors in a tier and measure impact.

    Tests each assessor in the specified tier sequentially, measures impact,
    and generates a summary report with tier-level statistics.

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Test all Tier 1 assessors (5 total)
        agentready eval-harness run-tier --tier 1

        \b
        # Test with more iterations for better statistical confidence
        agentready eval-harness run-tier --tier 1 --iterations 10
    """
    repo_path = Path(repository).resolve()

    # Validate repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    # Validate tier
    if tier not in [1, 2, 3, 4]:
        click.echo("Error: Tier must be 1, 2, 3, or 4", err=True)
        sys.exit(1)

    tier_names = {1: "Essential", 2: "Critical", 3: "Important", 4: "Advanced"}

    click.echo(f"🧪 AgentReady Eval Harness - Tier {tier} Testing")
    click.echo("=" * 60)
    click.echo(f"\nTier: {tier} ({tier_names[tier]})")
    click.echo(f"Repository: {repo_path}")
    click.echo(f"Iterations per assessor: {iterations}")
    click.echo()

    # Load baseline
    if baseline_dir:
        baseline_path = Path(baseline_dir)
    else:
        baseline_path = repo_path / ".agentready" / "eval_harness" / "baseline"

    try:
        establisher = BaselineEstablisher()
        baseline_metrics = establisher.load_baseline(baseline_path)
        click.echo(
            f"📊 Baseline loaded: {baseline_metrics.mean_score:.2f} ± {baseline_metrics.std_dev:.2f}"
        )
    except FileNotFoundError:
        click.echo(f"❌ Baseline not found at {baseline_path}", err=True)
        click.echo("\nRun 'agentready eval-harness baseline' first.")
        sys.exit(1)

    # Get assessors for this tier
    all_assessors = create_all_assessors()
    tier_assessors = [a for a in all_assessors if a.attribute.tier == tier]

    if not tier_assessors:
        click.echo(f"❌ No assessors found for Tier {tier}", err=True)
        sys.exit(1)

    click.echo(f"\nAssessors to test: {len(tier_assessors)}")
    for assessor in tier_assessors:
        click.echo(f"  - {assessor.attribute_id} ({assessor.attribute.name})")
    click.echo()

    # Create tester
    tbench_runner = TbenchRunner(mock=True)
    tester = AssessorTester(tbench_runner=tbench_runner)

    # Test each assessor
    click.echo("🔬 Testing assessors...\n")

    for i, assessor in enumerate(tier_assessors, 1):
        click.echo(f"[{i}/{len(tier_assessors)}] Testing {assessor.attribute_id}...")

        output_dir = (
            repo_path
            / ".agentready"
            / "eval_harness"
            / "assessors"
            / assessor.attribute_id
        )

        try:
            impact = tester.test_assessor(
                assessor.attribute_id,
                repo_path,
                baseline_metrics,
                iterations=iterations,
                output_dir=output_dir,
            )

            # Show brief results
            delta_sign = "+" if impact.delta_score >= 0 else ""
            significance_icon = "✅" if impact.is_significant else "❌"
            click.echo(
                f"  Delta: {delta_sign}{impact.delta_score:.2f} | "
                f"Significant: {significance_icon} | "
                f"Fixes: {impact.fixes_applied}"
            )
            click.echo()

        except Exception as e:
            click.echo(f"  ❌ Error: {str(e)}", err=True)
            if verbose:
                import traceback

                traceback.print_exc()
            click.echo()

    # Automatically run summarize
    click.echo("=" * 60)
    click.echo("📊 Generating summary...\n")

    try:
        eval_harness_dir = repo_path / ".agentready" / "eval_harness"
        aggregator = ResultsAggregator()
        summary = aggregator.aggregate(eval_harness_dir)

        click.echo("✅ Summary generated!")
        click.echo("\n📈 Results:")
        click.echo(f"  Total Assessors Tested: {summary.total_assessors_tested}")
        click.echo(
            f"  Significant Improvements: {summary.significant_improvements} ({summary.significant_improvements / summary.total_assessors_tested * 100:.0f}%)"
        )

        # Show tier impacts
        click.echo("\n🎯 Tier Impacts (Average Delta):")
        for t in sorted(summary.tier_impacts.keys()):
            delta = summary.tier_impacts[t]
            if delta != 0:
                delta_sign = "+" if delta >= 0 else ""
                click.echo(f"  Tier {t}: {delta_sign}{delta:.2f} points")

        # Show top 3 assessors
        ranked = summary.get_ranked_assessors()
        click.echo("\n🏆 Top 3 Assessors by Impact:")
        for i, impact in enumerate(ranked[:3], 1):
            delta_sign = "+" if impact.delta_score >= 0 else ""
            click.echo(
                f"  {i}. {impact.assessor_name}: {delta_sign}{impact.delta_score:.2f} points"
            )

        click.echo("\n💾 Summary saved to:")
        click.echo(f"  {eval_harness_dir / 'summary.json'}")

        click.echo("\n📈 Next steps:")
        click.echo(
            "  agentready eval-harness dashboard  # Generate GitHub Pages dashboard"
        )

    except Exception as e:
        click.echo(f"❌ Error generating summary: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@eval_harness.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed assessor breakdown",
)
def summarize(repository, verbose):
    """Aggregate and display evaluation results.

    Loads all assessor impact results and generates a summary report
    with tier-level statistics and ranked assessors.

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Generate summary after testing assessors
        agentready eval-harness summarize

        \b
        # Show detailed breakdown
        agentready eval-harness summarize --verbose
    """
    repo_path = Path(repository).resolve()
    eval_harness_dir = repo_path / ".agentready" / "eval_harness"

    click.echo("📊 AgentReady Eval Harness - Summary")
    click.echo("=" * 60)

    try:
        aggregator = ResultsAggregator()
        summary = aggregator.aggregate(eval_harness_dir)

        click.echo("\n✅ Summary generated successfully!")

        # Baseline
        click.echo("\n📈 Baseline Performance:")
        click.echo(f"  Mean Score: {summary.baseline.mean_score:.2f}")
        click.echo(f"  Std Dev: {summary.baseline.std_dev:.2f}")
        click.echo(f"  Iterations: {summary.baseline.iterations}")

        # Overall stats
        click.echo("\n📊 Overall Results:")
        click.echo(f"  Total Assessors Tested: {summary.total_assessors_tested}")
        click.echo(f"  Significant Improvements: {summary.significant_improvements}")
        click.echo(
            f"  Significance Rate: {summary.significant_improvements / summary.total_assessors_tested * 100:.0f}%"
        )

        # Tier impacts
        click.echo("\n🎯 Impact by Tier (Average Delta):")
        for t in sorted(summary.tier_impacts.keys()):
            delta = summary.tier_impacts[t]
            delta_sign = "+" if delta >= 0 else ""
            tier_names = {1: "Essential", 2: "Critical", 3: "Important", 4: "Advanced"}
            click.echo(
                f"  Tier {t} ({tier_names.get(t, 'Unknown')}): {delta_sign}{delta:.2f} points"
            )

        # Ranked assessors
        ranked = summary.get_ranked_assessors()
        click.echo("\n🏆 Assessors Ranked by Impact:")

        if verbose:
            # Show all assessors
            for i, impact in enumerate(ranked, 1):
                delta_sign = "+" if impact.delta_score >= 0 else ""
                sig_icon = "✅" if impact.is_significant else "❌"
                click.echo(
                    f"  {i:2d}. {impact.assessor_name:40s} "
                    f"{delta_sign}{impact.delta_score:+6.2f} | "
                    f"Sig: {sig_icon} | "
                    f"Fixes: {impact.fixes_applied}"
                )
        else:
            # Show top 5
            for i, impact in enumerate(ranked[:5], 1):
                delta_sign = "+" if impact.delta_score >= 0 else ""
                sig_icon = "✅" if impact.is_significant else "❌"
                click.echo(
                    f"  {i}. {impact.assessor_name}: {delta_sign}{impact.delta_score:.2f} | Sig: {sig_icon}"
                )

            if len(ranked) > 5:
                click.echo(f"  ... and {len(ranked) - 5} more")
                click.echo("\n  (Use --verbose to see all assessors)")

        click.echo("\n💾 Summary saved to:")
        click.echo(f"  {eval_harness_dir / 'summary.json'}")

        click.echo("\n📈 Next steps:")
        click.echo(
            "  agentready eval-harness dashboard  # Generate GitHub Pages dashboard"
        )

    except FileNotFoundError as e:
        click.echo(f"❌ {str(e)}", err=True)
        click.echo(
            "\nRun 'agentready eval-harness run-tier --tier 1' first to test assessors."
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@eval_harness.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--docs-dir",
    type=click.Path(),
    default=None,
    help="Docs data directory (default: docs/_data/tbench/)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed file output information",
)
def dashboard(repository, docs_dir, verbose):
    """Generate dashboard data files for GitHub Pages.

    Converts evaluation summary into Jekyll-compatible JSON data files
    for visualization with Chart.js on the GitHub Pages dashboard.

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Generate dashboard data after testing
        agentready eval-harness dashboard

        \b
        # Custom docs directory
        agentready eval-harness dashboard --docs-dir /path/to/docs/_data/tbench
    """
    repo_path = Path(repository).resolve()
    eval_harness_dir = repo_path / ".agentready" / "eval_harness"

    click.echo("📊 AgentReady Eval Harness - Dashboard Generator")
    click.echo("=" * 60)

    try:
        generator = DashboardGenerator()

        # Set docs directory if provided
        if docs_dir:
            docs_data_dir = Path(docs_dir)
        else:
            docs_data_dir = None  # Will use default (docs/_data/tbench/)

        click.echo("\n🔄 Generating dashboard data...")
        click.echo(f"Source: {eval_harness_dir / 'summary.json'}")

        generated_files = generator.generate(eval_harness_dir, docs_data_dir)

        click.echo("\n✅ Dashboard data generated successfully!")

        click.echo("\n📁 Generated Files:")
        for name, path in generated_files.items():
            click.echo(f"  • {name}: {path.relative_to(repo_path)}")
            if verbose:
                # Show file size
                size = path.stat().st_size
                click.echo(f"    Size: {size:,} bytes")

        click.echo("\n📈 Next Steps:")
        click.echo("  1. Review generated data in docs/_data/tbench/")
        click.echo("  2. Create dashboard page: docs/tbench.md")
        click.echo("  3. Update navigation: docs/_config.yml")
        click.echo("  4. Commit and push to GitHub Pages")

        click.echo("\n💡 Tip:")
        click.echo(
            "  The dashboard will auto-update when you run 'eval-harness run-tier'"
        )

    except FileNotFoundError as e:
        click.echo(f"❌ {str(e)}", err=True)
        click.echo(
            "\nRun 'agentready eval-harness run-tier --tier 1' first to generate summary."
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
