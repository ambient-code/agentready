"""Tests for documentation assessors."""

from agentready.assessors.documentation import AgentInstructionsAssessor
from agentready.models.repository import Repository


class TestAgentInstructionsAssessor:
    """Test AgentInstructionsAssessor."""

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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0  # AGENTS.md is the cross-tool standard
        assert "AGENTS.md present" in finding.measured_value
        assert "CLAUDE.md not found" in finding.evidence[0]
        assert "AGENTS.md found" in finding.evidence[1]
        assert "cross-tool standard" in finding.evidence[2]

    def test_passes_with_dotclaude_claude_md(self, tmp_path):
        """Test that .claude/CLAUDE.md is detected when root CLAUDE.md is absent."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        dotclaude_dir = tmp_path / ".claude"
        dotclaude_dir.mkdir()
        (dotclaude_dir / "CLAUDE.md").write_text(
            "# Project Config\n\nThis project uses pytest for testing.\n"
            "Run `pytest` to execute all tests.\n"
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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert ".claude/CLAUDE.md" in finding.measured_value
        assert any(".claude/CLAUDE.md" in e for e in finding.evidence)

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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "AGENTS.md also present (cross-tool compatibility)" in finding.evidence

    def test_at_reference_extraction_various_formats(self):
        """Test _extract_at_reference method with various formats."""
        assessor = AgentInstructionsAssessor()

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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        # Should fail with score 25 (minimal CLAUDE.md, no valid reference)
        assert finding.status == "fail"
        assert finding.score == 25.0
        assert finding.remediation is not None

    # --- Length validation tests (ADR A.1) ---

    def test_length_full_credit_under_150_lines(self, tmp_path):
        """Test full length credit for context file <=150 lines."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        lines = ["# Project Config"] + [f"Line {i}" for i in range(100)]
        (tmp_path / "CLAUDE.md").write_text("\n".join(lines))

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("good: <=150" in e for e in finding.evidence)

    def test_length_partial_credit_150_to_300_lines(self, tmp_path):
        """Test partial length credit for context file 151-300 lines."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        lines = ["# Project Config"] + [f"Line {i}" for i in range(200)]
        (tmp_path / "CLAUDE.md").write_text("\n".join(lines))

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 85.0
        assert any("partial credit: <=300" in e for e in finding.evidence)

    def test_length_no_credit_over_300_lines(self, tmp_path):
        """Test no length credit for context file >300 lines."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        lines = ["# Project Config"] + [f"Line {i}" for i in range(400)]
        (tmp_path / "CLAUDE.md").write_text("\n".join(lines))

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 70.0
        assert any("exceeds 300 line limit" in e for e in finding.evidence)

    def test_length_check_follows_symlink(self, tmp_path):
        """Test that length check counts lines of the resolved symlink target."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        lines = ["# Agent Config"] + [f"Line {i}" for i in range(250)]
        (tmp_path / "AGENTS.md").write_text("\n".join(lines))
        (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 85.0
        assert any("partial credit" in e for e in finding.evidence)

    def test_length_check_follows_at_reference(self, tmp_path):
        """Test that length check counts lines of the @ referenced file."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        lines = ["# Agent Config"] + [f"Line {i}" for i in range(350)]
        (tmp_path / "AGENTS.md").write_text("\n".join(lines))
        (tmp_path / "CLAUDE.md").write_text("@AGENTS.md")

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 70.0
        assert any("exceeds 300 line limit" in e for e in finding.evidence)

    # --- Agent access documentation tests (ADR A.9) ---

    def test_agent_access_heading_in_evidence(self, tmp_path):
        """Test that agent access heading is detected as evidence."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        content = (
            "# Project\n\n## Agent Access\n\nUse `gh` CLI for GitHub operations.\n"
        )
        (tmp_path / "CLAUDE.md").write_text(content)

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("Agent access documentation found" in e for e in finding.evidence)

    def test_agent_access_keywords_in_evidence(self, tmp_path):
        """Test that platform + tool/auth keyword co-occurrence is detected."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        content = (
            "# Project\n\nHosted on GitHub. Use `gh ` CLI with token authentication.\n"
        )
        (tmp_path / "CLAUDE.md").write_text(content)

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert any("Agent access documentation found" in e for e in finding.evidence)

    def test_no_agent_access_no_penalty(self, tmp_path):
        """Test that missing agent access documentation does not affect score."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        content = "# Project\n\nThis is a Python project using pytest for tests.\n"
        (tmp_path / "CLAUDE.md").write_text(content)

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

        assessor = AgentInstructionsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert not any("Agent access" in e for e in finding.evidence)


class TestArchitectureDecisionsAssessorCentralSource:
    """Test that ArchitectureDecisionsAssessor gives credit for central ADR repos."""

    def _make_repo(self, tmp_path, config=None):
        """Create a minimal Repository at tmp_path with an optional Config."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / ".git").mkdir(exist_ok=True)
        from agentready.models.repository import Repository

        return Repository(
            path=tmp_path,
            name="build-service",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=5,
            total_lines=50,
            config=config,
        )

    def test_passes_when_central_adr_source_configured(self, tmp_path):
        """Return pass when central ADR repo exists with enough well-formed ADRs.

        Scoring mirrors local ADRs: 40 (dir) + count (8/ADR, max 40) + template (max 20).
        Three ADRs with all four template sections → 40 + 24 + 20 = 84 ≥ 75 → pass.
        """
        from agentready.assessors.documentation import ArchitectureDecisionsAssessor
        from agentready.models.config import Config

        central = tmp_path / "central" / "ADR"
        central.mkdir(parents=True)
        # Three ADRs each containing all required template sections (status/context/decision/consequences)
        full_template = "# Status\nAccepted\n# Context\nWhy.\n# Decision\nWe will.\n# Consequences\nBecause.\n"
        for i in range(1, 4):
            (central / f"000{i}.md").write_text(
                f'---\nstatus: Accepted\napplies_to: "*"\n---\n{full_template}'
            )

        config = Config(adr_source={"repo": str(tmp_path / "central"), "path": "ADR"})
        repo = self._make_repo(tmp_path / "repo", config=config)

        finding = ArchitectureDecisionsAssessor().assess(repo)
        assert finding.status == "pass"
        assert finding.score >= 75.0
        assert any("central" in e.lower() for e in finding.evidence)

    def test_skips_when_central_path_missing(self, tmp_path):
        """Return skipped (not fail) when the configured central repo path does not exist.

        When adr_source is configured but unreachable, the assessor degrades
        gracefully to a skipped finding rather than falling through to a FAIL.
        """
        from agentready.assessors.documentation import ArchitectureDecisionsAssessor
        from agentready.models.config import Config

        config = Config(
            adr_source={"repo": str(tmp_path / "nonexistent"), "path": "ADR"}
        )
        repo = self._make_repo(tmp_path / "repo", config=config)

        finding = ArchitectureDecisionsAssessor().assess(repo)
        assert finding.status == "skipped"
        assert (
            "not found" in finding.evidence[0].lower()
            or "nonexistent" in finding.evidence[0]
        )

    def test_falls_through_when_no_adrs_match_repo(self, tmp_path):
        """Fall through to fail when central ADRs exist but none match the repo name."""
        from agentready.assessors.documentation import ArchitectureDecisionsAssessor
        from agentready.models.config import Config

        central = tmp_path / "central" / "ADR"
        central.mkdir(parents=True)
        # ADR only applies to a different service, not the assessed repo
        (central / "0001.md").write_text(
            "---\nstatus: Accepted\napplies_to: other-service\n---\n# ADR\n"
        )

        config = Config(adr_source={"repo": str(tmp_path / "central"), "path": "ADR"})
        repo = self._make_repo(tmp_path / "repo", config=config)

        finding = ArchitectureDecisionsAssessor().assess(repo)
        # No ADRs match the repo name → falls through to normal failure path
        assert finding.status == "fail"

    def test_skips_when_adr_subdir_missing(self, tmp_path):
        """Return skipped (not fail) when the repo root exists but ADR subdir is absent.

        Configured-but-broken central repos degrade gracefully to skipped,
        not to a FAIL that would penalise the score.
        """
        from agentready.assessors.documentation import ArchitectureDecisionsAssessor
        from agentready.models.config import Config

        # local_path exists but the ADR subdir does not
        central = tmp_path / "central"
        central.mkdir(parents=True)

        config = Config(adr_source={"repo": str(central), "path": "ADR"})
        repo = self._make_repo(tmp_path / "repo", config=config)

        finding = ArchitectureDecisionsAssessor().assess(repo)
        assert finding.status == "skipped"
        assert "subdir" in finding.evidence[0].lower() or "ADR" in finding.evidence[0]

    def test_no_config_still_fails_without_local_adr(self, tmp_path):
        """Fail with score 0 when no config is set and no local ADR directory exists."""
        from agentready.assessors.documentation import ArchitectureDecisionsAssessor

        repo = self._make_repo(tmp_path)
        finding = ArchitectureDecisionsAssessor().assess(repo)
        assert finding.status == "fail"
        assert finding.score == 0.0
