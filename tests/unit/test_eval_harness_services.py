"""Unit tests for eval harness services."""

import tempfile
from pathlib import Path

import git
import pytest

from agentready.models.eval_harness import AssessorImpact, BaselineMetrics, EvalSummary
from agentready.services.eval_harness import (
    AssessorTester,
    BaselineEstablisher,
    ResultsAggregator,
    TbenchRunner,
)


class TestTbenchRunner:
    """Tests for TbenchRunner."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()

            # Initialize git repo
            repo = git.Repo.init(repo_path)

            # Create a simple file
            test_file = repo_path / "test.py"
            test_file.write_text("print('hello')\n" * 100)

            # Commit
            repo.index.add(["test.py"])
            repo.index.commit("Initial commit")

            yield repo_path

    def test_create_runner_mock(self):
        """Test creating a mocked runner."""
        runner = TbenchRunner(mock=True)
        assert runner.mock is True

    def test_create_runner_real_raises_not_implemented(self):
        """Test that real runner raises NotImplementedError."""
        runner = TbenchRunner(mock=False)
        assert runner.mock is False

    def test_run_benchmark_on_invalid_repo_raises(self):
        """Test that non-git repo raises ValueError."""
        runner = TbenchRunner(mock=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            non_repo = Path(tmpdir)
            with pytest.raises(ValueError, match="Not a git repository"):
                runner.run_benchmark(non_repo)

    def test_mock_tbench_result(self, temp_repo):
        """Test mocked tbench result generation."""
        runner = TbenchRunner(mock=True)
        result = runner.run_benchmark(temp_repo)

        # Check structure
        assert hasattr(result, "score")
        assert hasattr(result, "completion_rate")
        assert hasattr(result, "pytest_pass_rate")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "is_mocked")

        # Check values are reasonable
        assert 0.0 <= result.score <= 100.0
        assert 0.0 <= result.completion_rate <= 100.0
        assert 0.0 <= result.pytest_pass_rate <= 100.0
        assert result.latency_ms > 0
        assert result.is_mocked is True

    def test_deterministic_scores(self, temp_repo):
        """Test that same repo produces same score (deterministic)."""
        runner = TbenchRunner(mock=True)

        # Run twice
        result1 = runner.run_benchmark(temp_repo)
        result2 = runner.run_benchmark(temp_repo)

        # Scores should be identical (seeded from commit hash)
        assert result1.score == result2.score
        assert result1.completion_rate == result2.completion_rate
        assert result1.pytest_pass_rate == result2.pytest_pass_rate

    def test_real_runner_not_implemented(self, temp_repo):
        """Test that real runner raises NotImplementedError."""
        runner = TbenchRunner(mock=False)

        with pytest.raises(NotImplementedError, match="Real Terminal-Bench"):
            runner.run_benchmark(temp_repo)


class TestBaselineEstablisher:
    """Tests for BaselineEstablisher."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()

            # Initialize git repo
            repo = git.Repo.init(repo_path)

            # Create a simple file
            test_file = repo_path / "test.py"
            test_file.write_text("print('hello')\n" * 100)

            # Commit
            repo.index.add(["test.py"])
            repo.index.commit("Initial commit")

            yield repo_path

    def test_create_establisher_with_default_runner(self):
        """Test creating establisher with default runner."""
        establisher = BaselineEstablisher()
        assert establisher.tbench_runner is not None
        assert establisher.tbench_runner.mock is True

    def test_create_establisher_with_custom_runner(self):
        """Test creating establisher with custom runner."""
        custom_runner = TbenchRunner(mock=True)
        establisher = BaselineEstablisher(tbench_runner=custom_runner)
        assert establisher.tbench_runner is custom_runner

    def test_establish_baseline(self, temp_repo):
        """Test baseline establishment."""
        establisher = BaselineEstablisher()
        baseline = establisher.establish_baseline(temp_repo, iterations=3)

        # Check structure
        assert isinstance(baseline, BaselineMetrics)
        assert baseline.iterations == 3
        assert len(baseline.raw_results) == 3

        # Check statistics were calculated
        assert baseline.mean_score > 0
        assert baseline.median_score > 0
        assert baseline.min_score <= baseline.mean_score <= baseline.max_score

    def test_establish_baseline_saves_files(self, temp_repo):
        """Test that baseline establishment saves result files."""
        establisher = BaselineEstablisher()
        output_dir = temp_repo / ".agentready" / "eval_harness" / "baseline"

        _baseline = establisher.establish_baseline(
            temp_repo, iterations=3, output_dir=output_dir
        )

        # Check files were created
        assert (output_dir / "summary.json").exists()
        assert (output_dir / "run_001.json").exists()
        assert (output_dir / "run_002.json").exists()
        assert (output_dir / "run_003.json").exists()

    def test_establish_baseline_invalid_iterations(self, temp_repo):
        """Test that invalid iterations raises ValueError."""
        establisher = BaselineEstablisher()

        with pytest.raises(ValueError, match="Iterations must be >= 1"):
            establisher.establish_baseline(temp_repo, iterations=0)

    def test_establish_baseline_invalid_repo(self):
        """Test that invalid repo path raises ValueError."""
        establisher = BaselineEstablisher()

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "does-not-exist"
            with pytest.raises(ValueError, match="does not exist"):
                establisher.establish_baseline(non_existent)

    def test_load_baseline(self, temp_repo):
        """Test loading previously established baseline."""
        establisher = BaselineEstablisher()
        output_dir = temp_repo / ".agentready" / "eval_harness" / "baseline"

        # Establish baseline first
        original = establisher.establish_baseline(
            temp_repo, iterations=3, output_dir=output_dir
        )

        # Load it back
        loaded = establisher.load_baseline(output_dir)

        # Check values match
        assert loaded.mean_score == original.mean_score
        assert loaded.std_dev == original.std_dev
        assert loaded.iterations == original.iterations

    def test_load_baseline_not_found(self):
        """Test that loading non-existent baseline raises error."""
        establisher = BaselineEstablisher()

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "not-here"
            with pytest.raises(FileNotFoundError, match="Baseline summary not found"):
                establisher.load_baseline(non_existent)

    def test_baseline_variance(self, temp_repo):
        """Test that baseline has low variance (std dev).

        Mocked scores should be deterministic, so std dev should be 0
        when run on the same repo commit.
        """
        establisher = BaselineEstablisher()
        baseline = establisher.establish_baseline(temp_repo, iterations=5)

        # For deterministic mocking, std dev should be exactly 0
        assert baseline.std_dev == 0.0


class TestAssessorTester:
    """Tests for AssessorTester."""

    @pytest.fixture
    def temp_repo_with_missing_claude_md(self):
        """Create a temp repo missing CLAUDE.md (for claude_md_file assessor)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()

            # Initialize git repo
            repo = git.Repo.init(repo_path)

            # Create README.md (but not CLAUDE.md)
            readme = repo_path / "README.md"
            readme.write_text("# Test Repo\n\nThis is a test.\n")

            # Create .gitignore
            gitignore = repo_path / ".gitignore"
            gitignore.write_text("*.pyc\n__pycache__/\n")

            # Create some Python files
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("print('hello')\n" * 50)

            # Commit
            repo.index.add([".gitignore", "README.md", "src/main.py"])
            repo.index.commit("Initial commit")

            yield repo_path

    @pytest.fixture
    def baseline_metrics(self):
        """Create baseline metrics for testing."""
        from datetime import datetime

        from agentready.models.eval_harness import TbenchResult

        results = [
            TbenchResult(
                score=70.0,
                completion_rate=68.0,
                pytest_pass_rate=75.0,
                latency_ms=2500.0,
                timestamp=datetime.now(),
                is_mocked=True,
            )
            for _ in range(5)
        ]
        return BaselineMetrics.from_results(results)

    def test_create_tester_with_default_runner(self):
        """Test creating tester with default runner."""
        tester = AssessorTester()
        assert tester.tbench_runner is not None
        assert tester.tbench_runner.mock is True
        assert tester.fixer_service is not None

    def test_create_tester_with_custom_runner(self):
        """Test creating tester with custom runner."""
        custom_runner = TbenchRunner(mock=True)
        tester = AssessorTester(tbench_runner=custom_runner)
        assert tester.tbench_runner is custom_runner

    def test_test_assessor_invalid_id_raises(
        self, temp_repo_with_missing_claude_md, baseline_metrics
    ):
        """Test that invalid assessor ID raises ValueError."""
        tester = AssessorTester()

        with pytest.raises(ValueError, match="Assessor 'invalid_id' not found"):
            tester.test_assessor(
                "invalid_id",
                temp_repo_with_missing_claude_md,
                baseline_metrics,
                iterations=3,
            )

    def test_test_assessor_valid(
        self, temp_repo_with_missing_claude_md, baseline_metrics
    ):
        """Test testing a valid assessor (claude_md_file)."""
        tester = AssessorTester()

        impact = tester.test_assessor(
            "claude_md_file",
            temp_repo_with_missing_claude_md,
            baseline_metrics,
            iterations=3,
        )

        # Check structure
        assert isinstance(impact, AssessorImpact)
        assert impact.assessor_id == "claude_md_file"
        assert impact.assessor_name == "CLAUDE.md Configuration Files"
        assert impact.tier == 1

        # Check scores
        assert impact.baseline_score == baseline_metrics.mean_score
        assert impact.post_remediation_score > 0
        assert impact.iterations == 3

        # Check statistics
        assert impact.p_value >= 0
        assert isinstance(impact.effect_size, float)
        assert isinstance(impact.is_significant, bool)

        # Check remediation
        assert impact.fixes_applied >= 0
        assert len(impact.remediation_log) > 0

    def test_test_assessor_saves_files(
        self, temp_repo_with_missing_claude_md, baseline_metrics
    ):
        """Test that assessor testing saves result files."""
        tester = AssessorTester()
        output_dir = (
            temp_repo_with_missing_claude_md
            / ".agentready"
            / "eval_harness"
            / "claude_md_file"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        _impact = tester.test_assessor(
            "claude_md_file",
            temp_repo_with_missing_claude_md,
            baseline_metrics,
            iterations=3,
            output_dir=output_dir,
        )

        # Check files were created
        assert (output_dir / "impact.json").exists()
        assert (output_dir / "run_001.json").exists()
        assert (output_dir / "run_002.json").exists()
        assert (output_dir / "run_003.json").exists()

    def test_calculate_cohens_d_positive(self):
        """Test Cohen's d calculation for improvement."""
        baseline = [70.0, 71.0, 69.0, 70.5, 70.0]
        post = [75.0, 76.0, 74.0, 75.5, 75.0]

        d = AssessorTester._calculate_cohens_d(baseline, post)

        # Should be positive (improvement)
        assert d > 0
        # Should be large effect (|d| >= 0.8)
        assert abs(d) >= 0.8

    def test_calculate_cohens_d_negative(self):
        """Test Cohen's d calculation for regression."""
        baseline = [75.0, 76.0, 74.0, 75.5, 75.0]
        post = [70.0, 71.0, 69.0, 70.5, 70.0]

        d = AssessorTester._calculate_cohens_d(baseline, post)

        # Should be negative (regression)
        assert d < 0
        # Should be large effect (|d| >= 0.8)
        assert abs(d) >= 0.8

    def test_calculate_cohens_d_no_change(self):
        """Test Cohen's d when scores are identical."""
        baseline = [70.0] * 5
        post = [70.0] * 5

        d = AssessorTester._calculate_cohens_d(baseline, post)

        # Should be 0 (no change)
        assert d == 0.0

    def test_calculate_cohens_d_insufficient_samples(self):
        """Test Cohen's d with insufficient samples."""
        baseline = [70.0]  # Only 1 sample
        post = [75.0, 76.0]

        d = AssessorTester._calculate_cohens_d(baseline, post)

        # Should return 0 (not enough samples)
        assert d == 0.0


class TestResultsAggregator:
    """Tests for ResultsAggregator."""

    @pytest.fixture
    def eval_harness_structure(self):
        """Create complete eval harness directory structure with results."""
        from datetime import datetime

        from agentready.models.eval_harness import TbenchResult, save_to_json

        with tempfile.TemporaryDirectory() as tmpdir:
            eval_dir = Path(tmpdir) / "eval_harness"
            eval_dir.mkdir()

            # Create baseline
            baseline_dir = eval_dir / "baseline"
            baseline_dir.mkdir()

            baseline_results = [
                TbenchResult(
                    score=70.0,
                    completion_rate=68.0,
                    pytest_pass_rate=75.0,
                    latency_ms=2500.0,
                    timestamp=datetime.now(),
                    is_mocked=True,
                )
                for _ in range(5)
            ]
            baseline = BaselineMetrics.from_results(baseline_results)
            save_to_json(baseline, baseline_dir / "summary.json")

            # Create assessor impacts
            assessors_dir = eval_dir / "assessors"
            assessors_dir.mkdir()

            # Assessor 1: claude_md_file (Tier 1, small positive impact)
            claude_dir = assessors_dir / "claude_md_file"
            claude_dir.mkdir()
            claude_impact = AssessorImpact(
                assessor_id="claude_md_file",
                assessor_name="CLAUDE.md Configuration Files",
                tier=1,
                baseline_score=70.0,
                post_remediation_score=72.0,
                delta_score=2.0,
                p_value=0.01,
                effect_size=0.3,
                is_significant=True,
                iterations=5,
                fixes_applied=1,
                remediation_log=["Created CLAUDE.md"],
            )
            save_to_json(claude_impact, claude_dir / "impact.json")

            # Assessor 2: readme_structure (Tier 1, large positive impact)
            readme_dir = assessors_dir / "readme_structure"
            readme_dir.mkdir()
            readme_impact = AssessorImpact(
                assessor_id="readme_structure",
                assessor_name="README Structure",
                tier=1,
                baseline_score=70.0,
                post_remediation_score=80.0,
                delta_score=10.0,
                p_value=0.001,
                effect_size=1.2,
                is_significant=True,
                iterations=5,
                fixes_applied=3,
                remediation_log=["Updated README", "Added sections", "Fixed links"],
            )
            save_to_json(readme_impact, readme_dir / "impact.json")

            # Assessor 3: pre_commit_hooks (Tier 2, no impact)
            precommit_dir = assessors_dir / "pre_commit_hooks"
            precommit_dir.mkdir()
            precommit_impact = AssessorImpact(
                assessor_id="pre_commit_hooks",
                assessor_name="Pre-commit Hooks",
                tier=2,
                baseline_score=70.0,
                post_remediation_score=70.0,
                delta_score=0.0,
                p_value=1.0,
                effect_size=0.0,
                is_significant=False,
                iterations=5,
                fixes_applied=0,
                remediation_log=["No fixes available"],
            )
            save_to_json(precommit_impact, precommit_dir / "impact.json")

            yield eval_dir

    def test_create_aggregator(self):
        """Test creating aggregator."""
        aggregator = ResultsAggregator()
        assert aggregator is not None

    def test_aggregate_missing_directory_raises(self):
        """Test that missing eval harness directory raises error."""
        aggregator = ResultsAggregator()

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "does-not-exist"
            with pytest.raises(
                FileNotFoundError, match="Eval harness directory not found"
            ):
                aggregator.aggregate(non_existent)

    def test_aggregate_missing_baseline_raises(self):
        """Test that missing baseline raises error."""
        aggregator = ResultsAggregator()

        with tempfile.TemporaryDirectory() as tmpdir:
            eval_dir = Path(tmpdir) / "eval_harness"
            eval_dir.mkdir()
            # Create assessors dir but no baseline
            (eval_dir / "assessors").mkdir()

            with pytest.raises(FileNotFoundError, match="Baseline directory not found"):
                aggregator.aggregate(eval_dir)

    def test_aggregate_no_assessor_results_raises(self):
        """Test that no assessor results raises error."""
        from agentready.models.eval_harness import TbenchResult, save_to_json

        aggregator = ResultsAggregator()

        with tempfile.TemporaryDirectory() as tmpdir:
            eval_dir = Path(tmpdir) / "eval_harness"
            eval_dir.mkdir()

            # Create baseline
            baseline_dir = eval_dir / "baseline"
            baseline_dir.mkdir()
            baseline_results = [
                TbenchResult(
                    score=70.0,
                    completion_rate=68.0,
                    pytest_pass_rate=75.0,
                    latency_ms=2500.0,
                    timestamp=__import__("datetime").datetime.now(),
                    is_mocked=True,
                )
                for _ in range(3)
            ]
            baseline = BaselineMetrics.from_results(baseline_results)
            save_to_json(baseline, baseline_dir / "summary.json")

            # Create empty assessors dir
            (eval_dir / "assessors").mkdir()

            with pytest.raises(FileNotFoundError, match="No assessor results found"):
                aggregator.aggregate(eval_dir)

    def test_aggregate_valid_structure(self, eval_harness_structure):
        """Test aggregation with valid structure."""
        aggregator = ResultsAggregator()
        summary = aggregator.aggregate(eval_harness_structure)

        # Check structure
        assert isinstance(summary, EvalSummary)
        assert summary.total_assessors_tested == 3
        assert (
            summary.significant_improvements == 2
        )  # claude_md_file and readme_structure

        # Check baseline
        assert summary.baseline.mean_score == 70.0

        # Check assessor impacts
        assert len(summary.assessor_impacts) == 3
        assessor_ids = [i.assessor_id for i in summary.assessor_impacts]
        assert "claude_md_file" in assessor_ids
        assert "readme_structure" in assessor_ids
        assert "pre_commit_hooks" in assessor_ids

        # Check tier impacts
        assert 1 in summary.tier_impacts
        assert 2 in summary.tier_impacts
        # Tier 1 average: (2.0 + 10.0) / 2 = 6.0
        assert summary.tier_impacts[1] == 6.0
        # Tier 2 average: 0.0 / 1 = 0.0
        assert summary.tier_impacts[2] == 0.0

    def test_aggregate_saves_summary_file(self, eval_harness_structure):
        """Test that aggregation saves summary.json."""
        aggregator = ResultsAggregator()
        _summary = aggregator.aggregate(eval_harness_structure)

        # Check file was created
        summary_file = eval_harness_structure / "summary.json"
        assert summary_file.exists()

        # Check can load it back
        import json

        with open(summary_file) as f:
            data = json.load(f)

        assert "baseline" in data
        assert "assessor_impacts" in data
        assert "ranked_assessors" in data
        assert "tier_impacts" in data

    def test_aggregate_ranked_assessors(self, eval_harness_structure):
        """Test that summary includes ranked assessors."""
        aggregator = ResultsAggregator()
        summary = aggregator.aggregate(eval_harness_structure)

        ranked = summary.get_ranked_assessors()

        # Should be sorted by delta_score descending
        assert ranked[0].assessor_id == "readme_structure"  # delta = 10.0
        assert ranked[1].assessor_id == "claude_md_file"  # delta = 2.0
        assert ranked[2].assessor_id == "pre_commit_hooks"  # delta = 0.0

    def test_aggregate_custom_output_file(self, eval_harness_structure):
        """Test aggregation with custom output file."""
        aggregator = ResultsAggregator()
        custom_output = eval_harness_structure / "custom_summary.json"

        _summary = aggregator.aggregate(
            eval_harness_structure, output_file=custom_output
        )

        # Check custom file was created
        assert custom_output.exists()

        # Default summary.json should not exist
        default_file = eval_harness_structure / "summary.json"
        assert not default_file.exists()
