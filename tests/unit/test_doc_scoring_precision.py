"""Regression test for integer division bug in documentation scoring.

Tests that _check_template_compliance() uses float division so that
repositories with any number of ADR files can achieve the maximum
score of 20/20 when all required sections are present.
"""

import pytest

from agentready.assessors.documentation import ArchitectureDecisionsAssessor


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
