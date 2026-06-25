"""ADR Frontmatter Completeness assessor.

Scores repositories on whether ADR files contain structured YAML
frontmatter with required fields (status + applies_to).
"""

from pathlib import Path

from ..models.attribute import Attribute
from ..models.config import AdrSourceConfig
from ..models.finding import Finding, Remediation
from ..models.repository import Repository
from ._adr_utils import parse_frontmatter
from .adr_sources import CentralAdrSource, LocalAdrSource
from .base import BaseAssessor

# VALID_STATUSES is kept as a reference for documentation and upstream tooling;
# it is no longer used to gate completeness scoring so that unfamiliar lifecycle
# values (e.g. project-specific conventions) are not incorrectly rejected.
# Title Case entries follow MADR convention; lowercase entries follow adr-tools convention.
VALID_STATUSES: frozenset[str] = frozenset(
    [
        # MADR core
        "Proposed",
        "Accepted",
        "Implementable",
        "Implemented",
        "Replaced",
        "Deprecated",
        "Superseded",
        "Approved",
        # adr-tools lowercase
        "active",
        "superseded",
        "draft",
    ]
)


def classify_adr_file(path: Path) -> str:
    """Classify a single ADR markdown file.

    Returns one of:
    - "valid"          — frontmatter present, status + applies_to valid
    - "incomplete"     — frontmatter present but field(s) missing/invalid
    - "no_frontmatter" — no leading --- block
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "no_frontmatter"

    fm = parse_frontmatter(content)
    if fm is None:
        return "no_frontmatter"

    status = fm.get("status")
    applies_to = fm.get("applies_to")

    # status must be present and a non-empty string; we do not restrict to VALID_STATUSES
    # so that project-specific lifecycle values are not rejected.
    if not status or not isinstance(status, str):
        return "incomplete"

    # applies_to must be present: a non-empty string, or a list whose every
    # item is a non-empty string (matching the contract of _applies_to_matches).
    if applies_to is None:
        return "incomplete"
    if not isinstance(applies_to, (str, list)):
        return "incomplete"
    if isinstance(applies_to, str) and not applies_to.strip():
        return "incomplete"
    if isinstance(applies_to, list):
        if not applies_to:
            return "incomplete"
        if not all(isinstance(item, str) and item.strip() for item in applies_to):
            return "incomplete"

    return "valid"


def score_from_coverage(valid: int, total: int) -> tuple[str, float]:
    """Compute (status_label, score) from valid/total ADR counts.

    Uses a three-band step function (0 / 60 / 100) rather than
    BaseAssessor.calculate_proportional_score(), which does linear
    interpolation.  The discrete bands are intentional: frontmatter
    compliance is a threshold-based quality gate, not a continuous metric.

    Args:
        valid: Number of valid ADRs.
        total: Total number of ADRs (valid + incomplete + no_frontmatter).

    Returns:
        Tuple of (status_label, score) where status_label is one of
        "pass", "partial", or "fail", and score is 0.0, 60.0, or 100.0.
    """
    if total == 0:
        return ("pass", 100.0)
    coverage = valid / total
    if coverage >= 0.80:
        return ("pass", 100.0)
    elif coverage >= 0.50:
        return ("partial", 60.0)
    else:
        return ("fail", 0.0)


class AdrFrontmatterAssessor(BaseAssessor):
    """Assesses ADR frontmatter completeness (status + applies_to fields).

    Tier 3 Important (2% weight). Structured frontmatter enables automated
    tooling to filter ADRs by applicability, status, and lifecycle stage.
    """

    @property
    def attribute_id(self) -> str:
        """Unique identifier used to register and look up this assessor."""
        return "adr_frontmatter_completeness"

    @property
    def tier(self) -> int:
        """Tier 3 — Important."""
        return 3

    @property
    def attribute(self) -> Attribute:
        """Attribute metadata including name, category, and default weight."""
        return Attribute(
            id=self.attribute_id,
            name="ADR Frontmatter Completeness",
            category="Documentation Standards",
            tier=self.tier,
            description=(
                "ADR files contain structured YAML frontmatter with required "
                "status and applies_to fields"
            ),
            criteria="≥80% of ADR files have valid frontmatter",
            default_weight=0.02,
        )

    def assess(self, repository: Repository) -> Finding:
        """Score ADR frontmatter completeness using LocalAdrSource or CentralAdrSource.

        If repository.config.adr_source is set, tries CentralAdrSource first.
        A None return from _assess_central means no central ADRs matched this
        repo — fall through to _assess_local so local ADRs are still scored.
        A Finding return (pass, fail, or skipped) is used directly.

        Returns skipped if no ADR files are found anywhere.
        """
        adr_source_config = (
            repository.config.adr_source if repository.config is not None else None
        )

        if adr_source_config is not None:
            central_result = self._assess_central(repository, adr_source_config)
            if central_result is not None:
                return central_result
            # None → no central ADRs match this repo; fall through to local scan

        return self._assess_local(repository)

    def _assess_local(self, repository: Repository) -> Finding:
        """Assess using LocalAdrSource (default path)."""
        source = LocalAdrSource()
        adr_dir = source.find_adr_dir(repository)

        if adr_dir is None:
            return Finding.skipped(
                self.attribute,
                "No ADR files found in standard locations",
            )

        adr_files = source.get_adr_files(adr_dir)
        return self._score_files(adr_files, adr_dir)

    def _assess_central(
        self, repository: Repository, config: AdrSourceConfig
    ) -> "Finding | None":
        """Assess using CentralAdrSource (central repo path).

        Returns:
            Finding (pass/fail/skipped): use directly — repo is unconfigured,
                path/subdir is unreachable, or matching ADRs were scored.
            None: central repo is reachable but no ADRs match this repo;
                caller should fall through to _assess_local.
        """
        local_path = Path(config.repo)
        adr_path = config.path

        if not local_path.exists():
            return Finding.skipped(
                self.attribute,
                f"Central ADR repo not found at {local_path}",
            )

        source = CentralAdrSource(local_path=local_path, adr_path=adr_path)

        if not source.adr_dir.is_dir():
            return Finding.skipped(
                self.attribute,
                f"Central ADR subdirectory missing: {source.adr_dir}",
            )

        try:
            total_in_central = sum(
                1 for p in source.adr_dir.iterdir() if p.suffix == ".md" and p.is_file()
            )
        except OSError:
            return Finding.skipped(
                self.attribute,
                f"Central ADR directory is not readable: {source.adr_dir}",
            )

        matched_files = source.get_matching_adr_files(repository.name)

        if not matched_files:
            # No central match — caller falls through to local scan
            return None

        extra_evidence = [
            f"ADR source: {source.adr_dir}/ (central repo)",
            (
                f"Filtered by applies_to: {repository.name} "
                f"({len(matched_files)} of {total_in_central} total ADRs matched)"
            ),
        ]
        return self._score_files(
            matched_files, source.adr_dir, extra_evidence=extra_evidence
        )

    def _score_files(
        self,
        adr_files: list[Path],
        adr_dir: Path,
        extra_evidence: list[str] | None = None,
    ) -> Finding:
        """Classify files, compute coverage, and build Finding."""
        counts: dict[str, int] = {"valid": 0, "incomplete": 0, "no_frontmatter": 0}
        for f in adr_files:
            label = classify_adr_file(f)
            counts[label] += 1

        total = len(adr_files)
        valid = counts["valid"]
        status_label, score = score_from_coverage(valid, total)

        pct = int(valid / total * 100) if total > 0 else 100
        measured_value = f"{valid}/{total} ADRs valid ({pct}%)"
        evidence = [
            f"ADR location: {adr_dir}",
            (
                f"{valid} valid, {counts['incomplete']} incomplete, "
                f"{counts['no_frontmatter']} no-frontmatter ({total} total)"
            ),
        ]
        if extra_evidence:
            evidence.extend(extra_evidence)

        remediation = None
        if status_label != "pass":
            remediation = Remediation(
                summary="Add YAML frontmatter with status and applies_to to all ADR files",
                steps=[
                    "Add a frontmatter block at the top of each ADR file",
                    "Include 'status' with a meaningful lifecycle value (e.g. Proposed, Accepted, Implemented, Deprecated — any non-empty string is accepted)",
                    "Include 'applies_to' (repo name, list of repos, or '*' for all)",
                    "Aim for ≥80% of ADRs to have valid frontmatter",
                ],
                tools=[],
                commands=[],
                examples=[
                    "---\nstatus: Implemented\napplies_to: my-service\n---\n# ADR 0001: ..."
                ],
                citations=[],
            )

        # "partial" is reported as "fail" with score=60 (Finding requires pass/fail)
        finding_status = "pass" if status_label == "pass" else "fail"

        return Finding(
            attribute=self.attribute,
            status=finding_status,
            score=score,
            measured_value=measured_value,
            threshold="≥80% valid ADRs",
            evidence=evidence,
            remediation=remediation,
            error_message=None,
        )
