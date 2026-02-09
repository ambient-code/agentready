"""CLI command for submitting assessments to the AgentReady leaderboard."""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
from github import Github, GithubException

UPSTREAM_REPO = "ambient-code/agentready"
SUBPROCESS_TIMEOUT = 60  # seconds
MAX_ASSESSMENT_SIZE = 10 * 1024 * 1024  # 10 MB

# Valid GitHub org/repo name pattern: alphanumeric, hyphens, underscores, dots
GITHUB_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def find_assessment_file(repository: str, assessment_file: str | None) -> Path:
    """Find and validate the assessment file to submit."""
    repo_path = Path(repository).resolve()
    if assessment_file:
        return Path(assessment_file).resolve()

    latest = repo_path / ".agentready" / "assessment-latest.json"
    if not latest.exists():
        click.echo(
            "Error: No assessment found. Run 'agentready assess' first.", err=True
        )
        sys.exit(1)
    # Resolve symlink to actual file
    return latest.resolve() if latest.is_symlink() else latest


def load_assessment(assessment_path: Path) -> dict:
    """Load and validate assessment JSON."""
    try:
        with open(assessment_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        click.echo(f"Error: Failed to read assessment file: {e}", err=True)
        sys.exit(1)


def extract_repo_info(assessment_data: dict) -> tuple[str, str, float, str]:
    """Extract org, repo, score, and tier from assessment data."""
    try:
        repo_url = assessment_data["repository"]["url"]
        score = assessment_data["overall_score"]
        tier = assessment_data["certification_level"]
    except KeyError as e:
        click.echo(f"Error: Invalid assessment JSON (missing {e})", err=True)
        sys.exit(1)

    if not repo_url or "github.com" not in repo_url:
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

    # Validate org/repo names to prevent injection
    if not GITHUB_NAME_PATTERN.match(org) or not GITHUB_NAME_PATTERN.match(repo):
        click.echo(
            f"Error: Invalid GitHub org/repo name: {org}/{repo}",
            err=True,
        )
        click.echo(
            "Names must contain only alphanumeric characters, hyphens, underscores, or dots.",
            err=True,
        )
        sys.exit(1)

    return org, repo, score, tier


def generate_pr_body(org: str, repo: str, score: float, tier: str, user: str) -> str:
    """Generate the PR body for leaderboard submission."""
    return f"""## Leaderboard Submission

**Repository**: [{org}/{repo}](https://github.com/{org}/{repo})
**Score**: {score:.1f}/100
**Tier**: {tier}
**Submitted by**: @{user}

### Validation Checklist

- [ ] Repository exists and is public
- [ ] Submitter has commit access
- [ ] Assessment re-run passes (±2 points tolerance)
- [ ] JSON schema valid

*Automated validation will run on this PR.*

---

Submitted via `agentready submit` command.
"""


def run_gh_command(
    args: list[str], capture_output: bool = True, timeout: int = SUBPROCESS_TIMEOUT
) -> subprocess.CompletedProcess:
    """Run a gh CLI command and return the result.

    Args:
        args: Arguments to pass to gh CLI.
        capture_output: Whether to capture stdout/stderr.
        timeout: Timeout in seconds (default: SUBPROCESS_TIMEOUT).

    Returns:
        CompletedProcess with returncode, stdout, stderr.
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
        return result
    except subprocess.TimeoutExpired:
        click.echo(f"Error: gh command timed out after {timeout}s", err=True)
        sys.exit(1)


def submit_with_gh_cli(
    org: str,
    repo: str,
    score: float,
    tier: str,
    assessment_path: Path,
    timestamp: str,
) -> None:
    """Submit assessment using gh CLI."""
    # 1. Check gh CLI is available
    if not shutil.which("gh"):
        click.echo(
            "Error: gh CLI not found. Install it from https://cli.github.com/", err=True
        )
        sys.exit(1)

    # 2. Check authentication
    result = run_gh_command(["auth", "status"])
    if result.returncode != 0:
        click.echo("Error: Not authenticated with gh CLI", err=True)
        click.echo("\nRun: gh auth login", err=True)
        sys.exit(1)

    # 3. Get current user
    result = run_gh_command(["api", "user", "--jq", ".login"])
    if result.returncode != 0:
        click.echo("Error: Failed to get current user", err=True)
        sys.exit(1)
    user = result.stdout.strip()
    click.echo(f"Authenticated as: {user}\n")

    # 4. Verify user has access to submitted repo
    org_repo = f"{org}/{repo}"
    result = run_gh_command(
        [
            "api",
            f"repos/{org_repo}",
            "--jq",
            "{private: .private, permissions: .permissions}",
        ]
    )
    if result.returncode != 0:
        click.echo(
            f"Error: Repository {org_repo} not found or not accessible", err=True
        )
        sys.exit(1)

    try:
        repo_info = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Failed to parse GitHub API response: {e}", err=True)
        sys.exit(1)
    if repo_info.get("private"):
        click.echo(
            f"Error: Repository {org_repo} is private. Only public repositories can be submitted.",
            err=True,
        )
        sys.exit(1)

    permissions = repo_info.get("permissions", {})
    if not (permissions.get("push") or permissions.get("admin")):
        click.echo(f"Error: You must have commit access to {org_repo}", err=True)
        click.echo("\nYou can only submit repositories where you are:", err=True)
        click.echo("  - Repository owner", err=True)
        click.echo("  - Collaborator with push access", err=True)
        sys.exit(1)

    click.echo(f"Verified access to {org_repo}")

    # 5. Fork upstream repo (if not already forked)
    click.echo(f"Found upstream: {UPSTREAM_REPO}")

    # Check if fork exists
    result = run_gh_command(["api", f"repos/{user}/agentready", "--jq", ".full_name"])
    if result.returncode == 0:
        click.echo(f"Using existing fork: {result.stdout.strip()}")
    else:
        # Create fork
        click.echo("Creating fork...")
        result = run_gh_command(["repo", "fork", UPSTREAM_REPO, "--clone=false"])
        if result.returncode != 0:
            click.echo(f"Error: Failed to fork {UPSTREAM_REPO}", err=True)
            sys.exit(1)
        click.echo(f"Created fork: {user}/agentready")

    # 6. Create branch
    branch_name = f"leaderboard-{org}-{repo}-{timestamp}"

    # Get main branch SHA
    result = run_gh_command(
        ["api", f"repos/{user}/agentready/git/ref/heads/main", "--jq", ".object.sha"]
    )
    if result.returncode != 0:
        click.echo("Error: Failed to get main branch SHA", err=True)
        sys.exit(1)
    main_sha = result.stdout.strip()

    # Create new branch
    result = run_gh_command(
        [
            "api",
            f"repos/{user}/agentready/git/refs",
            "-X",
            "POST",
            "-f",
            f"ref=refs/heads/{branch_name}",
            "-f",
            f"sha={main_sha}",
        ]
    )
    if result.returncode != 0:
        click.echo(f"Error: Failed to create branch: {result.stderr}", err=True)
        sys.exit(1)
    click.echo(f"Created branch: {branch_name}")

    # 7. Commit assessment file
    # Check file size before reading
    file_size = assessment_path.stat().st_size
    if file_size > MAX_ASSESSMENT_SIZE:
        click.echo(
            f"Error: Assessment file too large ({file_size / 1024 / 1024:.1f} MB). "
            f"Maximum allowed: {MAX_ASSESSMENT_SIZE / 1024 / 1024:.0f} MB",
            err=True,
        )
        sys.exit(1)

    with open(assessment_path, encoding="utf-8") as f:
        content = f.read()

    # Base64 encode the content
    content_b64 = base64.b64encode(content.encode()).decode()

    submission_path = f"submissions/{org}/{repo}/{timestamp}-assessment.json"
    commit_message = (
        f"feat: add {org}/{repo} to leaderboard\n\n"
        f"Score: {score:.1f}/100 ({tier})\n"
        f"Repository: https://github.com/{org}/{repo}"
    )

    result = run_gh_command(
        [
            "api",
            f"repos/{user}/agentready/contents/{submission_path}",
            "-X",
            "PUT",
            "-f",
            f"message={commit_message}",
            "-f",
            f"content={content_b64}",
            "-f",
            f"branch={branch_name}",
        ]
    )
    if result.returncode != 0:
        click.echo(f"Error: Failed to commit file: {result.stderr}", err=True)
        sys.exit(1)
    click.echo(f"Committed assessment to {submission_path}")

    # 8. Create PR
    pr_title = f"Leaderboard: {org}/{repo} ({score:.1f}/100 - {tier})"
    pr_body = generate_pr_body(org, repo, score, tier, user)

    result = run_gh_command(
        [
            "pr",
            "create",
            "--repo",
            UPSTREAM_REPO,
            "--head",
            f"{user}:{branch_name}",
            "--base",
            "main",
            "--title",
            pr_title,
            "--body",
            pr_body,
        ]
    )
    if result.returncode != 0:
        click.echo(f"Error: Failed to create pull request: {result.stderr}", err=True)
        click.echo(
            "\nThe branch and commit were created successfully. "
            "You can manually create the PR at:",
            err=True,
        )
        click.echo(
            f"https://github.com/{UPSTREAM_REPO}/compare/main...{user}:{branch_name}",
            err=True,
        )
        sys.exit(1)

    # Extract PR URL from output
    pr_url = result.stdout.strip()
    click.echo("\nSubmission successful!")
    click.echo(f"\nPR URL: {pr_url}")
    click.echo(
        "\nYour submission will appear on the leaderboard after validation and review."
    )


def submit_with_token(
    org: str,
    repo: str,
    score: float,
    tier: str,
    assessment_path: Path,
    timestamp: str,
) -> None:
    """Submit assessment using GITHUB_TOKEN."""
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
        click.echo("\nAlternatively, use --gh flag to submit via gh CLI.", err=True)
        sys.exit(1)

    org_repo = f"{org}/{repo}"
    submission_path = f"submissions/{org}/{repo}/{timestamp}-assessment.json"

    # 2. Initialize GitHub client
    try:
        gh = Github(token)
        user = gh.get_user()
        click.echo(f"Authenticated as: {user.login}\n")
    except GithubException as e:
        click.echo(f"Error: Failed to authenticate with GitHub: {e}", err=True)
        click.echo("Check that your GITHUB_TOKEN is valid.", err=True)
        sys.exit(1)

    # 3. Verify user has access to submitted repo
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

        click.echo(f"Verified access to {org_repo}")

    except GithubException as e:
        if e.status == 404:
            click.echo(f"Error: Repository {org_repo} not found", err=True)
        else:
            click.echo(f"Error: Cannot access repository {org_repo}: {e}", err=True)
        sys.exit(1)

    # 4. Fork ambient-code/agentready (if not already forked)
    try:
        upstream = gh.get_repo(UPSTREAM_REPO)
        click.echo(f"Found upstream: {UPSTREAM_REPO}")

        # Check if user already has a fork
        try:
            fork = gh.get_repo(f"{user.login}/agentready")
            click.echo(f"Using existing fork: {fork.full_name}")
        except GithubException:
            # Create fork
            click.echo("Creating fork...")
            fork = user.create_fork(upstream)
            click.echo(f"Created fork: {fork.full_name}")

    except GithubException as e:
        click.echo(f"Error: Cannot access {UPSTREAM_REPO}: {e}", err=True)
        sys.exit(1)

    # 5. Create branch
    branch_name = f"leaderboard-{org}-{repo}-{timestamp}"
    try:
        # Get main branch reference
        main_ref = fork.get_git_ref("heads/main")
        main_sha = main_ref.object.sha

        # Create new branch
        fork.create_git_ref(f"refs/heads/{branch_name}", main_sha)
        click.echo(f"Created branch: {branch_name}")

    except GithubException as e:
        click.echo(f"Error: Failed to create branch: {e}", err=True)
        sys.exit(1)

    # 6. Commit assessment file
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
        click.echo(f"Committed assessment to {submission_path}")

    except GithubException as e:
        click.echo(f"Error: Failed to commit file: {e}", err=True)
        sys.exit(1)

    # 7. Create PR
    try:
        pr_title = f"Leaderboard: {org}/{repo} ({score:.1f}/100 - {tier})"
        pr_body = generate_pr_body(org, repo, score, tier, user.login)

        pr = upstream.create_pull(
            title=pr_title,
            body=pr_body,
            head=f"{user.login}:{branch_name}",
            base="main",
        )

        click.echo("\nSubmission successful!")
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
            f"https://github.com/{UPSTREAM_REPO}/compare/main...{user.login}:{branch_name}",
            err=True,
        )
        sys.exit(1)


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
@click.option(
    "--gh", "use_gh_cli", is_flag=True, help="Use gh CLI instead of GITHUB_TOKEN"
)
def submit(repository, assessment_file, dry_run, use_gh_cli):
    """Submit assessment results to AgentReady leaderboard.

    Creates a PR to agentready/agentready with your assessment results.
    Requires GITHUB_TOKEN environment variable or --gh flag for gh CLI.

    Examples:

        \b
        # Submit using GITHUB_TOKEN
        agentready submit

        \b
        # Submit using gh CLI (no token needed)
        agentready submit --gh

        \b
        # Submit specific assessment file
        agentready submit -f .agentready/assessment-20251203-143045.json

        \b
        # Preview submission without creating PR
        agentready submit --dry-run
    """
    # 1. Find and load assessment
    assessment_path = find_assessment_file(repository, assessment_file)
    assessment_data = load_assessment(assessment_path)

    # 2. Extract repo info
    org, repo, score, tier = extract_repo_info(assessment_data)

    # 3. Generate timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    submission_path = f"submissions/{org}/{repo}/{timestamp}-assessment.json"

    # 4. Handle dry-run
    if dry_run:
        click.echo("Dry-run mode - no PR will be created\n")
        click.echo(f"Submission path: {submission_path}")
        click.echo(f"Repository: {org}/{repo}")
        click.echo(f"Score: {score:.1f}/100 ({tier})")
        click.echo(f"Assessment file: {assessment_path}")
        return

    # 5. Submit using appropriate method
    if use_gh_cli:
        submit_with_gh_cli(org, repo, score, tier, assessment_path, timestamp)
    else:
        submit_with_token(org, repo, score, tier, assessment_path, timestamp)
