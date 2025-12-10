"""Tests for stub assessors (enhanced implementations)."""

import subprocess

from agentready.assessors.stub_assessors import (
    DependencyPinningAssessor,
    GitignoreAssessor,
)
from agentready.models.repository import Repository


class TestDependencyPinningAssessor:
    """Test DependencyPinningAssessor (formerly LockFilesAssessor)."""

    def test_no_lock_files(self, tmp_path):
        """Test that assessor fails when no lock files present."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "No dependency lock files found" in finding.evidence
        assert finding.remediation is not None

    def test_npm_package_lock(self, tmp_path):
        """Test detection of package-lock.json."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create package-lock.json
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text('{"name": "test", "lockfileVersion": 2}')

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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "package-lock.json" in finding.measured_value
        assert any("Found lock file" in e for e in finding.evidence)

    def test_python_poetry_lock(self, tmp_path):
        """Test detection of poetry.lock."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create poetry.lock
        lock_file = tmp_path / "poetry.lock"
        lock_file.write_text("[[package]]\nname = 'requests'\nversion = '2.28.1'\n")

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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "poetry.lock" in finding.measured_value

    def test_requirements_txt_all_pinned(self, tmp_path):
        """Test requirements.txt with all dependencies pinned."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create requirements.txt with exact versions
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(
            """requests==2.28.1
flask==2.3.0
pytest==7.4.0
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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "All 3 dependencies pinned" in " ".join(finding.evidence)

    def test_requirements_txt_unpinned_dependencies(self, tmp_path):
        """Test requirements.txt with unpinned dependencies."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create requirements.txt with mix of pinned and unpinned
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(
            """requests==2.28.1
flask>=2.0.0
pytest~=7.0
numpy
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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        # Score should be reduced (1 pinned, 3 unpinned = 25%)
        assert finding.status == "fail"
        assert finding.score < 75  # Below passing threshold
        assert any("unpinned" in e for e in finding.evidence)
        assert finding.remediation is not None

    def test_stale_lock_file(self, tmp_path):
        """Test detection of stale lock files (>6 months old)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        import time

        # Create lock file and set modification time to 8 months ago
        lock_file = tmp_path / "package-lock.json"
        lock_file.write_text('{"name": "test"}')

        # Set mtime to 8 months ago (240 days)
        old_time = time.time() - (240 * 24 * 60 * 60)
        import os

        os.utime(lock_file, (old_time, old_time))

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

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        # Score should be reduced for stale lock file
        assert finding.score < 100
        assert any("months old" in e for e in finding.evidence)

    def test_multiple_lock_files(self, tmp_path):
        """Test repository with multiple lock files."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create multiple lock files
        (tmp_path / "package-lock.json").write_text("{}")
        (tmp_path / "Cargo.lock").write_text("[[package]]")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"JavaScript": 50, "Rust": 50},
            total_files=10,
            total_lines=100,
        )

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "package-lock.json" in finding.measured_value
        assert "Cargo.lock" in finding.measured_value

    def test_backward_compatibility_alias(self):
        """Test that LockFilesAssessor is an alias for DependencyPinningAssessor."""
        from agentready.assessors.stub_assessors import LockFilesAssessor

        assert LockFilesAssessor is DependencyPinningAssessor


class TestGitignoreAssessor:
    """Test GitignoreAssessor with language-specific pattern checking."""

    def test_no_gitignore(self, tmp_path):
        """Test that assessor fails when .gitignore is missing."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert ".gitignore not found" in finding.evidence
        assert finding.remediation is not None

    def test_empty_gitignore(self, tmp_path):
        """Test that empty .gitignore fails."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create empty .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("")

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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert ".gitignore is empty" in finding.evidence

    def test_python_patterns(self, tmp_path):
        """Test detection of Python-specific patterns."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with Python patterns
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
venv/
.venv/
.env

# General
.DS_Store
.vscode/
.idea/
*.swp
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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        # Should pass with high coverage
        assert finding.status == "pass"
        assert finding.score >= 70
        assert "Pattern coverage" in finding.evidence[1]

    def test_javascript_patterns(self, tmp_path):
        """Test detection of JavaScript-specific patterns."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with JavaScript patterns
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """# JavaScript
node_modules/
dist/
build/
.npm/
*.log

# General
.DS_Store
.vscode/
"""
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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 70
        # Pattern coverage should be reported in evidence
        assert "Pattern coverage" in finding.evidence[1]

    def test_missing_patterns(self, tmp_path):
        """Test detection of missing language-specific patterns."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with only general patterns
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """# General only
.DS_Store
.vscode/
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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        # Should fail due to missing Python patterns
        assert finding.status == "fail"
        assert finding.score < 70
        assert any("Missing" in e for e in finding.evidence)
        assert finding.remediation is not None

    def test_multi_language_patterns(self, tmp_path):
        """Test repository with multiple languages."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with Python and JavaScript patterns
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
venv/
.venv/
.env

# JavaScript
node_modules/
dist/
build/
.npm/
*.log

# General
.DS_Store
.vscode/
.idea/
"""
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 60, "JavaScript": 40},
            total_files=10,
            total_lines=100,
        )

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 70
        # Should detect patterns for both languages

    def test_pattern_with_trailing_slash(self, tmp_path):
        """Test that patterns work with and without trailing slashes."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with mixed slash usage
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """__pycache__
venv
.venv/
.DS_Store
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

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        # Should match patterns regardless of trailing slash
        # __pycache__/ should match __pycache__ and vice versa
        assert finding.score > 0

    def test_no_languages_detected(self, tmp_path):
        """Test repository with no detected languages."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with some content
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".DS_Store\n.vscode/\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},  # No languages detected
            total_files=10,
            total_lines=100,
        )

        assessor = GitignoreAssessor()
        finding = assessor.assess(repo)

        # Should still give points if file exists with content
        assert finding.score > 0
