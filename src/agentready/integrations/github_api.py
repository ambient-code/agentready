"""GitHub API integration for status checks and PR comments."""

import os
from dataclasses import dataclass
from typing import Any, Literal

import requests

CheckConclusion = Literal["success", "failure", "neutral", "cancelled", "skipped"]
StatusState = Literal["error", "failure", "pending", "success"]


@dataclass
class GitHubCheckRun:
    """Data for creating a GitHub Check Run."""

    name: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: CheckConclusion | None = None
    output_title: str | None = None
    output_summary: str | None = None
    output_text: str | None = None
    details_url: str | None = None


@dataclass
class GitHubStatus:
    """Data for creating a GitHub Commit Status."""

    state: StatusState
    description: str
    context: str = "agentready/assessment"
    target_url: str | None = None


class GitHubAPIClient:
    """Client for GitHub API interactions (Status API, Checks API, Comments)."""

    def __init__(self, token: str | None = None, repo: str | None = None):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            repo: Repository in "owner/name" format (defaults to GITHUB_REPOSITORY env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPOSITORY")
        self.api_base = "https://api.github.com"

        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or pass token parameter."
            )
        if not self.repo:
            raise ValueError(
                "Repository required. Set GITHUB_REPOSITORY env var or pass repo parameter."
            )

    @property
    def headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentReady-Integration",
        }

    def create_commit_status(
        self, commit_sha: str, status: GitHubStatus
    ) -> dict[str, Any]:
        """
        Create a commit status using GitHub Status API.

        Args:
            commit_sha: Git commit SHA
            status: Status information

        Returns:
            API response data

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.api_base}/repos/{self.repo}/statuses/{commit_sha}"

        payload = {
            "state": status.state,
            "description": status.description,
            "context": status.context,
        }
        if status.target_url:
            payload["target_url"] = status.target_url

        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_check_run(
        self, commit_sha: str, check: GitHubCheckRun
    ) -> dict[str, Any]:
        """
        Create a check run using GitHub Checks API.

        Args:
            commit_sha: Git commit SHA
            check: Check run information

        Returns:
            API response data

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.api_base}/repos/{self.repo}/check-runs"

        payload = {
            "name": check.name,
            "head_sha": commit_sha,
            "status": check.status,
        }

        if check.conclusion:
            payload["conclusion"] = check.conclusion

        if check.output_title or check.output_summary or check.output_text:
            payload["output"] = {}
            if check.output_title:
                payload["output"]["title"] = check.output_title
            if check.output_summary:
                payload["output"]["summary"] = check.output_summary
            if check.output_text:
                payload["output"]["text"] = check.output_text

        if check.details_url:
            payload["details_url"] = check.details_url

        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_pr_comment(self, pr_number: int, body: str) -> dict[str, Any]:
        """
        Create a comment on a pull request.

        Args:
            pr_number: Pull request number
            body: Comment body (Markdown supported)

        Returns:
            API response data

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.api_base}/repos/{self.repo}/issues/{pr_number}/comments"

        payload = {"body": body}

        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def update_pr_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        """
        Update an existing PR comment.

        Args:
            comment_id: Comment ID
            body: Updated comment body

        Returns:
            API response data

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.api_base}/repos/{self.repo}/issues/comments/{comment_id}"

        payload = {"body": body}

        response = requests.patch(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def find_existing_comment(
        self, pr_number: int, search_text: str = "AgentReady Assessment"
    ) -> int | None:
        """
        Find existing bot comment on PR.

        Args:
            pr_number: Pull request number
            search_text: Text to search for in comments

        Returns:
            Comment ID if found, None otherwise
        """
        url = f"{self.api_base}/repos/{self.repo}/issues/{pr_number}/comments"

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        comments = response.json()
        for comment in comments:
            if search_text in comment.get("body", ""):
                return comment["id"]

        return None
