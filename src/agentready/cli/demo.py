"""Demo command for showcasing AgentReady capabilities."""

import sys
import tempfile
import time
import webbrowser
from pathlib import Path

import click

from ..services.scanner import Scanner


def create_demo_repository(demo_path: Path, language: str = "python") -> None:
    """Create a sample repository for demonstration.

    Args:
        demo_path: Path where demo repo should be created
        language: Language for demo repo (python, javascript, go)
    """
    demo_path.mkdir(parents=True, exist_ok=True)

    if language == "python":
        # Create basic Python project structure
        src_dir = demo_path / "src" / "demoapp"
        src_dir.mkdir(parents=True, exist_ok=True)

        tests_dir = demo_path / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Create README.md
        readme_content = """# Demo Python Project

A sample Python application demonstrating AgentReady assessment.

## Overview

This is a minimal Python project created to showcase the AgentReady tool's
capabilities in assessing repository quality for AI-assisted development.

## Features

- Basic Python package structure
- Simple module with type annotations
- Test coverage
- Git repository

## Installation

```bash
pip install -e .
```

## Usage

```python
from demoapp import greet

greet("World")
```

## Testing

```bash
pytest
```
"""
        (demo_path / "README.md").write_text(readme_content)

        # Create CLAUDE.md (for high score on that attribute)
        claude_md_content = """# Demo Python Project - AI Assistant Guide

## Overview

This is a demonstration project for the AgentReady assessment tool.

## Project Structure

```
demo-repo/
├── src/demoapp/     # Main application code
├── tests/           # Test suite
├── README.md        # User documentation
└── pyproject.toml   # Python package configuration
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### Running Tests

```bash
pytest
```

## Architecture

The project uses a simple module structure with type-annotated functions
for better IDE support and AI code generation.
"""
        (demo_path / "CLAUDE.md").write_text(claude_md_content)

        # Create main module with type annotations
        main_py_content = '''"""Main module for demo application."""


def greet(name: str) -> str:
    """Generate a greeting message.

    Args:
        name: Name of the person to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def main() -> None:
    """Main entry point."""
    print(greet("World"))
    print(f"2 + 2 = {add_numbers(2, 2)}")


if __name__ == "__main__":
    main()
'''
        (src_dir / "__init__.py").write_text(
            '"""Demo application package."""\n\nfrom .main import greet, add_numbers\n\n__all__ = ["greet", "add_numbers"]\n'
        )
        (src_dir / "main.py").write_text(main_py_content)

        # Create test file
        test_content = '''"""Tests for demo application."""

import pytest

from demoapp import greet, add_numbers


def test_greet():
    """Test greet function."""
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob") == "Hello, Bob!"


def test_add_numbers():
    """Test add_numbers function."""
    assert add_numbers(2, 2) == 4
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
'''
        (tests_dir / "test_main.py").write_text(test_content)
        (tests_dir / "__init__.py").write_text("")

        # Create pyproject.toml
        pyproject_content = """[project]
name = "demoapp"
version = "0.1.0"
description = "Demo application for AgentReady"
requires-python = ">=3.11"

[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}
packages = ["demoapp"]
"""
        (demo_path / "pyproject.toml").write_text(pyproject_content)

        # Create .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
"""
        (demo_path / ".gitignore").write_text(gitignore_content)

    elif language == "javascript":
        # Create basic JavaScript/Node.js project
        src_dir = demo_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # README
        readme = """# Demo JavaScript Project

A sample Node.js application for AgentReady demonstration.

## Installation

```bash
npm install
```

## Usage

```javascript
const { greet } = require('./src/index');
console.log(greet('World'));
```
"""
        (demo_path / "README.md").write_text(readme)

        # package.json
        package_json = """{
  "name": "demo-js-app",
  "version": "0.1.0",
  "description": "Demo JavaScript app for AgentReady",
  "main": "src/index.js",
  "scripts": {
    "test": "echo \\"No tests yet\\""
  },
  "keywords": ["demo"],
  "author": "",
  "license": "MIT"
}
"""
        (demo_path / "package.json").write_text(package_json)

        # Main JS file
        index_js = """/**
 * Demo JavaScript application
 */

function greet(name) {
  return `Hello, ${name}!`;
}

function addNumbers(a, b) {
  return a + b;
}

module.exports = { greet, addNumbers };
"""
        (src_dir / "index.js").write_text(index_js)

        # .gitignore
        gitignore = """node_modules/
.DS_Store
*.log
"""
        (demo_path / ".gitignore").write_text(gitignore)

    # Initialize git repository
    import git

    repo = git.Repo.init(demo_path)
    repo.index.add(["*"])
    repo.index.commit("Initial commit - Demo repository for AgentReady")


@click.command()
@click.option(
    "--language",
    type=click.Choice(["python", "javascript"], case_sensitive=False),
    default="python",
    help="Language for demo repository (default: python)",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't open HTML report in browser automatically",
)
@click.option(
    "--keep-repo",
    is_flag=True,
    help="Keep demo repository after assessment (for debugging)",
)
def demo(language, no_browser, keep_repo):
    """Run an automated demonstration of AgentReady.

    Creates a sample repository, runs a full assessment, generates reports,
    and displays the results. Perfect for presentations, demos, and onboarding.

    Examples:

        \b
        # Run Python demo (default)
        agentready demo

        \b
        # Run JavaScript demo
        agentready demo --language javascript

        \b
        # Run without opening browser
        agentready demo --no-browser
    """
    click.echo("🤖 AgentReady Demo")
    click.echo("=" * 60)
    click.echo()

    # Create temporary directory for demo repo
    temp_dir = tempfile.mkdtemp(prefix="agentready-demo-")
    demo_repo_path = Path(temp_dir) / "demo-repo"

    try:
        # Step 1: Create sample repository
        click.echo("📦 Creating sample repository...")
        time.sleep(0.3)  # Dramatic pause
        create_demo_repository(demo_repo_path, language)
        click.echo(f"   ✓ Sample {language} project created")
        click.echo()

        # Step 2: Initialize scanner
        click.echo("🔍 Analyzing repository structure...")
        time.sleep(0.3)
        scanner = Scanner(demo_repo_path, config=None)
        click.echo("   ✓ Repository validated")
        click.echo()

        # Step 3: Run assessment
        click.echo("⚙️  Running 25 attribute assessments...")
        click.echo()

        # Import assessors here to avoid circular import
        from ..assessors.code_quality import (
            CyclomaticComplexityAssessor,
            TypeAnnotationsAssessor,
        )
        from ..assessors.documentation import CLAUDEmdAssessor, READMEAssessor
        from ..assessors.structure import StandardLayoutAssessor
        from ..assessors.stub_assessors import (
            ConventionalCommitsAssessor,
            GitignoreAssessor,
            LockFilesAssessor,
            create_stub_assessors,
        )
        from ..assessors.testing import PreCommitHooksAssessor, TestCoverageAssessor

        # Create all 25 assessors
        assessors = [
            # Tier 1 Essential (5 assessors)
            CLAUDEmdAssessor(),
            READMEAssessor(),
            TypeAnnotationsAssessor(),
            StandardLayoutAssessor(),
            LockFilesAssessor(),
            # Tier 2 Critical (10 assessors - 3 implemented, 7 stubs)
            TestCoverageAssessor(),
            PreCommitHooksAssessor(),
            ConventionalCommitsAssessor(),
            GitignoreAssessor(),
            CyclomaticComplexityAssessor(),  # Actually Tier 3, but including here
        ]
        # Add remaining stub assessors
        assessors.extend(create_stub_assessors())

        # Show progress with actual assessor execution
        start_time = time.time()

        # Build repository model
        repository = scanner._build_repository_model(verbose=False)

        # Execute assessors with live progress
        findings = []
        for i, assessor in enumerate(assessors, 1):
            attr_id = assessor.attribute_id
            click.echo(f"   [{i:2d}/25] {attr_id:30s} ", nl=False)

            finding = scanner._execute_assessor(assessor, repository, verbose=False)
            findings.append(finding)

            # Show result with color
            if finding.status == "pass":
                click.secho(f"✓ PASS ({finding.score:.0f})", fg="green")
            elif finding.status == "fail":
                click.secho(f"✗ FAIL ({finding.score:.0f})", fg="red")
            elif finding.status == "skipped":
                click.secho("⊘ SKIP", fg="yellow")
            elif finding.status == "not_applicable":
                click.secho("- N/A", fg="bright_black")
            else:
                click.secho(f"? {finding.status.upper()}", fg="yellow")

            time.sleep(0.05)  # Small delay for visual effect

        duration = time.time() - start_time

        # Step 4: Calculate scores
        click.echo()
        click.echo("📊 Calculating scores...")
        time.sleep(0.2)

        from ..services.scorer import Scorer

        scorer = Scorer()
        overall_score = scorer.calculate_overall_score(findings, None)
        certification_level = scorer.determine_certification_level(overall_score)
        assessed, skipped = scorer.count_assessed_attributes(findings)

        click.echo()
        click.echo("=" * 60)
        click.echo()
        click.echo("Assessment Complete!")
        click.echo()

        # Display score with color based on level
        score_color = "green" if overall_score >= 75 else "yellow" if overall_score >= 60 else "red"
        click.echo(f"  Overall Score: ", nl=False)
        click.secho(f"{overall_score:.1f}/100", fg=score_color, bold=True)
        click.echo(f"  Certification: ", nl=False)
        click.secho(certification_level, fg=score_color, bold=True)
        click.echo(f"  Assessed:      {assessed}/25 attributes")
        click.echo(f"  Skipped:       {skipped} attributes")
        click.echo(f"  Duration:      {duration:.1f}s")
        click.echo()

        # Step 5: Generate reports
        click.echo("📄 Generating reports...")
        time.sleep(0.3)

        from datetime import datetime

        from ..models.assessment import Assessment
        from ..reporters.html import HTMLReporter
        from ..reporters.markdown import MarkdownReporter

        # Create assessment object
        assessment = Assessment(
            repository=repository,
            timestamp=datetime.now(),
            overall_score=overall_score,
            certification_level=certification_level,
            attributes_assessed=assessed,
            attributes_skipped=skipped,
            attributes_total=len(findings),
            findings=findings,
            config=None,
            duration_seconds=round(duration, 1),
        )

        # Create output directory in current directory
        output_dir = Path.cwd() / ".agentready-demo"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate reports
        timestamp = assessment.timestamp.strftime("%Y%m%d-%H%M%S")

        html_reporter = HTMLReporter()
        html_file = output_dir / f"demo-report-{timestamp}.html"
        html_reporter.generate(assessment, html_file)
        click.echo(f"   ✓ HTML report: {html_file}")

        markdown_reporter = MarkdownReporter()
        md_file = output_dir / f"demo-report-{timestamp}.md"
        markdown_reporter.generate(assessment, md_file)
        click.echo(f"   ✓ Markdown report: {md_file}")

        import json

        json_file = output_dir / f"demo-assessment-{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(assessment.to_dict(), f, indent=2)
        click.echo(f"   ✓ JSON assessment: {json_file}")

        click.echo()
        click.echo("=" * 60)
        click.echo()

        # Step 6: Open browser
        if not no_browser:
            click.echo("🌐 Opening HTML report in browser...")
            time.sleep(0.2)
            try:
                webbrowser.open(html_file.as_uri())
                click.echo("   ✓ Browser opened")
            except Exception as e:
                click.echo(f"   ⚠ Could not open browser: {e}", err=True)
                click.echo(f"   Open manually: {html_file}")

        click.echo()
        click.secho("✅ Demo complete!", fg="green", bold=True)
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  • View HTML report: {html_file}")
        click.echo(f"  • View Markdown report: {md_file}")
        click.echo(f"  • Assess your own repo: agentready assess /path/to/repo")
        click.echo()

        if keep_repo:
            click.echo(f"Demo repository saved at: {demo_repo_path}")

    except Exception as e:
        click.echo()
        click.secho(f"❌ Error during demo: {str(e)}", fg="red", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        # Clean up temporary directory unless --keep-repo
        if not keep_repo:
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Best effort cleanup
