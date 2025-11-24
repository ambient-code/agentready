"""Batch assessment orchestrator for multiple repositories."""

import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from ..models import BatchAssessment, BatchSummary, RepositoryResult
from .assessment_cache import AssessmentCache
from .repository_manager import RepositoryManager
from .scanner import Scanner


class BatchScanner:
    """Orchestrates batch assessment of multiple repositories.

    Coordinates:
    - Repository cloning/validation
    - Individual assessments
    - Result aggregation
    - Error handling and retry logic
    - Progress tracking
    """

    def __init__(
        self,
        cache_dir: Path = None,
        batch_id: Optional[str] = None,
        version: str = "unknown",
        command: str = "",
    ):
        """Initialize batch scanner.

        Args:
            cache_dir: Directory for caching (default: .agentready/cache)
            batch_id: Unique batch identifier (auto-generated if not provided)
            version: AgentReady version
            command: CLI command that triggered the batch
        """
        if cache_dir is None:
            cache_dir = Path(".agentready/cache")

        self.cache_dir = Path(cache_dir)
        self.batch_id = batch_id or str(uuid4())
        self.version = version
        self.command = command

        self.repo_manager = RepositoryManager(self.cache_dir / "repositories")
        self.cache = AssessmentCache(self.cache_dir / "assessments")

    def scan_batch(
        self,
        repository_urls: list[str],
        assessors: list,
        config=None,
        use_cache: bool = True,
        verbose: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchAssessment:
        """Scan multiple repositories and generate batch assessment.

        Args:
            repository_urls: List of repository URLs or local paths
            assessors: List of assessor instances
            config: Custom configuration
            use_cache: Whether to use cached results
            verbose: Verbose output
            progress_callback: Callback function(current, total) for progress tracking

        Returns:
            BatchAssessment with results and summary
        """
        start_time = time.time()
        results = []

        for i, url in enumerate(repository_urls):
            if progress_callback:
                progress_callback(i, len(repository_urls))

            result = self._assess_single_repository(
                url,
                assessors,
                config,
                use_cache,
                verbose,
            )
            results.append(result)

        # Calculate summary statistics
        summary = self._calculate_summary(results)

        # Create batch assessment
        batch = BatchAssessment(
            batch_id=self.batch_id,
            timestamp=datetime.fromtimestamp(start_time),
            results=results,
            summary=summary,
            total_duration_seconds=time.time() - start_time,
            agentready_version=self.version,
            command=self.command,
        )

        return batch

    def _assess_single_repository(
        self,
        url: str,
        assessors: list,
        config=None,
        use_cache: bool = True,
        verbose: bool = False,
    ) -> RepositoryResult:
        """Assess a single repository.

        Args:
            url: Repository URL or path
            assessors: List of assessors
            config: Custom configuration
            use_cache: Use cached results if available
            verbose: Verbose output

        Returns:
            RepositoryResult with assessment or error
        """
        start_time = time.time()

        try:
            # Prepare repository (clone if needed)
            success, repository, failure = self.repo_manager.prepare_repository(url)
            if not success:
                return RepositoryResult(
                    repository_url=url,
                    assessment=None,
                    error=failure.error_message,
                    error_type=failure.error_type,
                    duration_seconds=time.time() - start_time,
                )

            # Check cache
            if use_cache:
                cached = self.cache.get(url, repository.commit_hash)
                if cached:
                    return RepositoryResult(
                        repository_url=url,
                        assessment=cached,
                        duration_seconds=time.time() - start_time,
                        cached=True,
                    )

            # Perform assessment
            scanner = Scanner(repository.path, config)
            assessment = scanner.scan(assessors, verbose, self.version, self.command)

            # Cache result
            if use_cache:
                self.cache.set(url, repository.commit_hash, assessment)

            return RepositoryResult(
                repository_url=url,
                assessment=assessment,
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return RepositoryResult(
                repository_url=url,
                assessment=None,
                error=f"Unexpected error: {str(e)}",
                error_type="assessment_error",
                duration_seconds=time.time() - start_time,
            )

    def _calculate_summary(self, results: list[RepositoryResult]) -> BatchSummary:
        """Calculate summary statistics from results.

        Args:
            results: List of RepositoryResult objects

        Returns:
            BatchSummary with aggregated statistics
        """
        successful = [r for r in results if r.is_success()]
        failed = [r for r in results if not r.is_success()]

        # Calculate average score
        if successful:
            average_score = sum(r.assessment.overall_score for r in successful) / len(
                successful
            )
        else:
            average_score = 0.0

        # Score distribution
        score_distribution = {
            "Platinum": 0,
            "Gold": 0,
            "Silver": 0,
            "Bronze": 0,
            "Needs Improvement": 0,
        }
        for result in successful:
            level = result.assessment.certification_level
            if level in score_distribution:
                score_distribution[level] += 1

        # Language breakdown
        language_breakdown = {}
        for result in successful:
            for lang, count in result.assessment.repository.languages.items():
                language_breakdown[lang] = language_breakdown.get(lang, 0) + count

        # Top failing attributes
        failing_attributes = {}
        for result in successful:
            for finding in result.assessment.findings:
                if finding.status == "fail":
                    attr_id = finding.attribute.id
                    failing_attributes[attr_id] = failing_attributes.get(attr_id, 0) + 1

        top_failing = sorted(
            failing_attributes.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        top_failing_attributes = [
            {
                "attribute_id": attr_id,
                "failure_count": count,
            }
            for attr_id, count in top_failing
        ]

        return BatchSummary(
            total_repositories=len(results),
            successful_assessments=len(successful),
            failed_assessments=len(failed),
            average_score=average_score,
            score_distribution=score_distribution,
            language_breakdown=language_breakdown,
            top_failing_attributes=top_failing_attributes,
        )
