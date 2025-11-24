"""Unit tests for centralized security utilities."""

import tempfile
from pathlib import Path

import pytest

from agentready.utils.security import (
    sanitize_for_html,
    sanitize_for_json,
    validate_config_dict,
    validate_filename,
    validate_path,
    validate_url,
)


class TestValidatePath:
    """Test path validation and sanitization."""

    def test_validate_path_basic(self):
        """Test basic path validation."""
        path = validate_path("/tmp/test")
        assert path == Path("/tmp/test").resolve()

    def test_validate_path_empty_raises(self):
        """Test empty path raises ValueError."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path("")

    def test_validate_path_none_raises(self):
        """Test None path raises ValueError."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path(None)

    def test_validate_path_system_dirs_blocked_by_default(self):
        """Test system directories blocked by default."""
        # Note: /etc and /sys may resolve differently on different platforms
        # (e.g., /etc -> /private/etc on macOS)
        with pytest.raises(ValueError, match="sensitive system directory"):
            validate_path("/usr/bin/python")

        with pytest.raises(ValueError, match="sensitive system directory"):
            validate_path("/bin/bash")

    def test_validate_path_system_dirs_allowed_when_flag_set(self):
        """Test system directories allowed with flag."""
        path = validate_path("/usr/bin/python", allow_system_dirs=True)
        assert path == Path("/usr/bin/python").resolve()

    def test_validate_path_must_exist(self):
        """Test must_exist flag."""
        with tempfile.NamedTemporaryFile() as tmp:
            path = validate_path(tmp.name, must_exist=True, allow_system_dirs=True)
            assert path.exists()

        with pytest.raises(ValueError, match="does not exist"):
            validate_path("/nonexistent/path", must_exist=True)

    def test_validate_path_base_dir_constraint(self):
        """Test path must be within base_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subdir = base / "subdir"
            subdir.mkdir()

            # Valid: within base_dir
            path = validate_path(subdir, base_dir=base)
            assert path == subdir.resolve()

            # Invalid: outside base_dir
            with pytest.raises(ValueError, match="Path traversal detected"):
                validate_path("/tmp", base_dir=base)

    def test_validate_path_resolves_relative(self):
        """Test relative paths are resolved to absolute."""
        path = validate_path(".", allow_system_dirs=True)
        assert path.is_absolute()
        assert path == Path.cwd()


class TestValidateConfigDict:
    """Test configuration validation."""

    def test_validate_config_dict_basic(self):
        """Test basic config validation."""
        schema = {"name": str, "count": int}
        data = {"name": "test", "count": 42}

        result = validate_config_dict(data, schema)
        assert result == data

    def test_validate_config_dict_not_dict_raises(self):
        """Test non-dict raises ValueError."""
        with pytest.raises(ValueError, match="Config must be a dict"):
            validate_config_dict("not a dict", {})

    def test_validate_config_dict_unknown_keys_raises(self):
        """Test unknown keys raise ValueError."""
        schema = {"name": str}
        data = {"name": "test", "unknown": "value"}

        with pytest.raises(ValueError, match="Unknown config keys: unknown"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_wrong_type_raises(self):
        """Test wrong value type raises ValueError."""
        schema = {"count": int}
        data = {"count": "not an int"}

        with pytest.raises(ValueError, match="'count' must be int"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_nested_dict(self):
        """Test nested dict validation."""
        schema = {"weights": {str: float}}
        data = {"weights": {"attr1": 0.5, "attr2": 0.3}}

        result = validate_config_dict(data, schema)
        assert result == data

    def test_validate_config_dict_nested_dict_wrong_key_type(self):
        """Test nested dict with wrong key type."""
        schema = {"weights": {str: float}}
        data = {"weights": {123: 0.5}}  # int key instead of str

        with pytest.raises(ValueError, match="'weights' keys must be str"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_nested_dict_wrong_value_type(self):
        """Test nested dict with wrong value type."""
        schema = {"weights": {str: float}}
        data = {"weights": {"attr1": "not a float"}}

        with pytest.raises(ValueError, match="'weights' values must be"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_list(self):
        """Test list validation."""
        schema = {"items": [str]}
        data = {"items": ["a", "b", "c"]}

        result = validate_config_dict(data, schema)
        assert result == data

    def test_validate_config_dict_list_wrong_type(self):
        """Test list with wrong type."""
        schema = {"items": [str]}
        data = {"items": "not a list"}

        with pytest.raises(ValueError, match="'items' must be a list"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_list_wrong_item_type(self):
        """Test list with wrong item type."""
        schema = {"items": [str]}
        data = {"items": ["a", 123, "c"]}

        with pytest.raises(ValueError, match="'items' items must be str"):
            validate_config_dict(data, schema)

    def test_validate_config_dict_optional_fields(self):
        """Test optional fields (not in data) are skipped."""
        schema = {"required": str, "optional": int}
        data = {"required": "value"}

        result = validate_config_dict(data, schema)
        assert result == data


class TestSanitizeForHTML:
    """Test HTML sanitization."""

    def test_sanitize_for_html_basic(self):
        """Test basic HTML escaping."""
        result = sanitize_for_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "alert" in result

    def test_sanitize_for_html_ampersand(self):
        """Test ampersand escaping."""
        result = sanitize_for_html("5 < 10 & 10 > 5")
        assert result == "5 &lt; 10 &amp; 10 &gt; 5"

    def test_sanitize_for_html_quotes(self):
        """Test quote escaping."""
        result = sanitize_for_html('He said "hello"')
        assert "&quot;" in result or "&#x27;" in result

    def test_sanitize_for_html_empty_string(self):
        """Test empty string returns empty."""
        assert sanitize_for_html("") == ""

    def test_sanitize_for_html_none_returns_empty(self):
        """Test None returns empty string."""
        assert sanitize_for_html(None) == ""

    def test_sanitize_for_html_allow_safe_tags(self):
        """Test safe tags preserved when allowed."""
        result = sanitize_for_html("<b>Bold</b> text", allow_safe_tags=True)
        assert result == "<b>Bold</b> text"

        result = sanitize_for_html("<code>code</code>", allow_safe_tags=True)
        assert result == "<code>code</code>"

    def test_sanitize_for_html_block_unsafe_tags_even_with_flag(self):
        """Test unsafe tags blocked even with allow_safe_tags."""
        result = sanitize_for_html("<script>bad</script>", allow_safe_tags=True)
        assert "&lt;script&gt;" in result


class TestSanitizeForJSON:
    """Test JSON sanitization."""

    def test_sanitize_for_json_basic_types(self):
        """Test basic types pass through."""
        assert sanitize_for_json(None) is None
        assert sanitize_for_json(True) is True
        assert sanitize_for_json(42) == 42
        assert sanitize_for_json(3.14) == 3.14
        assert sanitize_for_json("text") == "text"

    def test_sanitize_for_json_removes_control_chars(self):
        """Test control characters removed."""
        result = sanitize_for_json("text\x00with\x01control\x1fchars")
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x1f" not in result
        assert "text" in result

    def test_sanitize_for_json_preserves_newline_tab(self):
        """Test newline and tab preserved."""
        result = sanitize_for_json("line1\nline2\ttab")
        assert "\n" in result
        assert "\t" in result

    def test_sanitize_for_json_list(self):
        """Test list sanitization."""
        result = sanitize_for_json(["a", 1, True, None])
        assert result == ["a", 1, True, None]

    def test_sanitize_for_json_dict(self):
        """Test dict sanitization."""
        result = sanitize_for_json({"key": "value", "num": 42})
        assert result == {"key": "value", "num": 42}

    def test_sanitize_for_json_nested(self):
        """Test nested structure sanitization."""
        data = {"list": [1, 2, {"nested": "value"}], "dict": {"key": [1, 2]}}
        result = sanitize_for_json(data)
        assert result == data

    def test_sanitize_for_json_max_depth_exceeded(self):
        """Test max depth protection."""
        # Create deeply nested structure
        deep = {"a": {"b": {"c": {"d": {"e": "value"}}}}}

        with pytest.raises(ValueError, match="Maximum nesting depth exceeded"):
            sanitize_for_json(deep, max_depth=3)

    def test_sanitize_for_json_converts_unsupported_types(self):
        """Test unsupported types converted to string."""
        result = sanitize_for_json(Path("/tmp/test"))
        assert isinstance(result, str)
        assert "tmp" in result


class TestValidateURL:
    """Test URL validation."""

    def test_validate_url_https(self):
        """Test HTTPS URLs allowed."""
        url = validate_url("https://github.com/user/repo")
        assert url == "https://github.com/user/repo"

    def test_validate_url_http(self):
        """Test HTTP URLs allowed."""
        url = validate_url("http://example.com")
        assert url == "http://example.com"

    def test_validate_url_empty_raises(self):
        """Test empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            validate_url("")

    def test_validate_url_javascript_blocked(self):
        """Test javascript: scheme blocked."""
        with pytest.raises(ValueError, match="Dangerous URL scheme: javascript"):
            validate_url("javascript:alert(1)")

    def test_validate_url_data_blocked(self):
        """Test data: scheme blocked."""
        with pytest.raises(ValueError, match="Dangerous URL scheme: data"):
            validate_url("data:text/html,<script>alert(1)</script>")

    def test_validate_url_vbscript_blocked(self):
        """Test vbscript: scheme blocked."""
        with pytest.raises(ValueError, match="Dangerous URL scheme: vbscript"):
            validate_url("vbscript:alert(1)")

    def test_validate_url_file_blocked(self):
        """Test file: scheme blocked."""
        with pytest.raises(ValueError, match="Dangerous URL scheme: file"):
            validate_url("file:///etc/passwd")

    def test_validate_url_relative_allowed(self):
        """Test relative URLs allowed."""
        url = validate_url("/path/to/page")
        assert url == "/path/to/page"

        url = validate_url("../relative")
        assert url == "../relative"

    def test_validate_url_custom_schemes(self):
        """Test custom allowed schemes."""
        url = validate_url("ftp://ftp.example.com/file.txt")
        assert url == "ftp://ftp.example.com/file.txt"

    def test_validate_url_custom_schemes_blocked(self):
        """Test URL with disallowed custom scheme."""
        with pytest.raises(ValueError, match="URL must use allowed scheme"):
            validate_url("gopher://example.com", allowed_schemes=["http", "https"])


class TestValidateFilename:
    """Test filename validation."""

    def test_validate_filename_basic(self):
        """Test basic filename validation."""
        filename = validate_filename("report.html")
        assert filename == "report.html"

    def test_validate_filename_empty_raises(self):
        """Test empty filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            validate_filename("")

    def test_validate_filename_null_byte_raises(self):
        """Test null byte in filename raises ValueError."""
        with pytest.raises(ValueError, match="cannot contain null bytes"):
            validate_filename("file\x00.txt")

    def test_validate_filename_slash_blocked_by_default(self):
        """Test forward slash blocked by default."""
        with pytest.raises(ValueError, match="cannot contain path separators"):
            validate_filename("path/to/file.txt")

    def test_validate_filename_backslash_blocked_by_default(self):
        """Test backslash blocked by default."""
        with pytest.raises(ValueError, match="cannot contain path separators"):
            validate_filename("path\\to\\file.txt")

    def test_validate_filename_slash_allowed_with_flag(self):
        """Test slash allowed with flag."""
        filename = validate_filename("path/to/file.txt", allow_path_separators=True)
        assert filename == "path/to/file.txt"

    def test_validate_filename_dotdot_blocked(self):
        """Test '..' path traversal blocked."""
        # The slash check happens first, so we get "path separators" error
        with pytest.raises(ValueError, match="cannot contain path separators"):
            validate_filename("../etc/passwd")

        # Test pure '..' (no slash)
        with pytest.raises(ValueError, match="cannot start with '..'"):
            validate_filename("..")

    def test_validate_filename_single_dot_allowed(self):
        """Test single dot allowed (hidden files)."""
        filename = validate_filename(".gitignore")
        assert filename == ".gitignore"

    def test_validate_filename_special_chars_allowed(self):
        """Test special characters allowed in filename."""
        filename = validate_filename("file-name_with.special+chars.txt")
        assert filename == "file-name_with.special+chars.txt"
