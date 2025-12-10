"""Unit tests for Harbor data models."""

import pytest

from agentready.models.harbor import (
    HarborComparison,
    HarborRunMetrics,
    HarborTaskResult,
)


class TestHarborTaskResult:
    """Tests for HarborTaskResult model."""

    def test_from_result_json_success(self):
        """Test creating HarborTaskResult from successful result.json data."""
        result_data = {
            "task_name": "adaptive-rejection-sampler",
            "trial_name": "adaptive-rejection-sampler__ABC123",
            "agent_result": {"status": "completed"},
            "verifier_result": {"passed": True},
            "exception_info": None,
            "started_at": "2025-12-09T10:00:00",
            "finished_at": "2025-12-09T10:05:00",
        }

        result = HarborTaskResult.from_result_json(result_data)

        assert result.task_name == "adaptive-rejection-sampler"
        assert result.trial_name == "adaptive-rejection-sampler__ABC123"
        assert result.success is True
        assert result.duration_sec == 300.0  # 5 minutes
        assert result.agent_result == {"status": "completed"}
        assert result.verifier_result == {"passed": True}
        assert result.exception_info is None

    def test_from_result_json_failure(self):
        """Test creating HarborTaskResult from failed result.json data."""
        result_data = {
            "task_name": "async-http-client",
            "trial_name": "async-http-client__DEF456",
            "agent_result": None,
            "verifier_result": None,
            "exception_info": {
                "exception_type": "TimeoutError",
                "exception_message": "Task timed out",
            },
            "started_at": "2025-12-09T10:00:00",
            "finished_at": "2025-12-09T10:30:00",
        }

        result = HarborTaskResult.from_result_json(result_data)

        assert result.task_name == "async-http-client"
        assert result.success is False
        assert result.duration_sec == 1800.0  # 30 minutes
        assert result.exception_info["exception_type"] == "TimeoutError"

    def test_to_dict(self):
        """Test converting HarborTaskResult to dictionary."""
        result = HarborTaskResult(
            task_name="test-task",
            trial_name="test-task__123",
            success=True,
            duration_sec=120.0,
            agent_result={"status": "ok"},
            verifier_result={"passed": True},
            exception_info=None,
            started_at="2025-12-09T10:00:00",
            finished_at="2025-12-09T10:02:00",
        )

        result_dict = result.to_dict()

        assert result_dict["task_name"] == "test-task"
        assert result_dict["success"] is True
        assert result_dict["duration_sec"] == 120.0


class TestHarborRunMetrics:
    """Tests for HarborRunMetrics model."""

    def test_from_task_results_all_successful(self):
        """Test calculating metrics from all successful task results."""
        task_results = [
            HarborTaskResult(
                task_name=f"task{i}",
                trial_name=f"task{i}__ABC",
                success=True,
                duration_sec=60.0 * i,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at=f"2025-12-09T10:0{i}:00",
            )
            for i in range(1, 4)
        ]

        metrics = HarborRunMetrics.from_task_results("run1", True, task_results)

        assert metrics.run_id == "run1"
        assert metrics.agent_file_enabled is True
        assert metrics.total_tasks == 3
        assert metrics.successful_tasks == 3
        assert metrics.failed_tasks == 0
        assert metrics.timed_out_tasks == 0
        assert metrics.success_rate == 100.0
        assert metrics.completion_rate == 100.0
        assert metrics.avg_duration_sec == 120.0  # (60 + 120 + 180) / 3

    def test_from_task_results_mixed(self):
        """Test calculating metrics from mixed success/failure results."""
        task_results = [
            HarborTaskResult(
                task_name="task1",
                trial_name="task1__ABC",
                success=True,
                duration_sec=60.0,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:01:00",
            ),
            HarborTaskResult(
                task_name="task2",
                trial_name="task2__DEF",
                success=False,
                duration_sec=120.0,
                agent_result=None,
                verifier_result=None,
                exception_info={"exception_type": "TimeoutError"},
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:02:00",
            ),
            HarborTaskResult(
                task_name="task3",
                trial_name="task3__GHI",
                success=False,
                duration_sec=90.0,
                agent_result={"status": "error"},
                verifier_result=None,
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:01:30",
            ),
        ]

        metrics = HarborRunMetrics.from_task_results("run2", False, task_results)

        assert metrics.total_tasks == 3
        assert metrics.successful_tasks == 1
        assert metrics.failed_tasks == 1  # task3 (no timeout exception)
        assert metrics.timed_out_tasks == 1  # task2
        assert metrics.success_rate == pytest.approx(33.33, rel=0.01)
        assert metrics.completion_rate == pytest.approx(66.67, rel=0.01)

    def test_to_dict(self):
        """Test converting HarborRunMetrics to dictionary."""
        task_results = [
            HarborTaskResult(
                task_name="task1",
                trial_name="task1__ABC",
                success=True,
                duration_sec=60.0,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:01:00",
            )
        ]

        metrics = HarborRunMetrics.from_task_results("run1", True, task_results)
        metrics_dict = metrics.to_dict()

        assert metrics_dict["run_id"] == "run1"
        assert metrics_dict["agent_file_enabled"] is True
        assert metrics_dict["total_tasks"] == 1
        assert len(metrics_dict["task_results"]) == 1


class TestHarborComparison:
    """Tests for HarborComparison model."""

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing."""
        without_results = [
            HarborTaskResult(
                task_name="task1",
                trial_name="task1__ABC",
                success=False,
                duration_sec=120.0,
                agent_result=None,
                verifier_result=None,
                exception_info={"exception_type": "TimeoutError"},
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:02:00",
            ),
            HarborTaskResult(
                task_name="task2",
                trial_name="task2__DEF",
                success=True,
                duration_sec=180.0,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:03:00",
            ),
        ]

        with_results = [
            HarborTaskResult(
                task_name="task1",
                trial_name="task1__GHI",
                success=True,
                duration_sec=90.0,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:01:30",
            ),
            HarborTaskResult(
                task_name="task2",
                trial_name="task2__JKL",
                success=True,
                duration_sec=150.0,
                agent_result={"status": "ok"},
                verifier_result={"passed": True},
                exception_info=None,
                started_at="2025-12-09T10:00:00",
                finished_at="2025-12-09T10:02:30",
            ),
        ]

        without_agent = HarborRunMetrics.from_task_results(
            "run1", False, without_results
        )
        with_agent = HarborRunMetrics.from_task_results("run2", True, with_results)

        return without_agent, with_agent

    def test_calculate_deltas(self, sample_metrics):
        """Test calculating delta metrics."""
        without_agent, with_agent = sample_metrics
        comparison = HarborComparison(
            without_agent=without_agent, with_agent=with_agent
        )

        comparison.calculate_deltas()

        assert "success_rate_delta" in comparison.deltas
        assert comparison.deltas["success_rate_delta"] == 50.0  # 50% -> 100%
        assert "avg_duration_delta_sec" in comparison.deltas
        assert "avg_duration_delta_pct" in comparison.deltas
        assert comparison.deltas["successful_tasks_delta"] == 1  # 1 -> 2

    def test_generate_per_task_comparison(self, sample_metrics):
        """Test generating per-task comparison."""
        without_agent, with_agent = sample_metrics
        comparison = HarborComparison(
            without_agent=without_agent, with_agent=with_agent
        )

        comparison.generate_per_task_comparison()

        assert len(comparison.per_task_comparison) == 2
        task1_comparison = next(
            c for c in comparison.per_task_comparison if c["task_name"] == "task1"
        )

        assert task1_comparison["without_agent"]["success"] is False
        assert task1_comparison["with_agent"]["success"] is True
        assert task1_comparison["delta"]["success_improved"] is True

    def test_to_dict_and_from_dict(self, sample_metrics):
        """Test serialization and deserialization."""
        without_agent, with_agent = sample_metrics
        comparison = HarborComparison(
            without_agent=without_agent, with_agent=with_agent
        )
        comparison.calculate_deltas()
        comparison.generate_per_task_comparison()

        comparison_dict = comparison.to_dict()
        restored_comparison = HarborComparison.from_dict(comparison_dict)

        assert restored_comparison.without_agent.run_id == without_agent.run_id
        assert restored_comparison.with_agent.run_id == with_agent.run_id
        assert restored_comparison.deltas == comparison.deltas
        assert len(restored_comparison.per_task_comparison) == len(
            comparison.per_task_comparison
        )
