"""Unit tests for align CLI command."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentready.cli.align import align, get_certification_level


@pytest.fixture
def temp_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()
        yield repo_path


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestGetCertificationLevel:
    """Test get_certification_level helper function."""

    def test_platinum_level(self):
        """Test Platinum certification level (90+)."""
        level, emoji = get_certification_level(95.0)
        assert level == "Platinum"
        assert emoji == "💎"

    def test_gold_level(self):
        """Test Gold certification level (75-89)."""
        level, emoji = get_certification_level(80.0)
        assert level == "Gold"
        assert emoji == "🥇"

    def test_silver_level(self):
        """Test Silver certification level (60-74)."""
        level, emoji = get_certification_level(65.0)
        assert level == "Silver"
        assert emoji == "🥈"

    def test_bronze_level(self):
        """Test Bronze certification level (40-59)."""
        level, emoji = get_certification_level(50.0)
        assert level == "Bronze"
        assert emoji == "🥉"

    def test_needs_improvement_level(self):
        """Test Needs Improvement level (<40)."""
        level, emoji = get_certification_level(30.0)
        assert level == "Needs Improvement"
        assert emoji == "📊"

    def test_boundary_90(self):
        """Test exact boundary at 90."""
        level, emoji = get_certification_level(90.0)
        assert level == "Platinum"

    def test_boundary_75(self):
        """Test exact boundary at 75."""
        level, emoji = get_certification_level(75.0)
        assert level == "Gold"

    def test_boundary_60(self):
        """Test exact boundary at 60."""
        level, emoji = get_certification_level(60.0)
        assert level == "Silver"

    def test_boundary_40(self):
        """Test exact boundary at 40."""
        level, emoji = get_certification_level(40.0)
        assert level == "Bronze"

    def test_zero_score(self):
        """Test zero score."""
        level, emoji = get_certification_level(0.0)
        assert level == "Needs Improvement"

    def test_hundred_score(self):
        """Test perfect score."""
        level, emoji = get_certification_level(100.0)
        assert level == "Platinum"


@pytest.mark.skip(
    reason="Tests use outdated mocks - LanguageDetector is not imported in align.py. Tests need to be updated to match current implementation."
)
class TestAlignCommand:
    """Test align CLI command."""

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_basic_execution(self, mock_fixer, mock_scanner, runner, temp_repo):
        """Test basic align command execution."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 75.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 75.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0
        assert "AgentReady Align" in result.output

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_dry_run(self, mock_fixer, mock_scanner, runner, temp_repo):
        """Test align command in dry-run mode."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 75.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 75.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo), "--dry-run"])

        # Should succeed and indicate dry run
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_with_specific_attributes(
        self, mock_fixer, mock_scanner, runner, temp_repo
    ):
        """Test align command with specific attributes."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 75.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 75.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(
            align, [str(temp_repo), "--attributes", "claude_md_file,gitignore_file"]
        )

        # Should succeed
        assert result.exit_code == 0

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_interactive_mode(self, mock_fixer, mock_scanner, runner, temp_repo):
        """Test align command in interactive mode."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 75.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 75.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo), "--interactive"])

        # Should succeed
        assert result.exit_code == 0

    def test_align_not_git_repository(self, runner):
        """Test align command on non-git repository."""
        with runner.isolated_filesystem():
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)
                # Don't create .git directory

                result = runner.invoke(align, [str(repo_path)])

                # Should fail with error message
                assert result.exit_code != 0
                assert "git repository" in result.output.lower()

    def test_align_nonexistent_repository(self, runner):
        """Test align command with non-existent path."""
        result = runner.invoke(align, ["/nonexistent/path"])

        # Should fail
        assert result.exit_code != 0

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_with_fixes_available(
        self, mock_fixer, mock_scanner, runner, temp_repo
    ):
        """Test align command when fixes are available."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.findings = [MagicMock()]
        mock_scanner.return_value.scan.return_value = mock_assessment

        # Mock fixes
        mock_fix = MagicMock()
        mock_fix.attribute_id = "test_attribute"
        mock_fix.description = "Test fix"
        mock_fix.files_modified = ["test.py"]
        mock_fix.preview.return_value = "Preview of fix"
        mock_fix.points_gained = 5.0

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = [mock_fix]
        mock_fix_plan.projected_score = 70.0
        mock_fix_plan.points_gained = 5.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        # Mock apply_fixes to return success
        mock_fixer.return_value.apply_fixes.return_value = {
            "succeeded": 1,
            "failed": 0,
            "failures": [],
        }

        # Provide "y" input to confirm applying fixes
        result = runner.invoke(align, [str(temp_repo)], input="y\n")

        # Should succeed and show fixes
        assert result.exit_code == 0

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_shows_score_improvement(
        self, mock_fixer, mock_scanner, runner, temp_repo
    ):
        """Test align command shows score improvement."""
        # Setup mocks

        # First assessment (lower score)
        mock_assessment1 = MagicMock()
        mock_assessment1.overall_score = 65.0
        mock_assessment1.findings = [MagicMock()]
        mock_scanner.return_value.scan.return_value = mock_assessment1

        # Mock fix plan with fixes available
        mock_fix = MagicMock()
        mock_fix.attribute_id = "test_attribute"
        mock_fix.description = "Test fix"
        mock_fix.preview.return_value = "Preview of fix"
        mock_fix.points_gained = 20.0

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = [mock_fix]
        mock_fix_plan.projected_score = 85.0
        mock_fix_plan.points_gained = 20.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        # Mock apply_fixes to return success
        mock_fixer.return_value.apply_fixes.return_value = {
            "succeeded": 1,
            "failed": 0,
            "failures": [],
        }

        # Provide "y" input to confirm applying fixes
        result = runner.invoke(align, [str(temp_repo)], input="y\n")

        # Should succeed
        assert result.exit_code == 0

    @patch("agentready.cli.align.Scanner")
    def test_align_scanner_error(self, mock_scanner, runner, temp_repo):
        """Test align command when scanner raises error."""
        # Setup mocks
        mock_scanner.return_value.scan.side_effect = Exception("Scanner error")

        result = runner.invoke(align, [str(temp_repo)])

        # Should handle error gracefully
        assert result.exit_code != 0

    def test_align_default_repository(self, runner):
        """Test align command with default repository (current directory)."""
        with runner.isolated_filesystem():
            # Create minimal git repo
            Path(".git").mkdir()

            with (
                patch("agentready.cli.align.Scanner") as mock_scanner,
                patch("agentready.cli.align.FixerService") as mock_fixer,
            ):

                mock_assessment = MagicMock()
                mock_assessment.overall_score = 75.0
                mock_assessment.findings = []
                mock_scanner.return_value.scan.return_value = mock_assessment

                mock_fix_plan = MagicMock()
                mock_fix_plan.fixes = []
                mock_fix_plan.projected_score = 75.0
                mock_fix_plan.points_gained = 0.0
                mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

                result = runner.invoke(align, [])

                # Should use current directory
                assert result.exit_code == 0


@pytest.mark.skip(
    reason="Tests use outdated mocks - LanguageDetector is not imported in align.py. Tests need to be updated to match current implementation."
)
class TestAlignCommandEdgeCases:
    """Test edge cases in align command."""

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_perfect_score(self, mock_fixer, mock_scanner, runner, temp_repo):
        """Test align command when repository already has perfect score."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 100.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 100.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0
        assert "Platinum" in result.output

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_zero_score(self, mock_fixer, mock_scanner, runner, temp_repo):
        """Test align command when repository has zero score."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 0.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 0.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0
        assert "Needs Improvement" in result.output

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_no_languages_detected(
        self, mock_fixer, mock_scanner, runner, temp_repo
    ):
        """Test align command when no languages are detected."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 50.0
        mock_assessment.findings = []
        mock_scanner.return_value.scan.return_value = mock_assessment

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 50.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        result = runner.invoke(align, [str(temp_repo)])

        # Should still work (languages detection is informational)
        assert result.exit_code == 0

    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.FixerService")
    def test_align_fixer_service_error(
        self, mock_fixer, mock_scanner, runner, temp_repo
    ):
        """Test align command when fixer service raises error."""
        # Setup mocks

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.findings = [MagicMock()]
        mock_scanner.return_value.scan.return_value = mock_assessment

        # Fixer raises error
        mock_fixer.return_value.generate_fixes.side_effect = Exception("Fixer error")

        result = runner.invoke(align, [str(temp_repo)])

        # Should handle error gracefully
        assert result.exit_code != 0


class TestAlignClaudeMdFileFeatures:
    """Test align command features specific to claude_md_file attribute.

    These tests verify the tip message when CLAUDE.md fix is skipped and
    the progress callback logging for CLAUDE.md generation.
    """

    @patch("agentready.cli.align.FixerService")
    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.Config")
    @patch("agentready.cli.main.create_all_assessors")
    def test_align_echoes_tip_when_no_fixes_and_claude_md_file_failing(
        self, mock_assessors, mock_config, mock_scanner, mock_fixer, runner, temp_repo
    ):
        """Test that align shows tip when claude_md_file fails but no fix is available."""
        # Setup mock finding with claude_md_file failing
        mock_finding = MagicMock()
        mock_finding.attribute.id = "claude_md_file"
        mock_finding.status = "fail"
        mock_finding.score = 0.0

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.findings = [mock_finding]
        mock_assessment.repository = MagicMock()
        mock_scanner.return_value.scan.return_value = mock_assessment

        # No fixes available (e.g., claude CLI not installed or no API key)
        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 65.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        mock_assessors.return_value = []

        result = runner.invoke(align, [str(temp_repo)])

        # Should show the tip about Claude CLI and API key
        assert "Install the Claude CLI and set ANTHROPIC_API_KEY" in result.output
        assert "CLAUDE.md" in result.output

    @patch("agentready.cli.align.FixerService")
    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.Config")
    @patch("agentready.cli.main.create_all_assessors")
    def test_align_does_not_show_tip_when_claude_md_file_passes(
        self, mock_assessors, mock_config, mock_scanner, mock_fixer, runner, temp_repo
    ):
        """Test that align does not show tip when claude_md_file passes."""
        # Setup mock finding with claude_md_file passing
        mock_finding = MagicMock()
        mock_finding.attribute.id = "claude_md_file"
        mock_finding.status = "pass"
        mock_finding.score = 100.0

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 85.0
        mock_assessment.findings = [mock_finding]
        mock_assessment.repository = MagicMock()
        mock_scanner.return_value.scan.return_value = mock_assessment

        # No fixes available
        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = []
        mock_fix_plan.projected_score = 85.0
        mock_fix_plan.points_gained = 0.0
        mock_fixer.return_value.generate_fix_plan.return_value = mock_fix_plan

        mock_assessors.return_value = []

        result = runner.invoke(align, [str(temp_repo)])

        # Should NOT show the tip
        assert "Install the Claude CLI and set ANTHROPIC_API_KEY" not in result.output

    @patch("agentready.cli.align.FixerService")
    @patch("agentready.cli.align.Scanner")
    @patch("agentready.cli.align.Config")
    @patch("agentready.cli.main.create_all_assessors")
    def test_align_echoes_generating_claude_md_when_fix_applies(
        self, mock_assessors, mock_config, mock_scanner, mock_fixer_cls, runner, temp_repo
    ):
        """Test that align echoes 'Generating CLAUDE.md file...' when applying fix."""
        # Setup mock finding
        mock_finding = MagicMock()
        mock_finding.attribute.id = "claude_md_file"
        mock_finding.status = "fail"
        mock_finding.score = 0.0

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.findings = [mock_finding]
        mock_assessment.repository = MagicMock()
        mock_scanner.return_value.scan.return_value = mock_assessment

        # Setup mock fix for claude_md_file
        mock_fix = MagicMock()
        mock_fix.attribute_id = "claude_md_file"
        mock_fix.description = "Run Claude CLI to create CLAUDE.md"
        mock_fix.preview.return_value = "RUN claude -p ..."
        mock_fix.points_gained = 10.0
        mock_fix.apply.return_value = True

        mock_fix_plan = MagicMock()
        mock_fix_plan.fixes = [mock_fix]
        mock_fix_plan.projected_score = 75.0
        mock_fix_plan.points_gained = 10.0

        # Capture the progress_callback when apply_fixes is called
        captured_callback = None

        def capture_apply_fixes(fixes, dry_run=False, progress_callback=None):
            nonlocal captured_callback
            captured_callback = progress_callback
            # Call the callback to simulate the real behavior
            if progress_callback:
                for fix in fixes:
                    progress_callback(fix, "before", None)
                    progress_callback(fix, "after", True)
            return {"succeeded": 1, "failed": 0, "failures": []}

        mock_fixer_instance = MagicMock()
        mock_fixer_instance.generate_fix_plan.return_value = mock_fix_plan
        mock_fixer_instance.apply_fixes.side_effect = capture_apply_fixes
        mock_fixer_cls.return_value = mock_fixer_instance

        mock_assessors.return_value = []

        # Provide "y" input to confirm applying fixes
        result = runner.invoke(align, [str(temp_repo)], input="y\n")

        # Should show the "Generating CLAUDE.md file..." message
        assert "Generating CLAUDE.md file..." in result.output

        # Verify the callback was captured
        assert captured_callback is not None
