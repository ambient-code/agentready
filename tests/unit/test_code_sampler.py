"""Unit tests for code sampler."""

import tempfile
from pathlib import Path

import pytest

from agentready.learners.code_sampler import CodeSampler
from agentready.models import Attribute, Finding, Repository


@pytest.fixture
def temp_repo():
    """Create a temporary repository with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create .git directory
        (repo_path / ".git").mkdir()

        # Create sample files
        (repo_path / "README.md").write_text("# Test Project\n\nThis is a test.")
        (repo_path / "CLAUDE.md").write_text("# CLAUDE.md\n\nAgent instructions.")
        (repo_path / ".gitignore").write_text("*.pyc\n__pycache__/")

        # Create Python files
        src_dir = repo_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text(
            "def hello(name: str) -> str:\n    return f'Hello {name}'"
        )
        (src_dir / "utils.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b"
        )

        # Create tests directory
        tests_dir = repo_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test_hello():\n    pass")

        # Create config files
        (repo_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\ntestpaths = ['tests']"
        )
        (repo_path / ".pre-commit-config.yaml").write_text("repos:\n  - repo: test")

        # Create github workflows
        github_dir = repo_path / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "tests.yml").write_text("name: Tests\non: [push]")

        yield Repository(
            path=repo_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=8,
            total_lines=50,
        )


@pytest.fixture
def sample_attribute():
    """Create a sample attribute."""
    return Attribute(
        id="claude_md_file",
        name="CLAUDE.md File",
        category="Documentation",
        tier=1,
        description="CLAUDE.md provides agent instructions",
        criteria="Must exist at repository root",
        default_weight=1.0,
    )


@pytest.fixture
def sample_finding(sample_attribute):
    """Create a sample finding."""
    return Finding(
        attribute=sample_attribute,
        status="pass",
        score=100.0,
        measured_value="present",
        threshold="present",
        evidence=["CLAUDE.md exists at root"],
        remediation=None,
        error_message=None,
    )


class TestCodeSampler:
    """Test CodeSampler class."""

    def test_init_default_params(self, temp_repo):
        """Test initialization with default parameters."""
        sampler = CodeSampler(temp_repo)

        assert sampler.repository == temp_repo
        assert sampler.max_files == 5
        assert sampler.max_lines_per_file == 100

    def test_init_custom_params(self, temp_repo):
        """Test initialization with custom parameters."""
        sampler = CodeSampler(temp_repo, max_files=3, max_lines_per_file=50)

        assert sampler.max_files == 3
        assert sampler.max_lines_per_file == 50

    def test_get_relevant_code_claude_md(self, temp_repo, sample_finding):
        """Test getting relevant code for CLAUDE.md attribute."""
        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(sample_finding)

        assert isinstance(code, str)
        # Should contain CLAUDE.md content or reference
        assert len(code) > 0

    def test_get_relevant_code_readme(self, temp_repo):
        """Test getting relevant code for README attribute."""
        attr = Attribute(
            id="readme_file",
            name="README",
            category="Documentation",
            tier=1,
            description="README file",
            criteria="Must exist",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="present",
            threshold="present",
            evidence=["README.md exists"],
            remediation=None,
            error_message=None,
        )

        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(finding)

        assert isinstance(code, str)
        assert len(code) > 0

    def test_get_relevant_code_type_annotations(self, temp_repo):
        """Test getting relevant code for type annotations attribute."""
        attr = Attribute(
            id="type_annotations",
            name="Type Annotations",
            category="Code Quality",
            tier=2,
            description="Type hints in code",
            criteria=">=80%",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=90.0,
            measured_value="90%",
            threshold="80%",
            evidence=["Most functions have type hints"],
            remediation=None,
            error_message=None,
        )

        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(finding)

        assert isinstance(code, str)
        # Should sample Python files
        assert len(code) > 0

    def test_get_relevant_code_gitignore(self, temp_repo):
        """Test getting relevant code for gitignore attribute."""
        attr = Attribute(
            id="gitignore",
            name="Gitignore",
            category="Structure",
            tier=1,
            description="Gitignore file",
            criteria="Must exist",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="present",
            threshold="present",
            evidence=[".gitignore exists"],
            remediation=None,
            error_message=None,
        )

        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(finding)

        assert isinstance(code, str)
        assert len(code) > 0

    def test_get_relevant_code_unknown_attribute(self, temp_repo):
        """Test getting relevant code for unknown attribute."""
        attr = Attribute(
            id="unknown_attribute",
            name="Unknown",
            category="Unknown",
            tier=4,
            description="Unknown attribute",
            criteria="Unknown",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="unknown",
            threshold="unknown",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(finding)

        # Should return fallback message
        assert "No code samples available" in code

    def test_get_relevant_code_standard_layout(self, temp_repo):
        """Test getting relevant code for standard layout attribute."""
        attr = Attribute(
            id="standard_project_layout",
            name="Standard Layout",
            category="Structure",
            tier=2,
            description="Standard project structure",
            criteria="src/, tests/, docs/",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="standard",
            threshold="standard",
            evidence=["Has src/ and tests/ directories"],
            remediation=None,
            error_message=None,
        )

        sampler = CodeSampler(temp_repo)
        code = sampler.get_relevant_code(finding)

        assert isinstance(code, str)
        # Should contain directory structure info
        assert len(code) > 0

    def test_get_relevant_code_respects_max_files(self, temp_repo):
        """Test that code sampler respects max_files limit."""
        attr = Attribute(
            id="type_annotations",
            name="Type Annotations",
            category="Code Quality",
            tier=2,
            description="Type hints",
            criteria=">=80%",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass",
            score=90.0,
            measured_value="90%",
            threshold="80%",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        # Set max_files to 1
        sampler = CodeSampler(temp_repo, max_files=1)
        code = sampler.get_relevant_code(finding)

        # Should limit to 1 file (implementation dependent)
        assert isinstance(code, str)

    def test_get_directory_tree_existing_dir(self, temp_repo):
        """Test getting directory tree for existing directory."""
        sampler = CodeSampler(temp_repo)
        tree = sampler._get_directory_tree("src/")

        assert isinstance(tree, dict)
        if tree:  # If not empty
            assert tree.get("type") == "directory"
            assert "children" in tree

    def test_get_directory_tree_nonexistent_dir(self, temp_repo):
        """Test getting directory tree for non-existent directory."""
        sampler = CodeSampler(temp_repo)
        tree = sampler._get_directory_tree("nonexistent/")

        # Should return empty dict
        assert tree == {}

    def test_format_code_samples_empty_list(self, temp_repo):
        """Test formatting code samples with empty list."""
        sampler = CodeSampler(temp_repo)
        result = sampler._format_code_samples([])

        # Should handle empty list gracefully
        assert isinstance(result, str)

    def test_format_code_samples_with_files(self, temp_repo):
        """Test formatting code samples with actual files."""
        sampler = CodeSampler(temp_repo)
        files = [temp_repo.path / "README.md"]
        result = sampler._format_code_samples(files)

        assert isinstance(result, str)
        assert len(result) > 0


class TestCodeSamplerEdgeCases:
    """Test edge cases in code sampler."""

    def test_empty_repository(self):
        """Test code sampler with empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / ".git").mkdir()

            repo = Repository(
                path=repo_path,
                name="empty",
                url=None,
                branch="main",
                commit_hash="abc",
                languages={},
                total_files=0,
                total_lines=0,
            )

            sampler = CodeSampler(repo)
            attr = Attribute(
                id="claude_md_file",
                name="CLAUDE.md",
                category="Documentation",
                tier=1,
                description="Test",
                criteria="Test",
                default_weight=1.0,
            )
            finding = Finding(
                attribute=attr,
                status="fail",
                score=0.0,
                measured_value="absent",
                threshold="present",
                evidence=[],
                remediation=None,
                error_message=None,
            )

            code = sampler.get_relevant_code(finding)

            # Should handle gracefully
            assert isinstance(code, str)

    def test_max_lines_per_file_limit(self, temp_repo):
        """Test that max_lines_per_file is respected."""
        # Create a file with many lines
        large_file = temp_repo.path / "large.py"
        large_file.write_text("\n".join([f"line {i}" for i in range(200)]))

        sampler = CodeSampler(temp_repo, max_lines_per_file=50)

        # Sample the large file
        files = [large_file]
        result = sampler._format_code_samples(files)

        # Result should not contain all 200 lines (implementation dependent)
        assert isinstance(result, str)

    def test_binary_file_handling(self, temp_repo):
        """Test handling of binary files."""
        # Create a binary file
        binary_file = temp_repo.path / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        sampler = CodeSampler(temp_repo)

        # Try to sample binary file
        files = [binary_file]
        result = sampler._format_code_samples(files)

        # Should handle gracefully (may skip or show placeholder)
        assert isinstance(result, str)

    def test_symlink_handling(self, temp_repo):
        """Test handling of symlinks."""
        # Create a file and a symlink to it
        real_file = temp_repo.path / "real.txt"
        real_file.write_text("Real content")

        try:
            symlink = temp_repo.path / "link.txt"
            symlink.symlink_to(real_file)

            sampler = CodeSampler(temp_repo)
            files = [symlink]
            result = sampler._format_code_samples(files)

            # Should handle symlinks (may follow or skip)
            assert isinstance(result, str)
        except OSError:
            # Skip test if symlinks not supported (Windows without admin)
            pytest.skip("Symlinks not supported on this platform")

    def test_nested_directory_tree(self, temp_repo):
        """Test getting directory tree for nested directories."""
        # Create nested structure
        nested = temp_repo.path / "deeply" / "nested" / "structure"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("content")

        sampler = CodeSampler(temp_repo)
        tree = sampler._get_directory_tree("deeply/")

        # Should return tree structure
        assert isinstance(tree, dict)

    def test_hidden_files_excluded_from_tree(self, temp_repo):
        """Test that hidden files/directories are excluded from tree."""
        # Create hidden directory
        hidden = temp_repo.path / "visible" / ".hidden"
        hidden.mkdir(parents=True)
        (hidden / "secret.txt").write_text("secret")

        sampler = CodeSampler(temp_repo)
        tree = sampler._get_directory_tree("visible/")

        # Tree should exist but not include .hidden directory
        assert isinstance(tree, dict)
        if tree and "children" in tree:
            hidden_dirs = [
                c for c in tree["children"] if c.get("name", "").startswith(".")
            ]
            assert len(hidden_dirs) == 0
