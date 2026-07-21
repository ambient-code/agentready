"""Tests for Git-aware assessment file discovery (#453)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentready.services.git_aware_file_index import (
    GitAwareFileIndex,
    GitAwareFileIndexError,
)
from agentready.services.language_detector import LanguageDetector


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def _write_tracked(repo: Path, relative: str, content: str = "x\n") -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    _git(repo, "add", relative)
    return path


class TestGitAwareFileIndex:
    def test_root_gitignore_excludes_generated(self, git_repo: Path):
        (git_repo / ".gitignore").write_text("generated/\n")
        _write_tracked(git_repo, "src/main.py", "print(1)\n")
        ignored = git_repo / "generated" / "out.py"
        ignored.parent.mkdir()
        ignored.write_text("print('ignored')\n")

        index = GitAwareFileIndex(git_repo)
        files = index.relative_files()
        assert "src/main.py" in files
        assert "generated/out.py" not in files
        assert index.is_ignored("generated/out.py")
        assert not index.exists("generated/out.py")

    def test_nested_gitignore(self, git_repo: Path):
        _write_tracked(git_repo, "pkg/__init__.py")
        nested_ignore = git_repo / "pkg" / ".gitignore"
        nested_ignore.write_text("local_cache/\n")
        _git(git_repo, "add", "pkg/.gitignore")
        cache = git_repo / "pkg" / "local_cache" / "x.py"
        cache.parent.mkdir()
        cache.write_text("x\n")

        index = GitAwareFileIndex(git_repo)
        assert "pkg/__init__.py" in index.relative_files()
        assert "pkg/local_cache/x.py" not in index.relative_files()

    def test_wildcard_min_js(self, git_repo: Path):
        (git_repo / ".gitignore").write_text("*.min.js\n")
        _write_tracked(git_repo, "app.js", "ok\n")
        minified = git_repo / "app.min.js"
        minified.write_text("min\n")

        index = GitAwareFileIndex(git_repo)
        assert "app.js" in index.relative_files()
        assert "app.min.js" not in index.relative_files()

    def test_anchored_build(self, git_repo: Path):
        (git_repo / ".gitignore").write_text("/build/\n")
        _write_tracked(git_repo, "src/ok.py")
        nested_build = git_repo / "pkg" / "build" / "x.py"
        nested_build.parent.mkdir(parents=True)
        nested_build.write_text("x\n")
        _git(git_repo, "add", "-f", "pkg/build/x.py")
        root_build = git_repo / "build" / "out.py"
        root_build.parent.mkdir()
        root_build.write_text("y\n")

        index = GitAwareFileIndex(git_repo)
        assert "pkg/build/x.py" in index.relative_files()
        assert "build/out.py" not in index.relative_files()

    def test_negation(self, git_repo: Path):
        (git_repo / ".gitignore").write_text("dist/*\n!dist/keep.js\n")
        keep = git_repo / "dist" / "keep.js"
        drop = git_repo / "dist" / "drop.js"
        keep.parent.mkdir()
        keep.write_text("keep\n")
        drop.write_text("drop\n")
        _git(git_repo, "add", "-f", "dist/keep.js")

        index = GitAwareFileIndex(git_repo)
        assert "dist/keep.js" in index.relative_files()
        assert "dist/drop.js" not in index.relative_files()

    def test_force_added_tracked_but_ignored(self, git_repo: Path):
        (git_repo / ".gitignore").write_text("secret.env\n")
        secret = git_repo / "secret.env"
        secret.write_text("TOKEN=1\n")
        _git(git_repo, "add", "-f", "secret.env")

        index = GitAwareFileIndex(git_repo)
        # Tracked but matching ignore must be excluded from assessment (#453)
        assert "secret.env" not in index.relative_files()
        assert index.is_ignored("secret.env")
        assert not index.exists("secret.env")

    def test_spaces_and_unicode_filenames(self, git_repo: Path):
        spaced = "docs/my file.md"
        unicode_name = "src/café.py"
        _write_tracked(git_repo, spaced, "# hi\n")
        _write_tracked(git_repo, unicode_name, "x=1\n")

        index = GitAwareFileIndex(git_repo)
        assert spaced in index.relative_files()
        assert unicode_name in index.relative_files()

    def test_no_gitignore_includes_tracked_files(self, git_repo: Path):
        _write_tracked(git_repo, "a.py", "a\n")
        _write_tracked(git_repo, "b.py", "b\n")

        index = GitAwareFileIndex(git_repo)
        assert index.relative_files() == frozenset({"a.py", "b.py"})

    def test_two_repos_do_not_leak_ignore_state(self, tmp_path: Path):
        repo_a = tmp_path / "a"
        repo_b = tmp_path / "b"
        for repo, rule in ((repo_a, "ignored_a/\n"), (repo_b, "ignored_b/\n")):
            repo.mkdir()
            _git(repo, "init")
            _git(repo, "config", "user.email", "t@example.com")
            _git(repo, "config", "user.name", "T")
            (repo / ".gitignore").write_text(rule)
            _write_tracked(repo, "ok.py", "x\n")
            ignored = repo / rule.strip().rstrip("/") / "x.py"
            ignored.parent.mkdir()
            ignored.write_text("no\n")

        index_a = GitAwareFileIndex(repo_a)
        index_b = GitAwareFileIndex(repo_b)
        assert "ok.py" in index_a.relative_files()
        assert "ignored_a/x.py" not in index_a.relative_files()
        assert "ignored_b/x.py" not in index_b.relative_files()
        assert "ok.py" in index_b.relative_files()
        # Ensure separate caches
        assert index_a.relative_files() is not index_b.relative_files()

    def test_ignored_generated_source_does_not_affect_language_totals(
        self, git_repo: Path
    ):
        (git_repo / ".gitignore").write_text("generated/\n")
        for i in range(3):
            _write_tracked(git_repo, f"src/m{i}.py", f"x={i}\n")
        gen = git_repo / "generated"
        gen.mkdir()
        for i in range(20):
            (gen / f"g{i}.py").write_text("print(1)\n")

        detector = LanguageDetector(git_repo)
        languages = detector.detect_languages()
        assert languages.get("Python") == 3
        assert all(
            not f.startswith("generated/") for f in detector.file_index.iter_files()
        )

    def test_git_command_failure_in_real_worktree(self, git_repo: Path, monkeypatch):
        """Unexpected Git failures in a real worktree fail closed (no rglob fallback)."""
        _write_tracked(git_repo, "ok.py", "x\n")

        def selective_boom(cmd, **kwargs):
            if list(cmd)[:2] == ["git", "rev-parse"]:
                result = type("R", (), {})()
                result.returncode = 0
                result.stdout = "true\n"
                result.stderr = ""
                return result
            raise RuntimeError("git exploded")

        monkeypatch.setattr(
            "agentready.services.git_aware_file_index.safe_subprocess_run",
            selective_boom,
        )
        index = GitAwareFileIndex(git_repo)
        with pytest.raises(GitAwareFileIndexError):
            index.relative_files()

    def test_dotfile_paths_are_not_stripped_by_normalize(self, git_repo: Path):
        """Paths like .github/... must remain intact (no str.lstrip bug)."""
        _write_tracked(git_repo, ".github/PULL_REQUEST_TEMPLATE.md", "pr\n")
        index = GitAwareFileIndex(git_repo)
        assert index.contains(".github/PULL_REQUEST_TEMPLATE.md")
        assert index.exists(".github/PULL_REQUEST_TEMPLATE.md")

    def test_stub_git_dir_lists_fixture_files(self, tmp_path: Path):
        """Unit fixtures that only mkdir .git still expose on-disk files."""
        repo = tmp_path / "fixture"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("print(1)\n")

        index = GitAwareFileIndex(repo)
        assert "src/main.py" in index.relative_files()


class TestAssessorIgnoresGeneratedTree:
    def test_type_annotations_ignore_generated_python(self, git_repo: Path):
        """Ignored generated/*.py must not change type-annotation scoring."""
        from agentready.assessors.code_quality import TypeAnnotationsAssessor
        from agentready.models.repository import Repository

        (git_repo / ".gitignore").write_text("generated/\n")
        src = git_repo / "src"
        src.mkdir()
        (src / "main.py").write_text(
            "def greet(name: str) -> str:\n" "    return name\n"
        )
        gen = git_repo / "generated"
        gen.mkdir()
        # Untyped functions that would tank the score if scanned
        (gen / "junk.py").write_text(
            "def a(x):\n"
            "    return x\n"
            "def b(x):\n"
            "    return x\n"
            "def c(x):\n"
            "    return x\n"
        )
        _git(git_repo, "add", ".gitignore", "src/main.py")

        repo = Repository(
            path=git_repo,
            name="typed",
            url=None,
            branch="main",
            commit_hash="abc",
            languages={"Python": 1},
            total_files=2,
            total_lines=10,
        )
        finding = TypeAnnotationsAssessor().assess(repo)
        assert "generated/" not in " ".join(finding.evidence or [])
        # Single fully-typed function → high score; ignored junk must not dilute it
        assert finding.score is not None and finding.score >= 90.0
