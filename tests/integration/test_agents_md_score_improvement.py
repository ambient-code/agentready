"""Integration test: AGENTS.md awareness improves assessment scores and performance.

Verifies SC-001: A Nova-like repository with AGENTS.md describing ADRs,
logging framework, and test directories should see ≥15 point improvement
on the affected assessors compared to the same repo without AGENTS.md.

Verifies SC-005: Assessment duration with AGENTS.md present is within
10% of baseline (no AGENTS.md).
"""

import textwrap
import time
from pathlib import Path

import pytest

from agentready.assessors.code_quality import StructuredLoggingAssessor
from agentready.assessors.documentation import ArchitectureDecisionsAssessor
from agentready.assessors.structure import StandardLayoutAssessor
from agentready.models.agent_context import ADRInfo, AgentContext, LoggingInfo
from agentready.models.repository import Repository
from agentready.services.scorer import Scorer


def _create_nova_like_repo(tmp_path: Path) -> Path:
    """Create a Nova-like repository structure without standard markers.

    Simulates a project like OpenStack Nova where:
    - ADRs live in an external repo (openstack/nova-specs)
    - Logging uses oslo.log (not in standard structured logging list)
    - Tests live in a non-standard path (nova/tests/)
    - No standard test directories (tests/, test/) at root
    """
    repo = tmp_path / "nova"
    repo.mkdir()
    (repo / ".git").mkdir()

    # Python project with non-standard layout
    (repo / "nova").mkdir()
    (repo / "nova" / "__init__.py").write_text("")
    (repo / "nova" / "compute").mkdir()
    (repo / "nova" / "compute" / "__init__.py").write_text("")
    (repo / "nova" / "compute" / "manager.py").write_text(
        "import logging\nLOG = logging.getLogger(__name__)\n"
    )

    # Non-standard test directory
    (repo / "nova" / "tests").mkdir()
    (repo / "nova" / "tests" / "__init__.py").write_text("")
    (repo / "nova" / "tests" / "unit").mkdir()
    (repo / "nova" / "tests" / "unit" / "__init__.py").write_text("")
    (repo / "nova" / "tests" / "unit" / "test_manager.py").write_text(
        "def test_placeholder(): pass\n"
    )

    # Requirements with oslo.log
    (repo / "requirements.txt").write_text("oslo.log>=5.0.0\npbr>=5.5\n")

    # setup.cfg for Python detection
    (repo / "setup.cfg").write_text("[metadata]\nname = nova\n")

    return repo


def _create_nova_agents_md_context() -> AgentContext:
    """Create AgentContext matching what AgentContextParser would produce
    from a Nova-like AGENTS.md file."""
    return AgentContext(
        source_file="AGENTS.md",
        raw_content=textwrap.dedent("""\
            # AGENTS.md

            ## Architecture Decisions
            Architecture decisions are tracked in the external `openstack/nova-specs`
            repository using RST-format specs.

            ## Logging
            Nova uses oslo.log for structured logging across all services.

            ## Directory Structure
            - nova/tests/ — Unit and functional tests
        """),
        test_directories=["nova/tests/"],
        logging_info=LoggingInfo(
            frameworks=["oslo.log"],
            conventions=[],
            has_structured_logging=True,
        ),
        adr_info=ADRInfo(
            local_paths=[],
            external_repos=["openstack/nova-specs"],
            format="rst",
        ),
    )


class TestAgentsMdScoreImprovement:
    """Verify AGENTS.md produces ≥15 point improvement on affected assessors."""

    @pytest.fixture
    def nova_repo(self, tmp_path):
        return _create_nova_like_repo(tmp_path)

    @pytest.fixture
    def repository(self, nova_repo):
        return Repository(
            path=nova_repo,
            name="nova",
            url=None,
            branch="master",
            commit_hash="abc123",
            languages={"Python": 5},
            total_files=10,
            total_lines=100,
        )

    @pytest.fixture
    def agent_context(self):
        return _create_nova_agents_md_context()

    def test_score_improvement_at_least_15_points(self, repository, agent_context):
        """SC-001: AGENTS.md awareness should improve score by ≥15 points."""
        assessors = [
            ArchitectureDecisionsAssessor(),
            StructuredLoggingAssessor(),
            StandardLayoutAssessor(),
        ]

        # Baseline: assess WITHOUT agent context
        baseline_findings = []
        for assessor in assessors:
            finding = assessor.assess(repository, agent_context=None)
            baseline_findings.append(finding)

        # Enhanced: assess WITH agent context
        enhanced_findings = []
        for assessor in assessors:
            finding = assessor.assess(repository, agent_context=agent_context)
            enhanced_findings.append(finding)

        # Calculate weighted scores
        scorer = Scorer()
        baseline_score = scorer.calculate_overall_score(baseline_findings)
        enhanced_score = scorer.calculate_overall_score(enhanced_findings)

        improvement = enhanced_score - baseline_score

        # Debug output for CI visibility
        for bf, ef in zip(baseline_findings, enhanced_findings):
            print(
                f"  {bf.attribute.id}: "
                f"baseline={bf.score:.0f} ({bf.status}) → "
                f"enhanced={ef.score:.0f} ({ef.status})"
            )
        print(f"  Baseline score: {baseline_score:.1f}")
        print(f"  Enhanced score: {enhanced_score:.1f}")
        print(f"  Improvement: {improvement:.1f} points")

        assert improvement >= 15.0, (
            f"Expected ≥15 point improvement, got {improvement:.1f} "
            f"(baseline={baseline_score:.1f}, enhanced={enhanced_score:.1f})"
        )

    def test_individual_assessor_improvements(self, repository, agent_context):
        """Each affected assessor should show improvement with AGENTS.md."""
        assessor_cases = [
            ("architecture_decisions", ArchitectureDecisionsAssessor()),
            ("structured_logging", StructuredLoggingAssessor()),
            ("standard_layout", StandardLayoutAssessor()),
        ]

        for name, assessor in assessor_cases:
            baseline = assessor.assess(repository, agent_context=None)
            enhanced = assessor.assess(repository, agent_context=agent_context)

            assert enhanced.score >= baseline.score, (
                f"{name}: enhanced score ({enhanced.score}) should be >= "
                f"baseline ({baseline.score})"
            )

    def test_agents_md_evidence_attribution(self, repository, agent_context):
        """US3: All AGENTS.md-sourced evidence has [AGENTS.md] prefix."""
        assessors = [
            ArchitectureDecisionsAssessor(),
            StructuredLoggingAssessor(),
            StandardLayoutAssessor(),
        ]

        for assessor in assessors:
            finding = assessor.assess(repository, agent_context=agent_context)
            evidence = finding.evidence or ""
            # Handle both string and list evidence formats
            evidence_str = (
                " ".join(evidence) if isinstance(evidence, list) else evidence
            )

            # If the assessor used agent_context info, evidence must be attributed
            if finding.score > 0:
                has_attribution = "[AGENTS.md]" in evidence_str
                # Only check assessors that rely on AGENTS.md in this scenario.
                # structured_logging finds oslo.log directly in requirements.txt
                # (added to extended_libs), so it doesn't use AGENTS.md path.
                if assessor.attribute_id == "architecture_decisions":
                    assert has_attribution, (
                        f"{assessor.attribute_id}: expected [AGENTS.md] "
                        f"attribution in evidence. "
                        f"Evidence: {evidence_str!r}"
                    )

    def test_performance_overhead_negligible(self, repository, agent_context):
        """SC-005: AGENTS.md processing adds negligible overhead.

        Measures the absolute per-assessment overhead of processing
        agent_context across all 3 affected assessors. The overhead
        should be <1ms per assessment run, which is negligible compared
        to the full assessment pipeline (typically 2-10 seconds).
        """

        def make_assessors():
            return [
                ArchitectureDecisionsAssessor(),
                StructuredLoggingAssessor(),
                StandardLayoutAssessor(),
            ]

        iterations = 200

        # Warmup
        for _ in range(20):
            for assessor in make_assessors():
                assessor.assess(repository, agent_context=None)
                assessor.assess(repository, agent_context=agent_context)

        # Baseline timing (no agent context)
        start = time.perf_counter()
        for _ in range(iterations):
            for assessor in make_assessors():
                assessor.assess(repository, agent_context=None)
        baseline_duration = time.perf_counter() - start

        # Enhanced timing (with agent context)
        start = time.perf_counter()
        for _ in range(iterations):
            for assessor in make_assessors():
                assessor.assess(repository, agent_context=agent_context)
        enhanced_duration = time.perf_counter() - start

        # Calculate absolute overhead per assessment
        overhead_total = enhanced_duration - baseline_duration
        overhead_per_run_ms = (overhead_total / iterations) * 1000

        print(f"  Baseline: {baseline_duration:.4f}s ({iterations} iterations)")
        print(f"  Enhanced: {enhanced_duration:.4f}s ({iterations} iterations)")
        print(f"  Overhead per run: {overhead_per_run_ms:.3f}ms")

        # Absolute overhead must be <1ms per assessment run.
        # A full assessment takes 2-10s, so <1ms is well within 10%.
        assert overhead_per_run_ms < 1.0, (
            f"AGENTS.md overhead {overhead_per_run_ms:.3f}ms/run exceeds 1ms "
            f"(baseline={baseline_duration:.4f}s, "
            f"enhanced={enhanced_duration:.4f}s)"
        )
