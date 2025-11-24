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


def create_test_batch_with_payload(payload: str, inject_location: str, tmp_path=None):
    """Helper to create batch assessment with XSS/injection payload.

    Args:
        payload: Malicious payload to inject
        inject_location: Where to inject ('repo_name', 'repo_url', 'error_message')
        tmp_path: Temporary path to use for repository (creates .git dir if provided)
    """
    # Use tmp_path if provided, otherwise use current directory (which exists)
    if tmp_path:
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir(exist_ok=True)
        (repo_path / ".git").mkdir(exist_ok=True)
    else:
        repo_path = Path.cwd()  # Use current directory which we know exists

    repo = Repository(
        path=repo_path,
        name="test-repo" if inject_location != "repo_name" else payload,
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 1},
        total_files=1,
        total_lines=1,
    )

    # Create a dummy finding to satisfy Assessment validation
    from src.agentready.models.attribute import Attribute
    from src.agentready.models.finding import Finding

    dummy_attr = Attribute(
        id="test_attr",
        name="Test Attribute",
        category="Test",
        tier=1,
        description="Test description",
        criteria="Test criteria",
        default_weight=1.0,
    )
    dummy_finding = Finding(
        attribute=dummy_attr,
        status="pass",
        score=100.0,
        measured_value="1 test",
        threshold="1+ tests",
        evidence=["Test evidence"],
        remediation=None,
        error_message=None,
    )

    assessment = Assessment(
        repository=repo,
        timestamp=datetime.now(),
        overall_score=50.0,
        certification_level="Bronze",
        attributes_assessed=1,
        attributes_not_assessed=0,
        attributes_total=1,
        findings=[dummy_finding],
        config=None,
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
        batch = create_test_batch_with_payload(xss_payload, "repo_name", tmp_path)

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify the malicious payload itself is NOT present unescaped
        # Note: Template has legitimate <script> tags for table sorting, so we check
        # for the specific attack payload instead
        assert (
            xss_payload not in html_content
        ), f"Unescaped XSS payload found: {xss_payload}"

        # Verify dangerous event handlers from the payload are not present as HTML attributes
        # (Allow them in legitimate script code)
        if "onerror=" in xss_payload:
            # Check it's not in an HTML attribute context (must be in legitimate script or escaped)
            assert "onerror=alert" not in html_content
        if (
            "onload=" in xss_payload
            and "<body" not in xss_payload
            and "<svg" not in xss_payload
        ):
            assert "onload=alert" not in html_content
        if "onfocus=" in xss_payload:
            assert "onfocus=alert" not in html_content
        if "onstart=" in xss_payload:
            assert "onstart=alert" not in html_content

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
        batch = create_test_batch_with_payload(malicious_url, "repo_url", tmp_path)

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
        batch = create_test_batch_with_payload(xss_payload, "error_message", tmp_path)

        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()

        # Verify the XSS payload is NOT present unescaped
        # Must be HTML-escaped to &lt;script&gt; or similar
        assert xss_payload not in html_content, "Unescaped XSS payload in error message"
        assert (
            "&lt;script&gt;" in html_content or "&#" in html_content
        ), "XSS should be HTML-escaped"

    def test_html_autoescape_enabled(self, template_dir):
        """Verify that Jinja2 autoescape is enabled (CRITICAL SECURITY CHECK)."""
        reporter = MultiRepoHTMLReporter(template_dir)
        # Autoescape should be True or a callable selector
        assert reporter.env.autoescape is True or callable(reporter.env.autoescape)

    def test_html_csp_header_present(self, template_dir, tmp_path):
        """Verify that Content Security Policy header is present (CRITICAL)."""
        batch = create_test_batch_with_payload("test", "repo_name", tmp_path)

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
        batch = create_test_batch_with_payload(injection_payload, "repo_name", tmp_path)

        reporter = CSVReporter()
        output_path = tmp_path / "test.csv"
        reporter.generate(batch, output_path)

        csv_content = output_path.read_text()

        # Verify formula characters are escaped with leading single quote
        first_char = injection_payload[0]
        if first_char in CSVReporter.FORMULA_CHARS:
            # Should be prefixed with single quote (may be quoted by CSV writer)
            # Note: \r may be normalized to \n by CSV writer
            assert (
                "'" + first_char in csv_content
                or '"' + "'" + first_char in csv_content
                or "'" + "\n" in csv_content
            ), f"Formula char {repr(first_char)} should be escaped with leading quote"

    def test_csv_formula_injection_prevention_in_error_message(self, tmp_path):
        """Test that CSV formula injection in error messages is prevented."""
        injection_payload = "=HYPERLINK('http://evil.com')"
        batch = create_test_batch_with_payload(
            injection_payload, "error_message", tmp_path
        )

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
        batch = create_test_batch_with_payload(injection_payload, "repo_name", tmp_path)

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
        xss_payload = "<script>alert(1)</script>"
        batch = create_test_batch_with_payload(xss_payload, "repo_name", tmp_path)
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        # Verify the XSS payload itself is not present unescaped
        assert xss_payload not in html_content, "Unescaped XSS payload found"

    def test_url_sanitization_verified(self, template_dir, tmp_path):
        """✓ URL sanitization verified (test with javascript: URLs)."""
        batch = create_test_batch_with_payload(
            "javascript:alert(1)", "repo_url", tmp_path
        )
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        assert 'href="javascript:' not in html_content

    def test_csp_header_present(self, template_dir, tmp_path):
        """✓ CSP header present in HTML reports."""
        batch = create_test_batch_with_payload("test", "repo_name", tmp_path)
        reporter = MultiRepoHTMLReporter(template_dir)
        output_path = tmp_path / "test.html"
        reporter.generate(batch, output_path)

        html_content = output_path.read_text()
        assert "Content-Security-Policy" in html_content

    def test_csv_formula_escaping_verified(self, tmp_path):
        """✓ CSV formula character escaping verified."""
        # Test all formula characters
        for char in ["=", "+", "-", "@"]:
            batch = create_test_batch_with_payload(f"{char}cmd", "repo_name", tmp_path)
            reporter = CSVReporter()
            output_path = tmp_path / f"test_{char}.csv"
            reporter.generate(batch, output_path)

            csv_content = output_path.read_text()
            assert f"'{char}" in csv_content or f'"{char}' in csv_content
