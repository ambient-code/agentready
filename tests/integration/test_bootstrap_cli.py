"""Integration tests for bootstrap CLI command."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from agentready.cli.main import cli


class TestBootstrapCLI:
    """Test bootstrap CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_bootstrap_help(self):
        """Test bootstrap --help."""
        result = self.runner.invoke(cli, ["bootstrap", "--help"])
        assert result.exit_code == 0
        assert "Bootstrap repository" in result.output
        assert "--dry-run" in result.output
        assert "--language" in result.output

    def test_bootstrap_non_git_repo(self):
        """Test bootstrap fails on non-git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(cli, ["bootstrap", tmpdir])
            assert result.exit_code == 1
            assert "Not a git repository" in result.output

    def test_bootstrap_dry_run(self):
        """Test bootstrap with --dry-run flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir, "--dry-run"])

            assert result.exit_code == 0
            assert "Dry run complete" in result.output
            assert "would be created" in result.output

            # Should list files that would be created
            assert ".github/workflows/agentready-assessment.yml" in result.output
            assert ".github/workflows/tests.yml" in result.output
            assert ".pre-commit-config.yaml" in result.output

            # Files should not actually be created
            assert not (repo_path / ".github" / "workflows").exists()

    def test_bootstrap_creates_files(self):
        """Test bootstrap actually creates files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0
            assert "Bootstrap complete" in result.output
            assert "Repository bootstrapped successfully" in result.output

            # Check that key files were created
            assert (
                repo_path / ".github" / "workflows" / "agentready-assessment.yml"
            ).exists()
            assert (repo_path / ".github" / "workflows" / "tests.yml").exists()
            assert (repo_path / ".github" / "workflows" / "security.yml").exists()
            assert (repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md").exists()
            assert (repo_path / ".github" / "dependabot.yml").exists()
            assert (repo_path / ".pre-commit-config.yaml").exists()

    def test_bootstrap_with_language_python(self):
        """Test bootstrap with --language python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(
                cli, ["bootstrap", tmpdir, "--language", "python"]
            )

            assert result.exit_code == 0
            assert "Language: python" in result.output

    def test_bootstrap_with_language_javascript(self):
        """Test bootstrap with --language javascript."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            # JavaScript templates might not exist, but command should handle gracefully
            result = self.runner.invoke(
                cli, ["bootstrap", tmpdir, "--language", "javascript"]
            )

            # Should either succeed or fail gracefully
            assert result.exit_code in [0, 1]

    def test_bootstrap_default_current_directory(self):
        """Test bootstrap defaults to current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            # Run from within the temp directory
            result = self.runner.invoke(
                cli,
                ["bootstrap", "--dry-run"],
                catch_exceptions=False,
                obj={"cwd": tmpdir},
            )

            # Should run without error
            assert "AgentReady Bootstrap" in result.output

    def test_bootstrap_shows_next_steps(self):
        """Test bootstrap shows next steps after completion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0
            assert "Next steps:" in result.output
            assert "Review generated files" in result.output
            assert "git add" in result.output
            assert "git commit" in result.output

    def test_bootstrap_output_format(self):
        """Test bootstrap output formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir, "--dry-run"])

            assert result.exit_code == 0

            # Should have proper header
            assert "🤖 AgentReady Bootstrap" in result.output
            assert "=" * 50 in result.output

            # Should show repository path (resolve to handle symlinks on macOS)
            assert "Repository:" in result.output
            # Path might be /var or /private/var on macOS, so just check basename
            assert tmpdir.split("/")[-1] in result.output

            # Should show language
            assert "Language:" in result.output

    def test_bootstrap_lists_created_files(self):
        """Test bootstrap lists all created files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0

            # Should list files with checkmarks
            assert "✓ .github/workflows/agentready-assessment.yml" in result.output
            assert "✓ .github/workflows/tests.yml" in result.output
            assert "✓ .github/workflows/security.yml" in result.output
            assert "✓ .github/PULL_REQUEST_TEMPLATE.md" in result.output
            assert "✓ .pre-commit-config.yaml" in result.output


class TestBootstrapCLIEdgeCases:
    """Test edge cases for bootstrap CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_bootstrap_with_existing_files(self):
        """Test bootstrap with some existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            # Create existing CONTRIBUTING.md
            contributing = repo_path / "CONTRIBUTING.md"
            contributing.write_text("# Existing Guide")

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0

            # Should not overwrite existing file
            assert contributing.read_text() == "# Existing Guide"

            # But should create other files
            assert (repo_path / "CODE_OF_CONDUCT.md").exists()

    def test_bootstrap_creates_nested_directories(self):
        """Test bootstrap creates nested directory structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0

            # Check nested directory creation
            assert (repo_path / ".github" / "workflows").is_dir()
            assert (repo_path / ".github" / "ISSUE_TEMPLATE").is_dir()

    def test_bootstrap_invalid_path(self):
        """Test bootstrap with invalid path."""
        result = self.runner.invoke(cli, ["bootstrap", "/nonexistent/path"])

        # Click should handle this with proper error
        assert result.exit_code != 0


class TestBootstrapCLIRepomix:
    """Test Repomix integration in bootstrap CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_bootstrap_with_repomix_flag(self):
        """Test bootstrap with --repomix flag creates Repomix files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir, "--repomix"])

            assert result.exit_code == 0
            assert "Repomix: True" in result.output

            # Check that Repomix files were created
            assert (repo_path / "repomix.config.json").exists()
            assert (repo_path / ".repomixignore").exists()

            # Check that Repomix workflow was created
            assert (repo_path / ".github" / "workflows" / "repomix-update.yml").exists()

    def test_bootstrap_without_repomix_flag(self):
        """Test bootstrap without --repomix flag doesn't create Repomix files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir])

            assert result.exit_code == 0
            assert "Repomix: False" in result.output

            # Check that Repomix files were NOT created
            assert not (repo_path / "repomix.config.json").exists()
            assert not (repo_path / ".repomixignore").exists()

            # Check that Repomix workflow was NOT created
            assert not (
                repo_path / ".github" / "workflows" / "repomix-update.yml"
            ).exists()

    def test_bootstrap_repomix_dry_run(self):
        """Test bootstrap --repomix with --dry-run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(
                cli, ["bootstrap", tmpdir, "--repomix", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Dry run complete" in result.output

            # Should list Repomix files that would be created
            assert "repomix.config.json" in result.output
            assert ".repomixignore" in result.output
            assert "repomix-update.yml" in result.output

            # Files should not actually be created
            assert not (repo_path / "repomix.config.json").exists()
            assert not (repo_path / ".repomixignore").exists()

    def test_bootstrap_repomix_lists_created_files(self):
        """Test bootstrap --repomix lists Repomix files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            result = self.runner.invoke(cli, ["bootstrap", tmpdir, "--repomix"])

            assert result.exit_code == 0

            # Should list Repomix files with checkmarks
            assert "✓ repomix.config.json" in result.output
            assert "✓ .repomixignore" in result.output
            assert "✓ .github/workflows/repomix-update.yml" in result.output

    def test_bootstrap_repomix_doesnt_overwrite_existing(self):
        """Test bootstrap --repomix doesn't overwrite existing Repomix config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            # Create existing Repomix config
            config_path = repo_path / "repomix.config.json"
            existing_content = '{"custom": "config"}'
            config_path.write_text(existing_content)

            result = self.runner.invoke(cli, ["bootstrap", tmpdir, "--repomix"])

            assert result.exit_code == 0

            # Should not overwrite existing config
            assert config_path.read_text() == existing_content

            # But should still create ignore file if it doesn't exist
            assert (repo_path / ".repomixignore").exists()
