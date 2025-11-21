"""Tests for demo command."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentready.cli.demo import create_demo_repository, demo


def test_create_demo_repository_python():
    """Test creating a Python demo repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "test-demo"
        create_demo_repository(demo_path, "python")

        # Check basic structure
        assert demo_path.exists()
        assert (demo_path / ".git").exists()
        assert (demo_path / "README.md").exists()
        assert (demo_path / "CLAUDE.md").exists()
        assert (demo_path / "pyproject.toml").exists()
        assert (demo_path / ".gitignore").exists()

        # Check source files
        assert (demo_path / "src" / "demoapp" / "__init__.py").exists()
        assert (demo_path / "src" / "demoapp" / "main.py").exists()

        # Check tests
        assert (demo_path / "tests" / "test_main.py").exists()

        # Verify content
        readme_content = (demo_path / "README.md").read_text()
        assert "Demo Python Project" in readme_content

        claude_content = (demo_path / "CLAUDE.md").read_text()
        assert "AI Assistant Guide" in claude_content


def test_create_demo_repository_javascript():
    """Test creating a JavaScript demo repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "test-demo-js"
        create_demo_repository(demo_path, "javascript")

        # Check basic structure
        assert demo_path.exists()
        assert (demo_path / ".git").exists()
        assert (demo_path / "README.md").exists()
        assert (demo_path / "package.json").exists()
        assert (demo_path / ".gitignore").exists()

        # Check source files
        assert (demo_path / "src" / "index.js").exists()

        # Verify content
        package_content = (demo_path / "package.json").read_text()
        assert "demo-js-app" in package_content


def test_demo_command_help():
    """Test demo command help output."""
    runner = CliRunner()
    result = runner.invoke(demo, ["--help"])
    assert result.exit_code == 0
    assert "automated demonstration" in result.output.lower()
    assert "--language" in result.output
    assert "--no-browser" in result.output
    assert "--keep-repo" in result.output


def test_demo_command_python():
    """Test running demo command with Python language."""
    runner = CliRunner()

    # Run with --no-browser to avoid opening browser in tests
    # Use isolated filesystem for cleaner testing
    with runner.isolated_filesystem():
        result = runner.invoke(demo, ["--language", "python", "--no-browser"])

        # Check exit code
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Check output contains expected messages
        assert "AgentReady Demo" in result.output
        assert "Creating sample repository" in result.output
        assert "Running 25 attribute assessments" in result.output
        assert "Assessment Complete!" in result.output
        assert "Overall Score:" in result.output
        assert "Certification:" in result.output
        assert "Generating reports" in result.output
        assert "Demo complete!" in result.output

        # Check reports were generated
        demo_output = Path(".agentready-demo")
        assert demo_output.exists()

        # Find generated reports (with timestamp)
        html_files = list(demo_output.glob("demo-report-*.html"))
        md_files = list(demo_output.glob("demo-report-*.md"))
        json_files = list(demo_output.glob("demo-assessment-*.json"))

        assert len(html_files) == 1, "HTML report should be generated"
        assert len(md_files) == 1, "Markdown report should be generated"
        assert len(json_files) == 1, "JSON assessment should be generated"


def test_demo_command_javascript():
    """Test running demo command with JavaScript language."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(demo, ["--language", "javascript", "--no-browser"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "sample javascript project created" in result.output.lower()
        assert "Demo complete!" in result.output


def test_demo_command_keep_repo():
    """Test demo command with --keep-repo flag."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            demo, ["--language", "python", "--no-browser", "--keep-repo"]
        )

        assert result.exit_code == 0
        assert "Demo repository saved at:" in result.output
