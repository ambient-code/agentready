"""Unit tests for GitHub organization scanner."""

from unittest.mock import Mock, patch

import pytest
import requests

from agentready.services.github_scanner import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubOrgScanner,
)


def test_missing_token():
    """Test that missing token raises error."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(GitHubAuthError, match="GITHUB_TOKEN"):
            GitHubOrgScanner()


def test_invalid_token_format():
    """Test that invalid token format raises error."""
    with patch.dict("os.environ", {"GITHUB_TOKEN": "invalid_token"}):
        with pytest.raises(GitHubAuthError, match="Invalid GitHub token format"):
            GitHubOrgScanner()


def test_valid_token_format():
    """Test that valid token format is accepted."""
    token = "ghp_" + "a" * 36
    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        assert scanner.token == token


def test_invalid_org_name():
    """Test that invalid org name raises error."""
    token = "ghp_" + "a" * 36
    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()

        # Test various invalid org names
        invalid_names = [
            "invalid org name!",  # Spaces
            "org/name",  # Slashes
            "org@name",  # Special characters
            "a" * 40,  # Too long
            "",  # Empty
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid organization name"):
                scanner.get_org_repos(invalid_name)


def test_valid_org_names():
    """Test that valid org names are accepted."""
    token = "ghp_" + "a" * 36

    valid_names = [
        "github",
        "anthropics",
        "my-org",
        "org123",
        "a",  # Single character
        "a" * 39,  # Max length
    ]

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()

        with patch("requests.get") as mock_get:
            # Mock empty response (no repos)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {"X-RateLimit-Remaining": "5000"}
            mock_get.return_value = mock_response

            for valid_name in valid_names:
                # Should not raise
                repos = scanner.get_org_repos(valid_name)
                assert repos == []


def test_token_redaction():
    """Test that token is redacted in error messages."""
    token = "ghp_" + "a" * 36
    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()

        # Test redaction
        text = f"Error with token {token}"
        redacted = scanner._redact_token(text)
        assert token not in redacted
        assert "[REDACTED]" in redacted

        # Test no change if token not present
        text_without_token = "Error without token"
        assert scanner._redact_token(text_without_token) == text_without_token


@patch("requests.get")
def test_successful_org_scan(mock_get):
    """Test successful organization scan."""
    token = "ghp_" + "a" * 36

    # Mock API response - return repos on first call, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        # First call returns 2 repos, second call returns empty (no more pages)
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_response.json.return_value = [
                {
                    "name": "repo1",
                    "clone_url": "https://github.com/org/repo1.git",
                    "private": False,
                    "archived": False,
                },
                {
                    "name": "repo2",
                    "clone_url": "https://github.com/org/repo2.git",
                    "private": False,
                    "archived": False,
                },
            ]
        else:
            mock_response.json.return_value = []

        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg")

        assert len(repos) == 2
        assert "https://github.com/org/repo1.git" in repos
        assert "https://github.com/org/repo2.git" in repos


@patch("requests.get")
def test_filters_private_repos(mock_get):
    """Test that private repos are filtered by default."""
    token = "ghp_" + "a" * 36

    # Mock API response - return repos on first call, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_response.json.return_value = [
                {
                    "name": "public-repo",
                    "clone_url": "https://github.com/org/public.git",
                    "private": False,
                    "archived": False,
                },
                {
                    "name": "private-repo",
                    "clone_url": "https://github.com/org/private.git",
                    "private": True,
                    "archived": False,
                },
            ]
        else:
            mock_response.json.return_value = []

        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg", include_private=False)

        assert len(repos) == 1
        assert "https://github.com/org/public.git" in repos


@patch("requests.get")
def test_includes_private_repos_when_requested(mock_get):
    """Test that private repos are included when requested."""
    token = "ghp_" + "a" * 36

    # Mock API response - return repos on first call, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_response.json.return_value = [
                {
                    "name": "public-repo",
                    "clone_url": "https://github.com/org/public.git",
                    "private": False,
                    "archived": False,
                },
                {
                    "name": "private-repo",
                    "clone_url": "https://github.com/org/private.git",
                    "private": True,
                    "archived": False,
                },
            ]
        else:
            mock_response.json.return_value = []

        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg", include_private=True)

        assert len(repos) == 2
        assert "https://github.com/org/public.git" in repos
        assert "https://github.com/org/private.git" in repos


@patch("requests.get")
def test_filters_archived_repos(mock_get):
    """Test that archived repos are always filtered."""
    token = "ghp_" + "a" * 36

    # Mock API response - return repos on first call, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_response.json.return_value = [
                {
                    "name": "active-repo",
                    "clone_url": "https://github.com/org/active.git",
                    "private": False,
                    "archived": False,
                },
                {
                    "name": "archived-repo",
                    "clone_url": "https://github.com/org/archived.git",
                    "private": False,
                    "archived": True,
                },
            ]
        else:
            mock_response.json.return_value = []

        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg")

        assert len(repos) == 1
        assert "https://github.com/org/active.git" in repos


@patch("requests.get")
def test_respects_max_repos_limit(mock_get):
    """Test that max_repos limit is enforced."""
    token = "ghp_" + "a" * 36

    # Return 150 repos in first batch, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_repos = [
                {
                    "name": f"repo{i}",
                    "clone_url": f"https://github.com/org/repo{i}.git",
                    "private": False,
                    "archived": False,
                }
                for i in range(150)
            ]
            mock_response.json.return_value = mock_repos
        else:
            mock_response.json.return_value = []

        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg", max_repos=10)

        assert len(repos) == 10


@patch("requests.get")
def test_pagination(mock_get):
    """Test that pagination works correctly."""
    token = "ghp_" + "a" * 36

    # First page: 100 repos
    page1_repos = [
        {
            "name": f"repo{i}",
            "clone_url": f"https://github.com/org/repo{i}.git",
            "private": False,
            "archived": False,
        }
        for i in range(100)
    ]

    # Second page: 50 repos
    page2_repos = [
        {
            "name": f"repo{i}",
            "clone_url": f"https://github.com/org/repo{i}.git",
            "private": False,
            "archived": False,
        }
        for i in range(100, 150)
    ]

    # Third page: empty (no more repos)
    page3_repos = []

    responses = [page1_repos, page2_repos, page3_repos]
    call_count = [0]

    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = responses[call_count[0]]
        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        call_count[0] += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg", max_repos=200)

        # Should get all 150 repos (stopped at empty page)
        assert len(repos) == 150


@patch("requests.get")
def test_handles_404_org_not_found(mock_get):
    """Test handling of 404 (org not found)."""
    token = "ghp_" + "a" * 36

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.HTTPError()
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAPIError, match="Organization not found"):
            scanner.get_org_repos("nonexistent")


@patch("requests.get")
def test_handles_401_auth_failed(mock_get):
    """Test handling of 401 (authentication failed)."""
    token = "ghp_" + "a" * 36

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = requests.HTTPError()
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAuthError, match="authentication failed"):
            scanner.get_org_repos("testorg")


@patch("requests.get")
def test_handles_403_rate_limit(mock_get):
    """Test handling of 403 (rate limit exceeded)."""
    token = "ghp_" + "a" * 36

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "API rate limit exceeded for user"
    mock_response.raise_for_status.side_effect = requests.HTTPError()
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAPIError, match="rate limit exceeded"):
            scanner.get_org_repos("testorg")


@patch("requests.get")
def test_handles_403_authorization_failed(mock_get):
    """Test handling of 403 (authorization failed, not rate limit)."""
    token = "ghp_" + "a" * 36

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden: insufficient permissions"
    mock_response.raise_for_status.side_effect = requests.HTTPError()
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAuthError, match="authorization failed"):
            scanner.get_org_repos("testorg")


@patch("requests.get")
def test_handles_timeout(mock_get):
    """Test handling of request timeout."""
    token = "ghp_" + "a" * 36

    mock_get.side_effect = requests.Timeout()

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAPIError, match="timeout"):
            scanner.get_org_repos("testorg")


@patch("requests.get")
def test_handles_invalid_json(mock_get):
    """Test handling of invalid JSON response."""
    token = "ghp_" + "a" * 36

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAPIError, match="Invalid JSON"):
            scanner.get_org_repos("testorg")


@patch("requests.get")
def test_token_redacted_in_request_exception(mock_get):
    """Test that token is redacted when RequestException contains it."""
    token = "ghp_" + "a" * 36

    # Simulate error message containing token
    mock_get.side_effect = requests.RequestException(f"Connection error with {token}")

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        with pytest.raises(GitHubAPIError) as exc_info:
            scanner.get_org_repos("testorg")

        # Verify token is redacted in error message
        error_msg = str(exc_info.value)
        assert token not in error_msg
        assert "[REDACTED]" in error_msg


@patch("requests.get")
def test_rate_limit_warning(mock_get, caplog):
    """Test that low rate limit triggers warning."""
    token = "ghp_" + "a" * 36

    # Mock API response - return repos on first call, empty on second
    def mock_get_side_effect(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        if not hasattr(mock_get_side_effect, "call_count"):
            mock_get_side_effect.call_count = 0

        if mock_get_side_effect.call_count == 0:
            mock_response.json.return_value = [
                {
                    "name": "repo1",
                    "clone_url": "https://github.com/org/repo1.git",
                    "private": False,
                    "archived": False,
                }
            ]
        else:
            mock_response.json.return_value = []

        # Low rate limit
        mock_response.headers = {"X-RateLimit-Remaining": "5"}
        mock_get_side_effect.call_count += 1
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    with patch.dict("os.environ", {"GITHUB_TOKEN": token}):
        scanner = GitHubOrgScanner()
        repos = scanner.get_org_repos("testorg")

        assert len(repos) == 1
        # Should have logged a warning about low rate limit
        assert any(
            "rate limit low" in record.message.lower() for record in caplog.records
        )
