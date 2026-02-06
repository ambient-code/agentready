"""Unit tests for data models."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.citation import Citation
from agentready.models.config import Config
from agentready.models.discovered_skill import DiscoveredSkill
from agentready.models.finding import Finding, Remediation
from agentready.models.fix import (
    CommandFix,
    FileCreationFix,
    FileModificationFix,
    MultiStepFix,
)
from agentready.models.metadata import AssessmentMetadata
from agentready.models.repository import Repository


class TestRepository:
    """Test Repository model."""

    def test_repository_creation(self, tmp_path):
        """Test creating a valid repository."""
        # Create a fake git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 10},
            total_files=15,
            total_lines=500,
        )

        assert repo.name == "test-repo"
        assert repo.total_files == 15
        assert "Python" in repo.languages

    def test_repository_invalid_path(self):
        """Test repository with invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            Repository(
                path=Path("/nonexistent"),
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            )

    def test_repository_to_dict(self, tmp_path):
        """Test repository serialization."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 5},
            total_files=10,
            total_lines=200,
        )

        data = repo.to_dict()
        assert data["name"] == "test"
        assert data["languages"] == {"Python": 5}


class TestAttribute:
    """Test Attribute model."""

    def test_attribute_creation(self):
        """Test creating a valid attribute."""
        attr = Attribute(
            id="test_attr",
            name="Test Attribute",
            category="Testing",
            tier=1,
            description="A test attribute",
            criteria="Must pass test",
            default_weight=0.10,
        )

        assert attr.id == "test_attr"
        assert attr.tier == 1
        assert attr.default_weight == 0.10

    def test_attribute_invalid_tier(self):
        """Test attribute with invalid tier."""
        with pytest.raises(ValueError, match="Tier must be"):
            Attribute(
                id="test",
                name="Test",
                category="Test",
                tier=5,  # Invalid
                description="Test",
                criteria="Test",
                default_weight=0.10,
            )

    def test_attribute_invalid_weight(self):
        """Test attribute with invalid weight."""
        with pytest.raises(ValueError, match="weight must be"):
            Attribute(
                id="test",
                name="Test",
                category="Test",
                tier=1,
                description="Test",
                criteria="Test",
                default_weight=1.5,  # Invalid
            )


class TestFinding:
    """Test Finding model."""

    def test_finding_pass(self):
        """Test creating a passing finding."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.10,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="present",
            threshold="present",
            evidence=["File found"],
            remediation=None,
            error_message=None,
        )

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_finding_fail_with_remediation(self):
        """Test creating a failing finding with remediation."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.10,
        )

        remediation = Remediation(
            summary="Fix the issue",
            steps=["Step 1", "Step 2"],
            tools=["tool1"],
            commands=["command1"],
            examples=["example1"],
            citations=[],
        )

        finding = Finding(
            attribute=attr,
            status="fail",
            score=0.0,
            measured_value="missing",
            threshold="present",
            evidence=["File not found"],
            remediation=remediation,
            error_message=None,
        )

        assert finding.status == "fail"
        assert finding.remediation is not None
        assert len(finding.remediation.steps) == 2

    def test_finding_invalid_status(self):
        """Test finding with invalid status."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.10,
        )

        with pytest.raises(ValueError, match="Status must be"):
            Finding(
                attribute=attr,
                status="invalid",  # Invalid status
                score=50.0,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )


class TestConfig:
    """Test Config model."""

    def test_config_creation(self):
        """Test creating a valid config."""
        config = Config(
            weights={"attr1": 0.5, "attr2": 0.5},
            excluded_attributes=[],
            language_overrides={},
            output_dir=None,
        )

        assert len(config.weights) == 2
        assert config.get_weight("attr1", 0.0) == 0.5

    def test_config_invalid_weights_negative(self):
        """Test config with negative weights (not allowed)."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            Config(
                weights={"attr1": 0.5, "attr2": -0.3},  # Negative weight not allowed
                excluded_attributes=[],
                language_overrides={},
                output_dir=None,
            )

    def test_config_is_excluded(self):
        """Test excluded attribute check."""
        config = Config(
            weights={},
            excluded_attributes=["attr1"],
            language_overrides={},
            output_dir=None,
        )

        assert config.is_excluded("attr1")
        assert not config.is_excluded("attr2")


class TestAssessment:
    """Test Assessment model."""

    def test_assessment_creation(self, tmp_path):
        """Test creating a valid assessment."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc",
            languages={},
            total_files=10,
            total_lines=100,
        )

        # Create dummy findings to match total
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )
        findings = [
            Finding(
                attribute=attr,
                status="pass",
                score=100.0,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )
            for _ in range(25)
        ]

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=75.0,
            certification_level="Gold",
            attributes_assessed=20,
            attributes_not_assessed=5,
            attributes_total=25,
            findings=findings,
            config=None,
            duration_seconds=1.5,
        )

        assert assessment.overall_score == 75.0
        assert assessment.certification_level == "Gold"

    def test_assessment_determine_certification(self):
        """Test certification level determination."""
        assert Assessment.determine_certification_level(95.0) == "Platinum"
        assert Assessment.determine_certification_level(80.0) == "Gold"
        assert Assessment.determine_certification_level(65.0) == "Silver"
        assert Assessment.determine_certification_level(45.0) == "Bronze"
        assert Assessment.determine_certification_level(20.0) == "Needs Improvement"


class TestAssessmentMetadata:
    """Test AssessmentMetadata model."""

    def test_metadata_create(self):
        """Test creating metadata from execution context."""
        timestamp = datetime(2025, 11, 21, 2, 11, 5)
        metadata = AssessmentMetadata.create(
            version="1.0.0",
            research_version="1.2.0",
            timestamp=timestamp,
            command="agentready assess . --verbose",
        )

        assert metadata.agentready_version == "1.0.0"
        assert metadata.command == "agentready assess . --verbose"
        assert "2025" in metadata.assessment_timestamp  # ISO format
        assert "November 21, 2025" in metadata.assessment_timestamp_human
        assert "@" in metadata.executed_by  # Should have user@host format
        assert len(metadata.working_directory) > 0

    def test_metadata_to_dict(self):
        """Test metadata serialization."""
        timestamp = datetime(2025, 11, 21, 2, 11, 5)
        metadata = AssessmentMetadata.create(
            version="1.0.0",
            research_version="1.2.0",
            timestamp=timestamp,
            command="agentready assess .",
        )

        data = metadata.to_dict()
        assert data["agentready_version"] == "1.0.0"
        assert data["command"] == "agentready assess ."
        assert "assessment_timestamp" in data
        assert "assessment_timestamp_human" in data
        assert "executed_by" in data
        assert "working_directory" in data

    def test_metadata_manual_creation(self):
        """Test manually creating metadata with all fields."""
        metadata = AssessmentMetadata(
            agentready_version="1.2.3",
            research_version="1.2.0",
            assessment_timestamp="2025-11-21T02:11:05",
            assessment_timestamp_human="November 21, 2025 at 2:11 AM",
            executed_by="testuser@testhost",
            command="agentready assess /path/to/repo",
            working_directory="/home/user",
        )

        assert metadata.agentready_version == "1.2.3"
        assert metadata.executed_by == "testuser@testhost"
        assert metadata.working_directory == "/home/user"

    def test_assessment_with_metadata(self, tmp_path):
        """Test that Assessment can include metadata."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc",
            languages={},
            total_files=10,
            total_lines=100,
        )

        timestamp = datetime.now()
        metadata = AssessmentMetadata.create(
            version="1.0.0",
            research_version="1.2.0",
            timestamp=timestamp,
            command="agentready assess .",
        )

        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )
        findings = [
            Finding(
                attribute=attr,
                status="pass",
                score=100.0,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )
            for _ in range(25)
        ]

        assessment = Assessment(
            repository=repo,
            timestamp=timestamp,
            overall_score=75.0,
            certification_level="Gold",
            attributes_assessed=25,
            attributes_not_assessed=0,
            attributes_total=25,
            findings=findings,
            config=None,
            duration_seconds=1.5,
            metadata=metadata,
        )

        assert assessment.metadata is not None
        assert assessment.metadata.agentready_version == "1.0.0"

        # Test serialization includes metadata
        data = assessment.to_dict()
        assert data["metadata"] is not None
        assert data["metadata"]["agentready_version"] == "1.0.0"


class TestDiscoveredSkill:
    """Test DiscoveredSkill model."""

    def test_valid_construction(self):
        """Test creating a valid DiscoveredSkill."""
        skill = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="Test description",
            confidence=85.0,
            source_attribute_id="test_attr",
            reusability_score=90.0,
            impact_score=50.0,
            pattern_summary="Test pattern",
        )

        assert skill.skill_id == "test-skill"
        assert skill.name == "Test Skill"
        assert skill.confidence == 85.0
        assert skill.reusability_score == 90.0
        assert skill.impact_score == 50.0
        assert skill.code_examples == []
        assert skill.citations == []

    def test_with_code_examples_and_citations(self):
        """Test DiscoveredSkill with optional fields."""
        citation = Citation(
            source="Test Source",
            title="Test Title",
            url="https://example.com",
            relevance="Test relevance",
        )

        skill = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="Test description",
            confidence=85.0,
            source_attribute_id="test_attr",
            reusability_score=90.0,
            impact_score=50.0,
            pattern_summary="Test pattern",
            code_examples=["example1", "example2"],
            citations=[citation],
        )

        assert len(skill.code_examples) == 2
        assert len(skill.citations) == 1

    @pytest.mark.parametrize(
        "field,value,error_match",
        [
            ("skill_id", "", "must be non-empty"),
            ("skill_id", "Invalid ID!", "must be lowercase"),
            ("skill_id", "Test Skill", "must be lowercase"),
            ("skill_id", "test skill", "must be lowercase"),
            ("name", "", "must be non-empty"),
            ("description", "", "must be non-empty"),
            ("confidence", -1.0, "must be in range"),
            ("confidence", 101.0, "must be in range"),
            ("reusability_score", -1.0, "must be in range"),
            ("reusability_score", 150.0, "must be in range"),
            ("impact_score", -1.0, "must be in range"),
            ("impact_score", 150.0, "must be in range"),
            ("source_attribute_id", "", "must be non-empty"),
            ("pattern_summary", "", "must be non-empty"),
        ],
    )
    def test_validation_errors(self, field, value, error_match):
        """Test DiscoveredSkill validation catches invalid values."""
        base_data = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "Test description",
            "confidence": 85.0,
            "source_attribute_id": "test_attr",
            "reusability_score": 90.0,
            "impact_score": 50.0,
            "pattern_summary": "Test pattern",
        }
        base_data[field] = value

        with pytest.raises(ValueError, match=error_match):
            DiscoveredSkill(**base_data)

    def test_description_too_long(self):
        """Test DiscoveredSkill validation for description length."""
        with pytest.raises(ValueError, match="too long"):
            DiscoveredSkill(
                skill_id="test-skill",
                name="Test Skill",
                description="x" * 1025,  # Over 1024 chars
                confidence=85.0,
                source_attribute_id="test_attr",
                reusability_score=90.0,
                impact_score=50.0,
                pattern_summary="Test pattern",
            )

    def test_to_dict(self):
        """Test DiscoveredSkill serialization."""
        citation = Citation(
            source="Test Source",
            title="Test Title",
            url="https://example.com",
            relevance="Test relevance",
        )

        skill = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="Test description",
            confidence=85.0,
            source_attribute_id="test_attr",
            reusability_score=90.0,
            impact_score=50.0,
            pattern_summary="Test pattern",
            code_examples=["example1"],
            citations=[citation],
        )

        data = skill.to_dict()

        assert data["skill_id"] == "test-skill"
        assert data["name"] == "Test Skill"
        assert data["confidence"] == 85.0
        assert data["reusability_score"] == 90.0
        assert data["impact_score"] == 50.0
        assert "code_examples" in data
        assert len(data["code_examples"]) == 1
        assert "citations" in data
        assert len(data["citations"]) == 1

    def test_skill_id_format_valid(self):
        """Test valid skill_id formats."""
        # lowercase-hyphen format
        skill = DiscoveredSkill(
            skill_id="setup-claude-md",
            name="Test",
            description="Test",
            confidence=85.0,
            source_attribute_id="test",
            reusability_score=90.0,
            impact_score=50.0,
            pattern_summary="Test",
        )
        assert skill.skill_id == "setup-claude-md"

        # lowercase-underscore format
        skill2 = DiscoveredSkill(
            skill_id="setup_claude_md",
            name="Test",
            description="Test",
            confidence=85.0,
            source_attribute_id="test",
            reusability_score=90.0,
            impact_score=50.0,
            pattern_summary="Test",
        )
        assert skill2.skill_id == "setup_claude_md"


class TestFixModels:
    """Test Fix models."""

    def test_file_creation_fix_construction(self, tmp_path):
        """Test creating a FileCreationFix."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="Test content",
            repository_path=tmp_path,
        )

        assert fix.attribute_id == "test_attr"
        assert fix.description == "Create test file"
        assert fix.points_gained == 10.0
        assert fix.file_path == Path("test.txt")
        assert fix.content == "Test content"

    def test_file_creation_fix_apply(self, tmp_path):
        """Test FileCreationFix.apply() creates file."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="Test content",
            repository_path=tmp_path,
        )

        result = fix.apply(dry_run=False)
        assert result is True

        target_file = tmp_path / "test.txt"
        assert target_file.exists()
        assert target_file.read_text() == "Test content"

    def test_file_creation_fix_dry_run(self, tmp_path):
        """Test FileCreationFix.apply() with dry_run."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="Test content",
            repository_path=tmp_path,
        )

        result = fix.apply(dry_run=True)
        assert result is True

        target_file = tmp_path / "test.txt"
        assert not target_file.exists()

    def test_file_creation_fix_existing_file(self, tmp_path):
        """Test FileCreationFix fails if file exists."""
        target_file = tmp_path / "test.txt"
        target_file.write_text("Existing content")

        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="Test content",
            repository_path=tmp_path,
        )

        result = fix.apply(dry_run=False)
        assert result is False

    def test_file_creation_fix_preview(self, tmp_path):
        """Test FileCreationFix.preview()."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="Test content",
            repository_path=tmp_path,
        )

        preview = fix.preview()
        assert "CREATE" in preview
        assert "test.txt" in preview

    def test_file_modification_fix_construction(self, tmp_path):
        """Test creating a FileModificationFix."""
        fix = FileModificationFix(
            attribute_id="test_attr",
            description="Modify test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            additions=["line1", "line2"],
            repository_path=tmp_path,
            append=True,
        )

        assert fix.attribute_id == "test_attr"
        assert len(fix.additions) == 2
        assert fix.append is True

    def test_file_modification_fix_apply_append(self, tmp_path):
        """Test FileModificationFix.apply() with append mode."""
        target_file = tmp_path / "test.txt"
        target_file.write_text("Existing content\n")

        fix = FileModificationFix(
            attribute_id="test_attr",
            description="Modify test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            additions=["line1", "line2"],
            repository_path=tmp_path,
            append=True,
        )

        result = fix.apply(dry_run=False)
        assert result is True

        content = target_file.read_text()
        assert "Existing content" in content
        assert "line1" in content
        assert "line2" in content

    def test_file_modification_fix_missing_file(self, tmp_path):
        """Test FileModificationFix fails if file doesn't exist."""
        fix = FileModificationFix(
            attribute_id="test_attr",
            description="Modify test file",
            points_gained=10.0,
            file_path=Path("nonexistent.txt"),
            additions=["line1"],
            repository_path=tmp_path,
        )

        result = fix.apply(dry_run=False)
        assert result is False

    def test_file_modification_fix_preview(self, tmp_path):
        """Test FileModificationFix.preview()."""
        fix = FileModificationFix(
            attribute_id="test_attr",
            description="Modify test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            additions=["line1", "line2"],
            repository_path=tmp_path,
        )

        preview = fix.preview()
        assert "MODIFY" in preview
        assert "test.txt" in preview
        assert "+2" in preview

    def test_command_fix_construction(self, tmp_path):
        """Test creating a CommandFix."""
        fix = CommandFix(
            attribute_id="test_attr",
            description="Run test command",
            points_gained=10.0,
            command="echo test",
            working_dir=None,
            repository_path=tmp_path,
        )

        assert fix.attribute_id == "test_attr"
        assert fix.command == "echo test"
        assert fix.working_dir is None

    def test_command_fix_preview(self, tmp_path):
        """Test CommandFix.preview()."""
        fix = CommandFix(
            attribute_id="test_attr",
            description="Run test command",
            points_gained=10.0,
            command="echo test",
            working_dir=None,
            repository_path=tmp_path,
        )

        preview = fix.preview()
        assert "RUN" in preview
        assert "echo test" in preview

    def test_command_fix_capture_output_default_true(self, tmp_path):
        """Test that CommandFix defaults to capture_output=True."""
        fix = CommandFix(
            attribute_id="test_attr",
            description="Run test command",
            points_gained=10.0,
            command="echo test",
            working_dir=None,
            repository_path=tmp_path,
        )

        assert fix.capture_output is True

    def test_command_fix_apply_passes_capture_output_false_to_subprocess(self, tmp_path):
        """Test CommandFix.apply() passes capture_output=False to subprocess.run."""
        fix = CommandFix(
            attribute_id="test_attr",
            description="Run test command",
            points_gained=10.0,
            command="echo hello",
            working_dir=None,
            repository_path=tmp_path,
            capture_output=False,
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = None
            result = fix.apply(dry_run=False)

        assert result is True
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is False

    def test_command_fix_apply_passes_capture_output_true_to_subprocess(self, tmp_path):
        """Test CommandFix.apply() passes capture_output=True (default) to subprocess.run."""
        fix = CommandFix(
            attribute_id="test_attr",
            description="Run test command",
            points_gained=10.0,
            command="echo hello",
            working_dir=None,
            repository_path=tmp_path,
            # capture_output defaults to True
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = None
            result = fix.apply(dry_run=False)

        assert result is True
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is True

    def test_multi_step_fix_construction(self, tmp_path):
        """Test creating a MultiStepFix."""
        fix1 = FileCreationFix(
            attribute_id="test",
            description="Create file",
            points_gained=5.0,
            file_path=Path("test.txt"),
            content="Test",
            repository_path=tmp_path,
        )

        fix2 = CommandFix(
            attribute_id="test",
            description="Run command",
            points_gained=5.0,
            command="echo test",
            working_dir=None,
            repository_path=tmp_path,
        )

        multi_fix = MultiStepFix(
            attribute_id="test_attr",
            description="Multi-step fix",
            points_gained=10.0,
            steps=[fix1, fix2],
        )

        assert multi_fix.attribute_id == "test_attr"
        assert len(multi_fix.steps) == 2

    def test_multi_step_fix_apply(self, tmp_path):
        """Test MultiStepFix.apply() executes all steps."""
        fix1 = FileCreationFix(
            attribute_id="test",
            description="Create file",
            points_gained=5.0,
            file_path=Path("test.txt"),
            content="Test",
            repository_path=tmp_path,
        )

        fix2 = FileCreationFix(
            attribute_id="test",
            description="Create file",
            points_gained=5.0,
            file_path=Path("test2.txt"),
            content="Test2",
            repository_path=tmp_path,
        )

        multi_fix = MultiStepFix(
            attribute_id="test_attr",
            description="Multi-step fix",
            points_gained=10.0,
            steps=[fix1, fix2],
        )

        result = multi_fix.apply(dry_run=False)
        assert result is True

        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "test2.txt").exists()

    def test_multi_step_fix_preview(self, tmp_path):
        """Test MultiStepFix.preview()."""
        fix1 = FileCreationFix(
            attribute_id="test",
            description="Create file",
            points_gained=5.0,
            file_path=Path("test.txt"),
            content="Test",
            repository_path=tmp_path,
        )

        fix2 = CommandFix(
            attribute_id="test",
            description="Run command",
            points_gained=5.0,
            command="echo test",
            working_dir=None,
            repository_path=tmp_path,
        )

        multi_fix = MultiStepFix(
            attribute_id="test_attr",
            description="Multi-step fix",
            points_gained=10.0,
            steps=[fix1, fix2],
        )

        preview = multi_fix.preview()
        assert "MULTI-STEP" in preview
        assert "2 steps" in preview
        assert "CREATE" in preview
        assert "RUN" in preview


class TestFindingFactories:
    """Test Finding factory methods."""

    def test_finding_not_applicable_factory(self):
        """Test Finding.not_applicable() factory method."""
        attr = Attribute(
            id="test_attr",
            name="Test",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding.not_applicable(attr, reason="Not a Python project")

        assert finding.status == "not_applicable"
        assert finding.score is None
        assert finding.measured_value is None
        assert finding.threshold is None
        assert "Not a Python project" in finding.evidence
        assert finding.remediation is None
        assert finding.error_message is None

    def test_finding_not_applicable_no_reason(self):
        """Test Finding.not_applicable() without reason."""
        attr = Attribute(
            id="test_attr",
            name="Test",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding.not_applicable(attr)

        assert finding.status == "not_applicable"
        assert finding.evidence == []

    def test_finding_skipped_factory_with_remediation(self):
        """Test Finding.skipped() factory method with remediation."""
        attr = Attribute(
            id="test_attr",
            name="Test",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding.skipped(
            attr, reason="Missing pytest", remediation="Install pytest with pip"
        )

        assert finding.status == "skipped"
        assert finding.score is None
        assert "Missing pytest" in finding.evidence
        assert finding.remediation is not None
        assert finding.remediation.summary == "Install pytest with pip"
        assert finding.error_message is None

    def test_finding_skipped_factory_without_remediation(self):
        """Test Finding.skipped() factory method without remediation."""
        attr = Attribute(
            id="test_attr",
            name="Test",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding.skipped(attr, reason="Missing tool")

        assert finding.status == "skipped"
        assert finding.remediation is None

    def test_finding_error_factory(self):
        """Test Finding.error() factory method."""
        attr = Attribute(
            id="test_attr",
            name="Test",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding.error(attr, reason="Unexpected exception occurred")

        assert finding.status == "error"
        assert finding.score is None
        assert finding.measured_value is None
        assert finding.threshold is None
        assert finding.evidence == []
        assert finding.remediation is None
        assert finding.error_message == "Unexpected exception occurred"


class TestFindingValidation:
    """Test Finding validation beyond existing tests."""

    def test_finding_pass_requires_score(self):
        """Test Finding with pass status requires score."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        with pytest.raises(ValueError, match="Score required"):
            Finding(
                attribute=attr,
                status="pass",
                score=None,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )

    def test_finding_fail_requires_score(self):
        """Test Finding with fail status requires score."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        with pytest.raises(ValueError, match="Score required"):
            Finding(
                attribute=attr,
                status="fail",
                score=None,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )

    def test_finding_score_out_of_range(self):
        """Test Finding validation for score range."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        with pytest.raises(ValueError, match="must be in range"):
            Finding(
                attribute=attr,
                status="pass",
                score=150.0,
                measured_value="test",
                threshold="test",
                evidence=[],
                remediation=None,
                error_message=None,
            )

    def test_finding_error_requires_message(self):
        """Test Finding with error status requires error_message."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        with pytest.raises(ValueError, match="Error message required"):
            Finding(
                attribute=attr,
                status="error",
                score=None,
                measured_value=None,
                threshold=None,
                evidence=[],
                remediation=None,
                error_message=None,
            )

    def test_finding_to_dict_with_remediation(self):
        """Test Finding.to_dict() with remediation."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        remediation = Remediation(
            summary="Fix it",
            steps=["Step 1"],
            tools=["tool1"],
            commands=["cmd1"],
            examples=["ex1"],
            citations=[],
        )

        finding = Finding(
            attribute=attr,
            status="fail",
            score=0.0,
            measured_value="missing",
            threshold="present",
            evidence=["File not found"],
            remediation=remediation,
            error_message=None,
        )

        data = finding.to_dict()

        assert data["status"] == "fail"
        assert data["score"] == 0.0
        assert data["remediation"] is not None
        assert data["remediation"]["summary"] == "Fix it"

    def test_finding_to_dict_without_remediation(self):
        """Test Finding.to_dict() without remediation."""
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.04,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="present",
            threshold="present",
            evidence=["File found"],
            remediation=None,
            error_message=None,
        )

        data = finding.to_dict()

        assert data["status"] == "pass"
        assert data["score"] == 100.0
        assert data["remediation"] is None


class TestRemediationValidation:
    """Test Remediation validation."""

    def test_remediation_empty_summary(self):
        """Test Remediation validation for empty summary."""
        with pytest.raises(ValueError, match="summary must be non-empty"):
            Remediation(
                summary="",
                steps=["Step 1"],
                tools=[],
                commands=[],
                examples=[],
                citations=[],
            )

    def test_remediation_empty_steps(self):
        """Test Remediation validation for empty steps."""
        with pytest.raises(ValueError, match="at least one step"):
            Remediation(
                summary="Fix it",
                steps=[],
                tools=[],
                commands=[],
                examples=[],
                citations=[],
            )
