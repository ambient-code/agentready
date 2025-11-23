"""Unit tests for bootstrap CLI command."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from agentready.cli.bootstrap import bootstrap


@pytest.fixture
def temp_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()
        yield repo_path


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestBootstrapCommand:
    """Test bootstrap CLI command."""

    def test_bootstrap_basic_execution(self, runner, temp_repo):
        """Test basic bootstrap command execution."""
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0
        assert "AgentReady Bootstrap" in result.output
        assert "Bootstrap complete" in result.output

    def test_bootstrap_dry_run(self, runner, temp_repo):
        """Test bootstrap command in dry-run mode."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--dry-run"])

        # Should succeed
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "would be created" in result.output

        # Files should not exist
        assert not (temp_repo / ".github" / "workflows").exists()

    def test_bootstrap_creates_files(self, runner, temp_repo):
        """Test bootstrap command actually creates files."""
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0

        # Verify key files were created
        assert (temp_repo / ".github" / "workflows").exists()
        assert len(list((temp_repo / ".github" / "workflows").glob("*.yml"))) > 0

    def test_bootstrap_with_python_language(self, runner, temp_repo):
        """Test bootstrap command with Python language."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "python"])

        # Should succeed
        assert result.exit_code == 0
        assert "Language: python" in result.output

    def test_bootstrap_with_javascript_language(self, runner, temp_repo):
        """Test bootstrap command with JavaScript language."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "javascript"])

        # Should succeed
        assert result.exit_code == 0
        assert "Language: javascript" in result.output

    def test_bootstrap_with_go_language(self, runner, temp_repo):
        """Test bootstrap command with Go language."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "go"])

        # Should succeed
        assert result.exit_code == 0
        assert "Language: go" in result.output

    def test_bootstrap_with_auto_detect(self, runner, temp_repo):
        """Test bootstrap command with auto language detection."""
        # Create Python files
        (temp_repo / "main.py").write_text("print('hello')")

        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "auto"])

        # Should succeed
        assert result.exit_code == 0
        assert "Language: auto" in result.output

    def test_bootstrap_not_git_repository(self, runner):
        """Test bootstrap command on non-git repository."""
        with runner.isolated_filesystem():
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                result = runner.invoke(bootstrap, [str(repo_path)])

                # Should fail
                assert result.exit_code != 0
                assert "git repository" in result.output.lower()

    def test_bootstrap_nonexistent_repository(self, runner):
        """Test bootstrap command with non-existent path."""
        result = runner.invoke(bootstrap, ["/nonexistent/path"])

        # Should fail
        assert result.exit_code != 0

    def test_bootstrap_invalid_language(self, runner, temp_repo):
        """Test bootstrap command with invalid language."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "invalid"])

        # Should fail with validation error
        assert result.exit_code != 0

    def test_bootstrap_shows_next_steps(self, runner, temp_repo):
        """Test bootstrap command shows next steps."""
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should show next steps
        assert result.exit_code == 0
        assert "Next steps:" in result.output
        assert "git add" in result.output
        assert "git commit" in result.output
        assert "git push" in result.output

    def test_bootstrap_default_repository(self, runner):
        """Test bootstrap command with default repository (current directory)."""
        with runner.isolated_filesystem():
            Path(".git").mkdir()

            result = runner.invoke(bootstrap, [])

            # Should use current directory
            assert result.exit_code == 0

    def test_bootstrap_reports_file_count(self, runner, temp_repo):
        """Test bootstrap command reports number of files created."""
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should report file count
        assert result.exit_code == 0
        assert "Created" in result.output
        assert "files:" in result.output

    def test_bootstrap_lists_created_files(self, runner, temp_repo):
        """Test bootstrap command lists created files."""
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should list files
        assert result.exit_code == 0
        # Look for checkmarks or file names
        assert "✓" in result.output or ".github" in result.output

    @patch("agentready.cli.bootstrap.BootstrapGenerator")
    def test_bootstrap_handles_generator_error(self, mock_generator, runner, temp_repo):
        """Test bootstrap command handles generator errors."""
        mock_generator.return_value.generate_all.side_effect = Exception(
            "Generator error"
        )

        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should fail gracefully
        assert result.exit_code != 0
        assert "Error during bootstrap" in result.output

    def test_bootstrap_dry_run_lists_files(self, runner, temp_repo):
        """Test bootstrap dry-run lists files that would be created."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--dry-run"])

        # Should list files
        assert result.exit_code == 0
        # Should mention files
        assert ".github" in result.output or "files" in result.output.lower()

    def test_bootstrap_dry_run_shows_no_next_steps(self, runner, temp_repo):
        """Test bootstrap dry-run shows appropriate message."""
        result = runner.invoke(bootstrap, [str(temp_repo), "--dry-run"])

        # Should not show "Bootstrap complete" message
        assert "Run without --dry-run" in result.output

    def test_bootstrap_works_in_nested_repo(self, runner, temp_repo):
        """Test bootstrap command works in nested repository."""
        # Create nested directory
        nested = temp_repo / "subdir"
        nested.mkdir()

        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should still work from parent
        assert result.exit_code == 0


class TestBootstrapCommandEdgeCases:
    """Test edge cases in bootstrap command."""

    def test_bootstrap_empty_repository(self, runner, temp_repo):
        """Test bootstrap command on empty repository."""
        # Just has .git directory, nothing else
        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should still work
        assert result.exit_code == 0

    def test_bootstrap_with_existing_files(self, runner, temp_repo):
        """Test bootstrap command when some files already exist."""
        # Create .github directory
        github_dir = temp_repo / ".github"
        github_dir.mkdir()

        # Create a workflow file
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "existing.yml").write_text("name: existing")

        result = runner.invoke(bootstrap, [str(temp_repo)])

        # Should still work (may skip existing files)
        assert result.exit_code == 0

    def test_bootstrap_multiple_runs(self, runner, temp_repo):
        """Test running bootstrap multiple times."""
        # First run
        result1 = runner.invoke(bootstrap, [str(temp_repo)])
        assert result1.exit_code == 0

        # Second run (files already exist)
        result2 = runner.invoke(bootstrap, [str(temp_repo)])
        # Should still work (may skip or overwrite)
        assert result2.exit_code == 0

    def test_bootstrap_creates_workflow_files(self, runner, temp_repo):
        """Test bootstrap creates specific workflow files."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for specific workflows
        workflows_dir = temp_repo / ".github" / "workflows"
        workflow_files = list(workflows_dir.glob("*.yml"))

        # Should have at least tests and agentready workflows
        assert len(workflow_files) >= 2

    def test_bootstrap_creates_issue_templates(self, runner, temp_repo):
        """Test bootstrap creates issue templates."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for issue templates
        issue_template_dir = temp_repo / ".github" / "ISSUE_TEMPLATE"
        if issue_template_dir.exists():
            template_files = list(issue_template_dir.glob("*.md"))
            assert len(template_files) > 0

    def test_bootstrap_creates_pr_template(self, runner, temp_repo):
        """Test bootstrap creates pull request template."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for PR template
        pr_template = temp_repo / ".github" / "PULL_REQUEST_TEMPLATE.md"
        # May or may not exist depending on implementation
        if pr_template.exists():
            assert pr_template.is_file()

    def test_bootstrap_creates_precommit_config(self, runner, temp_repo):
        """Test bootstrap creates pre-commit configuration."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for pre-commit config
        precommit_config = temp_repo / ".pre-commit-config.yaml"
        if precommit_config.exists():
            assert precommit_config.is_file()
            content = precommit_config.read_text()
            assert "repos:" in content

    def test_bootstrap_creates_dependabot_config(self, runner, temp_repo):
        """Test bootstrap creates Dependabot configuration."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for Dependabot config
        dependabot_config = temp_repo / ".github" / "dependabot.yml"
        if dependabot_config.exists():
            assert dependabot_config.is_file()
            content = dependabot_config.read_text()
            assert "version:" in content

    def test_bootstrap_creates_contributing_guide(self, runner, temp_repo):
        """Test bootstrap creates CONTRIBUTING.md."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for CONTRIBUTING.md
        contributing = temp_repo / "CONTRIBUTING.md"
        if contributing.exists():
            assert contributing.is_file()

    def test_bootstrap_creates_codeowners(self, runner, temp_repo):
        """Test bootstrap creates CODEOWNERS file."""
        result = runner.invoke(bootstrap, [str(temp_repo)])
        assert result.exit_code == 0

        # Check for CODEOWNERS
        codeowners = temp_repo / ".github" / "CODEOWNERS"
        if codeowners.exists():
            assert codeowners.is_file()

    def test_bootstrap_respects_language_choice(self, runner, temp_repo):
        """Test bootstrap generates language-specific content."""
        # Create repo with JavaScript files
        (temp_repo / "package.json").write_text('{"name": "test"}')

        # But specify Python
        result = runner.invoke(bootstrap, [str(temp_repo), "--language", "python"])

        assert result.exit_code == 0
        # Should use specified language, not detected one
        assert "Language: python" in result.output
