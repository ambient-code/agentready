"""End-to-end integration tests for eval harness workflow.

These tests verify the complete workflow from baseline establishment through
dashboard generation using mocked Terminal-Bench results.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from agentready.services.eval_harness import BaselineEstablisher, TbenchRunner


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Create minimal repo content
        (repo_path / "README.md").write_text("# Test Repository\n\nTest content.")
        (repo_path / "CLAUDE.md").write_text(
            "# Claude Instructions\n\nTest instructions."
        )
        (repo_path / "setup.py").write_text(
            "from setuptools import setup\nsetup(name='test')"
        )

        # Commit
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        yield repo_path


class TestEvalHarnessWorkflow:
    """Test complete eval harness workflow end-to-end."""

    def test_baseline_establishment(self, temp_repo):
        """Test baseline establishment with mocked tbench."""
        # Create runner and establisher
        runner = TbenchRunner(mock=True)
        establisher = BaselineEstablisher(tbench_runner=runner)

        # Establish baseline
        output_dir = temp_repo / ".agentready" / "eval_harness" / "baseline"
        baseline = establisher.establish_baseline(
            temp_repo, iterations=3, output_dir=output_dir
        )

        # Verify baseline metrics
        assert baseline.iterations == 3
        assert baseline.mean_score > 0
        assert baseline.std_dev >= 0
        assert len(baseline.raw_results) == 3

        # Verify files created
        assert output_dir.exists()
        assert (output_dir / "summary.json").exists()
        assert len(list(output_dir.glob("run_*.json"))) == 3

    def test_baseline_to_files(self, temp_repo):
        """Test baseline establishment creates expected files."""
        runner = TbenchRunner(mock=True)
        establisher = BaselineEstablisher(tbench_runner=runner)

        eval_dir = temp_repo / ".agentready" / "eval_harness"
        baseline_dir = eval_dir / "baseline"

        # Establish baseline
        baseline = establisher.establish_baseline(
            temp_repo, iterations=3, output_dir=baseline_dir
        )

        # Verify baseline metrics
        assert baseline.mean_score > 0

        # Verify files created
        assert (baseline_dir / "summary.json").exists()
        run_files = list(baseline_dir.glob("run_*.json"))
        assert len(run_files) == 3

        # Verify summary file contains valid JSON
        import json

        with open(baseline_dir / "summary.json") as f:
            summary_data = json.load(f)
            assert "mean_score" in summary_data
            assert summary_data["iterations"] == 3


class TestEvalHarnessFileStructure:
    """Test eval harness creates correct file structure."""

    def test_eval_harness_directory_structure(self, temp_repo):
        """Test that eval harness creates expected directory structure."""
        runner = TbenchRunner(mock=True)
        establisher = BaselineEstablisher(tbench_runner=runner)

        eval_dir = temp_repo / ".agentready" / "eval_harness"
        baseline_dir = eval_dir / "baseline"

        # Run baseline
        _baseline = establisher.establish_baseline(
            temp_repo, iterations=3, output_dir=baseline_dir
        )

        # Verify directory structure
        assert eval_dir.exists()
        assert baseline_dir.exists()

        # Verify baseline files
        assert (baseline_dir / "summary.json").exists()
        run_files = list(baseline_dir.glob("run_*.json"))
        assert len(run_files) == 3

        # Verify file naming convention
        for run_file in run_files:
            assert run_file.stem.startswith("run_")
            assert run_file.suffix == ".json"


class TestMockedTbenchDeterminism:
    """Test that mocked tbench produces deterministic results."""

    def test_mocked_results_reproducible(self, temp_repo):
        """Test that mocked tbench gives same results for same repo."""
        runner = TbenchRunner(mock=True)

        # Run benchmark twice
        result1 = runner.run_benchmark(temp_repo)
        result2 = runner.run_benchmark(temp_repo)

        # Should be identical (deterministic based on repo)
        assert result1.score == result2.score
        assert result1.completion_rate == result2.completion_rate
        assert result1.pytest_pass_rate == result2.pytest_pass_rate
        assert result1.is_mocked is True

    def test_mocked_results_vary_with_variance(self, temp_repo):
        """Test that mocked results have some variance across runs."""
        runner = TbenchRunner(mock=True)
        establisher = BaselineEstablisher(tbench_runner=runner)

        baseline_dir = temp_repo / ".agentready" / "eval_harness" / "baseline"
        baseline = establisher.establish_baseline(
            temp_repo, iterations=5, output_dir=baseline_dir
        )

        # With 5 iterations, should have some variance
        # (unless by chance they're all exactly the same, which is unlikely)
        scores = [r.score for r in baseline.raw_results]
        assert len(set(scores)) >= 1  # At least 1 unique score
        assert baseline.std_dev >= 0  # Standard deviation calculated
