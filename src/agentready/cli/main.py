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
from ..utils.security import (
    SENSITIVE_DIRS,
    VAR_SENSITIVE_SUBDIRS,
    _is_path_in_directory,
)
from ..utils.subprocess_utils import safe_subprocess_run

# Lightweight commands - imported immediately
from .align import align
from .benchmark import benchmark, validate_assessor
from .bootstrap import bootstrap
from .demo import demo
from .repomix import repomix_generate
from .research import research
from .schema import migrate_report, validate_report

# Heavy commands - lazy loaded via LazyGroup
# (assess_batch, experiment, extract_skills, harbor, learn, submit)


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
        "harbor": ("harbor", "harbor_cli"),
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
def assess(
    repository,
    verbose,
    output_dir,
    config,
    exclude,
):
    """Assess a repository against agent-ready criteria.

    REPOSITORY: Path to git repository (default: current directory)
    """
    run_assessment(
        repository,
        verbose,
        output_dir,
        config,
        exclude,
    )


def run_assessment(
    repository_path,
    verbose,
    output_dir,
    config_path,
    exclude=None,
):
    """Execute repository assessment."""
    repo_path = Path(repository_path).resolve()

    # Security: Warn when scanning sensitive directories
    # Use centralized constants and proper boundary checking
    is_sensitive = any(
        _is_path_in_directory(repo_path, Path(p)) for p in SENSITIVE_DIRS
    )

    # Special handling for /var subdirectories (macOS)
    # Only warn for specific subdirectories, not temp folders
    if not is_sensitive:
        is_sensitive = any(
            _is_path_in_directory(repo_path, Path(p)) for p in VAR_SENSITIVE_SUBDIRS
        )

    if is_sensitive:
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
    except click.Abort:
        # User declined to continue - re-raise to abort
        raise
    except Exception:
        # If we can't count files quickly (timeout, permission error, etc.), just continue
        pass

    if verbose:
        click.echo("AgentReady Repository Scorer")
        click.echo(f"{'=' * 50}\n")

    # Load configuration if provided
    config = None
    if config_path:
        config = load_config(Path(config_path))
    else:
        config = Config.load_default()

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

    # Merge exclusions from CLI --exclude flag and config.excluded_attributes
    # Fix for #302: config.excluded_attributes was previously ignored
    cli_exclusions = set(exclude or [])
    config_exclusions = set(config.excluded_attributes if config else [])
    all_exclusions = cli_exclusions | config_exclusions

    # Validate exclusions (strict mode) - applies to both CLI and config sources
    if all_exclusions:
        valid_ids = {a.attribute_id for a in all_assessors}
        invalid_ids = all_exclusions - valid_ids
        if invalid_ids:
            # Determine source of invalid IDs for clearer error messages
            invalid_from_cli = invalid_ids & cli_exclusions
            invalid_from_config = invalid_ids & config_exclusions

            # Build error message that includes all invalid IDs from both sources
            msg = ""
            if invalid_from_cli:
                msg = f"Invalid attribute ID(s): {', '.join(sorted(invalid_from_cli))}."
            if invalid_from_config:
                if msg:
                    msg += f" Also invalid in config file: {', '.join(sorted(invalid_from_config))}."
                else:
                    msg = f"Invalid attribute ID(s) in config file: {', '.join(sorted(invalid_from_config))}."
            msg += f" Valid IDs: {', '.join(sorted(valid_ids))}"
            raise click.ClickException(msg)
        # Filter out excluded assessors
        assessors = [a for a in all_assessors if a.attribute_id not in all_exclusions]
        if verbose:
            click.echo(
                f"Excluded {len(all_exclusions)} attribute(s): {', '.join(sorted(all_exclusions))}\n"
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
    click.echo(f"  Assessed: {assessment.attributes_assessed}")
    click.echo(f"  Skipped: {assessment.attributes_not_assessed}")
    click.echo(f"  Total: {assessment.attributes_total}")
    click.echo(f"  Duration: {assessment.duration_seconds:.1f}s")

    # Add assessment results table
    click.echo("\nAssessment Results:")
    click.echo("-" * 100)
    click.echo(f"{'Test Name':<35} {'Test Result':<14} {'Notes':<30}")
    click.echo("-" * 100)

    for finding in sorted(assessment.findings, key=lambda f: f.attribute.id):
        # Status emoji
        status_emoji = (
            "✅"
            if finding.status == "pass"
            else "❌" if finding.status == "fail" else "⏭️"
        )

        # Test Result column: emoji + status
        test_result = f"{status_emoji} {finding.status.upper()}"

        # Notes column: score for PASS, reason for FAIL/SKIP
        if finding.status == "pass":
            notes = f"{finding.score:.0f}/100"
        elif finding.status == "fail":
            # Show measured value vs threshold, or first evidence
            if finding.measured_value and finding.threshold:
                notes = f"{finding.measured_value} (need: {finding.threshold})"
            elif finding.evidence:
                notes = finding.evidence[0]
            else:
                notes = f"{finding.score:.0f}/100"
        elif finding.status in ("not_applicable", "skipped"):
            # Show reason for skip
            notes = finding.evidence[0] if finding.evidence else "Not applicable"
        else:
            # Error or unknown status
            notes = finding.error_message or "Error"

        # Truncate long notes to fit in column
        if len(notes) > 50:
            notes = notes[:47] + "..."

        click.echo(f"{finding.attribute.id:<35} {test_result:<14} {notes:<30}")

    click.echo("-" * 100)

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

        # Validate that data is a dictionary
        if not isinstance(data, dict):
            raise ValueError("Config must be a dict")

        # Pydantic handles all validation automatically
        return Config.from_yaml_dict(data)
    except ValidationError as e:
        # Convert Pydantic validation errors to ValueError with user-friendly messages
        # This allows callers (including tests) to catch and handle validation errors
        errors = e.errors()

        # Check for specific error types and provide user-friendly messages
        if errors:
            first_error = errors[0]
            error_type = first_error.get("type", "")
            field = first_error.get("loc", [])
            field_name = field[0] if field else "unknown"

            # Map Pydantic error types to user-friendly messages
            if error_type == "extra_forbidden":
                unknown_keys = [
                    err.get("loc", [""])[0]
                    for err in errors
                    if err.get("type") == "extra_forbidden"
                ]
                raise ValueError(f"Unknown config keys: {', '.join(unknown_keys)}")
            elif field_name == "weights" and error_type == "dict_type":
                raise ValueError("'weights' must be a dict")
            elif field_name == "weights" and (
                "float_parsing" in error_type or "value_error" in error_type
            ):
                raise ValueError("'weights' values must be positive numbers")
            elif field_name == "excluded_attributes" and error_type == "list_type":
                raise ValueError("'excluded_attributes' must be a list")
            elif field_name == "output_dir":
                # Check if it's a sensitive directory validation error
                # Pydantic wraps ValueError from validators - extract the message
                error_msg = first_error.get("msg", "")
                ctx = first_error.get("ctx", {})

                # Check if error message contains "sensitive"
                if "sensitive" in str(error_msg).lower():
                    # Strip "Value error, " prefix that Pydantic adds
                    msg = str(error_msg).replace("Value error, ", "")
                    raise ValueError(msg)

                # Check if error is in context
                if "error" in ctx:
                    ctx_error = str(ctx.get("error", ""))
                    if "sensitive" in ctx_error.lower():
                        raise ValueError(ctx_error)

                # For other output_dir errors, raise generic message
                raise ValueError(f"Invalid output_dir: {error_msg}")
            elif field_name == "report_theme":
                raise ValueError("'report_theme' must be str")
            else:
                # Generic error message for other validation failures
                field_path = " → ".join(str(x) for x in field)
                raise ValueError(
                    f"Validation failed for '{field_path}': {first_error.get('msg', 'Invalid value')}"
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
    # Try to find example config in current directory first (development mode)
    example_path = Path(".agentready-config.example.yaml")

    if example_path.exists():
        # Read from current directory (development mode)
        example_content = example_path.read_text(encoding="utf-8")
    else:
        # Fall back to package data (pip install mode)
        # Use same pattern as rest of codebase (research_loader.py, scorer.py, etc.)
        try:
            package_data_dir = Path(__file__).parent.parent / "data"
            package_example_path = package_data_dir / ".agentready-config.example.yaml"
            example_content = package_example_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            click.echo(
                "Error: .agentready-config.example.yaml not found in current directory or package data",
                err=True,
            )
            sys.exit(1)

    target = Path(".agentready-config.yaml")

    if target.exists():
        if not click.confirm(f"{target} already exists. Overwrite?"):
            return

    # Write example config to target file
    target.write_text(example_content, encoding="utf-8")
    click.echo(f"Created {target}")
    click.echo("Edit this file to customize weights and behavior.")


# Register lightweight commands (heavy commands loaded lazily via LazyGroup)
cli.add_command(align)
cli.add_command(benchmark)
cli.add_command(validate_assessor)
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
    click.echo(f"AgentReady v{version}")

    # Load research report date
    try:
        loader = ResearchLoader()
        _, metadata, _, _, _ = loader.load_and_validate()
        click.echo(f"Research Report: {metadata.date}")
    except Exception:
        click.echo("Research Report: unknown")


if __name__ == "__main__":
    cli()
