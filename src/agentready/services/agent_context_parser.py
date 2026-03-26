"""Parser for AGENTS.md and CLAUDE.md files to extract project context."""

import re
import warnings
from pathlib import Path

from ..models.agent_context import (
    ADRInfo,
    AgentContext,
    DocumentationInfo,
    LoggingInfo,
)

# Maximum file size to parse (500KB)
MAX_FILE_SIZE = 500 * 1024


class AgentContextParser:
    """Parses AGENTS.md and CLAUDE.md files to extract project context.

    Extracts structured information about test locations, logging practices,
    ADR locations, documentation formats, and directory structure.
    """

    @staticmethod
    def parse(repo_path: Path) -> AgentContext | None:
        """Parse agent context files from repository root.

        Checks AGENTS.md first, then CLAUDE.md. If both exist, merges
        with AGENTS.md taking precedence for overlapping information.

        Args:
            repo_path: Path to repository root

        Returns:
            AgentContext if AGENTS.md or CLAUDE.md found with content,
            None if neither file exists or both are empty.
        """
        agents_content = AgentContextParser._read_file(repo_path / "AGENTS.md")
        claude_content = AgentContextParser._read_file(repo_path / "CLAUDE.md")

        if agents_content is None and claude_content is None:
            return None

        # Determine source and merge content
        if agents_content is not None and claude_content is not None:
            source_file = "both"
            # AGENTS.md takes precedence; append CLAUDE.md for supplementary info
            combined_content = agents_content + "\n\n" + claude_content
            primary_content = agents_content
        elif agents_content is not None:
            source_file = "AGENTS.md"
            combined_content = agents_content
            primary_content = agents_content
        else:
            source_file = "CLAUDE.md"
            combined_content = claude_content
            primary_content = claude_content

        sections = AgentContextParser._extract_sections(primary_content)

        return AgentContext(
            source_file=source_file,
            raw_content=combined_content,
            test_directories=AgentContextParser._extract_test_directories(
                primary_content, sections
            ),
            logging_info=AgentContextParser._extract_logging_info(
                primary_content, sections
            ),
            adr_info=AgentContextParser._extract_adr_info(primary_content, sections),
            documentation_info=AgentContextParser._extract_documentation_info(
                primary_content, sections
            ),
            directory_structure=AgentContextParser._extract_directory_structure(
                primary_content, sections
            ),
            sections=sections,
        )

    @staticmethod
    def _read_file(file_path: Path) -> str | None:
        """Read a file if it exists and is within size limits.

        Returns file content or None if file doesn't exist, is empty,
        or exceeds MAX_FILE_SIZE.
        """
        try:
            if not file_path.exists():
                return None

            size = file_path.stat().st_size
            if size == 0:
                return None

            if size > MAX_FILE_SIZE:
                warnings.warn(
                    f"{file_path.name} exceeds {MAX_FILE_SIZE // 1024}KB limit "
                    f"({size // 1024}KB), skipping content parsing",
                    UserWarning,
                    stacklevel=3,
                )
                return None

            content = file_path.read_text(encoding="utf-8")
            return content if content.strip() else None

        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def _extract_sections(content: str) -> dict[str, str]:
        """Split content into sections by Markdown headings.

        Returns dict keyed by normalized heading text (lowercase, stripped).
        """
        sections: dict[str, str] = {}
        # Match ## and ### headings
        heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(content))

        if not matches:
            # No headings — treat entire content as one section
            sections["_full"] = content
            return sections

        for i, match in enumerate(matches):
            heading = match.group(2).strip().lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections[heading] = content[start:end].strip()

        return sections

    @staticmethod
    def _extract_test_directories(content: str, sections: dict[str, str]) -> list[str]:
        """Extract test directory paths from content.

        Looks for paths in directory structure sections and code blocks
        that reference test directories.
        """
        test_dirs: list[str] = []

        # Look in relevant sections
        relevant_keys = [
            k
            for k in sections
            if any(
                term in k
                for term in ["directory", "structure", "test", "running test", "layout"]
            )
        ]

        search_text = "\n".join(sections.get(k, "") for k in relevant_keys)
        if not search_text:
            search_text = content

        # Extract paths from code blocks and bullet lists that look like test dirs
        # Match patterns like: tests/, test/, nova/tests/unit/, etc.
        path_pattern = re.compile(
            r"(?:│\s*├──\s*|│\s*└──\s*|├──\s*|└──\s*|- |\* )?(\S*tests?(?:/\S*)?/?)",
            re.IGNORECASE,
        )

        for match in path_pattern.finditer(search_text):
            path = match.group(1).strip().rstrip(",")
            # Validate: relative path, no traversal
            if path and not path.startswith("/") and ".." not in path:
                # Normalize trailing slash
                if not path.endswith("/"):
                    path += "/"
                if path not in test_dirs:
                    test_dirs.append(path)

        return test_dirs

    @staticmethod
    def _extract_logging_info(
        content: str, sections: dict[str, str]
    ) -> LoggingInfo | None:
        """Extract logging framework and convention information."""
        # Known logging frameworks
        known_frameworks = [
            "structlog",
            "python-json-logger",
            "oslo.log",
            "oslo.logging",
            "loguru",
            "winston",
            "zap",
            "serilog",
            "log4j",
            "slf4j",
            "bunyan",
            "pino",
        ]

        content_lower = content.lower()
        found_frameworks: list[str] = []

        for fw in known_frameworks:
            if fw.lower() in content_lower:
                found_frameworks.append(fw)

        if not found_frameworks:
            return None

        # Check for structured logging indicators
        structured_keywords = [
            "structured log",
            "json log",
            "context-aware",
            "machine-parseable",
            "log format",
        ]
        has_structured = any(kw in content_lower for kw in structured_keywords)

        # Extract logging conventions from relevant sections
        conventions: list[str] = []
        log_sections = [
            k for k in sections if any(t in k for t in ["log", "convention", "coding"])
        ]
        for key in log_sections:
            section_text = sections[key]
            # Look for convention-style bullet points about logging
            for line in section_text.splitlines():
                line_stripped = line.strip()
                if line_stripped.startswith(("- ", "* ")) and any(
                    t in line_stripped.lower() for t in ["log", "LOG."]
                ):
                    conventions.append(line_stripped.lstrip("- *").strip())

        return LoggingInfo(
            frameworks=found_frameworks,
            conventions=conventions,
            has_structured_logging=has_structured,
        )

    @staticmethod
    def _extract_adr_info(content: str, sections: dict[str, str]) -> ADRInfo | None:
        """Extract Architecture Decision Record locations."""
        content_lower = content.lower()

        # Check for ADR-related keywords
        adr_keywords = [
            "architecture decision",
            "adr",
            "decision record",
            "specs/",
            "nova-specs",
            "approved/",
            "implemented/",
        ]

        if not any(kw in content_lower for kw in adr_keywords):
            return None

        local_paths: list[str] = []
        external_repos: list[str] = []
        doc_format = "unknown"
        directory_pattern: str | None = None

        # Look for external repository references
        # Patterns: org/repo-name, openstack/nova-specs, etc.
        repo_pattern = re.compile(
            r"(?:`|\*\*)?([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+(?:-specs?|-decisions?)?)(?:`|\*\*)?",
        )
        for match in repo_pattern.finditer(content):
            repo = match.group(1)
            # Filter out false positives (common path patterns)
            if "/" in repo and not repo.startswith(("src/", "tests/", "docs/")):
                if any(t in repo.lower() for t in ["spec", "decision", "adr"]):
                    if repo not in external_repos:
                        external_repos.append(repo)

        # Look for local ADR paths
        local_adr_patterns = [
            r"(?:docs/adr|\.adr|adr|docs/decisions)/?",
            r"specs?/[a-zA-Z0-9_<>]+/(?:approved|implemented|backlog|abandoned)/?",
        ]
        for pattern in local_adr_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                path = match.group(0)
                if path not in local_paths:
                    local_paths.append(path)

        # Detect directory pattern
        pattern_match = re.search(
            r"(specs?/[<\[]?\w+[>\]]?/(?:approved|implemented)/)", content
        )
        if pattern_match:
            directory_pattern = pattern_match.group(1)

        # Detect format
        if ".rst" in content_lower or "restructuredtext" in content_lower:
            doc_format = "rst"
        elif ".md" in content_lower and "markdown" in content_lower:
            doc_format = "markdown"

        if not local_paths and not external_repos:
            return None

        return ADRInfo(
            local_paths=local_paths,
            external_repos=external_repos,
            format=doc_format,
            directory_pattern=directory_pattern,
        )

    @staticmethod
    def _extract_documentation_info(
        content: str, sections: dict[str, str]
    ) -> DocumentationInfo | None:
        """Extract documentation format and location hints."""
        content_lower = content.lower()

        readme_format: str | None = None
        docs_directory: str | None = None
        external_docs_url: str | None = None

        # Detect README format mentions
        if "readme.rst" in content_lower:
            readme_format = "rst"
        elif "readme.txt" in content_lower:
            readme_format = "txt"
        elif "readme.md" in content_lower:
            readme_format = "md"

        # Look for docs directory
        docs_match = re.search(
            r"(?:doc|docs|documentation)/?\s*(?:directory|folder)?", content_lower
        )
        if docs_match:
            # Try to find the actual path
            path_match = re.search(r"`?(docs?/\S*)`?", content)
            if path_match:
                docs_directory = path_match.group(1).strip("`")

        # Look for external documentation URLs
        url_match = re.search(r"https?://docs\.[a-zA-Z0-9._/-]+", content)
        if url_match:
            external_docs_url = url_match.group(0)

        if (
            readme_format is None
            and docs_directory is None
            and external_docs_url is None
        ):
            return None

        return DocumentationInfo(
            readme_format=readme_format,
            docs_directory=docs_directory,
            external_docs_url=external_docs_url,
        )

    @staticmethod
    def _extract_directory_structure(
        content: str, sections: dict[str, str]
    ) -> dict[str, str]:
        """Extract documented directory purposes from content."""
        structure: dict[str, str] = {}

        # Look for directory structure sections
        relevant_keys = [
            k for k in sections if any(t in k for t in ["directory", "structure"])
        ]

        for key in relevant_keys:
            section_text = sections[key]
            # Match patterns like: ├── api/          # REST API endpoints
            dir_pattern = re.compile(
                r"(?:│\s*)?(?:├──|└──)\s*(\S+/)\s*#\s*(.+)$", re.MULTILINE
            )
            for match in dir_pattern.finditer(section_text):
                dir_name = match.group(1).strip()
                description = match.group(2).strip()
                structure[dir_name] = description

        return structure
