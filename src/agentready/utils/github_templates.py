"""GitHub organization-level template fetching.

Checks for issue/PR templates at the organization level via the .github repo.
"""

import logging
import os
import re
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class GitHubTemplatesError(Exception):
    """GitHub template fetch errors."""

    pass


class GitHubTemplatesFetcher:
    """Fetches organization-level issue/PR templates from .github repos.

    GitHub organizations can define default community health files (issue
    templates, PR templates, CODEOWNERS, etc.) in a dedicated `.github`
    repository that is inherited by all repositories in the organization.
    """

    def __init__(self, token: Optional[str] = None):
        """Initialize the fetcher.

        Args:
            token: GitHub personal access token (optional, defaults to
                GITHUB_TOKEN environment variable)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._api_base = "https://api.github.com"

    @property
    def configured(self) -> bool:
        """Check if a GitHub token is available."""
        return bool(self.token)

    def _request_headers(self) -> dict:
        """Get default headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {self.token}" if self.token else None,
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "agentready",
        }

    def _fetch_contents(self, owner: str, repo: str, path: str = "") -> List[dict]:
        """Fetch directory contents from a GitHub repository.

        Args:
            owner: Repository owner/organization name
            repo: Repository name
            path: Path within the repository (defaults to root)

        Returns:
            List of file metadata dicts from GitHub API
        """
        url = f"{self._api_base}/repos/{owner}/{repo}/contents/{path.lstrip('/')}"

        try:
            response = requests.get(
                url,
                headers={k: v for k, v in self._request_headers().items() if v},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if response.status_code == 404:
                logger.debug("Path not found: %s/%s/%s", owner, repo, path)
                return []
            elif response.status_code in (401, 403):
                logger.debug("Unauthorized to access %s/%s/%s", owner, repo, path)
                return []
            raise GitHubTemplatesError(
                f"Failed to fetch contents: {owner}/{repo}/{path}"
            ) from e
        except requests.RequestException as e:
            raise GitHubTemplatesError(
                f"Request failed for {owner}/{repo}/{path}: {e}"
            ) from e

    def fetch_pr_templates(self, owner: str, repo_name: str = ".github") -> List[str]:
        """Check for PR templates in an organization-level .github repo.

        Args:
            owner: GitHub organization name
            repo_name: Repository name (defaults to '.github')

        Returns:
            List of PR template file paths found (e.g.
            ['PULL_REQUEST_TEMPLATE.md'])
        """
        if not self.configured:
            return []

        contents = self._fetch_contents(owner, repo_name, ".github")
        if not contents:
            return []

        pr_filenames = {
            "PULL_REQUEST_TEMPLATE.md": "PULL_REQUEST_TEMPLATE.md",
            "pull_request_template.md": "PULL_REQUEST_TEMPLATE.md",
        }

        found = []
        for item in contents:
            if item.get("type") == "file" and item.get("name") in pr_filenames:
                found.append(pr_filenames[item["name"]])

        return sorted(set(found))

    def fetch_issue_templates(
        self, owner: str, repo_name: str = ".github"
    ) -> List[str]:
        """Check for issue templates in an organization-level .github repo.

        Args:
            owner: GitHub organization name
            repo_name: Repository name (defaults to '.github')

        Returns:
            List of issue template file paths found (e.g.
            ['ISSUE_TEMPLATE/bug_report.md', 'ISSUE_TEMPLATE/feature_request.md'])
        """
        if not self.configured:
            return []

        contents = self._fetch_contents(owner, repo_name, ".github/ISSUE_TEMPLATE")
        if not contents:
            return []

        extensions = {".md", ".yml", ".yaml"}
        found = []
        for item in contents:
            name = item.get("name", "")
            if item.get("type") == "file" and any(
                name.endswith(ext) for ext in extensions
            ):
                found.append(f"ISSUE_TEMPLATE/{name}")

        return sorted(found)

    def extract_owner(self, url: str) -> str | None:
        """Extract the owner/organization from a GitHub repository URL.

        Supports HTTPS (https://github.com/owner/repo) and SSH
        (git@github.com:owner/repo.git) formats.

        Args:
            url: Repository URL string

        Returns:
            Owner/organization name or None if not parseable
        """
        if not url:
            return None

        # SSH format: git@github.com:owner/repo.git
        ssh_match = re.match(r"git@github\.com:([^/]+)/.+?$", url)
        if ssh_match:
            return ssh_match.group(1)

        # HTTPS: https://github.com/owner/repo.git or .gitignore etc
        https_match = re.match(r"https://github\.com/([^/]+)/.+?$", url)
        if https_match:
            return https_match.group(1)

        return None
