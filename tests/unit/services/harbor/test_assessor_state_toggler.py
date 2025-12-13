"""Unit tests for AssessorStateToggler."""

import pytest

from agentready.services.harbor.agent_toggler import AssessorStateToggler


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure for testing."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()

    # Create .claude directory and CLAUDE.md
    claude_dir = repo_root / ".claude"
    claude_dir.mkdir()
    claude_md = claude_dir / "CLAUDE.md"
    claude_md.write_text("# Test Project\n\nThis is a test CLAUDE.md file.")

    # Create README.md
    readme = repo_root / "README.md"
    readme.write_text("# Test Repo\n\n## Installation\n\n## Usage")

    # Create tests directory
    tests_dir = repo_root / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test_example():\n    assert True")

    return repo_root


class TestAssessorStateToggler:
    """Test AssessorStateToggler functionality."""

    def test_initialization(self, temp_repo):
        """Test toggler initializes with correct repo root."""
        toggler = AssessorStateToggler(repo_root=temp_repo)
        assert toggler.repo_root == temp_repo
        assert toggler._backup_suffix == ".assessor_backup"

    def test_list_supported_assessors(self, temp_repo):
        """Test listing supported assessors returns expected IDs."""
        toggler = AssessorStateToggler(repo_root=temp_repo)
        supported = toggler.list_supported_assessors()

        assert "claude_md_file" in supported
        assert "readme_structure" in supported
        assert "test_coverage" in supported
        assert len(supported) == 3

    def test_force_fail_claude_md(self, temp_repo):
        """Test forcing CLAUDE.md assessor to fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        claude_md = temp_repo / ".claude" / "CLAUDE.md"
        backup = temp_repo / ".claude" / "CLAUDE.md.assessor_backup"

        # Verify file exists before fail
        assert claude_md.exists()
        assert not backup.exists()

        # Force fail
        toggler.force_fail("claude_md_file")

        # Verify file is backed up
        assert not claude_md.exists()
        assert backup.exists()

    def test_restore_claude_md(self, temp_repo):
        """Test restoring CLAUDE.md after forcing fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        # Force fail first
        toggler.force_fail("claude_md_file")

        claude_md = temp_repo / ".claude" / "CLAUDE.md"
        backup = temp_repo / ".claude" / "CLAUDE.md.assessor_backup"

        # Verify backup state
        assert not claude_md.exists()
        assert backup.exists()

        # Restore
        toggler.restore("claude_md_file")

        # Verify restored
        assert claude_md.exists()
        assert not backup.exists()

    def test_force_fail_readme(self, temp_repo):
        """Test forcing README assessor to fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        readme = temp_repo / "README.md"
        backup = temp_repo / "README.md.assessor_backup"

        # Force fail
        toggler.force_fail("readme_structure")

        # Verify
        assert not readme.exists()
        assert backup.exists()

    def test_restore_readme(self, temp_repo):
        """Test restoring README after forcing fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        # Force fail first
        toggler.force_fail("readme_structure")

        # Restore
        toggler.restore("readme_structure")

        readme = temp_repo / "README.md"
        backup = temp_repo / "README.md.assessor_backup"

        # Verify
        assert readme.exists()
        assert not backup.exists()

    def test_force_fail_tests(self, temp_repo):
        """Test forcing test coverage assessor to fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        tests_dir = temp_repo / "tests"
        backup_dir = temp_repo / "tests.assessor_backup"

        # Force fail
        toggler.force_fail("test_coverage")

        # Verify
        assert not tests_dir.exists()
        assert backup_dir.exists()

    def test_restore_tests(self, temp_repo):
        """Test restoring tests directory after forcing fail."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        # Force fail first
        toggler.force_fail("test_coverage")

        # Restore
        toggler.restore("test_coverage")

        tests_dir = temp_repo / "tests"
        backup_dir = temp_repo / "tests.assessor_backup"

        # Verify
        assert tests_dir.exists()
        assert not backup_dir.exists()

    def test_temporarily_failed_context_manager(self, temp_repo):
        """Test temporarily_failed context manager restores state."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        claude_md = temp_repo / ".claude" / "CLAUDE.md"

        # Verify initial state
        assert claude_md.exists()

        # Use context manager
        with toggler.temporarily_failed("claude_md_file"):
            # Inside context: file should be missing
            assert not claude_md.exists()

        # Outside context: file should be restored
        assert claude_md.exists()

    def test_temporarily_failed_exception_still_restores(self, temp_repo):
        """Test temporarily_failed restores even when exception occurs."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        claude_md = temp_repo / ".claude" / "CLAUDE.md"

        # Verify initial state
        assert claude_md.exists()

        # Use context manager with exception
        with pytest.raises(RuntimeError):
            with toggler.temporarily_failed("claude_md_file"):
                assert not claude_md.exists()
                raise RuntimeError("Test exception")

        # File should still be restored
        assert claude_md.exists()

    def test_unknown_assessor_raises_error(self, temp_repo):
        """Test that unknown assessor ID raises ValueError."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        with pytest.raises(ValueError, match="Unknown assessor: nonexistent"):
            toggler.force_fail("nonexistent")

        with pytest.raises(ValueError, match="Unknown assessor: nonexistent"):
            toggler.restore("nonexistent")

    def test_idempotent_force_fail(self, temp_repo):
        """Test that forcing fail multiple times is idempotent."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        # Force fail twice
        toggler.force_fail("claude_md_file")
        toggler.force_fail("claude_md_file")  # Should not error

        claude_md = temp_repo / ".claude" / "CLAUDE.md"
        backup = temp_repo / ".claude" / "CLAUDE.md.assessor_backup"

        # Still in failed state
        assert not claude_md.exists()
        assert backup.exists()

    def test_idempotent_restore(self, temp_repo):
        """Test that restoring multiple times is idempotent."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        # Force fail, then restore twice
        toggler.force_fail("claude_md_file")
        toggler.restore("claude_md_file")
        toggler.restore("claude_md_file")  # Should not error

        claude_md = temp_repo / ".claude" / "CLAUDE.md"
        backup = temp_repo / ".claude" / "CLAUDE.md.assessor_backup"

        # Still in normal state
        assert claude_md.exists()
        assert not backup.exists()

    def test_content_preservation(self, temp_repo):
        """Test that file content is preserved through fail/restore cycle."""
        toggler = AssessorStateToggler(repo_root=temp_repo)

        claude_md = temp_repo / ".claude" / "CLAUDE.md"
        original_content = claude_md.read_text()

        # Fail and restore
        toggler.force_fail("claude_md_file")
        toggler.restore("claude_md_file")

        # Verify content is identical
        assert claude_md.read_text() == original_content
