"""Smart code sampling from repositories for LLM analysis."""

import logging
from pathlib import Path

from agentready.models import Finding, Repository

logger = logging.getLogger(__name__)


class CodeSampler:
    """Extracts relevant code samples from repository for LLM analysis."""

    # Mapping of attribute IDs to file patterns to sample
    ATTRIBUTE_FILE_PATTERNS = {
        "claude_md_file": ["CLAUDE.md"],
        "readme_file": ["README.md"],
        "type_annotations": ["**/*.py"],  # Sample Python files
        "pre_commit_hooks": [".pre-commit-config.yaml", ".github/workflows/*.yml"],
        "standard_project_layout": [
            "**/",
            "src/",
            "tests/",
            "docs/",
        ],  # Directory structure
        "lock_files": [
            "requirements.txt",
            "poetry.lock",
            "package-lock.json",
            "go.sum",
            "Cargo.lock",
        ],
        "test_coverage": ["pytest.ini", "pyproject.toml", ".coveragerc"],
        "conventional_commits": [".github/workflows/*.yml"],  # CI configs
        "gitignore": [".gitignore"],
    }

    def __init__(
        self, repository: Repository, max_files: int = 5, max_lines_per_file: int = 100
    ):
        """Initialize code sampler.

        Args:
            repository: Repository to sample from
            max_files: Maximum number of files to include
            max_lines_per_file: Maximum lines per file to prevent token overflow
        """
        self.repository = repository
        self.max_files = max_files
        self.max_lines_per_file = max_lines_per_file

    def get_relevant_code(self, finding: Finding) -> str:
        """Get relevant code samples for a finding.

        Args:
            finding: The finding to get code for

        Returns:
            Formatted string with code samples
        """
        attribute_id = finding.attribute.id
        patterns = self.ATTRIBUTE_FILE_PATTERNS.get(attribute_id, [])

        if not patterns:
            logger.warning(f"No file patterns defined for {attribute_id}")
            return "No code samples available"

        # Collect files matching patterns
        files_to_sample = []
        for pattern in patterns:
            if pattern.endswith("/"):
                # Directory listing
                files_to_sample.append(self._get_directory_tree(pattern))
            else:
                # File pattern
                matching_files = list(self.repository.path.glob(pattern))
                files_to_sample.extend(matching_files[: self.max_files])

        # Format as string
        return self._format_code_samples(files_to_sample)

    def _get_directory_tree(self, dir_pattern: str) -> dict:
        """Get directory tree structure."""
        base_path = self.repository.path / dir_pattern.rstrip("/")
        if not base_path.exists():
            return {}

        tree = {
            "type": "directory",
            "path": str(base_path.relative_to(self.repository.path)),
            "children": [],
        }

        for item in base_path.iterdir():
            if item.is_file():
                tree["children"].append({"type": "file", "name": item.name})
            elif item.is_dir() and not item.name.startswith("."):
                tree["children"].append({"type": "directory", "name": item.name})

        return tree

    def _format_code_samples(self, files: list) -> str:
        """Format files as readable code samples."""
        samples = []

        for file_item in files[: self.max_files]:
            if isinstance(file_item, dict):
                # Skip empty dicts (invalid entries)
                if not file_item:
                    continue
                # Directory tree
                samples.append(f"## Directory Structure: {file_item['path']}\n")
                samples.append(self._format_tree(file_item))
            elif isinstance(file_item, Path):
                # Regular file
                try:
                    rel_path = file_item.relative_to(self.repository.path)
                    content = file_item.read_text(encoding="utf-8", errors="ignore")

                    # Truncate if too long
                    lines = content.splitlines()
                    if len(lines) > self.max_lines_per_file:
                        lines = lines[: self.max_lines_per_file]
                        lines.append("... (truncated)")

                    samples.append(f"## File: {rel_path}\n")
                    samples.append("```\n" + "\n".join(lines) + "\n```\n")

                except Exception as e:
                    logger.warning(f"Could not read {file_item}: {e}")

        return "\n".join(samples) if samples else "No code samples available"

    def _format_tree(self, tree: dict, indent: int = 0) -> str:
        """Format directory tree as text."""
        lines = []
        prefix = "  " * indent

        for child in tree.get("children", []):
            if child["type"] == "file":
                lines.append(f"{prefix}├── {child['name']}")
            elif child["type"] == "directory":
                lines.append(f"{prefix}├── {child['name']}/")

        return "\n".join(lines)
