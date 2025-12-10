"""Service for generating interactive HTML dashboards for Harbor comparisons."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentready.models.harbor import HarborComparison


class DashboardGenerator:
    """Generate interactive HTML dashboards with Chart.js visualizations."""

    def __init__(self, template_dir: Path = None):
        """Initialize dashboard generator.

        Args:
            template_dir: Directory containing Jinja2 templates
                         (defaults to src/agentready/templates)
        """
        if template_dir is None:
            # Default to package templates directory
            import agentready

            package_dir = Path(agentready.__file__).parent
            template_dir = package_dir / "templates"

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html"]),
        )

    def generate(self, comparison: HarborComparison, output_path: Path) -> None:
        """Generate interactive HTML dashboard.

        Creates a self-contained HTML file with:
        - Side-by-side bar charts (success rates, durations)
        - Per-task breakdown table
        - Statistical significance indicators
        - All CSS/JS inlined (no external dependencies)

        Args:
            comparison: HarborComparison with calculated deltas
            output_path: Path to write HTML dashboard

        Raises:
            FileNotFoundError: If template file not found
            jinja2.TemplateError: If template rendering fails
        """
        # Load template
        template = self.env.get_template("harbor_comparison.html.j2")

        # Prepare data for template
        template_data = {
            "comparison": comparison,
            "without_agent": comparison.without_agent,
            "with_agent": comparison.with_agent,
            "deltas": comparison.deltas,
            "significance": comparison.statistical_significance,
            "per_task": comparison.per_task_comparison,
            "created_at": comparison.created_at,
        }

        # Render template
        html_content = template.render(**template_data)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html_content)

    def generate_summary_text(self, comparison: HarborComparison) -> str:
        """Generate plain text summary of comparison.

        Args:
            comparison: HarborComparison with calculated deltas

        Returns:
            Plain text summary for console output
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Harbor Benchmark Comparison Summary")
        lines.append("=" * 60)
        lines.append("")

        # Overall metrics
        lines.append("Overall Metrics:")
        lines.append(
            f"  Success Rate:  {comparison.without_agent.success_rate:.1f}% → "
            f"{comparison.with_agent.success_rate:.1f}% "
            f"({comparison.deltas['success_rate_delta']:+.1f}%)"
        )

        lines.append(
            f"  Avg Duration:  {comparison.without_agent.avg_duration_sec:.1f}s → "
            f"{comparison.with_agent.avg_duration_sec:.1f}s "
            f"({comparison.deltas['avg_duration_delta_pct']:+.1f}%)"
        )

        lines.append("")

        # Statistical significance
        sig = comparison.statistical_significance
        if sig.get("success_rate_p_value") is not None:
            is_sig = (
                "✓ Significant"
                if sig["success_rate_significant"]
                else "✗ Not significant"
            )
            lines.append(
                f"  Success Rate: {is_sig} (p={sig['success_rate_p_value']:.4f})"
            )

        if sig.get("duration_p_value") is not None:
            is_sig = (
                "✓ Significant" if sig["duration_significant"] else "✗ Not significant"
            )
            lines.append(f"  Duration:     {is_sig} (p={sig['duration_p_value']:.4f})")

            if sig.get("duration_cohens_d") is not None:
                from agentready.services.harbor.comparer import interpret_effect_size

                effect = interpret_effect_size(sig["duration_cohens_d"])
                lines.append(
                    f"                Effect size: {effect} (d={sig['duration_cohens_d']:.2f})"
                )

        lines.append("")

        # Per-task summary
        lines.append("Per-Task Results:")
        for task_comp in comparison.per_task_comparison:
            task_name = task_comp["task_name"]
            without = task_comp.get("without_agent", {})
            with_agent_result = task_comp.get("with_agent", {})

            without_status = "✓" if without and without.get("success") else "✗"
            with_status = (
                "✓" if with_agent_result and with_agent_result.get("success") else "✗"
            )

            lines.append(f"  {task_name}:")
            lines.append(f"    Without agent: {without_status}")
            lines.append(f"    With agent:    {with_status}")

            if "delta" in task_comp:
                delta = task_comp["delta"]
                if delta.get("success_improved"):
                    lines.append("    Impact: +100% success (fixed failure)")
                elif delta.get("duration_delta_pct"):
                    lines.append(
                        f"    Impact: {delta['duration_delta_pct']:+.1f}% duration"
                    )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def generate_dashboard(comparison: HarborComparison, output_path: Path) -> None:
    """Convenience function to generate dashboard.

    Args:
        comparison: HarborComparison with calculated deltas
        output_path: Path to write HTML dashboard
    """
    generator = DashboardGenerator()
    generator.generate(comparison, output_path)
