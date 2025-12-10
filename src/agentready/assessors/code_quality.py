"""Code quality assessors for complexity, file length, type annotations, and code smells."""

import ast
import logging
import re

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..services.scanner import MissingToolError
from ..utils.subprocess_utils import safe_subprocess_run
from .base import BaseAssessor

logger = logging.getLogger(__name__)


class TypeAnnotationsAssessor(BaseAssessor):
    """Assesses type annotation coverage in code.

    Tier 1 Essential (10% weight) - Type hints are critical for AI understanding.
    """

    @property
    def attribute_id(self) -> str:
        return "type_annotations"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Type Annotations",
            category="Code Quality",
            tier=self.tier,
            description="Type hints in function signatures",
            criteria=">80% of functions have type annotations",
            default_weight=0.10,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Only applicable to statically-typed or type-hinted languages."""
        applicable_languages = {
            "Python",
            "TypeScript",
            "Java",
            "C#",
            "Kotlin",
            "Go",
            "Rust",
        }
        return bool(set(repository.languages.keys()) & applicable_languages)

    def assess(self, repository: Repository) -> Finding:
        """Check type annotation coverage.

        For Python: Use mypy or similar
        For TypeScript: Check tsconfig.json strict mode
        For others: Heuristic checks
        """
        if "Python" in repository.languages:
            return self._assess_python_types(repository)
        elif "TypeScript" in repository.languages:
            return self._assess_typescript_types(repository)
        else:
            # For other languages, use heuristic
            return Finding.not_applicable(
                self.attribute,
                reason=f"Type annotation check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_types(self, repository: Repository) -> Finding:
        """Assess Python type annotations using AST parsing."""
        # Use AST parsing to accurately detect type annotations
        try:
            # Security: Use safe_subprocess_run for validation and limits
            result = safe_subprocess_run(
                ["git", "ls-files", "*.py"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            python_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            python_files = [
                str(f.relative_to(repository.path))
                for f in repository.path.rglob("*.py")
            ]

        total_functions = 0
        typed_functions = 0

        for file_path in python_files:
            full_path = repository.path / file_path
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the file with AST
                tree = ast.parse(content, filename=str(file_path))

                # Walk the AST and count functions with type annotations
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        # Check if function has type annotations
                        # Return type annotation: node.returns is not None
                        # Parameter annotations: any arg has annotation
                        has_return_annotation = node.returns is not None
                        has_param_annotations = any(
                            arg.annotation is not None for arg in node.args.args
                        )

                        # Consider function typed if it has either return or param annotations
                        if has_return_annotation or has_param_annotations:
                            typed_functions += 1

            except (OSError, UnicodeDecodeError, SyntaxError):
                # Skip files that can't be read or parsed
                continue

        if total_functions == 0:
            return Finding.not_applicable(
                self.attribute, reason="No Python functions found"
            )

        coverage_percent = (typed_functions / total_functions) * 100
        score = self.calculate_proportional_score(
            measured_value=coverage_percent,
            threshold=80.0,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{coverage_percent:.1f}%",
            threshold="≥80%",
            evidence=[
                f"Typed functions: {typed_functions}/{total_functions}",
                f"Coverage: {coverage_percent:.1f}%",
            ],
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _assess_typescript_types(self, repository: Repository) -> Finding:
        """Assess TypeScript type configuration."""
        tsconfig_path = repository.path / "tsconfig.json"

        if not tsconfig_path.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing tsconfig.json",
                threshold="strict mode enabled",
                evidence=["tsconfig.json not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        try:
            import json

            with open(tsconfig_path, "r") as f:
                tsconfig = json.load(f)

            strict = tsconfig.get("compilerOptions", {}).get("strict", False)

            if strict:
                return Finding(
                    attribute=self.attribute,
                    status="pass",
                    score=100.0,
                    measured_value="strict mode enabled",
                    threshold="strict mode enabled",
                    evidence=["tsconfig.json has strict: true"],
                    remediation=None,
                    error_message=None,
                )
            else:
                return Finding(
                    attribute=self.attribute,
                    status="fail",
                    score=50.0,
                    measured_value="strict mode disabled",
                    threshold="strict mode enabled",
                    evidence=["tsconfig.json missing strict: true"],
                    remediation=self._create_remediation(),
                    error_message=None,
                )

        except (OSError, json.JSONDecodeError) as e:
            return Finding.error(
                self.attribute, reason=f"Could not parse tsconfig.json: {str(e)}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for type annotations."""
        return Remediation(
            summary="Add type annotations to function signatures",
            steps=[
                "For Python: Add type hints to function parameters and return types",
                "For TypeScript: Enable strict mode in tsconfig.json",
                "Use mypy or pyright for Python type checking",
                "Use tsc --strict for TypeScript",
                "Add type annotations gradually to existing code",
            ],
            tools=["mypy", "pyright", "typescript"],
            commands=[
                "# Python",
                "pip install mypy",
                "mypy --strict src/",
                "",
                "# TypeScript",
                "npm install --save-dev typescript",
                'echo \'{"compilerOptions": {"strict": true}}\' > tsconfig.json',
            ],
            examples=[
                """# Python - Before
def calculate(x, y):
    return x + y

# Python - After
def calculate(x: float, y: float) -> float:
    return x + y
""",
                """// TypeScript - tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
""",
            ],
            citations=[
                Citation(
                    source="Python.org",
                    title="Type Hints",
                    url="https://docs.python.org/3/library/typing.html",
                    relevance="Official Python type hints documentation",
                ),
                Citation(
                    source="TypeScript",
                    title="TypeScript Handbook",
                    url="https://www.typescriptlang.org/docs/handbook/2/everyday-types.html",
                    relevance="TypeScript type system guide",
                ),
            ],
        )


class CyclomaticComplexityAssessor(BaseAssessor):
    """Assesses cyclomatic complexity using radon."""

    @property
    def attribute_id(self) -> str:
        return "cyclomatic_complexity"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Cyclomatic Complexity Thresholds",
            category="Code Quality",
            tier=self.tier,
            description="Cyclomatic complexity thresholds enforced",
            criteria="Average complexity <10, no functions >15",
            default_weight=0.03,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable to languages supported by radon or lizard."""
        supported = {"Python", "JavaScript", "TypeScript", "C", "C++", "Java"}
        return bool(set(repository.languages.keys()) & supported)

    def assess(self, repository: Repository) -> Finding:
        """Check cyclomatic complexity using radon or lizard."""
        if "Python" in repository.languages:
            return self._assess_python_complexity(repository)
        else:
            # Use lizard for other languages
            return self._assess_with_lizard(repository)

    def _assess_python_complexity(self, repository: Repository) -> Finding:
        """Assess Python complexity using radon."""
        try:
            # Check if radon is available
            # Security: Use safe_subprocess_run for validation and limits
            result = safe_subprocess_run(
                ["radon", "cc", str(repository.path), "-s", "-a"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise MissingToolError("radon", install_command="pip install radon")

            # Parse radon output for average complexity
            # Output format: "Average complexity: A (5.2)"
            output = result.stdout

            if "Average complexity:" in output:
                # Extract average value
                avg_line = [
                    line for line in output.split("\n") if "Average complexity:" in line
                ][0]
                avg_value = float(avg_line.split("(")[1].split(")")[0])

                score = self.calculate_proportional_score(
                    measured_value=avg_value,
                    threshold=10.0,
                    higher_is_better=False,
                )

                status = "pass" if score >= 75 else "fail"

                return Finding(
                    attribute=self.attribute,
                    status=status,
                    score=score,
                    measured_value=f"{avg_value:.1f}",
                    threshold="<10.0",
                    evidence=[f"Average cyclomatic complexity: {avg_value:.1f}"],
                    remediation=(
                        self._create_remediation() if status == "fail" else None
                    ),
                    error_message=None,
                )
            else:
                return Finding.not_applicable(
                    self.attribute, reason="No Python code to analyze"
                )

        except FileNotFoundError:
            # radon command not found
            raise MissingToolError("radon", install_command="pip install radon")
        except MissingToolError:
            raise  # Re-raise to be caught by Scanner
        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
            )

    def _assess_with_lizard(self, repository: Repository) -> Finding:
        """Assess complexity using lizard (multi-language)."""
        try:
            # Security: Use safe_subprocess_run for validation and limits
            result = safe_subprocess_run(
                ["lizard", str(repository.path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise MissingToolError("lizard", install_command="pip install lizard")

            # Parse lizard output
            # This is simplified - production code should parse properly
            return Finding.not_applicable(
                self.attribute, reason="Lizard analysis not fully implemented"
            )

        except FileNotFoundError:
            # lizard command not found
            raise MissingToolError("lizard", install_command="pip install lizard")
        except MissingToolError:
            raise
        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for high complexity."""
        return Remediation(
            summary="Reduce cyclomatic complexity by refactoring complex functions",
            steps=[
                "Identify functions with complexity >15",
                "Break down complex functions into smaller functions",
                "Extract conditional logic into separate functions",
                "Use early returns to reduce nesting",
                "Consider using strategy pattern for complex conditionals",
            ],
            tools=["radon", "lizard"],
            commands=[
                "# Install radon",
                "pip install radon",
                "",
                "# Check complexity",
                "radon cc src/ -s -a",
                "",
                "# Find high complexity functions",
                "radon cc src/ -n C",
            ],
            examples=[],
            citations=[
                Citation(
                    source="Microsoft",
                    title="Code Metrics - Cyclomatic Complexity",
                    url="https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity",
                    relevance="Explanation of cyclomatic complexity and thresholds",
                )
            ],
        )


class SemanticNamingAssessor(BaseAssessor):
    """Assesses naming conventions and semantic clarity.

    Tier 3 Important (1.5% weight) - Consistent naming improves code
    readability and helps LLMs understand intent.
    """

    @property
    def attribute_id(self) -> str:
        return "semantic_naming"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Semantic Naming",
            category="Code Quality",
            tier=self.tier,
            description="Systematic naming patterns following language conventions",
            criteria="Language conventions followed, avoid generic names",
            default_weight=0.015,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Only applicable to code repositories."""
        return len(repository.languages) > 0

    def assess(self, repository: Repository) -> Finding:
        """Check naming conventions and patterns."""
        if "Python" in repository.languages:
            return self._assess_python_naming(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Naming check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_naming(self, repository: Repository) -> Finding:
        """Assess Python naming conventions using AST parsing."""
        # Get list of Python files
        try:
            result = safe_subprocess_run(
                ["git", "ls-files", "*.py"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            python_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            python_files = [
                str(f.relative_to(repository.path))
                for f in repository.path.rglob("*.py")
            ]

        # Sample files for large repositories (max 50 files)
        if len(python_files) > 50:
            import random

            python_files = random.sample(python_files, 50)

        total_functions = 0
        compliant_functions = 0
        total_classes = 0
        compliant_classes = 0
        generic_names_count = 0

        # Patterns
        snake_case_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
        pascal_case_pattern = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
        generic_names = {"temp", "data", "info", "obj", "var", "tmp", "x", "y", "z"}

        for file_path in python_files:
            full_path = repository.path / file_path
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    # Check function names
                    if isinstance(node, ast.FunctionDef):
                        # Skip private/magic methods
                        if node.name.startswith("_"):
                            continue

                        total_functions += 1
                        if snake_case_pattern.match(node.name):
                            compliant_functions += 1

                        # Check for generic names
                        if node.name.lower() in generic_names:
                            generic_names_count += 1

                    # Check class names
                    elif isinstance(node, ast.ClassDef):
                        # Skip private classes
                        if node.name.startswith("_"):
                            continue

                        total_classes += 1
                        if pascal_case_pattern.match(node.name):
                            compliant_classes += 1

            except (OSError, UnicodeDecodeError, SyntaxError):
                continue

        if total_functions == 0 and total_classes == 0:
            return Finding.not_applicable(
                self.attribute, reason="No Python functions or classes found"
            )

        # Calculate scores
        function_compliance = (
            (compliant_functions / total_functions * 100)
            if total_functions > 0
            else 100
        )
        class_compliance = (
            (compliant_classes / total_classes * 100) if total_classes > 0 else 100
        )

        # Overall score: 60% functions, 40% classes
        naming_score = (function_compliance * 0.6) + (class_compliance * 0.4)

        # Penalize generic names
        if generic_names_count > 0:
            penalty = min(20, generic_names_count * 5)
            naming_score = max(0, naming_score - penalty)

        status = "pass" if naming_score >= 75 else "fail"

        # Build evidence
        evidence = [
            f"Functions: {compliant_functions}/{total_functions} follow snake_case ({function_compliance:.1f}%)",
            f"Classes: {compliant_classes}/{total_classes} follow PascalCase ({class_compliance:.1f}%)",
        ]

        if generic_names_count > 0:
            evidence.append(
                f"Generic names detected: {generic_names_count} occurrences"
            )
        else:
            evidence.append("No generic names (temp, data, obj) detected")

        return Finding(
            attribute=self.attribute,
            status=status,
            score=naming_score,
            measured_value=f"functions:{function_compliance:.0f}%, classes:{class_compliance:.0f}%",
            threshold="≥75% compliance",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for naming issues."""
        return Remediation(
            summary="Improve naming consistency and semantic clarity",
            steps=[
                "Follow language naming conventions (PEP 8 for Python)",
                "Use snake_case for functions/variables in Python",
                "Use PascalCase for classes in Python",
                "Use descriptive names (>3 characters, no abbreviations)",
                "Avoid generic names: temp, data, obj, var, info",
                "Use verbs for functions: get_user, calculate_total",
                "Use nouns for classes: User, OrderService",
                "Enforce with linters: pylint --enable=invalid-name",
            ],
            tools=["pylint", "black"],
            commands=[
                "# Check naming conventions",
                "pylint --disable=all --enable=invalid-name src/",
            ],
            examples=[
                """# Good naming
class UserService:
    MAX_LOGIN_ATTEMPTS = 5

    def create_user(self, email: str) -> User:
        pass

    def delete_user(self, user_id: str) -> None:
        pass

# Bad naming
class userservice:  # Should be PascalCase
    maxLoginAttempts = 5  # Should be UPPER_CASE

    def CreateUser(self, e: str) -> User:  # Should be snake_case
        pass

    def data(self, temp):  # Generic names
        pass
""",
            ],
            citations=[
                Citation(
                    source="Python.org",
                    title="PEP 8 - Style Guide for Python Code",
                    url="https://peps.python.org/pep-0008/#naming-conventions",
                    relevance="Official Python naming conventions",
                ),
            ],
        )


class StructuredLoggingAssessor(BaseAssessor):
    """Assesses use of structured logging libraries.

    Tier 3 Important (1.5% weight) - Structured logs are machine-parseable
    and enable AI to analyze logs for debugging and optimization.
    """

    @property
    def attribute_id(self) -> str:
        return "structured_logging"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Structured Logging",
            category="Code Quality",
            tier=self.tier,
            description="Logging in structured format (JSON) with consistent fields",
            criteria="Structured logging library configured (structlog, winston, zap)",
            default_weight=0.015,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable to any code repository."""
        return len(repository.languages) > 0

    def assess(self, repository: Repository) -> Finding:
        """Check for structured logging library usage."""
        # Check Python dependencies
        if "Python" in repository.languages:
            return self._assess_python_logging(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Structured logging check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_logging(self, repository: Repository) -> Finding:
        """Check for Python structured logging libraries."""
        # Libraries to check for
        structured_libs = ["structlog", "python-json-logger", "structlog-sentry"]

        # Check dependency files
        dep_files = [
            repository.path / "pyproject.toml",
            repository.path / "requirements.txt",
            repository.path / "setup.py",
        ]

        found_libs = []
        checked_files = []

        for dep_file in dep_files:
            if not dep_file.exists():
                continue

            checked_files.append(dep_file.name)
            try:
                content = dep_file.read_text(encoding="utf-8")
                for lib in structured_libs:
                    if lib in content:
                        found_libs.append(lib)
            except (OSError, UnicodeDecodeError):
                continue

        if not checked_files:
            return Finding.not_applicable(
                self.attribute, reason="No Python dependency files found"
            )

        # Score: Binary - either has structured logging or not
        if found_libs:
            score = 100.0
            status = "pass"
            evidence = [
                f"Structured logging library found: {', '.join(set(found_libs))}",
                f"Checked files: {', '.join(checked_files)}",
            ]
            remediation = None
        else:
            score = 0.0
            status = "fail"
            evidence = [
                "No structured logging library found",
                f"Checked files: {', '.join(checked_files)}",
                "Using built-in logging module (unstructured)",
            ]
            remediation = self._create_remediation()

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value="configured" if found_libs else "not configured",
            threshold="structured logging library",
            evidence=evidence,
            remediation=remediation,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for structured logging."""
        return Remediation(
            summary="Add structured logging library for machine-parseable logs",
            steps=[
                "Choose structured logging library (structlog for Python, winston for Node.js)",
                "Install library and configure JSON formatter",
                "Add standard fields: timestamp, level, message, context",
                "Include request context: request_id, user_id, session_id",
                "Use consistent field naming (snake_case for Python)",
                "Never log sensitive data (passwords, tokens, PII)",
                "Configure different formats for dev (pretty) and prod (JSON)",
            ],
            tools=["structlog", "winston", "zap"],
            commands=[
                "# Install structlog",
                "pip install structlog",
                "",
                "# Configure structlog",
                "# See examples for configuration",
            ],
            examples=[
                """# Python with structlog
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Good: Structured logging
logger.info(
    "user_login",
    user_id="123",
    email="user@example.com",
    ip_address="192.168.1.1"
)

# Bad: Unstructured logging
logger.info(f"User {user_id} logged in from {ip}")
""",
            ],
            citations=[
                Citation(
                    source="structlog",
                    title="structlog Documentation",
                    url="https://www.structlog.org/en/stable/",
                    relevance="Python structured logging library",
                ),
            ],
        )


class CodeSmellsAssessor(BaseAssessor):
    """Assesses code smell detection through linter configuration.

    Tier 4 Advanced (1% weight) - Checks for language-specific linters that detect
    code smells, anti-patterns, and style violations. Enhanced to support multi-language
    linters: pylint, ruff, ESLint, RuboCop, golangci-lint, actionlint, markdownlint.
    """

    @property
    def attribute_id(self) -> str:
        return "code_smells"

    @property
    def tier(self) -> int:
        return 4  # Advanced

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Code Smell Elimination",
            category="Code Quality",
            tier=self.tier,
            description="Linter configuration for detecting code smells and anti-patterns",
            criteria="Language-specific linters configured (pylint, ESLint, RuboCop, etc.)",
            default_weight=0.01,
        )

    def _has_pylint(self, repository: Repository) -> bool:
        """Check for pylint configuration."""
        return (
            (repository.path / ".pylintrc").exists()
            or (repository.path / "pylintrc").exists()
            or (
                repository.path / "pyproject.toml"
            ).exists()  # Can contain [tool.pylint]
        )

    def _has_ruff(self, repository: Repository) -> bool:
        """Check for ruff configuration."""
        return (
            (repository.path / "ruff.toml").exists()
            or (repository.path / ".ruff.toml").exists()
            or (repository.path / "pyproject.toml").exists()  # Can contain [tool.ruff]
        )

    def _has_eslint(self, repository: Repository) -> bool:
        """Check for ESLint configuration."""
        return (
            (repository.path / ".eslintrc.js").exists()
            or (repository.path / ".eslintrc.json").exists()
            or (repository.path / ".eslintrc.yml").exists()
            or (repository.path / ".eslintrc.yaml").exists()
            or (repository.path / "eslint.config.js").exists()
            or (repository.path / "eslint.config.mjs").exists()
        )

    def _has_rubocop(self, repository: Repository) -> bool:
        """Check for RuboCop configuration."""
        return (repository.path / ".rubocop.yml").exists() or (
            repository.path / ".rubocop.yaml"
        ).exists()

    def _has_golangci_lint(self, repository: Repository) -> bool:
        """Check for golangci-lint configuration."""
        return (repository.path / ".golangci.yml").exists() or (
            repository.path / ".golangci.yaml"
        ).exists()

    def _has_actionlint(self, repository: Repository) -> bool:
        """Check for actionlint in pre-commit or GitHub Actions."""
        precommit_config = repository.path / ".pre-commit-config.yaml"
        if precommit_config.exists():
            try:
                content = precommit_config.read_text()
                if "actionlint" in content:
                    return True
            except Exception:
                pass

        # Check if actionlint is in GitHub Actions workflows
        workflows_dir = repository.path / ".github" / "workflows"
        if workflows_dir.exists():
            try:
                for workflow_file in workflows_dir.glob("*.yml") + workflows_dir.glob(
                    "*.yaml"
                ):
                    content = workflow_file.read_text()
                    if "actionlint" in content:
                        return True
            except Exception:
                pass

        return False

    def _has_markdownlint(self, repository: Repository) -> bool:
        """Check for markdownlint configuration."""
        return (
            (repository.path / ".markdownlint.json").exists()
            or (repository.path / ".markdownlintrc").exists()
            or (repository.path / ".markdownlint.yaml").exists()
            or (repository.path / ".markdownlint.yml").exists()
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for linter configurations across multiple languages."""
        linters_found = []
        score = 0
        max_possible_score = 0

        # Python linters (20 points each if Python detected)
        if "Python" in repository.languages:
            max_possible_score += 40

            if self._has_pylint(repository):
                score += 20
                linters_found.append("pylint")

            if self._has_ruff(repository):
                score += 20
                linters_found.append("ruff")

        # JavaScript/TypeScript linters (20 points if JS/TS detected)
        if "JavaScript" in repository.languages or "TypeScript" in repository.languages:
            max_possible_score += 20

            if self._has_eslint(repository):
                score += 20
                linters_found.append("ESLint")

        # Go linters (20 points if Go detected)
        if "Go" in repository.languages:
            max_possible_score += 20

            if self._has_golangci_lint(repository):
                score += 20
                linters_found.append("golangci-lint")

        # Ruby linters (20 points if Ruby detected)
        if "Ruby" in repository.languages:
            max_possible_score += 20

            if self._has_rubocop(repository):
                score += 20
                linters_found.append("RuboCop")

        # GitHub Actions linter (10 points if .github/workflows exists)
        if (repository.path / ".github" / "workflows").exists():
            max_possible_score += 10

            if self._has_actionlint(repository):
                score += 10
                linters_found.append("actionlint")

        # Markdown linter (10 points - always applicable for repos with docs)
        max_possible_score += 10

        if self._has_markdownlint(repository):
            score += 10
            linters_found.append("markdownlint")

        # Normalize score to 0-100 based on applicable linters
        if max_possible_score == 0:
            return Finding.not_applicable(
                self.attribute,
                reason="No applicable languages detected for linter configuration",
            )

        normalized_score = (score / max_possible_score) * 100

        # Determine status (≥60% coverage to pass)
        if normalized_score >= 60:
            status = "pass"
            remediation = None
        else:
            status = "fail"

            # Build remediation based on missing linters
            missing_linters = []
            steps = []
            tools = []
            commands = []

            if "Python" in repository.languages and not self._has_pylint(repository):
                missing_linters.append("pylint (Python)")
                steps.append("Configure pylint for Python code smell detection")
                tools.append("pylint")
                commands.append(
                    "pip install pylint && pylint --generate-rcfile > .pylintrc"
                )

            if "Python" in repository.languages and not self._has_ruff(repository):
                missing_linters.append("ruff (Python)")
                steps.append("Configure ruff for fast Python linting")
                tools.append("ruff")
                commands.append("pip install ruff && ruff init")

            if (
                "JavaScript" in repository.languages
                or "TypeScript" in repository.languages
            ) and not self._has_eslint(repository):
                missing_linters.append("ESLint (JavaScript/TypeScript)")
                steps.append("Configure ESLint for JavaScript/TypeScript")
                tools.append("ESLint")
                commands.append("npm install --save-dev eslint && npx eslint --init")

            if "Go" in repository.languages and not self._has_golangci_lint(repository):
                missing_linters.append("golangci-lint (Go)")
                steps.append("Configure golangci-lint for Go")
                tools.append("golangci-lint")
                commands.append(
                    "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
                )

            if "Ruby" in repository.languages and not self._has_rubocop(repository):
                missing_linters.append("RuboCop (Ruby)")
                steps.append("Configure RuboCop for Ruby")
                tools.append("RuboCop")
                commands.append("gem install rubocop && rubocop --auto-gen-config")

            if (
                repository.path / ".github" / "workflows"
            ).exists() and not self._has_actionlint(repository):
                missing_linters.append("actionlint (GitHub Actions)")
                steps.append("Add actionlint for GitHub Actions workflow validation")
                tools.append("actionlint")

            if not self._has_markdownlint(repository):
                missing_linters.append("markdownlint (Markdown)")
                steps.append("Configure markdownlint for documentation quality")
                tools.append("markdownlint")
                commands.append(
                    "npm install --save-dev markdownlint-cli && touch .markdownlint.json"
                )

            remediation = Remediation(
                summary=f"Configure {len(missing_linters)} missing linter(s)",
                steps=steps,
                tools=tools,
                commands=commands,
                examples=[
                    "# .pylintrc example\n[MASTER]\nmax-line-length=100\n\n[MESSAGES CONTROL]\ndisable=C0111",
                    '# .eslintrc.json example\n{\n  "extends": "eslint:recommended",\n  "rules": {\n    "no-console": "warn"\n  }\n}',
                ],
                citations=[
                    Citation(
                        source="Pylint",
                        title="Pylint Documentation",
                        url="https://pylint.readthedocs.io/",
                        relevance="Official documentation for Pylint code analysis tool",
                    ),
                    Citation(
                        source="ESLint",
                        title="ESLint Documentation",
                        url="https://eslint.org/docs/latest/",
                        relevance="Official documentation for ESLint JavaScript/TypeScript linter",
                    ),
                ],
            )

        # Build evidence
        if linters_found:
            evidence = [
                f"Linters configured: {', '.join(linters_found)}",
                f"Coverage: {score}/{max_possible_score} points ({normalized_score:.0f}%)",
            ]
        else:
            evidence = ["No linters configured"]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=normalized_score,
            measured_value=(", ".join(linters_found) if linters_found else "none"),
            threshold="≥60% of applicable linters configured",
            evidence=evidence,
            remediation=remediation,
            error_message=None,
        )
