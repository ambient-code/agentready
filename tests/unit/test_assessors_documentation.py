"""Tests for documentation assessors."""

from agentready.assessors.documentation import (
    ArchitectureDecisionsAssessor,
    CLAUDEmdAssessor,
    ConciseDocumentationAssessor,
    READMEAssessor,
)
from agentready.models.agent_context import ADRInfo, AgentContext
from agentready.models.repository import Repository


class TestCLAUDEmdAssessor:
    """Test CLAUDEmdAssessor."""

    def test_passes_with_sufficient_claude_md(self, tmp_path):
        """Test that assessor passes with CLAUDE.md file >50 bytes."""
        # Create repository with CLAUDE.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# My Project\n\nThis is a comprehensive guide for AI assistants.\n"
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "CLAUDE.md found" in finding.evidence[0]

    def test_passes_with_claude_md_symlink(self, tmp_path):
        """Test that assessor passes when CLAUDE.md is a symlink to AGENTS.md."""
        # Create repository with AGENTS.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Agent Configuration\n\nThis project uses standardized agent configuration.\n"
        )

        # Create symlink CLAUDE.md -> AGENTS.md
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.symlink_to("AGENTS.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "CLAUDE.md found" in finding.evidence[0]
        assert "Symlink to" in finding.evidence[1]

    def test_passes_with_at_reference_to_agents_md(self, tmp_path):
        """Test that assessor passes when CLAUDE.md contains @ reference to AGENTS.md."""
        # Create repository with both files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Agent Configuration\n\nThis is the main configuration file.\n"
        )

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@AGENTS.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "@ reference to AGENTS.md" in finding.evidence[0]
        assert "Referenced file contains" in finding.evidence[1]

    def test_passes_with_at_reference_with_space(self, tmp_path):
        """Test that assessor passes when CLAUDE.md contains @ reference with space."""
        # Create repository with both files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Agent Configuration\n\nThis is the main configuration file.\n"
        )

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@ AGENTS.md")  # Note the space after @

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "@ reference to AGENTS.md" in finding.evidence[0]

    def test_passes_with_at_reference_in_subdirectory(self, tmp_path):
        """Test that assessor passes when @ reference points to file in subdirectory."""
        # Create repository with agent file in .claude/ directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        agents_file = claude_dir / "agents.md"
        agents_file.write_text(
            "# Agent Configuration\n\nThis is the main configuration file.\n"
        )

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@.claude/agents.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "@ reference to .claude/agents.md" in finding.evidence[0]

    def test_fails_with_invalid_at_reference(self, tmp_path):
        """Test that assessor fails when @ reference points to missing file."""
        # Create repository with CLAUDE.md but no AGENTS.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@AGENTS.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 25.0
        assert "invalid @ reference" in finding.measured_value
        assert "file is missing or too small" in finding.evidence[1]

    def test_fails_with_minimal_claude_md_no_reference(self, tmp_path):
        """Test that assessor fails when CLAUDE.md is too small and has no @ reference."""
        # Create repository with minimal CLAUDE.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test")  # Only 6 bytes

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 25.0
        assert "6 bytes" in finding.measured_value
        assert finding.remediation is not None

    def test_passes_with_agents_md_only(self, tmp_path):
        """Test that assessor passes with AGENTS.md when CLAUDE.md is missing."""
        # Create repository with only AGENTS.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Agent Configuration\n\nThis is comprehensive agent config.\n"
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 90.0  # Slightly lower for missing CLAUDE.md
        assert "AGENTS.md present" in finding.measured_value
        assert "CLAUDE.md not found" in finding.evidence[0]
        assert "AGENTS.md found" in finding.evidence[1]
        assert "broader tool support" in finding.evidence[2]

    def test_fails_with_no_files(self, tmp_path):
        """Test that assessor fails when neither CLAUDE.md nor AGENTS.md exist."""
        # Create repository without any config files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "missing" in finding.measured_value
        assert "CLAUDE.md not found" in finding.evidence[0]
        assert "AGENTS.md not found" in finding.evidence[1]

    def test_bonus_points_for_both_files(self, tmp_path):
        """Test that evidence mentions cross-tool compatibility when both files exist."""
        # Create repository with both CLAUDE.md and AGENTS.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# My Project\n\nThis is a comprehensive guide for AI assistants.\n"
        )

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Agent Configuration\n\nThis is also comprehensive.\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "AGENTS.md also present (cross-tool compatibility)" in finding.evidence

    def test_at_reference_extraction_various_formats(self):
        """Test _extract_at_reference method with various formats."""
        assessor = CLAUDEmdAssessor()

        # Test basic @ reference
        assert assessor._extract_at_reference("@AGENTS.md") == "AGENTS.md"

        # Test with space
        assert assessor._extract_at_reference("@ AGENTS.md") == "AGENTS.md"

        # Test with path
        assert (
            assessor._extract_at_reference("@.claude/agents.md") == ".claude/agents.md"
        )

        # Test embedded in text
        assert (
            assessor._extract_at_reference("See @AGENTS.md for details") == "AGENTS.md"
        )

        # Test no reference
        assert assessor._extract_at_reference("No reference here") is None

        # Test case insensitive
        assert assessor._extract_at_reference("@agents.MD") == "agents.MD"

        # Test path traversal rejection
        assert assessor._extract_at_reference("@../etc/passwd.md") is None
        assert assessor._extract_at_reference("@../../secrets.md") is None
        assert assessor._extract_at_reference("@./../config.md") is None

        # Test absolute path rejection
        assert assessor._extract_at_reference("@/etc/passwd.md") is None
        assert assessor._extract_at_reference("@/root/secrets.md") is None

    def test_at_reference_with_at_reference_and_agents_md(self, tmp_path):
        """Test cross-tool compatibility bonus when using @ reference with AGENTS.md."""
        # Create repository with @ reference to AGENTS.md
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Agent Configuration\n\nThis is comprehensive agent config.\n"
        )

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@AGENTS.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        # Should detect AGENTS.md exists (the file being referenced)
        assert any("cross-tool compatibility" in ev for ev in finding.evidence)

    def test_rejects_path_traversal_attempts(self, tmp_path):
        """Test that @ references with path traversal are rejected for security."""
        # Create repository with CLAUDE.md containing path traversal
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@../../etc/passwd.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        # Should fail with score 25 (minimal CLAUDE.md, no valid reference)
        assert finding.status == "fail"
        assert finding.score == 25.0
        assert finding.remediation is not None

    def test_rejects_absolute_path_references(self, tmp_path):
        """Test that @ references with absolute paths are rejected for security."""
        # Create repository with CLAUDE.md containing absolute path
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@/etc/passwd.md")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = CLAUDEmdAssessor()
        finding = assessor.assess(repo)

        # Should fail with score 25 (minimal CLAUDE.md, no valid reference)
        assert finding.status == "fail"
        assert finding.score == 25.0
        assert finding.remediation is not None


class TestArchitectureDecisionsAssessorWithAgentContext:
    """Test ArchitectureDecisionsAssessor with AgentContext from AGENTS.md."""

    def _make_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        return Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

    def test_external_adr_repo_gets_60_percent_cap(self, tmp_path):
        """AGENTS.md describes ADRs in external repo -> 60% partial credit."""
        repo = self._make_repo(tmp_path)
        agent_context = AgentContext(
            source_file="AGENTS.md",
            raw_content="ADRs in nova-specs",
            adr_info=ADRInfo(
                external_repos=["openstack/nova-specs"],
            ),
        )

        assessor = ArchitectureDecisionsAssessor()
        finding = assessor.assess(repo, agent_context=agent_context)

        assert finding.status == "pass"
        assert finding.score == 60.0
        assert any("[AGENTS.md]" in e for e in finding.evidence)
        assert any("nova-specs" in e for e in finding.evidence)

    def test_verified_local_adr_path_gets_full_credit(self, tmp_path):
        """AGENTS.md describes local ADR path that exists -> full credit."""
        repo = self._make_repo(tmp_path)
        # Use a non-standard path so the normal scan doesn't find it first
        adr_dir = tmp_path / "specs" / "decisions"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-use-adrs.md").write_text("# Use ADRs\n## Status\nAccepted")

        agent_context = AgentContext(
            source_file="AGENTS.md",
            raw_content="ADRs in specs/decisions/",
            adr_info=ADRInfo(
                local_paths=["specs/decisions"],
            ),
        )

        assessor = ArchitectureDecisionsAssessor()
        finding = assessor.assess(repo, agent_context=agent_context)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("[AGENTS.md]" in e and "verified" in e for e in finding.evidence)

    def test_no_agent_context_existing_behavior_unchanged(self, tmp_path):
        """No AgentContext -> existing behavior (fail with 0)."""
        repo = self._make_repo(tmp_path)

        assessor = ArchitectureDecisionsAssessor()
        finding = assessor.assess(repo, agent_context=None)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_local_adr_path_not_found_on_filesystem(self, tmp_path):
        """AGENTS.md describes local ADR path that doesn't exist -> low score."""
        repo = self._make_repo(tmp_path)
        agent_context = AgentContext(
            source_file="AGENTS.md",
            raw_content="ADRs in docs/adr/",
            adr_info=ADRInfo(
                local_paths=["docs/adr"],
            ),
        )

        assessor = ArchitectureDecisionsAssessor()
        finding = assessor.assess(repo, agent_context=agent_context)

        assert finding.status == "fail"
        assert finding.score == 30.0
        assert any("not found on filesystem" in e for e in finding.evidence)


class TestREADMEAssessorAlternativeFormats:
    """Test READMEAssessor with README.rst and README.txt formats."""

    def _make_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        return Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

    def test_readme_rst_scored_like_md(self, tmp_path):
        """README.rst only -> scored same as .md."""
        repo = self._make_repo(tmp_path)
        (tmp_path / "README.rst").write_text(
            "Project\n=======\n\nInstallation\n"
            "------------\n\npip install foo\n\n"
            "Usage\n-----\n\nfoo --help\n\n"
            "Development\n-----------\n\npytest\n"
        )

        assessor = READMEAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("rst" in e.lower() for e in finding.evidence)

    def test_readme_txt_scored(self, tmp_path):
        """README.txt only -> scored."""
        repo = self._make_repo(tmp_path)
        (tmp_path / "README.txt").write_text(
            "Project\n\nInstallation: pip install foo\n"
            "Usage: foo --help\nDevelopment: pytest\n"
        )

        assessor = READMEAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_md_preferred_over_rst(self, tmp_path):
        """Both .md and .rst -> prefer .md, no rst note in evidence."""
        repo = self._make_repo(tmp_path)
        (tmp_path / "README.md").write_text(
            "# Project\n\n## Installation\npip install\n\n"
            "## Usage\nfoo --help\n\n## Development\npytest\n"
        )
        (tmp_path / "README.rst").write_text("RST content")

        assessor = READMEAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        # Should NOT mention rst format since .md was used
        assert not any("rst" in e.lower() for e in finding.evidence)

    def test_no_readme_at_all_fails(self, tmp_path):
        """No README at all -> fail (existing behavior)."""
        repo = self._make_repo(tmp_path)

        assessor = READMEAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0


class TestConciseDocumentationAssessorRSTFallback:
    """Test ConciseDocumentationAssessor with README.rst fallback."""

    def _make_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        return Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

    def test_readme_rst_conciseness_scored(self, tmp_path):
        """README.rst only -> conciseness scored."""
        repo = self._make_repo(tmp_path)
        (tmp_path / "README.rst").write_text(
            "Project\n=======\n\n- Feature one\n- Feature two\n- Feature three\n"
        )

        assessor = ConciseDocumentationAssessor()
        finding = assessor.assess(repo)

        # Should not be not_applicable since README.rst exists
        assert finding.status in ("pass", "fail")

    def test_no_readme_not_applicable(self, tmp_path):
        """No README -> not_applicable (existing behavior)."""
        repo = self._make_repo(tmp_path)

        assessor = ConciseDocumentationAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"
