"""Unit tests for benchmark CLI commands.

Test Strategy:
    - Uses Click's CliRunner with isolated filesystem for CLI command testing
    - Mocks external dependencies (_real_tbench_result, compare_assessor_impact)
    - Uses actual data models (HarborComparison, HarborRunMetrics) for type safety
    - Tests both high-level commands (benchmark, validate_assessor) and internal helpers (_run_tbench)
    - Covers CLI argument parsing, validation, and error handling

Coverage Target:
    - Achieves 80% coverage of cli/benchmark.py
    - All commands (benchmark, validate-assessor) tested
    - Helper functions (_run_tbench) tested independently
    - Edge cases: missing API keys, invalid inputs, file system operations

Test Fixtures:
    - runner: Click test runner for CLI command invocation
    - temp_repo: Temporary git repository structure
    - mock_tbench_result: Mock Terminal-Bench evaluation result
    - mock_comparison: Harbor comparison for assessor validation testing

Note on Directory Creation:
    Tests create output directories explicitly before invocation to match
    real-world usage where the CLI creates directories on demand.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentready.cli.benchmark import (
    DEFAULT_PHASE1_TASKS,
    _run_tbench,
    benchmark,
    validate_assessor,
)
from agentready.models.harbor import HarborComparison, HarborRunMetrics


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()
        yield repo_path


@pytest.fixture
def mock_tbench_result():
    """Create mock Terminal-Bench result."""
    result = MagicMock()
    result.score = 75.5
    result.task_solved = 10
    result.resolved_trials = 10
    result.unresolved_trials = 0
    result.pass_at_1 = 0.90
    result.trajectory_path = "/path/to/trajectory.json"
    return result


@pytest.fixture
def mock_comparison():
    """Create mock Harbor comparison for assessor validation.

    Simulates assessor A/B test results showing:
    - Baseline (assessor fails): 50% success rate
    - Treatment (assessor passes): 100% success rate
    - Impact: +50pp success rate when assessor criteria met
    """
    # Baseline: assessor forced to fail
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

    # Treatment: assessor passes normally
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

    return HarborComparison(
        created_at="2024-01-01T12:00:00",  # Fixed timestamp for test determinism
        without_agent=without_metrics,
        with_agent=with_metrics,
        deltas={
            "success_rate_delta": 50.0,
            "avg_duration_delta_sec": -2.5,
            "avg_duration_delta_pct": -20.0,
        },
        statistical_significance={
            "success_rate_significant": True,
            "duration_significant": False,
        },
        per_task_comparison=[],
    )


class TestBenchmarkCommand:
    """Test benchmark CLI command."""

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_basic_execution(self, mock_run, runner, temp_repo):
        """Test basic benchmark command execution."""
        result = runner.invoke(
            benchmark,
            [str(temp_repo), "--harness", "tbench", "--subset", "smoketest"],
        )

        # Should succeed
        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_defaults_to_current_dir(self, mock_run, runner):
        """Test benchmark defaults to current directory."""
        with runner.isolated_filesystem():
            Path(".git").mkdir()

            result = runner.invoke(
                benchmark,
                ["--subset", "smoketest"],
            )

            # Should use current directory
            assert result.exit_code == 0
            mock_run.assert_called_once()

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_with_verbose_flag(self, mock_run, runner, temp_repo):
        """Test benchmark command with verbose output."""
        result = runner.invoke(
            benchmark,
            [str(temp_repo), "--verbose", "--subset", "smoketest"],
        )

        assert result.exit_code == 0
        # Verbose flag passed to _run_tbench
        _, _, _, verbose, _, _, _ = mock_run.call_args[0]
        assert verbose is True

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_with_custom_timeout(self, mock_run, runner, temp_repo):
        """Test benchmark with custom timeout."""
        result = runner.invoke(
            benchmark,
            [str(temp_repo), "--timeout", "7200", "--subset", "smoketest"],
        )

        assert result.exit_code == 0
        _, _, _, _, timeout, _, _ = mock_run.call_args[0]
        assert timeout == 7200

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_with_output_dir(self, mock_run, runner, temp_repo):
        """Test benchmark with custom output directory."""
        result = runner.invoke(
            benchmark,
            [
                str(temp_repo),
                "--output-dir",
                "/custom/output",
                "--subset",
                "smoketest",
            ],
        )

        assert result.exit_code == 0
        _, _, _, _, _, output_dir, _ = mock_run.call_args[0]
        assert output_dir == "/custom/output"

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_skip_preflight(self, mock_run, runner, temp_repo):
        """Test benchmark with skip-preflight flag."""
        result = runner.invoke(
            benchmark,
            [str(temp_repo), "--skip-preflight", "--subset", "smoketest"],
        )

        assert result.exit_code == 0
        _, _, _, _, _, _, skip_preflight = mock_run.call_args[0]
        assert skip_preflight is True

    def test_benchmark_unknown_harness(self, runner, temp_repo):
        """Test benchmark with unknown harness."""
        result = runner.invoke(
            benchmark,
            [str(temp_repo), "--harness", "unknown"],
        )

        # Should fail (but unknown won't be accepted by Click's Choice validation)
        assert result.exit_code != 0

    @patch("agentready.cli.benchmark._run_tbench")
    def test_benchmark_with_model_selection(self, mock_run, runner, temp_repo):
        """Test benchmark with different models."""
        result = runner.invoke(
            benchmark,
            [
                str(temp_repo),
                "--model",
                "claude-sonnet-4-5",
                "--subset",
                "smoketest",
            ],
        )

        assert result.exit_code == 0
        _, _, model, _, _, _, _ = mock_run.call_args[0]
        assert model == "claude-sonnet-4-5"


class TestRunTbench:
    """Test _run_tbench internal function."""

    @patch("agentready.cli.benchmark._real_tbench_result")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_run_tbench_smoketest(self, mock_result, tmp_path, mock_tbench_result):
        """Test running tbench with smoketest subset."""
        mock_result.return_value = mock_tbench_result

        # Create mock repository
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        # Should not raise
        _run_tbench(
            repo_path=repo_path,
            subset="smoketest",
            model="claude-haiku-4-5",
            verbose=False,
            timeout=3600,
            output_dir=None,
            skip_preflight=True,  # Skip preflight to avoid dependencies
        )

        # Should call _real_tbench_result
        mock_result.assert_called_once()

    @patch("agentready.cli.benchmark._real_tbench_result")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_run_tbench_full_subset(self, mock_result, tmp_path, mock_tbench_result):
        """Test running tbench with full subset."""
        mock_result.return_value = mock_tbench_result

        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        _run_tbench(
            repo_path=repo_path,
            subset="full",
            model="claude-haiku-4-5",
            verbose=False,
            timeout=3600,
            output_dir=None,
            skip_preflight=True,
        )

        mock_result.assert_called_once()

    @patch("agentready.cli.benchmark.click.echo")
    @patch("agentready.cli.benchmark.click.Abort")
    def test_run_tbench_invalid_subset(self, mock_abort, mock_echo, tmp_path):
        """Test tbench with invalid subset."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with pytest.raises(Exception):
            _run_tbench(
                repo_path=repo_path,
                subset="invalid",
                model="claude-haiku-4-5",
                verbose=False,
                timeout=3600,
                output_dir=None,
                skip_preflight=True,
            )

    @patch.dict("os.environ", {}, clear=True)
    @patch("agentready.cli.benchmark.click.echo")
    @patch("agentready.cli.benchmark.click.Abort")
    def test_run_tbench_missing_api_key(self, mock_abort, mock_echo, tmp_path):
        """Test tbench fails without API key."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with pytest.raises(Exception):
            _run_tbench(
                repo_path=repo_path,
                subset="smoketest",
                model="claude-haiku-4-5",
                verbose=False,
                timeout=3600,
                output_dir=None,
                skip_preflight=True,
            )

    @patch("agentready.cli.benchmark._real_tbench_result")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_run_tbench_defaults_to_full(
        self, mock_result, tmp_path, mock_tbench_result
    ):
        """Test tbench defaults to full subset when None specified."""
        mock_result.return_value = mock_tbench_result

        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        _run_tbench(
            repo_path=repo_path,
            subset=None,  # Should default to 'full'
            model="claude-haiku-4-5",
            verbose=False,
            timeout=3600,
            output_dir=None,
            skip_preflight=True,
        )

        # Check that HarborConfig was created with smoketest=False
        mock_result.assert_called_once()
        harbor_config = mock_result.call_args[0][1]
        assert harbor_config.smoketest is False

    @patch("agentready.cli.benchmark._real_tbench_result")
    @patch("agentready.cli.benchmark.click.echo")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_run_tbench_exception_handling(self, mock_echo, mock_result, tmp_path):
        """Test tbench handles exceptions gracefully."""
        mock_result.side_effect = Exception("Benchmark error")

        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with pytest.raises(Exception):
            _run_tbench(
                repo_path=repo_path,
                subset="smoketest",
                model="claude-haiku-4-5",
                verbose=False,
                timeout=3600,
                output_dir=None,
                skip_preflight=True,
            )


class TestValidateAssessorCommand:
    """Test validate-assessor CLI command."""

    @patch("agentready.cli.benchmark.AssessorStateToggler")
    def test_list_assessors(self, mock_toggler_class, runner):
        """Test --list-assessors flag."""
        mock_toggler = MagicMock()
        mock_toggler.list_supported_assessors.return_value = [
            "claude_md_file",
            "readme_structure",
            "test_coverage",
        ]
        mock_toggler_class.return_value = mock_toggler

        result = runner.invoke(validate_assessor, ["--list-assessors"])

        # Should succeed
        assert result.exit_code == 0
        assert "claude_md_file" in result.output
        assert "readme_structure" in result.output
        assert "test_coverage" in result.output

    def test_validate_missing_assessor_flag(self, runner):
        """Test validate-assessor without --assessor flag."""
        result = runner.invoke(validate_assessor, [])

        # Should fail
        assert result.exit_code != 0
        assert "Missing required option" in result.output

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_basic(self, mock_compare, runner, mock_comparison):
        """Test basic assessor validation."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/claude_md_file").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                ["--assessor", "claude_md_file", "--smoketest"],
            )

            # Should succeed
            assert result.exit_code == 0
            assert "Results saved" in result.output
            mock_compare.assert_called_once()

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_with_custom_tasks(
        self, mock_compare, runner, mock_comparison
    ):
        """Test validation with custom tasks."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/readme_structure").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                [
                    "--assessor",
                    "readme_structure",
                    "--tasks",
                    "adaptive-rejection-sampler",
                    "--tasks",
                    "async-http-client",
                ],
            )

            assert result.exit_code == 0
            # Check that custom tasks were passed
            _, kwargs = mock_compare.call_args
            assert kwargs["task_names"] == [
                "adaptive-rejection-sampler",
                "async-http-client",
            ]

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_with_runs(self, mock_compare, runner, mock_comparison):
        """Test validation with custom number of runs."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/test_coverage").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                ["--assessor", "test_coverage", "--runs", "5", "--smoketest"],
            )

            assert result.exit_code == 0
            _, kwargs = mock_compare.call_args
            assert kwargs["runs_per_task"] == 5

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_default_tasks(
        self, mock_compare, runner, mock_comparison
    ):
        """Test validation uses default Phase 1 tasks."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/claude_md_file").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                ["--assessor", "claude_md_file"],
            )

            assert result.exit_code == 0
            # Should use DEFAULT_PHASE1_TASKS
            _, kwargs = mock_compare.call_args
            assert kwargs["task_names"] == DEFAULT_PHASE1_TASKS

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_smoketest_mode(
        self, mock_compare, runner, mock_comparison
    ):
        """Test smoketest mode uses single task."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/claude_md_file").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                ["--assessor", "claude_md_file", "--smoketest"],
            )

            assert result.exit_code == 0
            # Smoketest should use only 1 task
            _, kwargs = mock_compare.call_args
            assert kwargs["task_names"] == ["adaptive-rejection-sampler"]

    @patch.dict("os.environ", {}, clear=True)
    def test_validate_assessor_missing_api_key(self, runner):
        """Test validation fails without API key."""
        result = runner.invoke(
            validate_assessor,
            ["--assessor", "claude_md_file"],
        )

        # Should fail
        assert result.exit_code != 0
        assert "ANTHROPIC_API_KEY" in result.output

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_value_error(self, mock_compare, runner):
        """Test validation handles unsupported assessor."""
        mock_compare.side_effect = ValueError("Unsupported assessor")

        result = runner.invoke(
            validate_assessor,
            ["--assessor", "invalid_assessor", "--smoketest"],
        )

        # Should fail gracefully
        assert result.exit_code != 0
        assert "Error:" in result.output

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_creates_output_files(
        self, mock_compare, runner, mock_comparison
    ):
        """Test validation creates JSON and Markdown files."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            output_dir = Path("output")
            # Create output directory structure
            output_dir.mkdir(parents=True, exist_ok=True)

            result = runner.invoke(
                validate_assessor,
                [
                    "--assessor",
                    "claude_md_file",
                    "--output-dir",
                    str(output_dir),
                    "--smoketest",
                ],
            )

            assert result.exit_code == 0
            # Check files were created
            assert (output_dir / "claude_md_file.json").exists()
            assert (output_dir / "claude_md_file.md").exists()

    @patch("agentready.cli.benchmark.compare_assessor_impact")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_validate_assessor_concurrent_flag(
        self, mock_compare, runner, mock_comparison
    ):
        """Test validation with concurrent tasks."""
        mock_compare.return_value = mock_comparison

        with runner.isolated_filesystem():
            # Create output directory structure
            Path(".agentready/validations/claude_md_file").mkdir(
                parents=True, exist_ok=True
            )

            result = runner.invoke(
                validate_assessor,
                ["--assessor", "claude_md_file", "--concurrent", "5", "--smoketest"],
            )

            assert result.exit_code == 0
            _, kwargs = mock_compare.call_args
            assert kwargs["n_concurrent"] == 5


class TestPhase1Tasks:
    """Test DEFAULT_PHASE1_TASKS constant."""

    def test_phase1_tasks_defined(self):
        """Test that Phase 1 tasks are defined."""
        assert len(DEFAULT_PHASE1_TASKS) == 8
        assert "adaptive-rejection-sampler" in DEFAULT_PHASE1_TASKS
        assert "async-http-client" in DEFAULT_PHASE1_TASKS

    def test_phase1_tasks_diversity(self):
        """Test that Phase 1 tasks cover diverse categories."""
        # Just check that we have a good variety
        assert all(isinstance(task, str) for task in DEFAULT_PHASE1_TASKS)
        assert all("-" in task for task in DEFAULT_PHASE1_TASKS)
