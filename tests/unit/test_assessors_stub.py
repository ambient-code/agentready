"""Tests for stub assessors (LockFiles and ConventionalCommits)."""

from agentready.assessors.stub_assessors import (
    ConventionalCommitsAssessor,
    LockFilesAssessor,
)
from agentready.models.repository import Repository


class TestLockFilesAssessor:
    """Test LockFilesAssessor."""

    def test_python_project_with_uv_lock(self, tmp_path):
        """Test that Python project with uv.lock passes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        (tmp_path / "uv.lock").write_text("# uv lock file")

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

        assessor = LockFilesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "uv.lock" in finding.measured_value

    def test_python_library_with_pyproject_only(self, tmp_path):
        """Test that Python library with pyproject.toml but no lock file passes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # Create a library project (has [project.scripts])
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "test-lib"
version = "1.0.0"

[project.scripts]
test-cli = "test_lib.main:main"
"""
        )

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

        assessor = LockFilesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "pyproject.toml" in finding.measured_value

    def test_python_project_without_lock_fails(self, tmp_path):
        """Test that Python project without lock file fails."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # Not a library (no [project.scripts])
        (tmp_path / "pyproject.toml").write_text(
            """[project]
name = "test-app"
version = "1.0.0"
"""
        )

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

        assessor = LockFilesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "uv lock" in " ".join(finding.remediation.commands)

    def test_nodejs_project_with_package_lock(self, tmp_path):
        """Test that Node.js project with package-lock.json passes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "package-lock.json").write_text('{"lockfileVersion":2}')

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

        assessor = LockFilesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "package-lock.json" in finding.measured_value

    def test_nodejs_project_without_lock_suggests_npm(self, tmp_path):
        """Test that Node.js project without lock suggests npm commands."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "package.json").write_text('{"name":"test"}')

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

        assessor = LockFilesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        # Should suggest npm, not uv
        commands_text = " ".join(finding.remediation.commands)
        assert "npm install" in commands_text
        assert "uv lock" not in commands_text


class TestConventionalCommitsAssessor:
    """Test ConventionalCommitsAssessor."""

    def test_python_project_with_precommit_hook(self, tmp_path):
        """Test that Python project with conventional-pre-commit hook passes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        (tmp_path / ".pre-commit-config.yaml").write_text(
            """repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
"""
        )

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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "conventional-pre-commit" in " ".join(finding.evidence)

    def test_nodejs_project_with_commitlint(self, tmp_path):
        """Test that Node.js project with commitlint passes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "commitlint.config.js").write_text(
            "module.exports = {extends: ['@commitlint/config-conventional']}"
        )

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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "commitlint" in " ".join(finding.evidence)

    def test_project_without_conventional_commits_fails(self, tmp_path):
        """Test that project without conventional commit enforcement fails."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None

    def test_python_project_suggests_precommit(self, tmp_path):
        """Test that Python project without enforcement suggests pre-commit."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        # Should suggest pre-commit, not npm
        commands_text = " ".join(finding.remediation.commands)
        assert "pre-commit" in commands_text
        assert "npm install" not in commands_text

    def test_nodejs_project_suggests_commitlint(self, tmp_path):
        """Test that Node.js project without enforcement suggests commitlint."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / "package.json").write_text('{"name":"test"}')

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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        # Should suggest npm/commitlint, not pre-commit
        commands_text = " ".join(finding.remediation.commands)
        assert "npm install" in commands_text
        assert "commitlint" in commands_text
