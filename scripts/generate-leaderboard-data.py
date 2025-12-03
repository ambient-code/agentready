#!/usr/bin/env python3
"""Generate leaderboard data from submission files.

Scans the submissions/ directory, parses all assessment JSON files,
and generates a consolidated leaderboard.json for Jekyll consumption.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def scan_submissions(submissions_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Scan submissions directory and group assessments by repository.

    Args:
        submissions_dir: Path to submissions/ directory

    Returns:
        Dictionary mapping "org/repo" to list of submission dicts
    """
    repos = defaultdict(list)

    if not submissions_dir.exists():
        print(f"Warning: {submissions_dir} does not exist")
        return repos

    for json_file in submissions_dir.rglob("*-assessment.json"):
        # Path format: submissions/{org}/{repo}/{timestamp}-assessment.json
        parts = json_file.parts
        if len(parts) < 4:
            print(f"Warning: Skipping malformed path: {json_file}")
            continue

        org = parts[-3]
        repo = parts[-2]
        repo_key = f"{org}/{repo}"

        try:
            with open(json_file, encoding="utf-8") as f:
                assessment = json.load(f)

            # Extract timestamp from filename
            timestamp_str = json_file.stem.replace("-assessment", "")

            repos[repo_key].append(
                {
                    "assessment": assessment,
                    "timestamp": timestamp_str,
                    "path": json_file,
                }
            )

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to parse {json_file}: {e}")
            continue

    return repos


def generate_leaderboard_data(repos: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Generate leaderboard.json structure from submissions.

    Args:
        repos: Dictionary of repository submissions

    Returns:
        Leaderboard data structure for Jekyll
    """
    overall = []
    by_language = defaultdict(list)
    by_size = defaultdict(list)
    most_improved = []

    for repo_name, submissions in repos.items():
        # Sort by timestamp (most recent first)
        submissions.sort(key=lambda x: x["timestamp"], reverse=True)
        latest = submissions[0]["assessment"]

        try:
            entry = {
                "repo": repo_name,
                "org": repo_name.split("/")[0],
                "name": repo_name.split("/")[1],
                "score": float(latest["overall_score"]),
                "tier": latest["certification_level"],
                "language": latest["repository"].get("primary_language", "Unknown"),
                "size": latest["repository"].get("size_category", "Unknown"),
                "last_updated": submissions[0]["timestamp"][:10],  # YYYY-MM-DD
                "url": latest["repository"]["url"],
                "history": [
                    {
                        "date": s["timestamp"][:10],
                        "score": float(s["assessment"]["overall_score"]),
                    }
                    for s in submissions
                ],
            }

            overall.append(entry)
            by_language[entry["language"]].append(entry)
            by_size[entry["size"]].append(entry)

            # Calculate improvement if multiple submissions
            if len(submissions) > 1:
                oldest = submissions[-1]["assessment"]
                improvement = float(latest["overall_score"]) - float(
                    oldest["overall_score"]
                )

                if improvement > 0:
                    # Parse ISO timestamps
                    try:
                        from_dt = datetime.fromisoformat(
                            submissions[-1]["timestamp"][:19]
                        )
                        to_dt = datetime.fromisoformat(submissions[0]["timestamp"][:19])
                        days = (to_dt - from_dt).days
                    except ValueError:
                        days = 0

                    most_improved.append(
                        {
                            "repo": repo_name,
                            "improvement": round(improvement, 1),
                            "from_score": float(oldest["overall_score"]),
                            "to_score": float(latest["overall_score"]),
                            "from_date": submissions[-1]["timestamp"][:10],
                            "to_date": submissions[0]["timestamp"][:10],
                            "days": days,
                        }
                    )

        except (KeyError, ValueError, IndexError) as e:
            print(f"Warning: Skipping {repo_name} due to invalid data: {e}")
            continue

    # Sort rankings
    overall.sort(key=lambda x: x["score"], reverse=True)

    for lang in by_language:
        by_language[lang].sort(key=lambda x: x["score"], reverse=True)

    for size in by_size:
        by_size[size].sort(key=lambda x: x["score"], reverse=True)

    most_improved.sort(key=lambda x: x["improvement"], reverse=True)

    # Add ranks
    for i, entry in enumerate(overall, 1):
        entry["rank"] = i

    for lang, entries in by_language.items():
        for i, entry in enumerate(entries, 1):
            if "lang_rank" not in entry:
                entry["lang_rank"] = {}
            entry["lang_rank"][lang] = i

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_repositories": len(overall),
        "overall": overall,
        "by_language": dict(by_language),
        "by_size": dict(by_size),
        "most_improved": most_improved[:20],  # Top 20
    }


def main():
    """Main entry point for leaderboard generation."""
    # Determine repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    submissions_dir = repo_root / "submissions"
    output_dir = repo_root / "docs" / "_data"
    output_file = output_dir / "leaderboard.json"

    print(f"Scanning submissions in: {submissions_dir}")

    # Scan submissions
    repos = scan_submissions(submissions_dir)

    if not repos:
        print("No submissions found. Creating empty leaderboard.")
        leaderboard_data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_repositories": 0,
            "overall": [],
            "by_language": {},
            "by_size": {},
            "most_improved": [],
        }
    else:
        print(f"Found {len(repos)} repositories with submissions")
        leaderboard_data = generate_leaderboard_data(repos)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(leaderboard_data, f, indent=2)

    print(f"\n✅ Leaderboard data written to: {output_file}")
    print(f"Total repositories: {leaderboard_data['total_repositories']}")
    print(f"Generated at: {leaderboard_data['generated_at']}")

    if leaderboard_data["overall"]:
        print("\nTop 5 repositories:")
        for entry in leaderboard_data["overall"][:5]:
            print(
                f"  {entry['rank']}. {entry['repo']} - {entry['score']:.1f} ({entry['tier']})"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
