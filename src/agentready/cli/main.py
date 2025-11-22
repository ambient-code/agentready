"""CLI entry point for agentready tool."""

import json
import sys
from pathlib import Path

import click

try:
    from importlib.metadata import version as get_version
except ImportError:
    # Python 3.7 compatibility
    from importlib_metadata import version as get_version

from ..assessors.code_quality import (
    CyclomaticComplexityAssessor,
    TypeAnnotationsAssessor,
)

# Import all assessors
from ..assessors.documentation import CLAUDEmdAssessor, READMEAssessor
from ..assessors.structure import OneCommandSetupAssessor, StandardLayoutAssessor
from ..assessors.stub_assessors import (
    ConventionalCommitsAssessor,
    GitignoreAssessor,
    LockFilesAssessor,
    create_stub_assessors,
)
from ..assessors.testing import PreCommitHooksAssessor, TestCoverageAssessor
from ..models.config import Config
from ..reporters.html import HTMLReporter
from ..reporters.markdown import MarkdownReporter
from ..services.research_loader import ResearchLoader
from ..services.scanner import Scanner
from ..utils.subprocess_utils import safe_subprocess_run
from .align import align
from .bootstrap import bootstrap
from .demo import demo
from .learn import learn
from .repomix import repomix_generate
from .research import research
from .schema import migrate_report, validate_report


def get_agentready_version() -> str:
    """Get AgentReady version from package metadata.

    Returns:
        Version string (e.g., "1.0.0") or "unknown" if not installed
    """
    try:
        return get_version("agentready")
    except Exception:
        return "unknown"


def create_all_assessors():
    """Create all 25 assessors for assessment."""
    assessors = [
        # Tier 1 Essential (5 assessors)
        CLAUDEmdAssessor(),
        READMEAssessor(),
        TypeAnnotationsAssessor(),
        StandardLayoutAssessor(),
        LockFilesAssessor(),
        # Tier 2 Critical (10 assessors - 4 implemented, 6 stubs)
        TestCoverageAssessor(),
        PreCommitHooksAssessor(),
        ConventionalCommitsAssessor(),
        GitignoreAssessor(),
        OneCommandSetupAssessor(),
        CyclomaticComplexityAssessor(),  # Actually Tier 3, but including here
    ]

    # Add remaining stub assessors
    assessors.extend(create_stub_assessors())

    return assessors


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx, version):
    """AgentReady Repository Scorer - Assess repositories for AI-assisted development.

    Evaluates repositories against 25 evidence-based attributes and generates
    comprehensive reports with scores, findings, and remediation guidance.

    Examples:

        \b
        # Assess current repository
        agentready assess .

        \b
        # Assess with custom configuration
        agentready assess /path/to/repo --config my-config.yaml

        \b
        # Show research version
        agentready research-version

        \b
        # Generate example config
        agentready generate-config
    """
    if version:
        show_version()
        ctx.exit()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("repository", type=click.Path(exists=True), required=False, default=".")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory for reports (default: .agentready/)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file",
)
def assess(repository, verbose, output_dir, config):
    """Assess a repository against agent-ready criteria.

    REPOSITORY: Path to git repository (default: current directory)
    """
    run_assessment(repository, verbose, output_dir, config)


def run_assessment(repository_path, verbose, output_dir, config_path):
    """Execute repository assessment."""
    repo_path = Path(repository_path).resolve()

    # Security: Warn when scanning sensitive directories
    sensitive_dirs = ["/etc", "/sys", "/proc", "/.ssh", "/var"]
    if any(str(repo_path).startswith(p) for p in sensitive_dirs):
        click.confirm(
            f"⚠️  Warning: Scanning sensitive directory {repo_path}. Continue?",
            abort=True,
        )

    # Performance: Warn for large repositories
    try:
        # Quick file count using git ls-files (if it's a git repo) or fallback
        # Security: Use safe_subprocess_run for validation and limits
        result = safe_subprocess_run(
            ["git", "ls-files"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            file_count = len(result.stdout.splitlines())
        else:
            # Not a git repo, use glob (slower but works)
            file_count = sum(1 for _ in repo_path.rglob("*") if _.is_file())

        if file_count > 10000:
            click.confirm(
                f"⚠️  Warning: Large repository detected ({file_count:,} files). "
                "Assessment may take several minutes. Continue?",
                abort=True,
            )
    except Exception:
        # If we can't count files quickly, just continue
        pass

    if verbose:
        click.echo("AgentReady Repository Scorer")
        click.echo(f"{'=' * 50}\n")

    # Load configuration if provided
    config = None
    if config_path:
        config = load_config(Path(config_path))

    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = repo_path / ".agentready"

    output_path.mkdir(parents=True, exist_ok=True)

    # Create scanner
    try:
        scanner = Scanner(repo_path, config)
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

    # Create assessors
    assessors = create_all_assessors()

    if verbose:
        click.echo(f"Repository: {repo_path}")
        click.echo(f"Assessors: {len(assessors)}")
        click.echo(f"Output: {output_path}\n")

    # Run scan
    try:
        version = get_agentready_version()
        assessment = scanner.scan(assessors, verbose=verbose, version=version)
    except Exception as e:
        click.echo(f"Error during assessment: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Generate timestamp for file naming
    timestamp = assessment.timestamp.strftime("%Y%m%d-%H%M%S")

    # Save JSON output
    json_file = output_path / f"assessment-{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(assessment.to_dict(), f, indent=2)

    # Generate HTML report
    html_reporter = HTMLReporter()
    html_file = output_path / f"report-{timestamp}.html"
    html_reporter.generate(assessment, html_file)

    # Generate Markdown report
    markdown_reporter = MarkdownReporter()
    markdown_file = output_path / f"report-{timestamp}.md"
    markdown_reporter.generate(assessment, markdown_file)

    # Create latest symlinks
    latest_json = output_path / "assessment-latest.json"
    latest_html = output_path / "report-latest.html"
    latest_md = output_path / "report-latest.md"

    for latest, target in [
        (latest_json, json_file),
        (latest_html, html_file),
        (latest_md, markdown_file),
    ]:
        if latest.exists():
            latest.unlink()
        try:
            latest.symlink_to(target.name)
        except OSError:
            # Windows doesn't support symlinks easily, just copy
            import shutil

            shutil.copy(target, latest)

    if verbose:
        click.echo(f"\n{'=' * 50}")

    click.echo("\nAssessment complete!")
    click.echo(
        f"  Score: {assessment.overall_score:.1f}/100 ({assessment.certification_level})"
    )
    click.echo(
        f"  Assessed: {assessment.attributes_assessed}/{assessment.attributes_total}"
    )
    click.echo(f"  Skipped: {assessment.attributes_not_assessed}")
    click.echo(f"  Duration: {assessment.duration_seconds:.1f}s")
    click.echo("\nReports generated:")
    click.echo(f"  JSON: {json_file}")
    click.echo(f"  HTML: {html_file}")
    click.echo(f"  Markdown: {markdown_file}")


def load_config(config_path: Path) -> Config:
    """Load configuration from YAML file with validation.

    Security: Validates YAML structure to prevent injection attacks
    and malformed data from causing crashes or unexpected behavior.
    """
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Security: Validate data is a dict
    if not isinstance(data, dict):
        raise ValueError(
            f"Config must be a YAML object/dict, got {type(data).__name__}"
        )

    # Security: Validate expected keys and reject unknown keys
    allowed_keys = {
        "weights",
        "excluded_attributes",
        "language_overrides",
        "output_dir",
        "report_theme",
        "custom_theme",
    }
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown_keys))}")

    # Security: Validate weights is dict[str, float]
    weights = data.get("weights", {})
    if not isinstance(weights, dict):
        raise ValueError(f"'weights' must be a dict, got {type(weights).__name__}")
    for key, value in weights.items():
        if not isinstance(key, str):
            raise ValueError(f"Weight keys must be strings, got {type(key).__name__}")
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Weight values must be numbers, got {type(value).__name__} for '{key}'"
            )

    # Security: Validate excluded_attributes is list[str]
    excluded = data.get("excluded_attributes", [])
    if not isinstance(excluded, list):
        raise ValueError(
            f"'excluded_attributes' must be a list, got {type(excluded).__name__}"
        )
    for item in excluded:
        if not isinstance(item, str):
            raise ValueError(
                f"'excluded_attributes' items must be strings, got {type(item).__name__}"
            )

    # Security: Validate language_overrides is dict[str, list[str]]
    lang_overrides = data.get("language_overrides", {})
    if not isinstance(lang_overrides, dict):
        raise ValueError(
            f"'language_overrides' must be a dict, got {type(lang_overrides).__name__}"
        )
    for lang, patterns in lang_overrides.items():
        if not isinstance(lang, str):
            raise ValueError(
                f"'language_overrides' keys must be strings, got {type(lang).__name__}"
            )
        if not isinstance(patterns, list):
            raise ValueError(
                f"'language_overrides' values must be lists, got {type(patterns).__name__}"
            )
        for pattern in patterns:
            if not isinstance(pattern, str):
                raise ValueError(
                    f"'language_overrides' patterns must be strings, got {type(pattern).__name__}"
                )

    # Security: Validate and sanitize output_dir to prevent path traversal
    output_dir = None
    if "output_dir" in data:
        output_dir_str = data["output_dir"]
        if not isinstance(output_dir_str, str):
            raise ValueError(
                f"'output_dir' must be a string, got {type(output_dir_str).__name__}"
            )

        output_dir = Path(output_dir_str).resolve()

        # Prevent absolute paths to system directories
        sensitive_dirs = ["/etc", "/sys", "/proc", "/var", "/usr", "/bin", "/sbin"]
        if any(str(output_dir).startswith(p) for p in sensitive_dirs):
            raise ValueError(
                f"'output_dir' cannot be in sensitive system directory: {output_dir}"
            )

    # Security: Validate report_theme is string
    report_theme = data.get("report_theme", "default")
    if not isinstance(report_theme, str):
        raise ValueError(
            f"'report_theme' must be a string, got {type(report_theme).__name__}"
        )

    # Security: Validate custom_theme is dict[str, str] if provided
    custom_theme = data.get("custom_theme")
    if custom_theme is not None:
        if not isinstance(custom_theme, dict):
            raise ValueError(
                f"'custom_theme' must be a dict, got {type(custom_theme).__name__}"
            )
        for key, value in custom_theme.items():
            if not isinstance(key, str):
                raise ValueError(
                    f"'custom_theme' keys must be strings, got {type(key).__name__}"
                )
            if not isinstance(value, str):
                raise ValueError(
                    f"'custom_theme' values must be strings, got {type(value).__name__}"
                )

    return Config(
        weights=weights,
        excluded_attributes=excluded,
        language_overrides=lang_overrides,
        output_dir=output_dir,
        report_theme=report_theme,
        custom_theme=custom_theme,
    )


@cli.command()
def research_version():
    """Show bundled research report version."""
    loader = ResearchLoader()
    try:
        content, metadata, is_valid, errors, warnings = loader.load_and_validate()

        click.echo(f"Research Report Version: {metadata.version}")
        click.echo(f"Date: {metadata.date}")
        click.echo(f"Attributes: {metadata.attribute_count}")
        click.echo(f"References: {metadata.reference_count}")
        click.echo(f"\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'}")

        if errors:
            click.echo("\nErrors:")
            for error in errors:
                click.echo(f"  - {error}")

        if warnings:
            click.echo("\nWarnings:")
            for warning in warnings:
                click.echo(f"  - {warning}")

    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def generate_config():
    """Generate example configuration file."""
    example_path = Path(".agentready-config.example.yaml")

    if not example_path.exists():
        click.echo("Error: .agentready-config.example.yaml not found", err=True)
        sys.exit(1)

    target = Path(".agentready-config.yaml")

    if target.exists():
        if not click.confirm(f"{target} already exists. Overwrite?"):
            return

    import shutil

    shutil.copy(example_path, target)
    click.echo(f"Created {target}")
    click.echo("Edit this file to customize weights and behavior.")


# Register commands
cli.add_command(align)
cli.add_command(bootstrap)
cli.add_command(demo)
cli.add_command(learn)
cli.add_command(migrate_report)
cli.add_command(repomix_generate)
cli.add_command(research)
cli.add_command(validate_report)


def show_version():
    """Show version information."""
    version = get_agentready_version()
    click.echo(f"AgentReady Repository Scorer v{version}")
    click.echo("Research Report: bundled")


if __name__ == "__main__":
    cli()
