"""Integration tests for comprehensive multi-repository reporting."""

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
from src.agentready.reporters.aggregated_json import AggregatedJSONReporter
from src.agentready.reporters.csv_reporter import CSVReporter
from src.agentready.reporters.html import HTMLReporter
from src.agentready.reporters.json_reporter import JSONReporter
from src.agentready.reporters.markdown import MarkdownReporter
from src.agentready.reporters.multi_html import MultiRepoHTMLReporter


@pytest.fixture
def reports_dir(tmp_path):
    """Create temporary reports directory."""
    reports = tmp_path / "reports-20250122-143022"
    reports.mkdir(parents=True)
    return reports


@pytest.fixture
def template_dir():
    """Get template directory path."""
    return Path(__file__).parent.parent.parent / "src" / "agentready" / "templates"


@pytest.fixture
def mock_batch_assessment(tmp_path):
    """Create a comprehensive mock batch assessment."""
    # Create temporary repository directories for validation
    repo1_path = tmp_path / "repo1"
    repo1_path.mkdir()
    (repo1_path / ".git").mkdir()

    # Create first repository and assessment
    repo1 = Repository(
        path=repo1_path,
        name="repo1",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 50, "JavaScript": 10},
        total_files=100,
        total_lines=5000,
    )
    # Create dummy findings to satisfy Assessment validation
    from src.agentready.models.attribute import Attribute
    from src.agentready.models.finding import Finding

    dummy_findings = []
    for i in range(25):
        attr = Attribute(
            id=f"attr_{i}",
            name=f"Attribute {i}",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )
        finding = Finding(
            attribute=attr,
            status="pass" if i < 20 else "skipped",
            score=100.0 if i < 20 else None,
            measured_value="test",
            threshold="test",
            evidence=["test"],
            remediation=None,
            error_message=None,
        )
        dummy_findings.append(finding)

    assessment1 = Assessment(
        repository=repo1,
        timestamp=datetime(2025, 1, 22, 14, 30, 22),
        overall_score=85.5,
        certification_level="Gold",
        attributes_assessed=20,
        attributes_not_assessed=5,
        attributes_total=25,
        findings=dummy_findings,
        config=None,
        duration_seconds=42.5,
    )
    result1 = RepositoryResult(
        repository_url="https://github.com/user/repo1",
        assessment=assessment1,
        duration_seconds=42.5,
        cached=False,
    )

    # Create second repository directory
    repo2_path = tmp_path / "repo2"
    repo2_path.mkdir()
    (repo2_path / ".git").mkdir()

    # Create second repository and assessment
    repo2 = Repository(
        path=repo2_path,
        name="repo2",
        url=None,
        branch="develop",
        commit_hash="def456",
        languages={"JavaScript": 80, "TypeScript": 20},
        total_files=150,
        total_lines=7500,
    )
    assessment2 = Assessment(
        repository=repo2,
        timestamp=datetime(2025, 1, 22, 14, 35, 30),
        overall_score=72.0,
        certification_level="Silver",
        attributes_assessed=20,
        attributes_not_assessed=5,
        attributes_total=25,
        findings=dummy_findings,  # Reuse findings from assessment1
        config=None,
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
        error="Clone timeout after 60 seconds",
        error_type="timeout",
        duration_seconds=120.0,
        cached=False,
    )

    # Create summary
    summary = BatchSummary(
        total_repositories=3,
        successful_assessments=2,
        failed_assessments=1,
        average_score=78.75,
        score_distribution={"Gold": 1, "Silver": 1},
        language_breakdown={"Python": 1, "JavaScript": 2},
        top_failing_attributes=[
            {"attribute_id": "1.1", "failure_count": 2},
            {"attribute_id": "2.3", "failure_count": 1},
        ],
    )

    return BatchAssessment(
        batch_id="test-batch-20250122",
        timestamp=datetime(2025, 1, 22, 14, 30, 0),
        results=[result1, result2, result3],
        summary=summary,
        total_duration_seconds=200.5,
        agentready_version="1.0.0",
        command="assess-batch --repos-file repos.txt",
    )


class TestMultiReportGeneration:
    """Integration tests for complete multi-repository reporting."""

    def test_generate_all_reports(
        self, reports_dir, template_dir, mock_batch_assessment
    ):
        """Test generating all report formats in dated folder."""
        # 1. Generate CSV/TSV
        csv_reporter = CSVReporter()
        csv_path = csv_reporter.generate(
            mock_batch_assessment, reports_dir / "summary.csv"
        )
        tsv_path = csv_reporter.generate(
            mock_batch_assessment, reports_dir / "summary.tsv", delimiter="\t"
        )

        # 2. Generate aggregated JSON
        json_reporter = AggregatedJSONReporter()
        agg_json_path = json_reporter.generate(
            mock_batch_assessment, reports_dir / "all-assessments.json"
        )

        # 3. Generate individual reports for successful assessments
        html_reporter = HTMLReporter()
        md_reporter = MarkdownReporter()
        individual_json = JSONReporter()

        individual_reports = []
        for result in mock_batch_assessment.results:
            if result.is_success():
                assessment = result.assessment
                base_name = (
                    f"{assessment.repository.name}-"
                    f"{assessment.timestamp.strftime('%Y%m%d-%H%M%S')}"
                )

                html_reporter.generate(assessment, reports_dir / f"{base_name}.html")
                md_reporter.generate(assessment, reports_dir / f"{base_name}.md")
                individual_json.generate(assessment, reports_dir / f"{base_name}.json")

                individual_reports.append(base_name)

        # 4. Generate multi-repo summary HTML
        multi_html = MultiRepoHTMLReporter(template_dir)
        index_path = multi_html.generate(
            mock_batch_assessment, reports_dir / "index.html"
        )

        # Verify all files exist
        assert csv_path.exists()
        assert tsv_path.exists()
        assert agg_json_path.exists()
        assert index_path.exists()

        # Verify individual reports
        for base_name in individual_reports:
            assert (reports_dir / f"{base_name}.html").exists()
            assert (reports_dir / f"{base_name}.json").exists()
            assert (reports_dir / f"{base_name}.md").exists()

        # Verify expected number of files
        # Expected: summary.csv, summary.tsv, all-assessments.json, index.html
        #           + 3 files per successful assessment (2 successful)
        #           = 4 + (3 * 2) = 10 files
        all_files = list(reports_dir.iterdir())
        assert len(all_files) == 10

    def test_index_html_links_to_individual_reports(
        self, reports_dir, template_dir, mock_batch_assessment
    ):
        """Test that index.html contains links to individual reports."""
        # Generate individual reports first
        html_reporter = HTMLReporter()
        individual_json = JSONReporter()
        md_reporter = MarkdownReporter()

        for result in mock_batch_assessment.results:
            if result.is_success():
                assessment = result.assessment
                base_name = (
                    f"{assessment.repository.name}-"
                    f"{assessment.timestamp.strftime('%Y%m%d-%H%M%S')}"
                )

                html_reporter.generate(assessment, reports_dir / f"{base_name}.html")
                individual_json.generate(assessment, reports_dir / f"{base_name}.json")
                md_reporter.generate(assessment, reports_dir / f"{base_name}.md")

        # Generate index
        multi_html = MultiRepoHTMLReporter(template_dir)
        multi_html.generate(mock_batch_assessment, reports_dir / "index.html")

        # Read index.html and verify links
        index_content = (reports_dir / "index.html").read_text()

        assert "repo1-20250122-143022.html" in index_content
        assert "repo1-20250122-143022.json" in index_content
        assert "repo2-20250122-143530.html" in index_content
        assert "repo2-20250122-143530.json" in index_content

    def test_csv_contains_all_results(self, reports_dir, mock_batch_assessment):
        """Test that CSV contains all successful and failed results."""
        csv_reporter = CSVReporter()
        csv_reporter.generate(mock_batch_assessment, reports_dir / "summary.csv")

        # Read CSV
        import csv

        with open(reports_dir / "summary.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 3 rows (2 successful + 1 failed)
        assert len(rows) == 3

        # Verify successful results
        success_rows = [r for r in rows if r["status"] == "success"]
        assert len(success_rows) == 2
        assert success_rows[0]["repo_name"] == "repo1"
        assert success_rows[1]["repo_name"] == "repo2"

        # Verify failed result
        failed_rows = [r for r in rows if r["status"] == "failed"]
        assert len(failed_rows) == 1
        assert failed_rows[0]["error_type"] == "timeout"

    def test_aggregated_json_structure(self, reports_dir, mock_batch_assessment):
        """Test that aggregated JSON has correct structure."""
        import json

        json_reporter = AggregatedJSONReporter()
        json_reporter.generate(
            mock_batch_assessment, reports_dir / "all-assessments.json"
        )

        # Read JSON
        with open(reports_dir / "all-assessments.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify top-level structure
        assert "batch_id" in data
        assert "timestamp" in data
        assert "results" in data
        assert "summary" in data
        assert "total_duration_seconds" in data
        assert "agentready_version" in data

        # Verify results
        assert len(data["results"]) == 3
        assert data["summary"]["total_repositories"] == 3
        assert data["summary"]["successful_assessments"] == 2
        assert data["summary"]["failed_assessments"] == 1

    def test_reports_folder_structure_matches_specification(
        self, tmp_path, template_dir, mock_batch_assessment
    ):
        """Test that reports folder structure matches Phase 2 specification."""
        # Create dated reports folder
        timestamp = "20250122-143022"
        reports_dir = tmp_path / f"reports-{timestamp}"
        reports_dir.mkdir(parents=True)

        # Generate all reports
        csv_reporter = CSVReporter()
        csv_reporter.generate(mock_batch_assessment, reports_dir / "summary.csv")
        csv_reporter.generate(
            mock_batch_assessment, reports_dir / "summary.tsv", delimiter="\t"
        )

        json_reporter = AggregatedJSONReporter()
        json_reporter.generate(
            mock_batch_assessment, reports_dir / "all-assessments.json"
        )

        multi_html = MultiRepoHTMLReporter(template_dir)
        multi_html.generate(mock_batch_assessment, reports_dir / "index.html")

        # Generate individual reports
        html_reporter = HTMLReporter()
        md_reporter = MarkdownReporter()
        individual_json = JSONReporter()

        for result in mock_batch_assessment.results:
            if result.is_success():
                assessment = result.assessment
                base_name = (
                    f"{assessment.repository.name}-"
                    f"{assessment.timestamp.strftime('%Y%m%d-%H%M%S')}"
                )
                html_reporter.generate(assessment, reports_dir / f"{base_name}.html")
                md_reporter.generate(assessment, reports_dir / f"{base_name}.md")
                individual_json.generate(assessment, reports_dir / f"{base_name}.json")

        # Verify structure
        assert (reports_dir / "index.html").exists()
        assert (reports_dir / "summary.csv").exists()
        assert (reports_dir / "summary.tsv").exists()
        assert (reports_dir / "all-assessments.json").exists()
        assert (reports_dir / "repo1-20250122-143022.html").exists()
        assert (reports_dir / "repo1-20250122-143022.json").exists()
        assert (reports_dir / "repo1-20250122-143022.md").exists()
        assert (reports_dir / "repo2-20250122-143530.html").exists()
        assert (reports_dir / "repo2-20250122-143530.json").exists()
        assert (reports_dir / "repo2-20250122-143530.md").exists()

    def test_security_controls_applied_across_all_reports(
        self, reports_dir, template_dir, mock_batch_assessment
    ):
        """Test that security controls are applied across all report types."""
        # Inject XSS/CSV injection payloads
        mock_batch_assessment.results[0].assessment.repository.name = (
            "=cmd|'/c calc'!A1"
        )
        mock_batch_assessment.results[1].repository_url = (
            "javascript:alert('XSS')//https://fake.com"
        )

        # Generate all reports
        csv_reporter = CSVReporter()
        csv_reporter.generate(mock_batch_assessment, reports_dir / "summary.csv")

        multi_html = MultiRepoHTMLReporter(template_dir)
        multi_html.generate(mock_batch_assessment, reports_dir / "index.html")

        # Verify CSV escaping
        csv_content = (reports_dir / "summary.csv").read_text()
        assert "'=" in csv_content or "\"'=" in csv_content

        # Verify HTML escaping
        html_content = (reports_dir / "index.html").read_text()
        assert 'href="javascript:' not in html_content
        # Verify the actual XSS payload is not present (template has legitimate <script> tags)
        assert "javascript:alert('XSS')" not in html_content
