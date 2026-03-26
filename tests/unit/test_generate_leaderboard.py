"""Unit tests for leaderboard data generation script.

Regression tests for GitLab support — verifies that repository URLs
and display names are correctly derived from assessment JSON data.
"""

import sys
from pathlib import Path

# Add scripts directory to path so we can import the generation script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from importlib import import_module

# Import the module with hyphens in name
gen = import_module("generate-leaderboard-data")


class TestGitUrlToHttps:
    """Test git_url_to_https conversion."""

    def test_github_ssh_url(self):
        assert (
            gen.git_url_to_https("git@github.com:org/repo.git")
            == "https://github.com/org/repo"
        )

    def test_github_ssh_no_suffix(self):
        assert (
            gen.git_url_to_https("git@github.com:org/repo")
            == "https://github.com/org/repo"
        )

    def test_github_https_url(self):
        assert (
            gen.git_url_to_https("https://github.com/org/repo.git")
            == "https://github.com/org/repo"
        )

    def test_github_https_no_suffix(self):
        assert (
            gen.git_url_to_https("https://github.com/org/repo")
            == "https://github.com/org/repo"
        )

    def test_gitlab_ssh_deep_path(self):
        """Regression: GitLab SSH URLs with deep paths must convert correctly."""
        assert (
            gen.git_url_to_https("git@gitlab.com:redhat/rhel-ai/wheels/builder.git")
            == "https://gitlab.com/redhat/rhel-ai/wheels/builder"
        )

    def test_gitlab_https_deep_path(self):
        assert (
            gen.git_url_to_https("https://gitlab.com/redhat/rhel-ai/rhai/pipeline.git")
            == "https://gitlab.com/redhat/rhel-ai/rhai/pipeline"
        )

    def test_preserves_unknown_format(self):
        assert gen.git_url_to_https("some-other-url") == "some-other-url"


class TestRepoDisplayNameFromUrl:
    """Test repo_display_name_from_url extraction."""

    def test_github_ssh(self):
        assert (
            gen.repo_display_name_from_url("git@github.com:org/repo.git") == "org/repo"
        )

    def test_github_https(self):
        assert (
            gen.repo_display_name_from_url("https://github.com/org/repo") == "org/repo"
        )

    def test_gitlab_ssh_deep_path(self):
        """Regression: Full GitLab path must be preserved for display."""
        assert (
            gen.repo_display_name_from_url(
                "git@gitlab.com:redhat/rhel-ai/wheels/builder.git"
            )
            == "redhat/rhel-ai/wheels/builder"
        )

    def test_gitlab_https_deep_path(self):
        assert (
            gen.repo_display_name_from_url(
                "https://gitlab.com/redhat/rhel-ai/rhai/pipeline.git"
            )
            == "redhat/rhel-ai/rhai/pipeline"
        )

    def test_returns_none_for_unparseable(self):
        assert gen.repo_display_name_from_url("not-a-url") is None


class TestGenerateLeaderboardData:
    """Test the full leaderboard data generation with GitLab repos."""

    def _make_assessment(
        self, url, score=75.0, tier="Silver", attributes_assessed=25, attributes_total=25
    ):
        data = {
            "repository": {
                "url": url,
                "primary_language": "Python",
                "size_category": "Medium",
            },
            "overall_score": score,
            "certification_level": tier,
            "attributes_assessed": attributes_assessed,
            "attributes_total": attributes_total,
            "metadata": {
                "agentready_version": "2.30.1",
                "research_version": "1.0.1",
            },
        }
        return data

    def test_gitlab_repo_gets_correct_url(self):
        """Regression: GitLab repos must link to GitLab, not GitHub."""
        repos = {
            "redhat/builder": [
                {
                    "assessment": self._make_assessment(
                        "git@gitlab.com:redhat/rhel-ai/wheels/builder.git",
                        score=78.6,
                        tier="Gold",
                    ),
                    "timestamp": "2026-03-25T12-00-00",
                    "path": Path(
                        "submissions/redhat/builder/2026-03-25T12-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        assert entry["url"] == "https://gitlab.com/redhat/rhel-ai/wheels/builder"
        assert entry["repo"] == "redhat/rhel-ai/wheels/builder"
        assert entry["org"] == "redhat"
        assert entry["name"] == "builder"

    def test_github_repo_still_works(self):
        """Existing GitHub repos must continue to work correctly."""
        repos = {
            "org/repo": [
                {
                    "assessment": self._make_assessment(
                        "https://github.com/org/repo",
                        score=80.0,
                        tier="Gold",
                    ),
                    "timestamp": "2026-01-15T00-00-00",
                    "path": Path(
                        "submissions/org/repo/2026-01-15T00-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        assert entry["url"] == "https://github.com/org/repo"
        assert entry["repo"] == "org/repo"

    def test_fallback_when_no_url(self):
        """Repos without repository.url fall back to GitHub directory-derived URL."""
        repos = {
            "org/repo": [
                {
                    "assessment": {
                        "repository": {},
                        "overall_score": 60.0,
                        "certification_level": "Silver",
                        "metadata": {},
                    },
                    "timestamp": "2026-01-15T00-00-00",
                    "path": Path(
                        "submissions/org/repo/2026-01-15T00-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        # Falls back to GitHub URL constructed from directory path
        assert entry["url"] == "https://github.com/org/repo"
        assert entry["repo"] == "org/repo"

    def test_partial_assessment_attributes(self):
        """Issue #313: Partial assessments should include attribute counts."""
        repos = {
            "org/repo": [
                {
                    "assessment": self._make_assessment(
                        "https://github.com/org/repo",
                        score=72.0,
                        tier="Silver",
                        attributes_assessed=22,
                        attributes_total=25,
                    ),
                    "timestamp": "2026-03-01T00-00-00",
                    "path": Path(
                        "submissions/org/repo/2026-03-01T00-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        assert entry["attributes_assessed"] == 22
        assert entry["attributes_total"] == 25

    def test_full_assessment_attributes(self):
        """Full assessments (25/25) should also include attribute counts."""
        repos = {
            "org/repo": [
                {
                    "assessment": self._make_assessment(
                        "https://github.com/org/repo",
                        score=85.0,
                        tier="Gold",
                        attributes_assessed=25,
                        attributes_total=25,
                    ),
                    "timestamp": "2026-03-01T00-00-00",
                    "path": Path(
                        "submissions/org/repo/2026-03-01T00-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        assert entry["attributes_assessed"] == 25
        assert entry["attributes_total"] == 25

    def test_missing_attributes_defaults_to_25(self):
        """Old submissions without attribute fields default to 25/25."""
        repos = {
            "org/repo": [
                {
                    "assessment": {
                        "repository": {"url": "https://github.com/org/repo"},
                        "overall_score": 70.0,
                        "certification_level": "Silver",
                        "metadata": {},
                    },
                    "timestamp": "2026-01-01T00-00-00",
                    "path": Path(
                        "submissions/org/repo/2026-01-01T00-00-00-assessment.json"
                    ),
                }
            ]
        }

        result = gen.generate_leaderboard_data(repos)
        entry = result["overall"][0]

        assert entry["attributes_assessed"] == 25
        assert entry["attributes_total"] == 25
