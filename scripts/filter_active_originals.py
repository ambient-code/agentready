#!/usr/bin/env python3
"""
Filter GitHub repositories to active originals only.

Filters cached repository data to show only:
1. Original repositories (not forks)
2. Active within the last 90 days (merged commits)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_cache(cache_file: Path) -> dict[str, Any]:
    """Load cached data from JSON file."""
    if not cache_file.exists():
        print(f"Error: Cache file not found: {cache_file}")
        print("Run analyze_github_org.py first to fetch data")
        exit(1)

    with cache_file.open() as f:
        return json.load(f)


def filter_active_originals(
    repos: list[dict[str, Any]], days: int = 90
) -> list[dict[str, Any]]:
    """Filter to original repos with activity in last N days."""
    return [r for r in repos if not r["isFork"] and r["daysSinceLastPush"] <= days]


def save_filtered_list(repos: list[dict[str, Any]], output_file: Path):
    """Save filtered repository list to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    filtered_data = {
        "generatedAt": datetime.now().isoformat(),
        "filter": {
            "original_only": True,
            "max_days_since_push": 90,
        },
        "repositoryCount": len(repos),
        "repositories": repos,
    }

    with output_file.open("w") as f:
        json.dump(filtered_data, f, indent=2, default=str)

    print(f"✅ Saved filtered list to: {output_file}")


def print_report(repos: list[dict[str, Any]]):
    """Print formatted report of filtered repositories."""
    # Sort by activity (most recent first)
    sorted_repos = sorted(repos, key=lambda r: r["daysSinceLastPush"])

    print("\n" + "=" * 120)
    print("OpenDataHub.io - Active Original Repositories")
    print("Filter: Non-fork repos with activity in last 90 days")
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
        else:
            last_push = f"{days_ago // 30}mo ago"

        stars = repo["stargazerCount"]
        forks = repo["forkCount"]
        issues = repo.get("openIssuesCount", 0)
        language = repo["primaryLanguageName"] or "N/A"
        if len(language) > 13:
            language = language[:10] + "..."

        # Status markers
        status_parts = []
        if repo["isArchived"]:
            status_parts.append("ARCHIVED")
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

    very_active = [r for r in repos if r["daysSinceLastPush"] <= 7]
    active = [r for r in repos if 7 < r["daysSinceLastPush"] <= 30]
    moderate = [r for r in repos if 30 < r["daysSinceLastPush"] <= 90]
    archived = [r for r in repos if r["isArchived"]]

    print(f"Very Active (≤7 days):               {len(very_active):>4} repos")
    print(f"Active (8-30 days):                  {len(active):>4} repos")
    print(f"Moderate (31-90 days):               {len(moderate):>4} repos")
    print(f"Archived:                            {len(archived):>4} repos")
    print()

    # Total stars and forks
    total_stars = sum(r["stargazerCount"] for r in repos)
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

    print("Languages:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        print(f"  {lang:<25} {count:>3} repos")
    print()

    # High-value repos (stars + forks)
    print("Top 10 by Popularity (Stars + Forks):")
    by_popularity = sorted(
        repos, key=lambda r: r["stargazerCount"] + r["forkCount"], reverse=True
    )
    for idx, repo in enumerate(by_popularity[:10], 1):
        popularity = repo["stargazerCount"] + repo["forkCount"]
        print(
            f"  {idx:2}. {repo['name']:<45} ({repo['stargazerCount']} ⭐ + {repo['forkCount']} 🔱 = {popularity})"
        )
    print()


def main():
    cache_file = Path(".cache/github-org-analysis/opendatahub-io-repos.json")
    output_file = Path(
        ".cache/github-org-analysis/opendatahub-io-active-originals.json"
    )

    # Load cache
    print(f"Loading cache from: {cache_file}")
    cache_data = load_cache(cache_file)
    all_repos = cache_data["repositories"]
    print(f"Loaded {len(all_repos)} total repositories")
    print()

    # Filter to active originals
    filtered_repos = filter_active_originals(all_repos, days=90)
    print(f"Filtered to {len(filtered_repos)} active original repositories")

    # Save filtered list
    save_filtered_list(filtered_repos, output_file)
    print()

    # Print report
    print_report(filtered_repos)


if __name__ == "__main__":
    main()
