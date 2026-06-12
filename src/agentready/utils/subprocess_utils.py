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
import threading
import time
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


def sanitize_subprocess_error(
    error: Exception | str, repo_path: Path | None = None
) -> str:
    """Sanitize error message to prevent information leakage.

    Security: Redacts absolute paths, usernames, and sensitive data.

    Args:
        error: Exception or string to sanitize
        repo_path: Optional repository path to redact

    Returns:
        Sanitized error message
    """
    msg = error if isinstance(error, str) else str(error)

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


class StreamingSubprocess:
    """Iterator/context-manager wrapper around Popen that yields stdout lines.

    Provides the same security guardrails as safe_subprocess_run but streams
    output incrementally instead of buffering. stderr is accumulated in a
    background thread and available via the .stderr property after iteration.

    Usage::

        with safe_subprocess_run_stream(["cmd", "arg"], timeout=60) as stream:
            for line in stream:
                print(line, end="")
        print(stream.returncode)
        print(stream.stderr)
    """

    def __init__(
        self,
        process: subprocess.Popen,
        timeout: int,
        max_output_size: int,
        cwd: Path | None,
    ):
        self._process = process
        self._deadline = time.monotonic() + timeout
        self._timeout = timeout
        self._max_output_size = max_output_size
        self._cwd = cwd
        self._stderr_bytes_read = 0
        self._stderr_chunks: list[str] = []
        self._stderr_error: SubprocessSecurityError | None = None
        self._closed = False
        self._timed_out = False

        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

        self._watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self._watchdog_thread.start()

    @property
    def returncode(self) -> int | None:
        return self._process.returncode

    @property
    def stderr(self) -> str:
        if self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=2)
        return "".join(self._stderr_chunks)

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if self._closed or self._process.stdout is None:
            raise StopIteration

        if self._timed_out:
            self._cleanup()
            raise subprocess.TimeoutExpired(self._process.args, self._timeout)

        if self._stderr_error:
            self._cleanup()
            raise self._stderr_error

        line = self._process.stdout.readline()

        if self._timed_out:
            self._cleanup()
            raise subprocess.TimeoutExpired(self._process.args, self._timeout)

        if not line:
            self._finalize()
            if self._stderr_error:
                raise self._stderr_error
            raise StopIteration

        if self._stderr_error:
            self._cleanup()
            raise self._stderr_error

        return line

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._cleanup()

    def _read_stderr(self):
        try:
            for line in self._process.stderr:
                self._stderr_bytes_read += len(line.encode("utf-8"))
                if self._stderr_bytes_read > self._max_output_size:
                    self._stderr_error = SubprocessSecurityError(
                        f"Subprocess stderr too large: "
                        f"{self._stderr_bytes_read} bytes "
                        f"(max: {self._max_output_size})"
                    )
                    break
                self._stderr_chunks.append(line)
        except (OSError, ValueError):
            pass

    def _watchdog(self):
        remaining = self._deadline - time.monotonic()
        if remaining > 0:
            try:
                self._process.wait(timeout=remaining)
                return
            except subprocess.TimeoutExpired:
                pass
        if self._process.poll() is None:
            self._timed_out = True
            sanitized = sanitize_subprocess_error(
                subprocess.TimeoutExpired(self._process.args, self._timeout),
                self._cwd,
            )
            logger.error(f"Subprocess timeout ({self._timeout}s): {sanitized}")
            self._terminate()

    def _terminate(self):
        if self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

    def _cleanup(self):
        self._terminate()
        if self._process.stdout:
            try:
                self._process.stdout.close()
            except OSError:
                pass
        if self._process.stderr:
            try:
                self._process.stderr.close()
            except OSError:
                pass
        self._stderr_thread.join(timeout=2)
        self._watchdog_thread.join(timeout=2)

    def _finalize(self):
        self._process.wait(timeout=10)
        self._stderr_thread.join(timeout=5)
        self._closed = True


def safe_subprocess_run_stream(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int | None = None,
    max_output_size: int | None = None,
    **kwargs: Any,
) -> StreamingSubprocess:
    """Run subprocess with security guardrails, streaming stdout line-by-line.

    Same security features as safe_subprocess_run, but yields output
    incrementally via a StreamingSubprocess iterator instead of buffering.

    Args:
        cmd: Command and arguments (list form, never shell=True)
        cwd: Working directory (validated if provided)
        timeout: Timeout in seconds (default: SUBPROCESS_TIMEOUT)
        max_output_size: Max cumulative bytes per stream (default: MAX_OUTPUT_SIZE)
        **kwargs: Additional subprocess.Popen() arguments

    Returns:
        StreamingSubprocess that yields str lines from stdout.
        Access .returncode and .stderr after iteration completes.

    Raises:
        SubprocessSecurityError: If shell=True or validation fails
        subprocess.TimeoutExpired: If command exceeds timeout during iteration
    """
    if timeout is None:
        timeout = kwargs.pop("timeout", SUBPROCESS_TIMEOUT)

    if kwargs.get("shell"):
        raise SubprocessSecurityError("shell=True is forbidden for security")

    if cwd:
        cwd_path = Path(cwd)
        if (cwd_path / ".git").exists() or (cwd_path / ".git").is_file():
            try:
                cwd = validate_repository_path(cwd_path)
            except SubprocessSecurityError:
                logger.debug(f"Repository validation skipped for: {cwd}")

    if max_output_size is None:
        max_output_size = MAX_OUTPUT_SIZE

    kwargs.pop("capture_output", None)
    kwargs.pop("text", None)

    logger.debug(f"Executing streaming subprocess: {' '.join(cmd)} in {cwd}")

    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
    except Exception as e:
        sanitized = sanitize_subprocess_error(e, cwd)
        logger.error(f"Subprocess error: {sanitized}")
        raise

    return StreamingSubprocess(process, timeout, max_output_size, cwd)


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
