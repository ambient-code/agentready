"""Assessor factory for centralized assessor creation.

Phase 1 Task 3: Consolidated from duplicated create_all_assessors() functions
across CLI modules (main.py, assess_batch.py, demo.py).

v2.0.0: Updated with evidence-based rebalancing (ETH Zurich, Red Hat, Anthropic).
"""

from .base import BaseAssessor
from .code_quality import (
    CyclomaticComplexityAssessor,
    StructuredLoggingAssessor,
    TypeAnnotationsAssessor,
)
from .containers import ContainerSetupAssessor
from .dbt import (
    DbtDataTestsAssessor,
    DbtModelDocumentationAssessor,
    DbtProjectConfigAssessor,
    DbtProjectStructureAssessor,
)
from .documentation import (
    AgentInstructionsAssessor,
    ArchitectureDecisionsAssessor,
    InlineDocumentationAssessor,
    OpenAPISpecsAssessor,
    READMEAssessor,
)
from .patterns import (
    DesignIntentAssessor,
    PatternReferencesAssessor,
    ProgressiveDisclosureAssessor,
)
from .security import DependencySecurityAssessor, ThreatModelAssessor
from .structure import (
    ArchitecturalBoundaryAssessor,
    IssuePRTemplatesAssessor,
    OneCommandSetupAssessor,
    SeparationOfConcernsAssessor,
    StandardLayoutAssessor,
)
from .stub_assessors import LockFilesAssessor  # Backwards compatibility alias
from .stub_assessors import (
    ConventionalCommitsAssessor,
    DependencyPinningAssessor,
    FileSizeLimitsAssessor,
    GitignoreAssessor,
    create_stub_assessors,
)
from .testing import (
    CIQualityGatesAssessor,
    DeterministicEnforcementAssessor,
    TestExecutionAssessor,
)
from .verification import SingleFileVerificationAssessor

__all__ = ["create_all_assessors", "BaseAssessor", "LockFilesAssessor"]


def create_all_assessors() -> list[BaseAssessor]:
    """Create all assessors for assessment.

    Centralized factory function to eliminate duplication across CLI commands.
    Returns all implemented and stub assessors (27 attributes).

    Returns:
        List of all assessor instances
    """
    assessors = [
        # Tier 1 Essential — 58% total (9 attributes)
        TestExecutionAssessor(),  # 11%
        TypeAnnotationsAssessor(),  # 10%
        AgentInstructionsAssessor(),  # 7%
        CIQualityGatesAssessor(),  # 5%
        SingleFileVerificationAssessor(),  # 5%
        READMEAssessor(),  # 5%
        StandardLayoutAssessor(),  # 5%
        DependencyPinningAssessor(),  # 5%
        DependencySecurityAssessor(),  # 5%
        DbtProjectConfigAssessor(),  # dbt conditional
        DbtModelDocumentationAssessor(),  # dbt conditional
        # Tier 2 Critical — 27% total (9 attributes, 3% each)
        DeterministicEnforcementAssessor(),
        ConventionalCommitsAssessor(),
        GitignoreAssessor(),
        OneCommandSetupAssessor(),
        FileSizeLimitsAssessor(),
        SeparationOfConcernsAssessor(),
        InlineDocumentationAssessor(),
        PatternReferencesAssessor(),
        DesignIntentAssessor(),  # 3% (moved from T3)
        DbtDataTestsAssessor(),  # dbt conditional
        DbtProjectStructureAssessor(),  # dbt conditional
        # Tier 3 Important — 14% total (7 attributes)
        ArchitectureDecisionsAssessor(),  # 2%
        OpenAPISpecsAssessor(),  # 2%
        CyclomaticComplexityAssessor(),  # 2%
        StructuredLoggingAssessor(),  # 1%
        ProgressiveDisclosureAssessor(),  # 2% (moved from T4)
        ArchitecturalBoundaryAssessor(),  # 2% (ADR B.1)
        ThreatModelAssessor(),  # 2% (ADR B.2)
        # Tier 4 Advanced — 2% total (2 attributes, 1% each)
        IssuePRTemplatesAssessor(),
        ContainerSetupAssessor(),
    ]

    assessors.extend(create_stub_assessors())

    return assessors
