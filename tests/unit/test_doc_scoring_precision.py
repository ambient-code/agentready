"""Tests for ArchitectureDecisionsAssessor.

Covers:
- Integer division regression in _check_template_compliance()
- Case-insensitive and extended directory path detection (#379, #414)
- Partial credit via CLAUDE.md/AGENTS.md architecture sections (#392)
"""

import pytest

from agentready.assessors.documentation import ArchitectureDecisionsAssessor
from agentready.models.repository import Repository


@pytest.fixture
def assessor():
    """Create an ArchitectureDecisionsAssessor instance."""
    return ArchitectureDecisionsAssessor()


def _make_adr_files(tmp_path, count):
    """Create ADR files that contain all required sections."""
    files = []
    for i in range(count):
        f = tmp_path / f"adr-{i:03d}.md"
        f.write_text(
            "# ADR\n\n## Status\nAccepted\n\n## Context\n"
            "Background info\n\n## Decision\nWe decided X\n\n"
            "## Consequences\nResult of decision\n"
        )
        files.append(f)
    return files


class TestCheckTemplateCompliancePrecision:
    """Regression tests for the integer division bug."""

    @pytest.mark.parametrize("file_count", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    def test_perfect_adrs_score_20(self, assessor, tmp_path, file_count):
        """With all required sections present in every file, the score
        must be 20/20 regardless of file count.

        Previously, integer division (20 // n) caused precision loss
        for non-divisor counts (e.g., 7 files -> max 14/20).
        """
        files = _make_adr_files(tmp_path, file_count)
        score = assessor._check_template_compliance(files)
        assert (
            score == 20
        ), f"Expected 20/20 for {file_count} perfect ADR files, got {score}/20"

    def test_empty_files_score_zero(self, assessor):
        """Empty file list should return 0."""
        assert assessor._check_template_compliance([]) == 0

    def test_partial_sections_score_proportionally(self, assessor, tmp_path):
        """Files with half the required sections should score ~half."""
        f = tmp_path / "adr-001.md"
        # Only "status" and "context" present (2 of 4 required sections)
        f.write_text("# ADR\n\n## Status\nAccepted\n\n## Context\nInfo\n")
        score = assessor._check_template_compliance([f])
        # 2/4 sections * 20 points = 10
        assert score == 10

    def test_seven_files_no_longer_capped_at_14(self, assessor, tmp_path):
        """Specific regression: 7 files was previously capped at 14/20."""
        files = _make_adr_files(tmp_path, 7)
        score = assessor._check_template_compliance(files)
        assert score == 20, f"7-file regression: expected 20, got {score}"


def _make_repo(tmp_path) -> Repository:
    (tmp_path / ".git").mkdir(exist_ok=True)
    return Repository(
        path=tmp_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 100},
        total_files=10,
        total_lines=100,
    )


def _make_adr_dir(parent, count=3):
    parent.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        f = parent / f"adr-{i:03d}.md"
        f.write_text(
            "# ADR\n\n## Status\nAccepted\n\n## Context\n"
            "Info\n\n## Decision\nWe decided X\n\n## Consequences\nResult\n"
        )


class TestExtendedDirectoryPaths:
    """Issue #414: additional directory paths for ADR detection."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "docs/adr",
            "docs/ADRs",
            "docs/Adr",
            "docs/architecture",
            "docs/Architecture",
            "docs/design",
            "docs/Design",
            "docs/specs",
            "docs/Specs",
            "adr",
            "specs",
        ],
    )
    def test_recognized_directory(self, assessor, tmp_path, rel_path):
        _make_adr_dir(tmp_path / rel_path)
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score > 0, f"{rel_path} should be recognized; got score 0"
        assert finding.status == "pass", f"{rel_path} with 3 ADRs should pass"

    def test_hidden_adr_still_recognized(self, assessor, tmp_path):
        _make_adr_dir(tmp_path / ".adr")
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score > 0

    def test_unrelated_docs_subdir_not_matched(self, assessor, tmp_path):
        (tmp_path / "docs" / "guides").mkdir(parents=True)
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score == 0 or finding.score == 60


class TestClaudeMdPartialCredit:
    """Issue #392: partial credit when CLAUDE.md/AGENTS.md references ADRs."""

    def test_claude_md_with_architecture_section(self, assessor, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "# Project\n\n## Architecture Decisions\n\nWe use hexagonal architecture.\n"
        )
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score == 60.0
        assert finding.status == "fail"
        assert any("partial credit" in e for e in finding.evidence)

    def test_agents_md_with_adr_section(self, assessor, tmp_path):
        (tmp_path / "AGENTS.md").write_text(
            "# Guide\n\n## ADR Summary\n\nKey decisions are logged here.\n"
        )
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score == 60.0

    def test_claude_md_with_external_link(self, assessor, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "# Project\n\nArchitectural decisions are tracked at "
            "https://github.com/org/architecture-decisions.\n"
        )
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score == 60.0

    def test_claude_md_without_adr_content_scores_zero(self, assessor, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "# Project\n\nRun tests with pytest.\n"
        )
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score == 0.0

    def test_inline_adr_dir_takes_priority_over_claude_md(self, assessor, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "## Architecture Decisions\n\nSee docs/adr.\n"
        )
        _make_adr_dir(tmp_path / "docs" / "adr")
        repo = _make_repo(tmp_path)
        finding = assessor.assess(repo)
        assert finding.score > 60.0  # full scoring path, not partial credit
