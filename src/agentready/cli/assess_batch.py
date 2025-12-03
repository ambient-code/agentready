"""CLI command for batch repository assessment."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from pydantic import ValidationError

from ..assessors import create_all_assessors
from ..models.config import Config
from ..reporters.html import HTMLReporter
from ..reporters.markdown import MarkdownReporter
from ..services.batch_scanner import BatchScanner


def _get_agentready_version() -> str:
    """Get AgentReady version from package metadata."""
    try:
        from importlib.metadata import version as get_version
    except ImportError:
        from importlib_metadata import version as get_version

    try:
        return get_version("agentready")
    except Exception:
        return "unknown"


def _load_config(config_path: Path) -> Config:
    """Load configuration from YAML file with Pydantic validation.

    Uses Pydantic for automatic validation, replacing duplicated manual
    validation code with the Config.from_yaml_dict() classmethod.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated Config instance

    Raises:
        ValidationError: If YAML data doesn't match expected schema
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    import sys

    import yaml

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Pydantic handles all validation automatically
        return Config.from_yaml_dict(data)
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = []
        for error in e.errors():
            field = " → ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {field}: {msg}")

        click.echo("Configuration validation failed:", err=True)
        for error in errors:
            click.echo(error, err=True)
        sys.exit(1)


def _generate_multi_reports(batch_assessment, output_path: Path, verbose: bool) -> None:
    """Generate all report formats in dated folder structure.

    Phase 2 Reporting:
    - Creates dated reports folder (reports-YYYYMMDD-HHMMSS/)
    - Generates SQLite database (all assessments queryable)
    - Generates CSV/TSV summaries (one row per repo)
    - Generates aggregated JSON (all assessments in one file)
    - Generates individual reports (HTML/JSON/MD per repo)
    - Generates summary HTML (index.html with comparison table)

    Args:
        batch_assessment: Complete batch assessment with results
        output_path: Base output directory
        verbose: Whether to show verbose progress
    """
    from ..reporters.aggregated_json import AggregatedJSONReporter
    from ..reporters.csv_reporter import CSVReporter
    from ..reporters.json_reporter import JSONReporter
    from ..reporters.multi_html import MultiRepoHTMLReporter

    # Create dated reports folder
    timestamp = batch_assessment.timestamp.strftime("%Y%m%d-%H%M%S")
    reports_dir = output_path / f"reports-{timestamp}"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        click.echo(f"\nGenerating reports in {reports_dir}/")

    # 1. CSV/TSV summary
    try:
        csv_reporter = CSVReporter()
        csv_reporter.generate(
            batch_assessment, reports_dir / "summary.csv", delimiter=","
        )
        csv_reporter.generate(
            batch_assessment, reports_dir / "summary.tsv", delimiter="\t"
        )
        if verbose:
            click.echo("  ✓ summary.csv")
            click.echo("  ✓ summary.tsv")
    except Exception as e:
        click.echo(f"  ✗ CSV generation failed: {e}", err=True)

    # 2. Aggregated JSON
    try:
        json_reporter = AggregatedJSONReporter()
        json_reporter.generate(batch_assessment, reports_dir / "all-assessments.json")
        if verbose:
            click.echo("  ✓ all-assessments.json")
    except Exception as e:
        click.echo(f"  ✗ Aggregated JSON generation failed: {e}", err=True)

    # 3. Individual reports for each successful assessment
    individual_json = JSONReporter()
    for result in batch_assessment.results:
        if result.is_success():
            assessment = result.assessment
            base_name = f"{assessment.repository.name}-{assessment.timestamp.strftime('%Y%m%d-%H%M%S')}"

            try:
                # HTML report
                html_reporter = HTMLReporter()
                html_reporter.generate(assessment, reports_dir / f"{base_name}.html")

                # JSON report
                individual_json.generate(assessment, reports_dir / f"{base_name}.json")

                # Markdown report
                markdown_reporter = MarkdownReporter()
                markdown_reporter.generate(assessment, reports_dir / f"{base_name}.md")

                if verbose:
                    click.echo(f"  ✓ {base_name}.{{html,json,md}}")
            except Exception as e:
                click.echo(
                    f"  ✗ Individual reports failed for {base_name}: {e}", err=True
                )

    # 4. Multi-repo summary HTML (index)
    try:
        template_dir = Path(__file__).parent.parent / "templates"
        multi_html = MultiRepoHTMLReporter(template_dir)
        multi_html.generate(batch_assessment, reports_dir / "index.html")
        if verbose:
            click.echo("  ✓ index.html")
    except Exception as e:
        click.echo(f"  ✗ Multi-repo HTML generation failed: {e}", err=True)

    # 5. Failures JSON
    failed_results = [r for r in batch_assessment.results if not r.is_success()]
    if failed_results:
        try:
            failures_data = [
                {
                    "repo_url": r.repository_url,
                    "error_type": r.error_type,
                    "error_message": r.error,
                    "duration_seconds": r.duration_seconds,
                }
                for r in failed_results
            ]
            with open(reports_dir / "failures.json", "w", encoding="utf-8") as f:
                json.dump(failures_data, f, indent=2)
            if verbose:
                click.echo("  ✓ failures.json")
        except Exception as e:
            click.echo(f"  ✗ Failures JSON generation failed: {e}", err=True)

    # Print final summary
    click.echo(f"\n✓ Reports generated: {reports_dir}/")
    click.echo("  - index.html (summary)")
    click.echo("  - summary.csv & summary.tsv")
    click.echo("  - all-assessments.json")
    click.echo("  - Individual reports per repository")
    if failed_results:
        click.echo("  - failures.json")


@click.command()
@click.option(
    "--repos-file",
    "-f",
    type=click.Path(exists=True),
    default=None,
    help="File with repository URLs/paths (one per line)",
)
@click.option(
    "--repos",
    "-r",
    multiple=True,
    help="Repository URLs/paths (can be specified multiple times)",
)
@click.option(
    "--github-org",
    help="GitHub organization name to scan",
)
@click.option(
    "--include-private",
    is_flag=True,
    help="Include private repos from GitHub org (requires GITHUB_TOKEN)",
)
@click.option(
    "--max-repos",
    type=int,
    default=100,
    help="Maximum repos to assess from GitHub org (default: 100)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory for batch reports (default: .agentready/batch/)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file",
)
@click.option(
    "--use-cache",
    is_flag=True,
    default=True,
    help="Use cached assessments when available (default: True)",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default=None,
    help="Custom cache directory (default: .agentready/cache/)",
)
@click.option(
    "--generate-heatmap",
    is_flag=True,
    default=False,
    help="Generate interactive Plotly heatmap visualization",
)
@click.option(
    "--heatmap-output",
    type=click.Path(),
    default=None,
    help="Custom path for heatmap HTML (default: reports-*/heatmap.html)",
)
def assess_batch(
    repos_file: Optional[str],
    repos: tuple,
    github_org: Optional[str],
    include_private: bool,
    max_repos: int,
    verbose: bool,
    output_dir: Optional[str],
    config: Optional[str],
    use_cache: bool,
    cache_dir: Optional[str],
    generate_heatmap: bool,
    heatmap_output: Optional[str],
):
    """Assess multiple repositories in a batch operation.

    Supports three input methods:

    1. File-based input:
        agentready assess-batch --repos-file repos.txt

    2. Inline arguments:
        agentready assess-batch --repos https://github.com/user/repo1 --repos https://github.com/user/repo2

    3. GitHub organization:
        agentready assess-batch --github-org anthropics
        agentready assess-batch --github-org myorg --include-private --max-repos 50

    Output files are saved to .agentready/batch/ by default.
    """
    # Collect repository URLs
    repository_urls = []

    # Read from file if provided
    if repos_file:
        try:
            with open(repos_file, encoding="utf-8") as f:
                file_urls = [line.strip() for line in f if line.strip()]
                repository_urls.extend(file_urls)
        except IOError as e:
            click.echo(f"Error reading repos file: {e}", err=True)
            sys.exit(1)

    # Add inline repositories
    if repos:
        repository_urls.extend(repos)

    # NEW: GitHub org scanning
    if github_org:
        try:
            from ..services.github_scanner import (
                GitHubAPIError,
                GitHubAuthError,
                GitHubOrgScanner,
            )

            scanner = GitHubOrgScanner()
            org_repos = scanner.get_org_repos(
                org_name=github_org,
                include_private=include_private,
                max_repos=max_repos,
            )
            repository_urls.extend(org_repos)

            if verbose:
                click.echo(f"Found {len(org_repos)} repositories in {github_org}")

        except GitHubAuthError as e:
            click.echo(f"GitHub authentication error: {e}", err=True)
            sys.exit(1)

        except GitHubAPIError as e:
            click.echo(f"GitHub API error: {e}", err=True)
            sys.exit(1)

        except ValueError as e:
            click.echo(f"Invalid input: {e}", err=True)
            sys.exit(1)

    # Remove duplicates while preserving order
    if repository_urls:
        seen = set()
        unique_repos = []
        for url in repository_urls:
            if url not in seen:
                seen.add(url)
                unique_repos.append(url)
        repository_urls = unique_repos

    # Validate we have repositories
    if not repository_urls:
        click.echo(
            "Error: No repositories specified. Use --repos-file, --repos, or --github-org",
            err=True,
        )
        sys.exit(1)

    if verbose:
        click.echo("AgentReady Batch Assessment")
        click.echo(f"{'=' * 50}")
        click.echo(f"Repositories: {len(repository_urls)}")
        click.echo(f"Output: {output_dir or '.agentready/batch/'}\n")

    # Load configuration if provided
    config_obj = None
    if config:
        try:
            config_obj = _load_config(Path(config))
        except Exception as e:
            click.echo(f"Error loading config: {e}", err=True)
            sys.exit(1)

    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(".agentready/batch")

    output_path.mkdir(parents=True, exist_ok=True)

    # Set cache directory
    if cache_dir:
        cache_path = Path(cache_dir)
    else:
        cache_path = Path(".agentready/cache")

    # Create batch scanner
    version = _get_agentready_version()
    batch_scanner = BatchScanner(
        cache_dir=cache_path,
        version=version,
        command="assess-batch",
    )

    # Create assessors
    assessors = create_all_assessors()

    if verbose:
        click.echo(f"Assessors: {len(assessors)}")
        click.echo(f"Cache: {cache_path}")
        click.echo()

    # Progress callback
    def show_progress(current: int, total: int):
        click.echo(f"Assessing repository {current + 1}/{total}...")

    # Run batch assessment
    try:
        batch_assessment = batch_scanner.scan_batch(
            repository_urls=repository_urls,
            assessors=assessors,
            config=config_obj,
            use_cache=use_cache,
            verbose=verbose,
            progress_callback=show_progress if verbose else None,
        )
    except Exception as e:
        click.echo(f"Error during batch assessment: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Generate comprehensive Phase 2 reports
    _generate_multi_reports(batch_assessment, output_path, verbose)

    # Generate heatmap if requested
    if generate_heatmap:
        from ..services.attribute_analyzer import AttributeAnalyzer

        timestamp = batch_assessment.timestamp.strftime("%Y%m%d-%H%M%S")
        reports_dir = output_path / f"reports-{timestamp}"
        heatmap_path = (
            Path(heatmap_output) if heatmap_output else (reports_dir / "heatmap.html")
        )

        if verbose:
            click.echo("\nGenerating heatmap visualization...")

        try:
            analyzer = AttributeAnalyzer()
            analyzer.analyze_batch(batch_assessment, heatmap_path)
            click.echo("  ✓ heatmap.html")
        except Exception as e:
            click.echo(f"⚠ Warning: Failed to generate heatmap: {e}", err=True)
            if verbose:
                import traceback

                traceback.print_exc()

    # Print summary
    click.echo("\n" + "=" * 50)
    click.echo("Batch Assessment Summary")
    click.echo("=" * 50)
    click.echo(f"Total repositories: {batch_assessment.summary.total_repositories}")
    click.echo(f"Successful: {batch_assessment.summary.successful_assessments}")
    click.echo(f"Failed: {batch_assessment.summary.failed_assessments}")
    click.echo(f"Success rate: {batch_assessment.get_success_rate():.1f}%")
    click.echo(f"Average score: {batch_assessment.summary.average_score:.1f}/100")
    click.echo(f"Total duration: {batch_assessment.total_duration_seconds:.1f}s")
    click.echo()

    if batch_assessment.summary.score_distribution:
        click.echo("Score Distribution:")
        for level, count in batch_assessment.summary.score_distribution.items():
            if count > 0:
                click.echo(f"  {level}: {count}")
        click.echo()

    if batch_assessment.summary.top_failing_attributes:
        click.echo("Top Failing Attributes:")
        for item in batch_assessment.summary.top_failing_attributes[:5]:
            click.echo(f"  {item['attribute_id']}: {item['failure_count']} failures")


def _generate_batch_markdown_report(batch_assessment, output_file: Path) -> None:
    """Generate Markdown report for batch assessment.

    Args:
        batch_assessment: BatchAssessment object
        output_file: Path to write Markdown report
    """
    lines = [
        "# Batch Assessment Report\n",
        f"**Batch ID**: {batch_assessment.batch_id}\n",
        f"**Timestamp**: {batch_assessment.timestamp.isoformat()}\n",
        f"**AgentReady Version**: {batch_assessment.agentready_version}\n\n",
        "## Summary\n",
        f"- **Total Repositories**: {batch_assessment.summary.total_repositories}\n",
        f"- **Successful Assessments**: {batch_assessment.summary.successful_assessments}\n",
        f"- **Failed Assessments**: {batch_assessment.summary.failed_assessments}\n",
        f"- **Success Rate**: {batch_assessment.get_success_rate():.1f}%\n",
        f"- **Average Score**: {batch_assessment.summary.average_score:.1f}/100\n",
        f"- **Total Duration**: {batch_assessment.total_duration_seconds:.1f}s\n\n",
    ]

    # Score distribution
    if batch_assessment.summary.score_distribution:
        lines.append("## Score Distribution\n")
        for level, count in batch_assessment.summary.score_distribution.items():
            if count > 0:
                lines.append(f"- {level}: {count}\n")
        lines.append("\n")

    # Language breakdown
    if batch_assessment.summary.language_breakdown:
        lines.append("## Language Breakdown\n")
        for lang, count in sorted(
            batch_assessment.summary.language_breakdown.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            lines.append(f"- {lang}: {count}\n")
        lines.append("\n")

    # Top failing attributes
    if batch_assessment.summary.top_failing_attributes:
        lines.append("## Top Failing Attributes\n")
        for item in batch_assessment.summary.top_failing_attributes:
            lines.append(
                f"- {item['attribute_id']}: {item['failure_count']} failures\n"
            )
        lines.append("\n")

    # Results detail
    lines.append("## Individual Results\n")
    for result in batch_assessment.results:
        lines.append(f"\n### {result.repository_url}\n")
        if result.is_success():
            lines.append(f"- **Score**: {result.assessment.overall_score}/100\n")
            lines.append(
                f"- **Certification**: {result.assessment.certification_level}\n"
            )
            lines.append(f"- **Duration**: {result.duration_seconds:.1f}s\n")
            lines.append(f"- **Cached**: {result.cached}\n")
        else:
            lines.append(f"- **Error**: {result.error_type}\n")
            lines.append(f"- **Details**: {result.error}\n")
            lines.append(f"- **Duration**: {result.duration_seconds:.1f}s\n")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
