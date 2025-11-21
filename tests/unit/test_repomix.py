"""Unit tests for Repomix service and assessor."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentready.assessors.repomix import RepomixConfigAssessor
from agentready.models.repository import Repository
from agentready.services.repomix import RepomixService


class TestRepomixService:
    """Test Repomix service functionality."""

    def test_initialization(self, tmp_path):
        """Test service initialization."""
        service = RepomixService(tmp_path)
        assert service.repo_path == tmp_path
        assert service.config_path == tmp_path / "repomix.config.json"
        assert service.ignore_path == tmp_path / ".repomixignore"

    def test_is_installed_true(self):
        """Test repomix installation check when installed."""
        with patch("shutil.which", return_value="/usr/local/bin/repomix"):
            service = RepomixService(Path("/tmp"))
            assert service.is_installed() is True

    def test_is_installed_false(self):
        """Test repomix installation check when not installed."""
        with patch("shutil.which", return_value=None):
            service = RepomixService(Path("/tmp"))
            assert service.is_installed() is False

    def test_has_config_true(self, tmp_path):
        """Test configuration file detection when exists."""
        config_file = tmp_path / "repomix.config.json"
        config_file.write_text("{}")
        service = RepomixService(tmp_path)
        assert service.has_config() is True

    def test_has_config_false(self, tmp_path):
        """Test configuration file detection when missing."""
        service = RepomixService(tmp_path)
        assert service.has_config() is False

    def test_generate_config_creates_file(self, tmp_path):
        """Test configuration generation creates file."""
        service = RepomixService(tmp_path)
        result = service.generate_config()
        assert result is True
        assert service.config_path.exists()

        # Verify JSON is valid
        with open(service.config_path) as f:
            config = json.load(f)
        assert "$schema" in config
        assert config["output"]["style"] == "markdown"

    def test_generate_config_no_overwrite(self, tmp_path):
        """Test configuration generation skips existing file."""
        service = RepomixService(tmp_path)
        service.generate_config()
        result = service.generate_config(overwrite=False)
        assert result is False

    def test_generate_config_with_overwrite(self, tmp_path):
        """Test configuration generation overwrites with flag."""
        service = RepomixService(tmp_path)
        service.generate_config()
        result = service.generate_config(overwrite=True)
        assert result is True

    def test_generate_ignore_creates_file(self, tmp_path):
        """Test ignore file generation creates file."""
        service = RepomixService(tmp_path)
        result = service.generate_ignore()
        assert result is True
        assert service.ignore_path.exists()

        # Verify content
        content = service.ignore_path.read_text()
        assert ".venv/" in content
        assert "__pycache__/" in content

    def test_generate_ignore_with_custom_patterns(self, tmp_path):
        """Test ignore file generation with custom patterns."""
        service = RepomixService(tmp_path)
        custom = ["*.custom", "temp/"]
        service.generate_ignore(additional_patterns=custom)

        content = service.ignore_path.read_text()
        assert "*.custom" in content
        assert "temp/" in content

    def test_get_output_files_empty(self, tmp_path):
        """Test getting output files when none exist."""
        service = RepomixService(tmp_path)
        files = service.get_output_files()
        assert len(files) == 0

    def test_get_output_files_found(self, tmp_path):
        """Test getting output files when they exist."""
        (tmp_path / "repomix-output.md").write_text("content")
        (tmp_path / "repomix-output.xml").write_text("<xml/>")

        service = RepomixService(tmp_path)
        files = service.get_output_files()
        assert len(files) == 2

    def test_check_freshness_no_files(self, tmp_path):
        """Test freshness check when no output files."""
        service = RepomixService(tmp_path)
        is_fresh, message = service.check_freshness()
        assert is_fresh is False
        assert "no repomix output files found" == message.lower()

    def test_check_freshness_fresh_file(self, tmp_path):
        """Test freshness check with recent file."""
        output = tmp_path / "repomix-output.md"
        output.write_text("fresh content")

        service = RepomixService(tmp_path)
        is_fresh, message = service.check_freshness(max_age_days=7)
        assert is_fresh is True
        assert "fresh" in message.lower()

    @patch("subprocess.run")
    def test_run_repomix_success(self, mock_run, tmp_path):
        """Test running repomix successfully."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with patch("shutil.which", return_value="/usr/bin/repomix"):
            service = RepomixService(tmp_path)
            success, message = service.run_repomix()

        assert success is True
        assert "generated" in message.lower()
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_repomix_failure(self, mock_run, tmp_path):
        """Test running repomix with failure."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error occurred"
        )

        with patch("shutil.which", return_value="/usr/bin/repomix"):
            service = RepomixService(tmp_path)
            success, message = service.run_repomix()

        assert success is False
        assert "failed" in message.lower()

    def test_run_repomix_not_installed(self, tmp_path):
        """Test running repomix when not installed."""
        with patch("shutil.which", return_value=None):
            service = RepomixService(tmp_path)
            success, message = service.run_repomix()

        assert success is False
        assert "not installed" in message.lower()


class TestRepomixConfigAssessor:
    """Test Repomix configuration assessor."""

    def test_attribute_properties(self):
        """Test assessor attribute properties."""
        assessor = RepomixConfigAssessor()
        assert assessor.attribute_id == "repomix_config"
        assert assessor.tier == 3
        assert assessor.attribute.name == "Repomix AI Context Generation"

    def test_assess_no_config(self, tmp_path):
        """Test assessment when Repomix not configured."""
        (tmp_path / ".git").mkdir()
        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},
            total_files=0,
            total_lines=0,
        )
        assessor = RepomixConfigAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0
        assert "not found" in finding.evidence[0].lower()
        assert len(finding.remediation.steps) > 0

    def test_assess_config_but_no_output(self, tmp_path):
        """Test assessment with config but no output."""
        # Create git directory and config file
        (tmp_path / ".git").mkdir()
        config_path = tmp_path / "repomix.config.json"
        config_path.write_text("{}")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},
            total_files=0,
            total_lines=0,
        )
        assessor = RepomixConfigAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 50
        assert "exists" in finding.evidence[0].lower()
        assert "no repomix output files found" == finding.evidence[1].lower()

    def test_assess_fresh_output(self, tmp_path):
        """Test assessment with fresh output."""
        # Create git directory, config and output
        (tmp_path / ".git").mkdir()
        (tmp_path / "repomix.config.json").write_text("{}")
        (tmp_path / "repomix-output.md").write_text("content")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={},
            total_files=0,
            total_lines=0,
        )
        assessor = RepomixConfigAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100
        assert "fresh" in finding.evidence[2].lower()
