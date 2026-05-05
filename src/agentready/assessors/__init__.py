"""Assessor factory for centralized assessor creation.

Phase 1 Task 3: Consolidated from duplicated create_all_assessors() functions
across CLI modules (main.py, assess_batch.py, demo.py).

v2.0.0: Updated with evidence-based rebalancing (ETH Zurich, Red Hat, Anthropic).
"""

from .base import BaseAssessor
from .code_quality import (
    CodeSmellsAssessor,
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
    ArchitectureDecisionsAssessor,
    CLAUDEmdAssessor,
    ConciseDocumentationAssessor,
    InlineDocumentationAssessor,
    OpenAPISpecsAssessor,
    READMEAssessor,
)
from .patterns import (
    DesignIntentAssessor,
    PatternReferencesAssessor,
    ProgressiveDisclosureAssessor,
)
from .security import DependencySecurityAssessor
from .structure import (
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
    BranchProtectionAssessor,
    CIQualityGatesAssessor,
    DeterministicEnforcementAssessor,
    TestExecutionAssessor,
)
from .verification import SingleFileVerificationAssessor

__all__ = ["create_all_assessors", "BaseAssessor", "LockFilesAssessor"]


def create_all_assessors() -> list[BaseAssessor]:
    """Create all assessors for assessment.

    Centralized factory function to eliminate duplication across CLI commands.
    Returns all implemented and stub assessors.

    v2.0.0 changes:
    - TestCoverageAssessor → TestExecutionAssessor (Tier 1, 10%)
    - PreCommitHooksAssessor → DeterministicEnforcementAssessor (Tier 2, 3%)
    - CICDPipelineVisibilityAssessor → CIQualityGatesAssessor (Tier 1, 5%)
    - Added: SingleFileVerificationAssessor (Tier 1, 5%)
    - Added: PatternReferencesAssessor (Tier 2, 3%)
    - Added: DesignIntentAssessor (Tier 3, 2%)
    - Added: ProgressiveDisclosureAssessor (Tier 4, 1%)

    Returns:
        List of all assessor instances
    """
    assessors = [
        # Tier 1 Essential — 55% total
        TestExecutionAssessor(),  # 10% — #1 priority (was TestCoverageAssessor at T2/3%)
        TypeAnnotationsAssessor(),  # 8%
        CLAUDEmdAssessor(),  # 7% (was 10%)
        CIQualityGatesAssessor(),  # 5% — NEW (was CICDPipelineVisibilityAssessor at T3)
        SingleFileVerificationAssessor(),  # 5% — NEW
        READMEAssessor(),  # 5% (was 10%)
        StandardLayoutAssessor(),  # 5% (was 10%)
        DependencyPinningAssessor(),  # 5% (was 10%)
        DependencySecurityAssessor(),  # 5%
        DbtProjectConfigAssessor(),  # dbt conditional
        DbtModelDocumentationAssessor(),  # dbt conditional
        # Tier 2 Critical — 27% total (3% each)
        DeterministicEnforcementAssessor(),  # Was PreCommitHooksAssessor
        ConventionalCommitsAssessor(),
        GitignoreAssessor(),
        OneCommandSetupAssessor(),
        FileSizeLimitsAssessor(),
        SeparationOfConcernsAssessor(),
        ConciseDocumentationAssessor(),
        InlineDocumentationAssessor(),
        PatternReferencesAssessor(),  # NEW
        DbtDataTestsAssessor(),  # dbt conditional
        DbtProjectStructureAssessor(),  # dbt conditional
        # Tier 3 Important — 14% total
        DesignIntentAssessor(),  # NEW (2%)
        CyclomaticComplexityAssessor(),  # 3%
        ArchitectureDecisionsAssessor(),  # 3%
        IssuePRTemplatesAssessor(),  # 3%
        StructuredLoggingAssessor(),  # 3%
        OpenAPISpecsAssessor(),  # 3%
        # Tier 4 Advanced — 4% total (1% each)
        BranchProtectionAssessor(),
        CodeSmellsAssessor(),
        ContainerSetupAssessor(),
        ProgressiveDisclosureAssessor(),  # NEW
    ]

    assessors.extend(create_stub_assessors())

    return assessors
