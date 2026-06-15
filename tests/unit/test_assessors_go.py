"""Tests for Go language support across all assessors."""

import subprocess

import pytest

from agentready.assessors.code_quality import (
    CyclomaticComplexityAssessor,
    StructuredLoggingAssessor,
    TypeAnnotationsAssessor,
)
from agentready.assessors.documentation import InlineDocumentationAssessor
from agentready.assessors.structure import StandardLayoutAssessor
from agentready.assessors.testing import (
    CIQualityGatesAssessor,
    TestExecutionAssessor,
)
from agentready.models.repository import Repository


def _make_go_repo(tmp_path, languages=None, **kwargs):
    """Create a test Go repository with git init."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return Repository(
        path=tmp_path,
        name="test-go-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"Go": 20},
        total_files=kwargs.get("total_files", 30),
        total_lines=kwargs.get("total_lines", 5000),
    )


def _git_add(tmp_path, *files):
    """Stage files in git so git ls-files finds them."""
    for f in files:
        subprocess.run(
            ["git", "add", str(f)],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )


# =============================================================================
# TestExecutionAssessor — Go support
# =============================================================================


class TestTestExecutionAssessorGo:
    """Test Go support in TestExecutionAssessor."""

    def test_applicable_with_go_test_files(self, tmp_path):
        """Go repos with *_test.go files should be applicable."""
        repo = _make_go_repo(tmp_path)
        test_file = tmp_path / "handler_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = TestExecutionAssessor()
        assert assessor.is_applicable(repo)

    def test_not_applicable_without_test_files(self, tmp_path):
        """Go repos without test files or test dirs should not be applicable."""
        repo = _make_go_repo(tmp_path)
        go_file = tmp_path / "main.go"
        go_file.write_text("package main\n")
        _git_add(tmp_path, go_file)

        assessor = TestExecutionAssessor()
        assert not assessor.is_applicable(repo)

    def test_go_full_score(self, tmp_path):
        """Go repo with tests, command, coverage, and race detection scores 100."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "handler_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        makefile = tmp_path / "Makefile"
        makefile.write_text(
            ".PHONY: test\n"
            "test:\n"
            "\tgo test -v -race -coverprofile=coverage.txt -covermode=atomic ./...\n"
        )

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("test files found" in e for e in finding.evidence)
        assert any("Race detector enabled" in e for e in finding.evidence)

    def test_go_tests_only(self, tmp_path):
        """Go repo with only test files scores partial."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "main_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 40.0
        assert finding.status == "fail"

    def test_go_tests_with_ci(self, tmp_path):
        """Go repo with test files and CI go test command."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "main_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text(
            "jobs:\n  test:\n    steps:\n"
            "      - run: go test -race -coverprofile=coverage.txt ./...\n"
        )

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_go_remediation_on_fail(self, tmp_path):
        """Failed Go assessment includes Go-specific remediation."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "main_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.remediation is not None
        assert any("go test" in cmd for cmd in finding.remediation.commands)

    def test_go_test_command_in_agents_md(self, tmp_path):
        """Go test command documented in AGENTS.md is detected (#470)."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "main_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "## Quick Commands\n\n"
            "| Action | Command |\n"
            "|--------|----------|\n"
            "| Run tests | `make test` (runs fmt and vet first) |\n"
            "| Lint | `make lint` |\n"
        )

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert any("test command found" in e.lower() for e in finding.evidence)
        assert finding.score >= 60.0


# =============================================================================
# TypeAnnotationsAssessor — Go support
# =============================================================================


class TestTypeAnnotationsAssessorGo:
    """Test Go support in TypeAnnotationsAssessor."""

    def test_go_is_applicable(self, tmp_path):
        """Go repos should be applicable for type annotations."""
        repo = _make_go_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        assert assessor.is_applicable(repo)

    def test_go_statically_typed_high_score(self, tmp_path):
        """Go repos score high because Go is statically typed."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package main\n\n"
            "func HandleRequest(w http.ResponseWriter, r *http.Request) {\n"
            "}\n\n"
            "func ProcessData(input string) (string, error) {\n"
            "\treturn input, nil\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 95.0
        assert any("statically typed" in e for e in finding.evidence)

    def test_go_heavy_any_usage_lower_score(self, tmp_path):
        """Go repos with heavy interface{}/any usage score lower."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package main\n\n"
            "func Process(data interface{}) interface{} {\n"
            "\treturn data\n"
            "}\n\n"
            "func Transform(input any) any {\n"
            "\treturn input\n"
            "}\n\n"
            "func Other(x any, y any) any {\n"
            "\treturn x\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.score < 95.0
        assert any("interface{}" in e or "any" in e for e in finding.evidence)

    def test_go_no_source_files(self, tmp_path):
        """Go repo with no source files returns not_applicable."""
        repo = _make_go_repo(tmp_path)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_non_go_repo_not_affected(self, tmp_path):
        """Python repos still use the Python assessment path."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        repo = Repository(
            path=tmp_path,
            name="test-py-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 50},
            total_files=10,
            total_lines=1000,
        )

        py_file = tmp_path / "main.py"
        py_file.write_text("def hello(): pass\n")
        _git_add(tmp_path, py_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        # Should use Python path, not Go
        assert "statically typed" not in str(finding.evidence)


# =============================================================================
# StandardLayoutAssessor — Go support
# =============================================================================


class TestStandardLayoutAssessorGo:
    """Test Go layout detection in StandardLayoutAssessor."""

    def test_go_full_layout(self, tmp_path):
        """Go repo with go.mod + cmd/ + internal/ + tests scores high."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text("module github.com/test/repo\n\ngo 1.22\n")
        (tmp_path / "cmd" / "myapp").mkdir(parents=True)
        (tmp_path / "cmd" / "myapp" / "main.go").write_text("package main\n")
        (tmp_path / "internal" / "handler").mkdir(parents=True)
        (tmp_path / "internal" / "handler" / "handler.go").write_text(
            "package handler\n"
        )

        test_file = tmp_path / "internal" / "handler" / "handler_test.go"
        test_file.write_text('package handler\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("go.mod" in e for e in finding.evidence)
        assert any("cmd/" in e for e in finding.evidence)
        assert any("internal/" in e for e in finding.evidence)

    def test_go_simple_project(self, tmp_path):
        """Go repo with go.mod + root main.go + tests scores well."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text("module github.com/test/repo\n\ngo 1.22\n")
        (tmp_path / "main.go").write_text("package main\n")

        test_file = tmp_path / "main_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # go.mod (30) + main.go at root (20) + tests (20) = 70
        assert finding.score >= 70.0
        assert any("main.go" in e and "✓" in e for e in finding.evidence)

    def test_go_missing_go_mod(self, tmp_path):
        """Go repo without go.mod scores lower."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "main.go").write_text("package main\n")

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.score < 75.0
        assert any("go.mod" in e and "✗" in e for e in finding.evidence)

    def test_go_remediation_includes_go_commands(self, tmp_path):
        """Failed Go layout assessment has Go-specific remediation."""
        repo = _make_go_repo(tmp_path)

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.remediation is not None
        assert any("go mod init" in cmd for cmd in finding.remediation.commands)

    def test_go_monorepo_layout(self, tmp_path):
        """Go monorepo with go.mod in subdirectories scores well."""
        repo = _make_go_repo(tmp_path)

        # Create monorepo structure
        svc_a = tmp_path / "service-a"
        svc_b = tmp_path / "service-b"
        svc_a.mkdir()
        svc_b.mkdir()
        (svc_a / "go.mod").write_text("module github.com/test/service-a\n\ngo 1.22\n")
        (svc_b / "go.mod").write_text("module github.com/test/service-b\n\ngo 1.22\n")
        (svc_a / "cmd").mkdir()
        (svc_a / "cmd" / "main.go").write_text("package main\n")
        (svc_b / "internal").mkdir()
        (svc_b / "internal" / "handler.go").write_text("package handler\n")

        test_file = svc_a / "handler_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("monorepo" in e for e in finding.evidence)
        assert any("cmd/" in e for e in finding.evidence)
        assert any("internal/" in e for e in finding.evidence)

    def test_python_repo_uses_python_layout(self, tmp_path):
        """Python repos still use the Python layout detection path."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        repo = Repository(
            path=tmp_path,
            name="test-py-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 50},
            total_files=10,
            total_lines=1000,
        )

        (tmp_path / "src").mkdir()

        assessor = StandardLayoutAssessor()
        finding = assessor.assess(repo)

        # Should not mention Go-specific dirs
        assert not any("go.mod" in e for e in finding.evidence)


# =============================================================================
# CyclomaticComplexityAssessor — Go support
# =============================================================================


class TestCyclomaticComplexityAssessorGo:
    """Test Go support in CyclomaticComplexityAssessor."""

    def test_go_is_applicable(self, tmp_path):
        """Go repos should be applicable for complexity checking."""
        repo = _make_go_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()
        assert assessor.is_applicable(repo)

    def test_go_with_golangci_lint_complexity(self, tmp_path):
        """Go repo with golangci-lint cyclop/gocyclo enabled passes."""
        repo = _make_go_repo(tmp_path)

        config = tmp_path / ".golangci.yml"
        config.write_text(
            "linters:\n" "  enable:\n" "    - gocyclo\n" "    - errcheck\n"
        )

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 80.0
        assert any(
            "golangci" in e.lower() or "complexity" in e.lower()
            for e in finding.evidence
        )

    def test_go_with_cyclop_linter(self, tmp_path):
        """Go repo with cyclop linter configured passes."""
        repo = _make_go_repo(tmp_path)

        config = tmp_path / ".golangci.yaml"
        config.write_text("linters:\n" "  enable:\n" "    - cyclop\n")

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 80.0

    def test_go_commented_linter_not_detected(self, tmp_path):
        """Commented-out complexity linter does not produce a configured-pass."""
        from agentready.services.scanner import MissingToolError

        repo = _make_go_repo(tmp_path)

        config = tmp_path / ".golangci.yml"
        config.write_text(
            "# gocyclo is too strict for this project\n"
            "linters:\n"
            "  enable:\n"
            "    - govet\n"
            "    - errcheck\n"
        )

        assessor = CyclomaticComplexityAssessor()
        with pytest.raises(MissingToolError):
            assessor.assess(repo)

    def test_go_disabled_linter_not_detected(self, tmp_path):
        """Complexity linter in disable list does not produce a configured-pass."""
        from agentready.services.scanner import MissingToolError

        repo = _make_go_repo(tmp_path)

        config = tmp_path / ".golangci.yml"
        config.write_text(
            "linters:\n" "  disable:\n" "    - gocyclo\n" "  enable:\n" "    - govet\n"
        )

        assessor = CyclomaticComplexityAssessor()
        with pytest.raises(MissingToolError):
            assessor.assess(repo)

    def test_go_linter_in_settings_only_not_detected(self, tmp_path):
        """Complexity linter in linters-settings but not enabled does not pass."""
        from agentready.services.scanner import MissingToolError

        repo = _make_go_repo(tmp_path)

        config = tmp_path / ".golangci.yml"
        config.write_text(
            "linters-settings:\n"
            "  gocyclo:\n"
            "    min-complexity: 15\n"
            "linters:\n"
            "  enable:\n"
            "    - govet\n"
        )

        assessor = CyclomaticComplexityAssessor()
        with pytest.raises(MissingToolError):
            assessor.assess(repo)

    def test_go_without_tools_raises_missing_tool(self, tmp_path):
        """Go repo without gocyclo or golangci-lint config raises MissingToolError."""
        from agentready.services.scanner import MissingToolError

        repo = _make_go_repo(tmp_path)

        assessor = CyclomaticComplexityAssessor()
        with pytest.raises(MissingToolError):
            assessor.assess(repo)


# =============================================================================
# StructuredLoggingAssessor — Go support
# =============================================================================


class TestStructuredLoggingAssessorGo:
    """Test Go support in StructuredLoggingAssessor."""

    def test_go_with_zap(self, tmp_path):
        """Go repo using zap should pass."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text(
            "module github.com/test/repo\n\n"
            "go 1.22\n\n"
            "require go.uber.org/zap v1.27.0\n"
        )

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("zap" in e for e in finding.evidence)

    def test_go_with_logrus(self, tmp_path):
        """Go repo using logrus should pass."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text(
            "module github.com/test/repo\n\n"
            "go 1.22\n\n"
            "require github.com/sirupsen/logrus v1.9.0\n"
        )

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("logrus" in e for e in finding.evidence)

    def test_go_with_zerolog(self, tmp_path):
        """Go repo using zerolog should pass."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text(
            "module github.com/test/repo\n\n"
            "go 1.22\n\n"
            "require github.com/rs/zerolog v1.33.0\n"
        )

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("zerolog" in e for e in finding.evidence)

    def test_go_with_slog_stdlib(self, tmp_path):
        """Go repo using stdlib log/slog should pass."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text("module github.com/test/repo\n\ngo 1.22\n")

        go_file = tmp_path / "main.go"
        go_file.write_text(
            'package main\n\nimport "log/slog"\n\n'
            'func main() {\n\tslog.Info("hello")\n}\n'
        )
        _git_add(tmp_path, go_file)

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("slog" in e for e in finding.evidence)

    def test_go_without_structured_logging(self, tmp_path):
        """Go repo without structured logging fails."""
        repo = _make_go_repo(tmp_path)

        (tmp_path / "go.mod").write_text("module github.com/test/repo\n\ngo 1.22\n")

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None

    def test_go_no_go_mod(self, tmp_path):
        """Go repo without go.mod returns not_applicable."""
        repo = _make_go_repo(tmp_path)

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_go_monorepo_zap_in_subdir(self, tmp_path):
        """Go monorepo with zap in subdirectory go.mod should pass."""
        repo = _make_go_repo(tmp_path)

        svc = tmp_path / "my-service"
        svc.mkdir()
        (svc / "go.mod").write_text(
            "module github.com/test/my-service\n\n"
            "go 1.22\n\n"
            "require go.uber.org/zap v1.27.0\n"
        )

        assessor = StructuredLoggingAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("zap" in e for e in finding.evidence)


# =============================================================================
# Go monorepo integration tests
# =============================================================================


class TestGoMonorepoSupport:
    """Test that assessors handle Go monorepos with go.mod in subdirectories."""

    def test_complexity_golangci_in_subdir(self, tmp_path):
        """CyclomaticComplexityAssessor finds golangci-lint config in subdirectory."""
        repo = _make_go_repo(tmp_path)

        svc = tmp_path / "my-api"
        svc.mkdir()
        (svc / "go.mod").write_text("module github.com/test/api\n\ngo 1.22\n")
        (svc / ".golangci.yml").write_text("linters:\n  enable:\n    - gocyclo\n")

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 70.0

    def test_dependency_pinning_go_sum_in_subdir(self, tmp_path):
        """DependencyPinningAssessor finds go.sum in subdirectory."""
        from agentready.assessors.stub_assessors import DependencyPinningAssessor

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        repo = Repository(
            path=tmp_path,
            name="test-go-mono",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 20},
            total_files=30,
            total_lines=5000,
        )

        svc = tmp_path / "my-service"
        svc.mkdir()
        (svc / "go.mod").write_text("module github.com/test/svc\n\ngo 1.22\n")
        (svc / "go.sum").write_text("github.com/some/dep v1.0.0 h1:abc=\n")

        assessor = DependencyPinningAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("go.sum" in e for e in finding.evidence)


# =============================================================================
# InlineDocumentationAssessor — Go godoc support
# =============================================================================


class TestInlineDocumentationAssessorGo:
    """Test Go godoc support in InlineDocumentationAssessor."""

    def test_go_is_applicable(self, tmp_path):
        """Go repos should be applicable for inline documentation."""
        repo = _make_go_repo(tmp_path)
        assessor = InlineDocumentationAssessor()
        assert assessor.is_applicable(repo)

    def test_go_well_documented(self, tmp_path):
        """Go repo with godoc comments on all exports scores high."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// Handler processes incoming HTTP requests.\n"
            "func Handler() {}\n\n"
            "// ErrNotFound is returned when a resource is missing.\n"
            'var ErrNotFound = errors.New("not found")\n\n'
            "// Config holds the application configuration.\n"
            "type Config struct {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_undocumented_exports(self, tmp_path):
        """Go repo with undocumented exports scores low."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "func Handler() {}\n\n"
            "func Process() {}\n\n"
            "func Transform() {}\n\n"
            "type Config struct {}\n\n"
            "var MaxRetries = 3\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 75.0

    def test_go_private_symbols_ignored(self, tmp_path):
        """Private (lowercase) Go symbols should not count."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// Handler processes requests.\n"
            "func Handler() {}\n\n"
            "func privateHelper() {}\n\n"
            "func anotherPrivate() {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_doc_go_detected(self, tmp_path):
        """doc.go files should be detected in evidence."""
        repo = _make_go_repo(tmp_path)

        doc_file = tmp_path / "doc.go"
        doc_file.write_text(
            "// Package handler provides HTTP handling.\npackage handler\n"
        )

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// Handler processes requests.\n"
            "func Handler() {}\n"
        )
        _git_add(tmp_path, go_file, doc_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert any("doc.go" in e for e in finding.evidence)

    def test_go_test_files_excluded(self, tmp_path):
        """Test files (*_test.go) should not count toward documentation coverage."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// Handler processes requests.\n"
            "func Handler() {}\n"
        )

        test_file = tmp_path / "handler_test.go"
        test_file.write_text(
            "package handler\n\n" "func TestHandler() {}\n" "func TestOther() {}\n"
        )
        _git_add(tmp_path, go_file, test_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_no_exports(self, tmp_path):
        """Go repo with no exported symbols returns not_applicable."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text("package handler\n\n" "func privateFunc() {}\n")
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"


# =============================================================================
# CIQualityGatesAssessor — Go (already supported, verify)
# =============================================================================


class TestCIQualityGatesAssessorGo:
    """Verify Go CI patterns are detected."""

    def test_go_test_in_ci(self, tmp_path):
        """CI config with 'go test' should be detected as a test gate."""
        repo = _make_go_repo(tmp_path)

        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text(
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: go test ./...\n"
            "      - run: golangci-lint run\n"
            "      - run: go vet ./...\n"
        )

        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        assert any("Test gate" in e for e in finding.evidence)
        assert any("Lint gate" in e for e in finding.evidence)
        assert any("Type-check gate" in e for e in finding.evidence)


# =============================================================================
# Regression tests for PR #412 review findings
# =============================================================================


class TestGoMultiLineGodoc:
    """Tests for multi-line godoc comment detection."""

    def test_go_multiline_doc_comment(self, tmp_path):
        """Multi-line // doc comments should be detected."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// Handler processes incoming HTTP requests.\n"
            "// It routes them to the appropriate service method.\n"
            "func Handler() {}\n\n"
            "// Config holds the application configuration.\n"
            "// It is loaded from environment variables.\n"
            "type Config struct {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_block_comment_doc(self, tmp_path):
        """/* */ block-style doc comments should be detected."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "/* Handler processes incoming HTTP requests. */\n"
            "func Handler() {}\n\n"
            "/* Config holds the application configuration.\n"
            "It supports multiple environments. */\n"
            "type Config struct {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_method_with_receiver_documented(self, tmp_path):
        """Exported methods with receivers should be detected and docs counted."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "server.go"
        go_file.write_text(
            "package server\n\n"
            "// Start begins listening for connections.\n"
            "func (s *Server) Start() {}\n\n"
            "// Stop gracefully shuts down the server.\n"
            "func (s *Server) Stop() {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0


class TestGoMakeVariableTest:
    """Tests for $(GO) test Makefile convention."""

    def test_go_make_variable_test_command(self, tmp_path):
        """$(GO) test should be recognized as a test command."""
        repo = _make_go_repo(tmp_path)

        test_file = tmp_path / "handler_test.go"
        test_file.write_text('package main\nimport "testing"\n')
        _git_add(tmp_path, test_file)

        makefile = tmp_path / "Makefile"
        makefile.write_text(
            "GO ?= go\n\n"
            ".PHONY: test\n"
            "test:\n"
            "\t$(GO) test -v -race -coverprofile=coverage.txt ./...\n"
        )

        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("test command found" in e.lower() for e in finding.evidence)


class TestGoAnyInComments:
    """Tests for any/interface{} matching excluding comments."""

    def test_go_any_in_comments_not_counted(self, tmp_path):
        """'any' in comments should not inflate the type-weakness count."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package main\n\n"
            "// Process handles any incoming request.\n"
            "// It can accept any valid payload.\n"
            "func Process(data string) string {\n"
            '\treturn "ok"\n'
            "}\n\n"
            "func Transform(input int) int {\n"
            "\treturn input * 2\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 95.0
        assert finding.status == "pass"

    def test_go_any_in_code_still_counted(self, tmp_path):
        """'any' in actual code should still be counted."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package main\n\n"
            "func Process(data any) any {\n"
            "\treturn data\n"
            "}\n\n"
            "func Other(x any, y any) any {\n"
            "\treturn x\n"
            "}\n\n"
            "func More(a any) any {\n"
            "\treturn a\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.score < 95.0

    def test_go_any_in_string_literals_not_counted(self, tmp_path):
        """'any' in string literals should not inflate the type-weakness count."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package main\n\n"
            'import "fmt"\n\n'
            "func Process(data string) string {\n"
            '\tfmt.Println("can accept any value")\n'
            '\treturn "any"\n'
            "}\n\n"
            "func Transform(input int) int {\n"
            "\treturn input * 2\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 95.0
        assert finding.status == "pass"


class TestGoNonSymbolNameDocs:
    """Tests for doc comments that don't start with the symbol name."""

    def test_go_descriptive_comment_accepted(self, tmp_path):
        """Comments describing the function without symbol name prefix are valid."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "remote.go"
        go_file.write_text(
            "package context\n\n"
            "// Filter remotes by given hostnames, maintains original order\n"
            "func FilterByHosts(hosts []string) []string {\n"
            "\treturn hosts\n"
            "}\n\n"
            "// Returns the first remote matching the given name\n"
            "func FindByName(name string) string {\n"
            "\treturn name\n"
            "}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0

    def test_go_blank_line_separates_comment(self, tmp_path):
        """A blank line between comment and symbol means no doc comment."""
        repo = _make_go_repo(tmp_path)

        go_file = tmp_path / "handler.go"
        go_file.write_text(
            "package handler\n\n"
            "// This is not a doc comment because of the blank line.\n"
            "\n"
            "func Handler() {}\n\n"
            "func Process() {}\n"
        )
        _git_add(tmp_path, go_file)

        assessor = InlineDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 75.0
