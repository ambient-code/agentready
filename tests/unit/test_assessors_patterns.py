"""Tests for pattern and knowledge assessors."""

from agentready.assessors.patterns import (
    DesignIntentAssessor,
    PatternReferencesAssessor,
    ProgressiveDisclosureAssessor,
)
from agentready.models.repository import Repository


def _make_repo(tmp_path, total_lines=1000, **kwargs):
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
        total_files=kwargs.get("total_files", 10),
        total_lines=total_lines,
    )


class TestPatternReferencesAssessor:
    """Test PatternReferencesAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = PatternReferencesAssessor()
        assert assessor.attribute_id == "pattern_references"

    def test_tier(self):
        """Test tier is Critical (2)."""
        assessor = PatternReferencesAssessor()
        assert assessor.tier == 2

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = PatternReferencesAssessor()
        assert assessor.attribute.default_weight == 0.03

    def test_fails_with_no_patterns(self, tmp_path):
        """Test that assessor fails when no patterns exist."""
        repo = _make_repo(tmp_path)

        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_passes_with_skills_directory(self, tmp_path):
        """Test that .claude/skills/ with SKILL.md files passes."""
        skills_dir = tmp_path / ".claude" / "skills" / "add-endpoint"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "# Add API Endpoint\nFollow pattern in src/api/users.ts\n"
        )

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 60.0
        assert any(".claude/skills/" in e for e in finding.evidence)

    def test_passes_with_pattern_refs_in_claude_md(self, tmp_path):
        """Test that pattern references in CLAUDE.md pass."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Patterns\n"
            "- New endpoint: follow the pattern in `src/api/handlers/users.ts`\n"
        )

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 40.0

    def test_passes_with_reference_implementation_keyword(self, tmp_path):
        """Test that 'reference implementation' keyword matches."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "See the reference implementation in `src/adapters/postgres.py`.\n"
        )

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 40.0

    def test_examples_directory_adds_score(self, tmp_path):
        """Test that examples/ directory adds to score."""
        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "basic_usage.py").write_text("# Basic usage example\n")

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        # examples/ alone gives 20 points, which is below pass threshold (40)
        assert finding.score == 20.0

    def test_skills_plus_examples_caps_at_100(self, tmp_path):
        """Test that combined score caps at 100."""
        # Skills dir
        skills_dir = tmp_path / ".claude" / "skills" / "add-endpoint"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Pattern\n")

        # Examples dir
        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "example.py").write_text("# Example\n")

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 80.0  # 60 + 20

    def test_remediation_on_fail(self, tmp_path):
        """Test that remediation is provided on failure."""
        repo = _make_repo(tmp_path)

        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.remediation is not None
        assert len(finding.remediation.steps) > 0

    def test_agents_md_keyword_match(self, tmp_path):
        """Test that AGENTS.md is also checked for patterns."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "Use `src/api/users.ts` as a template for new endpoints.\n"
        )

        repo = _make_repo(tmp_path)
        assessor = PatternReferencesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 40.0


class TestDesignIntentAssessor:
    """Test DesignIntentAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = DesignIntentAssessor()
        assert assessor.attribute_id == "design_intent"

    def test_tier(self):
        """Test tier is Important (3)."""
        assessor = DesignIntentAssessor()
        assert assessor.tier == 3

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = DesignIntentAssessor()
        assert assessor.attribute.default_weight == 0.02

    def test_fails_with_no_design_docs(self, tmp_path):
        """Test that assessor fails when no design docs exist."""
        repo = _make_repo(tmp_path)

        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_passes_with_design_directory(self, tmp_path):
        """Test that docs/design/ with markdown files passes."""
        design_dir = tmp_path / "docs" / "design"
        design_dir.mkdir(parents=True)
        (design_dir / "event-system.md").write_text(
            "# Event System Design\n## Invariants\n- Append-only log\n"
        )

        repo = _make_repo(tmp_path)
        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 50.0

    def test_passes_with_architecture_directory(self, tmp_path):
        """Test that docs/architecture/ with intent language passes."""
        arch_dir = tmp_path / "docs" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "overview.md").write_text(
            "# Architecture\n## Invariants\n- Event log is append-only\n"
        )

        repo = _make_repo(tmp_path)
        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 50.0

    def test_stub_design_docs_score_lower(self, tmp_path):
        """Test that design docs without intent language get lower score."""
        arch_dir = tmp_path / "docs" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "overview.md").write_text("# Architecture\nTODO: fill in\n")

        repo = _make_repo(tmp_path)
        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        # Structural-only credit (15 pts), below pass threshold (50)
        assert finding.status == "fail"
        assert finding.score == 15.0
        assert any("no intent language" in e.lower() for e in finding.evidence)

    def test_intent_keywords_in_claude_md(self, tmp_path):
        """Test that design intent keywords in CLAUDE.md add score."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Design Notes\n"
            "## Invariants\n"
            "- The event log is append-only; never mutate or delete entries\n"
            "- This invariant must hold across all write paths\n"
        )

        repo = _make_repo(tmp_path)
        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30.0

    def test_design_dir_plus_keywords_scores_higher(self, tmp_path):
        """Test that design dir with intent + keywords in context file gives higher score."""
        design_dir = tmp_path / "docs" / "design"
        design_dir.mkdir(parents=True)
        (design_dir / "overview.md").write_text(
            "# Design Overview\n## Invariants\n- Data is append-only\n"
        )

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("This assumes that the auth middleware is configured.\n")

        repo = _make_repo(tmp_path)
        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 80.0  # 50 from dir with intent + 30 from keyword

    def test_remediation_on_fail(self, tmp_path):
        """Test that remediation is provided on failure."""
        repo = _make_repo(tmp_path)

        assessor = DesignIntentAssessor()
        finding = assessor.assess(repo)

        assert finding.remediation is not None
        assert "docs/design" in finding.remediation.commands[0]


class TestProgressiveDisclosureAssessor:
    """Test ProgressiveDisclosureAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = ProgressiveDisclosureAssessor()
        assert assessor.attribute_id == "progressive_disclosure"

    def test_tier(self):
        """Test tier is Advanced (4)."""
        assessor = ProgressiveDisclosureAssessor()
        assert assessor.tier == 4

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = ProgressiveDisclosureAssessor()
        assert assessor.attribute.default_weight == 0.01

    def test_not_applicable_for_small_repos(self, tmp_path):
        """Test that small repos get not_applicable status."""
        repo = _make_repo(tmp_path, total_lines=1000)

        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_threshold_is_50k(self):
        """Test that LOC threshold is 50K as documented."""
        assessor = ProgressiveDisclosureAssessor()
        assert assessor.LOC_THRESHOLD == 50000

    def test_applicable_for_large_repos(self, tmp_path):
        """Test that repos over 50K lines are assessed."""
        repo = _make_repo(tmp_path, total_lines=60000)

        assessor = ProgressiveDisclosureAssessor()
        assert assessor.is_applicable(repo)

    def test_fails_for_large_repo_without_disclosure(self, tmp_path):
        """Test that large repo without progressive disclosure fails."""
        repo = _make_repo(tmp_path, total_lines=60000)

        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_passes_with_path_scoped_rules(self, tmp_path):
        """Test that .claude/rules/ with path-scoped frontmatter passes."""
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api-module.md").write_text(
            '---\npaths:\n  - "src/api/**/*.ts"\n---\n\n# API Rules\n'
        )

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 50.0
        assert any("path-scoped" in e for e in finding.evidence)

    def test_rules_without_frontmatter_lower_score(self, tmp_path):
        """Test that rules without path frontmatter give lower score."""
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general.md").write_text("# General Rules\n- Use TypeScript\n")

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 20.0  # No path-scoped frontmatter

    def test_skills_directory_adds_score(self, tmp_path):
        """Test that .claude/skills/ directory adds score."""
        skills_dir = tmp_path / ".claude" / "skills" / "add-endpoint"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Add API Endpoint\n")

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 30.0

    def test_compact_root_context_adds_score(self, tmp_path):
        """Test that a short root CLAUDE.md adds bonus score."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Project\n## Commands\n- test: pytest\n")

        # Also need some mechanism to get above threshold
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths:\n  - "src/api/**"\n---\n# API Rules\n'
        )

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert any("<150" in e for e in finding.evidence)

    def test_large_root_context_noted(self, tmp_path):
        """Test that a large root context file is noted in evidence."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("\n".join([f"Line {i}" for i in range(400)]))

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert any("consider splitting" in e for e in finding.evidence)

    def test_remediation_on_fail(self, tmp_path):
        """Test that remediation is provided on failure."""
        repo = _make_repo(tmp_path, total_lines=60000)

        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.remediation is not None
        assert len(finding.remediation.steps) > 0

    def test_combined_mechanisms_high_score(self, tmp_path):
        """Test that multiple disclosure mechanisms give high score."""
        # Path-scoped rules
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text('---\npaths:\n  - "src/api/**"\n---\n# API\n')

        # Skills
        skills_dir = tmp_path / ".claude" / "skills" / "endpoint"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Add Endpoint\n")

        # Compact root context
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Project\n## Commands\n- test: pytest\n")

        repo = _make_repo(tmp_path, total_lines=60000)
        assessor = ProgressiveDisclosureAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 90.0
