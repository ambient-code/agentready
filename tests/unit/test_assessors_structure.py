"""Tests for structure assessors."""

from agentready.assessors.structure import StandardLayoutAssessor
from agentready.models.repository import Repository


class TestStandardLayoutAssessor:
    """Test StandardLayoutAssessor."""

    def test_recognizes_tests_directory(self, tmp_path):
        """Test that assessor recognizes tests/ directory."""
        # Create repository with tests/ directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "2/2" in finding.measured_value

    def test_recognizes_test_directory(self, tmp_path):
        """Test that assessor recognizes test/ directory (not just tests/)."""
        # Create repository with test/ directory only
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "test").mkdir()  # Note: singular 'test', not 'tests'

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"JavaScript": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Should pass - test/ is valid
        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "2/2" in finding.measured_value

    def test_fails_without_standard_directories(self, tmp_path):
        """Test that assessor fails when standard directories missing."""
        # Create repository with no standard directories
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "lib").mkdir()  # Non-standard directory

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None

    def test_partial_score_with_only_src(self, tmp_path):
        """Test partial score when only src/ exists."""
        # Create repository with only src/
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "src").mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Should fail but have partial score
        assert finding.status == "fail"  # Less than 75%
        assert 0.0 < finding.score < 100.0
        assert "1/2" in finding.measured_value

    def test_evidence_shows_both_test_variants(self, tmp_path):
        """Test that evidence shows check for both tests/ and test/."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "test").mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Evidence should mention tests/
        evidence_str = " ".join(finding.evidence)
        assert "tests/" in evidence_str or "test/" in evidence_str
        assert "✓" in evidence_str  # Should show checkmark for test dir
