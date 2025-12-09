"""Scanner service orchestrating the assessment workflow."""

import sys
import time
from datetime import datetime
from pathlib import Path

import git

from ..models.assessment import Assessment
from ..models.config import Config
from ..models.finding import Finding
from ..models.metadata import AssessmentMetadata
from ..models.repository import Repository
from .language_detector import LanguageDetector
from .research_loader import ResearchLoader
from .scorer import Scorer


class MissingToolError(Exception):
    """Raised when a required tool is missing."""

    def __init__(self, tool_name: str, install_command: str = ""):
        self.tool_name = tool_name
        self.install_command = install_command
        super().__init__(f"Missing tool: {tool_name}")


class Scanner:
    """Orchestrates assessment workflow with try-assess-skip error handling.

    Responsibilities:
    - Validate repository structure
    - Detect languages and metadata
    - Execute assessors with graceful degradation
    - Calculate scores and certification level
    - Track progress
    """

    def __init__(self, repository_path: Path, config: Config | None = None):
        """Initialize scanner for repository.

        Args:
            repository_path: Path to git repository root
            config: User configuration (optional)

        Raises:
            ValueError: If repository is invalid
        """
        self.repository_path = repository_path
        self.config = config
        self.scorer = Scorer()

        # Validate repository
        self._validate_repository()

    def _validate_repository(self):
        """Validate repository has .git directory per FR-017.

        Raises:
            ValueError: If not a valid git repository
        """
        if not self.repository_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")

        if not (self.repository_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repository_path}")

    def scan(
        self,
        assessors: list,
        verbose: bool = False,
        version: str = "unknown",
        command: str | None = None,
    ) -> Assessment:
        """Execute full assessment workflow.

        Args:
            assessors: List of assessor instances to run
            verbose: Enable detailed progress logging
            version: AgentReady version string
            command: CLI command executed (reconstructed from sys.argv if None)

        Returns:
            Complete Assessment with findings and scores

        Flow:
        1. Build Repository model (detect languages, metadata)
        2. For each assessor: try assess → catch errors → create finding
        3. Calculate overall score with weighted average
        4. Determine certification level
        5. Return Assessment
        """
        start_time = time.time()
        timestamp = datetime.now()

        if verbose:
            print(f"Scanning repository: {self.repository_path.name}")

        # Build Repository model
        repository = self._build_repository_model(verbose)

        if verbose:
            print(f"Languages detected: {', '.join(repository.languages.keys())}")
            print(f"\nEvaluating {len(assessors)} attributes...")

        # Execute assessors with graceful degradation
        findings = []
        for assessor in assessors:
            finding = self._execute_assessor(assessor, repository, verbose)
            findings.append(finding)

        # Calculate scores
        overall_score = self.scorer.calculate_overall_score(findings, self.config)
        certification_level = self.scorer.determine_certification_level(overall_score)

        # Count assessed vs skipped
        assessed, skipped = self.scorer.count_assessed_attributes(findings)

        duration = time.time() - start_time

        # Create metadata
        if command is None:
            # Reconstruct command from sys.argv
            command = " ".join(sys.argv)

        # Load research version
        research_loader = ResearchLoader()
        try:
            _, research_metadata, _, _, _ = research_loader.load_and_validate()
            research_version = research_metadata.version
        except Exception:
            research_version = "unknown"

        metadata = AssessmentMetadata.create(
            version=version,
            research_version=research_version,
            timestamp=timestamp,
            command=command,
        )

        if verbose:
            print(f"\nAssessment complete in {duration:.1f}s")
            print(f"Overall Score: {overall_score}/100 ({certification_level})")
            print(
                f"Attributes Assessed: {assessed}/{len(findings)} ({skipped} skipped)"
            )

        return Assessment(
            repository=repository,
            timestamp=timestamp,
            overall_score=overall_score,
            certification_level=certification_level,
            attributes_assessed=assessed,
            attributes_not_assessed=skipped,
            attributes_total=len(findings),
            findings=findings,
            config=self.config,
            duration_seconds=round(duration, 1),
            metadata=metadata,
        )

    def _build_repository_model(self, verbose: bool = False) -> Repository:
        """Build Repository model with metadata and language detection.

        Args:
            verbose: Enable progress logging

        Returns:
            Repository model
        """
        if verbose:
            print("Detecting languages and repository metadata...")

        # Git metadata
        repo = git.Repo(self.repository_path)
        name = self.repository_path.name

        # Handle detached HEAD state (e.g., in CI/CD)
        try:
            branch = repo.active_branch.name
        except TypeError:
            # Detached HEAD - use commit hash or "HEAD"
            branch = "HEAD"

        commit_hash = repo.head.commit.hexsha

        # Get remote URL (if available)
        try:
            url = repo.remotes.origin.url if repo.remotes else None
        except Exception:
            url = None

        # Language detection
        detector = LanguageDetector(self.repository_path)
        languages = detector.detect_languages()
        total_files = detector.count_total_files()
        total_lines = detector.count_total_lines()

        return Repository(
            path=self.repository_path,
            name=name,
            url=url,
            branch=branch,
            commit_hash=commit_hash,
            languages=languages,
            total_files=total_files,
            total_lines=total_lines,
            config=self.config,
        )

    def _execute_assessor(
        self, assessor, repository: Repository, verbose: bool = False
    ) -> Finding:
        """Execute single assessor with error handling.

        Implements try-assess-skip pattern per research.md:
        - Check if applicable
        - Try to assess
        - Catch errors → return Finding.skipped() or Finding.error()

        Args:
            assessor: Assessor instance
            repository: Repository model
            verbose: Enable progress logging

        Returns:
            Finding (pass/fail/skipped/error/not_applicable)
        """
        attr_id = assessor.attribute_id

        if verbose:
            print(f"  [{attr_id}] ", end="", flush=True)

        # Check if applicable (language-specific checks)
        try:
            if not assessor.is_applicable(repository):
                if verbose:
                    print("not applicable")
                return Finding.not_applicable(
                    assessor.attribute,
                    reason=f"Not applicable to {list(repository.languages.keys())}",
                )
        except Exception as e:
            if verbose:
                print("error (applicability check failed)")
            return Finding.error(
                assessor.attribute, reason=f"Applicability check failed: {str(e)}"
            )

        # Try to assess
        try:
            finding = assessor.assess(repository)

            if verbose:
                if finding.status == "pass":
                    print(f"pass ({finding.score:.0f})")
                elif finding.status == "fail":
                    print(f"fail ({finding.score:.0f})")
                elif finding.status == "skipped":
                    print("skipped")
                else:
                    print(finding.status)

            return finding

        except MissingToolError as e:
            if verbose:
                print(f"skipped (missing {e.tool_name})")

            return Finding.skipped(
                assessor.attribute,
                reason=f"Missing tool: {e.tool_name}",
                remediation=(
                    f"Install with: {e.install_command}" if e.install_command else ""
                ),
            )

        except PermissionError as e:
            if verbose:
                print("skipped (permission denied)")

            return Finding.skipped(
                assessor.attribute,
                reason=f"Permission denied: {getattr(e, 'filename', 'unknown')}",
            )

        except Exception as e:
            if verbose:
                print(f"error ({type(e).__name__})")

            return Finding.error(assessor.attribute, reason=str(e))
