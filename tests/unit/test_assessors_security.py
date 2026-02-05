"""Tests for security assessors."""

import subprocess

from agentready.assessors.security import DependencySecurityAssessor
from agentready.models.repository import Repository


class TestDependencySecurityAssessor:
    """Test DependencySecurityAssessor."""

    def test_no_security_tools(self, tmp_path):
        """Test that assessor fails when no security tools configured."""
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None
        assert "No security scanning tools" in finding.measured_value

    def test_dependabot_configured(self, tmp_path):
        """Test that Dependabot configuration is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .github/dependabot.yml
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        dependabot_file = github_dir / "dependabot.yml"
        dependabot_file.write_text("""version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Dependabot = 30 points
        assert "Dependabot" in finding.measured_value
        assert any("Dependabot configured" in e for e in finding.evidence)

    def test_codeql_workflow(self, tmp_path):
        """Test that CodeQL workflow is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .github/workflows/codeql.yml
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        codeql_file = workflows_dir / "codeql-analysis.yml"
        codeql_file.write_text("name: CodeQL\nsteps:\n  - uses: github/codeql-action\n")

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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 25  # CodeQL = 25 points
        assert "CodeQL" in finding.measured_value
        assert any("CodeQL" in e for e in finding.evidence)

    def test_python_security_tools(self, tmp_path):
        """Test detection of Python security tools (pip-audit, bandit)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create pyproject.toml with security tools
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""[tool.poetry.dev-dependencies]
pip-audit = "^2.0.0"
bandit = "^1.7.0"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 20  # pip-audit/safety (10) + bandit (10)
        assert (
            "pip-audit" in finding.measured_value or "safety" in finding.measured_value
        )
        assert "Bandit" in finding.measured_value

    def test_secret_detection(self, tmp_path):
        """Test detection of secret scanning tools."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .pre-commit-config.yaml with detect-secrets
        precommit = tmp_path / ".pre-commit-config.yaml"
        precommit.write_text("""repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 20  # Secret detection = 20 points
        assert "detect-secrets" in finding.measured_value
        assert any("Secret detection" in e for e in finding.evidence)

    def test_security_policy_bonus(self, tmp_path):
        """Test that SECURITY.md gives bonus points."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create SECURITY.md
        security_md = tmp_path / "SECURITY.md"
        security_md.write_text(
            "# Security Policy\n\nReport vulnerabilities to security@example.com\n"
        )

        # Also add Dependabot to get above minimum threshold
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        dependabot = github_dir / "dependabot.yml"
        dependabot.write_text("version: 2\nupdates:\n  - package-ecosystem: pip\n")

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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 35  # Dependabot (30) + bonus (5)
        assert any("SECURITY.md" in e for e in finding.evidence)

    def test_comprehensive_security_setup(self, tmp_path):
        """Test repository with comprehensive security setup."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create all security configurations
        github_dir = tmp_path / ".github"
        github_dir.mkdir()

        # Dependabot
        (github_dir / "dependabot.yml").write_text(
            "version: 2\nupdates:\n  - package-ecosystem: pip\n"
        )

        # CodeQL workflow
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "codeql.yml").write_text("name: CodeQL\n")

        # Pre-commit with secrets
        (tmp_path / ".pre-commit-config.yaml").write_text(
            "repos:\n  - repo: detect-secrets\n"
        )

        # pyproject.toml with bandit
        (tmp_path / "pyproject.toml").write_text("[tool.bandit]\nskip = []\n")

        # SECURITY.md
        (tmp_path / "SECURITY.md").write_text("# Security\n")

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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        # Should pass with high score
        assert finding.status == "pass"
        assert finding.score >= 60  # Minimum passing threshold
        assert finding.remediation is None
        assert len(finding.evidence) > 4  # Multiple tools detected

    def test_javascript_security_tools(self, tmp_path):
        """Test detection of JavaScript security tools."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create package.json with audit script
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "scripts": {
    "audit": "npm audit",
    "test": "jest"
  },
  "devDependencies": {
    "snyk": "^1.0.0"
  }
}
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 20  # npm audit (10) + Snyk (10)
        assert (
            "npm/yarn audit" in finding.measured_value
            or "Snyk" in finding.measured_value
        )
