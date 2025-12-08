"""Extract-skills command for extracting patterns and generating skills."""

import os
import sys
from pathlib import Path

import click

from ..services.learning_service import LearningService


@click.command("extract-skills")
@click.argument("repository", type=click.Path(exists=True), default=".")
@click.option(
    "--output-format",
    type=click.Choice(
        ["json", "skill_md", "github_issues", "markdown", "all"], case_sensitive=False
    ),
    default="json",
    help="Output format for discovered skills (default: json)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default=".skills-proposals",
    help="Directory for generated skill files (default: .skills-proposals)",
)
@click.option(
    "--attribute",
    multiple=True,
    help="Specific attribute(s) to extract (can be specified multiple times)",
)
@click.option(
    "--min-confidence",
    type=int,
    default=70,
    help="Minimum confidence score to include skills (default: 70)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with detailed skill information",
)
@click.option(
    "--enable-llm",
    is_flag=True,
    help="Enable LLM-powered skill enrichment (requires ANTHROPIC_API_KEY)",
)
@click.option(
    "--llm-budget",
    type=click.IntRange(min=0),
    default=5,
    help="Maximum number of skills to enrich with LLM (default: 5)",
)
@click.option(
    "--llm-no-cache",
    is_flag=True,
    help="Bypass LLM response cache (always call API)",
)
def extract_skills(
    repository,
    output_format,
    output_dir,
    attribute,
    min_confidence,
    verbose,
    enable_llm,
    llm_budget,
    llm_no_cache,
):
    """Extract reusable patterns and generate Claude Code skills.

    Analyzes assessment results to identify successful patterns that could
    be extracted as reusable Claude Code skills for other repositories.

    This command looks for the most recent assessment in .agentready/ and
    extracts skills from high-scoring attributes (default: ≥70% confidence).

    REPOSITORY: Path to repository (default: current directory)

    Examples:

        \b
        # Discover skills from current repository
        agentready extract-skills .

        \b
        # Generate SKILL.md files
        agentready extract-skills . --output-format skill_md

        \b
        # Create GitHub issue templates
        agentready extract-skills . --output-format github_issues

        \b
        # Extract specific attributes only
        agentready extract-skills . --attribute claude_md_file --attribute type_annotations

        \b
        # Generate all formats with higher confidence threshold
        agentready extract-skills . --output-format all --min-confidence 85
    """
    repo_path = Path(repository).resolve()

    # Validate repository exists
    if not repo_path.exists():
        click.echo(f"Error: Repository not found: {repo_path}", err=True)
        sys.exit(1)

    # Resolve output_dir relative to repository if it's relative
    output_dir_path = Path(output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = repo_path / output_dir
    output_dir = str(output_dir_path)

    # Find latest assessment file
    agentready_dir = repo_path / ".agentready"
    if not agentready_dir.exists():
        click.echo(
            "Error: No assessment found in .agentready/\n"
            "Run 'agentready assess .' first to generate an assessment.",
            err=True,
        )
        sys.exit(1)

    # Look for assessment files
    assessment_files = sorted(agentready_dir.glob("assessment-*.json"))
    if not assessment_files:
        click.echo(
            "Error: No assessment files found in .agentready/\n"
            "Run 'agentready assess .' first to generate an assessment.",
            err=True,
        )
        sys.exit(1)

    # Use most recent assessment
    assessment_file = assessment_files[-1]

    # Display header
    click.echo("🧠 AgentReady Skill Extraction")
    click.echo("=" * 50)
    click.echo(f"\nRepository: {repo_path}")
    click.echo(f"Assessment: {assessment_file.name}")
    click.echo(f"Output format: {output_format}")
    click.echo(f"Min confidence: {min_confidence}%")
    if attribute:
        click.echo(f"Filtering attributes: {', '.join(attribute)}")

    # Display LLM status
    if enable_llm:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            click.echo(f"LLM enrichment: ENABLED (budget: {llm_budget} skills)")
            if llm_no_cache:
                click.echo("LLM cache: DISABLED")
        else:
            click.echo("⚠️  LLM enrichment: DISABLED (ANTHROPIC_API_KEY not set)")
            enable_llm = False
    click.echo()

    # Create learning service
    learning_service = LearningService(
        min_confidence=min_confidence,
        output_dir=output_dir,
    )

    # Ensure output directory exists
    learning_service.output_dir.mkdir(parents=True, exist_ok=True)

    # Run learning workflow
    try:
        results = learning_service.run_full_workflow(
            assessment_file=assessment_file,
            output_format=output_format,
            attribute_ids=list(attribute) if attribute else None,
            enable_llm=enable_llm,
            llm_budget=llm_budget,
        )
    except Exception as e:
        click.echo(f"\nError during skill extraction: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Display results
    skills_count = results["skills_discovered"]
    generated_files = results["generated_files"]

    click.echo("=" * 50)
    click.echo(
        f"\n✅ Discovered {skills_count} skill(s) with confidence ≥{min_confidence}%\n"
    )

    # Show LLM info if used
    if enable_llm and skills_count > 0:
        enriched_count = min(llm_budget, skills_count)
        click.echo(f"🤖 LLM-enriched {enriched_count} skill(s)\n")

    if skills_count == 0:
        click.echo("No skills met the confidence threshold.")
        click.echo(
            f"Try lowering --min-confidence (current: {min_confidence}) "
            "or run assessment on a higher-scoring repository."
        )
        return

    # Display discovered skills
    if verbose:
        click.echo("Discovered Skills:")
        click.echo("-" * 50)
        for skill in results["skills"]:
            click.echo(f"\n📚 {skill.name}")
            click.echo(f"   ID: {skill.skill_id}")
            click.echo(f"   Confidence: {skill.confidence}%")
            click.echo(f"   Impact: +{skill.impact_score} pts")
            click.echo(f"   Reusability: {skill.reusability_score}%")
            click.echo(f"   Source: {skill.source_attribute_id}")
            click.echo(f"\n   {skill.pattern_summary}")
        click.echo()

    # Display generated files
    click.echo("\nGenerated Files:")
    click.echo("-" * 50)
    for file_path in generated_files:
        click.echo(f"  ✓ {file_path}")

    # Next steps
    click.echo("\n" + "=" * 50)
    click.echo("\n📖 Next Steps:\n")

    if output_format in ["skill_md", "all"]:
        click.echo("  1. Review generated SKILL.md files in " + output_dir)
        click.echo("  2. Test skills on 3-5 repositories")
        click.echo("  3. Refine instructions based on testing")
        click.echo("  4. Copy to ~/.claude/skills/ or .claude/skills/")

    if output_format in ["github_issues", "all"]:
        click.echo(f"  1. Review issue templates in {output_dir}")
        click.echo("  2. Create GitHub issues:")
        click.echo("     gh issue create --body-file .skills-proposals/skill-*.md")

    if output_format == "json":
        click.echo(f"  1. Review discovered-skills.json in {output_dir}")
        click.echo("  2. Generate other formats:")
        click.echo("     agentready extract-skills . --output-format all")

    click.echo()
