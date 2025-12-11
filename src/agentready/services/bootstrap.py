"""Bootstrap generator for repository infrastructure."""

from pathlib import Path
from typing import List

from jinja2 import Environment, PackageLoader, select_autoescape

from .language_detector import LanguageDetector


class BootstrapGenerator:
    """Generates GitHub infrastructure files for repository."""

    def __init__(
        self,
        repo_path: Path,
        language: str = "auto",
        enable_release: bool = False,
        enable_publishing: bool = False,
    ):
        """Initialize bootstrap generator.

        Args:
            repo_path: Path to repository
            language: Primary language or "auto" to detect
            enable_release: Enable release automation workflow
            enable_publishing: Enable package publishing (PyPI/npm)
        """
        self.repo_path = repo_path
        self.language = self._detect_language(language)
        self.enable_release = enable_release
        self.enable_publishing = enable_publishing
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

    def generate_all(self, dry_run: bool = False) -> List[Path]:
        """Generate all bootstrap files including optional advanced features.

        Args:
            dry_run: If True, don't create files, just return paths

        Returns:
            List of created file paths
        """
        created_files = []

        # Base infrastructure (always generated)
        created_files.extend(self._generate_workflows(dry_run))
        created_files.extend(self._generate_github_templates(dry_run))
        created_files.extend(self._generate_precommit_config(dry_run))
        created_files.extend(self._generate_dependabot(dry_run))
        created_files.extend(self._generate_docs(dry_run))

        # Advanced features (opt-in)
        if self.enable_release:
            created_files.extend(self._generate_release_workflow(dry_run))
            created_files.extend(self._generate_release_config(dry_run))
            created_files.extend(self._generate_version_sync_scripts(dry_run))

        return created_files

    def _generate_workflows(self, dry_run: bool) -> List[Path]:
        """Generate GitHub Actions workflows."""
        workflows_dir = self.repo_path / ".github" / "workflows"
        created = []

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
        created.append(self._write_file(agentready_workflow, content, dry_run))

        # Tests workflow
        tests_workflow = workflows_dir / "tests.yml"
        template = self.env.get_template(f"{test_language}/workflows/tests.yml.j2")
        content = template.render()
        created.append(self._write_file(tests_workflow, content, dry_run))

        # Security workflow
        security_workflow = workflows_dir / "security.yml"
        template = self.env.get_template(f"{test_language}/workflows/security.yml.j2")
        content = template.render()
        created.append(self._write_file(security_workflow, content, dry_run))

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
            template = self.env.get_template(f"{template_language}/precommit.yaml.j2")
        except Exception:
            # Template doesn't exist, fallback to python
            template_language = "python"
            template = self.env.get_template(f"{template_language}/precommit.yaml.j2")

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

    def _generate_release_workflow(self, dry_run: bool) -> List[Path]:
        """Generate release automation workflow."""
        workflows_dir = self.repo_path / ".github" / "workflows"
        release_workflow = workflows_dir / "release.yml"

        # Only Python templates implemented in MVP
        if self.language != "python":
            return []

        template = self.env.get_template(f"{self.language}/workflows/release.yml.j2")
        context = {
            "enable_publishing": self.enable_publishing,
            "project_name": self._detect_project_name(),
        }
        content = template.render(**context)

        return [self._write_file(release_workflow, content, dry_run)]

    def _generate_release_config(self, dry_run: bool) -> List[Path]:
        """Generate .releaserc.json semantic-release configuration."""
        release_config_file = self.repo_path / ".releaserc.json"

        # Only Python templates implemented in MVP
        if self.language != "python":
            return []

        template = self.env.get_template(f"{self.language}/releaserc.json.j2")
        context = {
            "enable_publishing": self.enable_publishing,
            "has_claude_md": (self.repo_path / "CLAUDE.md").exists(),
        }
        content = template.render(**context)

        return [self._write_file(release_config_file, content, dry_run)]

    def _generate_version_sync_scripts(self, dry_run: bool) -> List[Path]:
        """Generate version synchronization scripts."""
        scripts_dir = self.repo_path / "scripts"

        # Only Python templates implemented in MVP
        if self.language != "python":
            return []

        sync_script = scripts_dir / "sync-version.sh"
        template = self.env.get_template(f"{self.language}/sync-version.sh.j2")
        context = {
            "project_name": self._detect_project_name(),
            "has_claude_md": (self.repo_path / "CLAUDE.md").exists(),
        }
        content = template.render(**context)

        return [self._write_file(sync_script, content, dry_run)]

    def _detect_project_name(self) -> str:
        """Detect project name from repository structure."""
        if self.language == "python":
            # Try pyproject.toml
            pyproject = self.repo_path / "pyproject.toml"
            if pyproject.exists():
                import re

                content = pyproject.read_text()
                match = re.search(r'name = "([^"]+)"', content)
                if match:
                    return match.group(1)

        # Fallback to directory name
        return self.repo_path.name

    def _write_file(self, path: Path, content: str, dry_run: bool) -> Path:
        """Write file to disk or simulate for dry run."""
        if dry_run:
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path
