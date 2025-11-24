"""JSON reporter for generating machine-readable assessment reports."""

import json
from pathlib import Path

from ..models.assessment import Assessment
from .base import BaseReporter


class JSONReporter(BaseReporter):
    """Generates JSON reports from individual assessments.

    Features:
    - Schema versioning for backwards compatibility
    - Complete assessment data including findings and remediation
    - Machine-readable for automation and tooling
    - ISO 8601 timestamps for unambiguous dates
    """

    def generate(self, assessment: Assessment, output_path: Path) -> Path:
        """Generate JSON report from assessment data.

        Args:
            assessment: Complete assessment with findings
            output_path: Path where JSON file should be saved

        Returns:
            Path to generated JSON file

        Raises:
            IOError: If JSON cannot be written
        """
        # Serialize to JSON string
        json_content = json.dumps(assessment.to_dict(), indent=2, default=str)

        # Write to file using base class method
        return self._write_file(json_content, output_path)
