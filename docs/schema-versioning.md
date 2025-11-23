# Report Schema Versioning

**Version**: 1.0.0
**Last Updated**: 2025-11-22
**Status**: Implemented

---

## Overview

AgentReady assessment reports now include formal schema versioning to ensure backwards compatibility and enable schema evolution. All reports include a `schema_version` field that follows semantic versioning (`MAJOR.MINOR.PATCH`).

**Current Schema Version**: `1.0.0`

---

## Features

### 1. Schema Version Field

Every assessment report includes a `schema_version` field:

```json
{
  "schema_version": "1.0.0",
  "metadata": { ... },
  "repository": { ... },
  ...
}
```

### 2. Schema Validation

Validate assessment reports against their schema version:

```bash
# Validate report with strict checking
agentready validate-report assessment-20251122-061500.json

# Validate with lenient mode (allow extra fields)
agentready validate-report --no-strict assessment-20251122-061500.json
```

**Features**:

- JSON Schema Draft 7 validation
- Automatic version detection
- Strict/lenient validation modes
- Detailed error messages

### 3. Schema Migration

Migrate reports between schema versions:

```bash
# Migrate report to version 2.0.0
agentready migrate-report assessment.json --to 2.0.0

# Specify custom output path
agentready migrate-report old-report.json --to 2.0.0 --output new-report.json
```

**Features**:

- Automatic migration path resolution
- Multi-step migrations
- Data transformation
- Validation after migration

---

## Semantic Versioning Strategy

Schema versions follow semantic versioning:

### MAJOR version (X.0.0)

**Breaking changes** - Incompatible schema modifications:

- Removing required fields
- Changing field types
- Renaming fields
- Changing validation rules (stricter)

**Example**: Removing `attributes_skipped` field

### MINOR version (1.X.0)

**Backward-compatible additions** - New optional features:

- Adding optional fields
- Adding new enum values
- Relaxing validation rules

**Example**: Adding optional `ai_suggestions` field

### PATCH version (1.0.X)

**Non-functional changes** - No schema modifications:

- Documentation updates
- Example clarifications
- Bug fixes in descriptions

**Example**: Clarifying field descriptions

---

## Schema Files

Schemas are stored in `specs/001-agentready-scorer/contracts/`:

### assessment-schema.json

JSON Schema for assessment reports (Draft 7)

**Location**: `specs/001-agentready-scorer/contracts/assessment-schema.json`

**Usage**:

```python
from agentready.services.schema_validator import SchemaValidator

validator = SchemaValidator()
is_valid, errors = validator.validate_report(report_data)
```

### report-html-schema.md

HTML report structure specification

**Location**: `specs/001-agentready-scorer/contracts/report-html-schema.md`

Defines:

- HTML document structure
- Required sections
- Interactivity requirements
- Self-contained design

### report-markdown-schema.md

Markdown report format specification

**Location**: `specs/001-agentready-scorer/contracts/report-markdown-schema.md`

Defines:

- GitHub-Flavored Markdown format
- Section requirements
- Table formatting
- Evidence presentation

---

## API Reference

### SchemaValidator

Validates assessment reports against JSON schemas.

```python
from agentready.services.schema_validator import SchemaValidator

validator = SchemaValidator()

# Validate report data
is_valid, errors = validator.validate_report(report_data)

# Validate report file
is_valid, errors = validator.validate_report_file(report_path)

# Lenient validation (allow extra fields)
is_valid, errors = validator.validate_report(report_data, strict=False)
```

**Methods**:

- `validate_report(report_data, strict=True)` → `(bool, list[str])`
- `validate_report_file(report_path, strict=True)` → `(bool, list[str])`
- `get_schema_path(version)` → `Path`

**Attributes**:

- `SUPPORTED_VERSIONS` - List of supported schema versions
- `DEFAULT_VERSION` - Default schema version (`"1.0.0"`)

### SchemaMigrator

Migrates assessment reports between schema versions.

```python
from agentready.services.schema_migrator import SchemaMigrator

migrator = SchemaMigrator()

# Migrate report data
migrated_data = migrator.migrate_report(report_data, to_version="2.0.0")

# Migrate report file
migrator.migrate_report_file(input_path, output_path, to_version="2.0.0")

# Check migration path
steps = migrator.get_migration_path(from_version="1.0.0", to_version="2.0.0")
```

**Methods**:

- `migrate_report(report_data, to_version)` → `dict`
- `migrate_report_file(input_path, output_path, to_version)` → `None`
- `get_migration_path(from_version, to_version)` → `list[tuple[str, str]]`

**Attributes**:

- `SUPPORTED_VERSIONS` - List of supported schema versions
- `MIGRATION_PATHS` - Dictionary of migration functions

---

## CLI Commands

### validate-report

Validate assessment report against its schema version.

```bash
agentready validate-report [OPTIONS] REPORT
```

**Arguments**:

- `REPORT` - Path to JSON assessment report file

**Options**:

- `--strict` / `--no-strict` - Strict validation mode (default: strict)

**Examples**:

```bash
# Strict validation
agentready validate-report assessment-20251122.json

# Lenient validation
agentready validate-report --no-strict assessment-20251122.json
```

**Exit Codes**:

- `0` - Report is valid
- `1` - Validation failed

### migrate-report

Migrate assessment report to a different schema version.

```bash
agentready migrate-report [OPTIONS] INPUT_REPORT
```

**Arguments**:

- `INPUT_REPORT` - Path to source JSON assessment report file

**Options**:

- `--from VERSION` - Source schema version (auto-detected if not specified)
- `--to VERSION` - Target schema version (required)
- `--output PATH` / `-o PATH` - Output file path (default: auto-generated)

**Examples**:

```bash
# Migrate to version 2.0.0
agentready migrate-report assessment.json --to 2.0.0

# Custom output path
agentready migrate-report old.json --to 2.0.0 --output new.json

# Explicit source version
agentready migrate-report old.json --from 1.0.0 --to 2.0.0
```

**Exit Codes**:

- `0` - Migration successful
- `1` - Migration failed

---

## Migration Guide

### Adding a New Schema Version

1. **Create Migration Function**

```python
# In src/agentready/services/schema_migrator.py

@staticmethod
def migrate_1_0_to_2_0(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate from schema 1.0.0 to 2.0.0."""
    migrated = data.copy()
    migrated["schema_version"] = "2.0.0"

    # Add new required fields with defaults
    migrated["new_field"] = "default_value"

    # Transform existing fields
    if "old_field" in migrated:
        migrated["new_field_name"] = migrated.pop("old_field")

    return migrated
```

2. **Register Migration**

```python
# In SchemaMigrator.__init__()
MIGRATION_PATHS = {
    ("1.0.0", "2.0.0"): migrate_1_0_to_2_0,
}
```

3. **Update Supported Versions**

```python
SUPPORTED_VERSIONS = ["1.0.0", "2.0.0"]
```

4. **Create New Schema File**

Copy and modify `assessment-schema.json`:

```bash
cp specs/001-agentready-scorer/contracts/assessment-schema.json \
   specs/001-agentready-scorer/contracts/assessment-schema-v2.0.0.json
```

Update schema file with changes.

5. **Write Tests**

```python
def test_migrate_1_0_to_2_0(migrator):
    data_v1 = {"schema_version": "1.0.0", ...}

    result = migrator.migrate_report(data_v1, "2.0.0")

    assert result["schema_version"] == "2.0.0"
    assert "new_field" in result
```

6. **Update Documentation**

Update this document with new version details.

---

## Backwards Compatibility

### Reading Old Reports

AgentReady can read and validate reports from any supported schema version:

```bash
# Validate old report
agentready validate-report old-assessment-v1.0.0.json
# ✅ Report is valid! (schema version: 1.0.0)
```

### Writing New Reports

All new assessments use the current schema version:

```bash
agentready assess .
# Generates report with schema_version: "1.0.0"
```

### Migration Strategy

When breaking changes are introduced:

1. **Add migration path** from old version to new version
2. **Support old versions** for validation (read-only)
3. **Document breaking changes** in release notes
4. **Provide migration command** for users

---

## Testing

### Running Tests

```bash
# All schema tests
pytest tests/unit/test_schema_validator.py tests/unit/test_schema_migrator.py

# Integration tests
pytest tests/integration/test_schema_commands.py

# With coverage
pytest --cov=agentready.services tests/unit/test_schema_*.py
```

### Test Coverage

**Unit Tests**:

- `test_schema_validator.py` - 14 test cases
- `test_schema_migrator.py` - 10 test cases

**Integration Tests**:

- `test_schema_commands.py` - 8 test cases

**Total**: 32 test cases covering:

- Validation (strict/lenient)
- Migration (single/multi-step)
- Error handling
- CLI interface
- File I/O

---

## Dependencies

Schema versioning requires:

- **jsonschema** >= 4.17.0 (for validation)

Install with:

```bash
pip install jsonschema
# or
uv pip install jsonschema
```

---

## Future Enhancements

### Planned Features (v2.0)

1. **Multi-step migrations** - Automatic chaining (1.0 → 1.1 → 2.0)
2. **Validation caching** - Cache validation results for performance
3. **Schema registry** - Centralized schema version management
4. **Web-based validator** - Validate reports in browser
5. **Automatic migration on load** - Migrate on-the-fly when loading old reports

### Proposed Schema Changes

See `BACKLOG.md` for proposed schema enhancements:

- Add `ai_suggestions` field (v1.1.0)
- Add `historical_trends` field (v1.1.0)
- Restructure `findings` for nested attributes (v2.0.0)

---

## Troubleshooting

### "jsonschema not installed"

**Solution**: Install jsonschema

```bash
pip install jsonschema
```

### "Unsupported schema version"

**Solution**: Migrate report to supported version

```bash
agentready migrate-report old-report.json --to 1.0.0
```

### "Validation failed: missing required field"

**Solution**: Report may be corrupted or incomplete

1. Check report file is valid JSON
2. Verify report was generated by AgentReady
3. Try lenient validation: `--no-strict`

### "No migration path found"

**Solution**: Multi-step migration not yet implemented

1. Check `SUPPORTED_VERSIONS` in `SchemaMigrator`
2. Manually chain migrations if needed
3. File issue for requested migration path

---

## References

- **JSON Schema**: <https://json-schema.org/>
- **Semantic Versioning**: <https://semver.org/>
- **Assessment Schema**: `specs/001-agentready-scorer/contracts/assessment-schema.json`
- **Test Suite**: `tests/unit/test_schema_*.py`

---

**Maintained by**: AgentReady Team
**Last Updated**: 2025-11-22
**Schema Version**: 1.0.0
