"""Unit tests for fixers."""

import tempfile
from pathlib import Path

import pytest

from agentready.fixers.documentation import CLAUDEmdFixer, GitignoreFixer
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding, Remediation
from agentready.models.repository import Repository


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create .git directory to make it a valid repo
        (repo_path / ".git").mkdir()
        yield Repository(
            path=repo_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},
            total_files=0,
            total_lines=0,
        )


@pytest.fixture
def claude_md_failing_finding():
    """Create a failing finding for CLAUDE.md."""
    attribute = Attribute(
        id="claude_md_file",
        name="CLAUDE.md File",
        description="Repository has CLAUDE.md",
        category="Documentation",
        tier=1,
        criteria="File exists",
        default_weight=0.10,
    )

    remediation = Remediation(
        summary="Create CLAUDE.md",
        steps=["Create CLAUDE.md file"],
        tools=[],
        commands=[],
        examples=[],
        citations=[],
    )

    return Finding(
        attribute=attribute,
        status="fail",
        score=0.0,
        measured_value="Not found",
        threshold="Present",
        evidence=[],
        remediation=remediation,
        error_message=None,
    )


@pytest.fixture
def gitignore_failing_finding():
    """Create a failing finding for gitignore."""
    attribute = Attribute(
        id="gitignore_completeness",
        name="Gitignore Completeness",
        description="Complete .gitignore patterns",
        category="Version Control",
        tier=2,
        criteria=">90% patterns",
        default_weight=0.03,
    )

    remediation = Remediation(
        summary="Improve .gitignore",
        steps=["Add recommended patterns"],
        tools=[],
        commands=[],
        examples=[],
        citations=[],
    )

    return Finding(
        attribute=attribute,
        status="fail",
        score=50.0,
        measured_value="50% coverage",
        threshold=">90% coverage",
        evidence=[],
        remediation=remediation,
        error_message=None,
    )


class TestCLAUDEmdFixer:
    """Tests for CLAUDEmdFixer."""

    def test_attribute_id(self):
        """Test attribute ID matches."""
        fixer = CLAUDEmdFixer()
        assert fixer.attribute_id == "claude_md_file"

    def test_can_fix_failing_finding(self, claude_md_failing_finding):
        """Test can fix failing CLAUDE.md finding."""
        fixer = CLAUDEmdFixer()
        assert fixer.can_fix(claude_md_failing_finding) is True

    def test_cannot_fix_passing_finding(self, claude_md_failing_finding):
        """Test cannot fix passing finding."""
        fixer = CLAUDEmdFixer()
        claude_md_failing_finding.status = "pass"
        assert fixer.can_fix(claude_md_failing_finding) is False

    def test_generate_fix(self, temp_repo, claude_md_failing_finding):
        """Test generating CLAUDE.md fix."""
        fixer = CLAUDEmdFixer()
        fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is not None
        assert fix.attribute_id == "claude_md_file"
        assert fix.file_path == Path("CLAUDE.md")
        assert "# " in fix.content  # Has markdown header
        assert fix.points_gained > 0

    def test_apply_fix_dry_run(self, temp_repo, claude_md_failing_finding):
        """Test applying fix in dry-run mode."""
        fixer = CLAUDEmdFixer()
        fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        result = fix.apply(dry_run=True)
        assert result is True

        # File should NOT be created in dry run
        assert not (temp_repo.path / "CLAUDE.md").exists()

    def test_apply_fix_real(self, temp_repo, claude_md_failing_finding):
        """Test applying fix for real."""
        fixer = CLAUDEmdFixer()
        fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        result = fix.apply(dry_run=False)
        assert result is True

        # File should be created
        assert (temp_repo.path / "CLAUDE.md").exists()

        # Content should be valid
        content = (temp_repo.path / "CLAUDE.md").read_text()
        assert len(content) > 0
        assert "# " in content


class TestGitignoreFixer:
    """Tests for GitignoreFixer."""

    def test_attribute_id(self):
        """Test attribute ID matches."""
        fixer = GitignoreFixer()
        assert fixer.attribute_id == "gitignore_completeness"

    def test_can_fix_failing_finding(self, gitignore_failing_finding):
        """Test can fix failing gitignore finding."""
        fixer = GitignoreFixer()
        assert fixer.can_fix(gitignore_failing_finding) is True

    def test_generate_fix_requires_existing_gitignore(
        self, temp_repo, gitignore_failing_finding
    ):
        """Test fix requires .gitignore to exist."""
        fixer = GitignoreFixer()
        fix = fixer.generate_fix(temp_repo, gitignore_failing_finding)

        assert fix is not None
        assert fix.attribute_id == "gitignore_completeness"

        # Should fail to apply if .gitignore doesn't exist
        result = fix.apply(dry_run=False)
        assert result is False  # File doesn't exist

    def test_apply_fix_to_existing_gitignore(self, temp_repo, gitignore_failing_finding):
        """Test applying fix to existing .gitignore."""
        # Create existing .gitignore
        gitignore_path = temp_repo.path / ".gitignore"
        gitignore_path.write_text("# Existing patterns\n*.log\n")

        fixer = GitignoreFixer()
        fix = fixer.generate_fix(temp_repo, gitignore_failing_finding)

        result = fix.apply(dry_run=False)
        assert result is True

        # Check additions were made
        content = gitignore_path.read_text()
        assert "# AgentReady recommended patterns" in content
        assert "__pycache__/" in content
