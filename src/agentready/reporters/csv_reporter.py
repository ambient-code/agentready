"""CSV reporter for generating tabular assessment reports.

SECURITY: Implements CSV formula injection prevention (CWE-1236).
"""

import csv
from pathlib import Path
from typing import Any

from ..models.batch_assessment import BatchAssessment


class CSVReporter:
    """Generates CSV/TSV summary reports for batch assessments.

    SECURITY REQUIREMENT: Must escape CSV formula injection characters
    (=, +, -, @, tab, newline) to prevent malicious payloads from executing
    in spreadsheet applications like Excel.

    References:
    - OWASP: https://owasp.org/www-community/attacks/CSV_Injection
    - CWE-1236: Improper Neutralization of Formula Elements in a CSV File
    """

    # SECURITY: Characters that trigger formula execution in spreadsheet apps
    FORMULA_CHARS = {"=", "+", "-", "@", "\t", "\r"}

    @staticmethod
    def sanitize_csv_field(value: Any) -> str:
        """Escape fields that could be interpreted as formulas.

        SECURITY: Prevents CSV injection (CWE-1236) by prefixing
        formula-triggering characters with a single quote. This causes
        spreadsheet applications to treat the value as literal text.

        Args:
            value: Any value to be written to CSV

        Returns:
            Sanitized string safe for CSV output

        Examples:
            >>> CSVReporter.sanitize_csv_field("=1+1")
            "'=1+1"
            >>> CSVReporter.sanitize_csv_field("normal text")
            "normal text"
            >>> CSVReporter.sanitize_csv_field(None)
            ""
        """
        if value is None:
            return ""

        str_value = str(value)

        # Prefix formula-triggering fields with single quote
        if str_value and str_value[0] in CSVReporter.FORMULA_CHARS:
            return f"'{str_value}"

        return str_value

    def generate(
        self, batch_assessment: BatchAssessment, output_path: Path, delimiter: str = ","
    ) -> Path:
        """Generate CSV with one row per repository.

        Columns:
        - repo_url: Repository URL or path
        - repo_name: Repository name
        - overall_score: Numeric score (0-100)
        - certification_level: Bronze/Silver/Gold/Platinum/Needs Improvement
        - primary_language: Primary detected language
        - timestamp: Assessment timestamp (ISO 8601)
        - duration_seconds: Time taken to assess
        - cached: Whether result came from cache

        Args:
            batch_assessment: Complete batch assessment with results
            output_path: Path where CSV file should be saved
            delimiter: Field delimiter (default: comma, use tab for TSV)

        Returns:
            Path to generated CSV file

        Raises:
            IOError: If CSV cannot be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            # Define columns
            fieldnames = [
                "repo_url",
                "repo_name",
                "overall_score",
                "certification_level",
                "primary_language",
                "timestamp",
                "duration_seconds",
                "cached",
                "status",
                "error_type",
                "error_message",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()

            # Write successful assessments
            for result in batch_assessment.results:
                if result.is_success():
                    assessment = result.assessment
                    # SECURITY: Sanitize all string fields
                    row = {
                        "repo_url": self.sanitize_csv_field(result.repository_url),
                        "repo_name": self.sanitize_csv_field(
                            assessment.repository.name
                        ),
                        "overall_score": assessment.overall_score,
                        "certification_level": self.sanitize_csv_field(
                            assessment.certification_level
                        ),
                        "primary_language": self.sanitize_csv_field(
                            assessment.repository.primary_language
                        ),
                        "timestamp": assessment.timestamp.isoformat(),
                        "duration_seconds": result.duration_seconds,
                        "cached": result.cached,
                        "status": "success",
                        "error_type": "",
                        "error_message": "",
                    }
                    writer.writerow(row)

            # Write failed assessments
            for result in batch_assessment.results:
                if not result.is_success():
                    # SECURITY: Sanitize all string fields
                    row = {
                        "repo_url": self.sanitize_csv_field(result.repository_url),
                        "repo_name": "",
                        "overall_score": 0,
                        "certification_level": "",
                        "primary_language": "",
                        "timestamp": "",
                        "duration_seconds": result.duration_seconds,
                        "cached": False,
                        "status": "failed",
                        "error_type": self.sanitize_csv_field(result.error_type),
                        "error_message": self.sanitize_csv_field(result.error),
                    }
                    writer.writerow(row)

        return output_path
