"""CLI command for submitting assessments to the AgentReady leaderboard."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import click
from github import Github, GithubException


@click.command()
@click.argument("repository", type=click.Path(exists=True), required=False, default=".")
@click.option(
    "-f",
    "--file",
    "assessment_file",
    type=click.Path(exists=True),
    help="Path to assessment JSON file (default: latest in .agentready/)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be submitted without creating PR"
)
def submit(repository, assessment_file, dry_run):
    """Submit assessment results to AgentReady leaderboard.

    Creates a PR to agentready/agentready with your assessment results.
    Requires GITHUB_TOKEN environment variable.

    Examples:

        \b
        # Submit current repository (uses latest assessment)
        agentready submit

        \b
        # Submit specific assessment file
        agentready submit -f .agentready/assessment-20251203-143045.json

        \b
        # Preview submission without creating PR
        agentready submit --dry-run
    """
    # 1. Validate GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        click.echo("Error: GITHUB_TOKEN environment variable not set", err=True)
        click.echo(
            "\nCreate token at: https://github.com/settings/tokens/new", err=True
        )
        click.echo(
            "Required scopes: public_repo (for creating PRs to public repos)", err=True
        )
        click.echo("\nThen set it: export GITHUB_TOKEN=ghp_your_token_here", err=True)
        sys.exit(1)

    # 2. Find assessment file
    repo_path = Path(repository).resolve()
    if assessment_file:
        assessment_path = Path(assessment_file).resolve()
    else:
        latest = repo_path / ".agentready" / "assessment-latest.json"
        if not latest.exists():
            click.echo(
                "Error: No assessment found. Run 'agentready assess' first.", err=True
            )
            sys.exit(1)
        # Resolve symlink to actual file
        assessment_path = latest.resolve() if latest.is_symlink() else latest

    # 3. Load and validate assessment
    try:
        with open(assessment_path, encoding="utf-8") as f:
            assessment_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        click.echo(f"Error: Failed to read assessment file: {e}", err=True)
        sys.exit(1)

    # Extract metadata
    try:
        repo_url = assessment_data["repository"]["url"]
        score = assessment_data["overall_score"]
        tier = assessment_data["certification_level"]
    except KeyError as e:
        click.echo(f"Error: Invalid assessment JSON (missing {e})", err=True)
        sys.exit(1)

    # 4. Extract org/repo from URL (handle both HTTPS and SSH formats)
    if "github.com" not in repo_url:
        click.echo(
            "Error: Only GitHub repositories are supported for the leaderboard",
            err=True,
        )
        click.echo(f"Repository URL: {repo_url}", err=True)
        sys.exit(1)

    try:
        # Handle SSH format: git@github.com:org/repo.git
        if repo_url.startswith("git@github.com:"):
            org_repo = repo_url.split("git@github.com:")[1].rstrip(".git")
        # Handle HTTPS format: https://github.com/org/repo.git
        else:
            org_repo = repo_url.split("github.com/")[1].strip("/").rstrip(".git")

        org, repo = org_repo.split("/")
    except (IndexError, ValueError):
        click.echo(f"Error: Could not parse GitHub repository from URL: {repo_url}")
        sys.exit(1)

    # 5. Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{timestamp}-assessment.json"
    submission_path = f"submissions/{org}/{repo}/{filename}"

    if dry_run:
        click.echo("🔍 Dry-run mode - no PR will be created\n")
        click.echo(f"Submission path: {submission_path}")
        click.echo(f"Repository: {org}/{repo}")
        click.echo(f"Score: {score:.1f}/100 ({tier})")
        click.echo(f"Assessment file: {assessment_path}")
        return

    # 6. Initialize GitHub client
    try:
        gh = Github(token)
        user = gh.get_user()
        click.echo(f"Authenticated as: {user.login}\n")
    except GithubException as e:
        click.echo(f"Error: Failed to authenticate with GitHub: {e}", err=True)
        click.echo("Check that your GITHUB_TOKEN is valid.", err=True)
        sys.exit(1)

    # 7. Verify user has access to submitted repo
    try:
        submitted_repo = gh.get_repo(org_repo)

        # Check if user is collaborator or owner
        is_collaborator = submitted_repo.has_in_collaborators(user.login)
        is_owner = submitted_repo.owner.login == user.login

        if not (is_collaborator or is_owner):
            click.echo(f"Error: You must have commit access to {org_repo}", err=True)
            click.echo("\nYou can only submit repositories where you are:", err=True)
            click.echo("  - Repository owner", err=True)
            click.echo("  - Collaborator with push access", err=True)
            sys.exit(1)

        # Verify repository is public
        if submitted_repo.private:
            click.echo(
                f"Error: Repository {org_repo} is private. Only public repositories can be submitted to the leaderboard.",
                err=True,
            )
            sys.exit(1)

        click.echo(f"✅ Verified access to {org_repo}")

    except GithubException as e:
        if e.status == 404:
            click.echo(f"Error: Repository {org_repo} not found", err=True)
        else:
            click.echo(f"Error: Cannot access repository {org_repo}: {e}", err=True)
        sys.exit(1)

    # 8. Fork ambient-code/agentready (if not already forked)
    upstream_repo = "ambient-code/agentready"
    try:
        upstream = gh.get_repo(upstream_repo)
        click.echo(f"Found upstream: {upstream_repo}")

        # Check if user already has a fork
        try:
            fork = gh.get_repo(f"{user.login}/agentready")
            click.echo(f"Using existing fork: {fork.full_name}")
        except GithubException:
            # Create fork
            click.echo("Creating fork...")
            fork = user.create_fork(upstream)
            click.echo(f"✅ Created fork: {fork.full_name}")

    except GithubException as e:
        click.echo(f"Error: Cannot access {upstream_repo}: {e}", err=True)
        sys.exit(1)

    # 9. Create branch
    branch_name = f"leaderboard-{org}-{repo}-{timestamp}"
    try:
        # Get main branch reference
        main_ref = fork.get_git_ref("heads/main")
        main_sha = main_ref.object.sha

        # Create new branch
        fork.create_git_ref(f"refs/heads/{branch_name}", main_sha)
        click.echo(f"✅ Created branch: {branch_name}")

    except GithubException as e:
        click.echo(f"Error: Failed to create branch: {e}", err=True)
        sys.exit(1)

    # 10. Commit assessment file
    try:
        with open(assessment_path, encoding="utf-8") as f:
            content = f.read()

        commit_message = (
            f"feat: add {org}/{repo} to leaderboard\n\n"
            f"Score: {score:.1f}/100 ({tier})\n"
            f"Repository: https://github.com/{org}/{repo}"
        )

        fork.create_file(
            path=submission_path,
            message=commit_message,
            content=content,
            branch=branch_name,
        )
        click.echo(f"✅ Committed assessment to {submission_path}")

    except GithubException as e:
        click.echo(f"Error: Failed to commit file: {e}", err=True)
        sys.exit(1)

    # 11. Create PR
    try:
        pr_title = f"Leaderboard: {org}/{repo} ({score:.1f}/100 - {tier})"
        pr_body = f"""## Leaderboard Submission

**Repository**: [{org}/{repo}](https://github.com/{org}/{repo})
**Score**: {score:.1f}/100
**Tier**: {tier}
**Submitted by**: @{user.login}

### Validation Checklist

- [ ] Repository exists and is public
- [ ] Submitter has commit access
- [ ] Assessment re-run passes (±2 points tolerance)
- [ ] JSON schema valid

*Automated validation will run on this PR.*

---

Submitted via `agentready submit` command.
"""

        pr = upstream.create_pull(
            title=pr_title,
            body=pr_body,
            head=f"{user.login}:{branch_name}",
            base="main",
        )

        click.echo("\n🎉 Submission successful!")
        click.echo(f"\nPR URL: {pr.html_url}")
        click.echo(
            "\nYour submission will appear on the leaderboard after validation and review."
        )

    except GithubException as e:
        click.echo(f"Error: Failed to create pull request: {e}", err=True)
        click.echo(
            "\nThe branch and commit were created successfully. "
            "You can manually create the PR at:",
            err=True,
        )
        click.echo(
            f"https://github.com/{upstream_repo}/compare/main...{user.login}:{branch_name}",
            err=True,
        )
        sys.exit(1)
