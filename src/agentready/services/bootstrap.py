"""Bootstrap generator for repository infrastructure."""

from pathlib import Path
from typing import List

from jinja2 import Environment, PackageLoader, select_autoescape

from .language_detector import LanguageDetector
from .repomix import RepomixService


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

    def generate_all(
        self, dry_run: bool = False, enable_repomix: bool = False
    ) -> List[Path]:
        """Generate all bootstrap files.

        Args:
            dry_run: If True, don't create files, just return paths
            enable_repomix: If True, generate Repomix configuration and workflow

        Returns:
            List of created file paths
        """
        created_files = []

        # GitHub Actions workflows
        created_files.extend(self._generate_workflows(dry_run, enable_repomix))

        # GitHub templates
        created_files.extend(self._generate_github_templates(dry_run))

        # Pre-commit hooks
        created_files.extend(self._generate_precommit_config(dry_run))

        # Dependabot
        created_files.extend(self._generate_dependabot(dry_run))

        # Contributing guidelines
        created_files.extend(self._generate_docs(dry_run))

        # Repomix configuration (if enabled)
        if enable_repomix:
            created_files.extend(self._generate_repomix_config(dry_run))

        return created_files

    def _generate_workflows(
        self, dry_run: bool, enable_repomix: bool = False
    ) -> List[Path]:
        """Generate GitHub Actions workflows."""
        workflows_dir = self.repo_path / ".github" / "workflows"
        created = []

        # Determine test workflow language (fallback to python if template doesn't exist)
        test_language = self.language
        try:
            self.env.get_template(f"workflows/tests-{test_language}.yml.j2")
        except Exception:
            # Template doesn't exist, fallback to python
            test_language = "python"

        # AgentReady assessment workflow
        agentready_workflow = workflows_dir / "agentready-assessment.yml"
        template = self.env.get_template("workflows/agentready-assessment.yml.j2")
        content = template.render(language=test_language)
        created.append(self._write_file(agentready_workflow, content, dry_run))

        # Tests workflow
        tests_workflow = workflows_dir / "tests.yml"
        template = self.env.get_template(f"workflows/tests-{test_language}.yml.j2")
        content = template.render()
        created.append(self._write_file(tests_workflow, content, dry_run))

        # Security workflow
        security_workflow = workflows_dir / "security.yml"
        template = self.env.get_template("workflows/security.yml.j2")
        content = template.render(language=test_language)
        created.append(self._write_file(security_workflow, content, dry_run))

        # Repomix update workflow (if enabled)
        if enable_repomix:
            repomix_workflow = workflows_dir / "repomix-update.yml"
            template = self.env.get_template("workflows/repomix-update.yml.j2")
            content = template.render()
            created.append(self._write_file(repomix_workflow, content, dry_run))

        return created

    def _generate_github_templates(self, dry_run: bool) -> List[Path]:
        """Generate GitHub issue and PR templates."""
        created = []

        # Issue templates
        issue_template_dir = self.repo_path / ".github" / "ISSUE_TEMPLATE"

        bug_template = issue_template_dir / "bug_report.md"
        template = self.env.get_template("issue_templates/bug_report.md.j2")
        content = template.render()
        created.append(self._write_file(bug_template, content, dry_run))

        feature_template = issue_template_dir / "feature_request.md"
        template = self.env.get_template("issue_templates/feature_request.md.j2")
        content = template.render()
        created.append(self._write_file(feature_template, content, dry_run))

        # PR template
        pr_template = self.repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md"
        template = self.env.get_template("PULL_REQUEST_TEMPLATE.md.j2")
        content = template.render()
        created.append(self._write_file(pr_template, content, dry_run))

        # CODEOWNERS
        codeowners = self.repo_path / ".github" / "CODEOWNERS"
        template = self.env.get_template("CODEOWNERS.j2")
        content = template.render()
        created.append(self._write_file(codeowners, content, dry_run))

        return created

    def _generate_precommit_config(self, dry_run: bool) -> List[Path]:
        """Generate pre-commit hooks configuration."""
        precommit_file = self.repo_path / ".pre-commit-config.yaml"

        # Determine language for template (fallback to python)
        template_language = self.language
        try:
            template = self.env.get_template(f"precommit-{template_language}.yaml.j2")
        except Exception:
            # Template doesn't exist, fallback to python
            template_language = "python"
            template = self.env.get_template(f"precommit-{template_language}.yaml.j2")

        content = template.render()
        return [self._write_file(precommit_file, content, dry_run)]

    def _generate_dependabot(self, dry_run: bool) -> List[Path]:
        """Generate Dependabot configuration."""
        dependabot_file = self.repo_path / ".github" / "dependabot.yml"
        template = self.env.get_template("dependabot.yml.j2")
        content = template.render(language=self.language)
        return [self._write_file(dependabot_file, content, dry_run)]

    def _generate_docs(self, dry_run: bool) -> List[Path]:
        """Generate contributing guidelines and code of conduct."""
        created = []

        # CONTRIBUTING.md
        contributing = self.repo_path / "CONTRIBUTING.md"
        if not contributing.exists():  # Don't overwrite existing
            template = self.env.get_template("CONTRIBUTING.md.j2")
            content = template.render(language=self.language)
            created.append(self._write_file(contributing, content, dry_run))

        # CODE_OF_CONDUCT.md (Red Hat standard)
        code_of_conduct = self.repo_path / "CODE_OF_CONDUCT.md"
        if not code_of_conduct.exists():
            template = self.env.get_template("CODE_OF_CONDUCT.md.j2")
            content = template.render()
            created.append(self._write_file(code_of_conduct, content, dry_run))

        return created

    def _generate_repomix_config(self, dry_run: bool) -> List[Path]:
        """Generate Repomix configuration files.

        Args:
            dry_run: If True, don't create files, just return paths

        Returns:
            List of created file paths
        """
        created = []

        if not dry_run:
            # Use RepomixService to generate config and ignore files
            service = RepomixService(self.repo_path)

            # Generate config (don't overwrite if exists)
            if service.generate_config(overwrite=False):
                created.append(service.config_path)

            # Generate ignore file (don't overwrite if exists)
            if service.generate_ignore(overwrite=False):
                created.append(service.ignore_path)
        else:
            # For dry run, just return the paths that would be created
            created.append(self.repo_path / "repomix.config.json")
            created.append(self.repo_path / ".repomixignore")

        return created

    def _write_file(self, path: Path, content: str, dry_run: bool) -> Path:
        """Write file to disk or simulate for dry run."""
        if dry_run:
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path
