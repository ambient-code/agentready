"""Tests for LocalAdrSource and CentralAdrSource."""

from pathlib import Path

from agentready.assessors.adr_sources import CentralAdrSource, LocalAdrSource
from agentready.models.repository import Repository


def _make_repo(tmp_path: Path, *, name: str = "test-repo") -> Repository:
    """Create a minimal Repository pointing at tmp_path."""
    (tmp_path / ".git").mkdir()
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


class TestLocalAdrSourceFindAdrDir:
    def test_returns_none_when_no_adr_dir(self, tmp_path):
        """Return None when no candidate ADR directory exists."""
        repo = _make_repo(tmp_path)
        source = LocalAdrSource()
        assert source.find_adr_dir(repo) is None

    def test_finds_uppercase_ADR_at_root_first(self, tmp_path):
        """Return ADR/ (uppercase) when it exists alongside docs/adr/, honoring priority."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        (adr_dir / "0001-init.md").write_text("# ADR 1")
        # Also create docs/adr/ to confirm priority ordering
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0002-other.md").write_text("# ADR 2")

        source = LocalAdrSource()
        found = source.find_adr_dir(repo)
        assert found == adr_dir

    def test_finds_docs_adr_when_no_uppercase_ADR(self, tmp_path):
        """Return docs/adr/ when ADR/ is absent."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-init.md").write_text("# ADR 1")

        source = LocalAdrSource()
        assert source.find_adr_dir(repo) == adr_dir

    def test_finds_root_adr_lowercase(self, tmp_path):
        """Return adr/ (lowercase) when it is the first matching candidate."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir()
        (adr_dir / "0001-init.md").write_text("# ADR 1")

        source = LocalAdrSource()
        assert source.find_adr_dir(repo) == adr_dir

    def test_finds_decisions_dir(self, tmp_path):
        """Return decisions/ when it contains .md files."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "decisions"
        adr_dir.mkdir()
        (adr_dir / "0001-init.md").write_text("# ADR 1")

        source = LocalAdrSource()
        assert source.find_adr_dir(repo) == adr_dir

    def test_finds_doc_adr_dir(self, tmp_path):
        """Return doc/adr/ (singular doc) when it contains .md files."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "doc" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-init.md").write_text("# ADR 1")

        source = LocalAdrSource()
        assert source.find_adr_dir(repo) == adr_dir

    def test_skips_dir_with_no_md_files(self, tmp_path):
        """Skip a candidate directory that contains no .md files."""
        repo = _make_repo(tmp_path)
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        (adr_dir / "not-an-adr.txt").write_text("ignored")
        # docs/adr/ has a .md file
        docs_adr = tmp_path / "docs" / "adr"
        docs_adr.mkdir(parents=True)
        (docs_adr / "0001-init.md").write_text("# ADR 1")

        source = LocalAdrSource()
        assert source.find_adr_dir(repo) == docs_adr


class TestLocalAdrSourceGetAdrFiles:
    def test_returns_md_files_only(self, tmp_path):
        """Return only .md files, ignoring other extensions."""
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        (adr_dir / "0001-init.md").write_text("# ADR 1")
        (adr_dir / "0002-db.md").write_text("# ADR 2")
        (adr_dir / "README.txt").write_text("ignored")

        source = LocalAdrSource()
        files = source.get_adr_files(adr_dir)
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_returns_empty_list_for_empty_dir(self, tmp_path):
        """Return an empty list when the directory has no .md files."""
        adr_dir = tmp_path / "ADR"
        adr_dir.mkdir()
        source = LocalAdrSource()
        assert source.get_adr_files(adr_dir) == []


VALID_ADR_APPLIES_TO_STAR = """\
---
status: Implemented
applies_to: "*"
---
# ADR 0001: Applies to all
"""

VALID_ADR_APPLIES_TO_SHORT = """\
---
status: active
applies_to: build-service
---
# ADR 0002: Applies to build-service
"""

VALID_ADR_APPLIES_TO_FULL = """\
---
status: Proposed
applies_to: konflux-ci/build-service
---
# ADR 0003: Applies to full org/repo
"""

VALID_ADR_APPLIES_TO_LIST = """\
---
status: Deprecated
applies_to:
  - build-service
  - release-service
---
# ADR 0004: Applies to a list
"""

VALID_ADR_APPLIES_TO_OTHER = """\
---
status: Implemented
applies_to: other-service
---
# ADR 0005: Applies to other-service only
"""

NO_FRONTMATTER_ADR = """\
# ADR 0006: No frontmatter
"""


class TestCentralAdrSource:
    def _make_central_repo(self, tmp_path: Path) -> Path:
        """Create a fake central ADR repo at tmp_path/central with ADR/ subdir."""
        central = tmp_path / "central"
        adr_dir = central / "ADR"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-star.md").write_text(VALID_ADR_APPLIES_TO_STAR)
        (adr_dir / "0002-short.md").write_text(VALID_ADR_APPLIES_TO_SHORT)
        (adr_dir / "0003-full.md").write_text(VALID_ADR_APPLIES_TO_FULL)
        (adr_dir / "0004-list.md").write_text(VALID_ADR_APPLIES_TO_LIST)
        (adr_dir / "0005-other.md").write_text(VALID_ADR_APPLIES_TO_OTHER)
        (adr_dir / "0006-nofm.md").write_text(NO_FRONTMATTER_ADR)
        return central

    def test_wildcard_matches_any_repo(self, tmp_path):
        """Include ADRs with applies_to '*' regardless of repo name."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("totally-different-repo")
        names = {f.name for f in files}
        assert "0001-star.md" in names

    def test_short_name_matches_short_applies_to(self, tmp_path):
        """Include ADRs whose applies_to exactly equals the short repo name."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("build-service")
        names = {f.name for f in files}
        assert "0002-short.md" in names
        assert "0005-other.md" not in names

    def test_full_org_repo_matches_full_applies_to(self, tmp_path):
        """Include ADRs whose applies_to is the full 'org/repo' name."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("konflux-ci/build-service")
        names = {f.name for f in files}
        assert "0003-full.md" in names
        assert (
            "0002-short.md" in names
        )  # "build-service" matches suffix of "konflux-ci/build-service"

    def test_short_name_also_matches_full_org_repo(self, tmp_path):
        """Match an 'org/repo' applies_to value using only the short repo name."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        # "build-service" short name should match "konflux-ci/build-service" applies_to
        files = source.get_matching_adr_files("build-service")
        names = {f.name for f in files}
        assert "0003-full.md" in names

    def test_list_applies_to_matches_any_item(self, tmp_path):
        """Include ADRs whose applies_to list contains the repo name."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("release-service")
        names = {f.name for f in files}
        assert "0004-list.md" in names

    def test_no_frontmatter_not_included(self, tmp_path):
        """Exclude ADR files that have no YAML frontmatter block."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("build-service")
        names = {f.name for f in files}
        assert "0006-nofm.md" not in names

    def test_non_matching_repo_excluded(self, tmp_path):
        """Only the wildcard ADR is returned for a repo with no specific applies_to."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files("unknown-service")
        names = {f.name for f in files}
        # Only the wildcard should match
        assert names == {"0001-star.md"}

    def test_missing_local_path_returns_empty(self, tmp_path):
        """Return an empty list when the central repo path does not exist."""
        source = CentralAdrSource(
            local_path=tmp_path / "does-not-exist",
            adr_path="ADR",
        )
        files = source.get_matching_adr_files("build-service")
        assert files == []

    def test_adr_path_with_trailing_slash(self, tmp_path):
        """Strip trailing slash from adr_path so directory lookup succeeds."""
        central = self._make_central_repo(tmp_path)
        source = CentralAdrSource(local_path=central, adr_path="ADR/")
        files = source.get_matching_adr_files("build-service")
        assert len(files) > 0

    def test_missing_adr_dir_returns_empty(self, tmp_path):
        """Return empty list when local_path exists but the ADR subdir is absent."""
        central = tmp_path / "central"
        central.mkdir()  # local_path exists, but "ADR/" subdir does not
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        assert source.get_matching_adr_files("build-service") == []

    def test_non_string_applies_to_not_matched(self, tmp_path):
        """Exclude ADRs whose applies_to is a non-string, non-list value."""
        central = tmp_path / "central"
        adr_dir = central / "ADR"
        adr_dir.mkdir(parents=True)
        (adr_dir / "numeric.md").write_text(
            "---\nstatus: Implemented\napplies_to: 42\n---\n# ADR\n"
        )
        source = CentralAdrSource(local_path=central, adr_path="ADR")
        files = source.get_matching_adr_files(
            "42"
        )  # even if repo_name == str(applies_to), no match
        assert files == []
