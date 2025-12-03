#!/usr/bin/env python3
"""Regenerate heatmap from existing batch assessment JSON."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentready.services.attribute_analyzer import AttributeAnalyzer  # noqa: E402


def main():
    """Load fixed all-assessments.json and regenerate heatmap with deduplication fix."""
    # Use the fixed JSON with duplicates removed
    input_file = Path(
        ".agentready/batch/reports-20251124-160049/all-assessments-fixed.json"
    )
    output_file = Path(".agentready/batch/reports-20251124-160049/heatmap-fixed.html")

    print(f"Loading batch assessment from {input_file}...")

    with input_file.open() as f:
        batch_data = json.load(f)

    successful = len([r for r in batch_data["results"] if r.get("assessment")])
    print(f"Loaded {len(batch_data['results'])} repositories, {successful} successful")

    # Generate heatmap using the new JSON-based method
    print(f"Generating heatmap to {output_file}...")
    analyzer = AttributeAnalyzer()
    analyzer.analyze_batch_from_json(batch_data, output_file)

    print("\n✓ Heatmap regenerated successfully!")
    print(f"  File: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
