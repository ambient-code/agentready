"""Shared helpers for ADR assessor modules.

Extracted to avoid a circular import between adr_frontmatter and adr_sources.
"""

import yaml


def parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from a markdown string.

    Returns a dict if a valid frontmatter block is found, an empty dict
    for an empty block, or None if no block exists, the YAML is invalid,
    or the parsed value is not a mapping (e.g. a scalar or list).
    """
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        result = yaml.safe_load(content[3:end])
        if result is None:
            return {}
        if not isinstance(result, dict):
            return None
        return result
    except yaml.YAMLError:
        return None
