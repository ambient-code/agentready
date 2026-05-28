"""Unit tests for BaseAssessor helper methods."""

from unittest.mock import patch

from agentready.assessors.base import BaseAssessor
from agentready.models.finding import Finding
from agentready.models.repository import Repository


class ConcreteAssessor(BaseAssessor):
    """Concrete implementation for testing BaseAssessor methods."""

    @property
    def attribute_id(self) -> str:
        return "test_attribute"

    @property
    def tier(self) -> int:
        return 1

    def assess(self, repository: Repository) -> Finding:
        return Finding.create_pass(self.attribute_id, evidence="test", details="test")


class TestPrimaryLanguage:
    """Tests for _primary_language() method."""

    def test_go_manifest_detection(self, tmp_path):
        """Single language detected by manifest returns immediately."""
        (tmp_path / "go.mod").write_text("module test\n")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Go": 10, "Python": 100},  # Python has more files
                total_files=110,
                total_lines=1000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Go", "Python"})

            # Go should win despite having fewer files, because go.mod exists
            assert result == "Go"

    def test_python_manifest_detection(self, tmp_path):
        """Python project detected by pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Python": 50, "JavaScript": 100},  # JS has more files
                total_files=150,
                total_lines=1000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Python", "JavaScript"})

            # Python should win because pyproject.toml exists
            assert result == "Python"

    def test_typescript_manifest_detection(self, tmp_path):
        """TypeScript detected when tsconfig.json exists."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "tsconfig.json").write_text("{}")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"JavaScript": 200, "TypeScript": 50},
                total_files=250,
                total_lines=5000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"JavaScript", "TypeScript"})

            # TypeScript should win because tsconfig.json exists
            assert result == "TypeScript"

    def test_java_maven_detection(self, tmp_path):
        """Java project detected by pom.xml."""
        (tmp_path / "pom.xml").write_text("<project></project>")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Java": 100},
                total_files=100,
                total_lines=2000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Java", "Python"})

            assert result == "Java"

    def test_java_gradle_detection(self, tmp_path):
        """Java project detected by build.gradle."""
        (tmp_path / "build.gradle").write_text("plugins {}")
        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Java": 100},
                total_files=100,
                total_lines=2000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Java", "Python"})

            assert result == "Java"

    def test_rust_cargo_detection(self, tmp_path):
        """Rust project detected by Cargo.toml."""
        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'\n")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Rust": 100},
                total_files=100,
                total_lines=2000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Rust"})

            assert result == "Rust"

    def test_multiple_manifests_use_file_count(self, tmp_path):
        """When multiple languages have manifests, use file count."""
        (tmp_path / "go.mod").write_text("module test\n")
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Go": 50, "Python": 150},
                total_files=200,
                total_lines=4000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Go", "Python"})

            # Python has more files, so it should win
            assert result == "Python"

    def test_no_manifests_use_file_count(self, tmp_path):
        """Falls back to file count when no manifests."""
        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Python": 100, "JavaScript": 50},
                total_files=150,
                total_lines=3000,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Python", "JavaScript"})

            # Python has more files
            assert result == "Python"

    def test_language_not_in_candidates(self, tmp_path):
        """Manifest for language not in candidates is ignored."""
        (tmp_path / "go.mod").write_text("module test\n")

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={"Python": 100},
                total_files=100,
                total_lines=2000,
            )

            assessor = ConcreteAssessor()
            # Only ask about Python, not Go
            result = assessor._primary_language(repo, {"Python"})

            assert result == "Python"

    def test_no_languages_returns_none(self, tmp_path):
        """Returns None when no languages present."""

        with patch.object(Repository, "__post_init__", lambda self: None):
            repo = Repository(
                path=tmp_path,
                name="test",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            )

            assessor = ConcreteAssessor()
            result = assessor._primary_language(repo, {"Go", "Python"})

            assert result is None
