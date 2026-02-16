"""Align command for automated remediation."""

import sys
import textwrap
from pathlib import Path

import click

from ..models.config import Config
from ..services.fixer_service import FixerService
from ..services.scanner import Scanner


def get_certification_level(score: float) -> tuple[str, str]:
    """Get certification level and emoji for score.

    Args:
        score: Score 0-100

    Returns:
        Tuple of (level_name, emoji)
    """
    if score >= 90:
        return ("Platinum", "💎")
    elif score >= 75:
        return ("Gold", "🥇")
    elif score >= 60:
        return ("Silver", "🥈")
    elif score >= 40:
        return ("Bronze", "🥉")
    else:
        return ("Needs Improvement", "📊")


@click.command()
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying them",
)
@click.option(
    "--attributes",
    help="Comma-separated attribute IDs to fix (default: all)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Confirm each fix before applying",
)
def align(repository, dry_run, attributes, interactive):
    """Align repository with best practices by applying automatic fixes.

    Runs assessment, identifies failing attributes, and automatically generates
    and applies fixes to improve the repository's agent-ready score.

    REPOSITORY: Path to repository (default: current directory)
    """
    repo_path = Path(repository).resolve()

    # Validate git repository
    if not (repo_path / ".git").exists():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    click.echo("🔧 AgentReady Align")
    click.echo("=" * 60)
    click.echo(f"\nRepository: {repo_path}")
    if dry_run:
        click.echo("Mode: DRY RUN (preview only)\n")
    else:
        click.echo("Mode: APPLY FIXES\n")

    # Step 1: Run assessment
    click.echo("📊 Running assessment...")
    try:
        # Load config
        config = Config.load_default()

        # Create scanner
        scanner = Scanner(repo_path, config)

        # Create assessors
        from agentready.cli.main import create_all_assessors

        assessors = create_all_assessors()

        # Filter assessors if specific attributes requested
        if attributes:
            attr_set = set(attributes.split(","))
            assessors = [a for a in assessors if a.attribute_id in attr_set]

        # Run assessment
        from agentready.cli.main import get_agentready_version

        version = get_agentready_version()
        assessment = scanner.scan(assessors, verbose=False, version=version)

        current_level, current_emoji = get_certification_level(assessment.overall_score)

        click.echo(
            f"Current Score: {assessment.overall_score:.1f}/100 ({current_level} {current_emoji})"
        )
        click.echo(f"Attributes Assessed: {len(assessment.findings)}")
        click.echo(
            f"Failing Attributes: {sum(1 for f in assessment.findings if f.status == 'fail')}\n"
        )

        # Show full results table
        click.echo("Assessment Results:")
        click.echo("-" * 80)
        click.echo(f"{'Attribute ID':<35} {'Status':<10} {'Score':<10}")
        click.echo("-" * 80)
        for finding in sorted(assessment.findings, key=lambda f: f.attribute.id):
            status_emoji = (
                "✅"
                if finding.status == "pass"
                else "❌" if finding.status == "fail" else "⏭️"
            )
            status_display = f"{status_emoji} {finding.status.upper()}"
            score_display = (
                f"{finding.score:.0f}/100" if finding.score is not None else "N/A"
            )
            click.echo(
                f"{finding.attribute.id:<35} {status_display:<10} {score_display:<10}"
            )
        click.echo("-" * 80)
        click.echo()

    except Exception as e:
        click.echo(f"\nError during assessment: {str(e)}", err=True)
        sys.exit(1)

    # Step 2: Generate fix plan
    click.echo("🔍 Analyzing fixable issues...")

    attribute_list = None
    if attributes:
        attribute_list = [a.strip() for a in attributes.split(",")]

    fixer_service = FixerService()
    fix_plan = fixer_service.generate_fix_plan(
        assessment, assessment.repository, attribute_list
    )

    if not fix_plan.fixes:
        click.echo("\n✅ No automatic fixes available.")
        failing_ids = {
            f.attribute.id for f in assessment.findings if f.status == "fail"
        }
        if "claude_md_file" in failing_ids:
            click.echo(
                "\n💡 Tip: Install the Claude CLI and set ANTHROPIC_API_KEY to "
                "enable automatic CLAUDE.md generation."
            )
        sys.exit(0)

    # Show fix plan
    projected_level, projected_emoji = get_certification_level(fix_plan.projected_score)

    click.echo(f"\nFixes Available: {len(fix_plan.fixes)}")
    click.echo(f"Points to Gain: +{fix_plan.points_gained:.1f}")
    click.echo(
        f"Projected Score: {fix_plan.projected_score:.1f}/100 ({projected_level} {projected_emoji})\n"
    )

    click.echo("Changes to be applied:\n")
    for i, fix in enumerate(fix_plan.fixes, 1):
        click.echo(f"  {i}. [{fix.attribute_id}] {fix.description}")
        click.echo(textwrap.indent(fix.preview(), "     "))
        click.echo(f"     Points: +{fix.points_gained:.1f}\n")

    # Step 3: Confirm or apply
    if dry_run:
        click.echo("=" * 60)
        click.echo("\nDry run complete! Run without --dry-run to apply fixes.")
        return

    # Interactive mode: confirm each fix
    fixes_to_apply = []
    if interactive:
        click.echo("=" * 60)
        click.echo("\nInteractive mode: Confirm each fix\n")
        for fix in fix_plan.fixes:
            if click.confirm(f"Apply fix: {fix.description}?", default=True):
                fixes_to_apply.append(fix)
        click.echo()
    else:
        # Confirm all
        if not click.confirm("\nApply all fixes?", default=True):
            click.echo("Aborted.")
            sys.exit(0)
        fixes_to_apply = fix_plan.fixes

    if not fixes_to_apply:
        click.echo("No fixes selected. Aborted.")
        sys.exit(0)

    # Step 4: Apply fixes
    click.echo(f"\n🔨 Applying {len(fixes_to_apply)} fixes...\n")

    def progress_callback(fix, phase: str, success: bool | None) -> None:
        if fix.attribute_id == "claude_md_file" and phase == "before":
            click.echo("  Generating CLAUDE.md file...")

    results = fixer_service.apply_fixes(
        fixes_to_apply,
        dry_run=False,
        progress_callback=progress_callback,
    )

    # Report results
    click.echo("=" * 60)
    click.echo(f"\n✅ Fixes applied: {results['succeeded']}/{len(fixes_to_apply)}")

    if results["failed"] > 0:
        click.echo(f"❌ Fixes failed: {results['failed']}")
        click.echo("\nFailures:")
        for failure in results["failures"]:
            click.echo(f"  - {failure}")

    click.echo("\nNext steps:")
    click.echo("  1. Review changes: git status")
    click.echo("  2. Test the changes")
    click.echo(
        "  3. Commit: git add . && git commit -m 'chore: Apply AgentReady fixes'"
    )
    click.echo("  4. Run assessment again: agentready assess .")
