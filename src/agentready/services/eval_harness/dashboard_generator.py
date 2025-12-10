"""Service for generating GitHub Pages dashboard data from evaluation results."""

from pathlib import Path

from ...models.eval_harness import EvalSummary, load_from_json, save_to_json


class DashboardGenerator:
    """Generate Jekyll-compatible data files for GitHub Pages dashboard.

    Responsibilities:
    - Load evaluation summary
    - Generate docs/_data/tbench/ data files for Jekyll
    - Format data for Chart.js consumption
    - Create summary.json, ranked_assessors.json, tier_impacts.json
    """

    def generate(
        self,
        eval_harness_dir: Path,
        docs_data_dir: Path = None,
    ) -> dict:
        """Generate dashboard data files for GitHub Pages.

        Args:
            eval_harness_dir: Directory containing summary.json
                             (e.g., .agentready/eval_harness/)
            docs_data_dir: Jekyll _data directory
                          (defaults to docs/_data/tbench/)

        Returns:
            Dict with paths to generated files

        Raises:
            FileNotFoundError: If summary.json not found
        """
        # Load summary
        summary_file = eval_harness_dir / "summary.json"
        if not summary_file.exists():
            raise FileNotFoundError(
                f"Summary file not found: {summary_file}. "
                "Run 'agentready eval-harness run-tier' or 'summarize' first."
            )

        summary = load_from_json(EvalSummary, summary_file)

        # Set output directory
        if docs_data_dir is None:
            # Default to docs/_data/tbench/ in repository root
            repo_root = self._find_repo_root(eval_harness_dir)
            docs_data_dir = repo_root / "docs" / "_data" / "tbench"

        docs_data_dir.mkdir(parents=True, exist_ok=True)

        # Generate data files
        generated_files = {}

        # 1. Complete summary (for main dashboard)
        summary_data_file = docs_data_dir / "summary.json"
        save_to_json(summary, summary_data_file)
        generated_files["summary"] = summary_data_file

        # 2. Ranked assessors (for leaderboard table)
        ranked = summary.get_ranked_assessors()
        ranked_data = [impact.to_dict() for impact in ranked]
        ranked_file = docs_data_dir / "ranked_assessors.json"
        self._save_json_list(ranked_data, ranked_file)
        generated_files["ranked_assessors"] = ranked_file

        # 3. Tier impacts (for bar chart)
        tier_data = [
            {"tier": tier, "delta": delta, "tier_name": self._tier_name(tier)}
            for tier, delta in sorted(summary.tier_impacts.items())
        ]
        tier_file = docs_data_dir / "tier_impacts.json"
        self._save_json_list(tier_data, tier_file)
        generated_files["tier_impacts"] = tier_file

        # 4. Baseline data (for comparison chart)
        baseline_data = {
            "mean_score": summary.baseline.mean_score,
            "std_dev": summary.baseline.std_dev,
            "median_score": summary.baseline.median_score,
            "min_score": summary.baseline.min_score,
            "max_score": summary.baseline.max_score,
            "iterations": summary.baseline.iterations,
        }
        baseline_file = docs_data_dir / "baseline.json"
        self._save_json_dict(baseline_data, baseline_file)
        generated_files["baseline"] = baseline_file

        # 5. Summary stats (for overview cards)
        stats_data = {
            "total_assessors_tested": summary.total_assessors_tested,
            "significant_improvements": summary.significant_improvements,
            "significance_rate": (
                summary.significant_improvements / summary.total_assessors_tested * 100
                if summary.total_assessors_tested > 0
                else 0
            ),
            "timestamp": summary.timestamp.isoformat(),
        }
        stats_file = docs_data_dir / "stats.json"
        self._save_json_dict(stats_data, stats_file)
        generated_files["stats"] = stats_file

        return generated_files

    @staticmethod
    def _find_repo_root(start_path: Path) -> Path:
        """Find repository root by looking for .git directory.

        Args:
            start_path: Starting directory

        Returns:
            Repository root path

        Raises:
            FileNotFoundError: If .git not found
        """
        current = start_path.resolve()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        raise FileNotFoundError(
            f"Could not find repository root from {start_path}. "
            "No .git directory found."
        )

    @staticmethod
    def _tier_name(tier: int) -> str:
        """Get human-readable tier name.

        Args:
            tier: Tier number 1-4

        Returns:
            Tier name (Essential, Critical, Important, Advanced)
        """
        tier_names = {
            1: "Essential",
            2: "Critical",
            3: "Important",
            4: "Advanced",
        }
        return tier_names.get(tier, f"Tier {tier}")

    @staticmethod
    def _save_json_list(data: list, output_path: Path):
        """Save list to JSON file.

        Args:
            data: List to save
            output_path: Path to output file
        """
        import json

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, indent=2, fp=f)

    @staticmethod
    def _save_json_dict(data: dict, output_path: Path):
        """Save dict to JSON file.

        Args:
            data: Dict to save
            output_path: Path to output file
        """
        import json

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, indent=2, fp=f)
