"""Unit tests for fixer service."""

from datetime import datetime
from pathlib import Path

import pytest

from agentready.fixers.base import BaseFixer
from agentready.models import Assessment, Attribute, Finding, Repository
from agentready.models.fix import (
    CommandFix,
    FileCreationFix,
    FileModificationFix,
    MultiStepFix,
)
from agentready.services.fixer_service import FixerService, FixPlan


class MockFixer(BaseFixer):
    """Mock fixer for testing."""

    def __init__(self, attr_id: str, can_fix_result: bool = True):
        self._attr_id = attr_id
        self._can_fix_result = can_fix_result

    @property
    def attribute_id(self) -> str:
        return self._attr_id

    def can_fix(self, finding: Finding) -> bool:
        return self._can_fix_result

    def generate_fix(self, repository: Repository, finding: Finding):
        if not self.can_fix(finding):
            return None

        return FileCreationFix(
            attribute_id=self._attr_id,
            description=f"Fix for {self._attr_id}",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="test content",
            repository_path=repository.path,
        )


@pytest.fixture
def sample_repository(tmp_path):
    """Create test repository."""
    return Repository(
        path=tmp_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 100},
        total_files=10,
        total_lines=500,
    )


@pytest.fixture
def sample_attribute():
    """Create test attribute."""
    return Attribute(
        id="test_attr",
        name="Test Attribute",
        category="Testing",
        tier=1,
        description="Test description",
        criteria="Test criteria",
        default_weight=0.1,
    )


@pytest.fixture
def failing_finding(sample_attribute):
    """Create failing finding."""
    return Finding(
        attribute=sample_attribute,
        status="fail",
        score=0.0,
        measured_value="missing",
        threshold="present",
        evidence=["Test is missing"],
        remediation=None,
        error_message=None,
    )


@pytest.fixture
def passing_finding(sample_attribute):
    """Create passing finding."""
    return Finding(
        attribute=sample_attribute,
        status="pass",
        score=100.0,
        measured_value="present",
        threshold="present",
        evidence=["Test exists"],
        remediation=None,
        error_message=None,
    )


@pytest.fixture
def sample_assessment(sample_repository, failing_finding):
    """Create assessment with failing finding."""
    return Assessment(
        repository=sample_repository,
        timestamp=datetime.now(),
        overall_score=50.0,
        certification_level="Needs Improvement",
        attributes_assessed=1,
        attributes_not_assessed=0,
        attributes_total=1,
        findings=[failing_finding],
        config=None,
        duration_seconds=1.0,
    )


class TestFixerService:
    """Test FixerService class."""

    def test_init_with_default_fixers(self):
        """Test initialization with default fixers."""
        service = FixerService()
        assert len(service.fixers) > 0
        # Should have CLAUDEmdFixer, GitignoreFixer, PrecommitHooksFixer
        assert len(service.fixers) == 3

    def test_generate_fix_plan_with_failing_finding(
        self, sample_assessment, sample_repository
    ):
        """Test generating fix plan for failing finding."""
        service = FixerService()
        # Add a mock fixer that can fix our test attribute
        mock_fixer = MockFixer("test_attr", can_fix_result=True)
        service.fixers.append(mock_fixer)

        plan = service.generate_fix_plan(sample_assessment, sample_repository)

        assert isinstance(plan, FixPlan)
        assert plan.current_score == 50.0
        assert plan.projected_score > plan.current_score
        assert plan.points_gained > 0
        assert len(plan.fixes) == 1

    def test_generate_fix_plan_no_failing_findings(self, sample_repository):
        """Test generating fix plan with no failing findings."""
        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=100.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            config=None,
            duration_seconds=1.0,
        )

        service = FixerService()
        plan = service.generate_fix_plan(assessment, sample_repository)

        assert len(plan.fixes) == 0
        assert plan.points_gained == 0
        assert plan.projected_score == plan.current_score

    def test_generate_fix_plan_filters_by_attribute_ids(
        self, sample_repository, sample_attribute
    ):
        """Test generating fix plan filtered by attribute IDs."""
        # Create two failing findings
        finding1 = Finding(
            attribute=sample_attribute,
            status="fail",
            score=0.0,
            measured_value="missing",
            threshold="present",
            evidence=["Missing"],
            remediation=None,
            error_message=None,
        )

        attr2 = Attribute(
            id="other_attr",
            name="Other Attribute",
            category="Testing",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=0.1,
        )
        finding2 = Finding(
            attribute=attr2,
            status="fail",
            score=0.0,
            measured_value="missing",
            threshold="present",
            evidence=["Missing"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=50.0,
            certification_level="Needs Improvement",
            attributes_assessed=2,
            attributes_not_assessed=0,
            attributes_total=2,
            findings=[finding1, finding2],
            config=None,
            duration_seconds=1.0,
        )

        service = FixerService()
        # Add fixers for both attributes
        service.fixers.append(MockFixer("test_attr"))
        service.fixers.append(MockFixer("other_attr"))

        # Generate plan for only test_attr
        plan = service.generate_fix_plan(
            assessment, sample_repository, attribute_ids=["test_attr"]
        )

        # Should only have fix for test_attr
        assert len(plan.fixes) == 1
        assert plan.fixes[0].attribute_id == "test_attr"

    def test_generate_fix_plan_score_projection(
        self, sample_assessment, sample_repository
    ):
        """Test score projection calculation."""
        service = FixerService()
        mock_fixer = MockFixer("test_attr")
        service.fixers.append(mock_fixer)

        plan = service.generate_fix_plan(sample_assessment, sample_repository)

        # Projected score should be current + points gained
        expected_projected = min(100.0, sample_assessment.overall_score + 10.0)
        assert plan.projected_score == expected_projected
        assert plan.points_gained == 10.0

    def test_generate_fix_plan_caps_at_100(self, sample_repository, sample_attribute):
        """Test that projected score is capped at 100."""
        finding = Finding(
            attribute=sample_attribute,
            status="fail",
            score=0.0,
            measured_value="missing",
            threshold="present",
            evidence=["Missing"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=sample_repository,
            timestamp=datetime.now(),
            overall_score=95.0,  # High score
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        service = FixerService()
        mock_fixer = MockFixer("test_attr")
        service.fixers.append(mock_fixer)

        plan = service.generate_fix_plan(assessment, sample_repository)

        # Should be capped at 100
        assert plan.projected_score == 100.0

    def test_apply_fixes_success(self, tmp_path):
        """Test applying fixes successfully."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="test content",
            repository_path=tmp_path,
        )

        service = FixerService()
        results = service.apply_fixes([fix])

        assert results["succeeded"] == 1
        assert results["failed"] == 0
        assert len(results["failures"]) == 0
        assert (tmp_path / "test.txt").exists()

    def test_apply_fixes_dry_run(self, tmp_path):
        """Test applying fixes in dry run mode."""
        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create test file",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="test content",
            repository_path=tmp_path,
        )

        service = FixerService()
        results = service.apply_fixes([fix], dry_run=True)

        assert results["succeeded"] == 1
        assert results["failed"] == 0
        # File should NOT exist in dry run
        assert not (tmp_path / "test.txt").exists()

    def test_apply_fixes_failure(self, tmp_path):
        """Test applying fixes that fail."""
        # Create fix that will fail (file already exists)
        test_file = tmp_path / "existing.txt"
        test_file.write_text("existing content")

        fix = FileCreationFix(
            attribute_id="test_attr",
            description="Create existing file",
            points_gained=10.0,
            file_path=Path("existing.txt"),
            content="new content",
            repository_path=tmp_path,
        )

        service = FixerService()
        results = service.apply_fixes([fix])

        assert results["succeeded"] == 0
        assert results["failed"] == 1
        assert len(results["failures"]) == 1
        assert "Create existing file" in results["failures"][0]

    def test_apply_fixes_exception_handling(self, tmp_path):
        """Test that exceptions during fix application are handled."""

        class FailingFix(FileCreationFix):
            def apply(self, dry_run=False):
                raise RuntimeError("Intentional failure")

        fix = FailingFix(
            attribute_id="test_attr",
            description="Failing fix",
            points_gained=10.0,
            file_path=Path("test.txt"),
            content="content",
            repository_path=tmp_path,
        )

        service = FixerService()
        results = service.apply_fixes([fix])

        assert results["succeeded"] == 0
        assert results["failed"] == 1
        assert len(results["failures"]) == 1
        assert "Intentional failure" in results["failures"][0]

    def test_apply_multiple_fixes(self, tmp_path):
        """Test applying multiple fixes."""
        fixes = [
            FileCreationFix(
                attribute_id="test_attr_1",
                description="Create file 1",
                points_gained=5.0,
                file_path=Path("file1.txt"),
                content="content 1",
                repository_path=tmp_path,
            ),
            FileCreationFix(
                attribute_id="test_attr_2",
                description="Create file 2",
                points_gained=5.0,
                file_path=Path("file2.txt"),
                content="content 2",
                repository_path=tmp_path,
            ),
        ]

        service = FixerService()
        results = service.apply_fixes(fixes)

        assert results["succeeded"] == 2
        assert results["failed"] == 0
        assert (tmp_path / "file1.txt").exists()
        assert (tmp_path / "file2.txt").exists()

    def test_apply_mixed_success_and_failure(self, tmp_path):
        """Test applying fixes with mixed success and failure."""
        # Create one file that already exists
        (tmp_path / "existing.txt").write_text("existing")

        fixes = [
            FileCreationFix(
                attribute_id="test_attr_1",
                description="Create new file",
                points_gained=5.0,
                file_path=Path("new.txt"),
                content="content",
                repository_path=tmp_path,
            ),
            FileCreationFix(
                attribute_id="test_attr_2",
                description="Create existing file",
                points_gained=5.0,
                file_path=Path("existing.txt"),
                content="content",
                repository_path=tmp_path,
            ),
        ]

        service = FixerService()
        results = service.apply_fixes(fixes)

        assert results["succeeded"] == 1
        assert results["failed"] == 1
        assert len(results["failures"]) == 1

    def test_find_fixer_existing(self):
        """Test finding fixer for existing attribute."""
        service = FixerService()
        mock_fixer = MockFixer("test_attr")
        service.fixers.append(mock_fixer)

        found = service._find_fixer("test_attr")
        assert found is mock_fixer

    def test_find_fixer_nonexistent(self):
        """Test finding fixer for non-existent attribute."""
        service = FixerService()
        found = service._find_fixer("nonexistent_attr")
        assert found is None

    def test_generate_fix_plan_with_non_fixable_finding(
        self, sample_assessment, sample_repository
    ):
        """Test generating fix plan when fixer can't fix the finding."""
        service = FixerService()
        # Add a mock fixer that returns False for can_fix
        mock_fixer = MockFixer("test_attr", can_fix_result=False)
        service.fixers.append(mock_fixer)

        plan = service.generate_fix_plan(sample_assessment, sample_repository)

        # Should have no fixes since can_fix returns False
        assert len(plan.fixes) == 0
        assert plan.points_gained == 0

    def test_generate_fix_plan_with_no_matching_fixer(
        self, sample_assessment, sample_repository
    ):
        """Test generating fix plan when no fixer matches the attribute."""
        service = FixerService()
        # Don't add any fixer for test_attr

        plan = service.generate_fix_plan(sample_assessment, sample_repository)

        # Should have no fixes since no fixer is registered
        assert len(plan.fixes) == 0
        assert plan.points_gained == 0


class TestFixPlan:
    """Test FixPlan dataclass."""

    def test_fix_plan_creation(self):
        """Test creating a FixPlan."""
        fixes = []
        plan = FixPlan(
            fixes=fixes,
            current_score=60.0,
            projected_score=75.0,
            points_gained=15.0,
        )

        assert plan.fixes == fixes
        assert plan.current_score == 60.0
        assert plan.projected_score == 75.0
        assert plan.points_gained == 15.0

    def test_fix_plan_with_multiple_fixes(self, tmp_path):
        """Test FixPlan with multiple fixes."""
        fixes = [
            FileCreationFix(
                attribute_id="attr1",
                description="Fix 1",
                points_gained=5.0,
                file_path=Path("file1.txt"),
                content="content1",
                repository_path=tmp_path,
            ),
            FileCreationFix(
                attribute_id="attr2",
                description="Fix 2",
                points_gained=10.0,
                file_path=Path("file2.txt"),
                content="content2",
                repository_path=tmp_path,
            ),
        ]

        total_points = sum(f.points_gained for f in fixes)
        plan = FixPlan(
            fixes=fixes,
            current_score=50.0,
            projected_score=50.0 + total_points,
            points_gained=total_points,
        )

        assert len(plan.fixes) == 2
        assert plan.points_gained == 15.0
        assert plan.projected_score == 65.0
