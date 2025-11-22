"""Structure assessors for project layout and separation of concerns."""


from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class StandardLayoutAssessor(BaseAssessor):
    """Assesses standard project layout patterns.

    Tier 1 Essential (10% weight) - Standard layouts help AI navigate code.
    """

    @property
    def attribute_id(self) -> str:
        return "standard_layout"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Standard Project Layouts",
            category="Repository Structure",
            tier=self.tier,
            description="Follows standard project structure for language",
            criteria="Standard directories (src/, tests/, docs/) present",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for standard project layout directories.

        Expected patterns:
        - Python: src/, tests/, docs/
        - JavaScript: src/, test/, docs/
        - Java: src/main/java, src/test/java
        """
        # Check for common standard directories
        standard_dirs = {
            "src": repository.path / "src",
        }

        # Check for tests directory (either tests/ or test/)
        tests_path = repository.path / "tests"
        if not tests_path.exists():
            tests_path = repository.path / "test"
        standard_dirs["tests"] = tests_path

        found_dirs = sum(1 for d in standard_dirs.values() if d.exists())
        required_dirs = len(standard_dirs)

        score = self.calculate_proportional_score(
            measured_value=found_dirs,
            threshold=required_dirs,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        evidence = [
            f"Found {found_dirs}/{required_dirs} standard directories",
            f"src/: {'✓' if (repository.path / 'src').exists() else '✗'}",
            f"tests/: {'✓' if (repository.path / 'tests').exists() or (repository.path / 'test').exists() else '✗'}",
        ]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{found_dirs}/{required_dirs} directories",
            threshold=f"{required_dirs}/{required_dirs} directories",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for standard layout."""
        return Remediation(
            summary="Organize code into standard directories (src/, tests/, docs/)",
            steps=[
                "Create src/ directory for source code",
                "Create tests/ directory for test files",
                "Create docs/ directory for documentation",
                "Move source code into src/",
                "Move tests into tests/",
            ],
            tools=[],
            commands=[
                "mkdir -p src tests docs",
                "# Move source files to src/",
                "# Move test files to tests/",
            ],
            examples=[],
            citations=[
                Citation(
                    source="Python Packaging Authority",
                    title="Python Project Structure",
                    url="https://packaging.python.org/en/latest/tutorials/packaging-projects/",
                    relevance="Standard Python project layout",
                )
            ],
        )
