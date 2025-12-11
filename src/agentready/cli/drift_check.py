"""Drift detection command for Bootstrap templates."""

import sys
from pathlib import Path

import click

from ..services.drift_detector import DriftDetector


@click.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed diffs of drifted files",
)
def drift_check(verbose):
    """Check for template drift in AgentReady repository.

    Compares Bootstrap templates with AgentReady's actual infrastructure
    files to detect drift and ensure templates stay synchronized.

    This command should be run from the AgentReady repository root.

    Examples:

        \b
        # Quick drift check
        agentready drift-check

        \b
        # Detailed drift analysis with diffs
        agentready drift-check --verbose
    """
    repo_path = Path.cwd()

    # Verify we're in AgentReady repository
    if not (repo_path / "src" / "agentready").exists():
        click.echo(
            "❌ Error: This command must be run from AgentReady repository root",
            err=True,
        )
        click.echo("   (Looking for src/agentready/ directory)", err=True)
        sys.exit(1)

    # Create drift detector
    detector = DriftDetector(repo_path)

    # Generate and display drift report
    click.echo("Checking Bootstrap template drift...")
    click.echo()

    report = detector.generate_drift_report(verbose=verbose)
    click.echo(report)

    # Exit with error if drift detected
    drift_data = detector.check_drift(verbose=False)
    if drift_data["drifted"]:
        click.echo()
        click.echo(
            "💡 Tip: Update templates in src/agentready/templates/bootstrap/ to match actual files"
        )
        sys.exit(1)
