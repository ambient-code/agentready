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

    # === Tests for issue #246: Project-named directory support ===

    def test_recognizes_project_named_directory_with_pyproject(self, tmp_path):
        """Test that assessor recognizes project-named directory from pyproject.toml.

        Fix for #246: Project-named directories like pandas/pandas/ should pass.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create project-named directory with __init__.py
        (tmp_path / "mypackage").mkdir()
        (tmp_path / "mypackage" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        # Create pyproject.toml with project name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "mypackage"\n')

        repo = Repository(
            path=tmp_path,
            name="mypackage",
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
        assert "project-named" in " ".join(finding.evidence)

    def test_recognizes_project_named_directory_with_hyphens(self, tmp_path):
        """Test that hyphens in package name are converted to underscores.

        Fix for #246: my-package in pyproject.toml should match my_package/ dir.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create directory with underscores (Python convention)
        (tmp_path / "my_package").mkdir()
        (tmp_path / "my_package" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        # pyproject.toml uses hyphens (common convention)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-package"\n')

        repo = Repository(
            path=tmp_path,
            name="my-package",
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

    def test_recognizes_project_named_directory_without_pyproject(self, tmp_path):
        """Test fallback detection of project-named directory without pyproject.toml.

        Fix for #246: Should detect any directory with __init__.py not in blocklist.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create a package directory without pyproject.toml
        (tmp_path / "coolpackage").mkdir()
        (tmp_path / "coolpackage" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        repo = Repository(
            path=tmp_path,
            name="coolpackage",
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

    def test_blocklist_excludes_non_source_directories(self, tmp_path):
        """Test that directories in blocklist are not considered source dirs.

        Fix for #246: utils/, scripts/, etc. should not count as source directories.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create directories that are in the blocklist
        (tmp_path / "utils").mkdir()
        (tmp_path / "utils" / "__init__.py").touch()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        repo = Repository(
            path=tmp_path,
            name="some-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Should fail - utils/ and scripts/ are in blocklist, not valid source dirs
        assert finding.status == "fail"
        assert finding.score < 100.0

    def test_src_takes_precedence_over_project_named(self, tmp_path):
        """Test that src/ is preferred over project-named directory.

        Fix for #246: If both exist, src/ should be reported.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create both src/ and project-named directory
        (tmp_path / "src").mkdir()
        (tmp_path / "mypackage").mkdir()
        (tmp_path / "mypackage" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        repo = Repository(
            path=tmp_path,
            name="mypackage",
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
        # Evidence should show src/, not project-named
        evidence_str = " ".join(finding.evidence)
        assert "src/: ✓" in evidence_str

    # === Tests for issue #305: Test-only repository support ===

    def test_test_only_repo_returns_not_applicable(self, tmp_path):
        """Test that test-only repositories return not_applicable.

        Fix for #305: Repos with only tests/ and no source should not fail.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create test-only structure
        (tmp_path / "tests").mkdir()
        (tmp_path / "conftest.py").touch()

        repo = Repository(
            path=tmp_path,
            name="opendatahub-tests",  # Name suggests test repo
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"
        # The reason is stored in evidence, not error_message
        evidence_str = " ".join(finding.evidence) if finding.evidence else ""
        assert "Test-only repository" in evidence_str

    def test_test_only_repo_detected_by_name(self, tmp_path):
        """Test that repos with 'test' in name are detected as test-only.

        Fix for #305: Repo name containing 'test' indicates test-only repo.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        (tmp_path / "tests").mkdir()
        # No conftest.py, but name suggests tests

        repo = Repository(
            path=tmp_path,
            name="my-project-tests",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_test_only_repo_detected_by_pytest_ini(self, tmp_path):
        """Test that repos with pytest.ini are detected as test-only.

        Fix for #305: pytest.ini indicates a test-focused repository.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        (tmp_path / "tests").mkdir()
        (tmp_path / "pytest.ini").touch()

        repo = Repository(
            path=tmp_path,
            name="some-repo",  # Generic name
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_repo_with_tests_but_no_source_and_no_indicators_fails(self, tmp_path):
        """Test that repos with tests/ but no test indicators still fail.

        Fix for #305: Only repos that look like test repos get not_applicable.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        (tmp_path / "tests").mkdir()
        # No conftest.py, no pytest.ini, generic name

        repo = Repository(
            path=tmp_path,
            name="generic-project",  # Doesn't suggest tests
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Should fail because it doesn't look like a test-only repo
        assert finding.status == "fail"
        assert finding.remediation is not None

    # === Tests for Poetry support ===

    def test_recognizes_poetry_project_name(self, tmp_path):
        """Test that assessor parses [tool.poetry].name from pyproject.toml."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        (tmp_path / "mypoetrypackage").mkdir()
        (tmp_path / "mypoetrypackage" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()

        # Poetry-style pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "mypoetrypackage"\n')

        repo = Repository(
            path=tmp_path,
            name="mypoetrypackage",
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

    # === Edge case tests ===

    def test_malformed_pyproject_toml_handled_gracefully(self, tmp_path):
        """Test that malformed pyproject.toml doesn't crash the assessor."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        (tmp_path / "tests").mkdir()

        # Malformed TOML
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml {{{{")

        repo = Repository(
            path=tmp_path,
            name="broken-project",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = StandardLayoutAssessor()
        # Should not raise, should fall back to other strategies
        finding = assessor.assess(repo)

        # Will fail (no source dir found) but shouldn't crash
        assert finding.status in ["fail", "not_applicable"]
