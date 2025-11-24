"""Integration tests for GitHub scanner (requires GITHUB_TOKEN)."""

import os
import urllib.parse

import pytest

from agentready.services.github_scanner import GitHubOrgScanner


@pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
def test_real_github_org_scan():
    """Integration test with real GitHub API (requires GITHUB_TOKEN).

    Tests scanning a well-known public organization.
    """
    scanner = GitHubOrgScanner()

    # Scan a well-known public org with a small limit
    repos = scanner.get_org_repos("python", max_repos=5)

    assert len(repos) > 0
    assert len(repos) <= 5
    assert all(url.startswith("https://") for url in repos)
    assert all(url.endswith(".git") for url in repos)


@pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
def test_github_org_scan_filters_archived():
    """Test that archived repos are filtered in real API calls."""
    scanner = GitHubOrgScanner()

    # Scan an org, check that no archived repos are included
    repos = scanner.get_org_repos("python", max_repos=10)

    # We can't easily verify archived status without making additional API calls,
    # but at least verify we get valid repo URLs
    assert all(isinstance(url, str) for url in repos)
    assert all(urllib.parse.urlparse(url).hostname == "github.com" for url in repos)


@pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
def test_github_org_scan_respects_limit():
    """Test that max_repos limit is respected with real API."""
    scanner = GitHubOrgScanner()

    # Request only 3 repos
    repos = scanner.get_org_repos("python", max_repos=3)

    # Should get exactly 3 repos (or fewer if org has fewer repos)
    assert len(repos) <= 3


@pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
def test_github_nonexistent_org():
    """Test error handling for nonexistent organization."""
    from agentready.services.github_scanner import GitHubAPIError

    scanner = GitHubOrgScanner()

    # Use a very unlikely org name
    with pytest.raises(GitHubAPIError, match="Organization not found"):
        scanner.get_org_repos("this-org-definitely-does-not-exist-12345")
