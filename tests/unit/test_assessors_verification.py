"""Tests for verification assessors."""

from agentready.assessors.verification import SingleFileVerificationAssessor
from agentready.models.repository import Repository


class TestSingleFileVerificationAssessor:
    """Test SingleFileVerificationAssessor."""

    def _make_repo(self, tmp_path, **kwargs):
        """Create a test repository."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir(exist_ok=True)
        return Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages=kwargs.get("languages", {"Python": 100}),
            total_files=10,
            total_lines=1000,
        )

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = SingleFileVerificationAssessor()
        assert assessor.attribute_id == "single_file_verification"

    def test_tier(self):
        """Test tier is Essential (1)."""
        assessor = SingleFileVerificationAssessor()
        assert assessor.tier == 1

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = SingleFileVerificationAssessor()
        assert assessor.attribute.default_weight == 0.05

    def test_fails_with_no_context_files(self, tmp_path):
        """Test that assessor fails when no context or config files exist."""
        repo = self._make_repo(tmp_path)

        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_passes_with_lint_in_claude_md(self, tmp_path):
        """Test that a lint command in CLAUDE.md scores as lint found."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Commands\n- Lint: `ruff check path/to/file.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 50.0
        assert any("lint" in e.lower() for e in finding.evidence)

    def test_passes_with_typecheck_in_claude_md(self, tmp_path):
        """Test that a type-check command in CLAUDE.md scores as typecheck found."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Commands\n- Type check: `mypy src/module.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 50.0
        assert any("type-check" in e.lower() for e in finding.evidence)

    def test_full_score_with_both_lint_and_typecheck(self, tmp_path):
        """Test that both lint + typecheck commands give full score."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Commands\n"
            "- Lint: `ruff check path/to/file.py`\n"
            "- Type check: `mypy path/to/file.py`\n"
        )

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_recognizes_eslint(self, tmp_path):
        """Test that eslint pattern is recognized as lint."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Run `eslint src/index.ts` to lint.\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0

    def test_recognizes_rubocop(self, tmp_path):
        """Test that rubocop pattern is recognized as lint (was previously missed)."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Run `rubocop app/models/user.rb` to lint.\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0
        assert any("lint" in e.lower() for e in finding.evidence)

    def test_recognizes_black(self, tmp_path):
        """Test that black pattern is recognized as lint."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Format: `black src/module.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0

    def test_recognizes_golangci_lint(self, tmp_path):
        """Test that golangci-lint pattern is recognized as lint."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Run `golangci-lint run pkg/handler.go`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0

    def test_recognizes_pyright(self, tmp_path):
        """Test that pyright pattern is recognized as typecheck."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Type check: `pyright src/main.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0
        assert any("type-check" in e.lower() for e in finding.evidence)

    def test_readme_gives_lower_score_than_context_file(self, tmp_path):
        """Test that README matches score lower than context file matches."""
        readme = tmp_path / "README.md"
        readme.write_text("Lint: `ruff check path/to/file.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 30.0
        assert any("README" in e for e in finding.evidence)

    def test_linter_config_fallback(self, tmp_path):
        """Test that linter config files give partial score when no docs exist."""
        # Create ruff.toml but no CLAUDE.md
        ruff_toml = tmp_path / "ruff.toml"
        ruff_toml.write_text("[lint]\nselect = ['E', 'F']\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 30.0
        assert any("Linter configs found" in e for e in finding.evidence)

    def test_agents_md_works(self, tmp_path):
        """Test that AGENTS.md is checked for commands."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("- Lint: `pylint src/module.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 50.0

    def test_both_found_across_files(self, tmp_path):
        """Test that lint in one file and typecheck in another both count."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Lint: `ruff check path/to/file.py`\n")

        readme = tmp_path / "README.md"
        readme.write_text("Type check: `mypy src/module.py`\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        # 50 from context file lint + 30 from README typecheck = 80
        assert finding.score == 80.0

    def test_pyproject_ruff_config(self, tmp_path):
        """Test that [tool.ruff] in pyproject.toml is detected."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nselect = ['E', 'F']\n")

        repo = self._make_repo(tmp_path)
        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 30.0

    def test_remediation_present_on_fail(self, tmp_path):
        """Test that remediation is provided when assessment fails."""
        repo = self._make_repo(tmp_path)

        assessor = SingleFileVerificationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.remediation is not None
        assert len(finding.remediation.steps) > 0
