"""Centralized security validation and sanitization.

This module consolidates security validation logic that was previously
duplicated across multiple modules (cli/main.py, reporters/html.py,
services/bootstrap.py, services/llm_cache.py).

Security principles:
- Path traversal prevention (validate all file paths)
- XSS prevention (sanitize HTML output)
- Injection prevention (validate configuration inputs)
- Sensitive directory protection (block system paths)
"""

import html
import re
from pathlib import Path
from typing import Any


def validate_path(
    path: str | Path,
    allow_system_dirs: bool = False,
    must_exist: bool = False,
    base_dir: Path | None = None,
) -> Path:
    """Validate and sanitize file paths to prevent path traversal attacks.

    Args:
        path: Path to validate (string or Path object)
        allow_system_dirs: If False, block sensitive system directories
        must_exist: If True, raise error if path doesn't exist
        base_dir: If provided, ensure path is within this directory

    Returns:
        Validated Path object (resolved to absolute path)

    Raises:
        ValueError: If path is invalid, traverses outside base_dir,
                   points to sensitive directory, or doesn't exist

    Examples:
        >>> validate_path("/tmp/test", allow_system_dirs=True)
        PosixPath('/tmp/test')
        >>> validate_path("../../../etc/passwd")  # doctest: +SKIP
        ValueError: Cannot be in sensitive system directory: /etc/passwd
        >>> validate_path("data/report.html", base_dir=Path.cwd())
        PosixPath('/current/dir/data/report.html')
    """
    if not path:
        raise ValueError("Path cannot be empty")

    # Convert to Path and resolve to absolute path
    try:
        resolved_path = Path(path).resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Check if path exists (if required)
    if must_exist and not resolved_path.exists():
        raise ValueError(f"Path does not exist: {resolved_path}")

    # Check base_dir constraint FIRST (takes precedence over sensitive dirs)
    if base_dir is not None:
        base_resolved = Path(base_dir).resolve()
        try:
            resolved_path.relative_to(base_resolved)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: {resolved_path} is outside {base_resolved}"
            )
        # If base_dir check passed, path is explicitly allowed - skip sensitive dir check
        return resolved_path

    # Block sensitive system directories (unless explicitly allowed)
    if not allow_system_dirs:
        sensitive_dirs = [
            "/etc",
            "/sys",
            "/proc",
            "/var",
            "/usr",
            "/bin",
            "/sbin",
            "/private/etc",  # macOS
            "/private/var",  # macOS
        ]
        if any(str(resolved_path).startswith(p) for p in sensitive_dirs):
            raise ValueError(
                f"Cannot be in sensitive system directory: {resolved_path}"
            )

    return resolved_path


def validate_config_dict(data: Any, schema: dict[str, type]) -> dict:
    """Validate configuration dictionary against schema.

    Prevents YAML injection attacks and malformed configuration by validating
    all keys and value types against expected schema.

    Args:
        data: Configuration data from YAML (must be dict)
        schema: Expected schema mapping keys to types
                Format: {"key": type | list[type] | dict[type, type]}

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If data is not a dict, has unknown keys, or values
                   don't match expected types

    Examples:
        >>> schema = {"weights": dict, "excluded": list}
        >>> validate_config_dict({"weights": {}, "excluded": []}, schema)
        {'weights': {}, 'excluded': []}
        >>> validate_config_dict("not a dict", schema)  # doctest: +SKIP
        ValueError: Config must be a dict, got str
    """
    # Validate data is a dict
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a dict, got {type(data).__name__}")

    # Validate no unknown keys
    allowed_keys = set(schema.keys())
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown_keys))}")

    # Validate each field
    validated = {}
    for key, expected_type in schema.items():
        if key not in data:
            continue  # Optional fields

        value = data[key]

        # Handle nested dict validation (e.g., dict[str, float])
        if isinstance(expected_type, dict):
            if not isinstance(value, dict):
                raise ValueError(f"'{key}' must be a dict, got {type(value).__name__}")
            key_type, val_type = list(expected_type.items())[0]
            for k, v in value.items():
                if not isinstance(k, key_type):
                    raise ValueError(
                        f"'{key}' keys must be {key_type.__name__}, "
                        f"got {type(k).__name__}"
                    )
                if not isinstance(v, val_type):
                    raise ValueError(
                        f"'{key}' values must be {val_type.__name__}, "
                        f"got {type(v).__name__} for '{k}'"
                    )

        # Handle list validation (e.g., list[str])
        elif isinstance(expected_type, list):
            if not isinstance(value, list):
                raise ValueError(f"'{key}' must be a list, got {type(value).__name__}")
            item_type = expected_type[0]
            for item in value:
                if not isinstance(item, item_type):
                    raise ValueError(
                        f"'{key}' items must be {item_type.__name__}, "
                        f"got {type(item).__name__}"
                    )

        # Handle simple type validation
        else:
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"'{key}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        validated[key] = value

    return validated


def sanitize_for_html(text: str, allow_safe_tags: bool = False) -> str:
    """Sanitize text for safe HTML rendering to prevent XSS attacks.

    Args:
        text: Text to sanitize
        allow_safe_tags: If True, preserve <code>, <pre>, <b>, <i>, <em>, <strong>

    Returns:
        HTML-safe string with dangerous characters escaped

    Examples:
        >>> sanitize_for_html("<script>alert('xss')</script>")
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
        >>> sanitize_for_html("<b>Bold</b>", allow_safe_tags=True)
        '<b>Bold</b>'
        >>> sanitize_for_html("5 < 10 & 10 > 5")
        '5 &lt; 10 &amp; 10 &gt; 5'
    """
    if not text:
        return ""

    # Always escape HTML special characters
    escaped = html.escape(str(text), quote=True)

    # If safe tags allowed, unescape them
    if allow_safe_tags:
        safe_tags = ["code", "pre", "b", "i", "em", "strong", "br", "hr"]
        for tag in safe_tags:
            # Unescape opening and closing tags
            escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
            escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

    return escaped


def sanitize_for_json(obj: Any, max_depth: int = 10) -> Any:
    """Sanitize object for safe JSON serialization.

    Recursively sanitizes objects to prevent JSON injection and ensure
    safe serialization. Handles nested structures up to max_depth.

    Args:
        obj: Object to sanitize (dict, list, str, number, bool, None)
        max_depth: Maximum nesting depth (prevents infinite recursion)

    Returns:
        Sanitized object safe for JSON serialization

    Raises:
        ValueError: If max_depth exceeded (possible circular reference)

    Examples:
        >>> sanitize_for_json({"key": "value", "nested": {"x": 1}})
        {'key': 'value', 'nested': {'x': 1}}
        >>> sanitize_for_json("<script>bad</script>")
        '<script>bad</script>'
    """
    if max_depth <= 0:
        raise ValueError("Maximum nesting depth exceeded (possible circular reference)")

    # Handle None, bool, numbers (safe as-is)
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj

    # Handle strings (validate no control characters except newline/tab)
    if isinstance(obj, str):
        # Remove dangerous control characters but keep \n and \t
        safe_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", obj)
        return safe_str

    # Handle lists recursively
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item, max_depth - 1) for item in obj]

    # Handle dicts recursively
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v, max_depth - 1) for k, v in obj.items()}

    # Unsupported type - convert to string
    return str(obj)


def validate_url(url: str, allowed_schemes: list[str] | None = None) -> str:
    """Validate URL for safe rendering in HTML/markdown.

    Args:
        url: URL to validate
        allowed_schemes: Allowed URL schemes (default: http, https)

    Returns:
        Validated URL

    Raises:
        ValueError: If URL contains dangerous scheme (javascript:, data:, etc.)

    Examples:
        >>> validate_url("https://github.com/user/repo")
        'https://github.com/user/repo'
        >>> validate_url("javascript:alert(1)")  # doctest: +SKIP
        ValueError: Dangerous URL scheme: javascript
    """
    if not url:
        raise ValueError("URL cannot be empty")

    if allowed_schemes is None:
        allowed_schemes = ["http", "https", "ftp", "ftps"]

    # Check for dangerous schemes
    dangerous_schemes = ["javascript", "data", "vbscript", "file"]
    url_lower = url.lower().strip()

    for scheme in dangerous_schemes:
        if url_lower.startswith(f"{scheme}:"):
            raise ValueError(f"Dangerous URL scheme: {scheme}")

    # Validate allowed schemes
    has_allowed_scheme = any(
        url_lower.startswith(f"{scheme}:") for scheme in allowed_schemes
    )

    # Allow relative URLs (no scheme)
    if ":" not in url_lower.split("/")[0]:
        return url

    if not has_allowed_scheme:
        raise ValueError(f"URL must use allowed scheme: {', '.join(allowed_schemes)}")

    return url


def validate_filename(filename: str, allow_path_separators: bool = False) -> str:
    """Validate filename to prevent path traversal in cache keys, etc.

    Args:
        filename: Filename to validate
        allow_path_separators: If False, reject '/' and '\\'

    Returns:
        Validated filename

    Raises:
        ValueError: If filename contains path separators, null bytes,
                   or other dangerous characters

    Examples:
        >>> validate_filename("report.html")
        'report.html'
        >>> validate_filename("../../../etc/passwd")  # doctest: +SKIP
        ValueError: Filename cannot contain path separators
        >>> validate_filename("file\\x00.txt")  # doctest: +SKIP
        ValueError: Filename cannot contain null bytes
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Check for null bytes (always dangerous)
    if "\x00" in filename:
        raise ValueError("Filename cannot contain null bytes")

    # Check for path separators (if not allowed)
    if not allow_path_separators:
        if "/" in filename or "\\" in filename:
            raise ValueError("Filename cannot contain path separators (/ or \\)")

    # Check for dangerous patterns
    if filename.startswith(".") and len(filename) > 1 and filename[1] == ".":
        raise ValueError("Filename cannot start with '..' (path traversal)")

    return filename
