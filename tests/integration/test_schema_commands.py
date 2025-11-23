"""Integration tests for schema CLI commands."""

import json

import pytest
from click.testing import CliRunner

from agentready.cli.main import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_report(tmp_path):
    """Create a sample assessment report file."""
    report_data = {
        "schema_version": "1.0.0",
        "metadata": None,
        "repository": {
            "name": "test-repo",
            "path": "/test/repo",
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
        "findings": [
            {
                "attribute": {
                    "id": f"attr_{i}",
                    "name": f"Attribute {i}",
                    "category": "Testing",
                    "tier": 1,
                    "description": "Test",
                    "criteria": "Test",
                    "default_weight": 0.04,
                },
                "status": "pass" if i < 20 else "skipped",
                "score": 100.0 if i < 20 else None,
                "measured_value": "100%",
                "threshold": "80%",
                "evidence": ["Test"],
                "remediation": None,
                "error_message": None,
            }
            for i in range(25)
        ],
        "config": None,
        "duration_seconds": 5.0,
        "discovered_skills": [],
    }

    report_file = tmp_path / "test-report.json"
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    return report_file


def test_validate_report_valid(runner, sample_report):
    """Test validate-report command with valid report."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    result = runner.invoke(cli, ["validate-report", str(sample_report)])

    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_report_nonexistent(runner, tmp_path):
    """Test validate-report command with nonexistent file."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    nonexistent = tmp_path / "nonexistent.json"
    result = runner.invoke(cli, ["validate-report", str(nonexistent)])

    # Click handles file existence differently
    # Exit code might be 2 (UsageError) or other non-zero
    assert result.exit_code != 0


def test_validate_report_invalid_json(runner, tmp_path):
    """Test validate-report command with invalid JSON."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    invalid_file = tmp_path / "invalid.json"
    with open(invalid_file, "w") as f:
        f.write("{ invalid }")

    result = runner.invoke(cli, ["validate-report", str(invalid_file)])

    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "error" in result.output.lower()


def test_validate_report_no_strict(runner, sample_report):
    """Test validate-report with --no-strict option."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    result = runner.invoke(cli, ["validate-report", "--no-strict", str(sample_report)])

    assert result.exit_code == 0


def test_migrate_report_same_version(runner, sample_report, tmp_path):
    """Test migrate-report command to same version."""
    output_file = tmp_path / "migrated.json"

    result = runner.invoke(
        cli,
        [
            "migrate-report",
            str(sample_report),
            "--to",
            "1.0.0",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "successful" in result.output.lower()


def test_migrate_report_default_output(runner, sample_report):
    """Test migrate-report with default output path."""
    result = runner.invoke(cli, ["migrate-report", str(sample_report), "--to", "1.0.0"])

    assert result.exit_code == 0

    # Check that output file was created with expected name
    expected_output = sample_report.parent / "test-report-migrated-v1.0.0.json"
    assert expected_output.exists()

    # Cleanup
    expected_output.unlink()


def test_migrate_report_unsupported_version(runner, sample_report):
    """Test migrate-report with unsupported target version."""
    result = runner.invoke(
        cli, ["migrate-report", str(sample_report), "--to", "99.0.0"]
    )

    assert result.exit_code != 0
    assert "unsupported" in result.output.lower() or "error" in result.output.lower()


def test_validate_then_migrate_workflow(runner, sample_report, tmp_path):
    """Test full workflow: validate, migrate, validate again."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    # Step 1: Validate original
    result = runner.invoke(cli, ["validate-report", str(sample_report)])
    assert result.exit_code == 0

    # Step 2: Migrate to same version
    output_file = tmp_path / "migrated.json"
    result = runner.invoke(
        cli,
        [
            "migrate-report",
            str(sample_report),
            "--to",
            "1.0.0",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0

    # Step 3: Validate migrated report
    result = runner.invoke(cli, ["validate-report", str(output_file)])
    assert result.exit_code == 0
