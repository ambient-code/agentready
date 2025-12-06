"""Terminal-Bench integration for eval harness.

This module provides both mocked (for testing workflow) and real
(future Harbor framework) Terminal-Bench integration.
"""

import hashlib
import random
from datetime import datetime
from pathlib import Path

import git

from ...models.eval_harness import TbenchResult


class TbenchRunner:
    """Interface to Terminal-Bench benchmark.

    Supports both mocked results (for workflow validation) and real
    Terminal-Bench integration via Harbor framework (future).
    """

    def __init__(self, mock: bool = True):
        """Initialize runner.

        Args:
            mock: If True, generate fake but realistic scores.
                  If False, use real Terminal-Bench via Harbor (future).
        """
        self.mock = mock

    def run_benchmark(self, repo_path: Path) -> TbenchResult:
        """Run Terminal-Bench on repository.

        Args:
            repo_path: Path to git repository to evaluate

        Returns:
            TbenchResult with scores and metrics

        Raises:
            ValueError: If repo_path is not a git repository
            NotImplementedError: If mock=False (real tbench not yet implemented)
        """
        # Validate repository
        if not (repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if self.mock:
            return self._mock_tbench_result(repo_path)
        else:
            # Future: Real Harbor framework integration
            raise NotImplementedError(
                "Real Terminal-Bench integration not yet implemented. "
                "Use mock=True for workflow validation."
            )

    def _mock_tbench_result(self, repo_path: Path) -> TbenchResult:
        """Generate realistic fake Terminal-Bench scores.

        Uses deterministic randomness seeded from repository commit hash
        for reproducible results. Incorporates repository characteristics
        (lines of code, languages) to make scores meaningful.

        Args:
            repo_path: Repository to generate score for

        Returns:
            Mocked TbenchResult with realistic scores
        """
        # Get repository metadata
        repo = git.Repo(repo_path)
        commit_hash = repo.head.commit.hexsha

        # Seed random generator from commit hash for determinism
        seed = int(hashlib.sha256(commit_hash.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        # Get repository characteristics
        total_lines = self._count_lines(repo_path)
        languages = self._detect_languages_simple(repo_path)

        # Base score depends on repository size and structure
        # Larger, more organized repos tend to score higher
        base_score = 50.0

        # Adjust for repository size (more lines = slightly better)
        if total_lines > 10000:
            base_score += 10.0
        elif total_lines > 5000:
            base_score += 5.0
        elif total_lines > 1000:
            base_score += 2.0

        # Adjust for language diversity (more languages = slightly better agent performance)
        base_score += min(len(languages) * 2.0, 10.0)

        # Add random variance (±10 points)
        variance = rng.uniform(-10.0, 10.0)
        score = max(0.0, min(100.0, base_score + variance))

        # Generate correlated metrics
        completion_rate = score + rng.uniform(-5.0, 5.0)
        completion_rate = max(0.0, min(100.0, completion_rate))

        pytest_pass_rate = score + rng.uniform(-10.0, 10.0)
        pytest_pass_rate = max(0.0, min(100.0, pytest_pass_rate))

        # Latency inversely correlated with score (better repos = faster)
        base_latency = 5000.0  # 5 seconds
        latency_ms = base_latency * (1.0 - score / 200.0) + rng.uniform(-500.0, 500.0)
        latency_ms = max(1000.0, latency_ms)  # At least 1 second

        return TbenchResult(
            score=round(score, 2),
            completion_rate=round(completion_rate, 2),
            pytest_pass_rate=round(pytest_pass_rate, 2),
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.now(),
            is_mocked=True,
        )

    def _count_lines(self, repo_path: Path) -> int:
        """Count total lines of code in repository.

        Args:
            repo_path: Repository path

        Returns:
            Total lines (approximate, using git ls-files)
        """
        try:
            repo = git.Repo(repo_path)
            files = repo.git.ls_files().splitlines()

            total_lines = 0
            for file_path in files[:100]:  # Sample first 100 files for speed
                full_path = repo_path / file_path
                if full_path.is_file():
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            total_lines += sum(1 for _ in f)
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or permission errors
                        continue

            # Extrapolate if we sampled
            if len(files) > 100:
                total_lines = int(total_lines * (len(files) / 100))

            return total_lines

        except Exception:
            # Fallback if git operations fail
            return 1000

    def _detect_languages_simple(self, repo_path: Path) -> list[str]:
        """Detect languages in repository (simplified version).

        Args:
            repo_path: Repository path

        Returns:
            List of detected languages (e.g., ["Python", "JavaScript"])
        """
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".c": "C",
            ".cpp": "C++",
            ".cs": "C#",
        }

        try:
            repo = git.Repo(repo_path)
            files = repo.git.ls_files().splitlines()

            detected = set()
            for file_path in files:
                suffix = Path(file_path).suffix
                if suffix in extensions:
                    detected.add(extensions[suffix])

            return list(detected)

        except Exception:
            return ["Unknown"]
