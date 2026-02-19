"""Unit tests for main CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentready.cli.main import (
    assess,
    cli,
    create_all_assessors,
    generate_config,
    get_agentready_version,
    load_config,
    research_version,
    run_assessment,
)
from agentready.models.config import Config


@pytest.fixture
def runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_repo(tmp_path):
    """Create a minimal test repository."""
    # Create .git directory
    (tmp_path / ".git").mkdir()

    # Create some files
    (tmp_path / "README.md").write_text("# Test Repo\n\nA test repository.")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_example(): pass")

    return tmp_path


@pytest.fixture
def mock_assessment(tmp_path):
    """Create a mock assessment for testing."""
    from datetime import datetime

    from agentready.models.assessment import Assessment
    from agentready.models.attribute import Attribute
    from agentready.models.finding import Finding
    from agentready.models.repository import Repository

    # Create a temporary directory with .git for Repository validation
    test_repo_path = tmp_path / "test-repo"
    test_repo_path.mkdir()
    (test_repo_path / ".git").mkdir()

    repo = Repository(
        name="test-repo",
        path=test_repo_path,
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 100},
        total_files=5,
        total_lines=100,
    )

    # Create 25 dummy findings to match attributes_total requirement
    findings = []
    for i in range(25):
        attr = Attribute(
            id=f"attr_{i}",
            name=f"Attribute {i}",
            category="Testing",
            tier=1,
            description="Test attribute",
            criteria="Test criteria",
            default_weight=0.5,
        )
        finding = Finding(
            attribute=attr,
            status="pass" if i < 20 else "not_applicable",
            score=100.0 if i < 20 else 0.0,
            measured_value="present",
            threshold="present",
            evidence=[f"Test evidence {i}"],
            remediation=None,
            error_message=None,
        )
        findings.append(finding)

    assessment = Assessment(
        repository=repo,
        timestamp=datetime.now(),
        findings=findings,
        overall_score=85.0,
        certification_level="Gold",
        attributes_assessed=20,
        attributes_not_assessed=5,
        attributes_total=25,
        config=None,
        duration_seconds=1.5,
    )

    return assessment


class TestCliGroup:
    """Test main CLI group."""

    def test_cli_no_args_shows_help(self, runner):
        """Test CLI with no arguments shows help."""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "AgentReady Repository Scorer" in result.output
        assert "assess" in result.output

    def test_cli_version_flag(self, runner):
        """Test CLI --version flag."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "AgentReady v" in result.output
        assert "Research Report:" in result.output

    def test_cli_help_flag(self, runner):
        """Test CLI --help flag."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "AgentReady Repository Scorer" in result.output
        assert "assess" in result.output


class TestAssessCommand:
    """Test assess command."""

    def test_assess_basic_execution(self, runner, test_repo, mock_assessment):
        """Test basic assess command execution."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code == 0
            assert "Assessment complete" in result.output
            mock_scanner.scan.assert_called_once()

    def test_assess_with_output_dir(self, runner, test_repo, mock_assessment):
        """Test assess with custom output directory."""
        output_dir = test_repo / "custom-reports"

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(
                assess,
                [str(test_repo), "--output-dir", str(output_dir)],
            )

            assert result.exit_code == 0
            assert output_dir.exists()

    def test_assess_with_verbose(self, runner, test_repo, mock_assessment):
        """Test assess with verbose flag."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(
                assess,
                [str(test_repo), "--verbose"],
            )

            assert result.exit_code == 0
            assert "AgentReady Repository Scorer" in result.output
            assert "Repository:" in result.output

    def test_assess_default_output_dir(self, runner, test_repo, mock_assessment):
        """Test assess creates default .agentready directory."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code == 0
            assert (test_repo / ".agentready").exists()

    def test_assess_generates_reports(self, runner, test_repo, mock_assessment):
        """Test that assess generates JSON, HTML, and MD reports."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code == 0

            agentready_dir = test_repo / ".agentready"
            json_reports = list(agentready_dir.glob("assessment-*.json"))
            html_reports = list(agentready_dir.glob("report-*.html"))
            md_reports = list(agentready_dir.glob("report-*.md"))

            assert len(json_reports) > 0
            assert len(html_reports) > 0
            assert len(md_reports) > 0

    def test_assess_creates_latest_symlinks(self, runner, test_repo, mock_assessment):
        """Test that assess creates latest symlinks."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code == 0

            agentready_dir = test_repo / ".agentready"
            assert (agentready_dir / "assessment-latest.json").exists()
            assert (agentready_dir / "report-latest.html").exists()
            assert (agentready_dir / "report-latest.md").exists()

    def test_assess_shows_score_and_stats(self, runner, test_repo, mock_assessment):
        """Test that assess shows overall score and stats in output."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code == 0
            assert "85.0" in result.output or "85" in result.output
            assert "Gold" in result.output
            assert "Duration:" in result.output

    def test_assess_with_config_file(self, runner, test_repo, mock_assessment):
        """Test assess with custom config file."""
        # Create config file
        config_file = test_repo / "test-config.yaml"
        config_file.write_text("weights:\n  claude_md_file: 1.0\n")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(
                assess,
                [str(test_repo), "--config", str(config_file)],
            )

            assert result.exit_code == 0

    def test_assess_default_repository(self, runner, mock_assessment):
        """Test assess with default repository (current directory)."""
        with runner.isolated_filesystem():
            # Create minimal git repo
            Path(".git").mkdir()

            with patch("agentready.cli.main.Scanner") as mock_scanner_class:
                mock_scanner = MagicMock()
                mock_scanner.scan.return_value = mock_assessment
                mock_scanner_class.return_value = mock_scanner

                result = runner.invoke(assess, [])

                assert result.exit_code == 0


class TestAssessErrorHandling:
    """Test error handling in assess command."""

    def test_assess_nonexistent_repo(self, runner):
        """Test assess with non-existent repository."""
        result = runner.invoke(assess, ["/nonexistent/path/to/repo"])

        # Path validation happens at Click level
        assert result.exit_code != 0

    def test_assess_not_git_repo(self, runner, tmp_path):
        """Test assess with directory that's not a git repo."""
        non_git_dir = tmp_path / "not-git"
        non_git_dir.mkdir()

        result = runner.invoke(assess, [str(non_git_dir)])

        # Scanner should raise ValueError for non-git repos
        assert result.exit_code != 0

    def test_assess_scanner_error(self, runner, test_repo):
        """Test assess handles scanner errors gracefully."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner_class.side_effect = ValueError("Not a git repository")

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code != 0
            assert "Error:" in result.output

    def test_assess_scan_error(self, runner, test_repo):
        """Test assess handles scan errors gracefully."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.side_effect = RuntimeError("Scan failed")
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo)])

            assert result.exit_code != 0
            assert "Error during assessment" in result.output

    def test_assess_scan_error_with_verbose(self, runner, test_repo):
        """Test assess shows traceback with verbose on error."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.side_effect = RuntimeError("Scan failed")
            mock_scanner_class.return_value = mock_scanner

            result = runner.invoke(assess, [str(test_repo), "--verbose"])

            assert result.exit_code != 0
            # With verbose, should show more error details
            assert "Error during assessment" in result.output

    def test_assess_invalid_config_file(self, runner, test_repo):
        """Test assess with invalid config file."""
        config_file = test_repo / "invalid-config.yaml"
        config_file.write_text("{invalid yaml content")

        result = runner.invoke(
            assess,
            [str(test_repo), "--config", str(config_file)],
        )

        # Should fail with YAML parse error
        assert result.exit_code != 0


class TestConfigLoading:
    """Test configuration loading."""

    def test_load_config_valid_yaml(self, tmp_path):
        """Test loading valid config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
weights:
  claude_md_file: 2.0
excluded_attributes:
  - test_attribute
""")

        config = load_config(config_file)

        assert isinstance(config, Config)
        assert config.weights["claude_md_file"] == 2.0
        assert "test_attribute" in config.excluded_attributes

    def test_load_config_empty(self, tmp_path):
        """Test loading empty config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("{}")

        config = load_config(config_file)

        assert isinstance(config, Config)

    def test_load_config_not_dict(self, tmp_path):
        """Test load_config rejects non-dict YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("- item1\n- item2")

        with pytest.raises(ValueError, match="Config must be a dict"):
            load_config(config_file)

    def test_load_config_unknown_keys(self, tmp_path):
        """Test load_config rejects unknown keys."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("unknown_key: value")

        with pytest.raises(ValueError, match="Unknown config keys"):
            load_config(config_file)

    def test_load_config_invalid_weights_type(self, tmp_path):
        """Test load_config rejects invalid weights type."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("weights: not_a_dict")

        with pytest.raises(ValueError, match="'weights' must be a dict"):
            load_config(config_file)

    def test_load_config_invalid_weight_value(self, tmp_path):
        """Test load_config rejects invalid weight values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("weights:\n  attr1: not_a_number")

        with pytest.raises(ValueError, match="'weights' values must be"):
            load_config(config_file)

    def test_load_config_invalid_excluded_attributes(self, tmp_path):
        """Test load_config rejects invalid excluded_attributes."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("excluded_attributes: not_a_list")

        with pytest.raises(ValueError, match="'excluded_attributes' must be a list"):
            load_config(config_file)

    def test_load_config_sensitive_output_dir(self, tmp_path):
        """Test load_config rejects sensitive output directories."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("output_dir: /etc/passwords")

        with pytest.raises(ValueError, match="Cannot be in sensitive system directory"):
            load_config(config_file)

    def test_load_config_invalid_report_theme(self, tmp_path):
        """Test load_config rejects invalid report_theme type."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("report_theme: 123")

        with pytest.raises(ValueError, match="'report_theme' must be str"):
            load_config(config_file)


class TestResearchVersionCommand:
    """Test research-version command."""

    def test_research_version_command(self, runner):
        """Test research-version command execution."""
        with patch("agentready.cli.main.ResearchLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_and_validate.return_value = (
                "content",
                MagicMock(
                    version="1.0.0",
                    date="2025-11-23",
                    attribute_count=25,
                    reference_count=30,
                ),
                True,
                [],
                [],
            )
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(research_version, [])

            assert result.exit_code == 0
            assert "1.0.0" in result.output
            assert "2025-11-23" in result.output
            assert "25" in result.output

    def test_research_version_with_errors(self, runner):
        """Test research-version command with validation errors."""
        with patch("agentready.cli.main.ResearchLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_and_validate.return_value = (
                "content",
                MagicMock(
                    version="1.0.0",
                    date="2025-11-23",
                    attribute_count=25,
                    reference_count=30,
                ),
                False,
                ["Error 1", "Error 2"],
                ["Warning 1"],
            )
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(research_version, [])

            assert result.exit_code == 0
            assert "FAIL" in result.output
            assert "Error 1" in result.output
            assert "Warning 1" in result.output

    def test_research_version_file_not_found(self, runner):
        """Test research-version command when file not found."""
        with patch("agentready.cli.main.ResearchLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_and_validate.side_effect = FileNotFoundError(
                "File not found"
            )
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(research_version, [])

            assert result.exit_code != 0
            assert "Error:" in result.output


class TestGenerateConfigCommand:
    """Test generate-config command."""

    def test_generate_config_creates_file(self, runner):
        """Test generate-config creates config file."""
        with runner.isolated_filesystem():
            # Create example config
            Path(".agentready-config.example.yaml").write_text("weights:\n  attr1: 1.0")

            result = runner.invoke(generate_config, [])

            assert result.exit_code == 0
            assert Path(".agentready-config.yaml").exists()
            assert "Created" in result.output

    def test_generate_config_no_example(self, runner):
        """Test generate-config fails when example not found."""
        with runner.isolated_filesystem():
            result = runner.invoke(generate_config, [])

            assert result.exit_code != 0
            assert "not found" in result.output

    def test_generate_config_overwrite_prompt(self, runner):
        """Test generate-config prompts when file exists."""
        with runner.isolated_filesystem():
            # Create both example and target
            Path(".agentready-config.example.yaml").write_text("weights:\n  attr1: 1.0")
            Path(".agentready-config.yaml").write_text("existing: content")

            # Decline overwrite
            result = runner.invoke(generate_config, [], input="n\n")

            assert result.exit_code == 0
            # Original file should still exist
            assert Path(".agentready-config.yaml").read_text() == "existing: content"

    def test_generate_config_overwrite_confirm(self, runner):
        """Test generate-config overwrites when confirmed."""
        with runner.isolated_filesystem():
            # Create both example and target
            Path(".agentready-config.example.yaml").write_text("weights:\n  attr1: 2.0")
            Path(".agentready-config.yaml").write_text("existing: content")

            # Confirm overwrite
            result = runner.invoke(generate_config, [], input="y\n")

            assert result.exit_code == 0
            assert "attr1: 2.0" in Path(".agentready-config.yaml").read_text()


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_agentready_version(self):
        """Test get_agentready_version returns string."""
        version = get_agentready_version()

        assert isinstance(version, str)
        # Should be either a version number or "unknown"
        assert version == "unknown" or "." in version

    def test_show_version(self, runner):
        """Test show_version function."""
        # Can't easily test this directly, but we can test via CLI
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "AgentReady" in result.output

    def test_create_all_assessors(self):
        """Test create_all_assessors returns list."""
        assessors = create_all_assessors()

        assert isinstance(assessors, list)
        # Should have all 25 assessors (implemented + stubs)
        assert len(assessors) >= 25


class TestSensitiveDirectoryWarning:
    """Test warning for sensitive directories."""

    @pytest.mark.skip(
        reason="Test uses /etc which causes PermissionError - needs redesign with proper mocks"
    )
    def test_assess_sensitive_directory_warning(self, runner):
        """Test assess warns for sensitive directories."""
        with patch("agentready.cli.main.Scanner"):
            # Decline to continue
            result = runner.invoke(assess, ["/etc"], input="n\n")

            # Should be aborted
            assert result.exit_code != 0

    @pytest.mark.skip(
        reason="Test uses /etc which causes PermissionError - needs redesign with proper mocks"
    )
    def test_assess_sensitive_directory_confirm(self, runner, mock_assessment):
        """Test assess continues when confirmed for sensitive directory."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Mock Path.mkdir to avoid PermissionError when creating .agentready in /etc
            with patch("pathlib.Path.mkdir"):
                # Confirm to continue
                result = runner.invoke(assess, ["/etc"], input="y\n")

                # Should proceed (though might fail for other reasons)
                # Main point is that it asked for confirmation
                assert "Warning" in result.output or result.exit_code == 0


class TestLargeRepositoryWarning:
    """Test warning for large repositories."""

    @pytest.mark.skip(
        reason="Test relies on complex mock interactions - needs redesign"
    )
    def test_assess_large_repo_warning(self, runner, test_repo, mock_assessment):
        """Test assess warns for large repositories."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Mock file count to be large
            with patch("agentready.cli.main.safe_subprocess_run") as mock_subprocess:
                # Simulate large repo with 15000 files
                mock_subprocess.return_value = MagicMock(
                    returncode=0, stdout="\n".join(["file.py"] * 15000)
                )

                # Decline to continue
                result = runner.invoke(assess, [str(test_repo)], input="n\n")

                # Should be aborted
                assert result.exit_code != 0


class TestRunAssessment:
    """Test run_assessment function directly."""

    def test_run_assessment_function(self, test_repo, mock_assessment):
        """Test run_assessment function."""
        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Call run_assessment directly
            run_assessment(
                str(test_repo), verbose=False, output_dir=None, config_path=None
            )

            # Should have created reports
            assert (test_repo / ".agentready").exists()
            mock_scanner.scan.assert_called_once()

    def test_run_assessment_excludes_attributes_from_config_issue_302(
        self, test_repo, mock_assessment, tmp_path
    ):
        """Test that excluded_attributes in config file are honored.

        Regression test for issue #302: excluded_attributes in config file
        was previously ignored - only --exclude CLI flag worked.
        """
        # Create config with excluded_attributes
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
excluded_attributes:
  - test_coverage
  - openapi_specs
""")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Call run_assessment with config
            run_assessment(
                str(test_repo),
                verbose=False,
                output_dir=None,
                config_path=str(config_file),
            )

            # Verify scan was called
            mock_scanner.scan.assert_called_once()

            # Get the assessors passed to scan using modern mock API
            call_args = mock_scanner.scan.call_args
            assessors = call_args.args[0]  # More robust than call_args[0][0]

            # Verify excluded attributes are NOT in the assessor list
            assessor_ids = {a.attribute_id for a in assessors}
            assert (
                "test_coverage" not in assessor_ids
            ), "test_coverage should be excluded by config"
            assert (
                "openapi_specs" not in assessor_ids
            ), "openapi_specs should be excluded by config"

    def test_run_assessment_merges_cli_and_config_exclusions_issue_302(
        self, test_repo, mock_assessment, tmp_path
    ):
        """Test that CLI --exclude and config excluded_attributes are merged.

        Regression test for issue #302: both sources of exclusions should
        be combined, not one overriding the other.
        """
        # Create config with one exclusion
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
excluded_attributes:
  - test_coverage
""")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Call run_assessment with config AND CLI exclusion
            run_assessment(
                str(test_repo),
                verbose=False,
                output_dir=None,
                config_path=str(config_file),
                exclude=["openapi_specs"],  # CLI exclusion
            )

            # Get the assessors passed to scan using modern mock API
            call_args = mock_scanner.scan.call_args
            assessors = call_args.args[0]  # More robust than call_args[0][0]

            # Verify BOTH exclusions are applied
            assessor_ids = {a.attribute_id for a in assessors}
            assert (
                "test_coverage" not in assessor_ids
            ), "test_coverage should be excluded by config"
            assert (
                "openapi_specs" not in assessor_ids
            ), "openapi_specs should be excluded by CLI"

    def test_run_assessment_validates_config_excluded_attributes_issue_302(
        self, test_repo, tmp_path
    ):
        """Test that invalid attribute IDs in config are rejected.

        Regression test for issue #302: invalid attribute IDs in config
        were previously silently ignored - now they should raise an error.
        Config-sourced errors use ClickException (not BadParameter) for clarity.
        """
        import click

        # Create config with invalid attribute ID
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
excluded_attributes:
  - nonexistent_attribute
  - test_coverage
""")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner_class.return_value = mock_scanner

            # Should raise ClickException for invalid attribute ID from config
            with pytest.raises(click.exceptions.ClickException) as exc_info:
                run_assessment(
                    str(test_repo),
                    verbose=False,
                    output_dir=None,
                    config_path=str(config_file),
                )

            # Verify error message mentions the invalid ID and source
            assert "nonexistent_attribute" in str(exc_info.value)
            assert "config file" in str(exc_info.value)

    def test_run_assessment_verbose_echoes_config_exclusions_issue_302(
        self, runner, test_repo, mock_assessment, tmp_path
    ):
        """Test that verbose mode echoes exclusions from config file.

        Regression test for issue #302: verbose output should show exclusions
        even when they come only from config (not CLI).
        Uses CliRunner for reliable Click output capture.
        """
        # Create config with exclusions
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
excluded_attributes:
  - test_coverage
""")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = mock_assessment
            mock_scanner_class.return_value = mock_scanner

            # Use CliRunner for reliable Click output capture
            result = runner.invoke(
                assess,
                [str(test_repo), "--verbose", "--config", str(config_file)],
            )

            # Verify exclusion message in output
            assert result.exit_code == 0
            assert "Excluded 1 attribute(s)" in result.output
            assert "test_coverage" in result.output

    def test_run_assessment_validates_mixed_source_invalid_attrs_issue_302(
        self, test_repo, tmp_path
    ):
        """Test that invalid IDs from both CLI and config are reported together.

        Regression test for issue #302: when both sources have invalid IDs,
        the error message should include all of them so the user can fix
        both in one round trip.
        """
        import click

        # Create config with invalid attribute ID
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
excluded_attributes:
  - invalid_config_attr
  - test_coverage
""")

        with patch("agentready.cli.main.Scanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner_class.return_value = mock_scanner

            # Should raise ClickException with both invalid IDs mentioned
            with pytest.raises(click.exceptions.ClickException) as exc_info:
                run_assessment(
                    str(test_repo),
                    verbose=False,
                    output_dir=None,
                    config_path=str(config_file),
                    exclude=["invalid_cli_attr"],  # CLI invalid ID
                )

            error_msg = str(exc_info.value)
            # Verify both sources are mentioned
            assert "invalid_cli_attr" in error_msg
            assert "invalid_config_attr" in error_msg
            assert "Also invalid in config file" in error_msg
