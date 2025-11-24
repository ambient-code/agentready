"""GitHub organization scanner for discovering repositories.

SECURITY REQUIREMENTS:
- Token read from GITHUB_TOKEN environment variable only
- Token format validated (ghp_...)
- Token redacted in all logs and error messages
- Token never stored in files or database
- Organization name validated (alphanumeric + hyphens only)
- Repository limit enforced (default: 100)
- Rate limiting implemented
- API errors caught and sanitized
"""

import logging
import os
import re
import time
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class GitHubAuthError(Exception):
    """GitHub authentication errors."""

    pass


class GitHubAPIError(Exception):
    """GitHub API errors."""

    pass


class GitHubOrgScanner:
    """Discovers repositories from GitHub organizations.

    SECURITY REQUIREMENTS:
    - Token read from GITHUB_TOKEN environment variable only
    - Token MUST be redacted in all logs/errors
    - Enforce repository limit (default: 100)
    - Implement rate limiting
    - Validate org name (alphanumeric + hyphens only)
    """

    # GitHub token pattern (ghp_ followed by 36 alphanumeric characters)
    TOKEN_PATTERN = re.compile(r"^ghp_[a-zA-Z0-9]{36}$")

    # Organization name pattern (alphanumeric and hyphens, max 39 chars)
    ORG_PATTERN = re.compile(r"^[a-zA-Z0-9-]{1,39}$")

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub scanner.

        Args:
            token: GitHub personal access token (optional, defaults to GITHUB_TOKEN env var)

        Raises:
            GitHubAuthError: If token is missing or invalid
        """
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise GitHubAuthError(
                "GITHUB_TOKEN environment variable required for GitHub org scanning.\n"
                "Create a token at: https://github.com/settings/tokens\n"
                "Required scopes: repo:status, public_repo"
            )

        self._validate_token_format()

    def _validate_token_format(self):
        """Validate GitHub token format.

        SECURITY: Ensures token matches expected pattern
        """
        if not self.TOKEN_PATTERN.match(self.token):
            raise GitHubAuthError(
                "Invalid GitHub token format. Expected format: ghp_<36 characters>"
            )

    def _redact_token(self, text: str) -> str:
        """Redact token from text for safe logging.

        SECURITY: Prevents token exposure in logs/errors
        """
        if self.token in text:
            return text.replace(self.token, "[REDACTED]")
        return text

    def get_org_repos(
        self, org_name: str, include_private: bool = False, max_repos: int = 100
    ) -> List[str]:
        """Get all repository URLs from GitHub organization.

        Args:
            org_name: GitHub organization name
            include_private: Include private repos (default: False)
            max_repos: Maximum repositories to fetch (default: 100)

        Returns:
            List of git clone URLs (https)

        Raises:
            ValueError: If org name is invalid
            GitHubAPIError: If API request fails

        SECURITY:
        - Validates org name (prevent injection)
        - Enforces max_repos limit
        - Redacts token in error messages
        """
        # SECURITY: Validate org name
        if not self.ORG_PATTERN.match(org_name):
            raise ValueError(
                f"Invalid organization name: {org_name}\n"
                "Organization names must contain only alphanumeric characters and hyphens"
            )

        logger.info(f"Scanning GitHub organization: {org_name}")

        repos = []
        page = 1
        per_page = 100

        while len(repos) < max_repos:
            url = f"https://api.github.com/orgs/{org_name}/repos"
            params = {
                "page": page,
                "per_page": per_page,
                "type": "all" if include_private else "public",
            }

            try:
                response = requests.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()

            except requests.Timeout:
                raise GitHubAPIError(f"GitHub API timeout for organization: {org_name}")

            except requests.HTTPError as e:
                # SECURITY: Redact token before raising
                safe_error = self._redact_token(str(e))

                if response.status_code == 404:
                    raise GitHubAPIError(
                        f"Organization not found: {org_name}\n"
                        "Verify the organization name is correct and your token has access"
                    )
                elif response.status_code == 401:
                    raise GitHubAuthError(
                        "GitHub authentication failed. Check your GITHUB_TOKEN"
                    )
                elif response.status_code == 403:
                    # Check if rate limited
                    if "rate limit" in response.text.lower():
                        raise GitHubAPIError(
                            "GitHub API rate limit exceeded. Try again later or use authentication"
                        )
                    raise GitHubAuthError(
                        "GitHub authorization failed. Your token may lack required permissions"
                    )
                else:
                    raise GitHubAPIError(f"GitHub API error: {safe_error}")

            except requests.RequestException as e:
                # SECURITY: Redact token before raising
                safe_error = self._redact_token(str(e))
                raise GitHubAPIError(f"GitHub API request failed: {safe_error}")

            # Parse response
            try:
                batch = response.json()
            except ValueError:
                raise GitHubAPIError("Invalid JSON response from GitHub API")

            # No more repos
            if not batch:
                break

            # Filter and collect repos
            for repo in batch:
                # Skip private repos unless explicitly included
                if not include_private and repo.get("private", False):
                    continue

                # Skip archived repos
                if repo.get("archived", False):
                    logger.info(f"Skipping archived repo: {repo['name']}")
                    continue

                clone_url = repo.get("clone_url")
                if clone_url:
                    repos.append(clone_url)

                    if len(repos) >= max_repos:
                        logger.warning(
                            f"Reached repository limit ({max_repos}). "
                            "Increase --max-repos to scan more repositories"
                        )
                        break

            # Check rate limit headers
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining and int(remaining) < 10:
                logger.warning(
                    f"GitHub API rate limit low: {remaining} requests remaining"
                )

            # Next page
            page += 1

            # SECURITY: Basic rate limiting (avoid hammering API)
            time.sleep(0.2)

        logger.info(f"Found {len(repos)} repositories in {org_name}")
        return repos[:max_repos]
