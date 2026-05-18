"""Unit tests for GitHubTemplatesFetcher."""

from unittest.mock import patch

from agentready.utils.github_templates import GitHubTemplatesFetcher


class TestGitHubTemplatesFetcherExtractOwner:
    """Test owner extraction from repository URLs."""

    def test_https_url(self):
        """Test extracting owner from HTTPS URL."""
        fetcher = GitHubTemplatesFetcher()
        owner = fetcher.extract_owner("https://github.com/kagenti/kagenti")
        assert owner == "kagenti"

    def test_https_url_with_git_suffix(self):
        """Test extracting owner from HTTPS URL with .git suffix."""
        fetcher = GitHubTemplatesFetcher()
        owner = fetcher.extract_owner("https://github.com/owner/repo.git")
        assert owner == "owner"

    def test_ssh_url(self):
        """Test extracting owner from SSH URL."""
        fetcher = GitHubTemplatesFetcher()
        owner = fetcher.extract_owner("git@github.com:kagenti/kagenti.git")
        assert owner == "kagenti"

    def test_ssh_url_with_git_suffix(self):
        """Test extracting owner from SSH URL with .git suffix."""
        fetcher = GitHubTemplatesFetcher()
        owner = fetcher.extract_owner("git@github.com:owner/repo.git")
        assert owner == "owner"

    def test_none_url(self):
        """Test that None URL returns None."""
        fetcher = GitHubTemplatesFetcher()
        assert fetcher.extract_owner(None) is None

    def test_empty_url(self):
        """Test that empty string returns None."""
        fetcher = GitHubTemplatesFetcher()
        assert fetcher.extract_owner("") is None

    def test_non_github_url(self):
        """Test that non-GitHub URLs return None."""
        fetcher = GitHubTemplatesFetcher()
        assert fetcher.extract_owner("https://gitlab.com/owner/repo") is None
        assert fetcher.extract_owner("https://bitbucket.org/owner/repo") is None

    @patch.dict("os.environ", {}, clear=True)
    def test_no_token_returns_empty(self):
        """Test that without token, no templates are fetched."""
        fetcher = GitHubTemplatesFetcher()
        assert fetcher.configured is False
        assert fetcher.fetch_pr_templates("kagenti") == []
        assert fetcher.fetch_issue_templates("kagenti") == []


class TestGitHubTemplatesFetcherConfigured:
    """Test configured property."""

    def test_configured_with_token(self):
        """Test that configured is True when token is provided."""
        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        assert fetcher.configured is True

    @patch.dict("os.environ", {}, clear=True)
    def test_not_configured_without_token(self):
        """Test that configured is False without token."""
        fetcher = GitHubTemplatesFetcher()
        assert fetcher.configured is False


class TestGitHubTemplatesFetcherFetchPrTemplates:
    """Test PR template fetching from org-level .github repo."""

    @patch.dict("os.environ", {}, clear=True)
    def test_no_token_returns_empty(self):
        """Test that missing token returns empty list."""
        fetcher = GitHubTemplatesFetcher()
        result = fetcher.fetch_pr_templates("owner")
        assert result == []

    @patch("agentready.utils.github_templates.requests.get")
    def test_no_repo_returns_empty(self, mock_get):
        """Test that non-existent .github repo returns empty."""
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = None

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_pr_templates("kagenti")
        assert result == []

    @patch("agentready.utils.github_templates.requests.get")
    def test_finds_pr_template(self, mock_get):
        """Test finding a PR template in org .github repo."""
        mock_get.return_value.json.return_value = [
            {
                "type": "file",
                "name": "PULL_REQUEST_TEMPLATE.md",
                "path": "PULL_REQUEST_TEMPLATE.md",
            }
        ]
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.status_code = 200

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_pr_templates("kagenti")
        assert "PULL_REQUEST_TEMPLATE.md" in result

    @patch("agentready.utils.github_templates.requests.get")
    def test_returns_all_pr_templates(self, mock_get):
        """Test returning multiple PR templates."""
        mock_get.return_value.json.return_value = [
            {
                "type": "file",
                "name": "PULL_REQUEST_TEMPLATE.md",
                "path": "PULL_REQUEST_TEMPLATE.md",
            },
            {
                "type": "file",
                "name": "pull_request_template.md",
                "path": "pull_request_template.md",
            },
        ]
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.status_code = 200

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_pr_templates("kagenti")
        assert result == ["PULL_REQUEST_TEMPLATE.md"]


class TestGitHubTemplatesFetcherFetchIssueTemplates:
    """Test issue template fetching from org-level .github repo."""

    @patch.dict("os.environ", {}, clear=True)
    def test_no_token_returns_empty(self):
        """Test that missing token returns empty list."""
        fetcher = GitHubTemplatesFetcher()
        result = fetcher.fetch_issue_templates("owner")
        assert result == []

    @patch("agentready.utils.github_templates.requests.get")
    def test_no_repo_returns_empty(self, mock_get):
        """Test that non-existent .github repo returns empty."""
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = None

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_issue_templates("kagenti")
        assert result == []

    @patch("agentready.utils.github_templates.requests.get")
    def test_finds_issue_templates(self, mock_get):
        """Test finding issue templates in org .github repo."""
        mock_get.return_value.json.return_value = [
            {
                "type": "file",
                "name": "bug_report.md",
                "path": ".github/ISSUE_TEMPLATE/bug_report.md",
            },
            {
                "type": "file",
                "name": "feature_request.md",
                "path": ".github/ISSUE_TEMPLATE/feature_request.md",
            },
        ]
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.status_code = 200

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_issue_templates("kagenti")
        assert len(result) == 2
        assert "ISSUE_TEMPLATE/bug_report.md" in result
        assert "ISSUE_TEMPLATE/feature_request.md" in result

    @patch("agentready.utils.github_templates.requests.get")
    def test_finds_yml_templates(self, mock_get):
        """Test finding YAML-based issue templates."""
        mock_get.return_value.json.return_value = [
            {
                "type": "file",
                "name": "config.yml",
                "path": ".github/ISSUE_TEMPLATE/config.yml",
            },
            {
                "type": "file",
                "name": "bug_report.yml",
                "path": ".github/ISSUE_TEMPLATE/bug_report.yml",
            },
        ]
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.status_code = 200

        fetcher = GitHubTemplatesFetcher(token="ghp_test123456789012345678901234567890")
        result = fetcher.fetch_issue_templates("kagenti")
        assert len(result) == 2
        assert "ISSUE_TEMPLATE/config.yml" in result
        assert "ISSUE_TEMPLATE/bug_report.yml" in result
