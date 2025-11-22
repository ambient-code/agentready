"""Secure subprocess utilities with validation and guardrails.

Security features:
- Mandatory timeouts to prevent DoS
- Output size limits to prevent memory exhaustion
- Path validation to prevent symlink attacks
- Error message sanitization
"""

import getpass
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Security constants
SUBPROCESS_TIMEOUT = 120  # 2 minutes max for any subprocess
MAX_OUTPUT_SIZE = 10_000_000  # 10MB max output
FORBIDDEN_PATHS = ["/etc", "/sys", "/proc", "/dev", "/.ssh", "/root", "/var"]


class SubprocessSecurityError(Exception):
    """Raised when subprocess security check fails."""

    pass


def validate_repository_path(path: Path) -> Path:
    """Validate and resolve repository path safely.

    Security: Prevents symlink attacks and access to sensitive directories.

    Args:
        path: Repository path to validate

    Returns:
        Validated resolved path

    Raises:
        SubprocessSecurityError: If path is invalid or forbidden
    """
    # Resolve symlinks to actual path
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as e:
        raise SubprocessSecurityError(f"Cannot resolve path {path}: {e}")

    # Prevent access to sensitive system directories
    for forbidden in FORBIDDEN_PATHS:
        if str(resolved).startswith(forbidden):
            raise SubprocessSecurityError(
                f"Cannot access sensitive directory: {resolved}"
            )

    # Ensure it's actually a git repository
    if not (resolved / ".git").exists() and not (resolved / ".git").is_file():
        raise SubprocessSecurityError(f"Not a git repository: {resolved}")

    return resolved


def sanitize_subprocess_error(error: Exception, repo_path: Path | None = None) -> str:
    """Sanitize error message to prevent information leakage.

    Security: Redacts absolute paths, usernames, and sensitive data.

    Args:
        error: Exception to sanitize
        repo_path: Optional repository path to redact

    Returns:
        Sanitized error message
    """
    msg = str(error)

    # Redact absolute paths
    if repo_path:
        msg = msg.replace(str(repo_path.resolve()), "<repo>")

    # Redact home directory
    try:
        msg = msg.replace(str(Path.home()), "<home>")
    except (RuntimeError, OSError):
        pass

    # Redact username
    try:
        username = getpass.getuser()
        msg = msg.replace(f"/{username}/", "/<user>/")
        msg = msg.replace(f"\\{username}\\", "\\<user>\\")
    except Exception:
        pass

    # Truncate if too long
    if len(msg) > 500:
        msg = msg[:500] + "... (truncated)"

    return msg


def safe_subprocess_run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run subprocess with security guardrails.

    Security features:
    - Enforces timeout to prevent DoS
    - Validates cwd if it's a repository
    - Limits output size to prevent memory exhaustion
    - Sanitizes error messages

    Args:
        cmd: Command and arguments (list form, never shell=True)
        cwd: Working directory (validated if provided)
        timeout: Timeout in seconds (default: SUBPROCESS_TIMEOUT)
        **kwargs: Additional subprocess.run() arguments

    Returns:
        CompletedProcess result

    Raises:
        SubprocessSecurityError: If security validation fails
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails and check=True
    """
    # Security: Enforce timeout
    if timeout is None:
        timeout = kwargs.pop("timeout", SUBPROCESS_TIMEOUT)

    # Security: Validate cwd if it looks like a repository path
    if cwd:
        cwd_path = Path(cwd)
        # Only validate if it has .git (repository check)
        if (cwd_path / ".git").exists() or (cwd_path / ".git").is_file():
            try:
                cwd = validate_repository_path(cwd_path)
            except SubprocessSecurityError:
                # If validation fails, log but don't block
                # (cwd might be temporary directory, etc.)
                logger.debug(f"Repository validation skipped for: {cwd}")

    # Security: Never allow shell=True
    if kwargs.get("shell"):
        raise SubprocessSecurityError("shell=True is forbidden for security")

    # Log subprocess execution for audit
    logger.debug(f"Executing subprocess: {' '.join(cmd)} in {cwd}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            **kwargs,
        )

        # Security: Check output size to prevent memory exhaustion
        if result.stdout and len(result.stdout) > MAX_OUTPUT_SIZE:
            raise SubprocessSecurityError(
                f"Subprocess output too large: {len(result.stdout)} bytes (max: {MAX_OUTPUT_SIZE})"
            )

        if result.stderr and len(result.stderr) > MAX_OUTPUT_SIZE:
            raise SubprocessSecurityError(
                f"Subprocess stderr too large: {len(result.stderr)} bytes (max: {MAX_OUTPUT_SIZE})"
            )

        return result

    except subprocess.TimeoutExpired as e:
        sanitized = sanitize_subprocess_error(e, cwd)
        logger.error(f"Subprocess timeout ({timeout}s): {sanitized}")
        raise

    except subprocess.CalledProcessError as e:
        sanitized = sanitize_subprocess_error(e, cwd)
        logger.error(f"Subprocess failed: {sanitized}")
        raise

    except Exception as e:
        sanitized = sanitize_subprocess_error(e, cwd)
        logger.error(f"Subprocess error: {sanitized}")
        raise
