"""Tests for Bootstrap template inheritance."""

import pytest
from jinja2 import Environment, PackageLoader


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for testing."""
    return Environment(
        loader=PackageLoader("agentready", "templates/bootstrap"),
        autoescape=False,  # YAML templates, not HTML
    )


class TestTemplateInheritance:
    """Test template inheritance for all languages."""

    def test_python_extends_base_tests(self, jinja_env):
        """Test that Python template extends base tests template correctly."""
        template = jinja_env.get_template("python/workflows/tests.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Tests" in content
        assert "on:" in content
        assert "pull_request:" in content
        assert "push:" in content
        assert "branches: [main, master]" in content
        assert "jobs:" in content
        assert "test:" in content
        assert "runs-on: ubuntu-latest" in content
        assert "uses: actions/checkout@v4" in content

        # Verify Python-specific elements
        assert "actions/setup-python@v5" in content
        assert "python-version:" in content
        assert "'3.12', '3.13'" in content
        assert "pip install" in content
        assert "pytest" in content
        assert "black --check" in content
        assert "isort --check" in content
        assert "ruff check" in content
        assert "codecov/codecov-action@v4" in content

    def test_javascript_extends_base_tests(self, jinja_env):
        """Test that JavaScript template extends base tests template correctly."""
        template = jinja_env.get_template("javascript/workflows/tests.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Tests" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "runs-on: ubuntu-latest" in content
        assert "uses: actions/checkout@v4" in content

        # Verify JavaScript-specific elements
        assert "actions/setup-node@v4" in content
        assert "node-version:" in content
        assert "'18', '20', '22'" in content
        assert "npm ci" in content
        assert "npm run lint" in content
        assert "npm run format:check" in content
        assert "npm test" in content
        assert "cache: 'npm'" in content

    def test_go_extends_base_tests(self, jinja_env):
        """Test that Go template extends base tests template correctly."""
        template = jinja_env.get_template("go/workflows/tests.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Tests" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "runs-on: ubuntu-latest" in content
        assert "uses: actions/checkout@v4" in content

        # Verify Go-specific elements
        assert "actions/setup-go@v5" in content
        assert "go-version:" in content
        assert "'1.23', '1.24'" in content
        assert "go mod download" in content
        assert "go test" in content
        assert "gofmt" in content
        assert "go vet" in content
        assert "golangci-lint" in content

    def test_python_extends_base_security(self, jinja_env):
        """Test that Python security template extends base correctly."""
        template = jinja_env.get_template("python/workflows/security.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Security" in content
        assert "on:" in content
        assert "schedule:" in content
        assert "cron: '0 0 * * 0'" in content
        assert "permissions:" in content
        assert "security-events: write" in content
        assert "codeql:" in content
        assert "github/codeql-action" in content

        # Verify Python-specific elements
        assert "languages: python" in content
        assert "safety:" in content
        assert "actions/setup-python@v5" in content
        assert "pip install safety" in content
        assert "safety check" in content

    def test_javascript_extends_base_security(self, jinja_env):
        """Test that JavaScript security template extends base correctly."""
        template = jinja_env.get_template("javascript/workflows/security.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Security" in content
        assert "github/codeql-action" in content

        # Verify JavaScript-specific elements
        assert "languages: javascript" in content
        assert "npm-audit:" in content
        assert "actions/setup-node@v4" in content
        assert "npm ci" in content
        assert "npm audit" in content

    def test_go_extends_base_security(self, jinja_env):
        """Test that Go security template extends base correctly."""
        template = jinja_env.get_template("go/workflows/security.yml.j2")
        content = template.render()

        # Verify common elements from base
        assert "name: Security" in content
        assert "github/codeql-action" in content

        # Verify Go-specific elements
        assert "languages: go" in content
        assert "gosec:" in content
        assert "actions/setup-go@v5" in content
        assert "securego/gosec" in content

    def test_python_extends_base_precommit(self, jinja_env):
        """Test that Python pre-commit template extends base correctly."""
        template = jinja_env.get_template("python/precommit.yaml.j2")
        content = template.render()

        # Verify common elements from base
        assert "repos:" in content
        assert "pre-commit/pre-commit-hooks" in content
        assert "trailing-whitespace" in content
        assert "end-of-file-fixer" in content
        assert "check-yaml" in content
        assert "detect-private-key" in content
        assert "conventional-pre-commit" in content

        # Verify Python-specific elements
        assert "psf/black" in content
        assert "pycqa/isort" in content
        assert "astral-sh/ruff-pre-commit" in content
        assert "python3.12" in content
        assert "--profile" in content
        assert "black" in content

    def test_javascript_extends_base_precommit(self, jinja_env):
        """Test that JavaScript pre-commit template extends base correctly."""
        template = jinja_env.get_template("javascript/precommit.yaml.j2")
        content = template.render()

        # Verify common elements from base
        assert "repos:" in content
        assert "pre-commit/pre-commit-hooks" in content
        assert "conventional-pre-commit" in content

        # Verify JavaScript-specific elements
        assert "mirrors-prettier" in content
        assert "mirrors-eslint" in content
        assert "eslint@8.56.0" in content
        assert "eslint-config-prettier" in content

    def test_go_extends_base_precommit(self, jinja_env):
        """Test that Go pre-commit template extends base correctly."""
        template = jinja_env.get_template("go/precommit.yaml.j2")
        content = template.render()

        # Verify common elements from base
        assert "repos:" in content
        assert "pre-commit/pre-commit-hooks" in content
        assert "conventional-pre-commit" in content

        # Verify Go-specific elements
        assert "pre-commit-golang" in content
        assert "golangci-lint" in content
        assert "go-fmt" in content
        assert "go-imports" in content
        assert "go-vet" in content
        assert "go-unit-tests" in content


class TestTemplateDRY:
    """Test that templates follow DRY principles."""

    def test_no_duplicate_common_structure_in_language_templates(self, jinja_env):
        """Test that language templates don't duplicate common structure."""
        # Read language-specific templates
        python_template = jinja_env.loader.get_source(
            jinja_env, "python/workflows/tests.yml.j2"
        )[0]
        javascript_template = jinja_env.loader.get_source(
            jinja_env, "javascript/workflows/tests.yml.j2"
        )[0]
        go_template = jinja_env.loader.get_source(
            jinja_env, "go/workflows/tests.yml.j2"
        )[0]

        # All should use {% extends %}
        assert "{% extends" in python_template
        assert "{% extends" in javascript_template
        assert "{% extends" in go_template

        # None should duplicate common YAML structure
        for template_source in [python_template, javascript_template, go_template]:
            # Should not contain full job definitions (only blocks)
            assert "jobs:" not in template_source
            assert "runs-on: ubuntu-latest" not in template_source
            assert (
                "on:\n" not in template_source
            )  # Workflow trigger (not "python-version:")

    def test_base_templates_contain_common_structure(self, jinja_env):
        """Test that base templates contain the common structure."""
        base_tests = jinja_env.loader.get_source(
            jinja_env, "_base/workflows/tests.yml.j2"
        )[0]
        base_security = jinja_env.loader.get_source(
            jinja_env, "_base/workflows/security.yml.j2"
        )[0]
        base_precommit = jinja_env.loader.get_source(
            jinja_env, "_base/precommit.yaml.j2"
        )[0]

        # Base tests should have common YAML structure
        assert "name: Tests" in base_tests
        assert "on:" in base_tests
        assert "jobs:" in base_tests
        assert "runs-on: ubuntu-latest" in base_tests
        assert "{% block" in base_tests

        # Base security should have common structure
        assert "name: Security" in base_security
        assert "permissions:" in base_security
        assert "github/codeql-action" in base_security
        assert "{% block" in base_security

        # Base pre-commit should have common hooks
        assert "repos:" in base_precommit
        assert "pre-commit/pre-commit-hooks" in base_precommit
        assert "conventional-pre-commit" in base_precommit
        assert "{% block" in base_precommit
