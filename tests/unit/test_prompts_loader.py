"""Unit tests for prompts loader."""

import importlib.resources

import pytest

from agentready.prompts import load_prompt


def test_load_prompt_success():
    """load_prompt returns content for existing prompt file."""
    content = load_prompt("claude_md_generator")
    assert content
    assert "senior technical documentation architect" in content
    assert "CLAUDE.md" in content


def test_load_prompt_invalid_name_raises_value_error():
    """load_prompt raises ValueError for names with path separators or leading dot."""
    with pytest.raises(ValueError, match="Invalid prompt name"):
        load_prompt("../malicious")
    with pytest.raises(ValueError, match="Invalid prompt name"):
        load_prompt("foo/bar")
    with pytest.raises(ValueError, match="Invalid prompt name"):
        load_prompt(".hidden")


def test_load_prompt_missing_file_raises_file_not_found_error():
    """load_prompt raises FileNotFoundError for non-existent prompt."""
    with pytest.raises(FileNotFoundError, match="nonexistent_prompt"):
        load_prompt("nonexistent_prompt")


def test_prompts_packaged_correctly():
    """Ensure .md prompt files are included in package distribution."""
    ref = importlib.resources.files("agentready.prompts")
    assert (ref / "claude_md_generator.md").is_file()
