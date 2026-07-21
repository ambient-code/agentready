"""Bootstrap command for setting up GitHub infrastructure."""

import sys
from pathlib import Path

import click

from ..services.bootstrap import BootstrapGenerator


@click.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without creating files",
)
@click.option(
    "--language",
    type=click.Choice(["python", "javascript", "go", "auto"], case_sensitive=False),
    default="auto",
    help="Primary language (default: auto-detect)",
)
def bootstrap(repository, dry_run, language):
    """Bootstrap repository with GitHub infrastructure and best practices.

    Creates:
    - GitHub Actions workflows (tests, AgentReady assessment, security)
    - GitHub templates (issues, pull requests, CODEOWNERS)
    - Pre-commit hooks configuration
    - Dependabot configuration
    - Contributing guidelines

    Existing files are never overwritten; they are reported as skipped.

    REPOSITORY: Path to git repository (default: current directory)
    """
    repo_path = Path(repository).resolve()

    # Validate git repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    click.echo("🤖 AgentReady Bootstrap")
    click.echo("=" * 50)
    click.echo(f"\nRepository: {repo_path}")
    click.echo(f"Language: {language}")
    click.echo(f"Dry run: {dry_run}\n")

    # Create generator
    generator = BootstrapGenerator(repo_path, language)

    # Generate all files
    try:
        result = generator.generate_all(dry_run=dry_run)
    except Exception as e:
        click.echo(f"\nError during bootstrap: {str(e)}", err=True)
        sys.exit(1)

    # Report results
    click.echo("\n" + "=" * 50)
    created_label = "Would create" if dry_run else "Created"
    skipped_label = "Would skip" if dry_run else "Skipped"

    if dry_run:
        click.echo("\nDry run complete!")
    else:
        click.echo("\nBootstrap complete!")

    click.echo(f"\n{created_label} {len(result.created_files)} file(s):")
    if result.created_files:
        for file_path in sorted(result.created_files):
            rel_path = file_path.relative_to(repo_path)
            click.echo(f"  ✓ {rel_path}")
    else:
        click.echo("  (none)")

    click.echo(
        f"\n{skipped_label} {len(result.skipped_files)} file(s) " "(already exists):"
    )
    if result.skipped_files:
        for file_path in sorted(result.skipped_files):
            rel_path = file_path.relative_to(repo_path)
            click.echo(f"  · {rel_path}")
    else:
        click.echo("  (none)")

    if not dry_run:
        click.echo("\n✅ Repository bootstrapped successfully!")
        click.echo("\nNext steps:")
        click.echo("  1. Review generated files")
        click.echo(
            "  2. Commit changes: git add . && git commit -m 'chore: Bootstrap repository infrastructure'"
        )
        click.echo("  3. Push to GitHub: git push")
        click.echo("  4. Set up branch protection rules")
        click.echo("  5. Enable GitHub Actions")
    else:
        click.echo("\nRun without --dry-run to create files")
