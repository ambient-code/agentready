"""Unit tests for CSV reporter with security controls."""

import csv
from datetime import datetime
from pathlib import Path

import pytest

from src.agentready.models.assessment import Assessment
from src.agentready.models.batch_assessment import (
    BatchAssessment,
    BatchSummary,
    RepositoryResult,
)
from src.agentready.models.repository import Repository
from src.agentready.reporters.csv_reporter import CSVReporter


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create temporary CSV file for testing."""
    return tmp_path / "test_report.csv"


@pytest.fixture
def temp_tsv_file(tmp_path):
    """Create temporary TSV file for testing."""
    return tmp_path / "test_report.tsv"


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    return Repository(
        path=Path("/test/repo"),
        name="test-repo",
        branch="main",
        commit_hash="abc123def456",
        primary_language="Python",
        languages={"Python": 10},
        total_files=100,
        total_lines=5000,
    )


@pytest.fixture
def mock_assessment(mock_repository):
    """Create a mock assessment for testing."""
    return Assessment(
        repository=mock_repository,
        timestamp=datetime(2025, 1, 22, 14, 30, 22),
        overall_score=85.5,
        certification_level="Gold",
        attributes_assessed=20,
        attributes_not_assessed=5,
        attributes_total=25,
        findings=[],
        duration_seconds=42.5,
    )


@pytest.fixture
def mock_batch_assessment(mock_assessment):
    """Create a mock batch assessment for testing."""
    # Create successful result
    result1 = RepositoryResult(
        repository_url="https://github.com/user/repo1",
        assessment=mock_assessment,
        duration_seconds=42.5,
        cached=False,
    )

    # Create another successful result
    repo2 = Repository(
        path=Path("/test/repo2"),
        name="test-repo-2",
        branch="main",
        commit_hash="def789abc123",
        primary_language="JavaScript",
        languages={"JavaScript": 15},
        total_files=75,
        total_lines=3000,
    )
    assessment2 = Assessment(
        repository=repo2,
        timestamp=datetime(2025, 1, 22, 14, 35, 30),
        overall_score=72.0,
        certification_level="Silver",
        attributes_assessed=20,
        attributes_not_assessed=5,
        attributes_total=25,
        findings=[],
        duration_seconds=38.0,
    )
    result2 = RepositoryResult(
        repository_url="https://github.com/user/repo2",
        assessment=assessment2,
        duration_seconds=38.0,
        cached=True,
    )

    # Create failed result
    result3 = RepositoryResult(
        repository_url="https://github.com/user/repo3",
        assessment=None,
        error="Clone timeout",
        error_type="timeout",
        duration_seconds=120.0,
        cached=False,
    )

    summary = BatchSummary(
        total_repositories=3,
        successful_assessments=2,
        failed_assessments=1,
        average_score=78.75,
        score_distribution={"Gold": 1, "Silver": 1},
        language_breakdown={"Python": 1, "JavaScript": 1},
        top_failing_attributes=[],
    )

    return BatchAssessment(
        batch_id="test-batch-123",
        timestamp=datetime(2025, 1, 22, 14, 30, 0),
        results=[result1, result2, result3],
        summary=summary,
        total_duration_seconds=200.5,
        agentready_version="1.0.0",
        command="assess-batch",
    )


class TestCSVReporter:
    """Test suite for CSVReporter."""

    def test_sanitize_csv_field_normal_text(self):
        """Test that normal text is not modified."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("normal text") == "normal text"
        assert reporter.sanitize_csv_field("test-repo") == "test-repo"
        assert reporter.sanitize_csv_field("123") == "123"

    def test_sanitize_csv_field_none(self):
        """Test that None becomes empty string."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field(None) == ""

    def test_sanitize_csv_field_formula_injection_equals(self):
        """Test that equals sign is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("=1+1") == "'=1+1"
        assert reporter.sanitize_csv_field("=cmd|'/c calc'!A1") == "'=cmd|'/c calc'!A1"

    def test_sanitize_csv_field_formula_injection_plus(self):
        """Test that plus sign is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("+1+1") == "'+1+1"
        assert reporter.sanitize_csv_field("+cmd") == "'+cmd"

    def test_sanitize_csv_field_formula_injection_minus(self):
        """Test that minus sign is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("-1+1") == "'-1+1"
        assert reporter.sanitize_csv_field("-cmd") == "'-cmd"

    def test_sanitize_csv_field_formula_injection_at(self):
        """Test that at sign is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("@SUM(A1:A10)") == "'@SUM(A1:A10)"

    def test_sanitize_csv_field_formula_injection_tab(self):
        """Test that tab is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("\tcmd") == "'\tcmd"

    def test_sanitize_csv_field_formula_injection_carriage_return(self):
        """Test that carriage return is escaped (CSV injection prevention)."""
        reporter = CSVReporter()
        assert reporter.sanitize_csv_field("\rcmd") == "'\rcmd"

    def test_generate_csv_success(self, mock_batch_assessment, temp_csv_file):
        """Test CSV generation with successful assessments."""
        reporter = CSVReporter()
        result_path = reporter.generate(mock_batch_assessment, temp_csv_file)

        assert result_path == temp_csv_file
        assert temp_csv_file.exists()

        # Read and verify CSV content
        with open(temp_csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3  # 2 successful + 1 failed

        # Verify successful row
        assert rows[0]["repo_url"] == "https://github.com/user/repo1"
        assert rows[0]["repo_name"] == "test-repo"
        assert rows[0]["overall_score"] == "85.5"
        assert rows[0]["certification_level"] == "Gold"
        assert rows[0]["primary_language"] == "Python"
        assert rows[0]["status"] == "success"
        assert rows[0]["cached"] == "False"

        # Verify second successful row
        assert rows[1]["repo_url"] == "https://github.com/user/repo2"
        assert rows[1]["cached"] == "True"

        # Verify failed row
        assert rows[2]["repo_url"] == "https://github.com/user/repo3"
        assert rows[2]["status"] == "failed"
        assert rows[2]["error_type"] == "timeout"
        assert rows[2]["error_message"] == "Clone timeout"

    def test_generate_tsv_success(self, mock_batch_assessment, temp_tsv_file):
        """Test TSV generation (tab delimiter)."""
        reporter = CSVReporter()
        result_path = reporter.generate(
            mock_batch_assessment, temp_tsv_file, delimiter="\t"
        )

        assert result_path == temp_tsv_file
        assert temp_tsv_file.exists()

        # Read and verify TSV content
        with open(temp_tsv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)

        assert len(rows) == 3

    def test_csv_formula_injection_in_repo_name(
        self, mock_batch_assessment, temp_csv_file
    ):
        """Test that formula injection in repo name is prevented."""
        # Modify repository name to contain formula
        mock_batch_assessment.results[0].assessment.repository.name = (
            "=cmd|'/c calc'!A1"
        )

        reporter = CSVReporter()
        reporter.generate(mock_batch_assessment, temp_csv_file)

        # Read CSV and verify escaping
        with open(temp_csv_file, "r", encoding="utf-8") as f:
            content = f.read()

        # The formula should be escaped with a leading single quote
        assert "'=cmd|'/c calc'!A1" in content or "\"'=cmd" in content

    def test_csv_formula_injection_in_error_message(
        self, mock_batch_assessment, temp_csv_file
    ):
        """Test that formula injection in error message is prevented."""
        # Modify error message to contain formula
        mock_batch_assessment.results[2].error = "=HYPERLINK('http://evil.com')"

        reporter = CSVReporter()
        reporter.generate(mock_batch_assessment, temp_csv_file)

        # Read CSV and verify escaping
        with open(temp_csv_file, "r", encoding="utf-8") as f:
            content = f.read()

        # The formula should be escaped
        assert "'=" in content or "\"'=" in content

    def test_csv_empty_batch(self, tmp_path):
        """Test CSV generation with no results."""
        # Create batch with no results (this should not happen in practice)
        summary = BatchSummary(
            total_repositories=0,
            successful_assessments=0,
            failed_assessments=0,
            average_score=0.0,
        )
        batch = BatchAssessment(
            batch_id="empty-batch",
            timestamp=datetime.now(),
            results=[],
            summary=summary,
            total_duration_seconds=0.0,
        )

        reporter = CSVReporter()
        output_path = tmp_path / "empty.csv"

        # Should not raise error, but will only have header
        with pytest.raises(ValueError, match="Batch must have at least one result"):
            reporter.generate(batch, output_path)

    def test_csv_creates_parent_directory(self, tmp_path):
        """Test that CSV reporter creates parent directories if needed."""
        nested_path = tmp_path / "nested" / "dir" / "report.csv"

        # Create a minimal batch assessment
        repo = Repository(
            path=Path("/test"),
            name="test",
            branch="main",
            commit_hash="abc123",
            primary_language="Python",
            languages={},
            total_files=1,
            total_lines=1,
        )
        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=50.0,
            certification_level="Bronze",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[],
            duration_seconds=1.0,
        )
        result = RepositoryResult(
            repository_url="https://test.com", assessment=assessment
        )
        summary = BatchSummary(
            total_repositories=1,
            successful_assessments=1,
            failed_assessments=0,
            average_score=50.0,
        )
        batch = BatchAssessment(
            batch_id="test",
            timestamp=datetime.now(),
            results=[result],
            summary=summary,
            total_duration_seconds=1.0,
        )

        reporter = CSVReporter()
        reporter.generate(batch, nested_path)

        assert nested_path.exists()
