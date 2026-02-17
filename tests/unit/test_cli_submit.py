"""Unit tests for CLI submit command."""

from agentready.cli.submit import extract_repo_info


class TestExtractRepoInfo:
    """Test extract_repo_info function."""

    def test_extract_repo_info_https_with_git_suffix(self):
        """Test extract_repo_info handles HTTPS .git suffix correctly."""
        assessment_data = {
            "repository": {"url": "https://github.com/feast-dev/feast.git"},
            "overall_score": 85.0,
            "certification_level": "Gold",
        }

        org, repo, score, tier = extract_repo_info(assessment_data)
        assert org == "feast-dev"
        assert repo == "feast"  # Not "feas"
        assert score == 85.0
        assert tier == "Gold"

    def test_extract_repo_info_https_without_git_suffix(self):
        """Test extract_repo_info handles HTTPS URL without .git suffix."""
        assessment_data = {
            "repository": {"url": "https://github.com/org/my-repo"},
            "overall_score": 70.0,
            "certification_level": "Silver",
        }

        org, repo, score, tier = extract_repo_info(assessment_data)
        assert org == "org"
        assert repo == "my-repo"

    def test_extract_repo_info_ssh_with_git_suffix(self):
        """Test extract_repo_info handles SSH .git suffix correctly."""
        assessment_data = {
            "repository": {"url": "git@github.com:feast-dev/feast.git"},
            "overall_score": 60.5,
            "certification_level": "Silver",
        }

        org, repo, score, tier = extract_repo_info(assessment_data)
        assert org == "feast-dev"
        assert repo == "feast"  # Not "feas"
        assert score == 60.5
        assert tier == "Silver"

    def test_extract_repo_info_ssh_without_git_suffix(self):
        """Test extract_repo_info handles SSH URL without .git suffix."""
        assessment_data = {
            "repository": {"url": "git@github.com:org/my-repo"},
            "overall_score": 90.0,
            "certification_level": "Gold",
        }

        org, repo, score, tier = extract_repo_info(assessment_data)
        assert org == "org"
        assert repo == "my-repo"

    def test_extract_repo_info_preserves_names_ending_in_git_chars(self):
        """Regression test: repo names ending in .git characters are preserved.

        rstrip('.git') incorrectly strips individual characters (., g, i, t)
        from the end of names. removesuffix('.git') is correct.
        """
        test_cases = [
            ("feast-dev/feast.git", "feast-dev", "feast"),  # Not "feas"
            ("user/audit.git", "user", "audit"),  # Not "aud"
            ("user/digit.git", "user", "digit"),  # Not "di"
            ("org/widget.git", "org", "widget"),  # Not "widge"
        ]

        for url_suffix, expected_org, expected_repo in test_cases:
            for url_template in [
                f"https://github.com/{url_suffix}",
                f"git@github.com:{url_suffix}",
            ]:
                assessment_data = {
                    "repository": {"url": url_template},
                    "overall_score": 80.0,
                    "certification_level": "Gold",
                }

                org, repo, score, tier = extract_repo_info(assessment_data)
                assert (
                    org == expected_org
                ), f"Expected org '{expected_org}' but got '{org}' for URL: {url_template}"
                assert (
                    repo == expected_repo
                ), f"Expected repo '{expected_repo}' but got '{repo}' for URL: {url_template}"
