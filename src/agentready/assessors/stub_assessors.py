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
        # Detect project type based on manifest files
        has_package_json = (repository.path / "package.json").exists()
        has_pyproject = (repository.path / "pyproject.toml").exists()
        has_setup_py = (repository.path / "setup.py").exists()
        has_cargo_toml = (repository.path / "Cargo.toml").exists()
        has_gemfile = (repository.path / "Gemfile").exists()
        has_go_mod = (repository.path / "go.mod").exists()

        # Check for lock files by language
        lock_files_found = []

        # Python lock files
        python_locks = ["uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock"]
        if has_pyproject or has_setup_py:
            for lock in python_locks:
                if (repository.path / lock).exists():
                    lock_files_found.append(lock)

        # Node.js lock files
        node_locks = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
        if has_package_json:
            for lock in node_locks:
                if (repository.path / lock).exists():
                    lock_files_found.append(lock)

        # Other language lock files
        if has_cargo_toml and (repository.path / "Cargo.lock").exists():
            lock_files_found.append("Cargo.lock")
        if has_gemfile and (repository.path / "Gemfile.lock").exists():
            lock_files_found.append("Gemfile.lock")
        if has_go_mod and (repository.path / "go.sum").exists():
            lock_files_found.append("go.sum")

        # Determine if this is a library project (more lenient for libraries)
        is_library = False
        if has_pyproject:
            try:
                import tomllib
                with open(repository.path / "pyproject.toml", "rb") as f:
                    pyproject = tomllib.load(f)
                    # Library if it has [project.scripts] or [tool.poetry.plugins]
                    is_library = "scripts" in pyproject.get("project", {}) or \
                                 "plugins" in pyproject.get("tool", {}).get("poetry", {})
            except Exception:
                pass

        if lock_files_found:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value=", ".join(lock_files_found),
                threshold="at least one lock file",
                evidence=[f"Found: {', '.join(lock_files_found)}"],
                remediation=None,
                error_message=None,
            )
        elif is_library and has_pyproject:
            # Python libraries can be more lenient - pyproject.toml with version constraints is acceptable
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="pyproject.toml with version constraints",
                threshold="lock file or pyproject.toml for libraries",
                evidence=["Python library detected with pyproject.toml dependency management"],
                remediation=None,
                error_message=None,
            )
        else:
            # Build language-specific remediation
            remediation_steps = []
            remediation_commands = []

            if has_pyproject or has_setup_py:
                remediation_steps.append("Generate a lock file using uv, poetry, or pipenv")
                remediation_commands.extend([
                    "uv lock  # Modern Python lock file",
                    "poetry lock  # Poetry lock file",
                    "pipenv lock  # Pipenv lock file"
                ])
            elif has_package_json:
                remediation_steps.append("Generate lock file using npm, yarn, or pnpm")
                remediation_commands.extend([
                    "npm install  # Generates package-lock.json",
                    "yarn install  # Generates yarn.lock",
                    "pnpm install  # Generates pnpm-lock.yaml"
                ])
            elif has_cargo_toml:
                remediation_steps.append("Cargo.lock should be auto-generated on build")
                remediation_commands.append("cargo build")
            elif has_go_mod:
                remediation_steps.append("go.sum should be auto-generated")
                remediation_commands.append("go mod tidy")
            else:
                remediation_steps.append("Add dependency lock file for your language/package manager")
                remediation_commands.append("# Use your package manager's lock command")

            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="none",
                threshold="at least one lock file",
                evidence=["No lock files found"],
                remediation=Remediation(
                    summary="Add lock file for dependency reproducibility",
                    steps=remediation_steps,
                    tools=[],
                    commands=remediation_commands,
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
        # Check for various conventional commit enforcement tools
        evidence = []
        configured = False

        # Node.js tools
        has_commitlint = (repository.path / ".commitlintrc.json").exists() or \
                        (repository.path / "commitlint.config.js").exists() or \
                        (repository.path / ".commitlintrc.js").exists()
        has_husky = (repository.path / ".husky").exists()

        if has_commitlint:
            evidence.append("Found commitlint configuration")
            configured = True
        if has_husky:
            evidence.append("Found husky hooks")
            configured = True

        # Python pre-commit hooks
        precommit_config = repository.path / ".pre-commit-config.yaml"
        if precommit_config.exists():
            try:
                import yaml
                with open(precommit_config, "r") as f:
                    config = yaml.safe_load(f)
                    if config and "repos" in config:
                        for repo in config["repos"]:
                            repo_url = repo.get("repo", "")
                            # Check for conventional-pre-commit hook
                            if "conventional-pre-commit" in repo_url:
                                hooks = repo.get("hooks", [])
                                for hook in hooks:
                                    if hook.get("id") == "conventional-pre-commit":
                                        evidence.append("Found conventional-pre-commit hook in .pre-commit-config.yaml")
                                        configured = True
                                        break
            except Exception:
                # If we can't parse the YAML, check for the string pattern
                try:
                    content = precommit_config.read_text()
                    if "conventional-pre-commit" in content:
                        evidence.append("Found conventional-pre-commit reference in .pre-commit-config.yaml")
                        configured = True
                except Exception:
                    pass

        if configured:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="configured",
                threshold="configured",
                evidence=evidence,
                remediation=None,
                error_message=None,
            )
        else:
            # Detect project type for appropriate remediation
            has_package_json = (repository.path / "package.json").exists()
            has_pyproject = (repository.path / "pyproject.toml").exists()
            has_setup_py = (repository.path / "setup.py").exists()

            remediation_steps = []
            remediation_tools = []
            remediation_commands = []

            if has_pyproject or has_setup_py:
                # Python project - recommend pre-commit
                remediation_steps.extend([
                    "Install pre-commit",
                    "Add conventional-pre-commit hook to .pre-commit-config.yaml"
                ])
                remediation_tools.append("pre-commit")
                remediation_commands.extend([
                    "pip install pre-commit",
                    "# Add to .pre-commit-config.yaml:",
                    "# - repo: https://github.com/compilerla/conventional-pre-commit",
                    "#   rev: v3.0.0",
                    "#   hooks:",
                    "#     - id: conventional-pre-commit",
                    "#       stages: [commit-msg]",
                    "pre-commit install --hook-type commit-msg"
                ])
            elif has_package_json:
                # Node.js project - recommend commitlint + husky
                remediation_steps.extend([
                    "Install commitlint and husky",
                    "Configure husky for commit-msg hook"
                ])
                remediation_tools.extend(["commitlint", "husky"])
                remediation_commands.append(
                    "npm install --save-dev @commitlint/cli @commitlint/config-conventional husky"
                )
            else:
                # Generic recommendation
                remediation_steps.append("Configure conventional commit enforcement for your project type")
                remediation_commands.append("# Use commitlint (Node.js) or pre-commit (Python)")

            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="not configured",
                threshold="configured",
                evidence=["No conventional commit enforcement detected"],
                remediation=Remediation(
                    summary="Configure conventional commits enforcement",
                    steps=remediation_steps,
                    tools=remediation_tools,
                    commands=remediation_commands,
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
            "one_command_setup",
            "One-Command Build/Setup",
            "Build & Development",
            2,
            0.03,
        ),
        StubAssessor(
            "file_size_limits",
            "File Size Limits",
            "Context Window Optimization",
            2,
            0.03,
        ),
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
