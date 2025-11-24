"""Security tests for XSS and CSV injection prevention in multi-repo reports.

CRITICAL: These tests verify security controls defined in the Phase 2 specification.
All tests must pass before considering Phase 2 complete.
"""

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
from src.agentready.reporters.multi_html import MultiRepoHTMLReporter


@pytest.fixture
def template_dir():
    """Get template directory path."""
    return Path(__file__).parent.parent.parent / "src" / "agentready" / "templates"


def create_test_batch_with_payload(payload: str, inject_location: str):
    """Helper to create batch assessment with XSS/injection payload.

    Args:
        payload: Malicious payload to inject
        inject_location: Where to inject ('repo_name', 'repo_url', 'error_message')
    """
    repo = Repository(
        path=Path("/test"),
        name="test-repo" if inject_location != "repo_name" else payload,
        branch="main",
        commit_hash="abc123",
        primary_language="Python",
        languages={"Python": 1},
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

    repo_url = (
        "https://github.com/test/repo" if inject_location != "repo_url" else payload
    )
    error = payload if inject_location == "error_message" else None

    if error:
        result = RepositoryResult(
            repository_url=repo_url,
            assessment=None,
            error=error,
            error_type="test_error",
            duration_seconds=1.0,
        )
        summary = BatchSummary(
            total_repositories=1,
            successful_assessments=0,
            failed_assessments=1,
            average_score=0.0,
        )
    else:
        result = RepositoryResult(
            repository_url=repo_url, assessment=assessment, duration_seconds=1.0
        )
        summary = BatchSummary(
            total_repositories=1,
            successful_assessments=1,
            failed_assessments=0,
            average_score=50.0,
        )

    return BatchAssessment(
        batch_id="test",
        timestamp=datetime.now(),
        results=[result],
        summary=summary,
        total_duration_seconds=1.0,
    )


class TestXSSPrevention:
    """Test suite for XSS prevention in HTML reports."""

    @pytest.mark.parametrize(
        "xss_payload",
        [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<marquee onstart=alert('XSS')>",
            "'-alert('XSS')-'",
            '"><script>alert(String.fromCharCode(88,83,83))</script>',
        ],
    )
    def test_html_xss_prevention_in_repo_name(
        self, template_dir, tmp_path, xss_payload
    ):
        """Test that XSS payloads in repository names are escaped."""
        batch = create_test_batch_with_payload(xss_payload, "repo_name")

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify script tags are escaped
        assert "<script>" not in html_content
        assert "onerror=" not in html_content or "&quot;onerror=" in html_content
        assert "onload=" not in html_content or "&quot;onload=" in html_content
        assert "onfocus=" not in html_content or "&quot;onfocus=" in html_content
        assert "onstart=" not in html_content or "&quot;onstart=" in html_content

        # Verify alternative escape patterns
        if "<" in xss_payload:
            assert "&lt;" in html_content or "<script>" not in html_content

    @pytest.mark.parametrize(
        "malicious_url",
        [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "vbscript:msgbox('XSS')",
            "file:///etc/passwd",
            "about:blank",
        ],
    )
    def test_html_url_sanitization(self, template_dir, tmp_path, malicious_url):
        """Test that malicious URLs are blocked."""
        batch = create_test_batch_with_payload(malicious_url, "repo_url")

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify malicious schemes are not present as clickable links
        assert 'href="javascript:' not in html_content
        assert 'href="data:' not in html_content
        assert 'href="vbscript:' not in html_content
        assert 'href="file:' not in html_content

    def test_html_xss_prevention_in_error_message(self, template_dir, tmp_path):
        """Test that XSS in error messages is prevented."""
        xss_payload = "<script>alert('XSS from error')</script>"
        batch = create_test_batch_with_payload(xss_payload, "error_message")

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify script tag is escaped
        assert "<script>" not in html_content
        assert "&lt;script&gt;" in html_content or "script" not in html_content.lower()

    def test_html_autoescape_enabled(self, template_dir):
        """Verify that Jinja2 autoescape is enabled (CRITICAL SECURITY CHECK)."""
        reporter = MultiRepoHTMLReporter(template_dir)
        # Autoescape should be True or a callable selector
        assert reporter.env.autoescape is True or callable(reporter.env.autoescape)

    def test_html_csp_header_present(self, template_dir, tmp_path):
        """Verify that Content Security Policy header is present (CRITICAL)."""
        batch = create_test_batch_with_payload("test", "repo_name")

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify CSP header is present and restrictive
        assert "Content-Security-Policy" in html_content
        assert "script-src 'none'" in html_content or "script-src" in html_content


class TestCSVInjectionPrevention:
    """Test suite for CSV formula injection prevention."""

    @pytest.mark.parametrize(
        "injection_payload",
        [
            "=1+1",
            "=cmd|'/c calc'!A1",
            "+1+1",
            "+cmd",
            "-1+1",
            "-cmd",
            "@SUM(A1:A10)",
            "\tcmd",
            "\rcmd",
            "=HYPERLINK('http://evil.com', 'click')",
            "=1+1+cmd|' /C calc'!A1",
            "@cmd|'/c calc'!A1",
        ],
    )
    def test_csv_formula_injection_prevention_in_repo_name(
        self, tmp_path, injection_payload
    ):
        """Test that CSV formula injection payloads are escaped."""
        batch = create_test_batch_with_payload(injection_payload, "repo_name")

        reporter = CSVReporter()
        output_path = tmp_path / "test.csv"
        reporter.generate(batch, output_path)

        csv_content = output_path.read_text()

        # Verify formula characters are escaped with leading single quote
        first_char = injection_payload[0]
        if first_char in CSVReporter.FORMULA_CHARS:
            # Should be prefixed with single quote
            assert f"'{first_char}" in csv_content or f'"{first_char}' in csv_content

    def test_csv_formula_injection_prevention_in_error_message(self, tmp_path):
        """Test that CSV formula injection in error messages is prevented."""
        injection_payload = "=HYPERLINK('http://evil.com')"
        batch = create_test_batch_with_payload(injection_payload, "error_message")

        reporter = CSVReporter()
        output_path = tmp_path / "test.csv"
        reporter.generate(batch, output_path)

        csv_content = output_path.read_text()

        # Verify formula is escaped
        assert "'=" in csv_content or "\"'=" in csv_content

    def test_csv_sanitize_field_static_method(self):
        """Test the sanitize_csv_field method directly."""
        reporter = CSVReporter()

        # Test formula characters
        assert reporter.sanitize_csv_field("=1+1") == "'=1+1"
        assert reporter.sanitize_csv_field("+cmd") == "'+cmd"
        assert reporter.sanitize_csv_field("-cmd") == "'-cmd"
        assert reporter.sanitize_csv_field("@SUM") == "'@SUM"
        assert reporter.sanitize_csv_field("\tcmd") == "'\tcmd"
        assert reporter.sanitize_csv_field("\rcmd") == "'\rcmd"

        # Test normal text (should not be modified)
        assert reporter.sanitize_csv_field("normal text") == "normal text"
        assert reporter.sanitize_csv_field("test-repo") == "test-repo"

        # Test None
        assert reporter.sanitize_csv_field(None) == ""

    def test_tsv_formula_injection_prevention(self, tmp_path):
        """Test that TSV (tab-delimited) also prevents formula injection."""
        injection_payload = "=cmd|'/c calc'!A1"
        batch = create_test_batch_with_payload(injection_payload, "repo_name")

        reporter = CSVReporter()
        output_path = tmp_path / "test.tsv"
        reporter.generate(batch, output_path, delimiter="\t")

        tsv_content = output_path.read_text()

        # Verify formula is escaped
        assert "'=" in tsv_content or "\"'=" in tsv_content


class TestSecurityChecklist:
    """Verify all security controls from Phase 2 specification."""

    def test_jinja2_autoescape_enabled(self, template_dir):
        """✓ Jinja2 autoescape enabled in MultiRepoHTMLReporter."""
        reporter = MultiRepoHTMLReporter(template_dir)
        assert reporter.env.autoescape is True or callable(reporter.env.autoescape)

    def test_html_escaping_verified(self, template_dir, tmp_path):
        """✓ HTML escaping verified (test with <script> tags)."""
        batch = create_test_batch_with_payload("<script>alert(1)</script>", "repo_name")
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        assert "<script>" not in html_content

    def test_url_sanitization_verified(self, template_dir, tmp_path):
        """✓ URL sanitization verified (test with javascript: URLs)."""
        batch = create_test_batch_with_payload("javascript:alert(1)", "repo_url")
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        assert 'href="javascript:' not in html_content

    def test_csp_header_present(self, template_dir, tmp_path):
        """✓ CSP header present in HTML reports."""
        batch = create_test_batch_with_payload("test", "repo_name")
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        assert "Content-Security-Policy" in html_content

    def test_csv_formula_escaping_verified(self, tmp_path):
        """✓ CSV formula character escaping verified."""
        # Test all formula characters
        for char in ["=", "+", "-", "@"]:
            batch = create_test_batch_with_payload(f"{char}cmd", "repo_name")
            reporter = CSVReporter()
            output_path = tmp_path / f"test_{char}.csv"
            reporter.generate(batch, output_path)

            csv_content = output_path.read_text()
            assert f"'{char}" in csv_content or f'"{char}' in csv_content
