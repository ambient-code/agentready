"""Unit tests for dbt assessors."""

from pathlib import Path

import pytest

from agentready.assessors.dbt import (
    DbtDataTestsAssessor,
    DbtModelDocumentationAssessor,
    DbtProjectConfigAssessor,
    DbtProjectStructureAssessor,
    _find_yaml_files,
    _is_dbt_project,
    _parse_yaml_safe,
)
from agentready.models.repository import Repository

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def minimal_valid_repo(tmp_path):
    """Minimal valid dbt project."""
    fixture_dir = (
        Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "minimal_valid"
    )
    return Repository(
        path=fixture_dir,
        name="minimal_valid",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 1},
        total_files=2,
        total_lines=10,
    )


@pytest.fixture
def well_structured_repo(tmp_path):
    """Well-structured dbt project with best practices."""
    fixture_dir = (
        Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "well_structured"
    )
    return Repository(
        path=fixture_dir,
        name="well_structured",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 2},
        total_files=10,
        total_lines=50,
    )


@pytest.fixture
def missing_docs_repo(tmp_path):
    """Valid dbt project but no documentation."""
    fixture_dir = (
        Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "missing_docs"
    )
    return Repository(
        path=fixture_dir,
        name="missing_docs",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 2},
        total_files=3,
        total_lines=10,
    )


@pytest.fixture
def missing_tests_repo(tmp_path):
    """Valid dbt project but no tests."""
    fixture_dir = (
        Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "missing_tests"
    )
    return Repository(
        path=fixture_dir,
        name="missing_tests",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 1},
        total_files=2,
        total_lines=10,
    )


@pytest.fixture
def flat_structure_repo(tmp_path):
    """Valid dbt project but flat structure."""
    fixture_dir = (
        Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "flat_structure"
    )
    return Repository(
        path=fixture_dir,
        name="flat_structure",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 55},
        total_files=56,
        total_lines=100,
    )


@pytest.fixture
def non_dbt_repo(tmp_path):
    """Regular project without dbt."""
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "dbt_projects" / "non_dbt"
    return Repository(
        path=fixture_dir,
        name="non_dbt",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"SQL": 1},
        total_files=2,
        total_lines=5,
    )


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Test shared utility functions."""

    def test_is_dbt_project_true(self, minimal_valid_repo):
        """Test _is_dbt_project returns True for dbt project."""
        assert _is_dbt_project(minimal_valid_repo) is True

    def test_is_dbt_project_false(self, non_dbt_repo):
        """Test _is_dbt_project returns False for non-dbt project."""
        assert _is_dbt_project(non_dbt_repo) is False

    def test_find_yaml_files(self, well_structured_repo):
        """Test _find_yaml_files finds YAML files recursively."""
        models_dir = well_structured_repo.path / "models"
        yaml_files = _find_yaml_files(models_dir, "*schema.yml")

        assert len(yaml_files) >= 2  # At least staging and marts schema.yml
        assert all(f.suffix in [".yml", ".yaml"] for f in yaml_files)

    def test_parse_yaml_safe_valid(self, minimal_valid_repo):
        """Test _parse_yaml_safe parses valid YAML."""
        dbt_project_path = minimal_valid_repo.path / "dbt_project.yml"
        data = _parse_yaml_safe(dbt_project_path)

        assert isinstance(data, dict)
        assert data["name"] == "minimal_valid"
        assert data["config-version"] == 2

    def test_parse_yaml_safe_invalid(self, tmp_path):
        """Test _parse_yaml_safe returns empty dict for invalid YAML."""
        invalid_yaml = tmp_path / "invalid.yml"
        invalid_yaml.write_text("invalid: yaml: content: [")

        data = _parse_yaml_safe(invalid_yaml)
        assert data == {}

    def test_parse_yaml_safe_nonexistent(self, tmp_path):
        """Test _parse_yaml_safe returns empty dict for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.yml"
        data = _parse_yaml_safe(nonexistent)
        assert data == {}


# ============================================================================
# DbtProjectConfigAssessor Tests
# ============================================================================


class TestDbtProjectConfigAssessor:
    """Test DbtProjectConfigAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create assessor instance."""
        return DbtProjectConfigAssessor()

    def test_attribute_id(self, assessor):
        """Test attribute_id property."""
        assert assessor.attribute_id == "dbt_project_config"

    def test_tier(self, assessor):
        """Test tier property."""
        assert assessor.tier == 1  # Essential

    def test_is_applicable_dbt_project(self, assessor, minimal_valid_repo):
        """Test is_applicable returns True for dbt project."""
        assert assessor.is_applicable(minimal_valid_repo) is True

    def test_is_applicable_non_dbt(self, assessor, non_dbt_repo):
        """Test is_applicable returns False for non-dbt project."""
        assert assessor.is_applicable(non_dbt_repo) is False

    def test_assess_valid_minimal(self, assessor, minimal_valid_repo):
        """Test assess with minimal valid configuration."""
        finding = assessor.assess(minimal_valid_repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "name" in str(finding.evidence)
        assert "config-version" in str(finding.evidence)
        assert finding.remediation is None

    def test_assess_valid_with_version(self, assessor, well_structured_repo):
        """Test assess with dbt version specified."""
        finding = assessor.assess(well_structured_repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "require-dbt-version" in str(finding.evidence)

    def test_assess_missing_file(self, assessor, non_dbt_repo):
        """Test assess when dbt_project.yml missing."""
        finding = assessor.assess(non_dbt_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "not found" in str(finding.evidence)
        assert finding.remediation is not None

    def test_assess_invalid_yaml(self, assessor, tmp_path):
        """Test assess with invalid YAML syntax."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create invalid dbt_project.yml
        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("invalid: yaml: [")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 1},
            total_files=1,
            total_lines=10,
        )
        finding = assessor.assess(repo)

        assert finding.status == "error"
        assert "invalid YAML" in finding.error_message

    def test_assess_missing_required_fields(self, assessor, tmp_path):
        """Test assess with missing required fields."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create incomplete dbt_project.yml
        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\n")  # Missing config-version and profile

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 1},
            total_files=1,
            total_lines=10,
        )
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "missing fields" in finding.measured_value
        assert finding.remediation is not None

    def test_remediation_content(self, assessor):
        """Test remediation has all required components."""
        remediation = assessor._create_remediation()

        assert len(remediation.steps) >= 3
        assert len(remediation.tools) >= 1
        assert "dbt-core" in remediation.tools
        assert len(remediation.commands) >= 1
        assert len(remediation.examples) >= 1
        assert len(remediation.citations) >= 1


# ============================================================================
# DbtModelDocumentationAssessor Tests
# ============================================================================


class TestDbtModelDocumentationAssessor:
    """Test DbtModelDocumentationAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create assessor instance."""
        return DbtModelDocumentationAssessor()

    def test_attribute_id(self, assessor):
        """Test attribute_id property."""
        assert assessor.attribute_id == "dbt_model_documentation"

    def test_tier(self, assessor):
        """Test tier property."""
        assert assessor.tier == 1  # Essential

    def test_is_applicable_dbt_project(self, assessor, minimal_valid_repo):
        """Test is_applicable returns True for dbt project."""
        assert assessor.is_applicable(minimal_valid_repo) is True

    def test_is_applicable_non_dbt(self, assessor, non_dbt_repo):
        """Test is_applicable returns False for non-dbt project."""
        assert assessor.is_applicable(non_dbt_repo) is False

    def test_assess_well_documented(self, assessor, well_structured_repo):
        """Test assess with well-documented models."""
        finding = assessor.assess(well_structured_repo)

        assert finding.status == "pass"
        assert finding.score == 100.0  # Both models documented
        assert "100.0%" in finding.measured_value
        assert finding.remediation is None

    def test_assess_no_documentation(self, assessor, missing_docs_repo):
        """Test assess with no documentation."""
        finding = assessor.assess(missing_docs_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "0.0%" in finding.measured_value
        assert finding.remediation is not None

    def test_assess_partial_documentation(self, assessor, missing_tests_repo):
        """Test assess with partial documentation (has schema.yml but documented)."""
        finding = assessor.assess(missing_tests_repo)

        # This project has 1 model with description
        assert finding.status == "pass"
        assert finding.score == 100.0  # 1/1 = 100%

    def test_assess_no_models_directory(self, assessor, non_dbt_repo):
        """Test assess when models/ directory missing."""
        finding = assessor.assess(non_dbt_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "no models/ directory" in finding.measured_value

    def test_assess_no_sql_files(self, assessor, tmp_path):
        """Test assess when models/ exists but no SQL files."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 0},
            total_files=0,
            total_lines=0,
        )
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"
        assert "No SQL models found" in str(finding.evidence)

    def test_proportional_scoring(self, assessor, tmp_path):
        """Test proportional scoring for partial documentation."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create 10 models, document 5
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        for i in range(10):
            (models_dir / f"model_{i}.sql").write_text(f"select {i} as id")

        # Document 5 models (50% coverage)
        schema_yml = models_dir / "schema.yml"
        schema_yml.write_text("""version: 2
models:
  - name: model_0
    description: This is model zero with data
  - name: model_1
    description: This is model one with data
  - name: model_2
    description: This is model two with data
  - name: model_3
    description: This is model three with data
  - name: model_4
    description: This is model four with data
""")

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 10},
            total_files=10,
            total_lines=100,
        )
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        # 50% coverage → 50/80 * 100 = 62.5 score
        assert 60.0 <= finding.score <= 65.0

    def test_remediation_content(self, assessor):
        """Test remediation has all required components."""
        remediation = assessor._create_remediation()

        assert len(remediation.steps) >= 3
        assert len(remediation.tools) >= 1
        assert len(remediation.commands) >= 1
        assert "dbt docs generate" in str(remediation.commands)
        assert len(remediation.examples) >= 1
        assert len(remediation.citations) >= 1


# ============================================================================
# DbtDataTestsAssessor Tests
# ============================================================================


class TestDbtDataTestsAssessor:
    """Test DbtDataTestsAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create assessor instance."""
        return DbtDataTestsAssessor()

    def test_attribute_id(self, assessor):
        """Test attribute_id property."""
        assert assessor.attribute_id == "dbt_data_tests"

    def test_tier(self, assessor):
        """Test tier property."""
        assert assessor.tier == 2  # Critical

    def test_is_applicable_dbt_project(self, assessor, minimal_valid_repo):
        """Test is_applicable returns True for dbt project."""
        assert assessor.is_applicable(minimal_valid_repo) is True

    def test_is_applicable_non_dbt(self, assessor, non_dbt_repo):
        """Test is_applicable returns False for non-dbt project."""
        assert assessor.is_applicable(non_dbt_repo) is False

    def test_assess_with_tests(self, assessor, well_structured_repo):
        """Test assess with models having PK tests."""
        finding = assessor.assess(well_structured_repo)

        assert finding.status == "pass"
        assert finding.score == 100.0  # Both models have unique+not_null
        assert "100.0%" in finding.measured_value
        assert "Singular tests" in str(finding.evidence)  # Has tests/ directory
        assert finding.remediation is None

    def test_assess_no_tests(self, assessor, missing_tests_repo):
        """Test assess with no tests."""
        finding = assessor.assess(missing_tests_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "0.0%" in finding.measured_value
        assert finding.remediation is not None

    def test_assess_no_models_directory(self, assessor, non_dbt_repo):
        """Test assess when models/ directory missing."""
        finding = assessor.assess(non_dbt_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "no models/ directory" in finding.measured_value

    def test_assess_no_sql_files(self, assessor, tmp_path):
        """Test assess when models/ exists but no SQL files."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 0},
            total_files=0,
            total_lines=0,
        )
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"
        assert "No SQL models found" in str(finding.evidence)

    def test_proportional_scoring(self, assessor, tmp_path):
        """Test proportional scoring for partial test coverage."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create 10 models, test 5 (50% coverage)
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        for i in range(10):
            (models_dir / f"model_{i}.sql").write_text(f"select {i} as id")

        # Test 5 models (50% coverage → 62.5 score → fail)
        schema_yml = models_dir / "schema.yml"
        models_yaml = []
        for i in range(5):
            models_yaml.append(f"""  - name: model_{i}
    columns:
      - name: id
        tests:
          - unique
          - not_null
""")

        schema_yml.write_text("version: 2\nmodels:\n" + "\n".join(models_yaml))

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 10},
            total_files=10,
            total_lines=100,
        )
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        # 50% coverage → 50/80 * 100 = 62.5 score
        assert 60.0 <= finding.score <= 65.0

    def test_remediation_content(self, assessor):
        """Test remediation has all required components."""
        remediation = assessor._create_remediation()

        assert len(remediation.steps) >= 3
        assert len(remediation.tools) >= 1
        assert "dbt-core" in remediation.tools
        assert len(remediation.commands) >= 1
        assert "dbt test" in str(remediation.commands)
        assert len(remediation.examples) >= 1
        assert len(remediation.citations) >= 1


# ============================================================================
# DbtProjectStructureAssessor Tests
# ============================================================================


class TestDbtProjectStructureAssessor:
    """Test DbtProjectStructureAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create assessor instance."""
        return DbtProjectStructureAssessor()

    def test_attribute_id(self, assessor):
        """Test attribute_id property."""
        assert assessor.attribute_id == "dbt_project_structure"

    def test_tier(self, assessor):
        """Test tier property."""
        assert assessor.tier == 2  # Critical

    def test_is_applicable_dbt_project(self, assessor, minimal_valid_repo):
        """Test is_applicable returns True for dbt project."""
        assert assessor.is_applicable(minimal_valid_repo) is True

    def test_is_applicable_non_dbt(self, assessor, non_dbt_repo):
        """Test is_applicable returns False for non-dbt project."""
        assert assessor.is_applicable(non_dbt_repo) is False

    def test_assess_well_structured(self, assessor, well_structured_repo):
        """Test assess with well-structured project."""
        finding = assessor.assess(well_structured_repo)

        assert finding.status == "pass"
        assert finding.score == 100.0  # Has staging, marts, tests, macros
        assert "staging/ layer: ✓" in str(finding.evidence)
        assert "marts/ layer: ✓" in str(finding.evidence)
        assert "tests/ directory: ✓" in str(finding.evidence)
        assert "macros/ directory: ✓" in str(finding.evidence)
        assert finding.remediation is None

    def test_assess_flat_structure(self, assessor, flat_structure_repo):
        """Test assess with flat structure (50+ files in root)."""
        finding = assessor.assess(flat_structure_repo)

        assert finding.status == "fail"
        assert finding.score < 75.0
        assert "Flat structure" in str(finding.evidence)
        assert finding.remediation is not None

    def test_assess_minimal_structure(self, assessor, minimal_valid_repo):
        """Test assess with minimal structure (just models/)."""
        finding = assessor.assess(minimal_valid_repo)

        assert finding.status == "fail"
        # Only has models/ (not flat), missing staging/marts/tests/macros
        # Score: 40 (not flat) + 0 (no layers) + 0 (no tests/macros) = 40
        assert finding.score == 40.0

    def test_assess_no_models_directory(self, assessor, non_dbt_repo):
        """Test assess when models/ directory missing."""
        finding = assessor.assess(non_dbt_repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "no models/ directory" in finding.measured_value

    def test_assess_partial_structure(self, assessor, tmp_path):
        """Test assess with partial structure (only staging, no marts)."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "staging").mkdir()
        (models_dir / "staging" / "model.sql").write_text("select 1")

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 1},
            total_files=1,
            total_lines=10,
        )
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        # Score: 40 (not flat) + 15 (staging only) + 0 (no tests/macros) = 55
        assert finding.score == 55.0

    def test_composite_scoring(self, assessor, tmp_path):
        """Test composite scoring components."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create staging and marts
        (models_dir / "staging").mkdir()
        (models_dir / "marts").mkdir()
        (models_dir / "staging" / "model.sql").write_text("select 1")
        (models_dir / "marts" / "model.sql").write_text("select 1")

        # Create tests directory
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test.sql").write_text("select 1")

        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.write_text("name: 'test'\nconfig-version: 2\nprofile: 'default'")

        repo = Repository(
            path=tmp_path,
            name="test",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"SQL": 2},
            total_files=3,
            total_lines=10,
        )
        finding = assessor.assess(repo)

        # Score: 40 (not flat) + 30 (staging+marts) + 15 (tests only) = 85
        assert finding.status == "pass"
        assert finding.score == 85.0

    def test_remediation_content(self, assessor):
        """Test remediation has all required components."""
        remediation = assessor._create_remediation()

        assert len(remediation.steps) >= 3
        assert len(remediation.tools) >= 1
        assert len(remediation.commands) >= 0  # May not have commands
        assert len(remediation.examples) >= 1
        assert "staging/" in remediation.examples[0]
        assert "marts/" in remediation.examples[0]
        assert len(remediation.citations) >= 1
