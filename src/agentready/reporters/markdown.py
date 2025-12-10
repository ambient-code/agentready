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

        # Next Steps (moved up for visibility)
        sections.append(self._generate_next_steps(assessment))

        # Findings (flat badge list)
        sections.append(self._generate_findings(assessment))

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
        # Certification emoji map
        cert_emoji_map = {
            "Platinum": "💎",
            "Gold": "🥇",
            "Silver": "🥈",
            "Bronze": "🥉",
            "Needs Improvement": "⚠️",
        }
        cert_emoji = cert_emoji_map.get(assessment.certification_level, "")

        return f"""## 📊 Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | **{assessment.overall_score:.1f}/100** {cert_emoji} **{assessment.certification_level}** ([Tier Definitions](https://agentready.dev/attributes.html#tier-system)) |
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

    def _status_priority(self, status: str) -> int:
        """Get sort priority for status (lower = more important)."""
        priority_map = {
            "fail": 0,
            "error": 1,
            "pass": 2,
            "skipped": 3,
            "not_applicable": 4,
        }
        return priority_map.get(status, 99)

    def _generate_badge_line(self, finding) -> str:
        """Generate single-line badge-style finding."""
        from urllib.parse import quote

        # Badge components
        tier_label = f"T{finding.attribute.tier}"

        # URL-safe attribute name
        attr_name_safe = finding.attribute.name.replace(" ", "_")
        attr_name_safe = quote(attr_name_safe, safe="_")

        # Score for badge
        if finding.score is not None:
            score_text = f"{finding.score:.0f}--100"  # shields.io uses -- for /
        else:
            score_text = "N--A"

        # Color based on status
        color_map = {
            "pass": "green",
            "fail": "red",
            "skipped": "lightgray",
            "not_applicable": "lightgray",
            "error": "yellow",
        }
        color = color_map.get(finding.status, "gray")

        # Build badge URL
        badge_message = f"{attr_name_safe}_{score_text}"
        badge_url = f"https://img.shields.io/badge/{tier_label}-{badge_message}-{color}"

        # Status emoji
        status_emoji = self._get_status_emoji(finding.status)

        # Readable score display
        score_display = f"{finding.score:.0f}/100" if finding.score is not None else ""

        return f"![{tier_label}]({badge_url}) **{finding.attribute.name}** {status_emoji} {score_display}"

    def _generate_findings(self, assessment: Assessment) -> str:
        """Generate flat priority-sorted badge-style findings."""
        lines = [
            "## 📋 Detailed Findings",
            "",
            "Findings sorted by priority (Tier 1 failures first, then Tier 2, etc.)",
            "",
        ]

        # Sort findings by priority
        sorted_findings = sorted(
            assessment.findings,
            key=lambda f: (
                f.attribute.tier,  # Tier 1 before Tier 2
                self._status_priority(f.status),  # Failures before passes
                f.score if f.score is not None else 100,  # Lower scores first
            ),
        )

        # Generate badge line for each finding
        for finding in sorted_findings:
            lines.append(self._generate_badge_line(finding))

            # Add remediation details for failures/errors only
            if finding.status in ("fail", "error"):
                lines.append(self._generate_finding_detail(finding))

            lines.append("")  # Single blank line between findings

        return "\n".join(lines)

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
        """Generate collapsible remediation section."""
        lines = ["<details>", "<summary>📝 Remediation Steps</summary>", ""]

        # Measured/threshold (moved inside details for compactness)
        if finding.measured_value:
            lines.append(
                f"**Measured**: {finding.measured_value} (Threshold: {finding.threshold})"
            )
            lines.append("")

        # Evidence
        if finding.evidence:
            lines.append("**Evidence**:")
            for item in finding.evidence:
                lines.append(f"- {item}")
            lines.append("")

        # Remediation
        if finding.remediation:
            lines.append(finding.remediation.summary)
            lines.append("")

            if finding.remediation.steps:
                for i, step in enumerate(finding.remediation.steps, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

            if finding.remediation.commands:
                lines.append("**Commands**:")
                lines.append("```bash")
                lines.extend(finding.remediation.commands)
                lines.append("```")
                lines.append("")

            if finding.remediation.examples:
                lines.append("**Examples**:")
                for example in finding.remediation.examples:
                    lines.append("```")
                    lines.append(example)
                    lines.append("```")
                lines.append("")

        # Error message
        if finding.error_message:
            lines.append(f"**Error**: {finding.error_message}")
            lines.append("")

        lines.append("</details>")
        return "\n".join(lines)

    def _generate_next_steps(self, assessment: Assessment) -> str:
        """Generate prioritized next steps based on failures."""
        # Find all failing attributes
        failures = [
            f for f in assessment.findings if f.status == "fail" and f.score is not None
        ]

        if not failures:
            return """## ✨ Priority Improvements

**Congratulations!** All assessed attributes are passing. Consider:
- Implementing currently skipped attributes
- Maintaining these standards as the codebase evolves"""

        # Sort by tier (lower tier = higher priority) and score (lower score = more important)
        failures.sort(key=lambda f: (f.attribute.tier, f.score or 0))

        lines = [
            "## 🎯 Priority Improvements",
            "",
            "Focus on these high-impact fixes first:",
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
        if assessment.metadata:
            agentready_version = assessment.metadata.agentready_version
            research_version = assessment.metadata.research_version
            executed_by = assessment.metadata.executed_by
            timestamp_human = assessment.metadata.assessment_timestamp_human
        else:
            agentready_version = "unknown"
            research_version = "unknown"
            executed_by = "unknown"
            timestamp_human = assessment.timestamp.strftime("%B %d, %Y at %H:%M")

        return f"""---

## 📝 Assessment Metadata

- **AgentReady Version**: v{agentready_version}
- **Research Version**: v{research_version}
- **Repository Snapshot**: {assessment.repository.commit_hash}
- **Assessment Duration**: {assessment.duration_seconds:.1f}s
- **Assessed By**: {executed_by}
- **Assessment Date**: {timestamp_human}

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""
