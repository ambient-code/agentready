"""dbt (data build tool) SQL repository assessors.

Evaluates dbt projects against core best practices for AI-assisted development.
Covers project configuration, documentation, testing, and structure.
"""

from pathlib import Path

import yaml

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor

# ============================================================================
# Shared Utility Functions
# ============================================================================


def _is_dbt_project(repository: Repository) -> bool:
    """Check if repository is a dbt project.

    Args:
        repository: Repository entity

    Returns:
        True if dbt_project.yml exists at repository root
    """
    return (repository.path / "dbt_project.yml").exists()


def _find_yaml_files(directory: Path, pattern: str = "*.yml") -> list[Path]:
    """Find YAML files matching pattern recursively.

    Args:
        directory: Directory to search
        pattern: Glob pattern (default: "*.yml")

    Returns:
        List of matching .yml and .yaml file paths
    """
    yml_files = list(directory.rglob(pattern))
    yaml_files = list(directory.rglob(pattern.replace("yml", "yaml")))
    return yml_files + yaml_files


def _parse_yaml_safe(path: Path) -> dict:
    """Parse YAML file with error handling.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content as dict, or empty dict on error
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ============================================================================
# Tier 1 Essential Assessors (20% total weight)
# ============================================================================


class DbtProjectConfigAssessor(BaseAssessor):
    """Assesses dbt_project.yml configuration validity.

    Tier 1 Essential (10% weight) - Without valid configuration, dbt won't run.
    """

    @property
    def attribute_id(self) -> str:
        return "dbt_project_config"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="dbt Project Configuration",
            category="dbt SQL Projects",
            tier=self.tier,
            description="Valid dbt_project.yml with required fields",
            criteria="dbt_project.yml exists with name, config-version, profile",
            default_weight=0.10,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable only to dbt projects."""
        return _is_dbt_project(repository)

    def assess(self, repository: Repository) -> Finding:
        """Check for valid dbt_project.yml configuration.

        Pass criteria:
        - dbt_project.yml exists at repository root
        - Contains required fields: name, config-version, profile
        - Has model-paths configured (default: ["models"])

        Scoring: Binary (100 if valid, 0 if missing/invalid)
        """
        dbt_project_path = repository.path / "dbt_project.yml"

        # Check file exists
        if not dbt_project_path.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="valid dbt_project.yml",
                evidence=["dbt_project.yml not found at repository root"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Parse YAML
        config = _parse_yaml_safe(dbt_project_path)

        if not config:
            return Finding.error(
                self.attribute,
                reason="Could not parse dbt_project.yml (invalid YAML syntax)",
            )

        # Check required fields
        required_fields = {
            "name": config.get("name"),
            "config-version": config.get("config-version"),
            "profile": config.get("profile"),
        }

        missing_fields = [
            field for field, value in required_fields.items() if not value
        ]

        # Check optional but recommended fields
        has_model_paths = bool(config.get("model-paths"))
        has_dbt_version = bool(config.get("require-dbt-version"))

        if missing_fields:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value=f"missing fields: {', '.join(missing_fields)}",
                threshold="all required fields present",
                evidence=[
                    "dbt_project.yml found but missing required fields:",
                    *[f"  - {field}: ✗" for field in missing_fields],
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Valid configuration
        evidence = [
            "dbt_project.yml found with all required fields:",
            f"  - name: {config.get('name')}",
            f"  - config-version: {config.get('config-version')}",
            f"  - profile: {config.get('profile')}",
        ]

        if has_model_paths:
            evidence.append(f"  - model-paths: {config.get('model-paths')}")

        if has_dbt_version:
            evidence.append(
                f"  - require-dbt-version: {config.get('require-dbt-version')} (reproducibility)"
            )

        return Finding(
            attribute=self.attribute,
            status="pass",
            score=100.0,
            measured_value="valid configuration",
            threshold="all required fields present",
            evidence=evidence,
            remediation=None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for invalid dbt_project.yml."""
        return Remediation(
            summary="Create valid dbt_project.yml with required fields",
            steps=[
                "Create dbt_project.yml in repository root",
                "Add required fields: name, config-version, profile",
                "Configure model-paths (recommended: ['models'])",
                "Add require-dbt-version for reproducibility",
                "Run 'dbt debug' to validate configuration",
            ],
            tools=["dbt-core"],
            commands=[
                "dbt init <project_name>  # Create new dbt project",
                "dbt debug  # Validate dbt_project.yml configuration",
            ],
            examples=["""# Minimal valid dbt_project.yml
name: 'my_dbt_project'
config-version: 2
profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

# Reproducibility (recommended)
require-dbt-version: ">=1.0.0"

# Model configuration
models:
  my_dbt_project:
    materialized: view"""],
            citations=[
                Citation(
                    source="dbt Labs Documentation",
                    title="dbt_project.yml Reference",
                    url="https://docs.getdbt.com/reference/dbt_project.yml",
                    relevance="Official dbt configuration reference",
                )
            ],
        )


class DbtModelDocumentationAssessor(BaseAssessor):
    """Assesses dbt model documentation coverage.

    Tier 1 Essential (10% weight) - Critical for AI understanding model purpose and lineage.
    """

    @property
    def attribute_id(self) -> str:
        return "dbt_model_documentation"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="dbt Model Documentation",
            category="dbt SQL Projects",
            tier=self.tier,
            description="Model descriptions in schema YAML files",
            criteria="≥80% of models have descriptions in schema.yml",
            default_weight=0.10,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable only to dbt projects."""
        return _is_dbt_project(repository)

    def assess(self, repository: Repository) -> Finding:
        """Check dbt model documentation coverage.

        Pass criteria:
        - schema.yml or _models.yml files exist in models/ subdirectories
        - Models have descriptions (not empty/placeholder text)
        - ≥80% of models documented

        Scoring: Proportional
        - 100% if ≥80% models documented
        - 50% if ≥50% models documented
        - 0% if <25% models documented
        """
        models_dir = repository.path / "models"

        if not models_dir.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no models/ directory",
                threshold="≥80% models documented",
                evidence=["models/ directory not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Count total SQL models
        sql_files = list(models_dir.rglob("*.sql"))
        total_models = len(sql_files)

        if total_models == 0:
            return Finding.not_applicable(
                self.attribute, reason="No SQL models found in models/"
            )

        # Find and parse schema YAML files (any .yml/.yaml file in models/)
        # dbt supports multiple naming conventions: schema.yml, _models.yml, or one file per model
        schema_files = _find_yaml_files(models_dir, "*.yml")

        # Extract documented model names
        documented_models = set()
        placeholder_texts = {"todo", "tbd", "fixme", "placeholder", "description"}

        for schema_file in schema_files:
            schema_data = _parse_yaml_safe(schema_file)

            # Extract models with descriptions
            models_list = schema_data.get("models", [])
            for model in models_list:
                if not isinstance(model, dict):
                    continue

                model_name = model.get("name", "")
                description = model.get("description", "").strip().lower()

                # Check if description is meaningful (not empty or placeholder)
                if description and not any(
                    placeholder in description for placeholder in placeholder_texts
                ):
                    documented_models.add(model_name)

        documented_count = len(documented_models)
        coverage_percent = (
            (documented_count / total_models) * 100 if total_models > 0 else 0
        )

        # Calculate proportional score
        score = self.calculate_proportional_score(
            measured_value=coverage_percent,
            threshold=80.0,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        evidence = [
            f"Documented models: {documented_count}/{total_models}",
            f"Coverage: {coverage_percent:.1f}%",
            f"Schema files found: {len(schema_files)}",
        ]

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

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing model documentation."""
        return Remediation(
            summary="Add descriptions to schema.yml files for each model",
            steps=[
                "Create or update schema.yml files in models/ subdirectories",
                "Add description field for each model explaining its purpose",
                "Include column descriptions for important fields",
                "Document data lineage and transformations",
                "Run 'dbt docs generate' to validate documentation",
            ],
            tools=["dbt-core", "dbt-codegen (optional)"],
            commands=[
                "dbt docs generate  # Generate documentation site",
                "dbt docs serve  # View documentation locally",
            ],
            examples=["""# models/staging/schema.yml
version: 2

models:
  - name: stg_customers
    description: >
      Staging table for customer data from the raw CRM system.
      Includes basic cleaning and standardization of customer records.
    columns:
      - name: customer_id
        description: Unique identifier for each customer
        tests:
          - unique
          - not_null
      - name: customer_name
        description: Full name of the customer
      - name: created_at
        description: Timestamp when customer record was created"""],
            citations=[
                Citation(
                    source="dbt Labs Documentation",
                    title="dbt Documentation Guide",
                    url="https://docs.getdbt.com/docs/collaborate/documentation",
                    relevance="Best practices for documenting dbt models",
                )
            ],
        )


# ============================================================================
# Tier 2 Critical Assessors (6% total weight)
# ============================================================================


class DbtDataTestsAssessor(BaseAssessor):
    """Assesses dbt data test coverage.

    Tier 2 Critical (3% weight) - Validates data quality, prevents breaking changes.
    """

    @property
    def attribute_id(self) -> str:
        return "dbt_data_tests"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="dbt Data Tests",
            category="dbt SQL Projects",
            tier=self.tier,
            description="Generic tests on model primary keys",
            criteria="≥80% of models have unique/not_null tests on primary key",
            default_weight=0.03,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable only to dbt projects."""
        return _is_dbt_project(repository)

    def assess(self, repository: Repository) -> Finding:
        """Check dbt data test coverage.

        Pass criteria:
        - Generic tests configured in schema YAML files
        - Every model has unique + not_null tests on primary key
        - Singular tests in tests/ directory (bonus)

        Scoring: Proportional
        - Count models with PK tests vs total models
        - 100% if ≥80% coverage, 50% if ≥50%, 0% if <25%
        """
        models_dir = repository.path / "models"

        if not models_dir.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no models/ directory",
                threshold="≥80% models with PK tests",
                evidence=["models/ directory not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Count total SQL models
        sql_files = list(models_dir.rglob("*.sql"))
        total_models = len(sql_files)

        if total_models == 0:
            return Finding.not_applicable(
                self.attribute, reason="No SQL models found in models/"
            )

        # Find and parse schema YAML files (any .yml/.yaml file in models/)
        # dbt supports multiple naming conventions: schema.yml, _models.yml, or one file per model
        schema_files = _find_yaml_files(models_dir, "*.yml")

        # Extract models with PK tests (unique + not_null)
        models_with_pk_tests = set()

        for schema_file in schema_files:
            schema_data = _parse_yaml_safe(schema_file)

            models_list = schema_data.get("models", [])
            for model in models_list:
                if not isinstance(model, dict):
                    continue

                model_name = model.get("name", "")
                columns = model.get("columns", [])

                # Check if any column has both unique and not_null tests
                for column in columns:
                    if not isinstance(column, dict):
                        continue

                    tests = column.get("tests", [])

                    # Tests can be strings or dicts
                    test_names = set()
                    for test in tests:
                        if isinstance(test, str):
                            test_names.add(test)
                        elif isinstance(test, dict):
                            # Extract test name from dict keys
                            test_names.update(test.keys())

                    # Check for unique and not_null tests
                    has_unique = "unique" in test_names
                    has_not_null = "not_null" in test_names

                    if has_unique and has_not_null:
                        models_with_pk_tests.add(model_name)
                        break  # Found PK tests for this model

        tested_count = len(models_with_pk_tests)
        coverage_percent = (
            (tested_count / total_models) * 100 if total_models > 0 else 0
        )

        # Check for singular tests (bonus)
        tests_dir = repository.path / "tests"
        singular_tests = list(tests_dir.rglob("*.sql")) if tests_dir.exists() else []

        # Calculate proportional score
        score = self.calculate_proportional_score(
            measured_value=coverage_percent,
            threshold=80.0,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        evidence = [
            f"Models with PK tests: {tested_count}/{total_models}",
            f"Coverage: {coverage_percent:.1f}%",
            f"Schema files found: {len(schema_files)}",
        ]

        if singular_tests:
            evidence.append(f"Singular tests: {len(singular_tests)} (bonus)")

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

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing data tests."""
        return Remediation(
            summary="Add unique/not_null tests to schema.yml for model primary keys",
            steps=[
                "Identify primary key columns for each model",
                "Add tests block to schema.yml with unique and not_null tests",
                "Add relationship tests for foreign keys (recommended)",
                "Create singular tests for complex business logic",
                "Run 'dbt test' to validate all tests pass",
            ],
            tools=["dbt-core", "dbt-utils", "dbt-expectations"],
            commands=[
                "dbt test  # Run all tests",
                "dbt test --select <model>  # Test specific model",
                "dbt test --select test_type:generic  # Run generic tests only",
            ],
            examples=["""# models/staging/schema.yml
version: 2

models:
  - name: stg_orders
    description: Staging table for order data
    columns:
      - name: order_id
        description: Unique identifier for each order
        tests:
          - unique
          - not_null
      - name: customer_id
        description: Foreign key to customers table
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
      - name: order_total
        description: Total order amount
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0"""],
            citations=[
                Citation(
                    source="dbt Labs Documentation",
                    title="dbt Data Tests Guide",
                    url="https://docs.getdbt.com/docs/build/data-tests",
                    relevance="Comprehensive guide to dbt testing",
                )
            ],
        )


class DbtProjectStructureAssessor(BaseAssessor):
    """Assesses dbt project directory structure.

    Tier 2 Critical (3% weight) - Helps AI navigate staging/marts layers and understand data flow.
    """

    @property
    def attribute_id(self) -> str:
        return "dbt_project_structure"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="dbt Project Structure",
            category="dbt SQL Projects",
            tier=self.tier,
            description="Organized staging/marts directory structure",
            criteria="models/ with staging/ and marts/ subdirectories",
            default_weight=0.03,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable only to dbt projects."""
        return _is_dbt_project(repository)

    def assess(self, repository: Repository) -> Finding:
        """Check dbt project structure.

        Pass criteria:
        - models/ directory exists
        - Recommended subdirectories: staging/, marts/
        - Optional: intermediate/, tests/, macros/
        - Avoid flat models/ with 50+ files

        Scoring: Proportional composite
        - 40% - Has models/ with subdirectories (not flat)
        - 30% - Has staging/ and marts/ layers
        - 30% - Has tests/ or macros/ directories
        """
        models_dir = repository.path / "models"

        if not models_dir.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no models/ directory",
                threshold="organized structure",
                evidence=["models/ directory not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Check for flat structure (50+ files in root models/)
        root_sql_files = list(models_dir.glob("*.sql"))
        is_flat = len(root_sql_files) >= 50

        # Check for recommended subdirectories
        has_staging = (models_dir / "staging").exists()
        has_marts = (models_dir / "marts").exists()
        has_intermediate = (models_dir / "intermediate").exists()

        # Check for supporting directories
        has_tests = (repository.path / "tests").exists()
        has_macros = (repository.path / "macros").exists()

        # Calculate composite score
        structure_score = 0.0

        # Component 1: Not flat (40%)
        if not is_flat:
            structure_score += 40.0

        # Component 2: Has staging and marts (30%)
        if has_staging and has_marts:
            structure_score += 30.0
        elif has_staging or has_marts:
            structure_score += 15.0  # Partial credit

        # Component 3: Has tests or macros (30%)
        if has_tests and has_macros:
            structure_score += 30.0
        elif has_tests or has_macros:
            structure_score += 15.0  # Partial credit

        status = "pass" if structure_score >= 75 else "fail"

        evidence = [
            f"Structure score: {structure_score:.0f}/100",
            "  - models/ directory: ✓",
            f"  - staging/ layer: {'✓' if has_staging else '✗'}",
            f"  - marts/ layer: {'✓' if has_marts else '✗'}",
        ]

        if has_intermediate:
            evidence.append("  - intermediate/ layer: ✓ (bonus)")

        evidence.append(f"  - tests/ directory: {'✓' if has_tests else '✗'}")
        evidence.append(f"  - macros/ directory: {'✓' if has_macros else '✗'}")

        if is_flat:
            evidence.append(
                f"  - ⚠ Flat structure: {len(root_sql_files)} files in models/ root"
            )

        return Finding(
            attribute=self.attribute,
            status=status,
            score=structure_score,
            measured_value=f"{structure_score:.0f}/100",
            threshold="≥75/100",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for poor project structure."""
        return Remediation(
            summary="Organize models into staging/, intermediate/, and marts/ layers",
            steps=[
                "Create staging/ subdirectory for raw source transformations",
                "Create marts/ subdirectory for business-facing analytics models",
                "Optionally create intermediate/ for intermediate transformations",
                "Create tests/ directory for singular tests",
                "Create macros/ directory for reusable SQL logic",
                "Move existing models into appropriate subdirectories",
                "Update model refs() to reflect new structure",
            ],
            tools=["dbt-core"],
            commands=[
                "# Manually reorganize directory structure",
                "# Update model references: ref('staging/stg_customers')",
            ],
            examples=["""# Recommended dbt project structure:
my_dbt_project/
├── dbt_project.yml
├── models/
│   ├── staging/           # Source system transformations
│   │   ├── _staging.yml   # Source configurations
│   │   ├── schema.yml     # Model documentation
│   │   ├── stg_customers.sql
│   │   └── stg_orders.sql
│   ├── intermediate/      # Intermediate transformations (optional)
│   │   ├── schema.yml
│   │   └── int_order_items.sql
│   └── marts/             # Business-facing analytics models
│       ├── core/          # Core business entities
│       │   ├── schema.yml
│       │   ├── dim_customers.sql
│       │   └── fct_orders.sql
│       └── marketing/     # Department-specific models
│           ├── schema.yml
│           └── customer_ltv.sql
├── tests/                 # Singular tests
│   └── assert_positive_order_totals.sql
├── macros/                # Reusable SQL logic
│   └── cents_to_dollars.sql
├── seeds/                 # CSV reference data
└── analyses/              # Ad-hoc analyses"""],
            citations=[
                Citation(
                    source="dbt Labs Best Practices",
                    title="How we structure our dbt projects",
                    url="https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview",
                    relevance="Official guide for organizing dbt projects",
                )
            ],
        )
