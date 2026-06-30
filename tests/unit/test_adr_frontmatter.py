"""Tests for AdrFrontmatterAssessor."""

from pathlib import Path

import pytest

from agentready.assessors.adr_frontmatter import (
    VALID_STATUSES,
    AdrFrontmatterAssessor,
    classify_adr_file,
    parse_frontmatter,
    score_from_coverage,
)
from agentready.models.config import Config
from agentready.models.repository import Repository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(tmp_path: Path, *, name: str = "test-repo") -> Repository:
    """Create a minimal Repository pointing at tmp_path."""
    (tmp_path / ".git").mkdir(exist_ok=True)
    return Repository(
        path=tmp_path,
        name=name,
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Go": 100},
        total_files=5,
        total_lines=50,
    )


def _write_adr(directory: Path, filename: str, content: str) -> Path:
    """Write an ADR file into directory, creating it if needed."""
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / filename
    p.write_text(content)
    return p


VALID_FRONTMATTER = """\
---
status: Implemented
applies_to: build-service
---
# ADR 0001: Use PostgreSQL

We chose PostgreSQL as our primary database.
"""

INCOMPLETE_NO_APPLIES_TO = """\
---
status: Implemented
---
# ADR 0002: Missing applies_to
"""

INCOMPLETE_INVALID_STATUS = """\
---
status: WrongValue
applies_to: "*"
---
# ADR 0003: Bad status
"""

INCOMPLETE_EMPTY_STATUS = """\
---
status: ""
applies_to: build-service
---
# ADR 0004: Empty status
"""

NO_FRONTMATTER = """\
# ADR 0005: No Frontmatter

Just a plain markdown file, no YAML block.
"""


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_parses_valid_block(self):
        """Return a dict when a well-formed frontmatter block is present."""
        result = parse_frontmatter(VALID_FRONTMATTER)
        assert result == {"status": "Implemented", "applies_to": "build-service"}

    def test_returns_none_when_no_leading_dashes(self):
        """Return None for content that does not start with ---."""
        assert parse_frontmatter(NO_FRONTMATTER) is None

    def test_returns_none_when_closing_dashes_missing(self):
        """Return None when the closing --- delimiter is absent."""
        content = "---\nstatus: Implemented\n"
        assert parse_frontmatter(content) is None

    def test_returns_empty_dict_for_empty_frontmatter(self):
        """Return an empty dict for an --- --- block with no keys."""
        content = "---\n---\nBody text"
        assert parse_frontmatter(content) == {}

    def test_returns_none_for_invalid_yaml(self):
        """Return None when the frontmatter block contains invalid YAML."""
        content = "---\n: invalid: yaml: [\n---\n"
        assert parse_frontmatter(content) is None

    def test_applies_to_wildcard_is_parsed(self):
        """Parse a wildcard applies_to value correctly."""
        content = '---\nstatus: active\napplies_to: "*"\n---\n'
        result = parse_frontmatter(content)
        assert result["applies_to"] == "*"

    def test_returns_none_for_scalar_frontmatter(self):
        """Return None when the frontmatter block is a bare scalar, not a mapping."""
        assert parse_frontmatter("---\ntrue\n---\n# Body\n") is None

    def test_returns_none_for_list_frontmatter(self):
        """Return None when the frontmatter block is a YAML list, not a mapping."""
        assert parse_frontmatter("---\n- item1\n- item2\n---\n# Body\n") is None


# ---------------------------------------------------------------------------
# classify_adr_file
# ---------------------------------------------------------------------------


class TestClassifyAdrFile:
    def test_valid_with_both_fields(self, tmp_path):
        """Return 'valid' when status and applies_to are both present and correct."""
        p = tmp_path / "0001.md"
        p.write_text(VALID_FRONTMATTER)
        assert classify_adr_file(p) == "valid"

    def test_valid_with_wildcard_applies_to(self, tmp_path):
        """Return 'valid' when applies_to is the wildcard string."""
        p = tmp_path / "0001.md"
        p.write_text('---\nstatus: active\napplies_to: "*"\n---\n# ADR\n')
        assert classify_adr_file(p) == "valid"

    def test_valid_with_list_applies_to(self, tmp_path):
        """Return 'valid' when applies_to is a non-empty list."""
        p = tmp_path / "0001.md"
        p.write_text(
            "---\nstatus: Proposed\napplies_to:\n  - repo-a\n  - repo-b\n---\n# ADR\n"
        )
        assert classify_adr_file(p) == "valid"

    def test_incomplete_missing_applies_to(self, tmp_path):
        """Return 'incomplete' when applies_to is absent."""
        p = tmp_path / "0002.md"
        p.write_text(INCOMPLETE_NO_APPLIES_TO)
        assert classify_adr_file(p) == "incomplete"

    def test_valid_unfamiliar_status(self, tmp_path):
        """Return 'valid' for an unfamiliar but non-empty status string.

        VALID_STATUSES is no longer enforced in classification — any non-empty
        string is accepted so project-specific lifecycle values are not rejected.
        """
        p = tmp_path / "0003.md"
        p.write_text(INCOMPLETE_INVALID_STATUS)
        assert classify_adr_file(p) == "valid"

    def test_incomplete_empty_status(self, tmp_path):
        """Return 'incomplete' when status is an empty string."""
        p = tmp_path / "0004.md"
        p.write_text(INCOMPLETE_EMPTY_STATUS)
        assert classify_adr_file(p) == "incomplete"

    def test_no_frontmatter(self, tmp_path):
        """Return 'no_frontmatter' for a plain markdown file."""
        p = tmp_path / "0005.md"
        p.write_text(NO_FRONTMATTER)
        assert classify_adr_file(p) == "no_frontmatter"

    def test_all_valid_statuses_accepted(self, tmp_path):
        """Return 'valid' for every status in VALID_STATUSES."""
        for status in VALID_STATUSES:
            p = tmp_path / f"adr-{status}.md"
            p.write_text(f"---\nstatus: {status}\napplies_to: myrepo\n---\n")
            assert (
                classify_adr_file(p) == "valid"
            ), f"Expected 'valid' for status={status}"

    def test_returns_no_frontmatter_for_missing_file(self, tmp_path):
        """Return 'no_frontmatter' gracefully when the file does not exist."""
        assert classify_adr_file(tmp_path / "nonexistent.md") == "no_frontmatter"

    def test_incomplete_when_applies_to_is_numeric(self, tmp_path):
        """Return 'incomplete' when applies_to is a number (not str or list)."""
        p = tmp_path / "numeric.md"
        p.write_text("---\nstatus: Implemented\napplies_to: 123\n---\n# ADR\n")
        assert classify_adr_file(p) == "incomplete"


# ---------------------------------------------------------------------------
# score_from_coverage
# ---------------------------------------------------------------------------


class TestScoreFromCoverage:
    def test_100_percent_is_pass(self):
        """100% valid ADRs yields pass with score 100."""
        status, score = score_from_coverage(10, 10)
        assert status == "pass"
        assert score == 100.0

    def test_80_percent_is_pass(self):
        """80% valid ADRs (the threshold) yields pass with score 100."""
        status, score = score_from_coverage(8, 10)
        assert status == "pass"
        assert score == 100.0

    def test_79_percent_is_partial(self):
        """79% valid ADRs (just below threshold) yields partial with score 60."""
        status, score = score_from_coverage(79, 100)
        assert status == "partial"
        assert score == 60.0

    def test_50_percent_is_partial(self):
        """50% valid ADRs (lower partial boundary) yields partial with score 60."""
        status, score = score_from_coverage(5, 10)
        assert status == "partial"
        assert score == 60.0

    def test_49_percent_is_fail(self):
        """49% valid ADRs (just below partial band) yields fail with score 0."""
        status, score = score_from_coverage(49, 100)
        assert status == "fail"
        assert score == 0.0

    def test_zero_of_zero_is_pass(self):
        """Zero files yields pass — caller is expected to handle the skip case."""
        # Edge case: no files → treat as 100% (skip handled upstream)
        status, score = score_from_coverage(0, 0)
        assert status == "pass"
        assert score == 100.0


# ---------------------------------------------------------------------------
# AdrFrontmatterAssessor — integration tests using LocalAdrSource
# ---------------------------------------------------------------------------


class TestAdrFrontmatterAssessorLocal:
    def test_skips_when_no_adrs(self, tmp_path):
        """Return skipped finding when no ADR directory exists in the repo."""
        repo = _make_repo(tmp_path)
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "skipped"
        assert "No ADR files found" in finding.evidence[0]

    def test_passes_when_all_adrs_valid(self, tmp_path):
        """Return pass with score 100 when all ADR files have valid frontmatter."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        for i in range(5):
            (adr_dir / f"000{i}-adr.md").write_text(
                f"---\nstatus: Implemented\napplies_to: myrepo\n---\n# ADR {i}\n"
            )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "ADR location:" in finding.evidence[0]
        assert "5 valid" in finding.evidence[1]

    def test_partial_between_50_and_79_percent(self, tmp_path):
        """Return fail with score 60 when coverage is in the 50–79% partial band."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        # 6 valid, 4 no-frontmatter = 60%
        for i in range(6):
            (adr_dir / f"valid-{i}.md").write_text(
                '---\nstatus: active\napplies_to: "*"\n---\n# ADR\n'
            )
        for i in range(4):
            (adr_dir / f"plain-{i}.md").write_text("# Just a heading\n")
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "fail"
        assert finding.score == 60.0
        assert finding.remediation is not None

    def test_fails_below_50_percent(self, tmp_path):
        """Return fail with score 0 when coverage is below 50%."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        # 3 valid, 7 no-frontmatter = 30%
        for i in range(3):
            (adr_dir / f"valid-{i}.md").write_text(
                "---\nstatus: Deprecated\napplies_to: svc-a\n---\n# ADR\n"
            )
        for i in range(7):
            (adr_dir / f"plain-{i}.md").write_text("# Plain ADR\n")
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None

    def test_attribute_id_and_tier(self, tmp_path):
        """Attribute metadata matches expected values for Tier 3 registration."""
        assessor = AdrFrontmatterAssessor()
        assert assessor.attribute_id == "adr_frontmatter_completeness"
        assert assessor.tier == 3
        assert assessor.attribute.default_weight == 0.02
        assert assessor.attribute.category == "Documentation Standards"

    def test_evidence_contains_adr_location(self, tmp_path):
        """Evidence includes the ADR directory path."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        (adr_dir / "0001.md").write_text(
            "---\nstatus: Proposed\napplies_to: svc-b\n---\n# ADR 1\n"
        )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert any("ADR location:" in e for e in finding.evidence)

    def test_measured_value_format(self, tmp_path):
        """Measured value string uses 'valid/total (pct%)' format."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        for i in range(4):
            (adr_dir / f"v-{i}.md").write_text(
                "---\nstatus: active\napplies_to: myrepo\n---\n# ADR\n"
            )
        (adr_dir / "bad.md").write_text("# No frontmatter\n")
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        # 4/5 = 80% → pass
        assert finding.measured_value is not None
        assert "4/5" in finding.measured_value
        assert "80%" in finding.measured_value


# ---------------------------------------------------------------------------
# AdrFrontmatterAssessor — CentralAdrSource integration via config
# ---------------------------------------------------------------------------


class TestAdrFrontmatterAssessorCentral:
    def _make_central_repo(self, tmp_path: Path) -> Path:
        """Create a fake central ADR repo with a few ADR files."""
        central = tmp_path / "central"
        adr_dir = central / "ADR"
        adr_dir.mkdir(parents=True)
        for i in range(3):
            (adr_dir / f"000{i}-global.md").write_text(
                f'---\nstatus: Implemented\napplies_to: "*"\n---\n# ADR {i}\n'
            )
        (adr_dir / "0003-specific.md").write_text(
            "---\nstatus: active\napplies_to: my-service\n---\n# ADR specific\n"
        )
        (adr_dir / "0004-other.md").write_text(
            "---\nstatus: active\napplies_to: other-service\n---\n# ADR other\n"
        )
        return central

    def _make_repo_with_central_config(
        self, tmp_path: Path, central_path: Path, repo_name: str = "my-service"
    ) -> Repository:
        """Create a Repository configured to use a central ADR source."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        config = Config(
            adr_source={
                "repo": str(central_path),
                "path": "ADR",
            }
        )
        return Repository(
            path=repo_dir,
            name=repo_name,
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=5,
            total_lines=50,
            config=config,
        )

    def test_passes_using_central_source(self, tmp_path):
        """Return pass when all ADRs matched from the central repo are valid."""
        central = self._make_central_repo(tmp_path)
        repo = self._make_repo_with_central_config(tmp_path, central)
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        # 4 files match (3 wildcard + 1 specific), all valid
        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_skips_when_central_local_path_missing(self, tmp_path):
        """Return skipped when the configured central repo path does not exist."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        config = Config(
            adr_source={
                "repo": str(tmp_path / "does-not-exist"),
                "path": "ADR",
            }
        )
        repo = Repository(
            path=repo_dir,
            name="my-service",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=5,
            total_lines=50,
            config=config,
        )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "skipped"
        assert (
            "central" in finding.evidence[0].lower()
            or "not found" in finding.evidence[0].lower()
        )

    def test_wildcard_adrs_match_any_repo(self, tmp_path):
        """Return pass when only wildcard ADRs exist and all are valid."""
        central = self._make_central_repo(tmp_path)
        # repo name with no specific applies_to but wildcard ADRs exist
        repo = self._make_repo_with_central_config(
            tmp_path, central, repo_name="unknown-repo"
        )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        # 3 wildcard ADRs match unknown-repo
        # They're all valid → pass
        assert finding.status == "pass"

    def test_skips_when_no_adrs_match_repo(self, tmp_path):
        """Fall through to local scan when no central ADRs match the repo.

        When adr_source is configured but no ADRs have applies_to for this repo,
        _assess_central returns None and _assess_local is called instead.
        With no local ADR dir either the result is a local skipped finding.
        """
        central = tmp_path / "central"
        adr_dir = central / "ADR"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-specific.md").write_text(
            "---\nstatus: active\napplies_to: other-service\n---\n# ADR\n"
        )
        repo = self._make_repo_with_central_config(
            tmp_path, central, repo_name="my-service"
        )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        # No central match → fall through to local → no local ADRs → skipped
        assert finding.status == "skipped"
        assert "No ADR files found" in finding.evidence[0]

    def test_config_rejects_missing_repo(self):
        """Config raises ValidationError when adr_source.repo is absent."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="repo"):
            Config(adr_source={"path": "ADR"})  # repo intentionally omitted

    def test_evidence_includes_central_source_info(self, tmp_path):
        """Evidence includes central repo path and applies_to filter summary."""
        central = self._make_central_repo(tmp_path)
        repo = self._make_repo_with_central_config(tmp_path, central)
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert any("central repo" in e for e in finding.evidence)
        assert any("Filtered by applies_to" in e for e in finding.evidence)

    def test_config_without_adr_source_uses_local(self, tmp_path):
        """Fall back to LocalAdrSource when Config has no adr_source key."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        adr_dir = repo_dir / "ADR"
        adr_dir.mkdir()
        (adr_dir / "0001.md").write_text(
            "---\nstatus: Implemented\napplies_to: my-service\n---\n# ADR\n"
        )
        config = Config()  # no adr_source
        repo = Repository(
            path=repo_dir,
            name="my-service",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=5,
            total_lines=50,
            config=config,
        )
        assessor = AdrFrontmatterAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "pass"
