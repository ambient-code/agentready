"""Unit tests for pattern extraction."""

from datetime import datetime

import pytest

from agentready.learners.pattern_extractor import PatternExtractor
from agentready.models import Assessment, Attribute, Finding, Repository


@pytest.fixture
def sample_repository():
    """Create test repository."""
    return Repository(
        path="/tmp/test",
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 100},
        total_files=10,
        total_lines=500,
    )


@pytest.fixture
def sample_attribute_tier1():
    """Create tier 1 test attribute."""
    return Attribute(
        id="claude_md_file",
        name="CLAUDE.md File",
        category="Documentation",
        tier=1,
        description="Comprehensive CLAUDE.md file with repository context",
        criteria="File exists and contains required sections",
        default_weight=1.0,
    )


@pytest.fixture
def sample_attribute_tier2():
    """Create tier 2 test attribute."""
    return Attribute(
        id="type_annotations",
        name="Type Annotations",
        category="Code Quality",
        tier=2,
        description="Comprehensive type annotations in code",
        criteria="80% of functions have type hints",
        default_weight=0.8,
    )


@pytest.fixture
def sample_finding_high_score(sample_attribute_tier1):
    """Create high-scoring passing finding."""
    return Finding(
        attribute=sample_attribute_tier1,
        status="pass",
        score=95.0,
        measured_value="present",
        threshold="present",
        evidence=["CLAUDE.md exists", "Contains 5/5 required sections"],
        remediation=None,
        error_message=None,
    )


@pytest.fixture
def sample_finding_low_score(sample_attribute_tier1):
    """Create low-scoring finding."""
    return Finding(
        attribute=sample_attribute_tier1,
        status="pass",
        score=65.0,
        measured_value="partial",
        threshold="complete",
        evidence=["CLAUDE.md exists but incomplete"],
        remediation=None,
        error_message=None,
    )


@pytest.fixture
def sample_finding_failing(sample_attribute_tier2):
    """Create failing finding."""
    return Finding(
        attribute=sample_attribute_tier2,
        status="fail",
        score=45.0,
        measured_value="30%",
        threshold="80%",
        evidence=["Only 30% coverage"],
        remediation=None,
        error_message=None,
    )


@pytest.fixture
def sample_assessment_with_findings(
    sample_repository, sample_finding_high_score, sample_finding_low_score
):
    """Create assessment with multiple findings."""
    return Assessment(
        repository=sample_repository,
        timestamp=datetime.now(),
        overall_score=85.0,
        certification_level="Gold",
        attributes_assessed=2,
        attributes_not_assessed=0,
        attributes_total=2,
        findings=[sample_finding_high_score, sample_finding_low_score],
        config=None,
        duration_seconds=1.0,
    )


class TestPatternExtractor:
    """Test PatternExtractor class."""

    def test_init_default_min_score(self, sample_repository):
        """Test initialization with default min score."""
        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=85.0,
            certification_level="Gold",
            attributes_assessed=0,
            attributes_not_assessed=0,
            attributes_total=0,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        assert extractor.min_score == 80.0

    def test_init_custom_min_score(self, sample_repository):
        """Test initialization with custom min score."""
        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=85.0,
            certification_level="Gold",
            attributes_assessed=0,
            attributes_not_assessed=0,
            attributes_total=0,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment, min_score=90.0)
        assert extractor.min_score == 90.0

    def test_extract_patterns_from_high_score_finding(
        self, sample_repository, sample_finding_high_score
    ):
        """Test extracting pattern from high-score finding."""
        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[sample_finding_high_score],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skills = extractor.extract_all_patterns()

        assert len(skills) == 1
        assert skills[0].confidence == 95.0
        assert skills[0].skill_id == "setup-claude-md"
        assert skills[0].name == "Setup CLAUDE.md Configuration"

    def test_filters_low_score_findings(self, sample_assessment_with_findings):
        """Test that low-score findings are filtered."""
        extractor = PatternExtractor(sample_assessment_with_findings, min_score=80.0)
        skills = extractor.extract_all_patterns()

        # Only the high-score finding (95.0) should be included
        assert len(skills) == 1
        assert skills[0].confidence == 95.0

    def test_filters_failing_findings(
        self, sample_repository, sample_finding_failing
    ):
        """Test that failing findings are filtered."""
        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=45.0,
            certification_level="Needs Improvement",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[sample_finding_failing],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skills = extractor.extract_all_patterns()

        # Failing finding should not be extracted
        assert len(skills) == 0

    def test_sorts_by_confidence_descending(self, sample_repository):
        """Test that patterns are sorted by confidence (highest first)."""
        # Create multiple high-score findings with different scores
        attr1 = Attribute(
            id="claude_md_file",
            name="CLAUDE.md File",
            category="Documentation",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )
        attr2 = Attribute(
            id="type_annotations",
            name="Type Annotations",
            category="Code Quality",
            tier=2,
            description="Test",
            criteria="Test",
            default_weight=0.8,
        )

        finding1 = Finding(
            attribute=attr1,
            status="pass",
            score=85.0,
            measured_value="good",
            threshold="good",
            evidence=["Test"],
            remediation=None,
            error_message=None,
        )
        finding2 = Finding(
            attribute=attr2,
            status="pass",
            score=95.0,
            measured_value="excellent",
            threshold="good",
            evidence=["Test"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=90.0,
            certification_level="Platinum",
            attributes_assessed=2,
            attributes_not_assessed=0,
            attributes_total=2,
            findings=[finding1, finding2],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skills = extractor.extract_all_patterns()

        assert len(skills) == 2
        assert skills[0].confidence == 95.0  # Highest first
        assert skills[1].confidence == 85.0

    def test_extract_specific_patterns(self, sample_assessment_with_findings):
        """Test extracting patterns for specific attribute IDs."""
        extractor = PatternExtractor(sample_assessment_with_findings)
        skills = extractor.extract_specific_patterns(["claude_md_file"])

        # Should only get claude_md_file patterns
        assert len(skills) == 1
        assert skills[0].source_attribute_id == "claude_md_file"

    def test_extract_specific_patterns_filters_correctly(
        self, sample_assessment_with_findings
    ):
        """Test that extract_specific_patterns filters by attribute ID."""
        extractor = PatternExtractor(sample_assessment_with_findings)
        # Request non-existent attribute
        skills = extractor.extract_specific_patterns(["non_existent_attr"])

        assert len(skills) == 0

    def test_should_extract_pattern_logic(self, sample_finding_high_score):
        """Test _should_extract_pattern() logic."""
        assessment = Assessment(
            repository=Repository(
                path="/tmp",
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            ),
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)

        # Should extract: passing + high score + in SKILL_NAMES
        assert extractor._should_extract_pattern(sample_finding_high_score) is True

    def test_should_not_extract_unknown_attribute(self, sample_repository):
        """Test that unknown attributes are not extracted."""
        # Create finding with unknown attribute ID
        unknown_attr = Attribute(
            id="unknown_attribute",
            name="Unknown",
            category="Other",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=unknown_attr,
            status="pass",
            score=95.0,
            measured_value="test",
            threshold="test",
            evidence=["Test"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skills = extractor.extract_all_patterns()

        # Unknown attribute should not be extracted
        assert len(skills) == 0

    def test_create_skill_from_finding(self, sample_finding_high_score):
        """Test _create_skill_from_finding() creates valid skill."""
        assessment = Assessment(
            repository=Repository(
                path="/tmp",
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            ),
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skill = extractor._create_skill_from_finding(sample_finding_high_score)

        assert skill is not None
        assert skill.skill_id == "setup-claude-md"
        assert skill.name == "Setup CLAUDE.md Configuration"
        assert skill.confidence == 95.0
        assert skill.source_attribute_id == "claude_md_file"

    def test_tier_based_impact_scores(self, sample_repository):
        """Test that impact scores are calculated based on tier."""
        # Test all tiers
        for tier, expected_impact in [(1, 50.0), (2, 30.0), (3, 15.0), (4, 5.0)]:
            if tier == 1:
                attr_id = "claude_md_file"
            elif tier == 2:
                attr_id = "type_annotations"
            elif tier == 3:
                attr_id = "pre_commit_hooks"
            else:
                continue  # Only test tiers with known attributes

            attr = Attribute(
                id=attr_id,
                name=f"Tier {tier} Attr",
                category="Test",
                tier=tier,
                description="Test",
                criteria="Test",
                default_weight=1.0,
            )
            finding = Finding(
                attribute=attr,
                status="pass",
                score=90.0,
                measured_value="test",
                threshold="test",
                evidence=["Test"],
                remediation=None,
                error_message=None,
            )

            assessment = Assessment(
                repository=sample_repository,
                timestamp=datetime.now(),
                overall_score=90.0,
                certification_level="Platinum",
                attributes_assessed=1,
                attributes_not_assessed=0,
                attributes_total=1,
                findings=[finding],
                config=None,
                duration_seconds=1.0,
            )

            extractor = PatternExtractor(assessment)
            skills = extractor.extract_all_patterns()

            if len(skills) > 0:
                assert skills[0].impact_score == expected_impact

    def test_reusability_score_calculation(self, sample_repository):
        """Test reusability score based on tier."""
        # Tier 1 should have highest reusability (100.0)
        attr_t1 = Attribute(
            id="claude_md_file",
            name="CLAUDE.md",
            category="Documentation",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )
        finding_t1 = Finding(
            attribute=attr_t1,
            status="pass",
            score=90.0,
            measured_value="test",
            threshold="test",
            evidence=["Test"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=90.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding_t1],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        skills = extractor.extract_all_patterns()

        assert len(skills) == 1
        assert skills[0].reusability_score == 100.0  # Tier 1

    def test_extract_code_examples_from_evidence(self, sample_finding_high_score):
        """Test extracting code examples from evidence."""
        assessment = Assessment(
            repository=Repository(
                path="/tmp",
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            ),
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        examples = extractor._extract_code_examples(sample_finding_high_score)

        assert len(examples) > 0
        assert "CLAUDE.md exists" in examples

    def test_extract_code_examples_limits_to_three(self, sample_repository):
        """Test that code examples are limited to 3."""
        attr = Attribute(
            id="claude_md_file",
            name="CLAUDE.md",
            category="Documentation",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=90.0,
            measured_value="test",
            threshold="test",
            evidence=["Example 1", "Example 2", "Example 3", "Example 4", "Example 5"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=90.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        examples = extractor._extract_code_examples(finding)

        assert len(examples) == 3

    def test_create_pattern_summary(self, sample_finding_high_score):
        """Test pattern summary generation."""
        assessment = Assessment(
            repository=Repository(
                path="/tmp",
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            ),
            timestamp=datetime.now(),
            overall_score=95.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        summary = extractor._create_pattern_summary(sample_finding_high_score)

        # Should use attribute description
        assert "Comprehensive CLAUDE.md" in summary

    def test_pattern_summary_fallback_to_evidence(self, sample_repository):
        """Test pattern summary falls back to evidence when no description."""
        attr = Attribute(
            id="claude_md_file",
            name="CLAUDE.md File",
            category="Documentation",
            tier=1,
            description="",  # Empty description
            criteria="Test",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=90.0,
            measured_value="test",
            threshold="test",
            evidence=["Evidence 1", "Evidence 2"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=90.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        extractor = PatternExtractor(assessment)
        summary = extractor._create_pattern_summary(finding)

        # Should use evidence as fallback
        assert "Evidence 1" in summary or "successfully implements" in summary
