"""Markdown reporter for generating version-control-friendly assessment reports."""

from pathlib import Path

from ..models.assessment import Assessment
from .base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Generates GitHub-Flavored Markdown reports.

    Features:
    - Version-control friendly (git diff shows progress)
    - Renders properly on GitHub/GitLab/Bitbucket
    - Tables for summary data
    - Collapsible details using HTML details/summary
    - Code blocks with syntax highlighting
    - Emoji indicators for status
    """

    def generate(self, assessment: Assessment, output_path: Path) -> Path:
        """Generate Markdown report from assessment data.

        Args:
            assessment: Complete assessment with findings
            output_path: Path where Markdown file should be saved

        Returns:
            Path to generated Markdown file

        Raises:
            IOError: If Markdown cannot be written
        """
        sections = []

        # Header
        sections.append(self._generate_header(assessment))

        # Summary
        sections.append(self._generate_summary(assessment))

        # Certification Ladder
        sections.append(self._generate_certification_ladder(assessment))

        # Findings by Category
        sections.append(self._generate_findings(assessment))

        # Next Steps
        sections.append(self._generate_next_steps(assessment))

        # Footer
        sections.append(self._generate_footer(assessment))

        # Combine all sections
        markdown_content = "\n\n".join(sections)

        # Write to file using base class method
        return self._write_file(markdown_content, output_path)

    def _generate_header(self, assessment: Assessment) -> str:
        """Generate report header with repository info and metadata."""
        header = "# 🤖 AgentReady Assessment Report\n\n"

        # Repository information
        header += f"**Repository**: {assessment.repository.name}\n"
        header += f"**Path**: `{assessment.repository.path}`\n"
        header += f"**Branch**: `{assessment.repository.branch}` | **Commit**: `{assessment.repository.commit_hash[:8]}`\n"

        # Assessment metadata (if available)
        if assessment.metadata:
            header += (
                f"**Assessed**: {assessment.metadata.assessment_timestamp_human}\n"
            )
            header += (
                f"**AgentReady Version**: {assessment.metadata.agentready_version}\n"
            )
            header += f"**Run by**: {assessment.metadata.executed_by}\n"
        else:
            # Fallback to timestamp if metadata not available
            header += (
                f"**Assessed**: {assessment.timestamp.strftime('%B %d, %Y at %H:%M')}\n"
            )

        header += "\n---"

        return header

    def _generate_summary(self, assessment: Assessment) -> str:
        """Generate summary section with key metrics."""
        return f"""## 📊 Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | **{assessment.overall_score:.1f}/100** |
| **Certification Level** | **{assessment.certification_level}** |
| **Attributes Assessed** | {assessment.attributes_assessed}/{assessment.attributes_total} |
| **Attributes Not Assessed** | {assessment.attributes_not_assessed} |
| **Assessment Duration** | {assessment.duration_seconds:.1f}s |

### Languages Detected

{self._format_languages(assessment.repository.languages)}

### Repository Stats

- **Total Files**: {assessment.repository.total_files:,}
- **Total Lines**: {assessment.repository.total_lines:,}"""

    def _format_languages(self, languages: dict[str, int]) -> str:
        """Format language detection results."""
        if not languages:
            return "No languages detected"

        lines = []
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{lang}**: {count} files")
        return "\n".join(lines)

    def _generate_certification_ladder(self, assessment: Assessment) -> str:
        """Generate certification ladder visualization."""
        levels = [
            ("Platinum", "💎", "90-100", assessment.certification_level == "Platinum"),
            ("Gold", "🥇", "75-89", assessment.certification_level == "Gold"),
            ("Silver", "🥈", "60-74", assessment.certification_level == "Silver"),
            ("Bronze", "🥉", "40-59", assessment.certification_level == "Bronze"),
            (
                "Needs Improvement",
                "⚠️",
                "0-39",
                assessment.certification_level == "Needs Improvement",
            ),
        ]

        lines = ["## 🎖️ Certification Ladder", ""]
        for name, emoji, range_str, is_active in levels:
            marker = "**→ YOUR LEVEL ←**" if is_active else ""
            lines.append(f"- {emoji} **{name}** ({range_str}) {marker}")

        return "\n".join(lines)

    def _generate_findings(self, assessment: Assessment) -> str:
        """Generate detailed findings by category."""
        sections = ["## 📋 Detailed Findings"]

        # Group findings by category
        by_category = {}
        for finding in assessment.findings:
            category = finding.attribute.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)

        # Generate section for each category
        for category in sorted(by_category.keys()):
            findings = by_category[category]
            sections.append(f"\n### {category}")

            # Summary table for this category
            sections.append("\n| Attribute | Tier | Status | Score |")
            sections.append("|-----------|------|--------|-------|")

            for finding in findings:
                status_emoji = self._get_status_emoji(finding.status)
                score_display = (
                    f"{finding.score:.0f}" if finding.score is not None else "—"
                )
                tier_badge = f"T{finding.attribute.tier}"

                sections.append(
                    f"| {finding.attribute.name} | {tier_badge} | {status_emoji} {finding.status} | {score_display} |"
                )

            # Detailed findings (only for fail/error)
            for finding in findings:
                if finding.status in ("fail", "error"):
                    sections.append(self._generate_finding_detail(finding))

        return "\n".join(sections)

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for finding status."""
        emoji_map = {
            "pass": "✅",
            "fail": "❌",
            "skipped": "⊘",
            "not_applicable": "⊘",
            "error": "⚠️",
        }
        return emoji_map.get(status, "❓")

    def _generate_finding_detail(self, finding) -> str:
        """Generate detailed finding section."""
        lines = [
            f"\n#### {self._get_status_emoji(finding.status)} {finding.attribute.name}"
        ]

        # Basic info
        if finding.measured_value:
            lines.append(
                f"\n**Measured**: {finding.measured_value} (Threshold: {finding.threshold})"
            )

        # Evidence
        if finding.evidence:
            lines.append("\n**Evidence**:")
            for item in finding.evidence:
                lines.append(f"- {item}")

        # Remediation
        if finding.remediation:
            lines.append(
                "\n<details><summary><strong>📝 Remediation Steps</strong></summary>\n"
            )
            lines.append(f"\n{finding.remediation.summary}\n")

            if finding.remediation.steps:
                for i, step in enumerate(finding.remediation.steps, 1):
                    lines.append(f"{i}. {step}")

            if finding.remediation.commands:
                lines.append("\n**Commands**:\n")
                lines.append("```bash")
                lines.append("\n".join(finding.remediation.commands))
                lines.append("```")

            if finding.remediation.examples:
                lines.append("\n**Examples**:\n")
                for example in finding.remediation.examples:
                    lines.append("```")
                    lines.append(example)
                    lines.append("```")

            lines.append("\n</details>")

        # Error message
        if finding.error_message:
            lines.append(f"\n**Error**: {finding.error_message}")

        return "\n".join(lines)

    def _generate_next_steps(self, assessment: Assessment) -> str:
        """Generate prioritized next steps based on failures."""
        # Find all failing attributes
        failures = [
            f for f in assessment.findings if f.status == "fail" and f.score is not None
        ]

        if not failures:
            return """## ✨ Next Steps

**Congratulations!** All assessed attributes are passing. Consider:
- Implementing currently skipped attributes
- Maintaining these standards as the codebase evolves"""

        # Sort by tier (lower tier = higher priority) and score (lower score = more important)
        failures.sort(key=lambda f: (f.attribute.tier, f.score or 0))

        lines = [
            "## 🎯 Next Steps",
            "",
            "**Priority Improvements** (highest impact first):",
            "",
        ]

        for i, finding in enumerate(failures[:5], 1):  # Top 5 only
            potential_points = finding.attribute.default_weight * 100
            lines.append(
                f"{i}. **{finding.attribute.name}** (Tier {finding.attribute.tier}) - "
                f"+{potential_points:.1f} points potential"
            )
            if finding.remediation:
                lines.append(f"   - {finding.remediation.summary}")

        return "\n".join(lines)

    def _generate_footer(self, assessment: Assessment) -> str:
        """Generate report footer."""
        return f"""---

## 📝 Assessment Metadata

- **Tool Version**: AgentReady v1.0.0
- **Research Report**: Bundled version
- **Repository Snapshot**: {assessment.repository.commit_hash}
- **Assessment Duration**: {assessment.duration_seconds:.1f}s

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""
