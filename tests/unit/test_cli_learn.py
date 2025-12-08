"""Unit tests for learn CLI command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from agentready.cli.learn import learn
from tests.fixtures.assessment_fixtures import create_test_assessment_json


@pytest.fixture
def temp_repo():
    """Create a temporary repository with assessment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create .git directory
        (repo_path / ".git").mkdir()

        # Create .agentready directory with assessment
        agentready_dir = repo_path / ".agentready"
        agentready_dir.mkdir()

        # Create sample assessment using shared fixture
        assessment_data = create_test_assessment_json(
            overall_score=85.0,
            num_findings=2,
            repo_path=str(repo_path),
            repo_name="test-repo",
        )

        assessment_file = agentready_dir / "assessment-latest.json"
        with open(assessment_file, "w") as f:
            json.dump(assessment_data, f)

        yield repo_path


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestLearnCommand:
    """Test learn CLI command."""

    def test_learn_command_basic(self, runner, temp_repo):
        """Test basic learn command execution."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(learn, [str(temp_repo)])

            # Should succeed
            assert result.exit_code == 0

            # Should create output directory
            output_dir = temp_repo / ".skills-proposals"
            assert output_dir.exists()

    def test_learn_command_json_output(self, runner, temp_repo):
        """Test learn command with JSON output."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(learn, [str(temp_repo), "--output-format", "json"])

            assert result.exit_code == 0

            # Check for JSON output file
            output_dir = temp_repo / ".skills-proposals"
            json_files = list(output_dir.glob("*.json"))
            assert len(json_files) > 0

    @pytest.mark.skip(
        reason="Test fixture doesn't create findings that produce extractable skills - needs proper test data"
    )
    def test_learn_command_skill_md_output(self, runner, temp_repo):
        """Test learn command with SKILL.md output."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn, [str(temp_repo), "--output-format", "skill_md"]
            )

            assert result.exit_code == 0

            # Check for SKILL.md files
            output_dir = temp_repo / ".skills-proposals"
            md_files = list(output_dir.glob("*.md"))
            assert len(md_files) > 0

    @pytest.mark.skip(
        reason="Test fixture doesn't create findings that produce extractable skills - needs proper test data"
    )
    def test_learn_command_github_issues_output(self, runner, temp_repo):
        """Test learn command with GitHub issues output."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn, [str(temp_repo), "--output-format", "github_issues"]
            )

            assert result.exit_code == 0

            # Check for issue files
            output_dir = temp_repo / ".skills-proposals"
            issue_files = list(output_dir.glob("issue-*.md"))
            assert len(issue_files) > 0

    @pytest.mark.skip(
        reason="Test fixture doesn't create findings that produce extractable skills - needs proper test data"
    )
    def test_learn_command_all_output_formats(self, runner, temp_repo):
        """Test learn command with all output formats."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(learn, [str(temp_repo), "--output-format", "all"])

            assert result.exit_code == 0

            # Should have multiple file types
            output_dir = temp_repo / ".skills-proposals"
            assert len(list(output_dir.glob("*.json"))) > 0
            assert len(list(output_dir.glob("*.md"))) > 0

    def test_learn_command_custom_output_dir(self, runner, temp_repo):
        """Test learn command with custom output directory."""
        custom_dir = temp_repo / "custom-skills"

        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [str(temp_repo), "--output-dir", str(custom_dir)],
            )

            assert result.exit_code == 0
            assert custom_dir.exists()

    def test_learn_command_specific_attribute(self, runner, temp_repo):
        """Test learn command with specific attribute filter."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [
                    str(temp_repo),
                    "--attribute",
                    "claude_md_file",
                ],
            )

            assert result.exit_code == 0

    def test_learn_command_multiple_attributes(self, runner, temp_repo):
        """Test learn command with multiple attribute filters."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [
                    str(temp_repo),
                    "--attribute",
                    "claude_md_file",
                    "--attribute",
                    "type_annotations",
                ],
            )

            assert result.exit_code == 0

    def test_learn_command_min_confidence(self, runner, temp_repo):
        """Test learn command with custom minimum confidence."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [str(temp_repo), "--min-confidence", "80"],
            )

            assert result.exit_code == 0

    def test_learn_command_verbose(self, runner, temp_repo):
        """Test learn command with verbose output."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [str(temp_repo), "--verbose"],
            )

            assert result.exit_code == 0
            # Verbose should produce more output
            assert len(result.output) > 0

    def test_learn_command_no_assessment_file(self, runner):
        """Test learn command fails gracefully with no assessment file."""
        with runner.isolated_filesystem():
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)
                (repo_path / ".git").mkdir()

                result = runner.invoke(learn, [str(repo_path)])

                # Should fail gracefully
                assert result.exit_code != 0
                assert (
                    "assessment" in result.output.lower()
                    or "not found" in result.output.lower()
                )

    def test_learn_command_invalid_repository(self, runner):
        """Test learn command with non-existent repository."""
        result = runner.invoke(learn, ["/nonexistent/path"])

        # Should fail
        assert result.exit_code != 0

    @patch("agentready.cli.learn.LearningService")
    def test_learn_command_enable_llm_without_api_key(
        self, mock_service, runner, temp_repo
    ):
        """Test learn command with LLM enabled but no API key."""
        # Remove ANTHROPIC_API_KEY if present
        import os

        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            with runner.isolated_filesystem(temp_dir=temp_repo.parent):
                result = runner.invoke(
                    learn,
                    [str(temp_repo), "--enable-llm"],
                )

                # Should warn or fall back gracefully
                # Implementation may vary, but shouldn't crash
                assert "API key" in result.output or result.exit_code == 0
        finally:
            # Restore API key if it existed
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    @patch("agentready.cli.learn.LearningService")
    def test_learn_command_enable_llm_with_budget(
        self, mock_service, runner, temp_repo
    ):
        """Test learn command with LLM enabled and custom budget."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [
                    str(temp_repo),
                    "--enable-llm",
                    "--llm-budget",
                    "10",
                ],
            )

            # Should succeed (or gracefully handle missing API key)
            assert result.exit_code == 0 or "API key" in result.output

    @patch("agentready.cli.learn.LearningService")
    def test_learn_command_llm_no_cache(self, mock_service, runner, temp_repo):
        """Test learn command with LLM cache bypass."""
        with runner.isolated_filesystem(temp_dir=temp_repo.parent):
            result = runner.invoke(
                learn,
                [
                    str(temp_repo),
                    "--enable-llm",
                    "--llm-no-cache",
                ],
            )

            # Should succeed (or gracefully handle missing API key)
            assert result.exit_code == 0 or "API key" in result.output

    def test_learn_command_default_repository(self, runner):
        """Test learn command with default repository (current directory)."""
        with runner.isolated_filesystem():
            # Create minimal git repo structure
            Path(".git").mkdir()
            agentready_dir = Path(".agentready")
            agentready_dir.mkdir()

            # Create minimal assessment using shared fixture
            assessment_data = create_test_assessment_json(
                overall_score=75.0,
                num_findings=1,
                repo_path=".",
                repo_name="test",
            )

            with open(agentready_dir / "assessment-latest.json", "w") as f:
                json.dump(assessment_data, f)

            result = runner.invoke(learn, [])

            # Should use current directory
            assert result.exit_code == 0


class TestLearnCommandErrorHandling:
    """Test error handling in learn command."""

    def test_learn_invalid_output_format(self, runner, temp_repo):
        """Test learn command with invalid output format."""
        result = runner.invoke(
            learn,
            [str(temp_repo), "--output-format", "invalid"],
        )

        # Should fail with validation error
        assert result.exit_code != 0

    def test_learn_invalid_min_confidence(self, runner, temp_repo):
        """Test learn command with invalid min confidence."""
        result = runner.invoke(
            learn,
            [str(temp_repo), "--min-confidence", "invalid"],
        )

        # Should fail with validation error
        assert result.exit_code != 0

    def test_learn_negative_llm_budget(self, runner, temp_repo):
        """Test learn command with negative LLM budget."""
        result = runner.invoke(
            learn,
            [str(temp_repo), "--llm-budget", "-5"],
        )

        # Should fail with validation error (Click validates int type)
        assert result.exit_code != 0

    def test_learn_corrupted_assessment_file(self, runner):
        """Test learn command with corrupted assessment file."""
        with runner.isolated_filesystem():
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)
                (repo_path / ".git").mkdir()

                # Create .agentready directory
                agentready_dir = repo_path / ".agentready"
                agentready_dir.mkdir()

                # Create corrupted assessment
                assessment_file = agentready_dir / "assessment-latest.json"
                assessment_file.write_text("{invalid json content")

                result = runner.invoke(learn, [str(repo_path)])

                # Should fail gracefully
                assert result.exit_code != 0
