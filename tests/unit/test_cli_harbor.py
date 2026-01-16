"""Unit tests for Harbor CLI commands.

Test Strategy:
    - Uses Click's CliRunner with isolated filesystem for CLI command testing
    - Mocks external dependencies (HarborRunner, AgentFileToggler, parse_harbor_results)
    - Uses actual data models (HarborComparison, HarborRunMetrics) for type safety
    - Covers success paths, error handling, and edge cases
    - Helper functions tested independently from CLI commands

Coverage Target:
    - Achieves 96% coverage of cli/harbor.py
    - All commands (compare, list, view) tested
    - Helper functions (_run_benchmark_phase, _generate_reports, _create_latest_symlinks) tested
    - Error conditions and validation logic covered

Test Fixtures:
    - runner: Click test runner for CLI command invocation
    - temp_repo: Temporary git repository with agent file structure
    - mock_task_results: Sample Harbor task results with realistic data
    - mock_comparison: Complete Harbor comparison object for testing report generation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentready.cli.harbor import (
    _create_latest_symlinks,
    _generate_reports,
    _run_benchmark_phase,
    compare,
    harbor_cli,
    list_comparisons,
    view_comparison,
)
from agentready.models.harbor import (
    HarborComparison,
    HarborRunMetrics,
    HarborTaskResult,
)


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_repo():
    """Create a temporary git repository with agent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()

        # Create agent file
        agent_dir = repo_path / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "doubleagent.md").write_text("# Agent file content")

        yield repo_path


@pytest.fixture
def mock_task_results():
    """Create mock Harbor task results."""
    return [
        HarborTaskResult(
            task_name="test-task-1",
            trial_name="trial_1",
            success=True,
            duration_sec=10.5,
            agent_result={"status": "success"},
            verifier_result={"passed": True},
            exception_info=None,
            started_at="2024-01-01T12:00:00",
            finished_at="2024-01-01T12:00:10",
        ),
        HarborTaskResult(
            task_name="test-task-2",
            trial_name="trial_2",
            success=True,
            duration_sec=15.2,
            agent_result={"status": "success"},
            verifier_result={"passed": True},
            exception_info=None,
            started_at="2024-01-01T12:01:00",
            finished_at="2024-01-01T12:01:15",
        ),
    ]


@pytest.fixture
def mock_comparison():
    """Create mock Harbor comparison.

    Simulates an A/B test comparison showing:
    - Baseline (without agent): 50% success rate, 12.5s avg duration
    - Treatment (with agent): 100% success rate, 10.0s avg duration
    - Delta: +50pp success rate improvement, -2.5s duration improvement
    """
    # Baseline metrics (agent disabled)
    without_metrics = HarborRunMetrics(
        run_id="without_20240101_120000",
        agent_file_enabled=False,
        task_results=[],
        success_rate=50.0,
        completion_rate=100.0,
        avg_duration_sec=12.5,
        total_tasks=2,
        successful_tasks=1,
        failed_tasks=1,
        timed_out_tasks=0,
    )

    # Treatment metrics (agent enabled)
    with_metrics = HarborRunMetrics(
        run_id="with_20240101_120000",
        agent_file_enabled=True,
        task_results=[],
        success_rate=100.0,
        completion_rate=100.0,
        avg_duration_sec=10.0,
        total_tasks=2,
        successful_tasks=2,
        failed_tasks=0,
        timed_out_tasks=0,
    )

    # Comparison with deltas and statistical significance
    return HarborComparison(
        created_at="2024-01-01T12:00:00",  # Fixed timestamp for determinism
        without_agent=without_metrics,
        with_agent=with_metrics,
        deltas={
            "success_rate_delta": 50.0,  # 50 percentage point improvement
            "avg_duration_delta_sec": -2.5,  # 2.5 second improvement
            "avg_duration_delta_pct": -20.0,  # 20% faster
        },
        statistical_significance={
            "success_rate_significant": True,
            "duration_significant": False,
        },
        per_task_comparison=[],
    )


class TestRunBenchmarkPhase:
    """Test _run_benchmark_phase helper function."""

    @patch("agentready.cli.harbor.click.echo")
    def test_run_without_agent(self, mock_echo, tmp_path):
        """Test running benchmark phase without agent."""
        mock_runner = MagicMock()
        mock_toggler = MagicMock()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = _run_benchmark_phase(
            runner=mock_runner,
            toggler=mock_toggler,
            phase_name="WITHOUT agent",
            run_number=1,
            output_dir=output_dir,
            task_list=["task1", "task2"],
            model="anthropic/claude-sonnet-4-5",
            verbose=False,
            disable_agent=True,
        )

        # Should use context manager for agent toggling
        mock_toggler.temporarily_disabled.assert_called_once()

        # Should run benchmark
        assert mock_runner.run_benchmark.called

        # Should return output directory
        assert result == output_dir

    @patch("agentready.cli.harbor.click.echo")
    def test_run_with_agent(self, mock_echo, tmp_path):
        """Test running benchmark phase with agent."""
        mock_runner = MagicMock()
        mock_toggler = MagicMock()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = _run_benchmark_phase(
            runner=mock_runner,
            toggler=mock_toggler,
            phase_name="WITH agent",
            run_number=2,
            output_dir=output_dir,
            task_list=["task1"],
            model="anthropic/claude-sonnet-4-5",
            verbose=True,
            disable_agent=False,
        )

        # Should NOT use context manager when agent enabled
        mock_toggler.temporarily_disabled.assert_not_called()

        # Should run benchmark with verbose
        mock_runner.run_benchmark.assert_called_once_with(
            task_names=["task1"],
            output_dir=output_dir,
            model="anthropic/claude-sonnet-4-5",
            verbose=True,
        )

        assert result == output_dir

    @patch("agentready.cli.harbor.click.echo")
    @patch("agentready.cli.harbor.click.Abort")
    def test_run_handles_exception(self, mock_abort, mock_echo, tmp_path):
        """Test benchmark phase handles exceptions."""
        mock_runner = MagicMock()
        mock_runner.run_benchmark.side_effect = Exception("Benchmark failed")
        mock_toggler = MagicMock()

        with pytest.raises(Exception):
            _run_benchmark_phase(
                runner=mock_runner,
                toggler=mock_toggler,
                phase_name="TEST",
                run_number=1,
                output_dir=tmp_path,
                task_list=["task1"],
                model="anthropic/claude-sonnet-4-5",
                verbose=False,
                disable_agent=False,
            )


class TestGenerateReports:
    """Test _generate_reports helper function."""

    @patch("agentready.cli.harbor.generate_dashboard")
    @patch("agentready.cli.harbor.generate_markdown_report")
    @patch("agentready.cli.harbor._create_latest_symlinks")
    @patch("agentready.cli.harbor.click.echo")
    def test_generates_all_formats(
        self,
        mock_echo,
        mock_symlinks,
        mock_markdown,
        mock_dashboard,
        tmp_path,
        mock_comparison,
    ):
        """Test report generation creates JSON, Markdown, and HTML."""
        run_dir = tmp_path / "run_123"
        run_dir.mkdir()
        output_dir = tmp_path

        paths = _generate_reports(
            comparison=mock_comparison,
            run_dir=run_dir,
            output_dir=output_dir,
            timestamp="20240101_120000",
        )

        # Should generate all three formats
        assert "json" in paths
        assert "markdown" in paths
        assert "html" in paths

        # JSON file should exist
        assert paths["json"].exists()

        # Should call generators
        mock_markdown.assert_called_once()
        mock_dashboard.assert_called_once()
        mock_symlinks.assert_called_once()

    @patch("agentready.cli.harbor.generate_dashboard")
    @patch("agentready.cli.harbor.generate_markdown_report")
    @patch("agentready.cli.harbor._create_latest_symlinks")
    @patch("agentready.cli.harbor.click.echo")
    def test_json_content_valid(
        self,
        mock_echo,
        mock_symlinks,
        mock_markdown,
        mock_dashboard,
        tmp_path,
        mock_comparison,
    ):
        """Test JSON report contains valid comparison data."""
        run_dir = tmp_path / "run_123"
        run_dir.mkdir()

        paths = _generate_reports(
            comparison=mock_comparison,
            run_dir=run_dir,
            output_dir=tmp_path,
            timestamp="20240101_120000",
        )

        # Read and validate JSON
        with open(paths["json"]) as f:
            data = json.load(f)

        assert "created_at" in data
        assert "without_agent" in data
        assert "with_agent" in data
        assert "deltas" in data


class TestCreateLatestSymlinks:
    """Test _create_latest_symlinks helper function."""

    @patch("agentready.cli.harbor.click.echo")
    def test_creates_symlinks(self, mock_echo, tmp_path):
        """Test symlink creation for latest comparison."""
        # Create source files
        run_dir = tmp_path / "run_123"
        run_dir.mkdir()

        json_file = run_dir / "comparison_123.json"
        json_file.write_text("{}")

        md_file = run_dir / "comparison_123.md"
        md_file.write_text("# Report")

        html_file = run_dir / "comparison_123.html"
        html_file.write_text("<html></html>")

        paths = {
            "json": json_file,
            "markdown": md_file,
            "html": html_file,
        }

        # Create symlinks
        _create_latest_symlinks(paths, tmp_path)

        # Verify symlinks exist
        assert (tmp_path / "comparison_latest.json").is_symlink()
        assert (tmp_path / "comparison_latest.md").is_symlink()
        assert (tmp_path / "comparison_latest.html").is_symlink()

    @patch("agentready.cli.harbor.click.echo")
    def test_replaces_existing_symlinks(self, mock_echo, tmp_path):
        """Test symlink replacement for updates."""
        # Create old files
        old_dir = tmp_path / "run_old"
        old_dir.mkdir()
        old_file = old_dir / "comparison_old.json"
        old_file.write_text("{}")

        # Create old symlink
        old_symlink = tmp_path / "comparison_latest.json"
        old_symlink.symlink_to(old_file.relative_to(tmp_path))

        # Create new files
        new_dir = tmp_path / "run_new"
        new_dir.mkdir()
        new_file = new_dir / "comparison_new.json"
        new_file.write_text("{}")

        paths = {"json": new_file}

        # Update symlink
        _create_latest_symlinks(paths, tmp_path)

        # Symlink should point to new file
        assert old_symlink.is_symlink()
        assert old_symlink.resolve() == new_file.resolve()

    @patch("agentready.cli.harbor.click.echo")
    def test_handles_symlink_errors_gracefully(self, mock_echo, tmp_path):
        """Test symlink creation handles errors gracefully."""
        paths = {
            "json": tmp_path / "nonexistent.json",
        }

        # Should not raise exception
        _create_latest_symlinks(paths, tmp_path)


class TestCompareCommand:
    """Test harbor compare CLI command."""

    @patch("agentready.cli.harbor.HarborRunner")
    @patch("agentready.cli.harbor.AgentFileToggler")
    @patch("agentready.cli.harbor._run_benchmark_phase")
    @patch("agentready.cli.harbor.parse_harbor_results")
    @patch("agentready.cli.harbor.compare_runs")
    @patch("agentready.cli.harbor._generate_reports")
    @patch("agentready.cli.harbor.DashboardGenerator")
    def test_compare_basic_execution(
        self,
        mock_dashboard_gen,
        mock_gen_reports,
        mock_compare_runs,
        mock_parse,
        mock_run_phase,
        mock_toggler,
        mock_runner_class,
        runner,
        temp_repo,
        mock_task_results,
        mock_comparison,
    ):
        """Test basic compare command execution."""
        # Setup mocks
        mock_runner_class.return_value = MagicMock()
        mock_run_phase.return_value = temp_repo / "results"
        mock_parse.return_value = mock_task_results
        mock_compare_runs.return_value = mock_comparison
        mock_gen_reports.return_value = {"json": temp_repo / "comparison.json"}
        mock_dashboard_gen.return_value.generate_summary_text.return_value = "Summary"

        # Run command
        result = runner.invoke(
            compare,
            [
                "--task",
                "test-task-1",
                "--task",
                "test-task-2",
                "--agent-file",
                str(temp_repo / ".claude/agents/doubleagent.md"),
                "--output-dir",
                str(temp_repo / "output"),
            ],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "Harbor Benchmark Comparison" in result.output
        assert "Summary" in result.output

        # Should run benchmarks twice (with and without agent)
        assert mock_run_phase.call_count == 2

    def test_compare_missing_agent_file(self, runner, temp_repo):
        """Test compare command with missing agent file."""
        result = runner.invoke(
            compare,
            [
                "--task",
                "test-task",
                "--agent-file",
                str(temp_repo / "nonexistent.md"),
            ],
        )

        # Should fail (Click validates path before function runs)
        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_compare_no_tasks_specified(self, runner, temp_repo):
        """Test compare command without tasks."""
        result = runner.invoke(
            compare,
            [
                "--agent-file",
                str(temp_repo / ".claude/agents/doubleagent.md"),
            ],
        )

        # Should fail
        assert result.exit_code != 0
        assert "At least one task must be specified" in result.output

    @patch("agentready.cli.harbor.HarborRunner")
    def test_compare_harbor_not_installed(self, mock_runner_class, runner, temp_repo):
        """Test compare command when Harbor not installed."""
        from agentready.services.harbor.runner import HarborNotInstalledError

        mock_runner_class.side_effect = HarborNotInstalledError("Harbor not found")

        result = runner.invoke(
            compare,
            [
                "--task",
                "test-task",
                "--agent-file",
                str(temp_repo / ".claude/agents/doubleagent.md"),
            ],
        )

        # Should fail gracefully
        assert result.exit_code != 0
        assert "Harbor not found" in result.output

    @patch("agentready.cli.harbor.HarborRunner")
    @patch("agentready.cli.harbor.AgentFileToggler")
    @patch("agentready.cli.harbor._run_benchmark_phase")
    @patch("agentready.cli.harbor.parse_harbor_results")
    @patch("agentready.cli.harbor.compare_runs")
    @patch("agentready.cli.harbor._generate_reports")
    @patch("agentready.cli.harbor.DashboardGenerator")
    @patch("webbrowser.open")
    def test_compare_open_dashboard(
        self,
        mock_webbrowser_open,
        mock_dashboard_gen,
        mock_gen_reports,
        mock_compare_runs,
        mock_parse,
        mock_run_phase,
        mock_toggler,
        mock_runner_class,
        runner,
        temp_repo,
        mock_task_results,
        mock_comparison,
    ):
        """Test compare command with --open-dashboard flag."""
        # Setup mocks
        mock_runner_class.return_value = MagicMock()
        mock_run_phase.return_value = temp_repo / "results"
        mock_parse.return_value = mock_task_results
        mock_compare_runs.return_value = mock_comparison

        html_path = temp_repo / "comparison.html"
        html_path.write_text("<html></html>")
        mock_gen_reports.return_value = {"html": html_path}
        mock_dashboard_gen.return_value.generate_summary_text.return_value = "Summary"

        # Run command with open-dashboard flag
        result = runner.invoke(
            compare,
            [
                "--task",
                "test-task",
                "--agent-file",
                str(temp_repo / ".claude/agents/doubleagent.md"),
                "--open-dashboard",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should open browser
        mock_webbrowser_open.assert_called_once()

    @patch("agentready.cli.harbor.HarborRunner")
    @patch("agentready.cli.harbor.AgentFileToggler")
    @patch("agentready.cli.harbor._run_benchmark_phase")
    @patch("agentready.cli.harbor.parse_harbor_results")
    def test_compare_parse_results_failure(
        self,
        mock_parse,
        mock_run_phase,
        mock_toggler,
        mock_runner_class,
        runner,
        temp_repo,
    ):
        """Test compare command handles result parsing errors."""
        # Setup mocks
        mock_runner_class.return_value = MagicMock()
        mock_run_phase.return_value = temp_repo / "results"
        mock_parse.side_effect = Exception("Parse error")

        result = runner.invoke(
            compare,
            [
                "--task",
                "test-task",
                "--agent-file",
                str(temp_repo / ".claude/agents/doubleagent.md"),
            ],
        )

        # Should fail gracefully
        assert result.exit_code != 0
        assert "Failed to parse results" in result.output


class TestListComparisonsCommand:
    """Test harbor list CLI command."""

    def test_list_empty_directory(self, runner, tmp_path):
        """Test list command with no comparisons."""
        output_dir = tmp_path / "comparisons"
        output_dir.mkdir()

        result = runner.invoke(
            list_comparisons,
            ["--output-dir", str(output_dir)],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "No comparisons found" in result.output

    def test_list_with_comparisons(self, runner, tmp_path, mock_comparison):
        """Test list command with existing comparisons."""
        output_dir = tmp_path / "comparisons"
        output_dir.mkdir()

        # Create comparison files
        run1 = output_dir / "run_20240101_120000"
        run1.mkdir()
        comp1 = run1 / "comparison_20240101_120000.json"
        comp1.write_text(json.dumps(mock_comparison.to_dict()))

        run2 = output_dir / "run_20240102_120000"
        run2.mkdir()
        comp2 = run2 / "comparison_20240102_120000.json"
        comp2.write_text(json.dumps(mock_comparison.to_dict()))

        result = runner.invoke(
            list_comparisons,
            ["--output-dir", str(output_dir)],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "run_20240101_120000" in result.output
        assert "run_20240102_120000" in result.output
        assert "Success Δ:" in result.output
        assert "Duration Δ:" in result.output

    def test_list_nonexistent_directory(self, runner, tmp_path):
        """Test list command with nonexistent directory."""
        result = runner.invoke(
            list_comparisons,
            ["--output-dir", str(tmp_path / "nonexistent")],
        )

        # Should fail
        assert result.exit_code != 0


class TestViewComparisonCommand:
    """Test harbor view CLI command."""

    @patch("agentready.cli.harbor.DashboardGenerator")
    def test_view_summary_format(
        self, mock_dashboard_gen, runner, tmp_path, mock_comparison
    ):
        """Test view command with summary format."""
        # Create comparison file
        comp_file = tmp_path / "comparison.json"
        comp_file.write_text(json.dumps(mock_comparison.to_dict()))

        mock_dashboard_gen.return_value.generate_summary_text.return_value = (
            "Test Summary"
        )

        result = runner.invoke(
            view_comparison,
            [str(comp_file), "--format", "summary"],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "Test Summary" in result.output

    def test_view_full_format(self, runner, tmp_path, mock_comparison):
        """Test view command with full JSON format."""
        # Create comparison file
        comp_file = tmp_path / "comparison.json"
        comp_file.write_text(json.dumps(mock_comparison.to_dict()))

        result = runner.invoke(
            view_comparison,
            [str(comp_file), "--format", "full"],
        )

        # Should succeed
        assert result.exit_code == 0
        # Should output JSON
        assert "without_agent" in result.output
        assert "with_agent" in result.output

    def test_view_nonexistent_file(self, runner, tmp_path):
        """Test view command with nonexistent file."""
        result = runner.invoke(
            view_comparison,
            [str(tmp_path / "nonexistent.json")],
        )

        # Should fail
        assert result.exit_code != 0

    def test_view_default_format(self, runner, tmp_path, mock_comparison):
        """Test view command defaults to summary format."""
        comp_file = tmp_path / "comparison.json"
        comp_file.write_text(json.dumps(mock_comparison.to_dict()))

        with patch("agentready.cli.harbor.DashboardGenerator") as mock_gen:
            mock_gen.return_value.generate_summary_text.return_value = "Summary"

            result = runner.invoke(
                view_comparison,
                [str(comp_file)],
            )

            # Should use summary format by default
            assert result.exit_code == 0
            mock_gen.return_value.generate_summary_text.assert_called_once()


class TestHarborCLIGroup:
    """Test harbor CLI group."""

    def test_harbor_group_help(self, runner):
        """Test harbor CLI group shows help."""
        result = runner.invoke(harbor_cli, ["--help"])

        assert result.exit_code == 0
        assert "Harbor benchmark comparison commands" in result.output
        assert "compare" in result.output
        assert "list" in result.output
        assert "view" in result.output

    def test_harbor_group_has_commands(self):
        """Test harbor CLI group has expected commands."""
        assert "compare" in harbor_cli.commands
        assert "list" in harbor_cli.commands
        assert "view" in harbor_cli.commands
