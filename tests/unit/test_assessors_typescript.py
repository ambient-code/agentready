"""Tests for TypeScript type annotation assessment (issues #383, #431)."""

import json
import subprocess

import pytest

from agentready.assessors.code_quality import TypeAnnotationsAssessor
from agentready.models.repository import Repository


def _make_ts_repo(tmp_path, languages=None, **kwargs):
    """Create a test TypeScript repository with git init."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return Repository(
        path=tmp_path,
        name="test-ts-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"TypeScript": 50},
        total_files=kwargs.get("total_files", 20),
        total_lines=kwargs.get("total_lines", 2000),
    )


def _write_tsconfig(path, strict=True, extra_options=None):
    """Write a tsconfig.json with optional strict mode."""
    config = {"compilerOptions": {"target": "ES2020", "module": "ESNext"}}
    if strict:
        config["compilerOptions"]["strict"] = True
    if extra_options:
        config["compilerOptions"].update(extra_options)
    path.write_text(json.dumps(config, indent=2))


class TestTypeAnnotationsAssessorTypeScript:
    """Test TypeScript support in TypeAnnotationsAssessor."""

    def test_ts_is_applicable(self, tmp_path):
        repo = _make_ts_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        assert assessor.is_applicable(repo)

    def test_root_tsconfig_strict_pass(self, tmp_path):
        """Root tsconfig.json with strict: true scores 100."""
        repo = _make_ts_repo(tmp_path)
        _write_tsconfig(tmp_path / "tsconfig.json", strict=True)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert any("strict: true" in e for e in finding.evidence)

    def test_root_tsconfig_no_strict_fail(self, tmp_path):
        """Root tsconfig.json without strict scores proportionally."""
        repo = _make_ts_repo(tmp_path)
        _write_tsconfig(tmp_path / "tsconfig.json", strict=False)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 100.0
        assert finding.remediation is not None

    def test_missing_tsconfig_fail(self, tmp_path):
        """No tsconfig.json at all scores 0."""
        repo = _make_ts_repo(tmp_path)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert any("not found" in e for e in finding.evidence)

    def test_jsonc_comments_parsed(self, tmp_path):
        """tsconfig.json with // and /* */ comments is parsed correctly (#383)."""
        repo = _make_ts_repo(tmp_path)
        (tmp_path / "tsconfig.json").write_text(
            "{\n"
            '  "compilerOptions": {\n'
            '    "strict": true, // enforce strict checks\n'
            "    /* multi-line\n"
            "       comment */\n"
            '    "target": "ES2020"\n'
            "  }\n"
            "}\n"
        )

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_monorepo_all_strict(self, tmp_path):
        """Monorepo with all packages strict scores 100 (#431)."""
        repo = _make_ts_repo(tmp_path)

        for pkg in ["packages/frontend", "packages/backend", "packages/shared"]:
            pkg_dir = tmp_path / pkg
            pkg_dir.mkdir(parents=True)
            _write_tsconfig(pkg_dir / "tsconfig.json", strict=True)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "3/3 strict" in finding.measured_value

    def test_monorepo_mixed_strict(self, tmp_path):
        """Monorepo with partial strict scores proportionally."""
        repo = _make_ts_repo(tmp_path)

        for pkg in ["packages/frontend", "packages/backend"]:
            pkg_dir = tmp_path / pkg
            pkg_dir.mkdir(parents=True)
            _write_tsconfig(pkg_dir / "tsconfig.json", strict=True)

        pkg_dir = tmp_path / "packages/legacy"
        pkg_dir.mkdir(parents=True)
        _write_tsconfig(pkg_dir / "tsconfig.json", strict=False)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert 0.0 < finding.score < 100.0
        assert "2/3 strict" in finding.measured_value

    def test_monorepo_none_strict(self, tmp_path):
        """Monorepo with no strict configs scores 0."""
        repo = _make_ts_repo(tmp_path)

        for pkg in ["packages/a", "packages/b"]:
            pkg_dir = tmp_path / pkg
            pkg_dir.mkdir(parents=True)
            _write_tsconfig(pkg_dir / "tsconfig.json", strict=False)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_node_modules_excluded(self, tmp_path):
        """tsconfig.json inside node_modules is ignored."""
        repo = _make_ts_repo(tmp_path)
        _write_tsconfig(tmp_path / "tsconfig.json", strict=True)

        nm_dir = tmp_path / "node_modules" / "some-pkg"
        nm_dir.mkdir(parents=True)
        _write_tsconfig(nm_dir / "tsconfig.json", strict=False)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "1/1 strict" in finding.measured_value

    def test_malformed_json_counts_as_non_strict(self, tmp_path):
        """Malformed tsconfig.json counts against the score, not silently skipped."""
        repo = _make_ts_repo(tmp_path)
        (tmp_path / "tsconfig.json").write_text("{ not valid json at all !!!")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert any("parse error" in e for e in finding.evidence)

    def test_malformed_mixed_with_valid(self, tmp_path):
        """One broken + one strict config penalizes the score."""
        repo = _make_ts_repo(tmp_path)
        _write_tsconfig(tmp_path / "tsconfig.json", strict=True)

        pkg_dir = tmp_path / "packages" / "broken"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "tsconfig.json").write_text("not json")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score < 100.0
        assert "1/2 strict" in finding.measured_value

    def test_root_plus_packages(self, tmp_path):
        """Root tsconfig + package tsconfigs all count."""
        repo = _make_ts_repo(tmp_path)
        _write_tsconfig(tmp_path / "tsconfig.json", strict=True)

        pkg_dir = tmp_path / "packages" / "lib"
        pkg_dir.mkdir(parents=True)
        _write_tsconfig(pkg_dir / "tsconfig.json", strict=True)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "2/2 strict" in finding.measured_value


class TestStripJsonComments:
    """Test the JSONC comment stripper."""

    def test_no_comments(self):
        text = '{"key": "value"}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        assert json.loads(result) == {"key": "value"}

    def test_line_comment(self):
        text = '{\n  "key": "value" // comment\n}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        assert json.loads(result) == {"key": "value"}

    def test_block_comment(self):
        text = '{\n  /* block */\n  "key": "value"\n}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        assert json.loads(result) == {"key": "value"}

    def test_comment_chars_in_string_preserved(self):
        text = '{"url": "https://example.com"}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        assert json.loads(result) == {"url": "https://example.com"}

    def test_multiline_block_comment(self):
        text = '{\n  /* line1\n     line2 */\n  "key": true\n}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        assert json.loads(result) == {"key": True}

    def test_trailing_comma_not_fixed(self):
        text = '{"a": 1, // comment\n}'
        result = TypeAnnotationsAssessor._strip_json_comments(text)
        with pytest.raises(json.JSONDecodeError):
            json.loads(result)


class TestPythonStrictMode:
    """Tests for A.6: Python strict mode detection in TypeAnnotationsAssessor."""

    def _make_py_repo(self, tmp_path, typed_funcs=0, total_funcs=1):
        """Create a Python repo with configurable type annotation coverage."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        lines = []
        for i in range(typed_funcs):
            lines.append(f"def typed_{i}(x: int) -> str:\n    return str(x)\n")
        for i in range(total_funcs - typed_funcs):
            lines.append(f"def untyped_{i}(x):\n    return str(x)\n")
        (tmp_path / "module.py").write_text("".join(lines))
        subprocess.run(["git", "add", "module.py"], cwd=tmp_path, capture_output=True)
        return Repository(
            path=tmp_path,
            name="py-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 1},
            total_files=1,
            total_lines=len(lines) * 2,
        )

    def test_no_strict_config_no_bonus(self, tmp_path):
        """No strict mode config: no bonus and evidence says not configured."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        finding = TypeAnnotationsAssessor().assess(repo)
        assert any("not configured" in e for e in finding.evidence)

    def test_mypy_ini_strict_adds_bonus(self, tmp_path):
        """mypy.ini with strict=True adds +15 pts bonus."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)

        # Baseline: no strict config
        baseline = TypeAnnotationsAssessor().assess(repo)

        # With mypy.ini strict mode
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = True\n")
        finding_with = TypeAnnotationsAssessor().assess(repo)

        assert finding_with.score == baseline.score + 15.0

    def test_mypy_ini_strict_evidence(self, tmp_path):
        """mypy.ini strict mode shows in evidence."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = True\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert any("mypy.ini" in e for e in finding.evidence)

    def test_setup_cfg_strict_adds_bonus(self, tmp_path):
        """setup.cfg with [mypy] strict=True adds bonus."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "setup.cfg").write_text("[mypy]\nstrict = True\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert any("setup.cfg" in e for e in finding.evidence)
        assert finding.score == 15.0

    def test_pyproject_toml_mypy_strict_adds_bonus(self, tmp_path):
        """pyproject.toml [tool.mypy] strict=true adds bonus."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert any("pyproject.toml" in e for e in finding.evidence)
        assert finding.score == 15.0

    def test_pyproject_toml_disallow_untyped_defs_adds_bonus(self, tmp_path):
        """pyproject.toml [tool.mypy] disallow_untyped_defs counts as strict."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\ndisallow_untyped_defs = true\n"
        )
        finding = TypeAnnotationsAssessor().assess(repo)
        assert finding.score == 15.0

    def test_pyrightconfig_strict_adds_bonus(self, tmp_path):
        """pyrightconfig.json typeCheckingMode=strict adds bonus."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "strict"}\n')
        finding = TypeAnnotationsAssessor().assess(repo)
        assert any("pyrightconfig.json" in e for e in finding.evidence)
        assert finding.score == 15.0

    def test_pyrightconfig_basic_no_bonus(self, tmp_path):
        """pyrightconfig.json with basic mode does not add bonus."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "basic"}\n')
        finding = TypeAnnotationsAssessor().assess(repo)
        assert finding.score == 0.0

    def test_strict_bonus_caps_at_100(self, tmp_path):
        """Strict bonus does not push score above 100."""
        repo = self._make_py_repo(tmp_path, typed_funcs=1, total_funcs=1)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = True\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert finding.score == 100.0

    def test_disallow_untyped_defs_in_setup_cfg(self, tmp_path):
        """setup.cfg disallow_untyped_defs=True is recognised as strict."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "setup.cfg").write_text("[mypy]\ndisallow_untyped_defs = True\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert finding.score == 15.0

    def test_mypy_ini_non_strict_section_ignored(self, tmp_path):
        """strict=True in a non-[mypy] section is not counted."""
        repo = self._make_py_repo(tmp_path, typed_funcs=0, total_funcs=1)
        (tmp_path / "mypy.ini").write_text("[other]\nstrict = True\n")
        finding = TypeAnnotationsAssessor().assess(repo)
        assert finding.score == 0.0


class TestIniMypyIsStrict:
    """Unit tests for the _ini_mypy_is_strict static method."""

    def test_strict_true(self):
        assert TypeAnnotationsAssessor._ini_mypy_is_strict("[mypy]\nstrict = True\n")

    def test_strict_lowercase(self):
        assert TypeAnnotationsAssessor._ini_mypy_is_strict("[mypy]\nstrict = true\n")

    def test_disallow_untyped_defs(self):
        assert TypeAnnotationsAssessor._ini_mypy_is_strict(
            "[mypy]\ndisallow_untyped_defs = True\n"
        )

    def test_no_mypy_section(self):
        assert not TypeAnnotationsAssessor._ini_mypy_is_strict(
            "[flake8]\nstrict = True\n"
        )

    def test_wrong_section(self):
        assert not TypeAnnotationsAssessor._ini_mypy_is_strict(
            "[mypy-tests.*]\nstrict = True\n"
        )

    def test_empty_file(self):
        assert not TypeAnnotationsAssessor._ini_mypy_is_strict("")

    def test_strict_value_false(self):
        assert not TypeAnnotationsAssessor._ini_mypy_is_strict(
            "[mypy]\nstrict = False\n"
        )
