"""Unit tests for bootstrap functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentready.services.bootstrap import BootstrapGenerator, BootstrapResult


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


def _sentinel(name: str) -> str:
    return f"SENTINEL-{name}-DO-NOT-OVERWRITE\n"


class TestBootstrapGenerator:
    """Test BootstrapGenerator class."""

    def test_init_with_explicit_language(self, temp_repo):
        """Test initialization with explicit language."""
        gen = BootstrapGenerator(temp_repo, language="python")
        assert gen.repo_path == temp_repo
        assert gen.language == "python"

    def test_init_with_auto_detect(self, temp_repo):
        """Test initialization with auto language detection."""
        (temp_repo / "main.py").write_text("print('hello')")
        gen = BootstrapGenerator(temp_repo, language="auto")
        assert gen.repo_path == temp_repo
        assert gen.language in ["python", "javascript", "go"]

    def test_generate_all_dry_run(self, generator):
        """Test generate_all in dry-run mode."""
        result = generator.generate_all(dry_run=True)

        assert isinstance(result, BootstrapResult)
        assert len(result.created_files) > 0
        assert result.skipped_files == []
        assert all(isinstance(f, Path) for f in result.created_files)

        for file_path in result.created_files:
            assert not file_path.exists()

    def test_generate_all_creates_files(self, generator):
        """Test generate_all actually creates files."""
        result = generator.generate_all(dry_run=False)

        assert len(result.created_files) > 0
        assert result.skipped_files == []

        for file_path in result.created_files:
            assert file_path.exists()
            assert file_path.is_file()

    def test_generate_workflows(self, generator):
        """Test workflow generation."""
        workflows = generator._generate_workflows(dry_run=False)

        assert len(workflows) == 4

        workflow_names = [w.name for w in workflows]
        assert "agentready-assessment.yml" in workflow_names
        assert "tests.yml" in workflow_names
        assert "security.yml" in workflow_names
        assert "repomix-update.yml" in workflow_names

        for workflow in workflows:
            content = workflow.read_text()
            assert "name:" in content
            assert "on:" in content
            assert "jobs:" in content

    def test_generate_github_templates(self, generator):
        """Test GitHub template generation."""
        templates = generator._generate_github_templates(dry_run=False)

        assert len(templates) == 4

        template_names = [t.name for t in templates]
        assert "bug_report.md" in template_names
        assert "feature_request.md" in template_names
        assert "PULL_REQUEST_TEMPLATE.md" in template_names
        assert "CODEOWNERS" in template_names

    def test_generate_precommit_config(self, generator):
        """Test pre-commit configuration generation."""
        configs = generator._generate_precommit_config(dry_run=False)

        assert len(configs) == 1

        precommit_file = configs[0]
        assert precommit_file.name == ".pre-commit-config.yaml"

        content = precommit_file.read_text()
        assert "repos:" in content
        assert "hooks:" in content

    def test_generate_dependabot(self, generator):
        """Test Dependabot configuration generation."""
        configs = generator._generate_dependabot(dry_run=False)

        assert len(configs) == 1

        dependabot_file = configs[0]
        assert dependabot_file.name == "dependabot.yml"

        content = dependabot_file.read_text()
        assert "version:" in content
        assert "updates:" in content

    def test_generate_docs(self, generator):
        """Test documentation generation."""
        docs = generator._generate_docs(dry_run=False)

        assert len(docs) == 2

        doc_names = [d.name for d in docs]
        assert "CONTRIBUTING.md" in doc_names
        assert "CODE_OF_CONDUCT.md" in doc_names

    def test_generate_docs_skips_existing(self, generator):
        """Test that docs generation skips existing files."""
        contributing = generator.repo_path / "CONTRIBUTING.md"
        contributing.write_text("# Existing Contributing Guide")

        docs = generator._generate_docs(dry_run=False)

        assert len(docs) == 1
        assert docs[0].name == "CODE_OF_CONDUCT.md"

        assert contributing.read_text() == "# Existing Contributing Guide"

    def test_preserves_all_existing_bootstrap_targets_byte_for_byte(self, generator):
        """Pre-create every bootstrap target; none may change."""
        first = generator.generate_all(dry_run=False)
        targets = list(first.created_files)
        assert targets

        sentinels = {}
        for path in targets:
            sentinel = _sentinel(path.name)
            path.write_text(sentinel)
            sentinels[path] = sentinel

        second = generator.generate_all(dry_run=False)
        assert second.created_files == []
        assert set(second.skipped_files) == set(targets)

        for path, sentinel in sentinels.items():
            assert path.read_text() == sentinel

    def test_mixed_create_and_skip(self, generator):
        """Missing targets are created; existing targets are skipped."""
        precommit = generator.repo_path / ".pre-commit-config.yaml"
        precommit.write_text(_sentinel("pre-commit"))

        result = generator.generate_all(dry_run=False)

        assert precommit in result.skipped_files
        assert precommit.read_text() == _sentinel("pre-commit")
        assert len(result.created_files) > 0
        assert precommit not in result.created_files
        for created in result.created_files:
            assert created.exists()

    def test_idempotent_second_run(self, generator):
        """Second bootstrap creates nothing and skips every target."""
        first = generator.generate_all(dry_run=False)
        assert len(first.created_files) > 0

        second = generator.generate_all(dry_run=False)
        assert second.created_files == []
        assert set(second.skipped_files) == set(first.created_files)

    def test_dry_run_separates_would_create_and_would_skip(self, generator):
        """Dry-run classifies existing vs missing without writing."""
        precommit = generator.repo_path / ".pre-commit-config.yaml"
        precommit.write_text(_sentinel("pre-commit"))

        result = generator.generate_all(dry_run=True)

        assert precommit in result.skipped_files
        assert precommit.read_text() == _sentinel("pre-commit")
        assert len(result.created_files) > 0
        for path in result.created_files:
            assert not path.exists()
        assert precommit not in result.created_files

    def test_file_exists_error_during_exclusive_create_is_skip(self, generator):
        """Simulated FileExistsError from open('x') is recorded as skip."""
        target = generator.repo_path / "exclusive.txt"
        generator._result = BootstrapResult()

        real_open = open

        def open_x_raises(path, mode="r", *args, **kwargs):
            if mode == "x":
                raise FileExistsError(path)
            return real_open(path, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=open_x_raises):
            result = generator._write_file(target, "content", dry_run=False)

        assert result is None
        assert target in generator._result.skipped_files
        assert target not in generator._result.created_files
        assert not target.exists()

    def test_write_file_creates_directories(self, generator):
        """Test that _write_file creates parent directories."""
        nested_file = generator.repo_path / "a" / "b" / "c" / "test.txt"

        result = generator._write_file(nested_file, "test content", dry_run=False)

        assert result == nested_file
        assert nested_file.exists()
        assert nested_file.read_text() == "test content"

    def test_write_file_dry_run(self, generator):
        """Test that _write_file doesn't create files in dry-run mode."""
        test_file = generator.repo_path / "test.txt"
        generator._result = BootstrapResult()

        result = generator._write_file(test_file, "test content", dry_run=True)

        assert result == test_file
        assert test_file in generator._result.created_files
        assert not test_file.exists()

    def test_write_file_skips_existing_symlink(self, generator, temp_repo):
        """Existing symlink targets must not be replaced."""
        real = temp_repo / "real-precommit.yaml"
        real.write_text(_sentinel("real"))
        link = temp_repo / ".pre-commit-config.yaml"
        link.symlink_to(real)

        result = generator.generate_all(dry_run=False)
        assert link in result.skipped_files
        assert link.is_symlink()
        assert real.read_text() == _sentinel("real")

    def test_all_generated_files_are_in_correct_locations(self, generator):
        """Test that all files are generated in expected locations."""
        result = generator.generate_all(dry_run=False)
        files = result.created_files

        github_files = [f for f in files if ".github" in str(f)]
        root_files = [f for f in files if ".github" not in str(f)]

        assert len(github_files) > 0
        assert len(root_files) > 0

        workflow_files = [f for f in files if "workflows" in str(f)]
        assert len(workflow_files) == 4

        issue_template_files = [f for f in files if "ISSUE_TEMPLATE" in str(f)]
        assert len(issue_template_files) == 2

    def test_language_fallback(self, temp_repo):
        """Test that unknown languages fall back to Python."""
        gen = BootstrapGenerator(temp_repo, language="python")

        result = gen.generate_all(dry_run=True)
        assert len(result.created_files) > 0

    def test_generate_all_resets_result_state(self, generator):
        """Each generate_all call starts with a fresh result."""
        first = generator.generate_all(dry_run=False)
        second = generator.generate_all(dry_run=False)
        assert first is not second
        assert second.created_files == []
        assert len(second.skipped_files) == len(first.created_files)


class TestBootstrapGeneratorLanguageDetection:
    """Test language detection in BootstrapGenerator."""

    def test_detect_language_explicit(self, temp_repo):
        """Test explicit language specification."""
        gen = BootstrapGenerator(temp_repo, language="javascript")
        assert gen.language == "javascript"

    def test_detect_language_auto_python(self, temp_repo):
        """Test auto-detection of Python."""
        (temp_repo / "main.py").write_text("import sys")
        (temp_repo / "lib.py").write_text("def foo(): pass")

        gen = BootstrapGenerator(temp_repo, language="auto")
        assert gen.language in ["python", "javascript", "go"]

    def test_detect_language_auto_empty_repo(self, temp_repo):
        """Test auto-detection in empty repo falls back to Python."""
        gen = BootstrapGenerator(temp_repo, language="auto")
        assert gen.language == "python"


class TestBootstrapTemplateRendering:
    """Test that templates render correctly."""

    def test_workflow_templates_are_valid_yaml(self, generator):
        """Test that workflow templates produce valid YAML."""
        workflows = generator._generate_workflows(dry_run=False)

        for workflow in workflows:
            content = workflow.read_text()

            assert content.startswith("name:")
            assert "\non:" in content or "\non :" in content
            assert "\njobs:" in content
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
        result = generator.generate_all(dry_run=False)

        assert len(result.created_files) > 0

        for file_path in result.created_files:
            assert file_path.stat().st_size > 0
