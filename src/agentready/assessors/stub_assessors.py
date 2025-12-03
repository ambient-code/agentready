"""Stub implementations for remaining assessors - minimal but functional.

These are simplified implementations to get the MVP working. Each can be
enhanced later with more sophisticated detection and scoring logic.
"""

from ..models.attribute import Attribute
from ..models.finding import Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class LockFilesAssessor(BaseAssessor):
    """Tier 1 Essential - Lock files for reproducible dependencies."""

    @property
    def attribute_id(self) -> str:
        return "lock_files"

    @property
    def tier(self) -> int:
        return 1

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Lock Files for Reproducibility",
            category="Dependency Management",
            tier=self.tier,
            description="Lock files present for dependency pinning",
            criteria="package-lock.json, yarn.lock, poetry.lock, or requirements.txt with versions",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        lock_files = [
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
            "Pipfile.lock",
            "uv.lock",
            "requirements.txt",
            "Cargo.lock",
            "Gemfile.lock",
            "go.sum",
        ]

        found = [f for f in lock_files if (repository.path / f).exists()]

        if found:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value=", ".join(found),
                threshold="at least one lock file",
                evidence=[f"Found: {', '.join(found)}"],
                remediation=None,
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="none",
                threshold="at least one lock file",
                evidence=["No lock files found"],
                remediation=Remediation(
                    summary="Add lock file for dependency reproducibility",
                    steps=[
                        "Use npm install, poetry lock, or equivalent to generate lock file"
                    ],
                    tools=[],
                    commands=["npm install  # generates package-lock.json"],
                    examples=[],
                    citations=[],
                ),
                error_message=None,
            )


# Tier 2 Critical Assessors (3% each)


class ConventionalCommitsAssessor(BaseAssessor):
    """Tier 2 - Conventional commit messages."""

    @property
    def attribute_id(self) -> str:
        return "conventional_commits"

    @property
    def tier(self) -> int:
        return 2

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Conventional Commit Messages",
            category="Git & Version Control",
            tier=self.tier,
            description="Follows conventional commit format",
            criteria="≥80% of recent commits follow convention",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        # Simplified: Check if commitlint or husky is configured
        has_commitlint = (repository.path / ".commitlintrc.json").exists()
        has_husky = (repository.path / ".husky").exists()

        if has_commitlint or has_husky:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="configured",
                threshold="configured",
                evidence=["Commit linting configured"],
                remediation=None,
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="not configured",
                threshold="configured",
                evidence=["No commitlint or husky configuration"],
                remediation=Remediation(
                    summary="Configure conventional commits with commitlint",
                    steps=["Install commitlint", "Configure husky for commit-msg hook"],
                    tools=["commitlint", "husky"],
                    commands=[
                        "npm install --save-dev @commitlint/cli @commitlint/config-conventional husky"
                    ],
                    examples=[],
                    citations=[],
                ),
                error_message=None,
            )


class GitignoreAssessor(BaseAssessor):
    """Tier 2 - Gitignore completeness."""

    @property
    def attribute_id(self) -> str:
        return "gitignore_completeness"

    @property
    def tier(self) -> int:
        return 2

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name=".gitignore Completeness",
            category="Git & Version Control",
            tier=self.tier,
            description="Comprehensive .gitignore file",
            criteria=".gitignore exists and covers common patterns",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        gitignore = repository.path / ".gitignore"

        if not gitignore.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="present",
                evidence=[".gitignore not found"],
                remediation=Remediation(
                    summary="Create .gitignore file",
                    steps=["Add .gitignore with common patterns for your language"],
                    tools=[],
                    commands=["touch .gitignore"],
                    examples=[],
                    citations=[],
                ),
                error_message=None,
            )

        # Check if it has content
        try:
            size = gitignore.stat().st_size
            score = 100.0 if size > 50 else 50.0
            status = "pass" if size > 50 else "fail"

            return Finding(
                attribute=self.attribute,
                status=status,
                score=score,
                measured_value=f"{size} bytes",
                threshold=">50 bytes",
                evidence=[f".gitignore found ({size} bytes)"],
                remediation=(
                    None
                    if status == "pass"
                    else Remediation(
                        summary="Expand .gitignore coverage",
                        steps=["Add common ignore patterns"],
                        tools=[],
                        commands=[],
                        examples=[],
                        citations=[],
                    )
                ),
                error_message=None,
            )
        except OSError:
            return Finding.error(self.attribute, reason="Could not read .gitignore")


class FileSizeLimitsAssessor(BaseAssessor):
    """Tier 2 - File size limits for context window optimization."""

    @property
    def attribute_id(self) -> str:
        return "file_size_limits"

    @property
    def tier(self) -> int:
        return 2

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="File Size Limits",
            category="Context Window Optimization",
            tier=self.tier,
            description="Files are reasonably sized for AI context windows",
            criteria="<5% of files >500 lines, no files >1000 lines",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for excessively large files that strain context windows.

        Scoring:
        - 100: All files <500 lines
        - 75-99: Some files 500-1000 lines
        - 0-74: Files >1000 lines exist
        """
        # Count files by size
        large_files = []  # 500-1000 lines
        huge_files = []  # >1000 lines
        total_files = 0

        # Check common source file extensions
        extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".go",
            ".java",
            ".rb",
            ".rs",
            ".cpp",
            ".c",
            ".h",
        }

        for ext in extensions:
            pattern = f"**/*{ext}"
            try:

                for file_path in repository.path.glob(pattern):
                    if file_path.is_file():
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                lines = len(f.readlines())
                                total_files += 1

                                if lines > 1000:
                                    huge_files.append(
                                        (file_path.relative_to(repository.path), lines)
                                    )
                                elif lines > 500:
                                    large_files.append(
                                        (file_path.relative_to(repository.path), lines)
                                    )
                        except (OSError, UnicodeDecodeError):
                            # Skip files we can't read
                            pass
            except Exception:
                pass

        if total_files == 0:
            return Finding.not_applicable(
                self.attribute,
                reason="No source files found to assess",
            )

        # Calculate score
        if huge_files:
            # Penalty for files >1000 lines
            percentage_huge = (len(huge_files) / total_files) * 100
            score = max(0, 70 - (percentage_huge * 10))
            status = "fail"
            evidence = [
                f"Found {len(huge_files)} files >1000 lines ({percentage_huge:.1f}% of {total_files} files)",
                f"Largest: {huge_files[0][0]} ({huge_files[0][1]} lines)",
            ]
        elif large_files:
            # Partial credit for files 500-1000 lines
            percentage_large = (len(large_files) / total_files) * 100
            if percentage_large < 5:
                score = 90
                status = "pass"
            else:
                score = max(75, 100 - (percentage_large * 5))
                status = "pass"

            evidence = [
                f"Found {len(large_files)} files 500-1000 lines ({percentage_large:.1f}% of {total_files} files)",
            ]
        else:
            # Perfect score
            score = 100.0
            status = "pass"
            evidence = [f"All {total_files} source files are <500 lines"]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{len(huge_files)} huge, {len(large_files)} large out of {total_files}",
            threshold="<5% files >500 lines, 0 files >1000 lines",
            evidence=evidence,
            remediation=(
                None
                if status == "pass"
                else Remediation(
                    summary="Refactor large files into smaller, focused modules",
                    steps=[
                        "Identify files >1000 lines",
                        "Split into logical submodules",
                        "Extract classes/functions into separate files",
                        "Maintain single responsibility principle",
                    ],
                    tools=["refactoring tools", "linters"],
                    commands=[],
                    examples=[
                        "# Split large file:\n# models.py (1500 lines) → models/user.py, models/product.py, models/order.py"
                    ],
                    citations=[],
                )
            ),
            error_message=None,
        )


# Create stub assessors for remaining attributes
# These return "not_applicable" for now but can be enhanced later


class StubAssessor(BaseAssessor):
    """Generic stub assessor for unimplemented attributes."""

    def __init__(
        self, attr_id: str, name: str, category: str, tier: int, weight: float
    ):
        self._attr_id = attr_id
        self._name = name
        self._category = category
        self._tier = tier
        self._weight = weight

    @property
    def attribute_id(self) -> str:
        return self._attr_id

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self._attr_id,
            name=self._name,
            category=self._category,
            tier=self._tier,
            description=f"Assessment for {self._name}",
            criteria="To be implemented",
            default_weight=self._weight,
        )

    def assess(self, repository: Repository) -> Finding:
        return Finding.not_applicable(
            self.attribute,
            reason=f"{self._name} assessment not yet implemented",
        )


# Factory function to create all stub assessors
def create_stub_assessors():
    """Create stub assessors for remaining attributes."""
    return [
        # Tier 2 Critical
        StubAssessor(
            "dependency_freshness",
            "Dependency Freshness & Security",
            "Dependency Management",
            2,
            0.03,
        ),
        StubAssessor(
            "separation_concerns",
            "Separation of Concerns",
            "Repository Structure",
            2,
            0.03,
        ),
        # Tier 3 Important
        StubAssessor(
            "architecture_decisions",
            "Architecture Decision Records",
            "Documentation Standards",
            3,
            0.03,
        ),
        # Tier 4 Advanced
        StubAssessor(
            "security_scanning", "Security Scanning Automation", "Security", 4, 0.01
        ),
        StubAssessor(
            "performance_benchmarks", "Performance Benchmarks", "Performance", 4, 0.01
        ),
        StubAssessor(
            "issue_pr_templates",
            "Issue & Pull Request Templates",
            "Git & Version Control",
            4,
            0.01,
        ),
        StubAssessor(
            "container_setup",
            "Container/Virtualization Setup",
            "Build & Development",
            4,
            0.01,
        ),
    ]
