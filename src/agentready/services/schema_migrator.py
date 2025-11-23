"""Schema migration service for AgentReady assessment reports."""

import json
from pathlib import Path
from typing import Any


class SchemaMigrationError(Exception):
    """Raised when schema migration fails."""

    pass


class SchemaMigrator:
    """Migrates assessment reports between schema versions."""

    SUPPORTED_VERSIONS = ["1.0.0"]
    MIGRATION_PATHS = {
        # Future migrations will be added here
        # Example: ("1.0.0", "1.1.0"): migrate_1_0_to_1_1,
    }

    def __init__(self):
        """Initialize schema migrator."""
        pass

    def get_migration_path(
        self, from_version: str, to_version: str
    ) -> list[tuple[str, str]]:
        """Determine migration path from one version to another.

        Args:
            from_version: Source schema version
            to_version: Target schema version

        Returns:
            List of (from, to) version tuples representing migration steps

        Raises:
            SchemaMigrationError: If no migration path exists
        """
        if from_version == to_version:
            return []

        # For now, we only support 1.0.0
        if from_version not in self.SUPPORTED_VERSIONS:
            raise SchemaMigrationError(f"Unsupported source version: {from_version}")

        if to_version not in self.SUPPORTED_VERSIONS:
            raise SchemaMigrationError(f"Unsupported target version: {to_version}")

        # Simple direct migration for now
        migration_key = (from_version, to_version)
        if migration_key in self.MIGRATION_PATHS:
            return [migration_key]

        # No migration path found
        raise SchemaMigrationError(
            f"No migration path from {from_version} to {to_version}"
        )

    def migrate_report(
        self, report_data: dict[str, Any], to_version: str
    ) -> dict[str, Any]:
        """Migrate assessment report to target schema version.

        Args:
            report_data: Parsed JSON report data
            to_version: Target schema version

        Returns:
            Migrated report data

        Raises:
            SchemaMigrationError: If migration fails
        """
        # Extract current version
        from_version = report_data.get("schema_version")

        if not from_version:
            raise SchemaMigrationError(
                "Report missing schema_version field. "
                "Cannot determine migration path."
            )

        # Get migration path
        migration_steps = self.get_migration_path(from_version, to_version)

        if not migration_steps:
            # Already at target version
            return report_data

        # Apply migrations in sequence
        current_data = report_data.copy()
        for step_from, step_to in migration_steps:
            migration_func = self.MIGRATION_PATHS.get((step_from, step_to))
            if not migration_func:
                raise SchemaMigrationError(
                    f"Migration function not found for {step_from} -> {step_to}"
                )
            current_data = migration_func(current_data)

        return current_data

    def migrate_report_file(
        self, input_path: Path, output_path: Path, to_version: str
    ) -> None:
        """Migrate assessment report file to target schema version.

        Args:
            input_path: Path to source JSON report file
            output_path: Path to write migrated report
            to_version: Target schema version

        Raises:
            SchemaMigrationError: If migration fails
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except FileNotFoundError:
            raise SchemaMigrationError(f"Report file not found: {input_path}")
        except json.JSONDecodeError as e:
            raise SchemaMigrationError(f"Invalid JSON in report file: {e}")

        # Migrate data
        migrated_data = self.migrate_report(report_data, to_version)

        # Write output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(migrated_data, f, indent=2)

    # Migration functions for specific version pairs
    # (These will be added as new versions are released)

    @staticmethod
    def migrate_1_0_to_1_1(data: dict[str, Any]) -> dict[str, Any]:
        """Migrate from schema 1.0.0 to 1.1.0 (example for future use).

        Args:
            data: Report data in 1.0.0 format

        Returns:
            Report data in 1.1.0 format
        """
        # Example migration logic (not yet implemented)
        migrated = data.copy()
        migrated["schema_version"] = "1.1.0"

        # Add new fields with defaults
        # migrated["new_field"] = "default_value"

        return migrated
