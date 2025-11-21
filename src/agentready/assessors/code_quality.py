"""Code quality assessors for complexity, file length, type annotations, and code smells."""

import subprocess

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..services.scanner import MissingToolError
from .base import BaseAssessor


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
        """Assess Python type annotations using file inspection."""
        # Simple heuristic: count functions with/without type hints
        try:
            result = subprocess.run(
                ["git", "ls-files", "*.py"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            python_files = [f for f in result.stdout.strip().split("\n") if f]
        except (subprocess.SubprocessError, FileNotFoundError):
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
                    for line in f:
                        line = line.strip()
                        if line.startswith("def ") and "(" in line:
                            total_functions += 1
                            # Check for type hints (-> in signature)
                            if "->" in line or ":" in line.split("(")[1]:
                                typed_functions += 1
            except (OSError, UnicodeDecodeError):
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
            result = subprocess.run(
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

        except MissingToolError:
            raise  # Re-raise to be caught by Scanner
        except Exception as e:
            return Finding.error(
                self.attribute, reason=f"Complexity analysis failed: {str(e)}"
            )

    def _assess_with_lizard(self, repository: Repository) -> Finding:
        """Assess complexity using lizard (multi-language)."""
        try:
            result = subprocess.run(
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
