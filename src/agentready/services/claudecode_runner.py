"""Claude Code headless mode execution wrapper."""

import json
import subprocess
from pathlib import Path
from typing import Optional


class ClaudeCodeRunner:
    """Run SWE-bench tasks using Claude Code headless mode."""

    def __init__(
        self,
        model: str = "claude-sonnet-4.5",
        max_turns: int = 30,
        timeout_minutes: int = 60,
    ):
        self.model = model
        self.max_turns = max_turns
        self.timeout_minutes = timeout_minutes

    def _get_swebench_system_prompt(self) -> str:
        """System prompt for SWE-bench task execution."""
        return """
You are solving a GitHub issue from a real repository.

TOOLS AVAILABLE:
- Bash Tool: Execute shell commands (no internet access, persistent state)
- Edit Tool: View, create, edit files using string replacement

INSTRUCTIONS:
1. Analyze the problem statement thoroughly
2. Explore the codebase to understand context
3. Implement a solution that passes existing unit tests
4. Create a git commit with your changes when done
5. Generate a unified diff patch (git diff HEAD~1)

COMPLETION:
Signal task completion by running: git diff HEAD~1 > /tmp/solution.patch
"""

    def run_task(
        self, instance_id: str, problem_statement: str, repo_path: Path
    ) -> dict:
        """
        Run single SWE-bench task using Claude Code.

        Args:
            instance_id: SWE-bench instance ID (e.g., "django__django-12345")
            problem_statement: GitHub issue description
            repo_path: Path to repository

        Returns:
            Prediction dict with instance_id, model, and patch
        """
        cmd = [
            "claude",
            "--print",
            "--output-format",
            "json",
            "--allowedTools",
            "Bash(*)",
            "Edit(*)",
            "--append-system-prompt",
            self._get_swebench_system_prompt(),
            "--cwd",
            str(repo_path),
            problem_statement,
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=self.timeout_minutes * 60
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Code failed: {result.stderr}")

        # Extract git patch from repository
        patch_result = subprocess.run(
            ["git", "diff", "HEAD~1"], cwd=repo_path, capture_output=True, text=True
        )

        return {
            "instance_id": instance_id,
            "model_name_or_path": f"claude-code-{self.model}",
            "model_patch": patch_result.stdout,
        }

    def run_batch(self, tasks_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Run batch of tasks.

        Args:
            tasks_file: JSONL file with tasks (instance_id, problem_statement, repo_path)
            output_file: Where to save predictions.jsonl

        Returns:
            Path to predictions.jsonl file
        """
        if output_file is None:
            output_file = Path("predictions_claudecode.jsonl")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(tasks_file) as f:
            tasks = [json.loads(line) for line in f]

        predictions = []
        for task in tasks:
            try:
                prediction = self.run_task(
                    instance_id=task["instance_id"],
                    problem_statement=task["problem_statement"],
                    repo_path=Path(task["repo_path"]),
                )
                predictions.append(prediction)
            except Exception as e:
                print(f"Error on {task['instance_id']}: {e}")
                continue

        # Save predictions in SWE-bench JSONL format
        with open(output_file, "w") as f:
            for pred in predictions:
                f.write(json.dumps(pred) + "\n")

        return output_file
