"""Unit tests for multi-repository HTML reporter with security controls."""

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
from src.agentready.reporters.multi_html import MultiRepoHTMLReporter


@pytest.fixture
def template_dir():
    """Get template directory path."""
    return Path(__file__).parent.parent.parent / "src" / "agentready" / "templates"


@pytest.fixture
def temp_html_file(tmp_path):
    """Create temporary HTML file for testing."""
    return tmp_path / "index.html"


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
    result1 = RepositoryResult(
        repository_url="https://github.com/user/repo1",
        assessment=mock_assessment,
        duration_seconds=42.5,
        cached=False,
    )

    summary = BatchSummary(
        total_repositories=1,
        successful_assessments=1,
        failed_assessments=0,
        average_score=85.5,
        score_distribution={"Gold": 1},
        language_breakdown={"Python": 1},
        top_failing_attributes=[{"attribute_id": "1.1", "failure_count": 5}],
    )

    return BatchAssessment(
        batch_id="test-batch-123",
        timestamp=datetime(2025, 1, 22, 14, 30, 0),
        results=[result1],
        summary=summary,
        total_duration_seconds=42.5,
        agentready_version="1.0.0",
        command="assess-batch",
    )


class TestMultiRepoHTMLReporter:
    """Test suite for MultiRepoHTMLReporter."""

    def test_sanitize_url_valid_https(self):
        """Test that valid HTTPS URLs are allowed and escaped."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "https://github.com/user/repo"
        result = reporter.sanitize_url(url)
        assert "github.com" in result
        assert result.startswith("https://")

    def test_sanitize_url_valid_http(self):
        """Test that valid HTTP URLs are allowed and escaped."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "http://example.com/path"
        result = reporter.sanitize_url(url)
        assert "example.com" in result

    def test_sanitize_url_javascript_scheme_blocked(self):
        """Test that javascript: URLs are blocked (XSS prevention)."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "javascript:alert('XSS')"
        result = reporter.sanitize_url(url)
        assert result == ""

    def test_sanitize_url_data_scheme_blocked(self):
        """Test that data: URLs are blocked (XSS prevention)."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "data:text/html,<script>alert('XSS')</script>"
        result = reporter.sanitize_url(url)
        assert result == ""

    def test_sanitize_url_file_scheme_blocked(self):
        """Test that file: URLs are blocked (security)."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "file:///etc/passwd"
        result = reporter.sanitize_url(url)
        assert result == ""

    def test_sanitize_url_empty_string(self):
        """Test that empty string returns empty string."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        assert reporter.sanitize_url("") == ""
        assert reporter.sanitize_url(None) == ""

    def test_sanitize_url_html_escape(self):
        """Test that URLs with special HTML characters are escaped."""
        reporter = MultiRepoHTMLReporter(Path("/tmp"))
        url = "https://example.com/path?param=<script>"
        result = reporter.sanitize_url(url)
        # Should escape < and >
        assert "&lt;" in result or "<" not in result

    def test_generate_html_success(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test HTML generation with successful batch assessment."""
        reporter = MultiRepoHTMLReporter(template_dir)
        result_path = reporter.generate(mock_batch_assessment, temp_html_file)

        assert result_path == temp_html_file
        assert temp_html_file.exists()

        # Read HTML content
        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify basic structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content

        # Verify CSP header
        assert "Content-Security-Policy" in html_content
        assert "script-src 'none'" in html_content

        # Verify content
        assert "Multi-Repository Assessment Report" in html_content
        assert "test-batch-123" in html_content
        assert "1.0.0" in html_content  # AgentReady version
        assert "85.5" in html_content  # Score

    def test_generate_html_xss_prevention_repo_name(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test that XSS in repository name is prevented."""
        # Inject XSS payload into repository name
        mock_batch_assessment.results[0].assessment.repository.name = (
            "<script>alert('XSS')</script>"
        )

        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify script tag is escaped
        assert "<script>" not in html_content
        assert "&lt;script&gt;" in html_content or "script" not in html_content.lower()

    def test_generate_html_xss_prevention_repo_url(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test that XSS in repository URL is prevented."""
        # Inject XSS payload into repository URL
        mock_batch_assessment.results[0].repository_url = (
            "javascript:alert('XSS')//https://fake.com"
        )

        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify javascript: is not present as a clickable link
        # Note: The sanitize_url filter should have blocked it
        assert 'href="javascript:' not in html_content

    def test_generate_html_xss_prevention_error_message(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test that XSS in error message is prevented."""
        # Add failed result with XSS payload
        failed_result = RepositoryResult(
            repository_url="https://github.com/user/bad",
            assessment=None,
            error="<img src=x onerror=alert('XSS')>",
            error_type="test_error",
            duration_seconds=1.0,
        )
        mock_batch_assessment.results.append(failed_result)
        mock_batch_assessment.summary.failed_assessments = 1

        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify img tag is escaped
        assert "<img" not in html_content or "&lt;img" in html_content
        assert "onerror=" not in html_content

    def test_generate_html_autoescape_enabled(self, template_dir):
        """Test that Jinja2 autoescape is enabled."""
        reporter = MultiRepoHTMLReporter(template_dir)
        assert reporter.env.autoescape is True or callable(reporter.env.autoescape)

    def test_generate_html_with_failed_assessments(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test HTML generation includes failed assessments section."""
        # Add failed result
        failed_result = RepositoryResult(
            repository_url="https://github.com/user/failed-repo",
            assessment=None,
            error="Clone timeout",
            error_type="timeout",
            duration_seconds=120.0,
        )
        mock_batch_assessment.results.append(failed_result)
        mock_batch_assessment.summary.failed_assessments = 1
        mock_batch_assessment.summary.total_repositories = 2

        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify failed assessments section
        assert "Failed Assessments" in html_content or "failed" in html_content.lower()
        assert "timeout" in html_content
        assert "Clone timeout" in html_content

    def test_generate_html_certification_badges(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test that certification badges are rendered correctly."""
        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Verify Gold badge is present
        assert "Gold" in html_content
        assert "gold" in html_content.lower()  # CSS class

    def test_generate_html_creates_parent_directory(self, template_dir, tmp_path):
        """Test that HTML reporter creates parent directories if needed."""
        nested_path = tmp_path / "nested" / "dir" / "index.html"

        # Create minimal batch assessment
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

        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(batch, nested_path)

        assert nested_path.exists()

    def test_generate_html_responsive_design(
        self, template_dir, mock_batch_assessment, temp_html_file
    ):
        """Test that HTML includes responsive design elements."""
        reporter = MultiRepoHTMLReporter(template_dir)
        reporter.generate(mock_batch_assessment, temp_html_file)

        html_content = temp_html_file.read_text(encoding="utf-8")

        # Check for viewport meta tag
        assert "viewport" in html_content
        assert "width=device-width" in html_content

        # Check for media queries or responsive CSS
        assert "@media" in html_content or "max-width" in html_content
