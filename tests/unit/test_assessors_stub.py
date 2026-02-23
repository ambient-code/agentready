"""Tests for stub assessors (enhanced implementations)."""

import os
import subprocess

import pytest

from agentready.assessors.stub_assessors import (
    ConventionalCommitsAssessor,
    DependencyPinningAssessor,
    FileSizeLimitsAssessor,
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
        requirements.write_text("""requests==2.28.1
flask==2.3.0
pytest==7.4.0
""")

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
        requirements.write_text("""requests==2.28.1
flask>=2.0.0
pytest~=7.0
numpy
""")

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
        gitignore.write_text("""# Python
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
""")

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
        gitignore.write_text("""# JavaScript
node_modules/
dist/
build/
.npm/
*.log

# General
.DS_Store
.vscode/
""")

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
        gitignore.write_text("""# General only
.DS_Store
.vscode/
""")

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
        gitignore.write_text("""# Python
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
""")

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
        gitignore.write_text("""__pycache__
venv
.venv/
.DS_Store
""")

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


class TestFileSizeLimitsAssessor:
    """Tests for FileSizeLimitsAssessor - Issue #245 fix."""

    def test_respects_gitignore_venv(self, tmp_path):
        """Verify .venv files are NOT counted (fixes issue #245)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with .venv/
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".venv/\n")

        # Create .venv directory with large file (should be IGNORED)
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        large_venv_file = venv_dir / "large_module.py"
        large_venv_file.write_text("x = 1\n" * 2000)  # 2000 lines - huge

        # Create src directory with small file (should be counted)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        small_file = src_dir / "main.py"
        small_file.write_text("print('hello')\n" * 50)  # 50 lines

        # Add only the tracked file to git
        subprocess.run(["git", "add", "src/main.py"], cwd=tmp_path, capture_output=True)

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 1},
            total_files=1,
            total_lines=50,
        )

        assessor = FileSizeLimitsAssessor()
        finding = assessor.assess(repo)

        # Should pass because .venv file is ignored
        assert finding.status == "pass"
        assert finding.score == 100.0
        # Evidence should NOT mention the 2000-line file
        assert "2000" not in str(finding.evidence)

    def test_no_source_files_returns_not_applicable(self, tmp_path):
        """Test not_applicable when no source files exist."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create only non-source files
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n")
        subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Markdown": 1},
            total_files=1,
            total_lines=1,
        )

        assessor = FileSizeLimitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_huge_files_detected(self, tmp_path):
        """Test that files >1000 lines are flagged."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create a huge file
        huge_file = tmp_path / "huge_module.py"
        huge_file.write_text("x = 1\n" * 1500)  # 1500 lines
        subprocess.run(
            ["git", "add", "huge_module.py"], cwd=tmp_path, capture_output=True
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 1},
            total_files=1,
            total_lines=1500,
        )

        assessor = FileSizeLimitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 70
        assert "1500" in str(finding.evidence) or ">1000" in str(finding.evidence)

    def test_small_files_pass(self, tmp_path):
        """Test that all files <500 lines gives perfect score."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create small files
        for i in range(5):
            small_file = tmp_path / f"module_{i}.py"
            small_file.write_text("x = 1\n" * 100)  # 100 lines each
            subprocess.run(
                ["git", "add", f"module_{i}.py"], cwd=tmp_path, capture_output=True
            )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 5},
            total_files=5,
            total_lines=500,
        )

        assessor = FileSizeLimitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "All 5 source files are <500 lines" in str(finding.evidence)

    def test_respects_gitignore_node_modules(self, tmp_path):
        """Verify node_modules files are NOT counted."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .gitignore with node_modules/
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n")

        # Create node_modules directory with large JS file (should be IGNORED)
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        large_js = nm_dir / "large_lib.js"
        large_js.write_text("var x = 1;\n" * 3000)  # 3000 lines

        # Create src directory with small JS file (should be counted)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        small_js = src_dir / "app.js"
        small_js.write_text("console.log('hi');\n" * 30)  # 30 lines

        subprocess.run(["git", "add", "src/app.js"], cwd=tmp_path, capture_output=True)

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"JavaScript": 1},
            total_files=1,
            total_lines=30,
        )

        assessor = FileSizeLimitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert "3000" not in str(finding.evidence)


class TestConventionalCommitsAssessor:
    """Test ConventionalCommitsAssessor config file detection."""

    def _make_repo(self, tmp_path):
        (tmp_path / ".git").mkdir(exist_ok=True)
        return Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

    @pytest.mark.parametrize(
        "config_file",
        [
            ".commitlintrc",
            ".commitlintrc.json",
            ".commitlintrc.yaml",
            ".commitlintrc.yml",
            ".commitlintrc.js",
            ".commitlintrc.cjs",
            ".commitlintrc.mjs",
            ".commitlintrc.ts",
            ".commitlintrc.cts",
            "commitlint.config.js",
            "commitlint.config.cjs",
            "commitlint.config.mjs",
            "commitlint.config.ts",
            "commitlint.config.cts",
        ],
    )
    def test_detects_all_config_formats(self, tmp_path, config_file):
        """Each supported commitlint config format should be detected."""
        (tmp_path / config_file).touch()
        repo = self._make_repo(tmp_path)
        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert finding.measured_value == "configured"

    def test_detects_husky_directory(self, tmp_path):
        """A .husky directory should also count as configured."""
        (tmp_path / ".husky").mkdir()
        repo = self._make_repo(tmp_path)
        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_fails_with_no_config(self, tmp_path):
        """Without any config files, the check must fail."""
        repo = self._make_repo(tmp_path)
        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.measured_value == "not configured"
        assert finding.remediation is not None

    def test_no_configuration_files(self, tmp_path):
        """Test that assessor fails when no conventional commit tools are configured."""
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

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "not configured" in finding.measured_value
        assert (
            "No commitlint configuration found (.commitlintrc.json, package.json, husky, or pre-commit)"
            in finding.evidence
        )
        assert finding.remediation is not None

    def test_commitlint_configuration(self, tmp_path):
        """Test detection of commitlint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .commitlintrc.json
        commitlint_config = tmp_path / ".commitlintrc.json"
        commitlint_config.write_text('{"extends": ["@commitlint/config-conventional"]}')

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
        assert "configured" in finding.measured_value
        assert "Commit linting configured" in finding.evidence

    def test_husky_configuration(self, tmp_path):
        """Test detection of husky configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .husky directory
        husky_dir = tmp_path / ".husky"
        husky_dir.mkdir()
        commit_msg_hook = husky_dir / "commit-msg"
        commit_msg_hook.write_text("#!/bin/sh\nnpx --no -- commitlint --edit $1")

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
        assert "configured" in finding.measured_value

    def test_package_json_commitlint_configuration(self, tmp_path):
        """Test detection of commitlint configuration in package.json."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create package.json with commitlint config
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "name": "test-project",
  "commitlint": {
    "extends": ["@commitlint/config-conventional"]
  },
  "devDependencies": {
    "@commitlint/cli": "^17.0.0",
    "@commitlint/config-conventional": "^17.0.0"
  }
}""")

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
        assert "configured" in finding.measured_value

    def test_package_json_malformed(self, tmp_path):
        """Test handling of malformed package.json."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create malformed package.json
        package_json = tmp_path / "package.json"
        package_json.write_text("{ invalid json content")

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

        # Should fail gracefully and not crash
        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_package_json_no_commitlint(self, tmp_path):
        """Test package.json without commitlint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create package.json without commitlint config
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "name": "test-project",
  "devDependencies": {
    "eslint": "^8.0.0"
  }
}""")

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
        assert finding.score == 0.0

    def test_precommit_conventional_linter(self, tmp_path):
        """Test detection of conventional-precommit-linter in pre-commit config."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml with conventional-precommit-linter
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("""repos:
  - repo: https://github.com/compilerla/conventional-precommit-linter
    rev: v2.1.1
    hooks:
      - id: conventional-precommit-linter
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, test, chore]
""")

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
        assert "configured" in finding.measured_value
        assert "Commit linting configured" in finding.evidence

    def test_precommit_conventional_pre_commit(self, tmp_path):
        """Test detection of conventional-pre-commit in pre-commit config."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml with conventional-pre-commit
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("""repos:
  - repo: https://github.com/example/conventional-pre-commit
    rev: v1.0.0
    hooks:
      - id: conventional-commit
""")

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

    def test_precommit_commitlint_hook(self, tmp_path):
        """Test detection of commitlint-pre-commit-hook in pre-commit config."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml with commitlint-pre-commit-hook
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("""repos:
  - repo: https://github.com/example/commitlint-pre-commit-hook
    rev: v1.0.0
    hooks:
      - id: commitlint
""")

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

    def test_precommit_no_conventional_tools(self, tmp_path):
        """Test that pre-commit config without conventional tools fails."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml without conventional commit tools
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("""repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
""")

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
        assert "not configured" in finding.measured_value

    def test_precommit_empty_config(self, tmp_path):
        """Test that empty pre-commit config fails."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create empty .pre-commit-config.yaml
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("")

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

    def test_precommit_invalid_yaml_fallback(self, tmp_path):
        """Test that invalid YAML in pre-commit config fails gracefully without attempting string matching fallback"""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml with invalid YAML (tests error handling)
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("invalid: yaml: content: [")

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

        # Should fail gracefully and not crash
        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_multiple_tools_configured(self, tmp_path):
        """Test repository with both commitlint and pre-commit conventional tools."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .commitlintrc.json
        commitlint_config = tmp_path / ".commitlintrc.json"
        commitlint_config.write_text('{"extends": ["@commitlint/config-conventional"]}')

        # Create .pre-commit-config.yaml with conventional tools
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("""repos:
  - repo: https://github.com/compilerla/conventional-precommit-linter
    rev: v2.1.1
    hooks:
      - id: conventional-precommit-linter
        stages: [commit-msg]
""")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 50, "JavaScript": 50},
            total_files=10,
            total_lines=100,
        )

        assessor = ConventionalCommitsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "configured" in finding.measured_value

    @pytest.mark.skipif(os.getuid() == 0, reason="chmod has no effect as root")
    def test_precommit_file_permission_error(self, tmp_path):
        """Test handling of permission error when reading pre-commit config."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        precommit_config.write_text("repos: []")

        # Make file unreadable (simulate permission error)
        os.chmod(precommit_config, 0o000)

        try:
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

            # Should handle the exception gracefully
            assert finding.status == "fail"
            assert finding.score == 0.0

        finally:
            # Restore permissions for cleanup
            os.chmod(precommit_config, 0o644)
