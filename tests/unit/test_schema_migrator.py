"""Unit tests for schema migrator service."""

import json

import pytest

from agentready.services.schema_migrator import SchemaMigrationError, SchemaMigrator


@pytest.fixture
def migrator():
    """Create schema migrator instance."""
    return SchemaMigrator()


@pytest.fixture
def report_data_v1():
    """Create assessment report data in v1.0.0 format."""
    return {
        "schema_version": "1.0.0",
        "repository": {
            "name": "test-repo",
            "path": "/path/to/repo",
            "url": None,
            "branch": "main",
            "commit_hash": "a" * 40,
            "languages": {"Python": 100},
            "total_files": 10,
            "total_lines": 1000,
        },
        "timestamp": "2025-11-22T06:00:00Z",
        "overall_score": 75.0,
        "certification_level": "Gold",
        "attributes_assessed": 20,
        "attributes_skipped": 5,
        "attributes_total": 25,
        "findings": [],
        "config": None,
        "duration_seconds": 5.0,
    }


def test_migrator_initialization(migrator):
    """Test migrator initializes correctly."""
    assert migrator is not None
    assert "1.0.0" in migrator.SUPPORTED_VERSIONS


def test_get_migration_path_same_version(migrator):
    """Test migration path returns empty list for same version."""
    path = migrator.get_migration_path("1.0.0", "1.0.0")
    assert path == []


def test_get_migration_path_unsupported_source(migrator):
    """Test migration path raises error for unsupported source version."""
    with pytest.raises(SchemaMigrationError, match="Unsupported source version"):
        migrator.get_migration_path("99.0.0", "1.0.0")


def test_get_migration_path_unsupported_target(migrator):
    """Test migration path raises error for unsupported target version."""
    with pytest.raises(SchemaMigrationError, match="Unsupported target version"):
        migrator.get_migration_path("1.0.0", "99.0.0")


def test_migrate_report_same_version(migrator, report_data_v1):
    """Test migrating to same version returns original data."""
    result = migrator.migrate_report(report_data_v1, "1.0.0")
    assert result == report_data_v1


def test_migrate_report_missing_version(migrator):
    """Test migration fails when schema_version is missing."""
    report_data = {"some": "data"}
    with pytest.raises(SchemaMigrationError, match="missing schema_version"):
        migrator.migrate_report(report_data, "1.0.0")


def test_migrate_report_file(migrator, report_data_v1, tmp_path):
    """Test migrating report file."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w") as f:
        json.dump(report_data_v1, f)

    # Migrate to same version (should succeed and copy)
    migrator.migrate_report_file(input_file, output_file, "1.0.0")

    assert output_file.exists()

    with open(output_file, "r") as f:
        result = json.load(f)

    assert result["schema_version"] == "1.0.0"


def test_migrate_report_file_nonexistent(migrator, tmp_path):
    """Test migration fails for nonexistent file."""
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(SchemaMigrationError, match="not found"):
        migrator.migrate_report_file(input_file, output_file, "1.0.0")


def test_migrate_report_file_invalid_json(migrator, tmp_path):
    """Test migration fails for invalid JSON file."""
    input_file = tmp_path / "invalid.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w") as f:
        f.write("{ invalid json }")

    with pytest.raises(SchemaMigrationError, match="Invalid JSON"):
        migrator.migrate_report_file(input_file, output_file, "1.0.0")


def test_migrate_1_0_to_1_1_example(migrator):
    """Test example 1.0 to 1.1 migration function."""
    data_v1 = {"schema_version": "1.0.0", "some_field": "value"}

    # Call the example migration function directly
    result = migrator.migrate_1_0_to_1_1(data_v1)

    assert result["schema_version"] == "1.1.0"
    assert result["some_field"] == "value"


def test_no_migration_path_exists(migrator):
    """Test error when no migration path exists."""
    # For now, there are no actual migrations registered
    # This test checks that appropriate error is raised
    report_data = {"schema_version": "1.0.0"}

    # Since we only support 1.0.0 and have no migrations,
    # trying to migrate to a different (unsupported) version should fail
    with pytest.raises(SchemaMigrationError):
        migrator.migrate_report(report_data, "2.0.0")
