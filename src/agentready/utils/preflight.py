"""Preflight dependency checks for CLI tools."""

import shutil
import subprocess
from pathlib import Path

import click

from .subprocess_utils import safe_subprocess_run


class PreflightError(Exception):
    """Raised when preflight check fails."""

    pass


def check_harbor_cli(interactive: bool = True) -> bool:
    """Check Harbor CLI availability and optionally install.

    Args:
        interactive: If True, prompt user to install if missing

    Returns:
        True if Harbor is available

    Raises:
        PreflightError: If Harbor is missing and installation declined/failed
    """
    # Check if harbor is installed
    if shutil.which("harbor") is not None:
        return True

    # Harbor not found
    if not interactive:
        raise PreflightError(
            "harbor CLI not installed.\n" "Install with: uv tool install harbor"
        )

    # Prompt user for installation
    click.echo("Harbor CLI not found.", err=True)

    # Detect available package manager (uv or pip)
    if shutil.which("uv") is not None:
        install_cmd = ["uv", "tool", "install", "harbor"]
        install_msg = "uv tool install harbor"
    elif shutil.which("pip") is not None:
        install_cmd = ["pip", "install", "harbor"]
        install_msg = "pip install harbor"
    else:
        raise PreflightError(
            "Neither 'uv' nor 'pip' found on PATH.\n"
            "Install uv (recommended): https://docs.astral.sh/uv/\n"
            "Or install pip: https://pip.pypa.io/en/stable/installation/"
        )

    if not click.confirm(f"Install with '{install_msg}'?", default=True):
        raise PreflightError(
            f"Harbor CLI installation declined.\n" f"To install manually: {install_msg}"
        )

    # Install Harbor
    try:
        click.echo(f"Installing Harbor CLI using {install_cmd[0]}...")
        safe_subprocess_run(install_cmd, check=True, timeout=300)  # 5 minute timeout
    except Exception as e:
        raise PreflightError(f"Harbor installation failed: {e}")

    # Verify installation succeeded
    if shutil.which("harbor") is None:
        raise PreflightError(
            "Harbor installation completed but 'harbor' not found on PATH.\n"
            "You may need to restart your shell or add ~/.local/bin to PATH."
        )

    click.echo("✓ Harbor CLI installed successfully")
    return True


def ensure_terminal_bench_dataset() -> Path:
    """Ensure Terminal-Bench dataset is downloaded and find smoketest task.

    Returns:
        Path to adaptive-rejection-sampler task directory

    Raises:
        PreflightError: If dataset download fails or task not found
    """
    # First, try to find an existing task
    cache_dir = Path.home() / ".cache/harbor/tasks"

    if cache_dir.exists():
        candidates = sorted(cache_dir.glob("*/adaptive-rejection-sampler"))
        if candidates:
            click.echo("✓ Terminal-Bench dataset found in cache")
            return candidates[-1]  # Use most recent

    # Dataset not found - download it
    click.echo("Downloading Terminal-Bench dataset (89 tasks, ~50MB)...")

    try:
        subprocess.run(
            ["harbor", "datasets", "download", "terminal-bench@2.0"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            check=True,
        )
        click.echo("✓ Terminal-Bench dataset downloaded")
    except subprocess.TimeoutExpired:
        raise PreflightError(
            "Dataset download timed out after 10 minutes.\n"
            "Check your network connection and try again."
        )
    except subprocess.CalledProcessError as e:
        raise PreflightError(
            f"Dataset download failed: {e.stderr}\n"
            f"Try manually: harbor datasets download terminal-bench@2.0"
        )
    except Exception as e:
        raise PreflightError(f"Dataset download failed: {e}")

    # Find the downloaded task
    if cache_dir.exists():
        candidates = sorted(cache_dir.glob("*/adaptive-rejection-sampler"))
        if candidates:
            return candidates[-1]

    raise PreflightError(
        "Dataset downloaded but task not found in cache.\n"
        "This may indicate a Harbor version incompatibility."
    )
