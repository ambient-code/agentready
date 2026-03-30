"""Agent context model for parsed AGENTS.md / CLAUDE.md content."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LoggingInfo:
    """Extracted logging framework and convention details."""

    frameworks: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    has_structured_logging: bool = False


@dataclass(frozen=True)
class ADRInfo:
    """Architecture Decision Record locations and format."""

    local_paths: list[str] = field(default_factory=list)
    external_repos: list[str] = field(default_factory=list)
    format: str = "unknown"
    directory_pattern: str | None = None


@dataclass(frozen=True)
class DocumentationInfo:
    """Documentation format and location hints."""

    readme_format: str | None = None
    docs_directory: str | None = None
    external_docs_url: str | None = None


@dataclass(frozen=True)
class AgentContext:
    """Parsed representation of AGENTS.md and/or CLAUDE.md content.

    Immutable after construction. Created once per assessment run
    by AgentContextParser and passed to assessors as supplementary evidence.
    """

    source_file: str
    raw_content: str
    test_directories: list[str] = field(default_factory=list)
    logging_info: LoggingInfo | None = None
    adr_info: ADRInfo | None = None
    documentation_info: DocumentationInfo | None = None
    directory_structure: dict[str, str] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
