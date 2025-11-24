"""Format code review findings with AgentReady attribute mapping and score impact."""

from dataclasses import dataclass
from typing import List, Optional

from ..models import Attribute


@dataclass
class ReviewFinding:
    """Represents a single code review finding."""

    description: str
    attribute_id: str
    attribute_name: str
    tier: int
    confidence: int
    location: str  # GitHub permalink
    details: str
    remediation_command: Optional[str] = None
    claude_md_section: Optional[str] = None

    @property
    def severity(self) -> str:
        """Determine severity based on confidence score."""
        if self.confidence >= 90:
            return "critical"
        elif self.confidence >= 80:
            return "major"
        elif self.confidence >= 70:
            return "minor"
        else:
            return "info"

    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level."""
        return {
            "critical": "🔴",
            "major": "🟡",
            "minor": "🔵",
            "info": "⚪",
        }[self.severity]

    @property
    def is_auto_fix_candidate(self) -> bool:
        """Check if this finding should be auto-fixed."""
        return self.confidence >= 90


def calculate_score_impact(
    attribute_id: str, tier: int, current_score: float = 80.0
) -> float:
    """Calculate impact on AgentReady score if this issue is fixed.

    Args:
        attribute_id: The attribute being affected (e.g., "2.3")
        tier: Attribute tier (1=Essential 50%, 2=Critical 30%, 3=Important 15%, 4=Advanced 5%)
        current_score: Current AgentReady score (default: 80.0)

    Returns:
        Score impact in points (e.g., -2.5 means fixing would add 2.5 points)
    """
    # Tier weights from AgentReady scoring algorithm
    tier_weights = {
        1: 0.50,  # Essential
        2: 0.30,  # Critical
        3: 0.15,  # Important
        4: 0.05,  # Advanced
    }

    # Each tier has multiple attributes, assume equal distribution
    # Tier 1: ~8 attrs, Tier 2: ~8 attrs, Tier 3: ~6 attrs, Tier 4: ~3 attrs
    attrs_per_tier = {1: 8, 2: 8, 3: 6, 4: 3}

    tier_weight = tier_weights.get(tier, 0.05)
    num_attrs = attrs_per_tier.get(tier, 8)

    # Impact = (tier_weight / num_attrs) * 100
    # This represents the max points this single attribute contributes
    impact = (tier_weight / num_attrs) * 100

    # If issue is found, assume attribute score drops from 100 to 0
    # So fixing it would restore full impact
    return -impact


def map_finding_to_attribute(
    description: str, file_path: str, attributes: List[Attribute]
) -> Optional[Attribute]:
    """Map a code review finding to an AgentReady attribute.

    Args:
        description: Brief description of the issue
        file_path: File where issue was found
        attributes: List of all AgentReady attributes

    Returns:
        Matching Attribute or None if no clear match
    """
    # Keyword mapping to attribute IDs (snake_case)
    # Note: These IDs should match actual attribute IDs from research report
    keyword_map = {
        "type annotation": "type_annotations",
        "type hint": "type_annotations",
        "mypy": "type_annotations",
        "test coverage": "test_coverage",
        "pytest": "test_coverage",
        "missing test": "test_coverage",
        "claude.md": "claude_md_file",
        "documentation": "readme_file",
        "readme": "readme_file",
        "conventional commit": "conventional_commits",
        "commit message": "conventional_commits",
        "pre-commit": "pre_commit_hooks",
        "hook": "pre_commit_hooks",
        "gitignore": "gitignore_file",
        "git ignore": "gitignore_file",
        "standard layout": "standard_layout",
        "project structure": "standard_layout",
        "dependency": "dependency_management",
        "requirements": "dependency_management",
        "lock file": "lock_file_present",
        "security": "security_best_practices",
        "vulnerability": "security_best_practices",
        "repomix": "repomix_configuration",
        "complexity": "low_complexity",
        "cyclomatic": "low_complexity",
    }

    # Search for keywords in description and file path
    search_text = f"{description.lower()} {file_path.lower()}"

    for keyword, attr_id in keyword_map.items():
        if keyword in search_text:
            # Find matching attribute
            for attr in attributes:
                if attr.id == attr_id:
                    return attr

    # Default fallback: if in assessors/, likely related to code quality
    if "assessors/" in file_path:
        for attr in attributes:
            if "code" in attr.category.lower():
                return attr

    return None


class ReviewFormatter:
    """Format AgentReady code review findings into structured output."""

    def __init__(self, current_score: float = 80.0, current_cert: str = "Gold"):
        """Initialize formatter.

        Args:
            current_score: Current AgentReady self-assessment score
            current_cert: Current certification level (Platinum/Gold/Silver/Bronze)
        """
        self.current_score = current_score
        self.current_cert = current_cert

    def format_review(self, findings: List[ReviewFinding]) -> str:
        """Format findings into AgentReady review output.

        Args:
            findings: List of review findings

        Returns:
            Markdown-formatted review comment
        """
        if not findings:
            return self._format_no_issues()

        # Categorize by severity
        critical = [f for f in findings if f.severity == "critical"]
        major = [f for f in findings if f.severity == "major"]
        minor = [f for f in findings if f.severity == "minor"]

        # Calculate total score impact
        total_impact = sum(
            calculate_score_impact(f.attribute_id, f.tier) for f in findings
        )
        potential_score = self.current_score - total_impact  # Impact is negative
        potential_cert = self._get_certification(potential_score)

        # Build output
        lines = [
            "### 🤖 AgentReady Code Review",
            "",
            f"**PR Status**: {len(findings)} issues found "
            f"({len(critical)} 🔴 Critical, {len(major)} 🟡 Major, {len(minor)} 🔵 Minor)",
            f"**Score Impact**: Current {self.current_score:.1f}/100 → {potential_score:.1f} if all issues fixed",
            f"**Certification**: {self.current_cert} → {potential_cert} potential",
            "",
            "---",
            "",
        ]

        # Critical issues
        if critical:
            lines.extend(
                [
                    "#### 🔴 Critical Issues (Confidence ≥90) - Auto-Fix Recommended",
                    "",
                ]
            )
            for i, finding in enumerate(critical, 1):
                lines.extend(self._format_finding(i, finding))
                lines.append("")

        # Major issues
        if major:
            lines.extend(
                ["#### 🟡 Major Issues (Confidence 80-89) - Manual Review Required", ""]
            )
            start_num = len(critical) + 1
            for i, finding in enumerate(major, start_num):
                lines.extend(self._format_finding(i, finding))
                lines.append("")

        # Minor issues
        if minor:
            lines.extend(["#### 🔵 Minor Issues (Confidence 70-79)", ""])
            start_num = len(critical) + len(major) + 1
            for i, finding in enumerate(minor, start_num):
                lines.extend(self._format_finding(i, finding))
                lines.append("")

        # Summary
        lines.extend(
            [
                "---",
                "",
                "#### Summary",
                "",
                f"- **Auto-Fix Candidates**: {len(critical)} critical issues flagged for automatic resolution",
                f"- **Manual Review**: {len(major)} major issues require human judgment",
                f"- **Total Score Improvement Potential**: +{abs(total_impact):.1f} points if all issues addressed",
                "- **AgentReady Assessment**: Run `agentready assess .` after fixes to verify score",
                "",
                "---",
                "",
                "🤖 Generated with [Claude Code](https://claude.ai/code)",
                "",
                "<sub>- If this review was useful, react with 👍. Otherwise, react with 👎.</sub>",
            ]
        )

        return "\n".join(lines)

    def _format_finding(self, num: int, finding: ReviewFinding) -> List[str]:
        """Format a single finding."""
        impact = calculate_score_impact(finding.attribute_id, finding.tier)
        lines = [
            f"##### {num}. {finding.description}",
            f"**Attribute**: {finding.attribute_id} {finding.attribute_name} (Tier {finding.tier})",
        ]

        if finding.claude_md_section:
            lines[-1] += f" - [CLAUDE.md section]({finding.claude_md_section})"

        lines.extend(
            [
                f"**Confidence**: {finding.confidence}%",
                f"**Score Impact**: {impact:+.1f} points",
                f"**Location**: {finding.location}",
                "",
                "**Issue Details**:",
                finding.details,
            ]
        )

        if finding.remediation_command:
            lines.extend(
                [
                    "",
                    "**Remediation**:",
                    "```bash",
                    "# Automated fix available via:",
                    "# (Will be applied automatically if this is a blocker/critical)",
                    finding.remediation_command,
                    "```",
                ]
            )

        return lines

    def _format_no_issues(self) -> str:
        """Format output when no issues found."""
        return """### 🤖 AgentReady Code Review

No issues found. Checked for bugs, CLAUDE.md compliance, and AgentReady-specific concerns.

**Review Coverage**:
- Security vulnerabilities (TOCTOU, path traversal, injection)
- Assessment accuracy (false positives/negatives)
- Type annotations (Python 3.11+ compatibility)
- Error handling patterns
- CLAUDE.md workflow compliance

---

🤖 Generated with [Claude Code](https://claude.ai/code)"""

    def _get_certification(self, score: float) -> str:
        """Get certification level for a given score."""
        if score >= 90:
            return "Platinum"
        elif score >= 75:
            return "Gold"
        elif score >= 60:
            return "Silver"
        elif score >= 40:
            return "Bronze"
        else:
            return "Needs Improvement"
