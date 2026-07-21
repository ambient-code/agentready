"""Git-aware repository file index for assessment discovery.

Enumerates files that should influence AgentReady scores using Git's own
ignore rules (root and nested ``.gitignore``, wildcards, anchors, negation).
Tracked files that match an ignore rule are excluded via
``git check-ignore --no-index`` per issue #453.

Instances are scoped to one repository path and cache an immutable file set
for reuse within a single assessment. They never use process-global state.

When ``.git`` is missing or is not a usable worktree (common in unit-test
fixtures that only ``mkdir .git``, or callers that bypass Repository
validation), the index falls back to a plain filesystem walk. Ignore
filtering requires a real Git worktree; production assessments always use
the Git path. Unexpected Git command failures in a real worktree fail
closed — they never silently reintroduce ignored trees via ``rglob``.
"""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Literal

from ..utils.subprocess_utils import safe_subprocess_run

logger = logging.getLogger(__name__)

IndexMode = Literal["git", "filesystem"]


class GitAwareFileIndexError(RuntimeError):
    """Raised when Git cannot provide a reliable assessment file list."""


class GitAwareFileIndex:
    """Immutable, Git-ignore-aware file set for one repository."""

    def __init__(self, repository_path: Path | str):
        """Create an index bound to ``repository_path``.

        Loading is lazy on first use so construction stays cheap.
        """
        self.repository_path = Path(repository_path).resolve()
        self._relative_files: frozenset[str] | None = None
        self._ignored_cache: dict[str, bool] = {}
        self._mode: IndexMode | None = None

    def _ensure_loaded(self) -> frozenset[str]:
        if self._relative_files is not None:
            return self._relative_files

        if self._is_usable_git_worktree():
            self._mode = "git"
            try:
                listed = self._ls_files()
                ignored = self._check_ignore(listed)
                files = frozenset(p for p in listed if p not in ignored)
            except GitAwareFileIndexError:
                raise
            except Exception as exc:  # noqa: BLE001 — surface as typed failure
                raise GitAwareFileIndexError(
                    f"Failed to build Git-aware file index for "
                    f"{self.repository_path}: {exc}"
                ) from exc
        else:
            # No usable worktree: stub ``.git`` fixtures, or callers that bypass
            # Repository validation. Walk the filesystem so discovery helpers
            # still see on-disk files. Ignore rules require a real Git worktree.
            self._mode = "filesystem"
            logger.debug(
                "No usable Git worktree at %s; listing files without ignore "
                "filtering",
                self.repository_path,
            )
            files = frozenset(self._walk_files())

        self._relative_files = files
        return files

    def _is_usable_git_worktree(self) -> bool:
        result = safe_subprocess_run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and (result.stdout or "").strip() == "true"

    def _ls_files(self) -> list[str]:
        """List tracked and eligible untracked files (NUL-delimited)."""
        result = safe_subprocess_run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=self.repository_path,
            capture_output=True,
            text=False,
            timeout=60,
            check=True,
        )
        return self._split_nul(result.stdout)

    def _check_ignore(self, paths: list[str]) -> set[str]:
        """Return paths that match ignore rules, including force-added tracked files."""
        if not paths:
            return set()

        ignored: set[str] = set()
        batch_size = 500
        for i in range(0, len(paths), batch_size):
            batch = paths[i : i + batch_size]
            payload = b"\0".join(
                p.encode("utf-8", errors="surrogateescape") for p in batch
            )
            payload += b"\0"
            result = safe_subprocess_run(
                ["git", "check-ignore", "--no-index", "-z", "--stdin"],
                cwd=self.repository_path,
                input=payload,
                capture_output=True,
                text=False,
                timeout=60,
                check=False,
            )
            # Exit 0: some matches; 1: none; other: error
            if result.returncode not in (0, 1):
                stderr = (result.stderr or b"").decode("utf-8", errors="replace")
                raise GitAwareFileIndexError(
                    f"git check-ignore failed (exit {result.returncode}): {stderr}"
                )
            ignored.update(self._split_nul(result.stdout))
        return ignored

    def _walk_files(self) -> list[str]:
        """Enumerate files on disk, excluding the ``.git`` directory tree."""
        out: list[str] = []
        for path in self.repository_path.rglob("*"):
            if not path.is_file() and not path.is_symlink():
                continue
            try:
                rel = path.relative_to(self.repository_path).as_posix()
            except ValueError:
                continue
            if rel == ".git" or rel.startswith(".git/"):
                continue
            out.append(rel)
        return out

    @staticmethod
    def _split_nul(data: bytes | str | None) -> list[str]:
        if not data:
            return []
        if isinstance(data, str):
            raw = data.encode("utf-8", errors="surrogateescape")
        else:
            raw = data
        parts = raw.split(b"\0")
        out: list[str] = []
        for part in parts:
            if not part:
                continue
            out.append(part.decode("utf-8", errors="surrogateescape"))
        return out

    @staticmethod
    def _normalize(relative: str | PurePosixPath | Path) -> str:
        text = str(relative).replace("\\", "/")
        while text.startswith("./"):
            text = text[2:]
        return text

    def relative_files(self) -> frozenset[str]:
        """Return all assessment-eligible repository-relative paths."""
        return self._ensure_loaded()

    def iter_files(self) -> Iterator[str]:
        """Iterate assessment-eligible relative paths in sorted order."""
        yield from sorted(self._ensure_loaded())

    def match(self, pattern: str) -> list[str]:
        """Return relative paths matching a pathlib-style pattern (e.g. ``*.py``)."""
        matched = [
            rel for rel in self._ensure_loaded() if PurePosixPath(rel).match(pattern)
        ]
        return sorted(matched)

    def match_any(self, patterns: Iterable[str]) -> list[str]:
        """Return relative paths matching any of the given patterns."""
        pats = list(patterns)
        matched = [
            rel
            for rel in self._ensure_loaded()
            if any(PurePosixPath(rel).match(p) for p in pats)
        ]
        return sorted(set(matched))

    def contains(self, relative: str | PurePosixPath | Path) -> bool:
        """True when the relative path is in the assessment file set."""
        return self._normalize(relative) in self._ensure_loaded()

    def is_ignored(self, relative: str | PurePosixPath | Path) -> bool:
        """True when Git ignore rules exclude this relative path."""
        rel = self._normalize(relative)
        if not rel:
            return False
        if rel in self._ignored_cache:
            return self._ignored_cache[rel]

        files = self._ensure_loaded()
        if self._mode != "git":
            # Filesystem mode cannot evaluate ignore rules without Git.
            self._ignored_cache[rel] = False
            return False

        if rel in files:
            self._ignored_cache[rel] = False
            return False

        ignored = self._path_check_ignore(rel)
        self._ignored_cache[rel] = ignored
        return ignored

    def _path_check_ignore(self, relative: str) -> bool:
        payload = relative.encode("utf-8", errors="surrogateescape") + b"\0"
        result = safe_subprocess_run(
            ["git", "check-ignore", "--no-index", "-z", "--stdin"],
            cwd=self.repository_path,
            input=payload,
            capture_output=True,
            text=False,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        stderr = (result.stderr or b"").decode("utf-8", errors="replace")
        raise GitAwareFileIndexError(
            f"git check-ignore failed for {relative!r}: {stderr}"
        )

    def exists(self, relative: str | PurePosixPath | Path) -> bool:
        """True when the path exists on disk and is not ignore-excluded."""
        rel = self._normalize(relative)
        full = self.repository_path / rel
        if not full.exists() and not full.is_symlink():
            return False
        if self.is_ignored(rel):
            return False
        return True

    def absolute_paths(self, pattern: str | None = None) -> list[Path]:
        """Return absolute Paths for matching (or all) assessment files."""
        rels = self.match(pattern) if pattern else sorted(self._ensure_loaded())
        return [self.repository_path / rel for rel in rels]
