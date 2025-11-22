"""Privacy utilities for sanitizing sensitive data in reports and logs.

Security features:
- Path sanitization (redact usernames, home directories)
- Command-line argument redaction
- API key/credential masking
- Email address redaction
"""

import getpass
import re
from pathlib import Path
from typing import List


def sanitize_path(path: Path | str, relative_to: Path | None = None) -> str:
    """Sanitize file path for public display.

    Security: Redacts usernames, home directories, and converts to relative paths.

    Args:
        path: Path to sanitize
        relative_to: Optional base path for relative path calculation

    Returns:
        Sanitized path string safe for public display

    Examples:
        >>> sanitize_path(Path("/Users/john/project/src"))
        "~/project/src"
        >>> sanitize_path(Path("/home/jane/secret/data.txt"), relative_to=Path.cwd())
        "secret/data.txt"
    """
    path_obj = Path(path) if isinstance(path, str) else path

    # Try to make relative to specified directory
    if relative_to:
        try:
            if path_obj.is_relative_to(relative_to):
                return str(path_obj.relative_to(relative_to))
        except (ValueError, RuntimeError):
            pass

    # Convert to string for replacements
    path_str = str(path_obj)

    # Redact home directory
    try:
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = path_str.replace(home, "~")
    except (RuntimeError, OSError):
        pass

    # Redact username
    try:
        username = getpass.getuser()
        path_str = path_str.replace(f"/{username}/", "/<user>/")
        path_str = path_str.replace(f"\\{username}\\", "\\<user>\\")
        path_str = path_str.replace(f"/Users/{username}/", "~/")
        path_str = path_str.replace(f"/home/{username}/", "~/")
        path_str = path_str.replace(f"C:\\Users\\{username}\\", "~\\")
    except Exception:
        pass

    return path_str


def sanitize_command_args(args: List[str]) -> List[str]:
    """Sanitize command-line arguments.

    Security: Redacts config files, API keys, and sensitive paths.

    Args:
        args: Command-line arguments list

    Returns:
        Sanitized arguments list

    Examples:
        >>> sanitize_command_args(["agentready", "assess", "/secret/path", "--config", "~/.credentials.yaml"])
        ["agentready", "assess", "<path>", "--config", "<config-file>"]
    """
    sanitized = []
    skip_next = False

    for i, arg in enumerate(args):
        if skip_next:
            sanitized.append("<redacted>")
            skip_next = False
            continue

        # Redact values after these flags
        if arg in ("--config", "-c", "--api-key", "--token", "--password"):
            sanitized.append(arg)
            skip_next = True
            continue

        # Redact absolute paths
        if (
            arg.startswith("/")
            or arg.startswith("~")
            or (len(arg) > 2 and arg[1] == ":")
        ):
            sanitized.append(sanitize_path(arg))
            continue

        # Redact API keys in arguments
        if re.match(r"sk-[a-zA-Z0-9-]{20,}", arg):
            sanitized.append("<api-key>")
            continue

        sanitized.append(arg)

    return sanitized


def sanitize_error_message(message: str, repo_path: Path | None = None) -> str:
    """Sanitize error message.

    Security: Removes paths, API keys, emails, and sensitive data.

    Args:
        message: Error message to sanitize
        repo_path: Optional repository path to redact

    Returns:
        Sanitized error message

    Examples:
        >>> sanitize_error_message("Error in /Users/john/project/file.py: sk-ant-123")
        "Error in <path>/file.py: <api-key>"
    """
    if not message:
        return message

    msg = str(message)

    # Redact repository path if provided
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

    # Redact absolute paths (Unix and Windows)
    msg = re.sub(r"/[\w/.-]+", "<path>", msg)
    msg = re.sub(r"C:\\[\w\\.-]+", "<path>", msg)

    # Redact API keys
    msg = re.sub(r"sk-ant-[a-zA-Z0-9-]+", "<api-key>", msg)
    msg = re.sub(r"sk-[a-zA-Z0-9-]{20,}", "<api-key>", msg)

    # Redact email addresses
    msg = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "<email>",
        msg,
    )

    # Truncate if too long
    if len(msg) > 1000:
        msg = msg[:1000] + "... (truncated)"

    return msg


def shorten_commit_hash(commit_hash: str) -> str:
    """Shorten git commit hash to 8 characters.

    Security: Reduces information exposure while maintaining traceability.

    Args:
        commit_hash: Full commit hash

    Returns:
        Shortened 8-character hash

    Examples:
        >>> shorten_commit_hash("abc123def456789012345678901234567890abcd")
        "abc123de"
    """
    if not commit_hash:
        return commit_hash
    return commit_hash[:8]


def sanitize_metadata(metadata: dict) -> dict:
    """Sanitize metadata dictionary.

    Security: Redacts sensitive fields while preserving structure.

    Args:
        metadata: Metadata dictionary

    Returns:
        Sanitized metadata dictionary
    """
    sanitized = {}

    for key, value in metadata.items():
        # Redact command field
        if key == "command" and isinstance(value, str):
            # Parse as space-separated args
            args = value.split()
            sanitized_args = sanitize_command_args(args)
            sanitized[key] = " ".join(sanitized_args)
        # Sanitize path-like strings
        elif isinstance(value, str) and ("/" in value or "\\" in value):
            sanitized[key] = sanitize_path(value)
        else:
            sanitized[key] = value

    return sanitized
