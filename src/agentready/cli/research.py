"""CLI commands for research report management."""

import sys
from pathlib import Path

import click

from ..services.research_formatter import ResearchFormatter
from ..services.research_loader import ResearchLoader


@click.group()
def research():
    """Manage and validate research reports.

    Commands for maintaining RESEARCH_REPORT.md
    following the validation schema.
    """
    pass


@research.command()
@click.argument(
    "report_path",
    type=click.Path(exists=True),
    default="RESEARCH_REPORT.md",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation output")
def validate(report_path, verbose):
    """Validate research report against schema.

    REPORT_PATH: Path to research report (default: RESEARCH_REPORT.md)

    Checks for:
    - Valid metadata header (version, date)
    - Exactly 25 attributes with required sections
    - 4 tier assignments
    - Minimum 20 references
    - Required sections: Definition, Measurable Criteria, Impact on Agent Behavior
    """
    report_file = Path(report_path)

    if verbose:
        click.echo(f"Validating research report: {report_file}")
        click.echo("=" * 60)
        click.echo()

    try:
        # Load research report from custom path
        loader = ResearchLoader(data_dir=report_file.parent)
        loader.research_file = report_file

        content, metadata, is_valid, errors, warnings = loader.load_and_validate()

        # Display metadata
        click.echo(f"Research Report: {report_file.name}")
        click.echo(f"Version: {metadata.version}")
        click.echo(f"Date: {metadata.date}")
        click.echo(f"Attributes: {metadata.attribute_count}")
        click.echo(f"Tiers: {metadata.tier_count}")
        click.echo(f"References: {metadata.reference_count}")
        click.echo()

        # Display validation results
        if errors:
            click.echo("❌ ERRORS (must be fixed):")
            for error in errors:
                click.echo(f"  - {error}")
            click.echo()

        if warnings:
            click.echo("⚠️  WARNINGS (non-critical):")
            for warning in warnings:
                click.echo(f"  - {warning}")
            click.echo()

        # Final verdict
        if is_valid:
            if warnings:
                click.echo("✅ Validation: PASSED with warnings")
                click.echo("   (Warnings can be ignored - report is usable)")
            else:
                click.echo("✅ Validation: PASSED")
            sys.exit(0)
        else:
            click.echo("❌ Validation: FAILED")
            click.echo("   Research report must be fixed before use")
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error during validation: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@research.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="RESEARCH_REPORT.md",
    help="Output file path",
)
@click.option(
    "--template",
    type=click.Path(exists=True),
    default=None,
    help="Template file to use (optional)",
)
def init(output, template):
    """Generate new research report from template.

    Creates a new research report with proper structure including:
    - YAML frontmatter (version, date)
    - 25 attribute placeholders
    - 4 tier sections
    - References section
    """
    output_path = Path(output)

    if output_path.exists():
        if not click.confirm(f"{output_path} already exists. Overwrite?"):
            return

    click.echo(f"Generating new research report: {output_path}")

    formatter = ResearchFormatter()

    if template:
        # Use custom template
        with open(template, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # Generate from scratch
        content = formatter.generate_template()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    click.echo(f"✅ Created {output_path}")
    click.echo("\nNext steps:")
    click.echo("  1. Edit attribute definitions")
    click.echo("  2. Add citations and references")
    click.echo("  3. Validate: agentready research validate")


@research.command()
@click.argument("report_path", type=click.Path(exists=True))
@click.option("--attribute-id", required=True, help="Attribute ID (e.g., '1.3')")
@click.option("--name", required=True, help="Attribute name")
@click.option("--tier", type=int, required=True, help="Tier assignment (1-4)")
@click.option("--category", default="Uncategorized", help="Category name")
def add_attribute(report_path, attribute_id, name, tier, category):
    """Add new attribute to research report.

    REPORT_PATH: Path to research report

    Example:
        agentready research add-attribute research.md \\
            --attribute-id "1.4" \\
            --name "New Attribute" \\
            --tier 2 \\
            --category "Documentation"
    """
    report_file = Path(report_path)

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        formatter = ResearchFormatter()
        new_content = formatter.add_attribute(
            content, attribute_id, name, tier, category
        )

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        click.echo(f"✅ Added attribute {attribute_id}: {name}")
        click.echo(f"   Tier: {tier}, Category: {category}")
        click.echo(f"\nUpdated: {report_file}")
        click.echo("Next: Edit the attribute definition and validate")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@research.command()
@click.argument("report_path", type=click.Path(exists=True))
@click.option(
    "--type",
    "bump_type",
    type=click.Choice(["major", "minor", "patch"]),
    default="patch",
    help="Version bump type (major.minor.patch)",
)
@click.option("--version", "new_version", default=None, help="Explicit version string")
def bump_version(report_path, bump_type, new_version):
    """Update research report version and date.

    REPORT_PATH: Path to research report

    Examples:
        # Bump patch version (1.0.0 -> 1.0.1)
        agentready research bump-version research.md --type patch

        # Bump minor version (1.0.0 -> 1.1.0)
        agentready research bump-version research.md --type minor

        # Set explicit version
        agentready research bump-version research.md --version 2.0.0
    """
    report_file = Path(report_path)

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        formatter = ResearchFormatter()

        if new_version:
            updated_content = formatter.set_version(content, new_version)
            click.echo(f"✅ Set version to: {new_version}")
        else:
            updated_content = formatter.bump_version(content, bump_type)
            # Extract new version
            loader = ResearchLoader()
            metadata = loader.extract_metadata(updated_content)
            click.echo(f"✅ Bumped version ({bump_type}): {metadata.version}")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(updated_content)

        click.echo(f"Updated: {report_file}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@research.command()
@click.argument("report_path", type=click.Path(exists=True))
@click.option("--check", is_flag=True, help="Check formatting without making changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def format(report_path, check, verbose):
    """Lint and format research report.

    REPORT_PATH: Path to research report

    Applies:
    - Consistent markdown formatting
    - Proper heading hierarchy
    - Citation formatting
    - Attribute numbering consistency
    """
    report_file = Path(report_path)

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        formatter = ResearchFormatter()
        formatted_content = formatter.format_report(content)

        if check:
            # Just check if formatting is needed
            if content == formatted_content:
                click.echo("✅ Research report is properly formatted")
                sys.exit(0)
            else:
                click.echo("❌ Research report needs formatting")
                click.echo("   Run without --check to apply changes")
                sys.exit(1)
        else:
            # Apply formatting
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(formatted_content)

            if verbose:
                # Show what changed
                import difflib

                diff = difflib.unified_diff(
                    content.splitlines(keepends=True),
                    formatted_content.splitlines(keepends=True),
                    fromfile=f"{report_file} (before)",
                    tofile=f"{report_file} (after)",
                )
                click.echo("".join(diff))

            click.echo(f"✅ Formatted: {report_file}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
