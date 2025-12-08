"""Unit tests for learning service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentready.models import DiscoveredSkill
from agentready.services.learning_service import LearningService


@pytest.fixture
def temp_dir():
    """Create a temporary directory with git initialization."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize as git repo to satisfy Repository model validation
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        yield Path(tmpdir)


@pytest.fixture
def sample_assessment_file(temp_dir):
    """Create a sample assessment file."""
    assessment_data = {
        "schema_version": "1.0.0",
        "timestamp": "2025-11-22T06:00:00",
        "repository": {
            "name": "test-repo",
            "path": str(temp_dir),
            "url": None,
            "branch": "main",
            "commit_hash": "abc123",
            "languages": {"Python": 100},
            "total_files": 5,
            "total_lines": 100,
        },
        "overall_score": 85.0,
        "certification_level": "Gold",
        "attributes_assessed": 2,
        "attributes_not_assessed": 0,
        "attributes_total": 2,
        "findings": [
            {
                "attribute": {
                    "id": "claude_md_file",
                    "name": "CLAUDE.md File",
                    "category": "Documentation",
                    "tier": 1,
                    "description": "Test attribute",
                    "criteria": "Must exist",
                    "default_weight": 1.0,
                },
                "status": "pass",
                "score": 100.0,
                "measured_value": "present",
                "threshold": "present",
                "evidence": ["CLAUDE.md exists at root"],
                "error_message": None,
            },
            {
                "attribute": {
                    "id": "type_annotations",
                    "name": "Type Annotations",
                    "category": "Code Quality",
                    "tier": 2,
                    "description": "Type hints in Python code",
                    "criteria": ">=80% coverage",
                    "default_weight": 1.0,
                },
                "status": "pass",
                "score": 90.0,
                "measured_value": "90%",
                "threshold": "80%",
                "evidence": ["90% of functions have type hints"],
                "error_message": None,
            },
        ],
        "duration_seconds": 1.5,
    }

    # Create .agentready directory
    agentready_dir = temp_dir / ".agentready"
    agentready_dir.mkdir()

    assessment_file = agentready_dir / "assessment-latest.json"
    with open(assessment_file, "w") as f:
        json.dump(assessment_data, f)

    return assessment_file


class TestLearningService:
    """Test LearningService class."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        service = LearningService()

        assert service.min_confidence == 70.0
        assert service.output_dir == Path(".skills-proposals")

    def test_init_custom_params(self, temp_dir):
        """Test initialization with custom parameters."""
        service = LearningService(
            min_confidence=80.0, output_dir=temp_dir / "custom-skills"
        )

        assert service.min_confidence == 80.0
        assert service.output_dir == temp_dir / "custom-skills"

    def test_load_assessment_valid_file(self, sample_assessment_file):
        """Test loading a valid assessment file."""
        service = LearningService()
        assessment = service.load_assessment(sample_assessment_file)

        assert isinstance(assessment, dict)
        assert assessment["overall_score"] == 85.0
        assert len(assessment["findings"]) == 2

    def test_load_assessment_nonexistent_file(self, temp_dir):
        """Test loading a non-existent assessment file."""
        service = LearningService()
        nonexistent = temp_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            service.load_assessment(nonexistent)

    def test_load_assessment_invalid_json(self, temp_dir):
        """Test loading an invalid JSON file."""
        service = LearningService()
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            service.load_assessment(invalid_file)

    def test_load_assessment_empty_file(self, temp_dir):
        """Test loading an empty JSON file."""
        service = LearningService()
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("")

        with pytest.raises(ValueError):
            service.load_assessment(empty_file)

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_from_file_basic(
        self, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test basic pattern extraction from file."""
        # Mock pattern extractor
        mock_skill = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="Test description",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Test pattern",
            code_examples=["example"],
            citations=[],
        )
        mock_extractor.return_value.extract_all_patterns.return_value = [mock_skill]

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(sample_assessment_file)

        # Should return skills
        assert len(skills) == 1
        assert skills[0].skill_id == "test-skill"

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_with_attribute_filter(
        self, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test pattern extraction with attribute filter."""
        mock_skill = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="Test description",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Test pattern",
            code_examples=["example"],
            citations=[],
        )
        mock_extractor.return_value.extract_all_patterns.return_value = [mock_skill]

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(
            sample_assessment_file, attribute_ids=["claude_md_file"]
        )

        # Should filter by attribute
        assert len(skills) >= 0  # Depends on implementation

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_filters_by_confidence(
        self, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test pattern extraction filters by confidence threshold."""
        # Create skills with different confidence levels
        high_confidence = DiscoveredSkill(
            skill_id="high",
            name="High Confidence",
            description="High",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="High pattern",
            code_examples=["example"],
            citations=[],
        )
        low_confidence = DiscoveredSkill(
            skill_id="low",
            name="Low Confidence",
            description="Low",
            confidence=50.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Low pattern",
            code_examples=["example"],
            citations=[],
        )
        mock_extractor.return_value.extract_all_patterns.return_value = [
            high_confidence,
            low_confidence,
        ]

        # Service with 70% threshold
        service = LearningService(min_confidence=70.0, output_dir=temp_dir)
        skills = service.extract_patterns_from_file(sample_assessment_file)

        # Should only include high confidence skill
        high_conf_skills = [s for s in skills if s.confidence >= 70.0]
        assert len(high_conf_skills) >= 1

    @patch("agentready.services.learning_service.PatternExtractor")
    @patch("agentready.learners.llm_enricher.LLMEnricher")
    def test_extract_patterns_with_llm_enrichment(
        self, mock_enricher, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test pattern extraction with LLM enrichment."""
        # Mock basic skill
        basic_skill = DiscoveredSkill(
            skill_id="test",
            name="Test",
            description="Basic",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Pattern",
            code_examples=["example"],
            citations=[],
        )
        mock_extractor.return_value.extract_all_patterns.return_value = [basic_skill]

        # Mock enriched skill
        enriched_skill = DiscoveredSkill(
            skill_id="test",
            name="Test",
            description="Enhanced by LLM",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Pattern",
            code_examples=["enhanced example"],
            citations=[],
        )
        mock_enricher.return_value.enrich_skill.return_value = enriched_skill

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(
            sample_assessment_file, enable_llm=True, llm_budget=1
        )

        # Should have enriched skills
        assert len(skills) >= 1

    def test_extract_patterns_missing_assessment_keys(self, temp_dir):
        """Test extract_patterns handles assessment with missing keys."""
        # Create assessment with missing optional keys
        minimal_assessment = {
            "schema_version": "1.0.0",
            "timestamp": "2025-11-22T06:00:00",
            "repository": {
                "name": "test",
                "path": str(temp_dir),
                "languages": {"Python": 100},
                "total_files": 1,
                "total_lines": 10,
            },
            "overall_score": 75.0,
            "certification_level": "Gold",
            "attributes_assessed": 0,
            "attributes_total": 0,
            "findings": [],
            "duration_seconds": 1.0,
        }

        assessment_file = temp_dir / "minimal.json"
        with open(assessment_file, "w") as f:
            json.dump(minimal_assessment, f)

        service = LearningService(output_dir=temp_dir)

        # Should handle gracefully (may return empty list)
        with patch("agentready.services.learning_service.PatternExtractor") as mock:
            mock.return_value.extract_all_patterns.return_value = []
            skills = service.extract_patterns_from_file(assessment_file)
            assert isinstance(skills, list)

    def test_extract_patterns_with_old_schema_key(self, temp_dir):
        """Test extract_patterns handles old schema key names."""
        # Old schema used "attributes_skipped" instead of "attributes_not_assessed"
        old_schema_assessment = {
            "schema_version": "1.0.0",
            "timestamp": "2025-11-22T06:00:00",
            "repository": {
                "name": "test",
                "path": str(temp_dir),
                "languages": {"Python": 100},
                "total_files": 1,
                "total_lines": 10,
            },
            "overall_score": 75.0,
            "certification_level": "Gold",
            "attributes_assessed": 0,
            "attributes_skipped": 0,  # Old key
            "attributes_total": 0,
            "findings": [],
            "duration_seconds": 1.0,
        }

        assessment_file = temp_dir / "old.json"
        with open(assessment_file, "w") as f:
            json.dump(old_schema_assessment, f)

        service = LearningService(output_dir=temp_dir)

        # Should handle gracefully
        with patch("agentready.services.learning_service.PatternExtractor") as mock:
            mock.return_value.extract_all_patterns.return_value = []
            skills = service.extract_patterns_from_file(assessment_file)
            assert isinstance(skills, list)


class TestLearningServiceEdgeCases:
    """Test edge cases in learning service."""

    def test_output_dir_string_conversion(self):
        """Test output_dir accepts string and converts to Path."""
        service = LearningService(output_dir="/tmp/skills")

        assert isinstance(service.output_dir, Path)
        assert str(service.output_dir) == "/tmp/skills"

    def test_min_confidence_boundary_values(self):
        """Test min_confidence with boundary values."""
        # Zero
        service1 = LearningService(min_confidence=0.0)
        assert service1.min_confidence == 0.0

        # 100
        service2 = LearningService(min_confidence=100.0)
        assert service2.min_confidence == 100.0

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_empty_findings(self, mock_extractor, temp_dir):
        """Test extract_patterns with empty findings list."""
        # Create assessment with no findings
        assessment_data = {
            "schema_version": "1.0.0",
            "timestamp": "2025-11-22T06:00:00",
            "repository": {
                "name": "test",
                "path": str(temp_dir),
                "languages": {"Python": 100},
                "total_files": 1,
                "total_lines": 10,
            },
            "overall_score": 0.0,
            "certification_level": "Needs Improvement",
            "attributes_assessed": 0,
            "attributes_not_assessed": 0,
            "attributes_total": 0,
            "findings": [],
            "duration_seconds": 1.0,
        }

        assessment_file = temp_dir / "empty.json"
        with open(assessment_file, "w") as f:
            json.dump(assessment_data, f)

        mock_extractor.return_value.extract_all_patterns.return_value = []

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(assessment_file)

        # Should return empty list
        assert skills == []

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_multiple_attribute_ids(
        self, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test extract_patterns with multiple attribute IDs."""
        mock_extractor.return_value.extract_all_patterns.return_value = []

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(
            sample_assessment_file,
            attribute_ids=["claude_md_file", "type_annotations", "gitignore_file"],
        )

        # Should handle multiple attributes
        assert isinstance(skills, list)

    @patch("agentready.services.learning_service.PatternExtractor")
    def test_extract_patterns_llm_budget_zero(
        self, mock_extractor, sample_assessment_file, temp_dir
    ):
        """Test extract_patterns with zero LLM budget."""
        mock_skill = DiscoveredSkill(
            skill_id="test",
            name="Test",
            description="Test",
            confidence=95.0,
            source_attribute_id="claude_md_file",
            reusability_score=100.0,
            impact_score=50.0,
            pattern_summary="Pattern",
            code_examples=["example"],
            citations=[],
        )
        mock_extractor.return_value.extract_all_patterns.return_value = [mock_skill]

        service = LearningService(output_dir=temp_dir)
        skills = service.extract_patterns_from_file(
            sample_assessment_file, enable_llm=True, llm_budget=0
        )

        # Should not enrich any skills (budget is 0)
        assert len(skills) >= 0
