"""CLI commands for schema validation and migration."""

import sys
from pathlib import Path

import click

from ..services.schema_migrator import SchemaMigrationError, SchemaMigrator
from ..services.schema_validator import SchemaValidator


@click.command(name="validate-report")
@click.argument("report", type=click.Path(exists=True), required=True)
@click.option(
    "--strict/--no-strict",
    default=True,
    help="Strict validation (fail on unknown properties)",
)
def validate_report(report, strict):
    """Validate assessment report against its schema version.

    REPORT: Path to JSON assessment report file

    Examples:

        \b
        # Validate report with strict checking
        agentready validate-report assessment-20251122.json

        \b
        # Validate with lenient mode (allow extra fields)
        agentready validate-report --no-strict assessment-20251122.json
    """
    report_path = Path(report)

    try:
        validator = SchemaValidator()
    except ImportError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nInstall jsonschema to use report validation:", err=True)
        click.echo("  pip install jsonschema", err=True)
        sys.exit(1)

    click.echo(f"Validating report: {report_path}")
    click.echo(f"Strict mode: {strict}\n")

    is_valid, errors = validator.validate_report_file(report_path, strict=strict)

    if is_valid:
        click.echo("✅ Report is valid!")
        sys.exit(0)
    else:
        click.echo("❌ Report validation failed:\n", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)


@click.command(name="migrate-report")
@click.argument("input_report", type=click.Path(exists=True), required=True)
@click.option(
    "--from",
    "from_version",
    type=str,
    default=None,
    help="Source schema version (auto-detected if not specified)",
)
@click.option(
    "--to",
    "to_version",
    type=str,
    required=True,
    help="Target schema version (e.g., 2.0.0)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: INPUT_REPORT with version suffix)",
)
def migrate_report(input_report, from_version, to_version, output):
    """Migrate assessment report to a different schema version.

    INPUT_REPORT: Path to source JSON assessment report file

    Examples:

        \b
        # Migrate report to version 2.0.0
        agentready migrate-report assessment-20251122.json --to 2.0.0

        \b
        # Migrate with custom output path
        agentready migrate-report old-report.json --to 2.0.0 --output new-report.json
    """
    input_path = Path(input_report)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Default: add version suffix to input filename
        stem = input_path.stem
        output_path = input_path.parent / f"{stem}-migrated-v{to_version}.json"

    click.echo(f"Migrating report: {input_path}")
    if from_version:
        click.echo(f"From version: {from_version}")
    else:
        click.echo("From version: (auto-detect)")
    click.echo(f"To version: {to_version}")
    click.echo(f"Output: {output_path}\n")

    try:
        migrator = SchemaMigrator()
        migrator.migrate_report_file(input_path, output_path, to_version)

        click.echo("✅ Migration successful!")
        click.echo(f"Migrated report saved to: {output_path}")
        sys.exit(0)

    except SchemaMigrationError as e:
        click.echo(f"❌ Migration failed: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        sys.exit(1)
