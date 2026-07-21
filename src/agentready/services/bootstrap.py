"""Bootstrap generator for repository infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .language_detector import LanguageDetector


@dataclass
class BootstrapResult:
    """Outcome of a single ``generate_all()`` invocation.

    Created and skipped lists are mutually exclusive and never contain
    ``None``. State is owned by the result of each ``generate_all`` call —
    callers must not reuse a previous result after another run.
    """

    created_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)

    @property
    def all_targets(self) -> list[Path]:
        """Every bootstrap target considered (created + skipped)."""
        return [*self.created_files, *self.skipped_files]


class BootstrapGenerator:
    """Generates GitHub infrastructure files for repository."""

    def __init__(self, repo_path: Path, language: str = "auto"):
        """Initialize bootstrap generator.

        Args:
            repo_path: Path to repository
            language: Primary language or "auto" to detect
        """
        self.repo_path = repo_path
        self.language = self._detect_language(language)
        self.env = Environment(
            loader=PackageLoader("agentready", "templates/bootstrap"),
            autoescape=select_autoescape(["html", "xml", "j2", "yaml", "yml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._result: BootstrapResult | None = None

    def _detect_language(self, language: str) -> str:
        """Detect primary language if auto."""
        if language != "auto":
            return language.lower()

        # Use language detector
        detector = LanguageDetector(self.repo_path)
        languages = detector.detect_languages()

        if not languages:
            return "python"  # Default fallback

        # Return most used language
        return max(languages, key=languages.get).lower()

    def generate_all(self, dry_run: bool = False) -> BootstrapResult:
        """Generate all bootstrap files without overwriting existing paths.

        Args:
            dry_run: If True, don't create files; classify would-create vs would-skip

        Returns:
            BootstrapResult with created/would-create and skipped/would-skip paths
        """
        self._result = BootstrapResult()

        # GitHub Actions workflows
        self._generate_workflows(dry_run)

        # GitHub templates
        self._generate_github_templates(dry_run)

        # Pre-commit hooks
        self._generate_precommit_config(dry_run)

        # Dependabot
        self._generate_dependabot(dry_run)

        # Contributing guidelines
        self._generate_docs(dry_run)

        return self._result

    def _generate_workflows(self, dry_run: bool) -> list[Path]:
        """Generate GitHub Actions workflows."""
        workflows_dir = self.repo_path / ".github" / "workflows"
        created: list[Path] = []

        # Determine test workflow language (fallback to python if template doesn't exist)
        test_language = self.language
        try:
            self.env.get_template(f"{test_language}/workflows/tests.yml.j2")
        except Exception:
            # Template doesn't exist, fallback to python
            test_language = "python"

        # AgentReady assessment workflow
        agentready_workflow = workflows_dir / "agentready-assessment.yml"
        template = self.env.get_template("workflows/agentready-assessment.yml.j2")
        content = template.render(language=test_language)
        path = self._write_file(agentready_workflow, content, dry_run)
        if path is not None:
            created.append(path)

        # Tests workflow
        tests_workflow = workflows_dir / "tests.yml"
        template = self.env.get_template(f"{test_language}/workflows/tests.yml.j2")
        content = template.render()
        path = self._write_file(tests_workflow, content, dry_run)
        if path is not None:
            created.append(path)

        # Security workflow
        security_workflow = workflows_dir / "security.yml"
        template = self.env.get_template(f"{test_language}/workflows/security.yml.j2")
        content = template.render()
        path = self._write_file(security_workflow, content, dry_run)
        if path is not None:
            created.append(path)

        # Repomix update workflow
        repomix_workflow = workflows_dir / "repomix-update.yml"
        template = self.env.get_template("workflows/repomix-update.yml.j2")
        content = template.render()
        path = self._write_file(repomix_workflow, content, dry_run)
        if path is not None:
            created.append(path)

        return created

    def _generate_github_templates(self, dry_run: bool) -> list[Path]:
        """Generate GitHub issue and PR templates."""
        created: list[Path] = []

        # Issue templates
        issue_template_dir = self.repo_path / ".github" / "ISSUE_TEMPLATE"

        bug_template = issue_template_dir / "bug_report.md"
        template = self.env.get_template("issue_templates/bug_report.md.j2")
        content = template.render()
        path = self._write_file(bug_template, content, dry_run)
        if path is not None:
            created.append(path)

        feature_template = issue_template_dir / "feature_request.md"
        template = self.env.get_template("issue_templates/feature_request.md.j2")
        content = template.render()
        path = self._write_file(feature_template, content, dry_run)
        if path is not None:
            created.append(path)

        # PR template
        pr_template = self.repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md"
        template = self.env.get_template("PULL_REQUEST_TEMPLATE.md.j2")
        content = template.render()
        path = self._write_file(pr_template, content, dry_run)
        if path is not None:
            created.append(path)

        # CODEOWNERS
        codeowners = self.repo_path / ".github" / "CODEOWNERS"
        template = self.env.get_template("CODEOWNERS.j2")
        content = template.render()
        path = self._write_file(codeowners, content, dry_run)
        if path is not None:
            created.append(path)

        return created

    def _generate_precommit_config(self, dry_run: bool) -> list[Path]:
        """Generate pre-commit hooks configuration."""
        precommit_file = self.repo_path / ".pre-commit-config.yaml"

        # Determine language for template (fallback to python)
        template_language = self.language
        try:
            template = self.env.get_template(f"{template_language}/precommit.yaml.j2")
        except Exception:
            # Template doesn't exist, fallback to python
            template_language = "python"
            template = self.env.get_template(f"{template_language}/precommit.yaml.j2")

        content = template.render()
        path = self._write_file(precommit_file, content, dry_run)
        return [path] if path is not None else []

    def _generate_dependabot(self, dry_run: bool) -> list[Path]:
        """Generate Dependabot configuration."""
        dependabot_file = self.repo_path / ".github" / "dependabot.yml"
        template = self.env.get_template("dependabot.yml.j2")
        content = template.render(language=self.language)
        path = self._write_file(dependabot_file, content, dry_run)
        return [path] if path is not None else []

    def _generate_docs(self, dry_run: bool) -> list[Path]:
        """Generate contributing guidelines and code of conduct."""
        created: list[Path] = []

        # No-clobber is enforced by _write_file for every target.
        contributing = self.repo_path / "CONTRIBUTING.md"
        template = self.env.get_template("CONTRIBUTING.md.j2")
        content = template.render(language=self.language)
        path = self._write_file(contributing, content, dry_run)
        if path is not None:
            created.append(path)

        code_of_conduct = self.repo_path / "CODE_OF_CONDUCT.md"
        template = self.env.get_template("CODE_OF_CONDUCT.md.j2")
        content = template.render()
        path = self._write_file(code_of_conduct, content, dry_run)
        if path is not None:
            created.append(path)

        return created

    def _record_created(self, path: Path) -> None:
        if self._result is not None:
            self._result.created_files.append(path)

    def _record_skipped(self, path: Path) -> None:
        if self._result is not None:
            self._result.skipped_files.append(path)

    def _write_file(self, path: Path, content: str, dry_run: bool) -> Path | None:
        """Create a file exclusively, or classify a dry-run would-create/skip.

        Never overwrites an existing file, symlink, or other filesystem entry.
        Uses exclusive create (``open(..., "x")``) so a race that creates the
        path between check and write is treated as a skip via FileExistsError.

        Returns:
            The path when created (or would be created in dry-run), else None.
        """
        if dry_run:
            # Any existing entry (file, symlink, directory) is a skip.
            if path.exists() or path.is_symlink():
                self._record_skipped(path)
                return None
            self._record_created(path)
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write(content)
        except FileExistsError:
            self._record_skipped(path)
            return None

        self._record_created(path)
        return path
