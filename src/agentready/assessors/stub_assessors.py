"""Stub implementations for remaining assessors - minimal but functional.

These are simplified implementations to get the MVP working. Each can be
enhanced later with more sophisticated detection and scoring logic.
"""

from pathlib import Path

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..utils.subprocess_utils import safe_subprocess_run
from .base import BaseAssessor


class DependencyPinningAssessor(BaseAssessor):
    """Tier 1 Essential - Dependency version pinning for reproducible builds.

    Renamed from LockFilesAssessor. Checks not just file existence, but actual
    version pinning quality and freshness.
    """

    @property
    def attribute_id(self) -> str:
        return "lock_files"  # Keep same ID for backwards compatibility

    @property
    def tier(self) -> int:
        return 1

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Dependency Pinning for Reproducibility",
            category="Dependency Management",
            tier=self.tier,
            description="Dependencies pinned to exact versions in lock files",
            criteria="Lock file with pinned versions, updated within 6 months",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for dependency lock files and validate version pinning quality."""
        # Language-specific lock files (auto-managed, always have exact versions)
        strict_lock_files = [
            "package-lock.json",  # npm
            "yarn.lock",  # Yarn
            "pnpm-lock.yaml",  # pnpm
            "poetry.lock",  # Poetry
            "Pipfile.lock",  # Pipenv
            "uv.lock",  # uv
            "Cargo.lock",  # Rust
            "Gemfile.lock",  # Ruby
            "go.sum",  # Go
        ]

        # Manual lock files (need validation)
        manual_lock_files = ["requirements.txt"]  # Python pip

        found_strict = [f for f in strict_lock_files if (repository.path / f).exists()]
        found_manual = [f for f in manual_lock_files if (repository.path / f).exists()]

        if not found_strict and not found_manual:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="none",
                threshold="lock file with pinned versions",
                evidence=["No dependency lock files found"],
                remediation=Remediation(
                    summary="Add lock file for dependency reproducibility",
                    steps=[
                        "For npm: run 'npm install' (generates package-lock.json)",
                        "For Python: use 'pip freeze > requirements.txt' or poetry",
                        "For Ruby: run 'bundle install' (generates Gemfile.lock)",
                    ],
                    tools=["npm", "pip", "poetry", "bundler"],
                    commands=[
                        "npm install  # npm",
                        "pip freeze > requirements.txt  # Python",
                        "poetry lock  # Python with Poetry",
                    ],
                    examples=[],
                    citations=[],
                ),
                error_message=None,
            )

        score = 100.0
        evidence = []
        warnings = []

        # Check strict lock files (always 100 points)
        if found_strict:
            evidence.append(f"Found lock file(s): {', '.join(found_strict)}")

            # Check freshness (< 6 months old)
            import time

            for lock_file in found_strict:
                lock_path = repository.path / lock_file
                try:
                    age_days = (time.time() - lock_path.stat().st_mtime) / 86400
                    age_months = age_days / 30

                    if age_months > 6:
                        score -= 15
                        warnings.append(
                            f"⚠️ {lock_file} is {int(age_months)} months old (consider updating dependencies)"
                        )
                except OSError:
                    pass

        # Check manual lock files (requirements.txt) for version pinning
        if found_manual and not found_strict:
            for lock_file in found_manual:
                lock_path = repository.path / lock_file
                try:
                    content = lock_path.read_text()
                    lines = [
                        line.strip()
                        for line in content.split("\n")
                        if line.strip() and not line.startswith("#")
                    ]

                    if not lines:
                        score = 0
                        evidence.append(f"❌ {lock_file} is empty")
                        continue

                    pinned_count = 0
                    unpinned_count = 0

                    for line in lines:
                        # Check for exact version pinning (==)
                        if "==" in line:
                            pinned_count += 1
                        # Check for range/minimum versions (>=, ~=, >, <, etc.)
                        elif any(
                            op in line for op in [">=", "<=", "~=", ">", "<", "^"]
                        ):
                            unpinned_count += 1
                        # No version specifier at all
                        elif "==" not in line and not any(
                            c in line for c in [">", "<", "~", "^"]
                        ):
                            unpinned_count += 1

                    if unpinned_count > 0:
                        # Deduct points for unpinned dependencies
                        pin_ratio = pinned_count / (pinned_count + unpinned_count)
                        score = pin_ratio * 100

                        evidence.append(
                            f"Found {lock_file}: {pinned_count} pinned, {unpinned_count} unpinned"
                        )
                        warnings.append(
                            f"⚠️ {unpinned_count} dependencies not pinned (use '==' not '>=')"
                        )
                    else:
                        evidence.append(
                            f"Found {lock_file}: All {pinned_count} dependencies pinned"
                        )

                except OSError as e:
                    return Finding.error(
                        self.attribute, reason=f"Could not read {lock_file}: {e}"
                    )

        # Combine evidence and warnings
        all_evidence = evidence + warnings

        if score >= 75:
            status = "pass"
            remediation = None
        else:
            status = "fail"
            remediation = Remediation(
                summary="Improve dependency version pinning",
                steps=[
                    "Use exact version pinning (== not >=) in requirements.txt",
                    "Or switch to poetry.lock or Pipfile.lock for automatic pinning",
                    "Update dependencies regularly (at least every 6 months)",
                ],
                tools=["pip", "poetry", "pipenv"],
                commands=[
                    "pip freeze > requirements.txt  # Exact versions",
                    "poetry lock  # Auto-managed lock file",
                ],
                examples=[],
                citations=[],
            )

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=", ".join(found_strict + found_manual),
            threshold="lock file with pinned versions, < 6 months old",
            evidence=all_evidence,
            remediation=remediation,
            error_message=None,
        )


# Backwards compatibility alias
LockFilesAssessor = DependencyPinningAssessor


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
        commitlint_configs = [
            ".commitlintrc",
            ".commitlintrc.json",
            ".commitlintrc.yaml",
            ".commitlintrc.yml",
            ".commitlintrc.js",
            ".commitlintrc.cjs",
            ".commitlintrc.mjs",
            ".commitlintrc.ts",
            ".commitlintrc.cts",
            "commitlint.config.js",
            "commitlint.config.cjs",
            "commitlint.config.mjs",
            "commitlint.config.ts",
            "commitlint.config.cts",
        ]
        has_commitlint = any(
            (repository.path / cfg).exists() for cfg in commitlint_configs
        )
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
    """Tier 2 - Gitignore completeness with language-specific pattern checking.

    Enhanced to check against GitHub's gitignore templates for language-specific patterns.
    References: https://github.com/github/gitignore
    """

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
            description="Comprehensive .gitignore file with language-specific patterns",
            criteria=".gitignore exists and includes language-specific patterns from GitHub templates",
            default_weight=0.03,
        )

    def _get_expected_patterns(self, languages: set[str]) -> list[str]:
        """Get expected .gitignore patterns for detected languages.

        Based on GitHub's gitignore templates: https://github.com/github/gitignore
        """
        patterns = {
            "Python": [
                "__pycache__/",
                "*.py[cod]",
                "*.egg-info/",
                ".pytest_cache/",
                "venv/",
                ".venv/",
                ".env",
            ],
            "JavaScript": [
                "node_modules/",
                "dist/",
                "build/",
                ".npm/",
                "*.log",
            ],
            "TypeScript": [
                "node_modules/",
                "dist/",
                "*.tsbuildinfo",
                ".npm/",
            ],
            "Java": [
                "target/",
                "*.class",
                ".gradle/",
                "build/",
                "*.jar",
            ],
            "Go": [
                "*.exe",
                "*.test",
                "vendor/",
                "*.out",
            ],
            "Ruby": [
                "*.gem",
                ".bundle/",
                "vendor/bundle/",
                ".ruby-version",
            ],
            "Rust": [
                "target/",
                "Cargo.lock",
                "**/*.rs.bk",
            ],
            # General patterns (always check)
            "General": [
                ".DS_Store",
                ".vscode/",
                ".idea/",
                "*.swp",
                "*.swo",
            ],
        }

        expected = []
        for lang in languages:
            if lang in patterns:
                expected.extend(patterns[lang])

        # Always include general patterns
        expected.extend(patterns["General"])

        return list(set(expected))  # Remove duplicates

    def assess(self, repository: Repository) -> Finding:
        gitignore = repository.path / ".gitignore"

        if not gitignore.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="present with language patterns",
                evidence=[".gitignore not found"],
                remediation=Remediation(
                    summary="Create .gitignore file with language-specific patterns",
                    steps=[
                        "Create .gitignore file",
                        "Add language-specific patterns from GitHub templates",
                        "Include editor/IDE ignore patterns",
                    ],
                    tools=[],
                    commands=["touch .gitignore"],
                    examples=[
                        "# Python .gitignore example\n__pycache__/\n*.py[cod]\n.venv/\n.env\n.pytest_cache/",
                        "# JavaScript .gitignore example\nnode_modules/\ndist/\nbuild/\n*.log\n.npm/",
                    ],
                    citations=[
                        Citation(
                            source="GitHub",
                            title="gitignore Templates",
                            url="https://github.com/github/gitignore",
                            relevance="Community-maintained collection of .gitignore templates for various languages and frameworks",
                        ),
                    ],
                ),
                error_message=None,
            )

        # Read gitignore content
        try:
            content = gitignore.read_text()
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not read .gitignore: {e}"
            )

        if not content.strip():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="empty",
                threshold="language-specific patterns",
                evidence=[".gitignore is empty"],
                remediation=Remediation(
                    summary="Add language-specific ignore patterns",
                    steps=["Add patterns for your language from GitHub templates"],
                    tools=[],
                    commands=[],
                    examples=[],
                    citations=[
                        Citation(
                            source="GitHub",
                            title="gitignore Templates",
                            url="https://github.com/github/gitignore",
                            relevance="Community-maintained collection of .gitignore templates for various languages and frameworks",
                        ),
                    ],
                ),
                error_message=None,
            )

        # Get expected patterns for detected languages
        expected_patterns = self._get_expected_patterns(repository.languages)

        # Count how many expected patterns are present
        found_patterns = []
        missing_patterns = []

        for pattern in expected_patterns:
            # Check if pattern (or close variant) exists in .gitignore
            # Handle both with and without trailing slashes
            pattern_base = pattern.rstrip("/")
            if pattern in content or pattern_base in content:
                found_patterns.append(pattern)
            else:
                missing_patterns.append(pattern)

        # Calculate score based on pattern coverage
        if expected_patterns:
            coverage = (len(found_patterns) / len(expected_patterns)) * 100
            score = coverage
        else:
            # No languages detected, just check if file exists and has content
            score = 100.0 if len(content) > 50 else 50.0

        # Determine status
        if score >= 70:
            status = "pass"
            remediation = None
        else:
            status = "fail"
            remediation = Remediation(
                summary="Add missing language-specific ignore patterns",
                steps=[
                    "Review GitHub's gitignore templates for your language",
                    f"Add the {len(missing_patterns)} missing patterns",
                    "Ensure editor/IDE patterns are included",
                ],
                tools=[],
                commands=[],
                examples=["# Missing patterns:\n" + "\n".join(missing_patterns[:5])],
                citations=[
                    Citation(
                        source="GitHub",
                        title="gitignore Templates Collection",
                        url="https://github.com/github/gitignore",
                        relevance="Comprehensive collection of language-specific gitignore patterns",
                    ),
                ],
            )

        evidence = [
            f".gitignore found ({len(content)} bytes)",
            f"Pattern coverage: {len(found_patterns)}/{len(expected_patterns)} ({score:.0f}%)",
        ]

        if missing_patterns:
            evidence.append(f"Missing {len(missing_patterns)} recommended patterns")

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{len(found_patterns)}/{len(expected_patterns)} patterns",
            threshold="≥70% of language-specific patterns",
            evidence=evidence,
            remediation=remediation,
            error_message=None,
        )


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

        Note: Uses git ls-files to respect .gitignore (fixes issue #245).
        """
        # Count files by size
        large_files: list[tuple[Path, int]] = []  # 500-1000 lines
        huge_files: list[tuple[Path, int]] = []  # >1000 lines
        total_files = 0

        # Check common source file extensions
        extensions = [
            "py",
            "js",
            "ts",
            "jsx",
            "tsx",
            "go",
            "java",
            "rb",
            "rs",
            "cpp",
            "c",
            "h",
        ]

        # Get git-tracked files (respects .gitignore)
        # This fixes issue #245 where .venv files were incorrectly scanned
        try:
            patterns = [f"*.{ext}" for ext in extensions]
            result = safe_subprocess_run(
                ["git", "ls-files"] + patterns,
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            tracked_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            # Fallback for non-git repos: use glob (less accurate)
            tracked_files = []
            for ext in extensions:
                tracked_files.extend(
                    str(f.relative_to(repository.path))
                    for f in repository.path.rglob(f"*.{ext}")
                    if f.is_file()
                )

        # Count lines in tracked files
        for rel_path in tracked_files:
            file_path = repository.path / rel_path
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = len(f.readlines())
                    total_files += 1

                    if lines > 1000:
                        huge_files.append((Path(rel_path), lines))
                    elif lines > 500:
                        large_files.append((Path(rel_path), lines))
            except (OSError, UnicodeDecodeError):
                # Skip files we can't read
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
    """Create stub assessors for remaining attributes.

    Note: Removed stubs that are now implemented:
    - dependency_freshness → Merged into DependencySecurityAssessor
    - security_scanning → Merged into DependencySecurityAssessor
    - performance_benchmarks → Removed (low ROI)
    - separation_concerns → Implemented as SeparationOfConcernsAssessor
    - architecture_decisions → Implemented as ArchitectureDecisionsAssessor
    - issue_pr_templates → Implemented as IssuePRTemplatesAssessor
    - container_setup → Will be implemented separately with conditional applicability
    """
    return []  # All stubs have been implemented or removed
