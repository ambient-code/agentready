#!/usr/bin/env python3
"""
Query cached GitHub organization data.

Provides various queries and filters on the cached repository data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_cache(cache_file: Path) -> dict[str, Any]:
    """Load cached data from JSON file."""
    if not cache_file.exists():
        print(f"Error: Cache file not found: {cache_file}", file=sys.stderr)
        print("Run analyze_github_org.py first to fetch data", file=sys.stderr)
        sys.exit(1)

    with cache_file.open() as f:
        return json.load(f)


def query_by_language(
    repos: list[dict[str, Any]], language: str
) -> list[dict[str, Any]]:
    """Filter repositories by primary language."""
    return [
        r for r in repos if r.get("primaryLanguageName", "").lower() == language.lower()
    ]


def query_active_repos(
    repos: list[dict[str, Any]], days: int = 30
) -> list[dict[str, Any]]:
    """Filter repositories active within specified days."""
    return [r for r in repos if r["daysSinceLastPush"] <= days]


def query_stale_repos(
    repos: list[dict[str, Any]], days: int = 180, exclude_archived: bool = True
) -> list[dict[str, Any]]:
    """Filter repositories not updated in specified days."""
    result = [r for r in repos if r["daysSinceLastPush"] > days]
    if exclude_archived:
        result = [r for r in result if not r["isArchived"]]
    return result


def query_archived_repos(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter archived repositories."""
    return [r for r in repos if r["isArchived"]]


def query_by_stars(
    repos: list[dict[str, Any]], min_stars: int = 10
) -> list[dict[str, Any]]:
    """Filter repositories with minimum star count."""
    return [r for r in repos if r["stargazerCount"] >= min_stars]


def query_forks_only(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter forked repositories."""
    return [r for r in repos if r["isFork"]]


def query_original_only(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter original (non-fork) repositories."""
    return [r for r in repos if not r["isFork"]]


def print_repo_list(repos: list[dict[str, Any]], title: str):
    """Print formatted repository list."""
    print(f"\n{'=' * 100}")
    print(f"{title} ({len(repos)} repositories)")
    print(f"{'=' * 100}\n")

    if not repos:
        print("No repositories found.\n")
        return

    # Sort by activity
    sorted_repos = sorted(repos, key=lambda r: r["daysSinceLastPush"])

    # Print header
    print(
        f"{'Repository':<45} {'Language':<15} {'Stars':<7} {'Forks':<7} {'Last Push':<12} {'Status'}"
    )
    print("-" * 100)

    for repo in sorted_repos:
        name = repo["name"]
        if len(name) > 43:
            name = name[:40] + "..."

        language = repo["primaryLanguageName"] or "N/A"
        if len(language) > 13:
            language = language[:10] + "..."

        stars = repo["stargazerCount"]
        forks = repo["forkCount"]

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

        status_parts = []
        if repo["isArchived"]:
            status_parts.append("ARCHIVED")
        if repo["isFork"]:
            status_parts.append("fork")

        status = " | ".join(status_parts) if status_parts else ""

        print(
            f"{name:<45} {language:<15} {stars:<7} {forks:<7} {last_push:<12} {status}"
        )

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Query cached GitHub organization data"
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".cache/github-org-analysis/opendatahub-io-repos.json"),
        help="Path to cache file",
    )

    # Query filters
    parser.add_argument("--language", help="Filter by language (e.g., Python, Go)")
    parser.add_argument(
        "--active", type=int, metavar="DAYS", help="Repos active within N days"
    )
    parser.add_argument(
        "--stale", type=int, metavar="DAYS", help="Repos not updated in N days"
    )
    parser.add_argument(
        "--archived", action="store_true", help="Show only archived repos"
    )
    parser.add_argument("--min-stars", type=int, metavar="N", help="Minimum star count")
    parser.add_argument(
        "--forks-only", action="store_true", help="Show only forked repos"
    )
    parser.add_argument(
        "--original-only", action="store_true", help="Show only original repos"
    )

    # Output options
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--count", action="store_true", help="Show only count")

    args = parser.parse_args()

    # Load cache
    cache_data = load_cache(args.cache)
    repos = cache_data["repositories"]

    # Apply filters
    filtered = repos
    title_parts = ["Repositories"]

    if args.language:
        filtered = query_by_language(filtered, args.language)
        title_parts.append(f"Language: {args.language}")

    if args.active is not None:
        filtered = query_active_repos(filtered, args.active)
        title_parts.append(f"Active within {args.active} days")

    if args.stale is not None:
        filtered = query_stale_repos(filtered, args.stale)
        title_parts.append(f"Stale (>{args.stale} days)")

    if args.archived:
        filtered = query_archived_repos(filtered)
        title_parts.append("Archived")

    if args.min_stars is not None:
        filtered = query_by_stars(filtered, args.min_stars)
        title_parts.append(f"≥{args.min_stars} stars")

    if args.forks_only:
        filtered = query_forks_only(filtered)
        title_parts.append("Forks only")

    if args.original_only:
        filtered = query_original_only(filtered)
        title_parts.append("Original repos only")

    # Output
    if args.count:
        print(len(filtered))
    elif args.json:
        print(json.dumps(filtered, indent=2, default=str))
    else:
        title = " - ".join(title_parts)
        print_repo_list(filtered, title)

        # Print cache info
        fetched_at = datetime.fromisoformat(cache_data["fetchedAt"])
        print(f"Data fetched: {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Cache file: {args.cache}")
        print()


if __name__ == "__main__":
    main()
