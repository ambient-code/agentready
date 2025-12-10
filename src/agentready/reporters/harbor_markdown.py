"""Markdown reporter for Harbor comparisons."""

from pathlib import Path

from agentready.models.harbor import HarborComparison


class HarborMarkdownReporter:
    """Generate GitHub-Flavored Markdown reports for Harbor comparisons."""

    def generate(self, comparison: HarborComparison, output_path: Path) -> None:
        """Generate Markdown report.

        Creates a GitHub-Flavored Markdown file with:
        - Summary table
        - Statistical significance indicators
        - Per-task breakdown
        - Recommendations

        Args:
            comparison: HarborComparison with calculated deltas
            output_path: Path to write Markdown file
        """
        markdown = self._build_markdown(comparison)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(markdown)

    def _build_markdown(self, comparison: HarborComparison) -> str:
        """Build complete Markdown content.

        Args:
            comparison: HarborComparison object

        Returns:
            Complete Markdown content as string
        """
        sections = [
            self._header(comparison),
            self._summary_table(comparison),
            self._statistical_significance(comparison),
            self._per_task_results(comparison),
            self._conclusion(comparison),
        ]

        return "\n\n".join(sections)

    def _header(self, comparison: HarborComparison) -> str:
        """Generate header section."""
        task_names = [t["task_name"] for t in comparison.per_task_comparison]
        return f"""# Harbor Benchmark Comparison

**Created**: {comparison.created_at}
**Tasks**: {len(task_names)} ({', '.join(task_names[:3])}{'...' if len(task_names) > 3 else ''})
**Agent File**: `.claude/agents/doubleagent.md`"""

    def _summary_table(self, comparison: HarborComparison) -> str:
        """Generate summary metrics table."""
        without = comparison.without_agent
        with_agent = comparison.with_agent
        deltas = comparison.deltas
        sig = comparison.statistical_significance

        # Format significance indicators
        success_sig = self._format_significance(
            sig.get("success_rate_significant"), sig.get("success_rate_p_value")
        )
        duration_sig = self._format_significance(
            sig.get("duration_significant"), sig.get("duration_p_value")
        )

        return f"""## Summary

| Metric | Without Agent | With Agent | Delta | Significant? |
|--------|--------------|------------|-------|--------------|
| Success Rate | {without.success_rate:.1f}% | {with_agent.success_rate:.1f}% | {deltas['success_rate_delta']:+.1f}% | {success_sig} |
| Completion Rate | {without.completion_rate:.1f}% | {with_agent.completion_rate:.1f}% | {deltas['completion_rate_delta']:+.1f}% | - |
| Avg Duration | {without.avg_duration_sec / 60:.1f} min | {with_agent.avg_duration_sec / 60:.1f} min | {deltas['avg_duration_delta_pct']:+.1f}% | {duration_sig} |
| Successful Tasks | {without.successful_tasks}/{without.total_tasks} | {with_agent.successful_tasks}/{with_agent.total_tasks} | {deltas['successful_tasks_delta']:+d} | - |"""

    def _format_significance(
        self, is_significant: bool = None, p_value: float = None
    ) -> str:
        """Format statistical significance indicator.

        Args:
            is_significant: Whether difference is statistically significant
            p_value: P-value from statistical test

        Returns:
            Formatted string (e.g., "✓ (p=0.04)" or "✗ (p=0.23)")
        """
        if is_significant is None or p_value is None:
            return "-"

        symbol = "✓" if is_significant else "✗"
        return f"{symbol} (p={p_value:.4f})"

    def _statistical_significance(self, comparison: HarborComparison) -> str:
        """Generate statistical significance section."""
        sig = comparison.statistical_significance

        if not sig.get("success_rate_p_value") and not sig.get("duration_p_value"):
            return "## Statistical Analysis\n\n*Statistical tests not available (scipy not installed)*"

        lines = ["## Statistical Analysis"]

        # Success rate analysis
        if sig.get("success_rate_p_value") is not None:
            is_sig = sig["success_rate_significant"]
            p_val = sig["success_rate_p_value"]

            if is_sig:
                lines.append(
                    f"- **Success Rate**: Statistically significant improvement "
                    f"(p={p_val:.4f}, p<0.05)"
                )
            else:
                lines.append(
                    f"- **Success Rate**: No statistically significant difference "
                    f"(p={p_val:.4f}, p≥0.05)"
                )

        # Duration analysis
        if sig.get("duration_p_value") is not None:
            is_sig = sig["duration_significant"]
            p_val = sig["duration_p_value"]
            cohens_d = sig.get("duration_cohens_d")

            if is_sig:
                effect_text = ""
                if cohens_d is not None:
                    from agentready.services.harbor.comparer import (
                        interpret_effect_size,
                    )

                    effect = interpret_effect_size(cohens_d)
                    effect_text = f" with {effect} effect size (d={cohens_d:.2f})"

                lines.append(
                    f"- **Duration**: Statistically significant difference "
                    f"(p={p_val:.4f}, p<0.05){effect_text}"
                )
            else:
                lines.append(
                    f"- **Duration**: No statistically significant difference "
                    f"(p={p_val:.4f}, p≥0.05)"
                )

        return "\n".join(lines)

    def _per_task_results(self, comparison: HarborComparison) -> str:
        """Generate per-task results section."""
        lines = ["## Per-Task Results"]

        for task_comp in comparison.per_task_comparison:
            lines.append(f"\n### {task_comp['task_name']}")
            lines.append(
                self._format_task_result(
                    "Without Agent", task_comp.get("without_agent")
                )
            )
            lines.append(
                self._format_task_result("With Agent", task_comp.get("with_agent"))
            )

            # Add impact analysis if delta exists
            if "delta" in task_comp:
                lines.append(self._format_task_impact(task_comp["delta"]))

        return "\n".join(lines)

    def _format_task_result(self, label: str, result: dict) -> str:
        """Format a single task result line."""
        if not result:
            return f"- **{label}**: N/A"

        status = "✓ Success" if result.get("success") else "✗ Failed"
        duration = result.get("duration_sec", 0) / 60
        return f"- **{label}**: {status} ({duration:.1f} min)"

    def _format_task_impact(self, delta: dict) -> str:
        """Format task impact analysis."""
        if delta.get("success_improved"):
            return "- **Impact**: +100% success (fixed failure)"

        duration_pct = delta.get("duration_delta_pct")
        if duration_pct:
            direction = "faster" if duration_pct < 0 else "slower"
            return f"- **Impact**: {abs(duration_pct):.1f}% {direction}"

        return "- **Impact**: No change"

    def _conclusion(self, comparison: HarborComparison) -> str:
        """Generate conclusion and recommendations."""
        deltas = comparison.deltas
        sig = comparison.statistical_significance

        lines = ["## Conclusion"]

        # Determine overall recommendation
        success_improved = deltas["success_rate_delta"] > 0
        duration_improved = deltas["avg_duration_delta_pct"] < 0
        statistically_significant = sig.get("success_rate_significant") or sig.get(
            "duration_significant"
        )

        if success_improved and statistically_significant:
            lines.append(
                f"\nThe `doubleagent.md` agent file shows **statistically significant improvement** "
                f"in success rate ({deltas['success_rate_delta']:+.1f}%)"
            )

            if duration_improved:
                lines.append(
                    f"and execution speed ({deltas['avg_duration_delta_pct']:+.1f}%)."
                )
            else:
                lines.append(".")

            lines.append(
                "\n**Recommendation**: ✅ **Include `doubleagent.md`** "
                "in AgentReady development workflows."
            )

        elif success_improved or duration_improved:
            lines.append("\nThe `doubleagent.md` agent file shows improvements:")
            if success_improved:
                lines.append(f"- Success rate: {deltas['success_rate_delta']:+.1f}%")
            if duration_improved:
                lines.append(f"- Duration: {deltas['avg_duration_delta_pct']:+.1f}%")

            lines.append(
                "\nHowever, differences are not statistically significant (larger sample size recommended)."
            )
            lines.append(
                "\n**Recommendation**: ⚠️ **Consider including** `doubleagent.md` "
                "but validate with larger benchmark."
            )

        else:
            lines.append("\nNo significant improvement detected.")
            lines.append(
                "\n**Recommendation**: ❌ **Agent file may not provide measurable benefit** "
                "for tested tasks."
            )

        return "\n".join(lines)


def generate_markdown_report(comparison: HarborComparison, output_path: Path) -> None:
    """Convenience function to generate Markdown report.

    Args:
        comparison: HarborComparison with calculated deltas
        output_path: Path to write Markdown file
    """
    reporter = HarborMarkdownReporter()
    reporter.generate(comparison, output_path)
