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
            default_weight=0.08,
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

        Dispatches based on the primary programming language (by file count)
        to handle multi-language repos correctly.
        """
        primary = self._primary_language(repository, {"Python", "TypeScript", "Go"})
        if primary == "Python":
            return self._assess_python_types(repository)
        elif primary == "TypeScript":
            return self._assess_typescript_types(repository)
        elif primary == "Go":
            return self._assess_go_types(repository)
        else:
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

    def _assess_go_types(self, repository: Repository) -> Finding:
        """Assess Go type safety.

        Go is statically typed at compile time. Score starts at 100 and
        deducts for excessive use of interface{}/any which weakens type safety.
        """
        from ..utils.subprocess_utils import safe_subprocess_run

        try:
            result = safe_subprocess_run(
                ["git", "ls-files", "*.go"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            go_files = [
                f
                for f in result.stdout.strip().split("\n")
                if f and not f.endswith("_test.go")
            ]
        except Exception:
            go_files = [
                str(f.relative_to(repository.path))
                for f in repository.path.rglob("*.go")
                if not f.name.endswith("_test.go")
            ]

        if not go_files:
            return Finding.not_applicable(
                self.attribute, reason="No Go source files found"
            )

        total_funcs = 0
        any_usage_count = 0

        for file_path in go_files:
            full_path = repository.path / file_path
            try:
                content = full_path.read_text(encoding="utf-8")
                total_funcs += len(re.findall(r"^func\s+", content, re.MULTILINE))
                any_usage_count += len(
                    re.findall(r"\binterface\s*\{\s*\}|\bany\b", content)
                )
            except (OSError, UnicodeDecodeError):
                continue

        evidence = ["Go enforces types at compile time (statically typed)"]

        if total_funcs == 0:
            score = 100.0
        elif any_usage_count == 0:
            score = 100.0
            evidence.append("No interface{}/any usage found — strong type safety")
        else:
            ratio = any_usage_count / max(total_funcs, 1)
            if ratio < 0.1:
                score = 95.0
                evidence.append(
                    f"Minimal interface{{}}/any usage: {any_usage_count} occurrences"
                )
            elif ratio < 0.25:
                score = 85.0
                evidence.append(
                    f"Moderate interface{{}}/any usage: {any_usage_count} occurrences"
                )
            else:
                score = 70.0
                evidence.append(
                    f"Heavy interface{{}}/any usage: {any_usage_count} occurrences — consider using generics"
                )

        return Finding(
            attribute=self.attribute,
            status="pass" if score >= 75 else "fail",
            score=score,
            measured_value=f"{score:.0f}%",
            threshold="≥80%",
            evidence=evidence,
            remediation=None,
            error_message=None,
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
            default_weight=0.02,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable to languages supported by radon, lizard, or gocyclo."""
        supported = {"Python", "JavaScript", "TypeScript", "C", "C++", "Java", "Go"}
        return bool(set(repository.languages.keys()) & supported)

    def assess(self, repository: Repository) -> Finding:
        """Check cyclomatic complexity using radon, lizard, or gocyclo."""
        primary = self._primary_language(repository, {"Python", "Go"})
        if primary == "Python":
            return self._assess_python_complexity(repository)
        elif primary == "Go":
            return self._assess_go_complexity(repository)
        else:
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

    def _assess_go_complexity(self, repository: Repository) -> Finding:
        """Assess Go complexity using gocyclo or golangci-lint config detection.

        Tries gocyclo first. Falls back to checking if golangci-lint has
        complexity linters (gocyclo/cyclop) enabled in config.
        """
        try:
            result = safe_subprocess_run(
                ["gocyclo", "-avg", str(repository.path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                avg_line = [line for line in lines if "Average" in line]
                if avg_line:
                    avg_value = float(avg_line[0].split()[-1])

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
                        evidence=[
                            f"Average cyclomatic complexity (gocyclo): {avg_value:.1f}"
                        ],
                        remediation=(
                            self._create_go_complexity_remediation()
                            if status == "fail"
                            else None
                        ),
                        error_message=None,
                    )
        except (FileNotFoundError, Exception):
            pass

        # Fallback: check if golangci-lint has complexity linters configured
        # Search root and Go module root directories
        search_dirs = [repository.path] + self._find_go_module_roots(repository)
        for search_dir in search_dirs:
            for config_name in [
                ".golangci.yml",
                ".golangci.yaml",
                ".golangci.toml",
            ]:
                config_path = search_dir / config_name
                if config_path.exists():
                    try:
                        content = config_path.read_text(encoding="utf-8")
                        has_complexity = bool(
                            re.search(r"\b(gocyclo|cyclop|gocognit)\b", content)
                        )
                        if has_complexity:
                            rel = config_path.relative_to(repository.path)
                            return Finding(
                                attribute=self.attribute,
                                status="pass",
                                score=80.0,
                                measured_value="configured",
                                threshold="complexity linter enabled",
                                evidence=[f"Complexity linter configured in {rel}"],
                                remediation=None,
                                error_message=None,
                            )
                    except (OSError, UnicodeDecodeError):
                        continue

        # Also check if golangci-lint is present at all (even without
        # explicit complexity linters — it enables several by default)
        for search_dir in search_dirs:
            for config_name in [
                ".golangci.yml",
                ".golangci.yaml",
                ".golangci.toml",
            ]:
                if (search_dir / config_name).exists():
                    rel = (search_dir / config_name).relative_to(repository.path)
                    return Finding(
                        attribute=self.attribute,
                        status="pass",
                        score=70.0,
                        measured_value="golangci-lint configured",
                        threshold="complexity linter enabled",
                        evidence=[
                            f"golangci-lint configured in {rel} (default linters include basic complexity checks)"
                        ],
                        remediation=None,
                        error_message=None,
                    )

        raise MissingToolError(
            "gocyclo",
            install_command="go install github.com/fzipp/gocyclo/cmd/gocyclo@latest",
        )

    def _create_go_complexity_remediation(self) -> Remediation:
        """Create remediation guidance for Go complexity."""
        return Remediation(
            summary="Reduce cyclomatic complexity in Go functions",
            steps=[
                "Identify functions with complexity >15",
                "Break complex functions into smaller, focused functions",
                "Use early returns to reduce nesting",
                "Extract switch/case logic into separate functions or maps",
            ],
            tools=["gocyclo", "golangci-lint"],
            commands=[
                "go install github.com/fzipp/gocyclo/cmd/gocyclo@latest",
                "gocyclo -over 15 .",
            ],
            examples=[],
            citations=[
                Citation(
                    source="Go Community",
                    title="gocyclo - Cyclomatic Complexity for Go",
                    url="https://github.com/fzipp/gocyclo",
                    relevance="Go cyclomatic complexity analysis tool",
                )
            ],
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


class StructuredLoggingAssessor(BaseAssessor):
    """Assesses use of structured logging libraries.

    Tier 3 Important (2% weight) - Structured logs are machine-parseable
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
            default_weight=0.02,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable to any code repository."""
        return len(repository.languages) > 0

    def assess(self, repository: Repository) -> Finding:
        """Check for structured logging library usage."""
        primary = self._primary_language(repository, {"Python", "Go"})
        if primary == "Python":
            return self._assess_python_logging(repository)
        elif primary == "Go":
            return self._assess_go_logging(repository)
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

    def _assess_go_logging(self, repository: Repository) -> Finding:
        """Check for Go structured logging libraries in go.mod and source."""
        go_structured_libs = {
            "go.uber.org/zap": "zap",
            "github.com/sirupsen/logrus": "logrus",
            "github.com/rs/zerolog": "zerolog",
            "golang.org/x/exp/slog": "slog (experimental)",
        }

        found_libs = []

        module_roots = self._find_go_module_roots(repository)
        if not module_roots:
            return Finding.not_applicable(self.attribute, reason="No go.mod found")

        for root in module_roots:
            try:
                mod_content = (root / "go.mod").read_text(encoding="utf-8")
                for lib_path, lib_name in go_structured_libs.items():
                    if lib_path in mod_content:
                        found_libs.append(lib_name)
            except (OSError, UnicodeDecodeError):
                pass

        # Check for stdlib log/slog (Go 1.21+, no go.mod entry needed)
        if not found_libs:
            from ..utils.subprocess_utils import safe_subprocess_run

            try:
                result = safe_subprocess_run(
                    ["git", "ls-files", "*.go"],
                    cwd=repository.path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    for f in result.stdout.strip().split("\n"):
                        if not f or f.endswith("_test.go"):
                            continue
                        try:
                            content = (repository.path / f).read_text(encoding="utf-8")
                            if '"log/slog"' in content:
                                found_libs.append("slog (stdlib)")
                                break
                        except (OSError, UnicodeDecodeError):
                            continue
            except Exception:
                pass

        if found_libs:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="configured",
                threshold="structured logging library",
                evidence=[
                    f"Structured logging library found: {', '.join(set(found_libs))}",
                    "Checked: go.mod and source imports",
                ],
                remediation=None,
                error_message=None,
            )

        return Finding(
            attribute=self.attribute,
            status="fail",
            score=0.0,
            measured_value="not configured",
            threshold="structured logging library",
            evidence=[
                "No structured logging library found in go.mod",
                "Go stdlib log package produces unstructured output",
            ],
            remediation=self._create_go_logging_remediation(),
            error_message=None,
        )

    def _create_go_logging_remediation(self) -> Remediation:
        """Create remediation guidance for Go structured logging."""
        return Remediation(
            summary="Add structured logging library for Go",
            steps=[
                "Choose a structured logging library (slog for Go 1.21+, zap for high-performance)",
                "Configure JSON output for production",
                "Use consistent field naming across the codebase",
            ],
            tools=["slog", "zap", "zerolog"],
            commands=[
                "# Option A: Use stdlib slog (Go 1.21+)",
                '# No installation needed — import "log/slog"',
                "",
                "# Option B: Use zap",
                "go get go.uber.org/zap",
            ],
            examples=[
                """// Using Go stdlib slog (Go 1.21+)
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
logger.Info("user_login",
    slog.String("user_id", "123"),
    slog.String("ip", remoteAddr),
)
""",
            ],
            citations=[
                Citation(
                    source="Go Documentation",
                    title="log/slog package",
                    url="https://pkg.go.dev/log/slog",
                    relevance="Go stdlib structured logging (Go 1.21+)",
                ),
            ],
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
        """Check for golangci-lint configuration at root or in Go module dirs."""
        config_names = [
            ".golangci.yml",
            ".golangci.yaml",
            ".golangci.toml",
            ".golangci.json",
        ]
        search_dirs = [repository.path] + self._find_go_module_roots(repository)
        return any((d / name).exists() for d in search_dirs for name in config_names)

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
                for workflow_file in list(workflows_dir.glob("*.yml")) + list(
                    workflows_dir.glob("*.yaml")
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
