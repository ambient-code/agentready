"""Load prompt content from package .md files."""

from __future__ import annotations

import importlib.resources


def load_prompt(name: str) -> str:
    """Load prompt content by name from package resources.

    Looks for a file named ``{name}.md`` under the prompts package.
    Names must not contain path separators or dots (except the implied .md).

    Args:
        name: Base name of the prompt file (e.g. "claude_md_generator").

    Returns:
        Raw text content of the prompt file.

    Raises:
        FileNotFoundError: If no such prompt file exists.
    """
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(f"Invalid prompt name: {name}")
    ref = importlib.resources.files("agentready.prompts")
    path = ref / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {name}.md")
    return path.read_text(encoding="utf-8")
