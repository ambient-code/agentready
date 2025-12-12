"""Repomix integration service for generating AI-friendly repository context."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.subprocess_utils import safe_subprocess_run, sanitize_subprocess_error

logger = logging.getLogger(__name__)


class RepomixService:
    """Service for managing Repomix configuration and generation."""

    DEFAULT_CONFIG = {
        "$schema": "https://repomix.com/schemas/latest/schema.json",
        "input": {"maxFileSize": 52428800},
        "output": {
            "filePath": "repomix/repomix-output.md",
            "style": "markdown",
            "parsableStyle": False,
            "fileSummary": True,
            "directoryStructure": True,
            "files": True,
            "removeComments": False,
            "removeEmptyLines": False,
            "compress": False,
            "topFilesLength": 5,
            "showLineNumbers": False,
            "truncateBase64": False,
            "copyToClipboard": False,
            "includeFullDirectoryStructure": False,
            "tokenCountTree": False,
            "git": {
                "sortByChanges": True,
                "sortByChangesMaxCommits": 100,
                "includeDiffs": False,
                "includeLogs": False,
                "includeLogsCount": 50,
            },
        },
        "include": [],
        "ignore": {
            "useGitignore": True,
            "useDotIgnore": True,
            "useDefaultPatterns": True,
            "customPatterns": [],
        },
        "security": {"enableSecurityCheck": True},
        "tokenCount": {"encoding": "o200k_base"},
    }

    DEFAULT_IGNORE_PATTERNS = [
        "# Virtual environment",
        ".venv/",
        "venv/",
        "env/",
        "",
        "# Python bytecode and cache",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "",
        "# Test coverage",
        ".coverage",
        ".coverage.*",
        "htmlcov/",
        ".pytest_cache/",
        ".tox/",
        ".hypothesis/",
        "",
        "# IDE and editor files",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        "",
        "# Generated reports (keep examples/ for reference)",
        ".agentready/*.html",
        ".agentready/*.json",
        ".agentready/*.md",
        "",
        "# Build artifacts",
        "build/",
        "dist/",
        "*.egg-info/",
        "*.egg",
        "",
        "# Git internal files",
        ".git/",
        "",
        "# Temporary files",
        "*.tmp",
        "*.temp",
        ".cache/",
        "",
        "# Large generated documentation",
        "repomix/repomix-output.md",
        "repomix/repomix-output.xml",
    ]

    def __init__(self, repo_path: Path):
        """Initialize Repomix service.

        Args:
            repo_path: Path to repository
        """
        self.repo_path = repo_path
        self.config_path = repo_path / "repomix.config.json"
        self.ignore_path = repo_path / ".repomixignore"

    def is_installed(self) -> bool:
        """Check if repomix is installed on the system.

        Returns:
            True if repomix is available
        """
        return shutil.which("repomix") is not None

    def has_config(self) -> bool:
        """Check if Repomix configuration exists.

        Returns:
            True if repomix.config.json exists
        """
        return self.config_path.exists()

    def generate_config(
        self, custom_config: Optional[Dict] = None, overwrite: bool = False
    ) -> bool:
        """Generate Repomix configuration file.

        Args:
            custom_config: Custom configuration to merge with defaults
            overwrite: Whether to overwrite existing config

        Returns:
            True if config was created, False if skipped
        """
        if self.config_path.exists() and not overwrite:
            return False

        config = self.DEFAULT_CONFIG.copy()
        if custom_config:
            config.update(custom_config)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return True

    def generate_ignore(
        self, additional_patterns: Optional[List[str]] = None, overwrite: bool = False
    ) -> bool:
        """Generate .repomixignore file.

        Args:
            additional_patterns: Extra patterns to add
            overwrite: Whether to overwrite existing file

        Returns:
            True if file was created, False if skipped
        """
        if self.ignore_path.exists() and not overwrite:
            return False

        patterns = [
            "# Add patterns to ignore here, one per line",
            "# Example:",
            "# *.log",
            "# tmp/",
            "",
        ]
        patterns.extend(self.DEFAULT_IGNORE_PATTERNS)

        if additional_patterns:
            patterns.extend(["", "# Custom patterns"])
            patterns.extend(additional_patterns)

        with open(self.ignore_path, "w", encoding="utf-8") as f:
            f.write("\n".join(patterns))

        return True

    def run_repomix(
        self, output_format: str = "markdown", verbose: bool = False
    ) -> Tuple[bool, str]:
        """Execute repomix to generate repository context.

        Args:
            output_format: Output format (markdown, xml, json, plain)
            verbose: Enable verbose output

        Returns:
            Tuple of (success, output_message)
        """
        if not self.is_installed():
            return (
                False,
                "Repomix is not installed. Install with: npm install -g repomix",
            )

        # Determine output file based on format
        output_file = f"repomix/repomix-output.{output_format if output_format != 'plain' else 'txt'}"

        cmd = ["repomix", "--style", output_format, "--output", output_file]

        if verbose:
            cmd.append("--verbose")

        try:
            # Security: Use safe_subprocess_run with extended timeout for Repomix
            # Repomix can be slow on large repos, allow 5 minutes
            result = safe_subprocess_run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,  # 5 minutes for large repos
            )

            if result.returncode == 0:
                return True, f"Repomix output generated: {output_file}"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Repomix failed: {error_msg}"

        except Exception as e:
            # Security: Sanitize error messages
            safe_msg = sanitize_subprocess_error(e, self.repo_path)
            logger.error(f"Repomix error: {safe_msg}")
            return False, f"Error running repomix: {safe_msg}"

    def get_output_files(self) -> List[Path]:
        """Get list of existing Repomix output files.

        Returns:
            List of paths to Repomix output files
        """
        patterns = ["repomix/repomix-output.*"]
        output_files = []

        for pattern in patterns:
            output_files.extend(self.repo_path.glob(pattern))

        return sorted(output_files)

    def check_freshness(self, max_age_days: int = 7) -> Tuple[bool, str]:
        """Check if Repomix output is fresh.

        Args:
            max_age_days: Maximum age in days before output is stale

        Returns:
            Tuple of (is_fresh, message)
        """
        output_files = self.get_output_files()

        if not output_files:
            return False, "No Repomix output files found"

        # Check most recent file
        newest_file = max(output_files, key=lambda p: p.stat().st_mtime)
        age_seconds = datetime.now().timestamp() - newest_file.stat().st_mtime
        age_days = age_seconds / (24 * 3600)

        if age_days > max_age_days:
            return (
                False,
                f"Repomix output is {age_days:.1f} days old (max: {max_age_days})",
            )

        return True, f"Repomix output is fresh ({age_days:.1f} days old)"
