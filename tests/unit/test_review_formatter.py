"""Unit tests for GitHub review formatter."""

import pytest

from agentready.github.review_formatter import (
    ReviewFinding,
    ReviewFormatter,
    calculate_score_impact,
    map_finding_to_attribute,
)
from agentready.models import Attribute


def test_review_finding_severity():
    """Test severity classification based on confidence."""
    finding_critical = ReviewFinding(
        description="Critical issue",
        attribute_id="2.3",
        attribute_name="Type Annotations",
        tier=2,
        confidence=95,
        location="https://github.com/org/repo/blob/abc123/file.py#L10-L15",
        details="Missing type hints",
    )
    assert finding_critical.severity == "critical"
    assert finding_critical.severity_emoji == "🔴"
    assert finding_critical.is_auto_fix_candidate is True

    finding_major = ReviewFinding(
        description="Major issue",
        attribute_id="2.8",
        attribute_name="Test Coverage",
        tier=2,
        confidence=85,
        location="https://github.com/org/repo/blob/abc123/test.py#L20-L25",
        details="Low test coverage",
    )
    assert finding_major.severity == "major"
    assert finding_major.severity_emoji == "🟡"
    assert finding_major.is_auto_fix_candidate is False


def test_calculate_score_impact():
    """Test score impact calculation with tier-based weighting."""
    # Tier 1 (Essential): 50% weight, ~8 attributes
    # Impact = (0.50 / 8) * 100 = 6.25 points
    impact_tier1 = calculate_score_impact("1.1", tier=1)
    assert impact_tier1 == pytest.approx(-6.25, rel=0.01)

    # Tier 2 (Critical): 30% weight, ~8 attributes
    # Impact = (0.30 / 8) * 100 = 3.75 points
    impact_tier2 = calculate_score_impact("2.3", tier=2)
    assert impact_tier2 == pytest.approx(-3.75, rel=0.01)

    # Tier 3 (Important): 15% weight, ~6 attributes
    # Impact = (0.15 / 6) * 100 = 2.5 points
    impact_tier3 = calculate_score_impact("3.1", tier=3)
    assert impact_tier3 == pytest.approx(-2.5, rel=0.01)

    # Tier 4 (Advanced): 5% weight, ~3 attributes
    # Impact = (0.05 / 3) * 100 = 1.67 points
    impact_tier4 = calculate_score_impact("4.1", tier=4)
    assert impact_tier4 == pytest.approx(-1.67, rel=0.01)


def test_map_finding_to_attribute_by_keyword():
    """Test attribute mapping using keyword analysis."""
    attributes = [
        Attribute(
            id="type_annotations",
            name="Type Annotations",
            tier=2,
            category="Code Quality",
            description="Type hints present",
            criteria="mypy passes",
            default_weight=0.0375,
        ),
        Attribute(
            id="test_coverage",
            name="Test Coverage",
            tier=2,
            category="Testing",
            description="High test coverage",
            criteria=">80% coverage",
            default_weight=0.0375,
        ),
    ]

    # Test type annotation mapping
    attr = map_finding_to_attribute(
        description="Missing type hints in function",
        file_path="src/module.py",
        attributes=attributes,
    )
    assert attr is not None
    assert attr.id == "type_annotations"
    assert attr.name == "Type Annotations"

    # Test test coverage mapping
    attr = map_finding_to_attribute(
        description="Low pytest coverage detected",
        file_path="tests/test_module.py",
        attributes=attributes,
    )
    assert attr is not None
    assert attr.id == "test_coverage"
    assert attr.name == "Test Coverage"


def test_map_finding_to_attribute_no_match():
    """Test attribute mapping when no keyword matches."""
    attributes = [
        Attribute(
            id="type_annotations",
            name="Type Annotations",
            tier=2,
            category="Code Quality",
            description="Type hints present",
            criteria="mypy passes",
            default_weight=0.0375,
        ),
    ]

    attr = map_finding_to_attribute(
        description="Generic code smell detected",
        file_path="src/module.py",
        attributes=attributes,
    )
    assert attr is None


def test_review_formatter_no_issues():
    """Test review output when no issues found."""
    formatter = ReviewFormatter(current_score=80.0, current_cert="Gold")
    output = formatter.format_review([])

    assert "### 🤖 AgentReady Code Review" in output
    assert "No issues found" in output
    assert "TOCTOU" in output  # Should mention coverage
    assert "Type annotations" in output


def test_review_formatter_with_findings():
    """Test review output with mixed severity findings."""
    findings = [
        ReviewFinding(
            description="Missing type annotations",
            attribute_id="2.3",
            attribute_name="Type Annotations",
            tier=2,
            confidence=95,
            location="https://github.com/org/repo/blob/abc123/file.py#L10-L15",
            details="Function lacks return type annotation",
            remediation_command="python -m mypy file.py",
            claude_md_section="#type-annotations",
        ),
        ReviewFinding(
            description="Low test coverage",
            attribute_id="2.8",
            attribute_name="Test Coverage",
            tier=2,
            confidence=85,
            location="https://github.com/org/repo/blob/abc123/test.py#L20-L25",
            details="Coverage is only 65%",
            remediation_command="pytest --cov=src",
        ),
    ]

    formatter = ReviewFormatter(current_score=80.0, current_cert="Gold")
    output = formatter.format_review(findings)

    # Check header
    assert "### 🤖 AgentReady Code Review" in output
    assert "2 issues found" in output
    assert "1 🔴 Critical" in output
    assert "1 🟡 Major" in output

    # Check score impact
    assert "Current 80.0/100" in output
    assert "if all issues fixed" in output

    # Check critical section
    assert "#### 🔴 Critical Issues" in output
    assert "Missing type annotations" in output
    assert "**Confidence**: 95%" in output
    assert "python -m mypy file.py" in output

    # Check major section
    assert "#### 🟡 Major Issues" in output
    assert "Low test coverage" in output
    assert "**Confidence**: 85%" in output

    # Check summary
    assert "#### Summary" in output
    assert "1 critical issues flagged for automatic resolution" in output
    assert "1 major issues require human judgment" in output
    assert "agentready assess ." in output

    # Check footer
    assert "🤖 Generated with [Claude Code]" in output


def test_review_formatter_certification_calculation():
    """Test certification level changes based on score."""
    formatter = ReviewFormatter(current_score=80.0, current_cert="Gold")

    # Test that formatter correctly identifies certification levels
    assert formatter._get_certification(95.0) == "Platinum"
    assert formatter._get_certification(85.0) == "Gold"
    assert formatter._get_certification(70.0) == "Silver"
    assert formatter._get_certification(50.0) == "Bronze"
    assert formatter._get_certification(30.0) == "Needs Improvement"


def test_review_finding_with_remediation():
    """Test finding with remediation command."""
    finding = ReviewFinding(
        description="Missing type hints",
        attribute_id="2.3",
        attribute_name="Type Annotations",
        tier=2,
        confidence=92,
        location="https://github.com/org/repo/blob/abc123/file.py#L10-L15",
        details="Function lacks return type",
        remediation_command="python -m mypy src/",
        claude_md_section="#type-safety",
    )

    formatter = ReviewFormatter()
    output = formatter.format_review([finding])

    assert "**Remediation**:" in output
    assert "python -m mypy src/" in output
    assert "Automated fix available via:" in output
    assert "```bash" in output
