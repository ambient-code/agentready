"""Code quality assessors for complexity, file length, type annotations, and code smells."""

import ast
import configparser
import json
import logging
import os
import re
import subprocess
import tomllib
from pathlib import Path

import lizard
import radon.complexity
import yaml

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..services.scanner import MissingToolError
from ..utils.subprocess_utils import (
    safe_subprocess_run,
    safe_subprocess_run_stream,
    sanitize_subprocess_error,
)
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

        evidence = [
            f"Typed functions: {typed_functions}/{total_functions}",
            f"Coverage: {coverage_percent:.1f}%",
        ]

        strict_pts, strict_evidence = self._check_python_strict_mode(repository)
        if strict_pts > 0:
            score = min(score + strict_pts, 100.0)
            evidence.extend(strict_evidence)

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{coverage_percent:.1f}%",
            threshold="≥80%",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _check_python_strict_mode(
        self, repository: Repository
    ) -> tuple[float, list[str]]:
        """Check whether a Python type checker is configured in strict mode.

        Awards 15 bonus points if strict mode is detected in any of:
        mypy.ini, .mypy.ini, setup.cfg [mypy], pyproject.toml [tool.mypy],
        pyrightconfig.json, or pyproject.toml [tool.pyright].
        """
        import json

        # Check INI-style mypy configs
        for ini_name in ("mypy.ini", ".mypy.ini", "setup.cfg"):
            ini_path = repository.path / ini_name
            if not ini_path.exists():
                continue
            try:
                parser = configparser.ConfigParser()
                parser.read(str(ini_path), encoding="utf-8")
                if parser.has_section("mypy"):
                    strict = parser.get("mypy", "strict", fallback="").lower()
                    disallow = parser.get(
                        "mypy", "disallow_untyped_defs", fallback=""
                    ).lower()
                    if strict == "true" or disallow == "true":
                        return 15.0, [
                            f"mypy strict mode configured in {ini_name} "
                            "(prevents new type violations)"
                        ]
            except (OSError, configparser.Error):
                continue

        # Check pyproject.toml for [tool.mypy] and [tool.pyright]
        pyproject_path = repository.path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)

                mypy_cfg = data.get("tool", {}).get("mypy", {})
                if (
                    mypy_cfg.get("strict") is True
                    or mypy_cfg.get("disallow_untyped_defs") is True
                ):
                    return 15.0, [
                        "mypy strict mode configured in pyproject.toml "
                        "(prevents new type violations)"
                    ]

                pyright_cfg = data.get("tool", {}).get("pyright", {})
                if pyright_cfg.get("typeCheckingMode") == "strict":
                    return 15.0, [
                        "pyright strict mode configured in pyproject.toml "
                        "(prevents new type violations)"
                    ]
            except (OSError, tomllib.TOMLDecodeError):
                pass

        # Check pyrightconfig.json (supports JSONC comments)
        pyright_path = repository.path / "pyrightconfig.json"
        if pyright_path.exists():
            try:
                raw = pyright_path.read_text(encoding="utf-8")
                cleaned = self._strip_json_comments(raw)
                config = json.loads(cleaned)
                if config.get("typeCheckingMode") == "strict":
                    return 15.0, [
                        "pyright strict mode configured in pyrightconfig.json "
                        "(prevents new type violations)"
                    ]
            except (OSError, json.JSONDecodeError):
                pass

        return 0.0, []

    def _assess_typescript_types(self, repository: Repository) -> Finding:
        """Assess TypeScript type configuration across all tsconfig.json files.

        Supports monorepos with per-package tsconfig.json and JSONC comments.
        """
        import json

        tsconfig_files = self._find_tsconfig_files(repository)

        if not tsconfig_files:
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

        strict_count = 0
        total_count = 0
        evidence: list[str] = []

        for tsconfig_path in tsconfig_files:
            rel_path = str(tsconfig_path.relative_to(repository.path))
            total_count += 1
            try:
                raw = tsconfig_path.read_text(encoding="utf-8")
                cleaned = self._strip_json_comments(raw)
                tsconfig = json.loads(cleaned)
            except (OSError, json.JSONDecodeError) as e:
                evidence.append(f"{rel_path}: parse error ({e})")
                continue

            strict = tsconfig.get("compilerOptions", {}).get("strict", False)
            if strict:
                strict_count += 1
                evidence.append(f"{rel_path}: strict: true")
            else:
                evidence.append(f"{rel_path}: strict mode disabled")

        score = self.calculate_proportional_score(
            measured_value=(strict_count / total_count) * 100,
            threshold=100.0,
            higher_is_better=True,
        )
        status = "pass" if strict_count == total_count else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{strict_count}/{total_count} strict",
            threshold="all tsconfig.json files strict",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    @staticmethod
    def _strip_go_non_code(content: str) -> str:
        """Strip comments and string literal contents from Go source.

        Preserves line structure so line-anchored regexes still work.
        """
        out = []
        i = 0
        n = len(content)
        while i < n:
            c = content[i]

            # Block comment
            if c == "/" and i + 1 < n and content[i + 1] == "*":
                i += 2
                while i + 1 < n and not (content[i] == "*" and content[i + 1] == "/"):
                    out.append("\n" if content[i] == "\n" else " ")
                    i += 1
                out.append(" ")  # *
                i += 1
                if i < n:
                    out.append(" ")  # /
                    i += 1
                continue

            # Line comment
            if c == "/" and i + 1 < n and content[i + 1] == "/":
                i += 2
                while i < n and content[i] != "\n":
                    i += 1
                continue

            # Double-quoted string
            if c == '"':
                out.append(c)
                i += 1
                while i < n and content[i] != '"':
                    if content[i] == "\\" and i + 1 < n:
                        out.append(" ")
                        out.append(" ")
                        i += 2
                    else:
                        out.append(" ")
                        i += 1
                if i < n:
                    out.append(c)
                    i += 1
                continue

            # Raw string (backtick)
            if c == "`":
                out.append(c)
                i += 1
                while i < n and content[i] != "`":
                    out.append("\n" if content[i] == "\n" else " ")
                    i += 1
                if i < n:
                    out.append(c)
                    i += 1
                continue

            out.append(c)
            i += 1

        return "".join(out)

    @staticmethod
    def _strip_json_comments(text: str) -> str:
        """Strip // and /* */ comments from JSONC, preserving string contents."""
        out: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]

            if c == '"':
                out.append(c)
                i += 1
                while i < n and text[i] != '"':
                    if text[i] == "\\" and i + 1 < n:
                        out.append(text[i])
                        out.append(text[i + 1])
                        i += 2
                    else:
                        out.append(text[i])
                        i += 1
                if i < n:
                    out.append(text[i])
                    i += 1
                continue

            if c == "/" and i + 1 < n and text[i + 1] == "/":
                i += 2
                while i < n and text[i] != "\n":
                    i += 1
                continue

            if c == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue

            out.append(c)
            i += 1

        return "".join(out)

    def _find_tsconfig_files(self, repository: Repository) -> list:
        """Find all tsconfig.json files, excluding node_modules/vendor/testdata."""
        found = []
        for tsconfig in repository.path.rglob("tsconfig.json"):
            parts = tsconfig.parts
            if "node_modules" in parts or "vendor" in parts or "testdata" in parts:
                continue
            found.append(tsconfig)
        return sorted(found)

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
                code_content = self._strip_go_non_code(content)
                total_funcs += len(re.findall(r"^func\s+", code_content, re.MULTILINE))
                any_usage_count += len(
                    re.findall(r"\binterface\s*\{\s*\}|\bany\b", code_content)
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
            all_blocks = []
            for py_file in repository.path.rglob("*.py"):
                try:
                    code = py_file.read_text(encoding="utf-8")
                    all_blocks.extend(radon.complexity.cc_visit(code))
                except (OSError, UnicodeDecodeError, SyntaxError):
                    continue

            if not all_blocks:
                return Finding.not_applicable(
                    self.attribute, reason="No Python code to analyze"
                )

            avg_value = radon.complexity.average_complexity(all_blocks)

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
                remediation=(self._create_remediation() if status == "fail" else None),
                error_message=None,
            )

        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
            )

    def _assess_with_lizard(self, repository: Repository) -> Finding:
        """Assess complexity using lizard (multi-language)."""
        try:
            total_ccn = 0
            total_funcs = 0
            for file_info in lizard.analyze(
                [str(repository.path)], threads=os.cpu_count() or 1
            ):
                for func in file_info.function_list:
                    total_ccn += func.cyclomatic_complexity
                    total_funcs += 1

            if total_funcs == 0:
                return Finding.not_applicable(
                    self.attribute, reason="No code to analyze with lizard"
                )

            avg_ccn = total_ccn / total_funcs

            score = self.calculate_proportional_score(
                measured_value=avg_ccn,
                threshold=10.0,
                higher_is_better=False,
            )
            status = "pass" if score >= 75 else "fail"

            return Finding(
                attribute=self.attribute,
                status=status,
                score=score,
                measured_value=f"{avg_ccn:.1f}",
                threshold="<10.0",
                evidence=[f"Average cyclomatic complexity (lizard): {avg_ccn:.1f}"],
                remediation=(self._create_remediation() if status == "fail" else None),
                error_message=None,
            )

        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
            )

    def _assess_go_complexity(self, repository: Repository) -> Finding:
        """Assess Go complexity using golangci-lint config or gocyclo.

        Checks for configured complexity linters first, then falls back
        to running gocyclo directly.
        """
        # Check if golangci-lint has complexity linters configured
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
                        if config_name.endswith(".toml"):
                            parsed = tomllib.loads(content)
                        else:
                            parsed = yaml.safe_load(content) or {}
                        enabled = parsed.get("linters", {}).get("enable") or []
                        complexity_linters = {"gocyclo", "cyclop", "gocognit"}
                        if complexity_linters & set(enabled):
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
                    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError):
                        continue

        # Fallback: run gocyclo directly
        try:
            last_line = None
            with safe_subprocess_run_stream(
                ["gocyclo", "-avg", "-top", "1", str(repository.path)],
                timeout=60,
            ) as stream:
                for line in stream:
                    last_line = line

            if stream.returncode != 0:
                stderr_msg = sanitize_subprocess_error(
                    stream.stderr.strip(), repository.path
                )
                stdout_msg = sanitize_subprocess_error(
                    (last_line or "").strip(), repository.path
                )
                raise subprocess.CalledProcessError(
                    stream.returncode,
                    "gocyclo",
                    output=stdout_msg,
                    stderr=stderr_msg,
                )

            if last_line and last_line.startswith("Average:"):
                avg_value = float(last_line.split()[-1])

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
            return Finding.not_applicable(
                self.attribute, reason="No Go complexity data from gocyclo"
            )

        except FileNotFoundError:
            raise MissingToolError(
                "gocyclo",
                install_command="go install github.com/fzipp/gocyclo/cmd/gocyclo@latest",
            )
        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
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
            default_weight=0.01,
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


class LintConfigCoverageAssessor(BaseAssessor):
    """Assesses lint config coverage across correctness, standards, and security categories.

    Tier 2 Critical (2% weight) - A formatting-only lint config gives an agent
    no automated signal about correctness errors or security issues in code it
    generates. This assessor distinguishes between lint breadth and depth.

    Scoring:
    - 0/3 categories: 0 pts (fail)
    - 1/3 categories: 33 pts (fail)
    - 2/3 categories: 67 pts (fail)
    - 3/3 categories: 100 pts (pass)

    Sources checked: standalone lint config files, pre-commit hooks, CI workflow files.
    """

    # Per-language mapping of tool name → set of covered categories.
    # A tool covering multiple categories counts for all of them.
    _PYTHON_TOOLS: dict[str, set[str]] = {
        # correctness
        "mypy": {"correctness"},
        "pyright": {"correctness"},
        "pyflakes": {"correctness"},
        "pylint": {"correctness", "standards"},
        "ruff": {"correctness", "standards"},
        "flake8": {"correctness", "standards"},
        # standards only
        "black": {"standards"},
        "isort": {"standards"},
        "autopep8": {"standards"},
        "pydocstyle": {"standards"},
        "pycodestyle": {"standards"},
        # security
        "bandit": {"security"},
        "semgrep": {"security"},
        "safety": {"security"},
        "pip-audit": {"security"},
        "dlint": {"security"},
        "flake8-bandit": {"security"},
    }

    _GO_TOOLS: dict[str, set[str]] = {
        # correctness
        "errcheck": {"correctness"},
        "staticcheck": {"correctness"},
        "gosimple": {"correctness"},
        "ineffassign": {"correctness"},
        "typecheck": {"correctness"},
        "govet": {"correctness"},
        "unused": {"correctness"},
        "nilerr": {"correctness"},
        "errorlint": {"correctness"},
        "nilnil": {"correctness"},
        "exhaustive": {"correctness"},
        "unparam": {"correctness"},
        "funclen": {"correctness"},
        # standards
        "revive": {"standards"},
        "stylecheck": {"standards"},
        "gofmt": {"standards"},
        "goimports": {"standards"},
        "godot": {"standards"},
        "misspell": {"standards"},
        "whitespace": {"standards"},
        "wsl": {"standards"},
        "lll": {"standards"},
        "maintidx": {"standards"},
        "godox": {"standards"},
        "gochecknoinits": {"standards"},
        # both
        "gocritic": {"correctness", "standards"},
        # security
        "gosec": {"security"},
        "bodyclose": {"security"},
        "sqlclosecheck": {"security"},
        "rowserrcheck": {"security"},
        "noctx": {"security"},
    }

    _JS_TOOLS: dict[str, set[str]] = {
        # correctness — TypeScript-specific
        "@typescript-eslint": {"correctness"},
        "typescript-eslint": {"correctness"},
        "@typescript-eslint/recommended": {"correctness"},
        "@typescript-eslint/recommended-type-checked": {"correctness"},
        "@typescript-eslint/strict-type-checked": {"correctness"},
        # correctness + standards (ESLint core rules catch real bugs as well as style)
        "eslint:recommended": {"correctness", "standards"},
        "eslint:all": {"correctness", "standards"},
        "airbnb": {"standards"},
        "airbnb-base": {"standards"},
        "standard": {"standards"},
        "prettier": {"standards"},
        "plugin:import": {"standards"},
        "plugin:unicorn": {"standards"},
        # security
        "plugin:security": {"security"},
        "security": {"security"},
        "no-unsanitized": {"security"},
        "no-secrets": {"security"},
        "eslint-plugin-security": {"security"},
    }

    CATEGORIES = ("correctness", "standards", "security")

    @property
    def attribute_id(self) -> str:
        return "lint_config_coverage"

    @property
    def tier(self) -> int:
        return 2

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Lint Config Coverage",
            category="Code Quality",
            tier=self.tier,
            description="Lint config covers correctness, standards, and security categories",
            criteria="All three lint categories present: correctness, standards, security",
            default_weight=0.02,
        )

    def is_applicable(self, repository: Repository) -> bool:
        supported = {"Python", "Go", "JavaScript", "TypeScript"}
        return bool(set(repository.languages.keys()) & supported)

    def assess(self, repository: Repository) -> Finding:
        primary = self._primary_language(
            repository, {"Python", "Go", "JavaScript", "TypeScript"}
        )
        if primary == "Python":
            tools = self._collect_python_tools(repository)
            catalog = self._PYTHON_TOOLS
        elif primary == "Go":
            tools = self._collect_go_tools(repository)
            catalog = self._GO_TOOLS
        elif primary in ("JavaScript", "TypeScript"):
            tools = self._collect_js_tools(repository)
            catalog = self._JS_TOOLS
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Lint coverage check not implemented for {list(repository.languages.keys())}",
            )

        # Merge CI-detected tools (language-agnostic text scan)
        ci_tools = self._collect_ci_tools(repository, primary)
        tools = tools | ci_tools

        covered: set[str] = set()
        tools_by_cat: dict[str, list[str]] = {c: [] for c in self.CATEGORIES}
        for tool in tools:
            tool_lower = tool.lower()
            for catalog_tool, cats in catalog.items():
                if tool_lower == catalog_tool:
                    for cat in cats:
                        covered.add(cat)
                        tools_by_cat[cat].append(tool)

        n_covered = len(covered)
        score = self.calculate_proportional_score(n_covered, 3)

        evidence = self._build_evidence(covered, tools_by_cat, tools)

        if n_covered == 3:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value="3/3 categories",
                threshold="all 3 categories (correctness, standards, security)",
                evidence=evidence,
                remediation=None,
                error_message=None,
            )

        missing = [c for c in self.CATEGORIES if c not in covered]
        return Finding(
            attribute=self.attribute,
            status="fail",
            score=score,
            measured_value=f"{n_covered}/3 categories",
            threshold="all 3 categories (correctness, standards, security)",
            evidence=evidence,
            remediation=self._create_remediation(missing, primary),
            error_message=None,
        )

    # ------------------------------------------------------------------ #
    #  Per-language tool collection                                        #
    # ------------------------------------------------------------------ #

    def _collect_python_tools(self, repository: Repository) -> set[str]:
        tools: set[str] = set()

        # pyproject.toml — [tool.X] sections
        pyproject = repository.path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                for key, cfg in data.get("tool", {}).items():
                    if cfg:  # section must have at least one key (not just the header)
                        tools.add(key.lower())
            except (OSError, tomllib.TOMLDecodeError):
                pass

        # setup.cfg — [X] section headers
        setup_cfg = repository.path / "setup.cfg"
        if setup_cfg.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(str(setup_cfg), encoding="utf-8")
                for section in parser.sections():
                    if parser.options(section):  # section must have at least one key
                        tools.add(section.strip("[]").lower())
            except (OSError, configparser.Error):
                pass

        # Standalone config file existence → tool presence
        standalone: dict[str, str] = {
            "mypy.ini": "mypy",
            ".mypy.ini": "mypy",
            "ruff.toml": "ruff",
            ".ruff.toml": "ruff",
            ".flake8": "flake8",
            ".pylintrc": "pylint",
            "pyrightconfig.json": "pyright",
            ".bandit": "bandit",
        }
        for filename, tool_name in standalone.items():
            if (repository.path / filename).exists():
                tools.add(tool_name)

        # .pre-commit-config.yaml — hook ids
        tools |= self._collect_precommit_hooks(repository)

        return tools

    def _collect_go_tools(self, repository: Repository) -> set[str]:
        tools: set[str] = set()

        config_names = (".golangci.yml", ".golangci.yaml", ".golangci.toml")
        search_dirs = [repository.path] + self._find_go_module_roots(repository)

        for search_dir in search_dirs:
            for config_name in config_names:
                config_path = search_dir / config_name
                if not config_path.exists():
                    continue
                try:
                    raw = config_path.read_text(encoding="utf-8")
                    if config_name.endswith(".toml"):
                        parsed = tomllib.loads(raw)
                    else:
                        parsed = yaml.safe_load(raw)
                    if not isinstance(parsed, dict):
                        continue

                    linters = parsed.get("linters", {})
                    if not isinstance(linters, dict):
                        continue
                    # Explicit enable list
                    enabled = linters.get("enable") or []
                    if isinstance(enabled, list):
                        tools.update(t.lower() for t in enabled if isinstance(t, str))

                    # enable-all implies everything, treat as full coverage
                    if linters.get("enable-all"):
                        tools.update(self._GO_TOOLS.keys())
                except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError):
                    continue

        return tools

    def _collect_js_tools(self, repository: Repository) -> set[str]:
        """Collect JS/TS lint tools from ESLint configs and tsconfig."""
        tools: set[str] = set()

        # JSON-parseable ESLint configs (structural extraction)
        eslint_json_configs = [".eslintrc", ".eslintrc.json"]
        # YAML ESLint configs — parse structurally with yaml.safe_load
        eslint_yaml_configs = [".eslintrc.yaml", ".eslintrc.yml"]
        # JS/CJS/MJS configs — text matching only (cannot parse without Node.js)
        eslint_js_configs = [
            ".eslintrc.js",
            ".eslintrc.cjs",
            ".eslintrc.mjs",
            "eslint.config.js",
            "eslint.config.mjs",
            "eslint.config.cjs",
            "eslint.config.ts",
        ]

        for cfg_name in eslint_json_configs:
            cfg_path = repository.path / cfg_name
            if not cfg_path.exists():
                continue
            try:
                raw = cfg_path.read_text(encoding="utf-8")
                tools |= self._extract_eslint_tools(raw, is_json=True)
            except (OSError, UnicodeDecodeError):
                continue

        for cfg_name in eslint_yaml_configs:
            cfg_path = repository.path / cfg_name
            if not cfg_path.exists():
                continue
            try:
                raw = cfg_path.read_text(encoding="utf-8")
                data = yaml.safe_load(raw)
                if isinstance(data, dict):
                    tools |= self._extract_eslint_tools_from_dict(data)
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                continue

        for cfg_name in eslint_js_configs:
            cfg_path = repository.path / cfg_name
            if not cfg_path.exists():
                continue
            try:
                raw = cfg_path.read_text(encoding="utf-8")
                tools |= self._extract_eslint_tools(raw, is_json=False)
            except (OSError, UnicodeDecodeError):
                continue

        # package.json — eslintConfig key (structural) only; devDependencies alone
        # are insufficient — a plugin must be explicitly enabled in an ESLint config.
        pkg_json = repository.path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise json.JSONDecodeError("not a dict", "", 0)
                # eslintConfig embedded — parse structurally
                eslint_cfg = data.get("eslintConfig", {})
                if isinstance(eslint_cfg, dict) and eslint_cfg:
                    tools |= self._extract_eslint_tools_from_dict(eslint_cfg)
                # prettier key in package.json signals active prettier config
                if data.get("prettier"):
                    tools.add("prettier")
            except (OSError, json.JSONDecodeError):
                pass

        # Standalone prettier config files
        prettier_configs = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yaml",
            ".prettierrc.yml",
            ".prettierrc.js",
            ".prettierrc.cjs",
            "prettier.config.js",
            "prettier.config.cjs",
            "prettier.config.mjs",
        ]
        for cfg_name in prettier_configs:
            if (repository.path / cfg_name).exists():
                tools.add("prettier")
                break

        # tsconfig.json strict: true → correctness signal
        for tsconfig_path in self._find_tsconfig_files(repository):
            try:
                raw = tsconfig_path.read_text(encoding="utf-8")
                cleaned = self._strip_json_comments(raw)
                tsconfig = json.loads(cleaned)
                if not isinstance(tsconfig, dict):
                    continue
                compiler = tsconfig.get("compilerOptions", {})
                if not isinstance(compiler, dict):
                    continue
                if compiler.get("strict") or (
                    compiler.get("noImplicitAny") and compiler.get("strictNullChecks")
                ):
                    tools.add("@typescript-eslint")  # signals correctness tooling
            except (OSError, json.JSONDecodeError):
                continue

        # .pre-commit-config.yaml
        tools |= self._collect_precommit_hooks(repository)

        return tools

    def _find_tsconfig_files(self, repository: Repository) -> list[Path]:
        """Find all tsconfig.json files, excluding node_modules/vendor/testdata."""
        found = []
        for tsconfig in repository.path.rglob("tsconfig.json"):
            parts = tsconfig.parts
            if "node_modules" in parts or "vendor" in parts or "testdata" in parts:
                continue
            found.append(tsconfig)
        return sorted(found)

    @staticmethod
    def _strip_json_comments(text: str) -> str:
        """Strip // and /* */ comments from JSONC, preserving string contents."""
        out: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c == '"':
                out.append(c)
                i += 1
                while i < n and text[i] != '"':
                    if text[i] == "\\" and i + 1 < n:
                        out.append(text[i])
                        out.append(text[i + 1])
                        i += 2
                    else:
                        out.append(text[i])
                        i += 1
                if i < n:
                    out.append(text[i])
                    i += 1
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                i += 2
                while i < n and text[i] != "\n":
                    i += 1
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue
            out.append(c)
            i += 1
        return "".join(out)

    def _extract_eslint_tools(self, text: str, is_json: bool = False) -> set[str]:
        """Extract extends and plugins from ESLint config content.

        For JSON-based configs (.eslintrc.json, eslintConfig in package.json),
        parse structurally and walk extends/plugins arrays to avoid false
        positives from comments or unrelated text.

        For JS/CJS/MJS configs (not parseable as JSON), fall back to text
        matching against the known tool catalog — only alternative without
        running Node.js.
        """
        tools: set[str] = set()

        if is_json:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return self._extract_eslint_tools_from_dict(data)
            except (json.JSONDecodeError, AttributeError):
                pass
            # JSON parse failed or yielded non-dict — do not fall back to text
            # matching for JSON configs; comments/disabled examples would cause
            # false positives.
            return tools

        # Text matching fallback for JS/CJS/MJS configs (cannot parse without Node.js)
        for candidate in self._JS_TOOLS:
            if candidate.lower() in text.lower():
                tools.add(candidate)
        return tools

    def _extract_eslint_tools_from_dict(self, data: dict) -> set[str]:
        """Structural extraction of ESLint tools from a parsed config dict.

        Inspects extends, plugins, and rule-key namespaces. Works for both
        JSON-parsed and YAML-parsed ESLint configs.
        """
        tools: set[str] = set()
        candidates: list[str] = []

        extends = data.get("extends", [])
        if isinstance(extends, str):
            extends = [extends]
        if isinstance(extends, list):
            candidates.extend(v for v in extends if isinstance(v, str))

        plugins = data.get("plugins", [])
        if isinstance(plugins, str):
            plugins = [plugins]
        if isinstance(plugins, list):
            candidates.extend(v for v in plugins if isinstance(v, str))

        # Rule-key namespaces (e.g. "@typescript-eslint/no-unused-vars")
        rules = data.get("rules", {})
        if isinstance(rules, dict):
            for rule_key in rules:
                if "/" in rule_key:
                    candidates.append(rule_key.split("/")[0])

        joined = " ".join(candidates).lower()
        for catalog_entry in self._JS_TOOLS:
            if catalog_entry.lower() in joined:
                tools.add(catalog_entry)
        return tools

    def _collect_precommit_hooks(self, repository: Repository) -> set[str]:
        """Parse .pre-commit-config.yaml for hook ids."""
        tools: set[str] = set()
        precommit = repository.path / ".pre-commit-config.yaml"
        if not precommit.exists():
            return tools
        try:
            data = yaml.safe_load(precommit.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return tools
            repos = data.get("repos", [])
            if not isinstance(repos, list):
                return tools
            for repo_entry in repos:
                if not isinstance(repo_entry, dict):
                    continue
                hooks = repo_entry.get("hooks", [])
                if not isinstance(hooks, list):
                    continue
                for hook in hooks:
                    if not isinstance(hook, dict):
                        continue
                    hook_id = hook.get("id", "").lower()
                    if hook_id:
                        tools.add(hook_id)
        except (OSError, yaml.YAMLError):
            pass
        return tools

    def _collect_ci_tools(self, repository: Repository, language: str) -> set[str]:
        """Scan CI workflow files for lint tool invocations in run: steps.

        Parses YAML structurally and extracts only the text of `run:` step
        values, avoiding false positives from job names, comments, or
        condition strings that happen to contain a tool name.

        Falls back to full-text scan for CI files that cannot be parsed as
        YAML (e.g. Travis .travis.yml with complex anchors, or corrupted files).
        """
        ci_files: list[Path] = []

        gh_workflows = repository.path / ".github" / "workflows"
        if gh_workflows.exists():
            ci_files.extend(gh_workflows.glob("*.yml"))
            ci_files.extend(gh_workflows.glob("*.yaml"))

        for ci_path in (
            repository.path / ".gitlab-ci.yml",
            repository.path / ".circleci" / "config.yml",
            repository.path / ".travis.yml",
        ):
            if ci_path.exists():
                ci_files.append(ci_path)

        if language == "Python":
            candidates = list(self._PYTHON_TOOLS.keys())
        elif language == "Go":
            candidates = list(self._GO_TOOLS.keys())
        else:
            candidates = list(self._JS_TOOLS.keys())

        all_tools: set[str] = set()

        for ci_file in ci_files:
            try:
                raw = ci_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            run_text = self._extract_ci_run_commands(raw)
            run_lower = run_text.lower()
            for tool in candidates:
                # Use lookarounds instead of \b so @-prefixed names like
                # @typescript-eslint also match (@ is non-\w, so \b fails there).
                pattern = r"(?<!\w)" + re.escape(tool.lower()) + r"(?!\w)"
                if re.search(pattern, run_lower):
                    all_tools.add(tool)

        return all_tools

    @staticmethod
    def _extract_ci_run_commands(ci_yaml: str) -> str:
        """Extract the text of all `run:` step values from a CI YAML file.

        Walks the parsed YAML tree recursively to collect every string value
        associated with a `run` key, regardless of nesting depth or CI platform
        (GitHub Actions, GitLab CI, CircleCI). Falls back to the full raw text
        if the file cannot be parsed.
        """
        try:
            data = yaml.safe_load(ci_yaml)
        except yaml.YAMLError:
            return ci_yaml  # fallback: full text scan

        if not isinstance(data, dict):
            return ci_yaml

        run_chunks: list[str] = []

        def _walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "run":
                        if isinstance(value, str):
                            # GitHub Actions: run: "cmd"
                            run_chunks.append(value)
                        elif isinstance(value, dict):
                            # CircleCI: run: {command: "cmd", ...}
                            cmd = value.get("command", "")
                            if isinstance(cmd, str) and cmd:
                                run_chunks.append(cmd)
                            _walk(value)
                        else:
                            _walk(value)
                    elif key == "script":
                        if isinstance(value, list):
                            # GitLab CI: script: [cmd1, cmd2, ...]
                            run_chunks.extend(s for s in value if isinstance(s, str))
                        else:
                            _walk(value)
                    else:
                        _walk(value)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(data)
        if not run_chunks:
            # YAML parsed successfully but contained no run/script commands —
            # return empty rather than the raw file to avoid false positives
            # from job names, YAML keys, or other inert text.
            return ""

        # Filter lines that are pure installation or echo statements with no
        # compound operator (&&, ;, |). These mention a tool without invoking it.
        _INERT_PREFIXES = (
            "echo ",
            "pip install ",
            "pip3 install ",
            "npm install ",
            "npm ci",
            "yarn add ",
            "yarn install",
            "apt-get install ",
            "apt install ",
            "brew install ",
            "go install ",
        )
        filtered: list[str] = []
        for chunk in run_chunks:
            lines = []
            for line in chunk.splitlines():
                stripped = line.strip().lower()
                has_compound = any(op in stripped for op in ("&&", ";", "|"))
                if not has_compound and any(
                    stripped.startswith(p) for p in _INERT_PREFIXES
                ):
                    continue  # skip pure install/echo line
                lines.append(line)
            if lines:
                filtered.append("\n".join(lines))

        return "\n".join(filtered)

    # ------------------------------------------------------------------ #
    #  Evidence and remediation helpers                                    #
    # ------------------------------------------------------------------ #

    def _build_evidence(
        self,
        covered: set[str],
        tools_by_cat: dict[str, list[str]],
        all_tools: set[str],
    ) -> list[str]:
        evidence: list[str] = []
        for cat in self.CATEGORIES:
            if cat in covered:
                unique_tools = list(dict.fromkeys(tools_by_cat[cat]))[:3]
                evidence.append(
                    f"Correctness: {', '.join(unique_tools)}"
                    if cat == "correctness"
                    else (
                        f"Standards: {', '.join(unique_tools)}"
                        if cat == "standards"
                        else f"Security: {', '.join(unique_tools)}"
                    )
                )
            else:
                evidence.append(f"Missing category: {cat}")
        if all_tools:
            evidence.append(f"Tools detected: {', '.join(sorted(all_tools)[:8])}")
        return evidence

    def _create_remediation(self, missing: list[str], language: str) -> Remediation:
        steps: list[str] = []
        tools: list[str] = []
        commands: list[str] = []
        examples: list[str] = []

        if language == "Python":
            if "correctness" in missing:
                steps.append(
                    "Add mypy or pyright for type/correctness checking: "
                    "configure [tool.mypy] in pyproject.toml"
                )
                tools += ["mypy", "pyright"]
                commands += ["pip install mypy", "mypy --strict src/"]
            if "standards" in missing:
                steps.append(
                    "Add ruff for style enforcement: configure [tool.ruff] in pyproject.toml"
                )
                tools += ["ruff"]
                commands += ["pip install ruff", "ruff check ."]
            if "security" in missing:
                steps.append(
                    "Add bandit for security analysis: configure [tool.bandit] in pyproject.toml "
                    "or add bandit pre-commit hook"
                )
                tools += ["bandit", "semgrep"]
                commands += ["pip install bandit", "bandit -r src/"]
            examples.append(
                "# pyproject.toml\n"
                "[tool.mypy]\nstrict = true\n\n"
                '[tool.ruff]\nselect = ["E", "F", "S"]  # S = flake8-bandit (security)\n\n'
                '[tool.bandit]\ntargets = ["src"]\n'
            )

        elif language == "Go":
            if "correctness" in missing:
                steps.append(
                    "Enable errcheck and staticcheck in .golangci.yml linters.enable"
                )
                tools += ["golangci-lint"]
                commands += ["golangci-lint run --enable errcheck,staticcheck"]
            if "standards" in missing:
                steps.append("Enable revive or stylecheck in .golangci.yml")
                tools += ["golangci-lint"]
            if "security" in missing:
                steps.append("Enable gosec in .golangci.yml linters.enable")
                tools += ["gosec"]
                commands += ["golangci-lint run --enable gosec"]
            examples.append(
                "# .golangci.yml\nlinters:\n  enable:\n"
                "    - errcheck\n    - staticcheck\n"
                "    - revive\n    - stylecheck\n    - gosec\n"
            )

        else:  # JS/TS
            if "correctness" in missing:
                steps.append(
                    "Add @typescript-eslint/recommended-type-checked to ESLint extends"
                )
                tools += ["@typescript-eslint/eslint-plugin"]
                commands += ["npm install --save-dev @typescript-eslint/eslint-plugin"]
            if "standards" in missing:
                steps.append(
                    "Add eslint:recommended or airbnb config to ESLint extends"
                )
                tools += ["eslint"]
                commands += ["npm install --save-dev eslint"]
            if "security" in missing:
                steps.append("Add eslint-plugin-security to ESLint plugins")
                tools += ["eslint-plugin-security"]
                commands += ["npm install --save-dev eslint-plugin-security"]
            examples.append(
                '// .eslintrc.json\n{\n  "extends": [\n'
                '    "eslint:recommended",\n'
                '    "plugin:@typescript-eslint/recommended-type-checked",\n'
                '    "plugin:security/recommended"\n'
                "  ]\n}\n"
            )

        return Remediation(
            summary=f"Extend lint config to cover missing categories: {', '.join(missing)}",
            steps=steps,
            tools=tools,
            commands=commands,
            examples=examples,
            citations=[
                Citation(
                    source="agentready",
                    title="Lint Config Coverage — Issue #511",
                    url="https://github.com/ambient-code/agentready/issues/511",
                    relevance="Feature rationale and tool categorization",
                )
            ],
        )
