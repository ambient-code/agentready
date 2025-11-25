#!/usr/bin/env python3
"""
Analyze GitHub organization repositories.

Fetches comprehensive repository data from a GitHub organization
and caches it to disk for analysis. Supports both GraphQL (via gh CLI)
and REST API (via curl) with automatic fallback.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def get_gh_token() -> str:
    """Get GitHub token from gh CLI config."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting GitHub token: {e}", file=sys.stderr)
        sys.exit(1)


def run_gh_command(args: list[str], max_retries: int = 3) -> dict[str, Any]:
    """Run gh CLI command and return JSON output with retry logic."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            if "502" in e.stderr or "503" in e.stderr:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"GitHub API error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})",
                        file=sys.stderr,
                    )
                    time.sleep(wait_time)
                    continue
            print(f"Error running gh command: {e}", file=sys.stderr)
            print(f"stderr: {e.stderr}", file=sys.stderr)
            raise
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            raise

    raise RuntimeError("Max retries exceeded")


def fetch_org_repos_graphql(
    org: str, include_private: bool = False
) -> list[dict[str, Any]]:
    """Fetch all repositories for an organization using GraphQL via gh CLI."""
    print(f"Fetching repositories for {org} using GraphQL...", file=sys.stderr)

    # Build gh repo list command
    args = [
        "repo",
        "list",
        org,
        "--limit",
        "1000",  # Max limit
        "--json",
        ",".join(
            [
                "name",
                "nameWithOwner",
                "description",
                "url",
                "sshUrl",
                "pushedAt",
                "createdAt",
                "updatedAt",
                "isPrivate",
                "isFork",
                "isArchived",
                "isTemplate",
                "visibility",
                "defaultBranchRef",
                "primaryLanguage",
                "languages",
                "stargazerCount",
                "forkCount",
                "watchers",
                "hasIssuesEnabled",
                "hasWikiEnabled",
                "hasProjectsEnabled",
                "diskUsage",
                "licenseInfo",
                "homepageUrl",
                "repositoryTopics",
                "latestRelease",
            ]
        ),
    ]

    if not include_private:
        args.extend(["--visibility", "public"])

    repos = run_gh_command(args)
    print(f"Fetched {len(repos)} repositories", file=sys.stderr)
    return repos


def fetch_org_repos_rest(
    org: str, token: str, include_private: bool = False
) -> list[dict[str, Any]]:
    """Fetch all repositories for an organization using REST API via curl."""
    print(f"Fetching repositories for {org} using REST API...", file=sys.stderr)

    all_repos = []
    page = 1
    per_page = 100

    visibility = "all" if include_private else "public"

    while True:
        url = f"https://api.github.com/orgs/{org}/repos?type={visibility}&per_page={per_page}&page={page}&sort=pushed&direction=desc"

        print(f"Fetching page {page}...", file=sys.stderr)

        # Use curl to fetch data
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-H",
                    f"Authorization: Bearer {token}",
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-H",
                    "X-GitHub-Api-Version: 2022-11-28",
                    url,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            repos = json.loads(result.stdout)

            # Check for API errors
            if isinstance(repos, dict) and "message" in repos:
                print(f"API Error: {repos['message']}", file=sys.stderr)
                sys.exit(1)

            if not repos:
                break

            all_repos.extend(repos)
            print(
                f"  Retrieved {len(repos)} repositories (total: {len(all_repos)})",
                file=sys.stderr,
            )

            # Check if there are more pages
            if len(repos) < per_page:
                break

            page += 1
            time.sleep(0.2)  # Rate limiting

        except subprocess.CalledProcessError as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            print(f"stderr: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            print(f"Response: {result.stdout[:500]}", file=sys.stderr)
            sys.exit(1)

    print(f"Fetched {len(all_repos)} repositories total", file=sys.stderr)
    return all_repos


def normalize_rest_data(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize REST API data to match GraphQL format."""
    normalized = []

    for repo in repos:
        normalized_repo = {
            "name": repo["name"],
            "nameWithOwner": repo["full_name"],
            "description": repo["description"],
            "url": repo["html_url"],
            "sshUrl": repo["ssh_url"],
            "pushedAt": repo["pushed_at"],
            "createdAt": repo["created_at"],
            "updatedAt": repo["updated_at"],
            "isPrivate": repo["private"],
            "isFork": repo["fork"],
            "isArchived": repo["archived"],
            "isTemplate": repo.get("is_template", False),
            "visibility": "private" if repo["private"] else "public",
            "defaultBranchRef": {"name": repo["default_branch"]},
            "primaryLanguage": {"name": repo["language"]} if repo["language"] else None,
            "stargazerCount": repo["stargazers_count"],
            "forkCount": repo["forks_count"],
            "watchers": {"totalCount": repo["watchers_count"]},
            "hasIssuesEnabled": repo["has_issues"],
            "hasWikiEnabled": repo["has_wiki"],
            "hasProjectsEnabled": repo["has_projects"],
            "diskUsage": repo.get("size", 0),
            "licenseInfo": (
                {"name": repo["license"]["name"]} if repo.get("license") else None
            ),
            "homepageUrl": repo["homepage"],
            "repositoryTopics": [],  # Would need separate API call
            "openIssuesCount": repo["open_issues_count"],
        }
        normalized.append(normalized_repo)

    return normalized


def fetch_org_repos(
    org: str, include_private: bool = False, use_rest: bool = False
) -> list[dict[str, Any]]:
    """Fetch organization repos with automatic fallback from GraphQL to REST."""
    if use_rest:
        token = get_gh_token()
        repos = fetch_org_repos_rest(org, token, include_private)
        return normalize_rest_data(repos)

    try:
        return fetch_org_repos_graphql(org, include_private)
    except Exception as e:
        print(f"GraphQL fetch failed: {e}", file=sys.stderr)
        print("Falling back to REST API...", file=sys.stderr)
        token = get_gh_token()
        repos = fetch_org_repos_rest(org, token, include_private)
        return normalize_rest_data(repos)


def enrich_repo_data(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add computed fields to repository data."""
    for repo in repos:
        # Parse dates
        pushed_at = datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00"))
        created_at = datetime.fromisoformat(repo["createdAt"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(repo["updatedAt"].replace("Z", "+00:00"))

        # Add days since last push
        repo["daysSinceLastPush"] = (datetime.now(pushed_at.tzinfo) - pushed_at).days
        repo["daysSinceCreation"] = (datetime.now(created_at.tzinfo) - created_at).days
        repo["daysSinceUpdate"] = (datetime.now(updated_at.tzinfo) - updated_at).days

        # Add activity score (lower is more active)
        repo["activityScore"] = repo["daysSinceLastPush"]

        # Extract language name
        if repo.get("primaryLanguage"):
            repo["primaryLanguageName"] = repo["primaryLanguage"]["name"]
        else:
            repo["primaryLanguageName"] = None

        # Count total languages (GraphQL format)
        if "languages" in repo and isinstance(repo["languages"], dict):
            repo["languageCount"] = len(repo.get("languages", {}).get("nodes", []))
        else:
            repo["languageCount"] = 1 if repo["primaryLanguageName"] else 0

    return repos


def save_cache(data: dict[str, Any], output_file: Path) -> None:
    """Save data to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Cached data to {output_file}", file=sys.stderr)


def generate_activity_report(repos: list[dict[str, Any]]) -> None:
    """Generate activity report sorted by most recent activity."""
    # Sort by activity (most recent first)
    sorted_repos = sorted(repos, key=lambda r: r["daysSinceLastPush"])

    print("\n" + "=" * 120)
    print("Repository Analysis - Sorted by Activity")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Repositories: {len(repos)}")
    print("=" * 120)
    print()

    # Print header
    print(
        f"{'#':<4} {'Repository':<45} {'Last Push':<12} {'Stars':<7} {'Forks':<7} {'Issues':<8} {'Language':<15} {'Status'}"
    )
    print("-" * 120)

    # Print repositories
    for idx, repo in enumerate(sorted_repos, 1):
        name = repo["name"]
        if len(name) > 43:
            name = name[:40] + "..."

        days_ago = repo["daysSinceLastPush"]
        if days_ago == 0:
            last_push = "Today"
        elif days_ago == 1:
            last_push = "Yesterday"
        elif days_ago < 30:
            last_push = f"{days_ago}d ago"
        elif days_ago < 365:
            last_push = f"{days_ago // 30}mo ago"
        else:
            last_push = f"{days_ago // 365}y ago"

        # Handle both GraphQL and REST formats for stargazerCount
        stars = (
            repo["stargazerCount"]["totalCount"]
            if isinstance(repo.get("stargazerCount"), dict)
            else repo.get("stargazerCount", 0)
        )
        forks = repo["forkCount"]
        issues = repo.get("openIssuesCount", 0)
        language = repo["primaryLanguageName"] or "N/A"
        if len(language) > 13:
            language = language[:10] + "..."

        # Status markers
        status_parts = []
        if repo["isArchived"]:
            status_parts.append("ARCHIVED")
        if repo["isFork"]:
            status_parts.append("fork")
        if repo["isTemplate"]:
            status_parts.append("template")

        status = " | ".join(status_parts) if status_parts else ""

        print(
            f"{idx:<4} {name:<45} {last_push:<12} {stars:<7} {forks:<7} {issues:<8} {language:<15} {status}"
        )

    print()

    # Summary statistics
    print("=" * 120)
    print("Summary Statistics")
    print("=" * 120)
    active_repos = [r for r in repos if r["daysSinceLastPush"] <= 30]
    moderate_repos = [r for r in repos if 30 < r["daysSinceLastPush"] <= 90]
    stale_repos = [r for r in repos if r["daysSinceLastPush"] > 180]
    archived_repos = [r for r in repos if r["isArchived"]]

    print(f"Active (pushed within 30 days):     {len(active_repos):>4} repos")
    print(f"Moderate (31-90 days):               {len(moderate_repos):>4} repos")
    print(f"Stale (180+ days, not archived):     {len(stale_repos):>4} repos")
    print(f"Archived:                            {len(archived_repos):>4} repos")
    print(
        f"Forks:                               {len([r for r in repos if r['isFork']]):>4} repos"
    )
    print(
        f"Templates:                           {len([r for r in repos if r['isTemplate']]):>4} repos"
    )
    print()

    # Total stars and forks
    total_stars = sum(
        (
            r["stargazerCount"]["totalCount"]
            if isinstance(r.get("stargazerCount"), dict)
            else r.get("stargazerCount", 0)
        )
        for r in repos
    )
    total_forks = sum(r["forkCount"] for r in repos)
    total_issues = sum(r.get("openIssuesCount", 0) for r in repos)

    print(f"Total Stars:                         {total_stars:>5}")
    print(f"Total Forks:                         {total_forks:>5}")
    print(f"Total Open Issues:                   {total_issues:>5}")
    print()

    # Language breakdown
    languages = {}
    for repo in repos:
        lang = repo["primaryLanguageName"]
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    print("Top Languages:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {lang:<25} {count:>3} repos")
    print()

    # Most active repositories (top 10)
    print("Most Recently Active (Top 10):")
    for idx, repo in enumerate(sorted_repos[:10], 1):
        days = repo["daysSinceLastPush"]
        if days == 0:
            when = "today"
        elif days == 1:
            when = "yesterday"
        else:
            when = f"{days} days ago"
        print(f"  {idx:2}. {repo['name']:<45} (pushed {when})")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze GitHub organization repositories"
    )
    parser.add_argument("org", help="GitHub organization name")
    parser.add_argument(
        "--include-private", action="store_true", help="Include private repositories"
    )
    parser.add_argument(
        "--use-rest",
        action="store_true",
        help="Force use of REST API instead of GraphQL",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".cache/github-org-analysis"),
        help="Cache directory",
    )

    args = parser.parse_args()

    cache_file = args.cache_dir / f"{args.org}-repos.json"

    # Fetch repository data
    repos = fetch_org_repos(
        args.org, include_private=args.include_private, use_rest=args.use_rest
    )

    # Enrich with computed fields
    repos = enrich_repo_data(repos)

    # Create cache object
    cache_data = {
        "organization": args.org,
        "fetchedAt": datetime.now().isoformat(),
        "repositoryCount": len(repos),
        "repositories": repos,
    }

    # Save to cache
    save_cache(cache_data, cache_file)

    # Generate activity report
    generate_activity_report(repos)

    print(f"✅ Data cached to: {cache_file}")
    print("   You can run additional queries on the cached data")
    print()


if __name__ == "__main__":
    main()
