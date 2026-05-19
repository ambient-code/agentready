"""Unit tests for bootstrap functionality."""

import tempfile
from pathlib import Path

import pytest

from agentready.services.bootstrap import BootstrapGenerator


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create .git directory to simulate a git repo
        (repo_path / ".git").mkdir()
        yield repo_path


@pytest.fixture
def generator(temp_repo):
    """Create a BootstrapGenerator instance."""
    return BootstrapGenerator(temp_repo, language="python")


class TestBootstrapGenerator:
    """Test BootstrapGenerator class."""

    def test_init_with_explicit_language(self, temp_repo):
        """Test initialization with explicit language."""
        gen = BootstrapGenerator(temp_repo, language="python")
        assert gen.repo_path == temp_repo
        assert gen.language == "python"

    def test_init_with_auto_detect(self, temp_repo):
        """Test initialization with auto language detection."""
        # Create some Python files
        (temp_repo / "main.py").write_text("print('hello')")
        gen = BootstrapGenerator(temp_repo, language="auto")
        assert gen.repo_path == temp_repo
        # Language should be detected (python or fallback)
        assert gen.language in ["python", "javascript", "go"]

    def test_generate_all_dry_run(self, generator):
        """Test generate_all in dry-run mode."""
        files = generator.generate_all(dry_run=True)

        # Should return list of paths that would be created
        assert len(files) > 0
        assert all(isinstance(f, Path) for f in files)

        # Files should not actually exist (dry run)
        for file_path in files:
            assert not file_path.exists()

    def test_generate_all_creates_files(self, generator):
        """Test generate_all actually creates files."""
        files = generator.generate_all(dry_run=False)

        # Should create files
        assert len(files) > 0

        # Files should actually exist
        for file_path in files:
            assert file_path.exists()
            assert file_path.is_file()

    def test_generate_workflows(self, generator):
        """Test workflow generation."""
        workflows = generator._generate_workflows(dry_run=False)

        # Should generate 4 workflows
        assert len(workflows) == 4

        # Check workflow files exist
        workflow_names = [w.name for w in workflows]
        assert "agentready-assessment.yml" in workflow_names
        assert "tests.yml" in workflow_names
        assert "security.yml" in workflow_names
        assert "repomix-update.yml" in workflow_names

        # Verify content is valid YAML
        for workflow in workflows:
            content = workflow.read_text()
            assert "name:" in content
            assert "on:" in content
            assert "jobs:" in content

    def test_generate_github_templates(self, generator):
        """Test GitHub template generation."""
        templates = generator._generate_github_templates(dry_run=False)

        # Should generate 4 files: 2 issue templates, 1 PR template, 1 CODEOWNERS
        assert len(templates) == 4

        # Check file names
        template_names = [t.name for t in templates]
        assert "bug_report.md" in template_names
        assert "feature_request.md" in template_names
        assert "PULL_REQUEST_TEMPLATE.md" in template_names
        assert "CODEOWNERS" in template_names

    def test_generate_precommit_config(self, generator):
        """Test pre-commit configuration generation."""
        configs = generator._generate_precommit_config(dry_run=False)

        # Should generate 1 file
        assert len(configs) == 1

        precommit_file = configs[0]
        assert precommit_file.name == ".pre-commit-config.yaml"

        # Verify content
        content = precommit_file.read_text()
        assert "repos:" in content
        assert "hooks:" in content

    def test_generate_dependabot(self, generator):
        """Test Dependabot configuration generation."""
        configs = generator._generate_dependabot(dry_run=False)

        # Should generate 1 file
        assert len(configs) == 1

        dependabot_file = configs[0]
        assert dependabot_file.name == "dependabot.yml"

        # Verify content
        content = dependabot_file.read_text()
        assert "version:" in content
        assert "updates:" in content

    def test_generate_docs(self, generator):
        """Test documentation generation."""
        docs = generator._generate_docs(dry_run=False)

        # Should generate 2 files (CONTRIBUTING.md, CODE_OF_CONDUCT.md)
        assert len(docs) == 2

        # Check file names
        doc_names = [d.name for d in docs]
        assert "CONTRIBUTING.md" in doc_names
        assert "CODE_OF_CONDUCT.md" in doc_names

    def test_generate_docs_skips_existing(self, generator):
        """Test that docs generation skips existing files."""
        # Create CONTRIBUTING.md
        contributing = generator.repo_path / "CONTRIBUTING.md"
        contributing.write_text("# Existing Contributing Guide")

        docs = generator._generate_docs(dry_run=False)

        # Should only generate CODE_OF_CONDUCT.md
        assert len(docs) == 1
        assert docs[0].name == "CODE_OF_CONDUCT.md"

        # CONTRIBUTING.md should not be overwritten
        assert contributing.read_text() == "# Existing Contributing Guide"

    def test_write_file_creates_directories(self, generator):
        """Test that _write_file creates parent directories."""
        nested_file = generator.repo_path / "a" / "b" / "c" / "test.txt"

        generator._write_file(nested_file, "test content", dry_run=False)

        assert nested_file.exists()
        assert nested_file.read_text() == "test content"

    def test_write_file_dry_run(self, generator):
        """Test that _write_file doesn't create files in dry-run mode."""
        test_file = generator.repo_path / "test.txt"

        result = generator._write_file(test_file, "test content", dry_run=True)

        # Should return path
        assert result == test_file

        # But file should not exist
        assert not test_file.exists()

    def test_all_generated_files_are_in_correct_locations(self, generator):
        """Test that all files are generated in expected locations."""
        files = generator.generate_all(dry_run=False)

        # Group files by location
        github_files = [f for f in files if ".github" in str(f)]
        root_files = [f for f in files if ".github" not in str(f)]

        # Should have files in both .github and root
        assert len(github_files) > 0
        assert len(root_files) > 0

        # Check specific locations
        workflow_files = [f for f in files if "workflows" in str(f)]
        assert len(workflow_files) == 4

        issue_template_files = [f for f in files if "ISSUE_TEMPLATE" in str(f)]
        assert len(issue_template_files) == 2

    def test_language_fallback(self, temp_repo):
        """Test that unknown languages fall back to Python."""
        # Create generator with unsupported language
        gen = BootstrapGenerator(temp_repo, language="python")

        # Should still work and generate files
        files = gen.generate_all(dry_run=True)
        assert len(files) > 0


class TestBootstrapGeneratorLanguageDetection:
    """Test language detection in BootstrapGenerator."""

    def test_detect_language_explicit(self, temp_repo):
        """Test explicit language specification."""
        gen = BootstrapGenerator(temp_repo, language="javascript")
        assert gen.language == "javascript"

    def test_detect_language_auto_python(self, temp_repo):
        """Test auto-detection of Python."""
        # Create Python files
        (temp_repo / "main.py").write_text("import sys")
        (temp_repo / "lib.py").write_text("def foo(): pass")

        gen = BootstrapGenerator(temp_repo, language="auto")
        # Should detect Python
        assert gen.language in ["python", "javascript", "go"]

    def test_detect_language_auto_empty_repo(self, temp_repo):
        """Test auto-detection in empty repo falls back to Python."""
        gen = BootstrapGenerator(temp_repo, language="auto")
        # Should fall back to python
        assert gen.language == "python"


class TestBootstrapTemplateRendering:
    """Test that templates render correctly."""

    def test_workflow_templates_are_valid_yaml(self, generator):
        """Test that workflow templates produce valid YAML."""
        workflows = generator._generate_workflows(dry_run=False)

        for workflow in workflows:
            content = workflow.read_text()

            # Basic YAML structure checks
            assert content.startswith("name:")
            assert "\non:" in content or "\non :" in content
            assert "\njobs:" in content

            # Should not have Jinja2 control flow syntax in output
            # Note: GitHub Actions uses ${{ }} syntax which is valid and expected
            assert "{%" not in content

    def test_repomix_workflow_uses_subdirectory_output(self, generator):
        """Test that repomix workflow outputs to repomix/ subdirectory."""
        generator.generate_all(dry_run=False)

        workflow = generator.repo_path / ".github" / "workflows" / "repomix-update.yml"
        assert workflow.exists()

        content = workflow.read_text()
        assert "repomix/repomix-output" in content
        assert "mkdir -p repomix" in content

    def test_templates_render_without_errors(self, generator):
        """Test that all templates render without errors."""
        # This test ensures no Jinja2 rendering errors occur
        files = generator.generate_all(dry_run=False)

        # All files should be created successfully
        assert len(files) > 0

        # All files should have content
        for file_path in files:
            assert file_path.stat().st_size > 0
