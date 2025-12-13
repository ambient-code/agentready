"""Service for executing Harbor benchmarks via CLI."""

import inspect
import subprocess
import warnings
from pathlib import Path
from typing import List


class HarborNotInstalledError(Exception):
    """Raised when Harbor framework is not installed."""

    pass


class HarborTaskFilteringBugWarning(UserWarning):
    """Raised when Harbor has the task filtering bug."""

    pass


class HarborRunner:
    """Execute Harbor benchmarks via subprocess and capture results."""

    def __init__(self):
        """Initialize Harbor runner and verify installation."""
        self._verify_harbor_installed()
        self._check_harbor_task_filtering()

    def _verify_harbor_installed(self) -> None:
        """Verify Harbor CLI is installed and accessible.

        Raises:
            HarborNotInstalledError: If Harbor is not installed or not in PATH
        """
        try:
            subprocess.run(
                ["harbor", "--help"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
        except FileNotFoundError:
            raise HarborNotInstalledError(
                "Harbor framework not installed.\n"
                "Install with: uv tool install harbor\n"
                "See: https://harborframework.com/docs/getting-started"
            )
        except subprocess.CalledProcessError as e:
            raise HarborNotInstalledError(f"Harbor CLI error: {e.stderr}")

    def _check_harbor_task_filtering(self) -> None:
        """Check if Harbor has the task filtering bug fix.

        Warns if Harbor version has the known task filtering bug where -t flags are ignored.

        The bug was fixed in Harbor commit f9e6d2e (Dec 12, 2025) but not yet released.
        PyPI version 0.1.23 (Dec 11, 2025) has the bug.

        See: https://github.com/laude-institute/harbor/commit/f9e6d2e10c72d33373012294c36fd4938c45c26c
        """
        try:
            from harbor.models.job.config import BaseDatasetConfig

            # Check if the fix is present by inspecting source code
            source = inspect.getsource(BaseDatasetConfig._filter_task_ids)

            # The fix changed task_id.path.name to task_id.get_name()
            # If we see path.name (the bug), warn the user
            if "task_id.path.name" in source or ".path.name" in source:
                warnings.warn(
                    "\n"
                    "⚠️  WARNING: Harbor has a task filtering bug!\n"
                    "\n"
                    "Your Harbor version has a bug where -t/--task-name flags are ignored.\n"
                    "This causes smoketests to run ALL tasks instead of the filtered subset.\n"
                    "\n"
                    "The bug was fixed in Harbor main (Dec 12, 2025) but not yet released.\n"
                    "Latest PyPI version 0.1.23 (Dec 11) still has the bug.\n"
                    "\n"
                    "FIX OPTIONS:\n"
                    "\n"
                    "Option 1 (recommended): Install Harbor from main\n"
                    "  pip uninstall harbor\n"
                    "  pip install git+https://github.com/laude-institute/harbor.git\n"
                    "\n"
                    "Option 2: Apply patch to your local Harbor installation\n"
                    "  See: patches/harbor-task-filtering-fix.patch in AgentReady repo\n"
                    "\n"
                    "Commit: https://github.com/laude-institute/harbor/commit/f9e6d2e\n",
                    HarborTaskFilteringBugWarning,
                    stacklevel=2,
                )
            # If we see get_name() (the fix), all good - no warning

        except ImportError:
            # Harbor not importable as Python package (only CLI installed)
            # Can't check for bug, but also can't use task filtering anyway
            pass
        except Exception:
            # Don't fail if we can't check - just skip the warning
            pass

    def run_benchmark(
        self,
        task_names: List[str],
        output_dir: Path,
        dataset: str = "terminal-bench",
        dataset_version: str = "2.0",
        model: str = "anthropic/claude-sonnet-4-5",
        agent: str = "claude-code",
        n_concurrent: int = 1,
        verbose: bool = True,
    ) -> Path:
        """Run Harbor benchmark and return results directory.

        Args:
            task_names: List of task names to run (e.g., ['adaptive-rejection-sampler'])
            output_dir: Directory to store results
            dataset: Dataset name (default: 'terminal-bench')
            dataset_version: Dataset version (default: '2.0')
            model: Model identifier (default: 'anthropic/claude-sonnet-4-5')
            agent: Agent identifier (default: 'claude-code')
            n_concurrent: Number of concurrent tasks (default: 1)
            verbose: Print Harbor output to console (default: True)

        Returns:
            Path to results directory containing result.json files

        Raises:
            HarborNotInstalledError: If Harbor is not installed
            subprocess.CalledProcessError: If Harbor command fails
            ValueError: If no tasks completed successfully
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build Harbor command
        cmd = [
            "harbor",
            "run",
            "-d",
            f"{dataset}@{dataset_version}",
            "-m",
            model,
            "-a",
            agent,
            "-n",
            str(n_concurrent),
        ]

        # Add task name filters
        # NOTE: Requires Harbor >= 0.1.24 (or install from main)
        # Task filtering was fixed in commit f9e6d2e (Dec 12, 2025)
        for task_name in task_names:
            cmd.extend(["-t", task_name])

        # Execute Harbor benchmark
        if verbose:
            print(f"Running Harbor benchmark: {' '.join(cmd)}")
            print(f"Tasks: {', '.join(task_names) if task_names else 'all'}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(output_dir),
                capture_output=not verbose,
                text=True,
                check=True,
                timeout=None,  # No timeout for long-running benchmarks
            )

            if verbose and result.stdout:
                print(result.stdout)

        except subprocess.CalledProcessError as e:
            error_msg = f"Harbor benchmark failed: {e.stderr if e.stderr else str(e)}"
            raise subprocess.CalledProcessError(
                e.returncode, e.cmd, e.output, error_msg
            )

        # Find results directory (Harbor creates timestamped subdirectory)
        results_dirs = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime)
        if not results_dirs:
            raise ValueError(f"No results found in {output_dir}")

        results_dir = results_dirs[-1]  # Most recent run

        if verbose:
            print(f"Results stored in: {results_dir}")

        return results_dir
