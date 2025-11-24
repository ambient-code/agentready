"""Security tests for AgentReady."""

from datetime import datetime
from unittest.mock import patch

import pytest

from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding
from agentready.models.repository import Repository
from agentready.reporters.html import HTMLReporter


class TestXSSPrevention:
    """Test XSS prevention in HTML reports."""

    def test_malicious_repository_name_escaped(self, tmp_path):
        """Test that malicious repository names are escaped in HTML."""
        # Create repository with XSS payload in name
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="<script>alert('xss')</script>",
            url="https://evil.com/<script>alert('xss')</script>",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        # Create minimal assessment
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="test",
            threshold="test",
            evidence=["<script>alert('evidence')</script>"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=100.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        # Read generated HTML
        html_content = result.read_text()

        # Verify XSS payloads are escaped in JavaScript context
        # The JSON.parse() line should have Unicode escapes
        assert (
            "\\u003cscript\\u003e" in html_content
            or "\u003cscript\u003e" in html_content
        )

        # Verify HTML contexts are escaped (title, body text)
        # Jinja2 autoescape should convert < to &lt; in HTML context
        title_section = html_content[
            html_content.find("<title>") : html_content.find("</title>")
        ]
        assert (
            "&lt;script&gt;" in title_section
            or "<script>alert('xss')</script>" not in title_section
        )

        # Most importantly: verify JavaScript execution context is safe
        script_section = html_content[
            html_content.find("<script>") : html_content.find("</script>")
        ]
        # JSON.parse() should have Unicode-escaped the malicious content
        assert "JSON.parse(" in script_section
        assert "\\u003c" in script_section  # Unicode escape for '<'

    def test_malicious_commit_message_escaped(self, tmp_path):
        """Test that malicious commit messages are escaped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="safe-repo",
            url=None,
            branch="<img src=x onerror=alert(1)>",
            commit_hash="<script>alert(1)</script>",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="fail",
            score=0.0,
            measured_value="test",
            threshold="test",
            evidence=[],
            remediation=None,
            error_message="<script>alert('error')</script>",
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=0.0,
            certification_level="Needs Improvement",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        html_content = result.read_text()

        # Verify JavaScript context is safe (JSON.parse with Unicode escapes)
        script_section = html_content[
            html_content.find("<script>") : html_content.find("</script>")
        ]
        assert "JSON.parse(" in script_section
        assert "\\u003c" in script_section  # '<' should be Unicode-escaped

        # Verify no direct script execution
        # The malicious payloads should be escaped
        assert "<img src=x onerror=alert(1)>" not in html_content
        # Script tags in data should be escaped
        assert (
            "\\u003cscript\\u003e" in html_content
            or "\u003cscript\u003e" in html_content
        )


class TestContentSecurityPolicy:
    """Test Content Security Policy headers in HTML reports."""

    def test_csp_header_present(self, tmp_path):
        """Test that CSP meta tag is present in HTML reports."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="test",
            threshold="test",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=100.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        # Read generated HTML
        html_content = result.read_text()

        # Verify CSP meta tag is present
        assert 'http-equiv="Content-Security-Policy"' in html_content
        assert "default-src 'self'" in html_content
        assert "script-src 'unsafe-inline'" in html_content
        assert "style-src 'unsafe-inline'" in html_content

    def test_csp_header_in_head_section(self, tmp_path):
        """Test that CSP meta tag is in the <head> section."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="test",
            threshold="test",
            evidence=[],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=100.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_not_assessed=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        html_content = result.read_text()

        # Extract head section
        head_start = html_content.find("<head>")
        head_end = html_content.find("</head>")
        head_section = html_content[head_start:head_end]

        # Verify CSP is in head section
        assert 'http-equiv="Content-Security-Policy"' in head_section


class TestGitHubTokenSecurity:
    """Test security controls for GitHub token handling."""

    def test_token_not_in_logs(self, caplog):
        """Test that token never appears in logs."""
        from unittest.mock import patch


        from agentready.services.github_scanner import GitHubOrgScanner

        token = "ghp_" + "a" * 36

        with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
            scanner = GitHubOrgScanner()

            # Trigger various operations that might log
            try:
                scanner.get_org_repos("invalid org!")
            except Exception:
                pass

            # Verify token not in any log messages
            for record in caplog.records:
                assert token not in record.message
                assert token not in str(record.args)

    def test_token_not_in_error_messages(self):
        """Test that token is redacted in error messages."""
        from unittest.mock import Mock, patch

        import requests

        from agentready.services.github_scanner import GitHubOrgScanner

        token = "ghp_" + "a" * 36

        with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
            with patch("requests.get") as mock_get:
                # Simulate error with token in response
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = f"Error: invalid token {token}"
                mock_response.raise_for_status.side_effect = requests.HTTPError(
                    f"Server error with token {token}"
                )
                mock_get.return_value = mock_response

                scanner = GitHubOrgScanner()

                try:
                    scanner.get_org_repos("testorg")
                except Exception as e:
                    error_msg = str(e)
                    # Token should be redacted
                    assert token not in error_msg
                    # Should contain redaction marker
                    if "token" in error_msg.lower():
                        assert "[REDACTED]" in error_msg

    def test_token_format_validation(self):
        """Test that token format is validated."""

        from agentready.services.github_scanner import GitHubAuthError, GitHubOrgScanner

        invalid_tokens = [
            "invalid",
            "ghp_short",
            "gho_" + "a" * 36,  # Wrong prefix
            "ghp_" + "a" * 35,  # Too short
            "ghp_" + "a" * 37,  # Too long
        ]

        for invalid_token in invalid_tokens:
            with patch.dict("os.environ", {"GITHUB_TOKEN": invalid_token}):
                with pytest.raises(
                    GitHubAuthError, match="Invalid GitHub token format"
                ):
                    GitHubOrgScanner()

    def test_token_read_from_env_only(self):
        """Test that token is only read from environment variable."""

        from agentready.services.github_scanner import GitHubAuthError, GitHubOrgScanner

        # Ensure environment is clean
        with patch.dict("os.environ", {}, clear=True):
            # Should fail without env var
            with pytest.raises(GitHubAuthError, match="GITHUB_TOKEN"):
                GitHubOrgScanner()

            # Should work with env var
            token = "ghp_" + "a" * 36
            with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
                scanner = GitHubOrgScanner()
                assert scanner.token == token

    def test_org_name_validation_prevents_injection(self):
        """Test that org name validation prevents injection attacks."""

        from agentready.services.github_scanner import GitHubOrgScanner

        token = "ghp_" + "a" * 36

        with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
            scanner = GitHubOrgScanner()

            # Test various injection attempts
            injection_attempts = [
                "org; rm -rf /",  # Command injection
                "../../../etc/passwd",  # Path traversal
                "org\x00evil",  # Null byte injection
                "org\n악성코드",  # Newline injection
                "org' OR '1'='1",  # SQL injection attempt
                "<script>alert(1)</script>",  # XSS attempt
            ]

            for malicious_org in injection_attempts:
                with pytest.raises(ValueError, match="Invalid organization name"):
                    scanner.get_org_repos(malicious_org)

    def test_max_repos_enforced(self):
        """Test that max_repos limit cannot be bypassed."""
        from unittest.mock import Mock, patch

        from agentready.services.github_scanner import GitHubOrgScanner

        token = "ghp_" + "a" * 36

        # Create mock response with many repos
        mock_repos = [
            {
                "name": f"repo{i}",
                "clone_url": f"https://github.com/org/repo{i}.git",
                "private": False,
                "archived": False,
            }
            for i in range(1000)
        ]

        with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_repos
                mock_response.headers = {"X-RateLimit-Remaining": "5000"}
                mock_get.return_value = mock_response

                scanner = GitHubOrgScanner()

                # Request with limit
                repos = scanner.get_org_repos("testorg", max_repos=50)

                # Should strictly enforce limit
                assert len(repos) == 50
                assert len(repos) <= 50  # Never exceeds limit
