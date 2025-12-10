"""Data models for Harbor benchmark integration."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class HarborTaskResult:
    """Single task result from Harbor result.json."""

    task_name: str
    trial_name: str
    success: bool
    duration_sec: float
    agent_result: Optional[Dict[str, Any]]
    verifier_result: Optional[Dict[str, Any]]
    exception_info: Optional[Dict[str, str]]
    started_at: str
    finished_at: str

    @classmethod
    def from_result_json(cls, result_data: Dict[str, Any]) -> "HarborTaskResult":
        """Create HarborTaskResult from parsed result.json data."""
        # Parse timestamps to calculate duration
        started = datetime.fromisoformat(result_data["started_at"])
        finished = datetime.fromisoformat(result_data["finished_at"])
        duration_sec = (finished - started).total_seconds()

        # Determine success based on agent_result and verifier_result
        agent_result = result_data.get("agent_result")
        verifier_result = result_data.get("verifier_result")
        exception_info = result_data.get("exception_info")

        # Success if no exception and both agent and verifier completed
        success = (
            exception_info is None
            and agent_result is not None
            and verifier_result is not None
        )

        return cls(
            task_name=result_data["task_name"],
            trial_name=result_data["trial_name"],
            success=success,
            duration_sec=duration_sec,
            agent_result=agent_result,
            verifier_result=verifier_result,
            exception_info=exception_info,
            started_at=result_data["started_at"],
            finished_at=result_data["finished_at"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_name": self.task_name,
            "trial_name": self.trial_name,
            "success": self.success,
            "duration_sec": self.duration_sec,
            "agent_result": self.agent_result,
            "verifier_result": self.verifier_result,
            "exception_info": self.exception_info,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass
class HarborRunMetrics:
    """Aggregated metrics for a Harbor run."""

    run_id: str
    agent_file_enabled: bool
    task_results: List[HarborTaskResult]
    success_rate: float
    completion_rate: float
    avg_duration_sec: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    timed_out_tasks: int

    @classmethod
    def from_task_results(
        cls, run_id: str, agent_file_enabled: bool, task_results: List[HarborTaskResult]
    ) -> "HarborRunMetrics":
        """Calculate aggregated metrics from task results."""
        total_tasks = len(task_results)
        successful_tasks = sum(1 for r in task_results if r.success)
        failed_tasks = sum(
            1 for r in task_results if not r.success and r.exception_info is None
        )
        timed_out_tasks = sum(
            1
            for r in task_results
            if not r.success
            and r.exception_info
            and "timeout" in r.exception_info.get("exception_type", "").lower()
        )

        success_rate = (
            (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        )
        completion_rate = (
            (successful_tasks + failed_tasks) / total_tasks * 100
            if total_tasks > 0
            else 0.0
        )

        # Calculate average duration (only for completed tasks)
        completed_results = [r for r in task_results if r.agent_result is not None]
        avg_duration_sec = (
            sum(r.duration_sec for r in completed_results) / len(completed_results)
            if completed_results
            else 0.0
        )

        return cls(
            run_id=run_id,
            agent_file_enabled=agent_file_enabled,
            task_results=task_results,
            success_rate=success_rate,
            completion_rate=completion_rate,
            avg_duration_sec=avg_duration_sec,
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            timed_out_tasks=timed_out_tasks,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "agent_file_enabled": self.agent_file_enabled,
            "task_results": [r.to_dict() for r in self.task_results],
            "success_rate": self.success_rate,
            "completion_rate": self.completion_rate,
            "avg_duration_sec": self.avg_duration_sec,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "timed_out_tasks": self.timed_out_tasks,
        }


@dataclass
class HarborComparison:
    """Complete comparison between two Harbor runs."""

    without_agent: HarborRunMetrics
    with_agent: HarborRunMetrics
    deltas: Dict[str, float] = field(default_factory=dict)
    statistical_significance: Dict[str, bool] = field(default_factory=dict)
    per_task_comparison: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def calculate_deltas(self) -> None:
        """Calculate delta metrics between runs."""
        success_rate_delta = (
            self.with_agent.success_rate - self.without_agent.success_rate
        )
        completion_rate_delta = (
            self.with_agent.completion_rate - self.without_agent.completion_rate
        )
        duration_delta_sec = (
            self.with_agent.avg_duration_sec - self.without_agent.avg_duration_sec
        )
        successful_tasks_delta = (
            self.with_agent.successful_tasks - self.without_agent.successful_tasks
        )

        # Calculate percentage change in duration
        duration_delta_pct = None
        if self.without_agent.avg_duration_sec > 0:
            duration_delta_pct = (
                duration_delta_sec / self.without_agent.avg_duration_sec * 100
            )

        self.deltas = {
            "success_rate_delta": success_rate_delta,
            "completion_rate_delta": completion_rate_delta,
            "avg_duration_delta_sec": duration_delta_sec,
            "avg_duration_delta_pct": duration_delta_pct,
            "successful_tasks_delta": successful_tasks_delta,
        }

    def generate_per_task_comparison(self) -> None:
        """Generate per-task comparison details."""
        # Create lookup dictionary for tasks
        without_tasks = {r.task_name: r for r in self.without_agent.task_results}
        with_tasks = {r.task_name: r for r in self.with_agent.task_results}

        self.per_task_comparison = []
        all_task_names = set(without_tasks.keys()) | set(with_tasks.keys())

        for task_name in all_task_names:
            without_result = without_tasks.get(task_name)
            with_result = with_tasks.get(task_name)

            comparison = {"task_name": task_name}

            # Add without_agent result if exists
            if without_result:
                comparison["without_agent"] = {
                    "success": without_result.success,
                    "duration_sec": without_result.duration_sec,
                }
            else:
                comparison["without_agent"] = None

            # Add with_agent result if exists
            if with_result:
                comparison["with_agent"] = {
                    "success": with_result.success,
                    "duration_sec": with_result.duration_sec,
                }
            else:
                comparison["with_agent"] = None

            # Calculate per-task delta if both results exist
            if without_result and with_result:
                comparison["delta"] = self._calculate_task_delta(
                    without_result, with_result
                )

            self.per_task_comparison.append(comparison)

    def _calculate_task_delta(
        self, without_result: HarborTaskResult, with_result: HarborTaskResult
    ) -> Dict[str, Any]:
        """Calculate delta between two task results."""
        duration_delta_sec = with_result.duration_sec - without_result.duration_sec
        duration_delta_pct = None

        if without_result.duration_sec > 0:
            duration_delta_pct = duration_delta_sec / without_result.duration_sec * 100

        return {
            "success_improved": with_result.success and not without_result.success,
            "duration_delta_sec": duration_delta_sec,
            "duration_delta_pct": duration_delta_pct,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "without_agent": self.without_agent.to_dict(),
            "with_agent": self.with_agent.to_dict(),
            "deltas": self.deltas,
            "statistical_significance": self.statistical_significance,
            "per_task_comparison": self.per_task_comparison,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HarborComparison":
        """Create HarborComparison from dictionary."""
        without_agent_data = data["without_agent"]
        with_agent_data = data["with_agent"]

        without_agent = HarborRunMetrics(
            run_id=without_agent_data["run_id"],
            agent_file_enabled=without_agent_data["agent_file_enabled"],
            task_results=[
                HarborTaskResult(**r) for r in without_agent_data["task_results"]
            ],
            success_rate=without_agent_data["success_rate"],
            completion_rate=without_agent_data["completion_rate"],
            avg_duration_sec=without_agent_data["avg_duration_sec"],
            total_tasks=without_agent_data["total_tasks"],
            successful_tasks=without_agent_data["successful_tasks"],
            failed_tasks=without_agent_data["failed_tasks"],
            timed_out_tasks=without_agent_data["timed_out_tasks"],
        )

        with_agent = HarborRunMetrics(
            run_id=with_agent_data["run_id"],
            agent_file_enabled=with_agent_data["agent_file_enabled"],
            task_results=[
                HarborTaskResult(**r) for r in with_agent_data["task_results"]
            ],
            success_rate=with_agent_data["success_rate"],
            completion_rate=with_agent_data["completion_rate"],
            avg_duration_sec=with_agent_data["avg_duration_sec"],
            total_tasks=with_agent_data["total_tasks"],
            successful_tasks=with_agent_data["successful_tasks"],
            failed_tasks=with_agent_data["failed_tasks"],
            timed_out_tasks=with_agent_data["timed_out_tasks"],
        )

        return cls(
            without_agent=without_agent,
            with_agent=with_agent,
            deltas=data.get("deltas", {}),
            statistical_significance=data.get("statistical_significance", {}),
            per_task_comparison=data.get("per_task_comparison", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
