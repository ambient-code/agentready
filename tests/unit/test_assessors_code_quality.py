"""Tests for code quality assessors."""

import subprocess

from agentready.assessors.code_quality import CodeSmellsAssessor
from agentready.models.repository import Repository


class TestCodeSmellsAssessor:
    """Test CodeSmellsAssessor with multi-language linter support."""

    def test_no_linters_configured(self, tmp_path):
        """Test that assessor fails when no linters configured (markdown always checked)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},  # No languages
            total_files=10,
            total_lines=100,
        )

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # markdownlint is always checked, so it fails with 0% coverage
        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "No linters configured" in finding.evidence

    def test_python_with_no_linters(self, tmp_path):
        """Test Python repository with no linters configured."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Python repository without linter configs
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        (tmp_path / "main.py").write_text("print('hello')")

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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "No linters configured" in finding.evidence
        assert finding.remediation is not None

    def test_python_pylint_configured(self, tmp_path):
        """Test detection of pylint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pylintrc
        pylintrc = tmp_path / ".pylintrc"
        pylintrc.write_text(
            """[MASTER]
max-line-length=100

[MESSAGES CONTROL]
disable=C0111
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Python has 40 points possible (pylint=20, ruff=20), markdownlint=10
        # pylint detected = 20 points out of 50 total = 40%
        assert finding.score >= 20
        assert "pylint" in finding.measured_value
        assert any("pylint" in e.lower() for e in finding.evidence)

    def test_python_ruff_configured(self, tmp_path):
        """Test detection of ruff configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create ruff.toml
        ruff_toml = tmp_path / "ruff.toml"
        ruff_toml.write_text(
            """line-length = 100
select = ["E", "F", "W"]
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 20
        assert "ruff" in finding.measured_value

    def test_python_pyproject_toml(self, tmp_path):
        """Test detection of pylint/ruff in pyproject.toml."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create pyproject.toml with both tools
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[tool.pylint]
max-line-length = 100

[tool.ruff]
line-length = 100
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Both linters detected (pylint + ruff = 40 points out of 50 = 80%)
        assert finding.status == "pass"
        assert finding.score >= 60  # Above passing threshold
        assert "pylint" in finding.measured_value
        assert "ruff" in finding.measured_value

    def test_javascript_eslint_configured(self, tmp_path):
        """Test detection of ESLint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .eslintrc.json
        eslintrc = tmp_path / ".eslintrc.json"
        eslintrc.write_text(
            """{
  "extends": "eslint:recommended",
  "rules": {
    "no-console": "warn"
  }
}
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # JavaScript has 20 points possible + markdownlint 10 = 30 total
        # ESLint = 20 points out of 30 = 67%
        assert finding.status == "pass"
        assert finding.score >= 60
        assert "ESLint" in finding.measured_value

    def test_typescript_eslint_configured(self, tmp_path):
        """Test that TypeScript also detects ESLint."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create eslint.config.js (flat config)
        eslint_config = tmp_path / "eslint.config.js"
        eslint_config.write_text("export default [];\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"TypeScript": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert "ESLint" in finding.measured_value

    def test_ruby_rubocop_configured(self, tmp_path):
        """Test detection of RuboCop configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .rubocop.yml
        rubocop = tmp_path / ".rubocop.yml"
        rubocop.write_text(
            """AllCops:
  TargetRubyVersion: 3.0

Style/StringLiterals:
  EnforcedStyle: double_quotes
"""
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Ruby": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Ruby has 20 points + markdownlint 10 = 30 total
        assert finding.status == "pass"
        assert finding.score >= 60
        assert "RuboCop" in finding.measured_value

    def test_go_golangci_lint_configured(self, tmp_path):
        """Test detection of golangci-lint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .golangci.yml
        golangci = tmp_path / ".golangci.yml"
        golangci.write_text(
            """linters:
  enable:
    - gofmt
    - golint
    - govet
"""
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Go has 20 points + markdownlint 10 = 30 total
        assert finding.status == "pass"
        assert finding.score >= 60
        assert "golangci-lint" in finding.measured_value

    def test_actionlint_in_precommit(self, tmp_path):
        """Test detection of actionlint in pre-commit config."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create GitHub Actions workflow
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            "name: CI\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )

        # Create .pre-commit-config.yaml with actionlint
        precommit = tmp_path / ".pre-commit-config.yaml"
        precommit.write_text(
            """repos:
  - repo: https://github.com/rhysd/actionlint
    rev: v1.6.0
    hooks:
      - id: actionlint
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Should detect actionlint
        assert "actionlint" in finding.measured_value

    def test_markdownlint_configured(self, tmp_path):
        """Test detection of markdownlint configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .markdownlint.json
        markdownlint = tmp_path / ".markdownlint.json"
        markdownlint.write_text(
            """{
  "default": true,
  "MD013": false
}
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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Should detect markdownlint
        assert "markdownlint" in finding.measured_value

    def test_comprehensive_multi_language_setup(self, tmp_path):
        """Test repository with comprehensive linter setup across languages."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Python linters
        (tmp_path / ".pylintrc").write_text("[MASTER]\n")
        (tmp_path / "ruff.toml").write_text("line-length = 100\n")

        # JavaScript linters
        (tmp_path / ".eslintrc.json").write_text("{}\n")

        # Ruby linters
        (tmp_path / ".rubocop.yml").write_text("AllCops:\n")

        # Go linters
        (tmp_path / ".golangci.yml").write_text("linters:\n")

        # GitHub Actions
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI\n")
        precommit = tmp_path / ".pre-commit-config.yaml"
        precommit.write_text("repos:\n  - repo: actionlint\n")

        # Markdown
        (tmp_path / ".markdownlint.json").write_text("{}\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={
                "Python": 30,
                "JavaScript": 25,
                "Ruby": 20,
                "Go": 25,
            },
            total_files=100,
            total_lines=10000,
        )

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Should pass with high score (all language linters + actionlint + markdownlint)
        assert finding.status == "pass"
        assert finding.score >= 90  # Nearly perfect coverage
        assert finding.remediation is None
        # Should detect at least 6 linters
        assert len(finding.measured_value.split(",")) >= 6

    def test_partial_linter_coverage(self, tmp_path):
        """Test repository with partial linter coverage."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Only pylint configured, missing ruff
        (tmp_path / ".pylintrc").write_text("[MASTER]\n")

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

        assessor = CodeSmellsAssessor()
        finding = assessor.assess(repo)

        # Python: 40 points possible + markdownlint: 10 = 50 total
        # pylint: 20 points = 40% coverage
        assert finding.status == "fail"
        assert finding.score < 60  # Below passing threshold
        assert finding.remediation is not None
        assert any("ruff" in s.lower() for s in finding.remediation.steps)
