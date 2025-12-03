#!/usr/bin/env python3
"""
Extract repository URLs from filtered GitHub org analysis.

Reads the filtered active originals JSON and outputs a simple text file
with one repository URL per line for use with agentready assess-batch.
"""

import json
from pathlib import Path


def main():
    # Input: filtered repos JSON
    input_file = Path(".cache/github-org-analysis/opendatahub-io-active-originals.json")

    # Output: simple text file with URLs
    output_file = Path("opendatahub-repos.txt")

    # Load filtered repository data
    print(f"Loading filtered repositories from {input_file}")
    with input_file.open() as f:
        data = json.load(f)

    repos = data["repositories"]
    print(f"Found {len(repos)} repositories")

    # Extract URLs
    urls = [repo["url"] for repo in repos]

    # Write to output file
    with output_file.open("w") as f:
        for url in urls:
            f.write(f"{url}\n")

    print(f"✅ Wrote {len(urls)} repository URLs to {output_file}")
    print("\nUsage:")
    print(
        f"  agentready assess-batch --repos-file {output_file} --cache-dir ~/repos/cache/github-org --generate-heatmap"
    )


if __name__ == "__main__":
    main()
