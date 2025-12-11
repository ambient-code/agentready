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
@click.option(
    "--enable-release",
    is_flag=True,
    help="Enable automated release workflow with semantic versioning",
)
@click.option(
    "--enable-publishing",
    is_flag=True,
    help="Enable package publishing (PyPI/npm/GitHub Releases)",
)
@click.option(
    "--enable-all",
    is_flag=True,
    help="Enable all advanced features (release + publishing)",
)
def bootstrap(
    repository, dry_run, language, enable_release, enable_publishing, enable_all
):
    """Bootstrap repository with GitHub infrastructure and best practices.

    Creates:
    - GitHub Actions workflows (tests, AgentReady assessment, security)
    - GitHub templates (issues, pull requests, CODEOWNERS)
    - Pre-commit hooks configuration
    - Dependabot configuration
    - Contributing guidelines

    Advanced features (opt-in):
    - Release automation with semantic versioning (--enable-release)
    - Package publishing to PyPI/npm (--enable-publishing)
    - All advanced features (--enable-all)

    REPOSITORY: Path to git repository (default: current directory)

    Examples:

        \b
        # Basic bootstrap
        agentready bootstrap .

        \b
        # With release automation
        agentready bootstrap . --enable-release

        \b
        # Full automation
        agentready bootstrap . --enable-all
    """
    repo_path = Path(repository).resolve()

    # Validate git repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    # Handle --enable-all flag
    if enable_all:
        enable_release = True
        enable_publishing = True

    click.echo("🤖 AgentReady Bootstrap")
    click.echo("=" * 50)
    click.echo(f"\nRepository: {repo_path}")
    click.echo(f"Language: {language}")
    click.echo(f"Dry run: {dry_run}")
    if enable_release:
        click.echo("Release automation: ENABLED")
    if enable_publishing:
        click.echo("Package publishing: ENABLED")
    click.echo()

    # Create generator
    generator = BootstrapGenerator(
        repo_path,
        language,
        enable_release=enable_release,
        enable_publishing=enable_publishing,
    )

    # Generate all files
    try:
        created_files = generator.generate_all(dry_run=dry_run)
    except Exception as e:
        click.echo(f"\nError during bootstrap: {str(e)}", err=True)
        sys.exit(1)

    # Report results
    click.echo("\n" + "=" * 50)
    if dry_run:
        click.echo("\nDry run complete! The following files would be created:")
    else:
        click.echo(f"\nBootstrap complete! Created {len(created_files)} files:")

    for file_path in sorted(created_files):
        rel_path = file_path.relative_to(repo_path)
        click.echo(f"  ✓ {rel_path}")

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
