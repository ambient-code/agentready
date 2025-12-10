"""Unit tests for Harbor services."""

import json

import pytest

from agentready.models.harbor import HarborTaskResult
from agentready.services.harbor.agent_toggler import AgentFileToggler
from agentready.services.harbor.result_parser import (
    parse_harbor_results,
    parse_single_result,
)


class TestAgentFileToggler:
    """Tests for AgentFileToggler service."""

    @pytest.fixture
    def sample_agent_file(self, tmp_path):
        """Create a sample agent file for testing."""
        agent_file = tmp_path / ".claude" / "agents" / "doubleagent.md"
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        agent_file.write_text("# Agent Content\n\nThis is the agent file.")
        return agent_file

    def test_disable_enable(self, sample_agent_file):
        """Test basic disable/enable functionality."""
        toggler = AgentFileToggler(sample_agent_file)

        # Initially enabled
        assert toggler.is_enabled()
        assert not toggler.is_disabled()

        # Disable
        toggler.disable()
        assert not toggler.is_enabled()
        assert toggler.is_disabled()
        assert not sample_agent_file.exists()
        assert toggler.disabled_file.exists()

        # Enable
        toggler.enable()
        assert toggler.is_enabled()
        assert not toggler.is_disabled()
        assert sample_agent_file.exists()
        assert not toggler.disabled_file.exists()

    def test_disable_idempotent(self, sample_agent_file):
        """Test that disable is idempotent."""
        toggler = AgentFileToggler(sample_agent_file)

        toggler.disable()
        assert toggler.is_disabled()

        # Disable again (should be no-op)
        toggler.disable()
        assert toggler.is_disabled()

    def test_enable_idempotent(self, sample_agent_file):
        """Test that enable is idempotent."""
        toggler = AgentFileToggler(sample_agent_file)

        toggler.disable()
        toggler.enable()
        assert toggler.is_enabled()

        # Enable again (should be no-op)
        toggler.enable()
        assert toggler.is_enabled()

    def test_temporarily_disabled_context_manager(self, sample_agent_file):
        """Test temporarily_disabled context manager."""
        toggler = AgentFileToggler(sample_agent_file)

        assert toggler.is_enabled()

        with toggler.temporarily_disabled():
            assert toggler.is_disabled()
            assert not sample_agent_file.exists()

        # Restored after context exit
        assert toggler.is_enabled()
        assert sample_agent_file.exists()

    def test_temporarily_disabled_with_exception(self, sample_agent_file):
        """Test that temporarily_disabled restores even on exception."""
        toggler = AgentFileToggler(sample_agent_file)

        assert toggler.is_enabled()

        with pytest.raises(ValueError):
            with toggler.temporarily_disabled():
                assert toggler.is_disabled()
                raise ValueError("Test exception")

        # Restored even after exception
        assert toggler.is_enabled()
        assert sample_agent_file.exists()

    def test_temporarily_enabled_context_manager(self, sample_agent_file):
        """Test temporarily_enabled context manager."""
        toggler = AgentFileToggler(sample_agent_file)
        toggler.disable()

        assert toggler.is_disabled()

        with toggler.temporarily_enabled():
            assert toggler.is_enabled()
            assert sample_agent_file.exists()

        # Restored to disabled after context exit
        assert toggler.is_disabled()
        assert not sample_agent_file.exists()

    def test_file_content_preserved(self, sample_agent_file):
        """Test that file content is preserved through disable/enable."""
        original_content = sample_agent_file.read_text()
        toggler = AgentFileToggler(sample_agent_file)

        toggler.disable()
        toggler.enable()

        assert sample_agent_file.read_text() == original_content


class TestResultParser:
    """Tests for result parser functions."""

    @pytest.fixture
    def sample_result_data(self):
        """Sample result.json data."""
        return {
            "task_name": "adaptive-rejection-sampler",
            "trial_name": "adaptive-rejection-sampler__ABC123",
            "agent_result": {"status": "completed"},
            "verifier_result": {"passed": True},
            "exception_info": None,
            "started_at": "2025-12-09T10:00:00",
            "finished_at": "2025-12-09T10:05:00",
        }

    @pytest.fixture
    def sample_results_dir(self, tmp_path, sample_result_data):
        """Create a sample Harbor results directory with result.json files."""
        results_dir = tmp_path / "harbor_run"
        results_dir.mkdir()

        # Create multiple task result directories
        for i in range(1, 4):
            task_dir = results_dir / f"task{i}__trial{i}"
            task_dir.mkdir()

            result_file = task_dir / "result.json"
            result_data = sample_result_data.copy()
            result_data["task_name"] = f"task{i}"
            result_data["trial_name"] = f"task{i}__trial{i}"

            with open(result_file, "w") as f:
                json.dump(result_data, f)

        return results_dir

    def test_parse_single_result(self, tmp_path, sample_result_data):
        """Test parsing a single result.json file."""
        result_file = tmp_path / "result.json"
        with open(result_file, "w") as f:
            json.dump(sample_result_data, f)

        result = parse_single_result(result_file)

        assert isinstance(result, HarborTaskResult)
        assert result.task_name == "adaptive-rejection-sampler"
        assert result.success is True
        assert result.duration_sec == 300.0

    def test_parse_single_result_file_not_found(self, tmp_path):
        """Test parsing non-existent file raises error."""
        result_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            parse_single_result(result_file)

    def test_parse_single_result_invalid_json(self, tmp_path):
        """Test parsing invalid JSON raises error."""
        result_file = tmp_path / "invalid.json"
        result_file.write_text("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            parse_single_result(result_file)

    def test_parse_harbor_results(self, sample_results_dir):
        """Test parsing multiple result.json files from a directory."""
        results = parse_harbor_results(sample_results_dir)

        assert len(results) == 3
        assert all(isinstance(r, HarborTaskResult) for r in results)
        assert {r.task_name for r in results} == {"task1", "task2", "task3"}

    def test_parse_harbor_results_dir_not_found(self, tmp_path):
        """Test parsing non-existent directory raises error."""
        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            parse_harbor_results(nonexistent_dir)

    def test_parse_harbor_results_no_result_files(self, tmp_path):
        """Test parsing directory with no result.json files raises error."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="No result.json files found"):
            parse_harbor_results(empty_dir)

    def test_parse_harbor_results_skips_invalid_files(self, sample_results_dir):
        """Test that parser skips invalid result files and continues."""
        # Add an invalid result file
        invalid_dir = sample_results_dir / "invalid__task"
        invalid_dir.mkdir()
        invalid_file = invalid_dir / "result.json"
        invalid_file.write_text("invalid json")

        # Should still parse valid files and skip invalid one
        results = parse_harbor_results(sample_results_dir)

        # Should have 3 valid results (skipped the invalid one)
        assert len(results) == 3

    def test_parse_harbor_results_partial_data(self, tmp_path):
        """Test parsing result with missing optional fields."""
        results_dir = tmp_path / "harbor_run"
        results_dir.mkdir()

        task_dir = results_dir / "task1__trial1"
        task_dir.mkdir()

        # Minimal valid result data
        result_data = {
            "task_name": "task1",
            "trial_name": "task1__trial1",
            "agent_result": None,
            "verifier_result": None,
            "exception_info": {"exception_type": "Error"},
            "started_at": "2025-12-09T10:00:00",
            "finished_at": "2025-12-09T10:05:00",
        }

        result_file = task_dir / "result.json"
        with open(result_file, "w") as f:
            json.dump(result_data, f)

        results = parse_harbor_results(results_dir)

        assert len(results) == 1
        assert results[0].task_name == "task1"
        assert results[0].success is False  # No agent/verifier results
