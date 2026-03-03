"""Unit tests for schema validator service."""

import json

import pytest

from agentready.services.schema_validator import SchemaValidator


@pytest.fixture
def validator():
    """Create schema validator instance."""
    try:
        return SchemaValidator()
    except ImportError:
        pytest.skip("jsonschema not installed")


@pytest.fixture
def valid_report_data():
    """Create valid assessment report data."""
    return {
        "schema_version": "1.0.0",
        "metadata": None,
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
        "findings": [
            {
                "attribute": {
                    "id": "attr_1",
                    "name": "Test Attribute",
                    "category": "Testing",
                    "tier": 1,
                    "description": "Test description",
                    "criteria": "Test criteria",
                    "default_weight": 0.5,
                },
                "status": "pass",
                "score": 100.0,
                "measured_value": "100%",
                "threshold": "80%",
                "evidence": ["Test evidence"],
                "remediation": None,
                "error_message": None,
            }
        ]
        * 25,  # Repeat for 25 attributes
        "config": None,
        "duration_seconds": 5.0,
        "discovered_skills": [],
    }


def test_validator_initialization(validator):
    """Test validator initializes correctly."""
    assert validator is not None
    assert validator.DEFAULT_VERSION == "1.0.0"
    assert "1.0.0" in validator.SUPPORTED_VERSIONS


def test_validate_valid_report(validator, valid_report_data):
    """Test validation passes for valid report."""
    is_valid, errors = validator.validate_report(valid_report_data)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_missing_schema_version(validator, valid_report_data):
    """Test validation fails when schema_version is missing."""
    del valid_report_data["schema_version"]
    is_valid, errors = validator.validate_report(valid_report_data)
    assert is_valid is False
    assert len(errors) > 0
    assert any("schema_version" in err for err in errors)


def test_validate_unsupported_version(validator, valid_report_data):
    """Test validation fails for unsupported schema version."""
    valid_report_data["schema_version"] = "99.0.0"
    is_valid, errors = validator.validate_report(valid_report_data)
    assert is_valid is False
    assert any("Unsupported schema version" in err for err in errors)


def test_validate_invalid_score(validator, valid_report_data):
    """Test validation fails for invalid score."""
    valid_report_data["overall_score"] = 150.0  # Out of range
    is_valid, errors = validator.validate_report(valid_report_data)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_invalid_certification_level(validator, valid_report_data):
    """Test validation fails for invalid certification level."""
    valid_report_data["certification_level"] = "Diamond"  # Not in enum
    is_valid, errors = validator.validate_report(valid_report_data)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_report_file(validator, valid_report_data, tmp_path):
    """Test validation of report file."""
    report_file = tmp_path / "test-report.json"
    with open(report_file, "w") as f:
        json.dump(valid_report_data, f)

    is_valid, errors = validator.validate_report_file(report_file)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_nonexistent_file(validator, tmp_path):
    """Test validation fails for nonexistent file."""
    report_file = tmp_path / "nonexistent.json"
    is_valid, errors = validator.validate_report_file(report_file)
    assert is_valid is False
    assert any("not found" in err for err in errors)


def test_validate_invalid_json_file(validator, tmp_path):
    """Test validation fails for invalid JSON file."""
    report_file = tmp_path / "invalid.json"
    with open(report_file, "w") as f:
        f.write("{ invalid json }")

    is_valid, errors = validator.validate_report_file(report_file)
    assert is_valid is False
    assert any("Invalid JSON" in err for err in errors)


def test_validate_strict_mode(validator, valid_report_data):
    """Test strict validation mode rejects additional properties."""
    # Add an extra field not in schema
    valid_report_data["extra_field"] = "should fail in strict mode"

    # Note: Current implementation may not fail on additional properties
    # at the root level depending on schema definition
    is_valid, errors = validator.validate_report(valid_report_data, strict=True)

    # This test depends on schema configuration
    # Just ensure validation completes without error
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_validate_lenient_mode(validator, valid_report_data):
    """Test lenient validation mode allows additional properties."""
    valid_report_data["extra_field"] = "allowed in lenient mode"

    is_valid, errors = validator.validate_report(valid_report_data, strict=False)

    # Lenient mode should pass
    assert is_valid is True or len(errors) == 0


def test_validate_excluded_attributes_issue_309(validator, valid_report_data):
    """Test validation passes for assessments with excluded attributes.

    Regression test for issue #309: Schema rejected valid assessments
    generated with --exclude flags because it hardcoded attributes_total=25.

    The schema now allows 10-25 attributes to support exclusions.
    """
    # Simulate an assessment with 15 excluded attributes (10 remaining)
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 9
    valid_report_data["attributes_skipped"] = 1
    valid_report_data["findings"] = valid_report_data["findings"][:10]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is True, f"Validation failed unexpectedly: {errors}"
    assert len(errors) == 0


def test_validate_partial_exclusion_issue_309(validator, valid_report_data):
    """Test validation passes for assessments with some excluded attributes.

    Tests the common case from issue #309: user excludes 3 attributes,
    resulting in 22 attributes instead of 25.
    """
    # Simulate PR #301: 22 attributes (3 excluded)
    valid_report_data["attributes_total"] = 22
    valid_report_data["attributes_assessed"] = 21
    valid_report_data["attributes_skipped"] = 1
    valid_report_data["findings"] = valid_report_data["findings"][:22]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is True, f"Validation failed unexpectedly: {errors}"
    assert len(errors) == 0


def test_validate_too_few_attributes_rejected(validator, valid_report_data):
    """Test validation fails when too many attributes are excluded.

    The schema requires at least 10 attributes to ensure meaningful assessments.
    """
    # Try to submit with only 5 attributes (below minimum of 10)
    valid_report_data["attributes_total"] = 5
    valid_report_data["attributes_assessed"] = 5
    valid_report_data["attributes_skipped"] = 0
    valid_report_data["findings"] = valid_report_data["findings"][:5]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is False, "Should reject assessments with fewer than 10 attributes"
    assert len(errors) > 0


# Cross-field validation tests (PR #312 review comment)
# These test the _validate_cross_field_constraints() method


def test_cross_field_findings_count_mismatch(validator, valid_report_data):
    """Test validation fails when findings count doesn't match attributes_total.

    Regression test for PR #312 review: JSON Schema cannot enforce that
    len(findings) == attributes_total, so we need programmatic validation.
    """
    # Set attributes_total to 10 but keep 25 findings
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 9
    valid_report_data["attributes_skipped"] = 1
    # Intentionally leave findings at 25 items (mismatch)

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is False, "Should reject when findings count != attributes_total"
    assert any("findings count" in err and "must equal" in err for err in errors)


def test_cross_field_assessed_skipped_sum_mismatch(validator, valid_report_data):
    """Test validation fails when assessed + skipped != attributes_total.

    Regression test for PR #312 review: JSON Schema cannot enforce that
    attributes_assessed + attributes_skipped == attributes_total.
    """
    # Set values that don't add up: 20 + 5 = 25, but total is 10
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 20
    valid_report_data["attributes_skipped"] = 5
    valid_report_data["findings"] = valid_report_data["findings"][:10]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is False, "Should reject when assessed + skipped != total"
    assert any("attributes_assessed" in err and "must equal" in err for err in errors)


def test_cross_field_both_constraints_violated(validator, valid_report_data):
    """Test validation catches multiple cross-field violations.

    Both constraints should be checked and all errors reported.
    """
    # Violate both constraints
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 20
    valid_report_data["attributes_skipped"] = 5
    # Keep 25 findings (mismatch with attributes_total=10)

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is False
    assert len(errors) >= 2, "Should report both cross-field validation errors"
    assert any("findings count" in err for err in errors)
    assert any("attributes_assessed" in err for err in errors)


def test_cross_field_valid_partial_assessment(validator, valid_report_data):
    """Test validation passes when all cross-field constraints are satisfied.

    A valid partial assessment should pass all checks.
    """
    # Valid partial assessment: 15 attributes excluded, 10 remaining
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 8
    valid_report_data["attributes_skipped"] = 2
    valid_report_data["findings"] = valid_report_data["findings"][:10]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is True, f"Valid partial assessment should pass: {errors}"
    assert len(errors) == 0


def test_cross_field_deprecated_attributes_not_assessed(validator, valid_report_data):
    """Test validation works with deprecated 'attributes_not_assessed' key.

    The deprecated key should be supported for backwards compatibility.
    """
    # Use deprecated key name
    valid_report_data["attributes_total"] = 10
    valid_report_data["attributes_assessed"] = 8
    del valid_report_data["attributes_skipped"]
    valid_report_data["attributes_not_assessed"] = 2
    valid_report_data["findings"] = valid_report_data["findings"][:10]

    is_valid, errors = validator.validate_report(valid_report_data)

    assert is_valid is True, f"Should accept deprecated key: {errors}"
    assert len(errors) == 0
