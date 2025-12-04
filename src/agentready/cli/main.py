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

from pydantic import ValidationError

from ..assessors import create_all_assessors
from ..models.config import Config
from ..reporters.html import HTMLReporter
from ..reporters.markdown import MarkdownReporter
from ..services.research_loader import ResearchLoader
from ..services.scanner import Scanner
from ..utils.subprocess_utils import safe_subprocess_run

# Lightweight commands - imported immediately
from .align import align
from .bootstrap import bootstrap
from .demo import demo
from .repomix import repomix_generate
from .research import research
from .schema import migrate_report, validate_report

# Heavy commands - lazy loaded via LazyGroup
# (assess_batch, experiment, extract_skills, learn, submit)


def get_agentready_version() -> str:
    """Get AgentReady version from package metadata.

    Returns:
        Version string (e.g., "1.0.0") or "unknown" if not installed
    """
    try:
        return get_version("agentready")
    except Exception:
        return "unknown"


class LazyGroup(click.Group):
    """Click group that lazily loads heavy commands to improve startup time.

    Commands like 'experiment', 'extract-skills', and 'assess-batch' import heavy
    dependencies (scipy, pandas, anthropic) that add ~1 second to startup time.
    This class defers those imports until the command is actually invoked.
    """

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        """Return list of all command names (including lazy ones)."""
        base_commands = super().list_commands(ctx)
        return sorted(list(base_commands) + list(self.lazy_subcommands.keys()))

    def get_command(self, ctx, cmd_name):
        """Load command on-demand."""
        # Try normal (already loaded) commands first
        command = super().get_command(ctx, cmd_name)
        if command:
            return command

        # Try lazy commands
        if cmd_name in self.lazy_subcommands:
            module_name, command_name = self.lazy_subcommands[cmd_name]
            module = __import__(
                f"agentready.cli.{module_name}", fromlist=[command_name]
            )
            command = getattr(module, command_name)
            # Cache the loaded command for future use
            self.add_command(command, cmd_name)
            return command

        return None


@click.group(
    invoke_without_command=True,
    cls=LazyGroup,
    lazy_subcommands={
        "assess-batch": ("assess_batch", "assess_batch"),
        "experiment": ("experiment", "experiment"),
        "extract-skills": ("extract_skills", "extract_skills"),
        "learn": ("learn", "learn"),
        "submit": ("submit", "submit"),
    },
)
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
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Attribute ID(s) to exclude (can be specified multiple times)",
)
def assess(repository, verbose, output_dir, config, exclude):
    """Assess a repository against agent-ready criteria.

    REPOSITORY: Path to git repository (default: current directory)
    """
    run_assessment(repository, verbose, output_dir, config, exclude)


def run_assessment(repository_path, verbose, output_dir, config_path, exclude=None):
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

    # Create all assessors first
    all_assessors = create_all_assessors()

    # Validate exclusions (strict mode)
    if exclude:
        valid_ids = {a.attribute_id for a in all_assessors}
        invalid_ids = set(exclude) - valid_ids
        if invalid_ids:
            raise click.BadParameter(
                f"Invalid attribute ID(s): {', '.join(sorted(invalid_ids))}. "
                f"Valid IDs: {', '.join(sorted(valid_ids))}"
            )
        # Filter out excluded assessors
        assessors = [a for a in all_assessors if a.attribute_id not in exclude]
        if verbose and exclude:
            click.echo(
                f"Excluded {len(exclude)} attribute(s): {', '.join(sorted(exclude))}\n"
            )
    else:
        assessors = all_assessors

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
    """Load configuration from YAML file with Pydantic validation.

    Uses Pydantic for automatic validation, replacing 67 lines of manual
    validation code with declarative field validators.

    Security: Uses yaml.safe_load() for safe YAML parsing and Pydantic
    validators for type checking and path sanitization.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated Config instance

    Raises:
        ValidationError: If YAML data doesn't match expected schema
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
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


# Register lightweight commands (heavy commands loaded lazily via LazyGroup)
cli.add_command(align)
cli.add_command(bootstrap)
cli.add_command(demo)
cli.add_command(migrate_report)
cli.add_command(repomix_generate)
cli.add_command(research)
cli.add_command(validate_report)
# Lazy-loaded commands (not registered here):
#   - assess-batch (imports pandas)
#   - experiment (imports scipy, pandas)
#   - extract-skills (imports anthropic)
#   - learn (imports anthropic)
#   - submit (imports github)


def show_version():
    """Show version information."""
    version = get_agentready_version()
    click.echo(f"AgentReady Repository Scorer v{version}")
    click.echo("Research Report: bundled")


if __name__ == "__main__":
    cli()
