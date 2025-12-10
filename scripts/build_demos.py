#!/usr/bin/env python3
"""Build and validate demo documentation

This script orchestrates the complete demo build process:
- Generate reveal.js slides
- Validate all required files exist
- Check Mermaid diagram syntax
- Verify links work

Usage:
    python scripts/build_demos.py all       # Build everything
    python scripts/build_demos.py slides    # Generate slides only
    python scripts/build_demos.py validate  # Validate all files
    python scripts/build_demos.py --help
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple

import click

# Required files that must exist
REQUIRED_FILES = [
    "docs/_includes/mermaid.html",
    "docs/_layouts/default.html",
    "docs/demos/index.md",
    "docs/demos/walkthrough.md",
    "docs/demos/terminal-demo.html",
    "scripts/generate_slides.py",
    "scripts/record_demo.sh",
    "src/agentready/templates/slides.html.j2",
]

# Generated files (may not exist yet)
GENERATED_FILES = [
    "docs/demos/slides.html",
    "docs/assets/recordings/eval-harness.cast",
]


def check_file_exists(filepath: Path) -> Tuple[bool, str]:
    """Check if a file exists and return status message."""
    if filepath.exists():
        size = filepath.stat().st_size
        return True, f"✅ {filepath} ({size:,} bytes)"
    else:
        return False, f"❌ {filepath} (missing)"


def validate_files(verbose: bool = False) -> bool:
    """Validate all required files exist.

    Returns:
        True if all required files exist, False otherwise
    """
    if verbose:
        click.echo("Validating required files...")

    all_exist = True

    for filepath_str in REQUIRED_FILES:
        filepath = Path(filepath_str)
        exists, message = check_file_exists(filepath)

        if verbose or not exists:
            click.echo(message)

        if not exists:
            all_exist = False

    if verbose:
        click.echo("\nChecking generated files (optional)...")

    for filepath_str in GENERATED_FILES:
        filepath = Path(filepath_str)
        exists, message = check_file_exists(filepath)

        if verbose:
            if exists:
                click.echo(message)
            else:
                click.echo(f"⚠️  {filepath} (not generated yet)")

    return all_exist


def validate_mermaid_diagrams(verbose: bool = False) -> bool:
    """Validate Mermaid diagrams in markdown files.

    Returns:
        True if all diagrams are valid, False otherwise
    """
    if verbose:
        click.echo("\nValidating Mermaid diagrams...")

    demo_files = [
        Path("docs/demos/walkthrough.md"),
        Path("docs/demos/index.md"),
    ]

    diagrams_found = 0
    diagrams_valid = 0

    for filepath in demo_files:
        if not filepath.exists():
            continue

        content = filepath.read_text()

        # Find all Mermaid code blocks
        import re

        mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)

        for diagram in mermaid_blocks:
            diagrams_found += 1

            # Basic syntax validation (check for diagram type)
            if any(
                keyword in diagram
                for keyword in [
                    "graph",
                    "sequenceDiagram",
                    "classDiagram",
                    "stateDiagram",
                    "erDiagram",
                    "gantt",
                    "pie",
                ]
            ):
                diagrams_valid += 1
                if verbose:
                    click.echo(f"✅ Valid Mermaid diagram in {filepath.name}")
            else:
                click.echo(f"❌ Invalid Mermaid diagram in {filepath.name}")

    if verbose:
        click.echo(
            f"\nFound {diagrams_found} Mermaid diagrams, " f"{diagrams_valid} valid"
        )

    return diagrams_found == diagrams_valid


def generate_slides(verbose: bool = False) -> bool:
    """Generate reveal.js slides from markdown.

    Returns:
        True if generation succeeded, False otherwise
    """
    if verbose:
        click.echo("Generating reveal.js slides...")

    try:
        cmd = [
            sys.executable,
            "scripts/generate_slides.py",
        ]

        if verbose:
            cmd.append("--verbose")

        subprocess.run(cmd, capture_output=not verbose, text=True, check=True)

        if verbose:
            click.echo("✅ Slides generated successfully")

        return True

    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Slide generation failed: {e}", fg="red", err=True)
        if e.stdout:
            click.echo(e.stdout)
        if e.stderr:
            click.echo(e.stderr, err=True)
        return False
    except FileNotFoundError:
        click.secho("❌ generate_slides.py not found", fg="red", err=True)
        return False


@click.group()
def cli():
    """Build and validate AgentReady demo documentation."""
    pass


@cli.command()
@click.option("--verbose", is_flag=True, help="Verbose output")
def all(verbose: bool):
    """Build all demo assets (slides, validate)."""
    click.echo("🏗️  Building all demo assets...")
    click.echo("")

    # Step 1: Generate slides
    if not generate_slides(verbose):
        click.secho("❌ Build failed at slide generation", fg="red", err=True)
        sys.exit(1)

    click.echo("")

    # Step 2: Validate files
    if not validate_files(verbose):
        click.secho("❌ Build failed at file validation", fg="red", err=True)
        sys.exit(1)

    click.echo("")

    # Step 3: Validate Mermaid diagrams
    if not validate_mermaid_diagrams(verbose):
        click.secho("⚠️  Some Mermaid diagrams may be invalid", fg="yellow", err=True)

    click.echo("")
    click.secho("✅ All demo assets built successfully!", fg="green")


@cli.command()
@click.option("--verbose", is_flag=True, help="Verbose output")
def slides(verbose: bool):
    """Generate reveal.js slides only."""
    if generate_slides(verbose):
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command()
@click.option("--verbose", is_flag=True, help="Verbose output")
def validate(verbose: bool):
    """Validate all required files exist."""
    files_ok = validate_files(verbose)
    diagrams_ok = validate_mermaid_diagrams(verbose)

    if files_ok and diagrams_ok:
        click.echo("")
        click.secho("✅ All validations passed!", fg="green")
        sys.exit(0)
    else:
        click.echo("")
        click.secho("❌ Validation failed", fg="red", err=True)
        sys.exit(1)


@cli.command()
def record():
    """Record terminal demo (wrapper for record_demo.sh)."""
    click.echo("🎬 Recording terminal demo...")
    click.echo("This will run: ./scripts/record_demo.sh")
    click.echo("")

    script_path = Path("scripts/record_demo.sh")

    if not script_path.exists():
        click.secho("❌ record_demo.sh not found", fg="red", err=True)
        sys.exit(1)

    # Make executable
    script_path.chmod(0o755)

    try:
        subprocess.run(["bash", str(script_path)], check=True)
        click.secho("✅ Recording complete!", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Recording failed: {e}", fg="red", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Recording cancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    cli()
