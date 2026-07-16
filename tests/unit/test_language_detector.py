"""Tests for LanguageDetector, focused on extension/basename detection coverage."""

import subprocess

from agentready.services.language_detector import LanguageDetector


def _git_init(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)


class TestLanguageDetectorTerraform:
    def test_tf_files_detected(self, tmp_path):
        _git_init(tmp_path)
        for i in range(3):
            (tmp_path / f"main{i}.tf").write_text('resource "x" "y" {}\n')
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True
        )
        detected = LanguageDetector(tmp_path).detect_languages()
        assert detected.get("Terraform") == 3


class TestLanguageDetectorDockerfile:
    def test_bare_dockerfile_below_threshold_not_reported(self, tmp_path):
        _git_init(tmp_path)
        (tmp_path / "Dockerfile").write_text("FROM ubuntu\n")
        # Bare filenames have no extension; pad with unrelated tracked files
        # so git ls-files has something realistic to walk alongside it.
        (tmp_path / "app.py").write_text("x = 1\n")
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True
        )
        # minimum_file_threshold is 3; Dockerfile below threshold still resolves
        # via BASENAME_MAP, it just won't clear the reporting threshold alone.
        detected = LanguageDetector(tmp_path).detect_languages()
        assert "Dockerfile" not in detected  # only 1 Dockerfile, below threshold

    def test_bare_dockerfile_detected_above_threshold(self, tmp_path):
        _git_init(tmp_path)
        for sub in ("a", "b", "c"):
            d = tmp_path / sub
            d.mkdir()
            (d / "Dockerfile").write_text("FROM ubuntu\n")
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True
        )
        detected = LanguageDetector(tmp_path).detect_languages()
        assert detected.get("Dockerfile") == 3

    def test_dockerfile_variant_suffix_not_matched(self, tmp_path):
        """Dockerfile.prod etc. are out of scope for the exact-basename rule."""
        _git_init(tmp_path)
        for i in range(3):
            (tmp_path / f"Dockerfile.stage{i}").write_text("FROM ubuntu\n")
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True
        )
        detected = LanguageDetector(tmp_path).detect_languages()
        assert "Dockerfile" not in detected
