"""Tests for AgentContextParser."""

import os
from pathlib import Path

import pytest

from agentready.models.agent_context import AgentContext
from agentready.services.agent_context_parser import AgentContextParser


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a minimal git repo structure."""
    (tmp_path / ".git").mkdir()
    return tmp_path


class TestParseNoFiles:
    """Test parse returns None when no agent files exist."""

    def test_no_files_returns_none(self, tmp_repo):
        result = AgentContextParser.parse(tmp_repo)
        assert result is None


class TestParseAgentsMdOnly:
    """Test parsing with only AGENTS.md present."""

    def test_basic_agents_md(self, tmp_repo):
        (tmp_repo / "AGENTS.md").write_text("# My Project\n\nSome content here.")
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.source_file == "AGENTS.md"
        assert "My Project" in result.raw_content

    def test_empty_agents_md_returns_none(self, tmp_repo):
        (tmp_repo / "AGENTS.md").write_text("")
        result = AgentContextParser.parse(tmp_repo)
        assert result is None

    def test_whitespace_only_returns_none(self, tmp_repo):
        (tmp_repo / "AGENTS.md").write_text("   \n\n  ")
        result = AgentContextParser.parse(tmp_repo)
        assert result is None


class TestParseClaudeMdOnly:
    """Test parsing with only CLAUDE.md present."""

    def test_basic_claude_md(self, tmp_repo):
        (tmp_repo / "CLAUDE.md").write_text("# Claude Config\n\nProject setup.")
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.source_file == "CLAUDE.md"


class TestParseBothFiles:
    """Test merge behavior when both files exist."""

    def test_merge_precedence(self, tmp_repo):
        (tmp_repo / "AGENTS.md").write_text("# AGENTS content\n\nFrom agents.")
        (tmp_repo / "CLAUDE.md").write_text("# CLAUDE content\n\nFrom claude.")
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.source_file == "both"
        # Both contents should be in raw_content
        assert "AGENTS content" in result.raw_content
        assert "CLAUDE content" in result.raw_content


class TestLargeFileSkip:
    """Test that files exceeding 500KB are skipped."""

    def test_large_file_skipped(self, tmp_repo):
        # Create a file larger than 500KB
        large_content = "x" * (501 * 1024)
        (tmp_repo / "AGENTS.md").write_text(large_content)
        with pytest.warns(UserWarning, match="exceeds"):
            result = AgentContextParser.parse(tmp_repo)
        assert result is None


class TestExtractTestDirectories:
    """Test extraction of test directory paths."""

    def test_extracts_test_dirs_from_structure(self, tmp_repo):
        content = """# Directory Structure

```
nova/
├── api/          # REST API endpoints
├── tests/        # Unit and functional tests
│   ├── unit/
│   └── functional/
```
"""
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert any("tests/" in d for d in result.test_directories)

    def test_rejects_absolute_paths(self, tmp_repo):
        content = "## Tests\n\nTests are at /absolute/tests/ path."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert not any(d.startswith("/") for d in result.test_directories)

    def test_rejects_path_traversal(self, tmp_repo):
        content = "## Tests\n\nTests are at ../outside/tests/ path."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert not any(".." in d for d in result.test_directories)


class TestExtractLoggingInfo:
    """Test extraction of logging framework information."""

    def test_detects_oslo_log(self, tmp_repo):
        content = """# Oslo Libraries

| Library | Purpose |
|---------|---------|
| `oslo.log` | Structured logging with context-aware formatters |

## Coding Conventions

### Logging
- Log messages must NOT be translated (N319)
- Use `LOG.warning` not `LOG.warn` (N352)
"""
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.logging_info is not None
        assert "oslo.log" in result.logging_info.frameworks
        assert result.logging_info.has_structured_logging

    def test_detects_structlog(self, tmp_repo):
        content = "# Config\n\nWe use structlog for structured JSON logging."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.logging_info is not None
        assert "structlog" in result.logging_info.frameworks

    def test_no_logging_returns_none(self, tmp_repo):
        content = "# Project\n\nNo logging info here."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.logging_info is None


class TestExtractADRInfo:
    """Test extraction of ADR information."""

    def test_detects_external_specs_repo(self, tmp_repo):
        content = """# Project Overview

- **Architecture decisions**: Tracked in **nova-specs** (`openstack/nova-specs`):
  - `specs/<release>/approved/` — accepted specs
  - `specs/<release>/implemented/` — specs that have landed
"""
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.adr_info is not None
        assert "openstack/nova-specs" in result.adr_info.external_repos

    def test_detects_local_adr_dir(self, tmp_repo):
        content = "# Project\n\nADRs are in `docs/adr/` directory."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.adr_info is not None
        assert any("docs/adr" in p for p in result.adr_info.local_paths)

    def test_no_adr_returns_none(self, tmp_repo):
        content = "# Project\n\nJust a regular project."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.adr_info is None


class TestExtractDocumentationInfo:
    """Test extraction of documentation information."""

    def test_detects_rst_format(self, tmp_repo):
        content = "# Project\n\nDocumentation is in README.rst format."
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.documentation_info is not None
        assert result.documentation_info.readme_format == "rst"

    def test_detects_external_docs_url(self, tmp_repo):
        content = "# Project\n\nDocs: https://docs.openstack.org/nova/latest/"
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.documentation_info is not None
        assert "docs.openstack.org" in result.documentation_info.external_docs_url


class TestExtractDirectoryStructure:
    """Test extraction of directory purposes."""

    def test_extracts_dir_descriptions(self, tmp_repo):
        content = """## Directory Structure

```
nova/
├── api/          # REST API endpoints
├── compute/      # Compute service core
├── scheduler/    # VM scheduling logic
```
"""
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert "api/" in result.directory_structure
        assert "REST API" in result.directory_structure["api/"]


class TestNonStandardFormatting:
    """Test parser handles non-standard Markdown formatting."""

    def test_no_headings_still_parses(self, tmp_repo):
        content = (
            "This project uses structlog for logging.\n"
            "Tests are in the tests/ directory.\n"
            "ADRs tracked in docs/adr/ folder."
        )
        (tmp_repo / "AGENTS.md").write_text(content)
        result = AgentContextParser.parse(tmp_repo)
        assert result is not None
        assert result.logging_info is not None
        assert "structlog" in result.logging_info.frameworks
