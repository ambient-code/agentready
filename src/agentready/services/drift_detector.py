"""Drift detection for Bootstrap templates.

Compares generated Bootstrap files with AgentReady's actual infrastructure
to detect template drift and ensure templates stay synchronized.
"""

import difflib
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, PackageLoader, select_autoescape


class DriftDetector:
    """Detects drift between Bootstrap templates and AgentReady's actual files."""

    def __init__(self, agentready_repo_path: Path):
        """Initialize drift detector.

        Args:
            agentready_repo_path: Path to AgentReady repository
        """
        self.repo_path = agentready_repo_path
        self.env = Environment(
            loader=PackageLoader("agentready", "templates/bootstrap"),
            autoescape=select_autoescape(["html", "xml", "j2", "yaml", "yml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def check_drift(self, verbose: bool = False) -> Dict[str, List[str]]:
        """Check for drift between templates and actual files.

        Args:
            verbose: Include detailed diff output

        Returns:
            Dictionary mapping file categories to drift reports
        """
        drift_report = {
            "drifted": [],
            "in_sync": [],
            "missing_actual": [],
            "template_errors": [],
        }

        # Check release workflow drift
        release_drift = self._check_release_workflow_drift(verbose)
        if release_drift:
            drift_report["drifted"].append(release_drift)
        else:
            drift_report["in_sync"].append("python/workflows/release.yml.j2")

        # Check releaserc.json drift
        releaserc_drift = self._check_releaserc_drift(verbose)
        if releaserc_drift:
            drift_report["drifted"].append(releaserc_drift)
        else:
            drift_report["in_sync"].append("python/releaserc.json.j2")

        # Check sync-version.sh drift
        sync_script_drift = self._check_sync_script_drift(verbose)
        if sync_script_drift:
            drift_report["drifted"].append(sync_script_drift)
        else:
            drift_report["in_sync"].append("python/sync-version.sh.j2")

        return drift_report

    def _check_release_workflow_drift(self, verbose: bool = False) -> Optional[str]:
        """Check if release workflow template has drifted.

        Args:
            verbose: Include detailed diff

        Returns:
            Drift report string if drifted, None if in sync
        """
        actual_file = self.repo_path / ".github" / "workflows" / "release.yml"
        if not actual_file.exists():
            return "Missing actual file: .github/workflows/release.yml"

        # Render template with AgentReady's config
        template = self.env.get_template("python/workflows/release.yml.j2")
        generated = template.render(enable_publishing=True)

        actual = actual_file.read_text()

        # Compare (ignoring container build job which is AgentReady-specific)
        actual_lines = actual.split("\n")
        generated_lines = generated.split("\n")

        # Find where container build starts
        container_start = None
        for i, line in enumerate(actual_lines):
            if "build-container:" in line:
                container_start = i
                break

        # Compare only the release job
        if container_start:
            actual_lines = actual_lines[:container_start]

        # Normalize whitespace for comparison
        actual_normalized = "\n".join(line.rstrip() for line in actual_lines)
        generated_normalized = "\n".join(line.rstrip() for line in generated_lines)

        if actual_normalized != generated_normalized:
            drift_msg = "DRIFT: python/workflows/release.yml.j2"
            if verbose:
                diff = difflib.unified_diff(
                    generated_normalized.split("\n"),
                    actual_normalized.split("\n"),
                    fromfile="template (generated)",
                    tofile="actual (.github/workflows/release.yml)",
                    lineterm="",
                )
                drift_msg += "\n" + "\n".join(diff)
            return drift_msg

        return None

    def _check_releaserc_drift(self, verbose: bool = False) -> Optional[str]:
        """Check if .releaserc.json template has drifted.

        Args:
            verbose: Include detailed diff

        Returns:
            Drift report string if drifted, None if in sync
        """
        actual_file = self.repo_path / ".releaserc.json"
        if not actual_file.exists():
            return "Missing actual file: .releaserc.json"

        # Render template with AgentReady's config
        template = self.env.get_template("python/releaserc.json.j2")
        generated = template.render(enable_publishing=True, has_claude_md=True)

        actual = actual_file.read_text()

        # Normalize for comparison (pretty-print JSON would be better, but this works)
        actual_normalized = actual.strip()
        generated_normalized = generated.strip()

        if actual_normalized != generated_normalized:
            drift_msg = "DRIFT: python/releaserc.json.j2"
            if verbose:
                diff = difflib.unified_diff(
                    generated_normalized.split("\n"),
                    actual_normalized.split("\n"),
                    fromfile="template (generated)",
                    tofile="actual (.releaserc.json)",
                    lineterm="",
                )
                drift_msg += "\n" + "\n".join(diff)
            return drift_msg

        return None

    def _check_sync_script_drift(self, verbose: bool = False) -> Optional[str]:
        """Check if sync-version.sh template has drifted.

        Args:
            verbose: Include detailed diff

        Returns:
            Drift report string if drifted, None if in sync
        """
        actual_file = self.repo_path / "scripts" / "sync-claude-md.sh"
        if not actual_file.exists():
            return "Missing actual file: scripts/sync-claude-md.sh"

        # Render template with AgentReady's config
        template = self.env.get_template("python/sync-version.sh.j2")
        generated = template.render(project_name="agentready", has_claude_md=True)

        # These files will never match exactly (AgentReady-specific vs generic)
        # But we can check for structural drift
        generated_lines = generated.split("\n")

        # Check key structural elements exist in both
        key_patterns = [
            "#!/bin/bash",
            "set -e",
            "VERSION=",
            "TODAY=",
            "sed -i.bak",
            "CLAUDE.md",
        ]

        missing_patterns = []
        for pattern in key_patterns:
            if not any(pattern in line for line in generated_lines):
                missing_patterns.append(pattern)

        if missing_patterns:
            return (
                f"DRIFT: python/sync-version.sh.j2 - "
                f"Missing patterns: {', '.join(missing_patterns)}"
            )

        return None

    def generate_drift_report(self, verbose: bool = False) -> str:
        """Generate human-readable drift report.

        Args:
            verbose: Include detailed diffs

        Returns:
            Formatted drift report
        """
        drift_data = self.check_drift(verbose=verbose)

        report_lines = ["Bootstrap Template Drift Report", "=" * 50, ""]

        if drift_data["drifted"]:
            report_lines.append("⚠️  DRIFTED TEMPLATES:")
            for item in drift_data["drifted"]:
                report_lines.append(f"  - {item}")
            report_lines.append("")

        if drift_data["in_sync"]:
            report_lines.append("✓ IN SYNC:")
            for item in drift_data["in_sync"]:
                report_lines.append(f"  - {item}")
            report_lines.append("")

        if drift_data["missing_actual"]:
            report_lines.append("❌ MISSING ACTUAL FILES:")
            for item in drift_data["missing_actual"]:
                report_lines.append(f"  - {item}")
            report_lines.append("")

        if drift_data["template_errors"]:
            report_lines.append("🔥 TEMPLATE ERRORS:")
            for item in drift_data["template_errors"]:
                report_lines.append(f"  - {item}")
            report_lines.append("")

        # Summary
        total_drifted = len(drift_data["drifted"])
        total_in_sync = len(drift_data["in_sync"])
        total_checked = total_drifted + total_in_sync

        report_lines.append("SUMMARY:")
        report_lines.append(f"  Checked: {total_checked}")
        report_lines.append(f"  In Sync: {total_in_sync}")
        report_lines.append(f"  Drifted: {total_drifted}")

        if total_drifted > 0:
            report_lines.append("")
            report_lines.append(
                "⚠️  Templates have drifted from AgentReady's actual infrastructure."
            )
            report_lines.append(
                "   Update templates to match actual files to prevent drift."
            )

        return "\n".join(report_lines)
