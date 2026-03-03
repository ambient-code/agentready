"""Schema validation service for AgentReady assessment reports."""

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema  # noqa: F401
    from jsonschema import Draft7Validator, validators

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""

    pass


class SchemaValidator:
    """Validates assessment reports against JSON schemas."""

    SUPPORTED_VERSIONS = ["1.0.0"]
    DEFAULT_VERSION = "1.0.0"

    def __init__(self):
        """Initialize schema validator."""
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema library not found. Install with: pip install jsonschema"
            )

        # Get path to bundled schemas
        self.schemas_dir = Path(__file__).parent.parent / "data" / "schemas"

    def get_schema_path(self, version: str) -> Path:
        """Get path to schema file for given version.

        Args:
            version: Schema version (e.g., "1.0.0")

        Returns:
            Path to schema JSON file

        Raises:
            FileNotFoundError: If schema for version doesn't exist
        """
        # For now, use the schema from specs/ directory as we haven't moved it yet
        # In production, this would use self.schemas_dir / f"v{version}"
        specs_schema = (
            Path(__file__).parent.parent.parent.parent
            / "specs"
            / "001-agentready-scorer"
            / "contracts"
            / "assessment-schema.json"
        )

        if specs_schema.exists():
            return specs_schema

        raise FileNotFoundError(f"Schema for version {version} not found")

    def validate_report(
        self, report_data: dict[str, Any], strict: bool = True
    ) -> tuple[bool, list[str]]:
        """Validate assessment report against its schema version.

        Args:
            report_data: Parsed JSON report data
            strict: If True, fail on unknown properties; if False, allow them

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Extract schema version from report
        schema_version = report_data.get("schema_version")

        if not schema_version:
            return (
                False,
                ["Missing required field: schema_version"],
            )

        # Check if version is supported
        if schema_version not in self.SUPPORTED_VERSIONS:
            return (
                False,
                [
                    f"Unsupported schema version: {schema_version}. "
                    f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}"
                ],
            )

        # Load schema for this version
        try:
            schema_path = self.get_schema_path(schema_version)
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except FileNotFoundError as e:
            return (False, [str(e)])
        except json.JSONDecodeError as e:
            return (False, [f"Invalid schema JSON: {e}"])

        # Validate against schema
        errors = []
        try:
            if strict:
                # Use default validator (doesn't allow additional properties by default)
                validator = Draft7Validator(schema)
            else:
                # Allow additional properties
                def set_additional_properties(validator_class):
                    """Extend validator to allow additional properties."""
                    all_validators = dict(validator_class.VALIDATORS)

                    def additional_properties(validator, aP, instance, schema):
                        # Don't check additionalProperties
                        return

                    all_validators["additionalProperties"] = additional_properties
                    return validators.create(
                        meta_schema=validator_class.META_SCHEMA,
                        validators=all_validators,
                    )

                LenientValidator = set_additional_properties(Draft7Validator)
                validator = LenientValidator(schema)

            # Collect all validation errors
            for error in validator.iter_errors(report_data):
                error_path = " -> ".join(str(p) for p in error.path)
                if error_path:
                    errors.append(f"{error_path}: {error.message}")
                else:
                    errors.append(error.message)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        # Cross-field validation: JSON Schema draft-07 cannot enforce these constraints
        # Fix for #309: ensure cross-field consistency after relaxing schema constraints
        cross_field_errors = self._validate_cross_field_constraints(report_data)
        errors.extend(cross_field_errors)

        return (len(errors) == 0, errors)

    def _validate_cross_field_constraints(
        self, report_data: dict[str, Any]
    ) -> list[str]:
        """Validate cross-field constraints that JSON Schema cannot express.

        These constraints are documented in specs/001-agentready-scorer/data-model.md
        but cannot be enforced by JSON Schema draft-07.

        Args:
            report_data: Parsed JSON report data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Constraint 1: len(findings) == attributes_total
        findings = report_data.get("findings", [])
        attributes_total = report_data.get("attributes_total", 0)

        if len(findings) != attributes_total:
            errors.append(
                f"findings count ({len(findings)}) must equal "
                f"attributes_total ({attributes_total})"
            )

        # Constraint 2: attributes_assessed + attributes_skipped == attributes_total
        # Note: attributes_skipped is the canonical key, attributes_not_assessed is deprecated
        attributes_assessed = report_data.get("attributes_assessed", 0)
        attributes_skipped = report_data.get(
            "attributes_skipped", report_data.get("attributes_not_assessed", 0)
        )

        if attributes_assessed + attributes_skipped != attributes_total:
            errors.append(
                f"attributes_assessed ({attributes_assessed}) + "
                f"attributes_skipped ({attributes_skipped}) must equal "
                f"attributes_total ({attributes_total})"
            )

        return errors

    def validate_report_file(
        self, report_path: Path, strict: bool = True
    ) -> tuple[bool, list[str]]:
        """Validate assessment report file.

        Args:
            report_path: Path to JSON report file
            strict: If True, fail on unknown properties; if False, allow them

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except FileNotFoundError:
            return (False, [f"Report file not found: {report_path}"])
        except json.JSONDecodeError as e:
            return (False, [f"Invalid JSON in report file: {e}"])

        return self.validate_report(report_data, strict=strict)
