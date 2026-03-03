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

    def test_renovate_json_configuration(self, tmp_path):
        """Test that Renovate configuration in renovate.json is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json
        renovate_file = tmp_path / "renovate.json"
        renovate_file.write_text("""{
  "extends": ["config:base"],
  "schedule": "after 10pm every weekday"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)

    def test_renovate_github_directory(self, tmp_path):
        """Test that Renovate configuration in .github/renovate.json is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .github/renovate.json
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        renovate_file = github_dir / "renovate.json"
        renovate_file.write_text("""{
  "extends": ["config:base"]
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)

    def test_renovate_github_directory_json5(self, tmp_path):
        """Test that Renovate configuration in .github/renovate.json5 is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .github/renovate.json5 with JSON5 syntax
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        renovate_file = github_dir / "renovate.json5"
        renovate_file.write_text("""{
  // GitHub directory JSON5 config
  "extends": ["config:base"],
  "timezone": "America/New_York", // trailing comma
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)

    def test_renovate_rc_configuration(self, tmp_path):
        """Test that Renovate configuration in .renovaterc.json is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .renovaterc.json
        renovaterc_file = tmp_path / ".renovaterc.json"
        renovaterc_file.write_text("""{
  "extends": ["config:base"],
  "timezone": "America/New_York"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)

    def test_renovate_package_json_configuration(self, tmp_path):
        """Test that Renovate configuration in package.json is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create package.json with renovate config
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "name": "test-project",
  "renovate": {
    "extends": ["config:base"],
    "schedule": "after 10pm every weekday"
  },
  "dependencies": {
    "react": "^18.0.0"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured in package.json" in e for e in finding.evidence)

    def test_renovate_json5_configuration(self, tmp_path):
        """Test that Renovate configuration in renovate.json5 is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json5 (JSON5 format allows comments and trailing commas)
        renovate_file = tmp_path / "renovate.json5"
        renovate_file.write_text("""{
  // JSON5 config with comments
  "extends": ["config:base"],
  "schedule": "after 10pm every weekday", // trailing comma allowed
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30  # Renovate = 30 points
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)

    def test_renovaterc_configuration(self, tmp_path):
        """Test that Renovate configuration in .renovaterc is detected."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .renovaterc (config without extension)
        renovaterc_file = tmp_path / ".renovaterc"
        renovaterc_file.write_text("""{
  "extends": ["config:base"],
  "timezone": "America/New_York",
  "dependencyDashboard": true
}""")

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

        assert finding.score == 35  # Renovate (30) + bonus for "extends" (5)
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)
        assert any(
            "Meaningful Renovate configuration detected" in e for e in finding.evidence
        )

    def test_dependabot_first_match_wins_over_renovate(self, tmp_path):
        """Test that if both Dependabot and Renovate exist, first match (Dependabot) wins due to if/else structure."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create both Dependabot and Renovate configs
        github_dir = tmp_path / ".github"
        github_dir.mkdir()

        # Dependabot (checked first in if/elif chain)
        dependabot_file = github_dir / "dependabot.yml"
        dependabot_file.write_text("""version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
""")

        # Renovate (would be detected if Dependabot wasn't present)
        renovate_file = tmp_path / "renovate.json"
        renovate_file.write_text("""{
  "extends": ["config:base"]
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        # Should detect first match (Dependabot), not both tools
        assert "Dependabot" in finding.measured_value
        assert "Renovate" not in finding.measured_value
        assert any("Dependabot configured" in e for e in finding.evidence)

    def test_renovate_package_json_malformed(self, tmp_path):
        """Test that malformed package.json doesn't crash when checking for Renovate."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create malformed package.json
        package_json = tmp_path / "package.json"
        package_json.write_text("{ malformed json")

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

        # Should not crash and should not give credit for malformed config
        assert finding.status == "fail"
        assert "Renovate" not in finding.measured_value

    def test_dependabot_bonus_scoring(self, tmp_path):
        """Test that Dependabot gets +5 bonus for meaningful configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create .github/dependabot.yml with updates
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        dependabot_file = github_dir / "dependabot.yml"
        dependabot_file.write_text("""version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: npm
    directory: /frontend
    schedule:
      interval: daily
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 35  # 30 base + 5 bonus
        assert "Dependabot" in finding.measured_value
        assert any("2 package ecosystem(s) monitored" in e for e in finding.evidence)

    def test_renovate_bonus_scoring(self, tmp_path):
        """Test that Renovate gets +5 bonus for meaningful configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json with meaningful config
        renovate_file = tmp_path / "renovate.json"
        renovate_file.write_text("""{
  "extends": ["config:base"],
  "schedule": "after 10pm every weekday",
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    }
  ]
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 35  # 30 base + 5 bonus
        assert "Renovate" in finding.measured_value
        assert any(
            "Meaningful Renovate configuration detected" in e for e in finding.evidence
        )

    def test_renovate_no_bonus_for_minimal_config(self, tmp_path):
        """Test that Renovate gets no bonus for minimal/non-meaningful configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json with only schema (non-meaningful)
        renovate_file = tmp_path / "renovate.json"
        renovate_file.write_text("""{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "timezone": "America/New_York"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 30  # 30 base, no bonus
        assert "Renovate" in finding.measured_value
        assert not any("Meaningful" in e for e in finding.evidence)

    def test_renovate_json5_no_bonus(self, tmp_path):
        """Test that JSON5 files get base points but no bonus (can't parse)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json5 with meaningful config (but JSON5 syntax)
        renovate_file = tmp_path / "renovate.json5"
        renovate_file.write_text("""{
  // JSON5 with meaningful config but unparseable by stdlib json
  "extends": ["config:base"],
  "schedule": "after 10pm every weekday", // trailing comma
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 30  # Base only, no bonus (JSON5 skipped)
        assert "Renovate" in finding.measured_value
        assert not any("Meaningful" in e for e in finding.evidence)

    def test_renovate_multiple_sources_file_precedence(self, tmp_path):
        """Test when both Renovate file and package.json exist, file gets bonus precedence."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create meaningful renovate.json
        renovate_file = tmp_path / "renovate.json"
        renovate_file.write_text("""{
  "extends": ["config:base"]
}""")

        # Create package.json with renovate config too
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "name": "test-project",
  "renovate": {
    "schedule": "after 10pm every weekday"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 35  # File-based config gets bonus
        assert "Renovate" in finding.measured_value
        assert any(
            "Meaningful Renovate configuration detected" in e for e in finding.evidence
        )

    def test_remediation_includes_renovate(self, tmp_path):
        """Test that remediation guidance mentions Renovate as option."""
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

        # Should fail and have remediation
        assert finding.status == "fail"
        assert finding.remediation is not None

        # Check remediation mentions both options
        remediation_text = " ".join(finding.remediation.steps)
        assert "Dependabot" in remediation_text
        assert "Renovate" in remediation_text
        assert "renovate.json" in remediation_text

        # Check tools list includes both
        assert "Dependabot" in finding.remediation.tools
        assert "Renovate" in finding.remediation.tools

        # Check examples include renovate.json
        examples_text = " ".join(finding.remediation.examples)
        assert "renovate.json" in examples_text

    def test_renovate_json5_with_meaningful_package_json_fallback(self, tmp_path):
        """Test that when only JSON5 file exists (no bonus), meaningful package.json awards bonus via fallback."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create renovate.json5 (gets base points but no bonus due to JSON5 parsing limitation)
        renovate_json5 = tmp_path / "renovate.json5"
        renovate_json5.write_text("""{
  // JSON5 config that can't be parsed for bonus
  "extends": ["config:base"], // meaningful config but unparseable
}""")

        # Create package.json with meaningful renovate config (should get bonus via fallback)
        package_json = tmp_path / "package.json"
        package_json.write_text("""{
  "name": "test-project",
  "renovate": {
    "schedule": "after 10pm every weekday"
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

        assessor = DependencySecurityAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 35  # Base (30) + fallback bonus from package.json (5)
        assert "Renovate" in finding.measured_value
        assert any("Renovate configured" in e for e in finding.evidence)
        assert any(
            "Meaningful Renovate configuration detected" in e for e in finding.evidence
        )
