"""Tests for Python type annotation assessment (ADR A.6)."""

import json
import subprocess

import pytest

from agentready.assessors.code_quality import TypeAnnotationsAssessor
from agentready.models.repository import Repository


def _make_py_repo(tmp_path, py_files=None, **kwargs):
    """Create a test Python repository with git init."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return Repository(
        path=tmp_path,
        name="test-py-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 50},
        total_files=kwargs.get("total_files", 10),
        total_lines=kwargs.get("total_lines", 500),
    )


class TestTypeAnnotationsAssessorPython:
    """Test Python type annotation assessment in TypeAnnotationsAssessor."""

    def test_applicable_to_python(self, tmp_path):
        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        assert assessor.is_applicable(repo)

    def test_no_python_files_returns_not_applicable(self, tmp_path):
        repo = _make_py_repo(tmp_path)
        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"JavaScript": 100},
            total_files=10,
            total_lines=100,
        )
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "not_applicable"

    # --- Strict mode detection tests (ADR A.6) ---

    def test_strict_mode_pyproject_toml_mypy_strict(self, tmp_path):
        """pyproject.toml with mypy strict = true is detected."""
        _write_pyproject(tmp_path, mypy_strict=True)

        # Add a simple Python file
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert "Strict mode configured" in " ".join(finding.evidence)
        # Should get the 20 pt bonus for strict mode
        assert "Strict mode configured" in finding.evidence or any(
            "Strict" in e for e in finding.evidence
        )

    def test_strict_mode_pyproject_toml_mypy_disallow_untyped(self, tmp_path):
        """pyproject.toml with mypy disallow_untyped_defs is detected."""
        _write_pyproject(tmp_path, mypy_disallow_untyped=True)

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_pyproject_toml_pyright_strict(self, tmp_path):
        """pyproject.toml with pyright strict = true is detected."""
        _write_pyproject(tmp_path, pyright_strict=True)

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_mypy_ini(self, tmp_path):
        """mypy.ini with strict = true is detected."""
        (tmp_path / "mypy.ini").write_text(
            "[mypy]\nstrict = true\n"
        )

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_mypy_ini_disallow_untyped(self, tmp_path):
        """mypy.ini with disallow_untyped_defs is detected."""
        (tmp_path / "mypy.ini").write_text(
            "[mypy]\ndisallow_untyped_defs = true\n"
        )

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_setup_cfg(self, tmp_path):
        """setup.cfg with mypy strict = true is detected."""
        (tmp_path / "setup.cfg").write_text(
            "[mypy]\nstrict = true\n"
        )

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_pyrightconfig_json(self, tmp_path):
        """pyrightconfig.json with typeCheckingMode = strict is detected."""
        (tmp_path / "pyrightconfig.json").write_text(
            json.dumps({"typeCheckingMode": "strict"})
        )

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_strict_mode_pyrightconfig_strict_field(self, tmp_path):
        """pyrightconfig.json with strict: true is detected."""
        (tmp_path / "pyrightconfig.json").write_text(
            json.dumps({"strict": True})
        )

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("Strict" in e for e in finding.evidence)

    def test_no_strict_mode_config(self, tmp_path):
        """No strict mode config means no bonus."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("No strict mode" in e for e in finding.evidence)

    def test_strict_mode_pyproject_malformed_toml(self, tmp_path):
        """Malformed pyproject.toml is handled gracefully."""
        (tmp_path / "pyproject.toml").write_text("not valid toml {{{")

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        # Should not crash, and should not find strict mode
        assert any("No strict mode" in e for e in finding.evidence)

    def test_strict_mode_prefers_pyproject_over_other_configs(self, tmp_path):
        """When multiple configs exist, strict mode is detected from any source."""
        _write_pyproject(tmp_path, mypy_strict=True)
        # Also create mypy.ini (shouldn't matter, pyproject already has it)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = false\n")

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("def foo(x: int) -> int:\n    return x\n")

        repo = _make_py_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        # Should find strict mode via pyproject.toml
        assert any("Strict mode" in e for e in finding.evidence)


def _write_pyproject(
    path,
    mypy_strict=False,
    mypy_disallow_untyped=False,
    pyright_strict=False,
):
    """Write a pyproject.toml with specified mypy/pyright config."""
    config = {"tool": {}}

    if mypy_strict:
        config["tool"]["mypy"] = {"strict": True}
    if mypy_disallow_untyped:
        config["tool"]["mypy"] = {"disallow_untyped_defs": True}
    if pyright_strict:
        config["tool"]["pyright"] = {"strict": True}

    with open(path / "pyproject.toml", "w") as f:
        f.write("[project]\nname = 'test'\n\n")
        f.write("[[project.dependencies]]\n")
        f.write("name = 'pytest'\n")
        f.write(f"\n{toml_str(config)}")


def toml_str(d):
    """Simple TOML serializer for test data."""
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"[tool.{k}]")
            for sk, sv in v.items():
                if isinstance(sv, bool):
                    lines.append(f"{sk} = {'true' if sv else 'false'}")
                elif isinstance(sv, str):
                    lines.append(f'{sk} = "{sv}"')
                else:
                    lines.append(f"{sk} = {sv}")
            lines.append("")
    return "\n".join(lines)