"""Simplified version of config loading with cleaner error handling."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from agentready.models import Config


def load_config(config_path: Path) -> Config:
    """Load configuration from YAML file with Pydantic validation.

    SIMPLIFIED VERSION - Reduces 60+ lines of error mapping to 20 lines
    while maintaining all user-friendly error messages.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated Config instance

    Raises:
        ValidationError: If YAML data doesn't match expected schema
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("Config must be a dict")

        return Config.from_yaml_dict(data)
    except ValidationError as e:
        # Simplified error mapping using a dictionary approach
        errors_list = e.errors()
        error = errors_list[0] if errors_list else {}
        field = error.get("loc", [""])[0]
        error_type = error.get("type", "")

        # Map common validation errors to user-friendly messages
        # Extract extra keys helper
        def get_extra_keys(errors):
            for error in errors:
                if error.get("type") == "extra_forbidden":
                    return [str(key) for key in error.get("loc", [])]
            return []

        extra_keys = get_extra_keys(errors_list)
        error_messages = {
            (
                "extra_forbidden",
                None,
            ): lambda: f"Unknown config keys: {', '.join(extra_keys)}",
            ("dict_type", "weights"): lambda: "'weights' must be a dict",
            (
                "float_parsing",
                "weights",
            ): lambda: "'weights' values must be positive numbers",
            (
                "value_error",
                "weights",
            ): lambda: "'weights' values must be positive numbers",
            (
                "list_type",
                "excluded_attributes",
            ): lambda: "'excluded_attributes' must be a list",
            ("str_type", "report_theme"): lambda: "'report_theme' must be str",
        }

        # Special handling for output_dir sensitive directory errors
        if field == "output_dir":
            error_msg = str(error.get("msg", ""))
            if "sensitive" in error_msg.lower():
                raise ValueError(error_msg.replace("Value error, ", ""))
            raise ValueError(f"Invalid output_dir: {error_msg}")

        # Look up error message
        key = (error_type, field) if field else (error_type, None)
        if key in error_messages:
            raise ValueError(error_messages[key]())

        # Generic fallback
        field_path = " → ".join(str(x) for x in error.get("loc", []))
        raise ValueError(
            f"Validation failed for '{field_path}': {error.get('msg', 'Invalid value')}"
        )


def _get_extra_keys(errors: list) -> list:
    """Extract unknown keys from validation errors."""
    return [
        err.get("loc", [""])[0]
        for err in errors
        if err.get("type") == "extra_forbidden"
    ]
