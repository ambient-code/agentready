"""Tests for IssuePRTemplatesAssessor with org-level template support."""

from unittest.mock import patch

import pytest

from agentready.assessors.structure import IssuePRTemplatesAssessor
from agentready.models.repository import Repository


class TestIssuePRTemplatesAssessorBasic:
    """Test basic issue/PR template checking (local templates only)."""

    @pytest.fixture
    def repo_path(self, tmp_path):
        """Create a test repository with .git directory."""
        (tmp_path / ".git").mkdir()
        return tmp_path

    def test_pass_with_complete_local_templates(self, repo_path):
        """Test passing when all templates exist locally."""
        # PR template
        (repo_path / ".github").mkdir()
        (repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("PR template")

        # Issue templates
        issue_dir = repo_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir()
        (issue_dir / "bug_report.md").write_text("bug")
        (issue_dir / "feature_request.md").write_text("feature")

        repo = Repository(
            path=repo_path,
            name="test-repo",
            url="https://github.com/owner/repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "PR template found" in finding.evidence
        assert "Issue templates found: 2 templates" in finding.evidence

    def test_fail_without_any_templates(self, repo_path):
        """Test failing when no templates exist."""
        repo = Repository(
            path=repo_path,
            name="test-repo",
            url="https://github.com/owner/repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0
        assert "No PR template found" in finding.evidence
        assert "No issue template directory found" in finding.evidence


class TestIssuePRTemplatesAssessorOrgFallback:
    """Test org-level .github repo fallback."""

    @pytest.fixture
    def repo_path(self, tmp_path):
        """Create a test repository with .git directory."""
        (tmp_path / ".git").mkdir()
        return tmp_path

    @patch("agentready.utils.github_templates.requests.get")
    @patch("agentready.utils.github_templates.GitHubTemplatesFetcher.extract_owner")
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_pr_templates"
    )
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_issue_templates"
    )
    @patch.dict(
        "os.environ", {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890"}
    )
    def test_passes_with_org_level_templates_only(
        self, mock_fetch_issues, mock_fetch_pr, mock_extract_owner, mock_get, repo_path
    ):
        """Test passing when only org-level .github repo has templates."""
        mock_extract_owner.return_value = "kagenti"
        mock_fetch_pr.return_value = ["PULL_REQUEST_TEMPLATE.md"]
        mock_fetch_issues.return_value = [
            "ISSUE_TEMPLATE/bug_report.md",
            "ISSUE_TEMPLATE/feature_request.md",
        ]
        mock_get.return_value.status_code = 200

        repo = Repository(
            path=repo_path,
            name="kagenti",
            url="https://github.com/kagenti/kagenti",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "inherited from org-level .github repo" in finding.evidence[0]

    @patch("agentready.utils.github_templates.requests.get")
    @patch("agentready.utils.github_templates.GitHubTemplatesFetcher.extract_owner")
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_pr_templates"
    )
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_issue_templates"
    )
    @patch.dict(
        "os.environ", {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890"}
    )
    def test_local_only_no_org_check_when_complete(
        self, mock_fetch_issues, mock_fetch_pr, mock_extract_owner, mock_get, repo_path
    ):
        """Test no org-level check when all local templates exist."""
        # Set up complete local templates
        (repo_path / ".github").mkdir()
        (repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("PR")
        issue_dir = repo_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir()
        (issue_dir / "bug_report.md").write_text("bug")
        (issue_dir / "feature_request.md").write_text("feature")

        mock_extract_owner.return_value = "kagenti"

        repo = Repository(
            path=repo_path,
            name="test-repo",
            url="https://github.com/owner/test-repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        # extract_owner should not be called because both local checks succeed
        mock_extract_owner.assert_not_called()

    @patch("agentready.utils.github_templates.requests.get")
    @patch("agentready.utils.github_templates.GitHubTemplatesFetcher.extract_owner")
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_pr_templates"
    )
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_issue_templates"
    )
    @patch.dict(
        "os.environ", {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890"}
    )
    def test_passes_with_partial_org_templates_combined_with_local(
        self, mock_fetch_issues, mock_fetch_pr, mock_extract_owner, mock_get, repo_path
    ):
        """Test passing when PR is from org but issue templates are local."""
        # Local PR template
        (repo_path / ".github").mkdir()
        (repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("PR")

        # Local issue templates (1 template - partial)
        issue_dir = repo_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir()
        (issue_dir / "bug_report.md").write_text("bug")

        mock_extract_owner.return_value = "owner"
        mock_fetch_issues.return_value = []

        repo = Repository(
            path=repo_path,
            name="test",
            url="https://github.com/owner/test",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        # Should get 50 (PR) + 25 (1 local issue template) = 75 = pass
        assert finding.score == 75.0
        assert finding.status == "pass"

    @patch("agentready.utils.github_templates.requests.get")
    @patch("agentready.utils.github_templates.GitHubTemplatesFetcher.extract_owner")
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_pr_templates"
    )
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_issue_templates"
    )
    @patch.dict(
        "os.environ", {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890"}
    )
    def test_fail_when_no_org_templates(
        self, mock_fetch_issues, mock_fetch_pr, mock_extract_owner, mock_get, repo_path
    ):
        """Test still fails when no local or org templates exist."""
        mock_extract_owner.return_value = "kagenti"
        mock_fetch_pr.return_value = []
        mock_fetch_issues.return_value = []

        repo = Repository(
            path=repo_path,
            name="kagenti",
            url="https://github.com/kagenti/kagenti",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0

    def test_no_token_no_org_check(self, tmp_path):
        """Test that without GITHUB_TOKEN, org-level checks are skipped."""
        # No local templates at all - pure fail without org fallback
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / ".git").mkdir()

        with patch.dict("os.environ", clear=True):
            from agentready.models.repository import Repository

            repo = Repository(
                path=tmp_path,
                name="kagenti",
                url="https://github.com/kagenti/kagenti",
                branch="main",
                commit_hash="abc123",
                languages={"Python": 100},
                total_files=10,
                total_lines=100,
            )

            finding = IssuePRTemplatesAssessor().assess(repo)

            # Should fail since no local templates and no token for org fallback
            assert finding.status == "fail"
            assert finding.score == 0
            assert "No PR template found" in finding.evidence
            assert "No issue template directory found" in finding.evidence

    @patch("agentready.utils.github_templates.requests.get")
    @patch("agentready.utils.github_templates.GitHubTemplatesFetcher.extract_owner")
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_pr_templates"
    )
    @patch(
        "agentready.utils.github_templates.GitHubTemplatesFetcher.fetch_issue_templates"
    )
    @patch.dict(
        "os.environ", {"GITHUB_TOKEN": "ghp_test123456789012345678901234567890"}
    )
    def test_fallback_with_no_owner(
        self, mock_fetch_issues, mock_fetch_pr, mock_extract_owner, mock_get, repo_path
    ):
        """Test fallback when owner cannot be extracted from URL."""
        mock_extract_owner.return_value = None  # Can't extract owner

        repo = Repository(
            path=repo_path,
            name="test-repo",
            url="https://gitlab.com/some/other/repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        finding = IssuePRTemplatesAssessor().assess(repo)

        assert finding.status == "fail"
        assert "No issue template directory found" in finding.evidence
        assert "No PR template found" in finding.evidence
