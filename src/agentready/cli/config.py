"""Configuration management commands."""

import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from ..assessors import create_all_assessors
from ..models.config import Config


@click.group()
def config():
    """Manage configuration files."""
    pass


@config.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation info")
def validate(config_path, verbose):
    """Validate configuration file.

    CONFIG_PATH: Path to .agentready.yaml or .agentready-config.yaml file

    Checks for:
    - Valid YAML syntax
    - Valid attribute IDs (match existing assessors)
    - Positive weight values
    - Valid path references
    - Reasonable weight distributions (warnings)

    Examples:

        \b
        # Validate config file
        agentready config validate .agentready.yaml

        \b
        # Validate with verbose output
        agentready config validate my-config.yaml --verbose
    """
    config_file = Path(config_path)

    if verbose:
        click.echo(f"Validating: {config_file}")
        click.echo("=" * 50)

    try:
        # Load YAML
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if verbose:
            click.echo(f"✓ YAML syntax valid")

        # Validate with Pydantic
        config_obj = Config.from_yaml_dict(data)

        if verbose:
            click.echo(f"✓ Schema validation passed")

        # Additional semantic checks
        warnings = []
        errors = []

        # Get all valid attribute IDs from assessors
        assessors = create_all_assessors()
        valid_ids = {assessor.attribute_id for assessor in assessors}

        if verbose:
            click.echo(f"✓ Loaded {len(valid_ids)} valid attribute IDs")

        # Check attribute IDs in weights
        for attr_id in config_obj.weights.keys():
            if attr_id not in valid_ids:
                warnings.append(f"Unknown attribute ID in weights: '{attr_id}'")

        # Check attribute IDs in exclusions
        for attr_id in config_obj.excluded_attributes:
            if attr_id not in valid_ids:
                warnings.append(f"Unknown attribute ID in exclusions: '{attr_id}'")

        # Check weight distribution (should sum close to 1.0, but auto-normalized)
        if config_obj.weights:
            total_weight = sum(config_obj.weights.values())
            if abs(total_weight - 1.0) > 0.01:
                warnings.append(
                    f"Weights sum to {total_weight:.3f} (expected ~1.0). "
                    "Scorer will auto-normalize, but this may indicate a typo."
                )

        # Check for conflicting settings
        excluded_with_weights = set(config_obj.excluded_attributes) & set(
            config_obj.weights.keys()
        )
        if excluded_with_weights:
            warnings.append(
                f"Attributes both excluded and weighted (exclusion takes precedence): "
                f"{', '.join(sorted(excluded_with_weights))}"
            )

        # Check output directory if specified
        if config_obj.output_dir:
            output_dir = Path(config_obj.output_dir)
            if output_dir.exists() and not output_dir.is_dir():
                errors.append(
                    f"output_dir exists but is not a directory: {output_dir}"
                )

        if verbose:
            click.echo(f"✓ Semantic validation complete")
            click.echo()

        # Print results
        if not errors and not warnings:
            click.echo(f"✅ Config valid: {config_file}")
            sys.exit(0)

        if errors:
            click.echo(f"❌ Config validation failed: {config_file}", err=True)
            click.echo("\nErrors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        # Warnings only
        click.echo(f"⚠️  Config valid with warnings: {config_file}")
        click.echo("\nWarnings:")
        for warning in warnings:
            click.echo(f"  - {warning}")
        sys.exit(0)

    except yaml.YAMLError as e:
        click.echo(f"❌ YAML syntax error: {config_file}", err=True)
        click.echo(f"  {str(e)}", err=True)
        sys.exit(1)

    except ValidationError as e:
        click.echo(f"❌ Config validation failed: {config_file}", err=True)
        click.echo("\nSchema errors:", err=True)
        for error in e.errors():
            field = " → ".join(str(x) for x in error["loc"])
            click.echo(f"  - {field}: {error['msg']}", err=True)
        sys.exit(1)

    except FileNotFoundError:
        click.echo(f"❌ File not found: {config_file}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@config.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=".agentready.yaml",
    help="Output file path (default: .agentready.yaml)",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing file")
def init(output, force):
    """Initialize config file from template.

    Creates a new configuration file based on the example template.
    By default, creates .agentready.yaml in the current directory.

    Examples:

        \b
        # Initialize default config
        agentready config init

        \b
        # Initialize with custom name
        agentready config init --output my-config.yaml

        \b
        # Overwrite existing file
        agentready config init --force
    """
    output_path = Path(output)

    # Check if file exists
    if output_path.exists() and not force:
        if not click.confirm(f"File {output_path} already exists. Overwrite?"):
            click.echo("Cancelled.")
            sys.exit(0)

    # Find example config file
    # It should be in the package root (same level as src/)
    example_path = Path(__file__).parent.parent.parent.parent / ".agentready-config.example.yaml"

    if not example_path.exists():
        # Fallback: try relative to current directory
        example_path = Path(".agentready-config.example.yaml")

    if not example_path.exists():
        click.echo(
            "❌ Error: .agentready-config.example.yaml not found", err=True
        )
        click.echo(
            "   This file should be in the AgentReady repository root.", err=True
        )
        sys.exit(1)

    # Copy example to target
    try:
        import shutil

        shutil.copy(example_path, output_path)
        click.echo(f"✅ Created config: {output_path}")
        click.echo(
            "\nEdit this file to customize attribute weights, exclusions, and themes."
        )
        click.echo("Run 'agentready config validate' to check your changes.")

    except Exception as e:
        click.echo(f"❌ Error creating config: {str(e)}", err=True)
        sys.exit(1)
