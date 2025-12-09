"""Tests for preflight dependency checks."""

from unittest.mock import patch

import pytest

from agentready.utils.preflight import PreflightError, check_harbor_cli


class TestCheckHarborCLI:
    """Tests for check_harbor_cli()."""

    def test_harbor_already_installed(self):
        """Harbor found on PATH - no prompts, returns True."""
        with patch("shutil.which", return_value="/usr/local/bin/harbor"):
            result = check_harbor_cli(interactive=True)
            assert result is True

    def test_harbor_missing_user_confirms_uv(self):
        """Harbor missing, user confirms with uv available - succeeds."""
        # First call (harbor check) returns None, second call (uv check) returns path,
        # third call (harbor verify) returns harbor path
        with patch(
            "shutil.which",
            side_effect=[None, "/usr/bin/uv", "/usr/local/bin/harbor"],
        ):
            with patch("click.confirm", return_value=True):
                with patch("click.echo"):
                    with patch(
                        "agentready.utils.preflight.safe_subprocess_run"
                    ) as mock_run:
                        result = check_harbor_cli(interactive=True)
                        assert result is True
                        mock_run.assert_called_once_with(
                            ["uv", "tool", "install", "harbor"],
                            check=True,
                            timeout=300,
                        )

    def test_harbor_missing_user_confirms_pip_fallback(self):
        """Harbor missing, uv not available, falls back to pip - succeeds."""
        # First: harbor=None, uv=None, pip=/usr/bin/pip, final harbor=/usr/local/bin/harbor
        with patch(
            "shutil.which",
            side_effect=[None, None, "/usr/bin/pip", "/usr/local/bin/harbor"],
        ):
            with patch("click.confirm", return_value=True):
                with patch("click.echo"):
                    with patch(
                        "agentready.utils.preflight.safe_subprocess_run"
                    ) as mock_run:
                        result = check_harbor_cli(interactive=True)
                        assert result is True
                        mock_run.assert_called_once_with(
                            ["pip", "install", "harbor"], check=True, timeout=300
                        )

    def test_harbor_missing_neither_uv_nor_pip(self):
        """Harbor missing, neither uv nor pip available - raises error."""
        with patch("shutil.which", return_value=None):
            with patch("click.echo"):
                with pytest.raises(PreflightError, match="Neither 'uv' nor 'pip'"):
                    check_harbor_cli(interactive=True)

    def test_harbor_missing_user_declines(self):
        """Harbor missing, user declines install - raises error."""
        with patch("shutil.which", side_effect=[None, "/usr/bin/uv"]):
            with patch("click.confirm", return_value=False):
                with patch("click.echo"):
                    with pytest.raises(
                        PreflightError, match="Harbor CLI installation declined"
                    ):
                        check_harbor_cli(interactive=True)

    def test_installation_subprocess_fails(self):
        """Installation subprocess fails - raises PreflightError."""
        with patch("shutil.which", side_effect=[None, "/usr/bin/uv"]):
            with patch("click.confirm", return_value=True):
                with patch("click.echo"):
                    with patch(
                        "agentready.utils.preflight.safe_subprocess_run",
                        side_effect=Exception("Subprocess failed"),
                    ):
                        with pytest.raises(
                            PreflightError, match="Harbor installation failed"
                        ):
                            check_harbor_cli(interactive=True)

    def test_installation_succeeds_but_not_on_path(self):
        """Installation completes but harbor not found on PATH - raises error."""
        # harbor check=None, uv=/usr/bin/uv, harbor verify=None (still not on PATH)
        with patch("shutil.which", side_effect=[None, "/usr/bin/uv", None]):
            with patch("click.confirm", return_value=True):
                with patch("click.echo"):
                    with patch("agentready.utils.preflight.safe_subprocess_run"):
                        with pytest.raises(PreflightError, match="not found on PATH"):
                            check_harbor_cli(interactive=True)

    def test_non_interactive_with_harbor_missing(self):
        """Non-interactive mode with missing Harbor - raises PreflightError immediately."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(PreflightError, match="harbor CLI not installed"):
                check_harbor_cli(interactive=False)

    def test_non_interactive_with_harbor_installed(self):
        """Non-interactive mode with Harbor installed - returns True."""
        with patch("shutil.which", return_value="/usr/local/bin/harbor"):
            result = check_harbor_cli(interactive=False)
            assert result is True
