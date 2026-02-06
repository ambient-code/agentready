"""Unit tests for fixers."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentready.fixers.documentation import (
    ANTHROPIC_API_KEY_ENV,
    CLAUDE_MD_COMMAND,
    CLAUDE_MD_REDIRECT_LINE,
    CLAUDEmdFixer,
    GitignoreFixer,
)
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding, Remediation
from agentready.models.fix import CommandFix, Fix, MultiStepFix
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

    def test_generate_fix_when_agent_md_missing(self, temp_repo, claude_md_failing_finding):
        """Test generating fix when AGENTS.md is missing returns MultiStepFix with CommandFix + post-step."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is not None
        assert isinstance(fix, MultiStepFix)
        assert len(fix.steps) == 2
        assert isinstance(fix.steps[0], CommandFix)
        assert fix.steps[0].command == CLAUDE_MD_COMMAND
        assert fix.steps[0].working_dir == temp_repo.path
        assert fix.steps[0].capture_output is False
        assert fix.attribute_id == "claude_md_file"
        assert fix.points_gained > 0
        assert "Move" in fix.steps[1].preview() and "AGENTS.md" in fix.steps[1].preview()

    def test_generate_fix_when_agent_md_exists_returns_redirect_only_fix(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test that when AGENTS.md exists, fixer returns single-step redirect fix (no Claude CLI)."""
        (temp_repo.path / "AGENTS.md").write_text("# Agent docs\n", encoding="utf-8")

        fixer = CLAUDEmdFixer()
        fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is not None
        assert isinstance(fix, Fix)
        assert not isinstance(fix, MultiStepFix)
        assert fix.attribute_id == "claude_md_file"
        assert fix.points_gained > 0
        # Applying the fix should create CLAUDE.md with redirect only
        result = fix.apply(dry_run=False)
        assert result is True
        assert (temp_repo.path / "CLAUDE.md").read_text() == CLAUDE_MD_REDIRECT_LINE

    def test_generate_fix_returns_none_when_claude_not_on_path(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test that no fix is generated when Claude CLI is not on PATH (AGENTS.md missing)."""
        with patch("agentready.fixers.documentation.shutil.which", return_value=None):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is None

    def test_generate_fix_returns_none_when_no_api_key(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test that no fix is generated when ANTHROPIC_API_KEY is not set."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: ""}, clear=False):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is None

    def test_apply_fix_dry_run_when_agent_md_missing(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test applying MultiStep fix in dry-run (command not executed)."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        result = fix.apply(dry_run=True)
        assert result is True

        # File should NOT be created in dry run (claude CLI not run)
        assert not (temp_repo.path / "CLAUDE.md").exists()

    def test_apply_fix_real_runs_claude_cli(self, temp_repo, claude_md_failing_finding):
        """Test applying MultiStep fix runs Claude CLI (subprocess mocked)."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = None  # run() returns None when check=True succeeds
            result = fix.apply(dry_run=False)

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "claude" in call_args[0][0]
        assert call_args[1]["capture_output"] is False
        assert call_args[1]["cwd"] == temp_repo.path

    def test_post_step_moves_content_to_agent_md(self, temp_repo, claude_md_failing_finding):
        """Test second step moves CLAUDE.md content to AGENTS.md and replaces CLAUDE.md with @AGENTS.md."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert isinstance(fix, MultiStepFix)
        (temp_repo.path / "CLAUDE.md").write_text("# Full content from Claude\nLine 2\n", encoding="utf-8")

        result = fix.steps[1].apply(dry_run=False)

        assert result is True
        assert (temp_repo.path / "AGENTS.md").exists()
        assert (temp_repo.path / "AGENTS.md").read_text() == "# Full content from Claude\nLine 2\n"
        assert (temp_repo.path / "CLAUDE.md").read_text() == CLAUDE_MD_REDIRECT_LINE

    def test_post_step_preserves_existing_agents_md(self, temp_repo, claude_md_failing_finding):
        """Test second step does not overwrite AGENTS.md when it already exists (idempotency)."""
        with patch("agentready.fixers.documentation.shutil.which", return_value="/usr/bin/claude"):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert isinstance(fix, MultiStepFix)
        existing_content = "# Existing AGENTS.md\nCustom rules here.\n"
        (temp_repo.path / "AGENTS.md").write_text(existing_content, encoding="utf-8")
        (temp_repo.path / "CLAUDE.md").write_text("# New content from Claude\n", encoding="utf-8")

        result = fix.steps[1].apply(dry_run=False)

        assert result is True
        assert (temp_repo.path / "AGENTS.md").read_text() == existing_content
        assert (temp_repo.path / "CLAUDE.md").read_text() == CLAUDE_MD_REDIRECT_LINE


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

    def test_apply_fix_to_existing_gitignore(
        self, temp_repo, gitignore_failing_finding
    ):
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
