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
from agentready.fixers.testing import PrecommitHooksFixer
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding, Remediation
from agentready.models.fix import CommandFix, FileCreationFix, Fix, MultiStepFix
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

    def test_generate_fix_when_agent_md_missing(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test generating fix when AGENTS.md is missing returns MultiStepFix with CommandFix + post-step."""
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
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
        assert (
            "Move" in fix.steps[1].preview() and "AGENTS.md" in fix.steps[1].preview()
        )

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
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: ""}, clear=False):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert fix is None

    def test_apply_fix_dry_run_when_agent_md_missing(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test applying MultiStep fix in dry-run (command not executed)."""
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        result = fix.apply(dry_run=True)
        assert result is True

        # File should NOT be created in dry run (claude CLI not run)
        assert not (temp_repo.path / "CLAUDE.md").exists()

    def test_apply_fix_real_runs_claude_cli(self, temp_repo, claude_md_failing_finding):
        """Test applying MultiStep fix runs Claude CLI (subprocess mocked)."""
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
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

    def test_post_step_moves_content_to_agent_md(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test second step moves CLAUDE.md content to AGENTS.md and replaces CLAUDE.md with @AGENTS.md."""
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert isinstance(fix, MultiStepFix)
        (temp_repo.path / "CLAUDE.md").write_text(
            "# Full content from Claude\nLine 2\n", encoding="utf-8"
        )

        result = fix.steps[1].apply(dry_run=False)

        assert result is True
        assert (temp_repo.path / "AGENTS.md").exists()
        assert (
            temp_repo.path / "AGENTS.md"
        ).read_text() == "# Full content from Claude\nLine 2\n"
        assert (temp_repo.path / "CLAUDE.md").read_text() == CLAUDE_MD_REDIRECT_LINE

    def test_post_step_preserves_existing_agents_md(
        self, temp_repo, claude_md_failing_finding
    ):
        """Test second step does not overwrite AGENTS.md when it already exists (idempotency)."""
        with patch(
            "agentready.fixers.documentation.shutil.which",
            return_value="/usr/bin/claude",
        ):
            with patch.dict(os.environ, {ANTHROPIC_API_KEY_ENV: "test-key"}):
                fixer = CLAUDEmdFixer()
                fix = fixer.generate_fix(temp_repo, claude_md_failing_finding)

        assert isinstance(fix, MultiStepFix)
        existing_content = "# Existing AGENTS.md\nCustom rules here.\n"
        (temp_repo.path / "AGENTS.md").write_text(existing_content, encoding="utf-8")
        (temp_repo.path / "CLAUDE.md").write_text(
            "# New content from Claude\n", encoding="utf-8"
        )

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


@pytest.fixture
def precommit_hooks_failing_finding():
    """Create a failing finding for pre-commit hooks."""
    attribute = Attribute(
        id="precommit_hooks",
        name="Pre-commit Hooks",
        description="Repository has pre-commit hooks configured",
        category="Testing",
        tier=2,
        criteria="Hooks configured",
        default_weight=0.05,
    )

    remediation = Remediation(
        summary="Set up pre-commit hooks",
        steps=["Create .pre-commit-config.yaml", "Run pre-commit install"],
        tools=["pre-commit"],
        commands=["pre-commit install"],
        examples=[],
        citations=[],
    )

    return Finding(
        attribute=attribute,
        status="fail",
        score=0.0,
        measured_value="Not configured",
        threshold="Configured",
        evidence=[],
        remediation=remediation,
        error_message=None,
    )


@pytest.fixture
def precommit_hooks_passing_finding():
    """Create a passing finding for pre-commit hooks."""
    attribute = Attribute(
        id="precommit_hooks",
        name="Pre-commit Hooks",
        description="Repository has pre-commit hooks configured",
        category="Testing",
        tier=2,
        criteria="Hooks configured",
        default_weight=0.05,
    )

    return Finding(
        attribute=attribute,
        status="pass",
        score=100.0,
        measured_value="Configured",
        threshold="Configured",
        evidence=[".pre-commit-config.yaml exists"],
        remediation=None,
        error_message=None,
    )


class TestPrecommitHooksFixer:
    """Tests for PrecommitHooksFixer.

    Tests cover:
    - Attribute ID verification
    - can_fix() with failing/passing findings
    - generate_fix() returns correct MultiStepFix structure
    - Language detection from repository.languages
    - Template fallback when language template doesn't exist
    - Generated .pre-commit-config.yaml content validation
    - Dry-run behavior

    References issue #271.
    """

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        fixer = PrecommitHooksFixer()
        assert fixer.attribute_id == "precommit_hooks"

    def test_can_fix_failing_finding(self, precommit_hooks_failing_finding):
        """Test can fix a failing pre-commit hooks finding."""
        fixer = PrecommitHooksFixer()
        assert fixer.can_fix(precommit_hooks_failing_finding) is True

    def test_cannot_fix_passing_finding(self, precommit_hooks_passing_finding):
        """Test cannot fix a passing finding."""
        fixer = PrecommitHooksFixer()
        assert fixer.can_fix(precommit_hooks_passing_finding) is False

    def test_cannot_fix_wrong_attribute(self, claude_md_failing_finding):
        """Test cannot fix finding for different attribute."""
        fixer = PrecommitHooksFixer()
        assert fixer.can_fix(claude_md_failing_finding) is False

    def test_generate_fix_returns_multistep_fix(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test generate_fix returns a MultiStepFix with file creation and command."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        assert fix is not None
        assert isinstance(fix, MultiStepFix)
        assert fix.attribute_id == "precommit_hooks"
        assert len(fix.steps) == 2

    def test_generate_fix_first_step_is_file_creation(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test first step creates .pre-commit-config.yaml."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        assert isinstance(fix.steps[0], FileCreationFix)
        assert fix.steps[0].file_path == Path(".pre-commit-config.yaml")
        assert fix.steps[0].description == "Create .pre-commit-config.yaml"

    def test_generate_fix_second_step_is_command(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test second step runs pre-commit install."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        assert isinstance(fix.steps[1], CommandFix)
        assert fix.steps[1].command == "pre-commit install"
        assert fix.steps[1].description == "Install pre-commit hooks"

    def test_generate_fix_has_positive_points(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test generated fix has positive points gained."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        assert fix.points_gained > 0

    def test_generate_fix_python_template_content(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test Python template generates correct pre-commit config content."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        file_fix = fix.steps[0]
        assert isinstance(file_fix, FileCreationFix)

        # Python template should include black and ruff
        content = file_fix.content
        assert "repos:" in content
        assert "black" in content or "ruff" in content

    def test_generate_fix_uses_primary_language(self, temp_repo):
        """Test fixer selects template based on primary language."""
        # Create finding for test
        attribute = Attribute(
            id="precommit_hooks",
            name="Pre-commit Hooks",
            description="Repository has pre-commit hooks",
            category="Testing",
            tier=2,
            criteria="Hooks configured",
            default_weight=0.05,
        )
        finding = Finding(
            attribute=attribute,
            status="fail",
            score=0.0,
            measured_value="Not configured",
            threshold="Configured",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        # Set Go as primary language
        temp_repo.languages = {"Go": 80, "Python": 20}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, finding)

        assert fix is not None
        file_fix = fix.steps[0]
        content = file_fix.content

        # Go template should have golangci-lint, not black
        assert "golangci-lint" in content or "gofmt" in content or "repos:" in content

    def test_generate_fix_fallback_to_python_for_unknown_language(self, temp_repo):
        """Test fixer falls back to Python template for unsupported languages."""
        attribute = Attribute(
            id="precommit_hooks",
            name="Pre-commit Hooks",
            description="Repository has pre-commit hooks",
            category="Testing",
            tier=2,
            criteria="Hooks configured",
            default_weight=0.05,
        )
        finding = Finding(
            attribute=attribute,
            status="fail",
            score=0.0,
            measured_value="Not configured",
            threshold="Configured",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        # Set an unsupported language
        temp_repo.languages = {"Haskell": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, finding)

        # Should still generate a fix using Python fallback
        assert fix is not None
        assert isinstance(fix, MultiStepFix)
        file_fix = fix.steps[0]
        # Python template content
        assert "repos:" in file_fix.content

    def test_generate_fix_empty_languages_defaults_to_python(self, temp_repo):
        """Test fixer defaults to Python when no languages detected."""
        attribute = Attribute(
            id="precommit_hooks",
            name="Pre-commit Hooks",
            description="Repository has pre-commit hooks",
            category="Testing",
            tier=2,
            criteria="Hooks configured",
            default_weight=0.05,
        )
        finding = Finding(
            attribute=attribute,
            status="fail",
            score=0.0,
            measured_value="Not configured",
            threshold="Configured",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        temp_repo.languages = {}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, finding)

        assert fix is not None
        file_fix = fix.steps[0]
        # Python is the default
        assert "black" in file_fix.content or "ruff" in file_fix.content

    def test_generate_fix_returns_none_for_passing_finding(
        self, temp_repo, precommit_hooks_passing_finding
    ):
        """Test generate_fix returns None for passing finding."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_passing_finding)

        assert fix is None

    def test_apply_file_creation_dry_run(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test file creation step in dry-run mode doesn't create file."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        file_fix = fix.steps[0]
        result = file_fix.apply(dry_run=True)

        assert result is True
        assert not (temp_repo.path / ".pre-commit-config.yaml").exists()

    def test_apply_file_creation_creates_file(
        self, temp_repo, precommit_hooks_failing_finding
    ):
        """Test file creation step creates .pre-commit-config.yaml."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        file_fix = fix.steps[0]
        result = file_fix.apply(dry_run=False)

        assert result is True
        config_path = temp_repo.path / ".pre-commit-config.yaml"
        assert config_path.exists()

        content = config_path.read_text()
        assert "repos:" in content

    def test_apply_command_dry_run(self, temp_repo, precommit_hooks_failing_finding):
        """Test command step in dry-run mode doesn't execute command."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        command_fix = fix.steps[1]

        with patch("subprocess.run") as mock_run:
            result = command_fix.apply(dry_run=True)

        assert result is True
        mock_run.assert_not_called()

    def test_apply_command_executes(self, temp_repo, precommit_hooks_failing_finding):
        """Test command step executes pre-commit install."""
        temp_repo.languages = {"Python": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, precommit_hooks_failing_finding)

        command_fix = fix.steps[1]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = None
            result = command_fix.apply(dry_run=False)

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        # Command is passed as list ['pre-commit', 'install']
        assert "pre-commit" in call_args[0][0]
        assert "install" in call_args[0][0]

    def test_estimate_score_improvement(self, precommit_hooks_failing_finding):
        """Test score improvement estimation."""
        fixer = PrecommitHooksFixer()
        points = fixer.estimate_score_improvement(precommit_hooks_failing_finding)

        # With default_weight of 0.05, should be 5.0 points
        assert points == 5.0

    def test_generate_fix_javascript_template(self, temp_repo):
        """Test JavaScript template is used for JS repositories."""
        attribute = Attribute(
            id="precommit_hooks",
            name="Pre-commit Hooks",
            description="Repository has pre-commit hooks",
            category="Testing",
            tier=2,
            criteria="Hooks configured",
            default_weight=0.05,
        )
        finding = Finding(
            attribute=attribute,
            status="fail",
            score=0.0,
            measured_value="Not configured",
            threshold="Configured",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        temp_repo.languages = {"JavaScript": 100}

        fixer = PrecommitHooksFixer()
        fix = fixer.generate_fix(temp_repo, finding)

        assert fix is not None
        file_fix = fix.steps[0]
        content = file_fix.content

        # JavaScript template should include prettier or eslint
        assert "repos:" in content
        assert (
            "prettier" in content
            or "eslint" in content
            or "pre-commit-hooks" in content
        )
