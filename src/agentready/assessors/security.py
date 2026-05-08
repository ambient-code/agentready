"""Security assessors for dependency scanning, SAST, and secret detection."""

import json

import yaml

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class DependencySecurityAssessor(BaseAssessor):
    """Tier 1 Essential - Dependency security scanning and vulnerability detection.

    Combines security_scanning and dependency_freshness concerns.
    Checks for security tooling, vulnerability scanning, and SAST configuration.
    """

    @property
    def attribute_id(self) -> str:
        return "dependency_security"

    @property
    def tier(self) -> int:
        return 1  # Tier 1 per user request

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Dependency Security & Vulnerability Scanning",
            category="Security",
            tier=self.tier,
            description="Security scanning tools configured for dependencies and code",
            criteria="Dependabot, Renovate, CodeQL, or SAST tools configured; secret detection enabled",
            default_weight=0.04,  # Combined weight
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for security scanning tools and vulnerability detection."""
        score = 0
        evidence = []
        tools_found = []
        package_json = repository.path / "package.json"

        # 1. Dependency update tools - Dependabot OR Renovate (30 points)
        # Note: Both tools serve the same purpose (dependency updates), so only one gets credit
        # to avoid double-counting. If both are present, Dependabot wins (checked first).
        dependabot_config = repository.path / ".github" / "dependabot.yml"
        renovate_configs = [
            repository.path / "renovate.json",
            repository.path
            / "renovate.json5",  # Note: JSON5 not parseable by stdlib json
            repository.path / ".github" / "renovate.json",
            repository.path
            / ".github"
            / "renovate.json5",  # Note: JSON5 not parseable by stdlib json
            repository.path / ".renovaterc",
            repository.path / ".renovaterc.json",
        ]

        if dependabot_config.exists():
            score += 30
            tools_found.append("Dependabot")
            evidence.append("✓ Dependabot configured for dependency updates")

            # Bonus: Check if updates are scheduled
            try:
                config = yaml.safe_load(dependabot_config.read_text())
                if config and "updates" in config and len(config["updates"]) > 0:
                    score += 5
                    evidence.append(
                        f"  {len(config['updates'])} package ecosystem(s) monitored"
                    )
            except Exception:
                pass

        else:
            # Check for any Renovate configuration (files or package.json)
            has_renovate_files = any(config.exists() for config in renovate_configs)
            has_renovate_package_json = False
            pkg_renovate_config = None

            # Check package.json for renovate config
            if package_json.exists():
                try:
                    pkg = json.loads(package_json.read_text())
                    if "renovate" in pkg:
                        has_renovate_package_json = True
                        pkg_renovate_config = pkg["renovate"]
                except Exception:
                    pass

            # If any Renovate source exists, apply scoring
            if has_renovate_files or has_renovate_package_json:
                score += 30
                tools_found.append("Renovate")

                # Add specific evidence based on source
                if has_renovate_files:
                    evidence.append("✓ Renovate configured for dependency updates")
                elif has_renovate_package_json:
                    evidence.append("✓ Renovate configured in package.json")

                # Bonus: Check for meaningful configuration across all sources
                meaningful_keys = {
                    "extends",
                    "schedule",
                    "packageRules",
                    "rangeStrategy",
                    "semanticCommits",
                }

                bonus_awarded = False

                # Check file-based configs first
                for config_file in renovate_configs:
                    if config_file.exists() and not config_file.name.endswith(".json5"):
                        try:
                            config = json.loads(config_file.read_text())
                            if config and any(key in config for key in meaningful_keys):
                                score += 5
                                evidence.append(
                                    "  Meaningful Renovate configuration detected"
                                )
                                bonus_awarded = True
                                break
                        except Exception:
                            continue

                # If no file-based bonus found, check cached package.json renovate config
                if (
                    not bonus_awarded
                    and has_renovate_package_json
                    and pkg_renovate_config
                    and isinstance(pkg_renovate_config, dict)
                ):
                    if any(key in pkg_renovate_config for key in meaningful_keys):
                        score += 5
                        evidence.append("  Meaningful Renovate configuration detected")

        # 2. CodeQL / GitHub Security Scanning (25 points)
        codeql_workflow = repository.path / ".github" / "workflows"
        if codeql_workflow.exists():
            codeql_files = list(codeql_workflow.glob("*codeql*.yml")) + list(
                codeql_workflow.glob("*codeql*.yaml")
            )
            if codeql_files:
                score += 25
                tools_found.append("CodeQL")
                evidence.append("✓ CodeQL security scanning configured")

        # 3. Python dependency scanners (20 points)
        if "Python" in repository.languages:
            # Check for pip-audit, safety, or bandit
            pyproject = repository.path / "pyproject.toml"
            if pyproject.exists():
                try:
                    content = pyproject.read_text()
                    if "pip-audit" in content or "safety" in content:
                        score += 10
                        tools_found.append("pip-audit/safety")
                        evidence.append(
                            "✓ Python dependency scanner configured (pip-audit/safety)"
                        )
                except Exception:
                    pass

            # Check for Bandit (SAST)
            if pyproject.exists():
                try:
                    content = pyproject.read_text()
                    if "bandit" in content:
                        score += 10
                        tools_found.append("Bandit")
                        evidence.append("✓ Bandit SAST configured for Python")
                except Exception:
                    pass

        # 4. JavaScript/TypeScript dependency scanners (20 points)
        if "JavaScript" in repository.languages or "TypeScript" in repository.languages:
            if package_json.exists():
                try:
                    pkg = json.loads(package_json.read_text())
                    scripts = pkg.get("scripts", {})

                    # Check for npm audit or yarn audit in scripts
                    if any("audit" in str(v) for v in scripts.values()):
                        score += 10
                        tools_found.append("npm/yarn audit")
                        evidence.append("✓ npm/yarn audit configured")

                    # Check for Snyk
                    deps = {
                        **pkg.get("dependencies", {}),
                        **pkg.get("devDependencies", {}),
                    }
                    if "snyk" in deps:
                        score += 10
                        tools_found.append("Snyk")
                        evidence.append("✓ Snyk security scanning configured")
                except Exception:
                    pass

        # 5. Secret detection in pre-commit (20 points)
        precommit_config = repository.path / ".pre-commit-config.yaml"
        if precommit_config.exists():
            try:
                content = precommit_config.read_text()
                secret_tools = ["detect-secrets", "gitleaks", "truffleHog"]
                found_secret_tools = [tool for tool in secret_tools if tool in content]

                if found_secret_tools:
                    score += 20
                    tools_found.extend(found_secret_tools)
                    evidence.append(
                        f"✓ Secret detection configured ({', '.join(found_secret_tools)})"
                    )
            except Exception:
                pass

        # 6. Semgrep (multi-language SAST) (15 points)
        semgrep_config = repository.path / ".semgrep.yml"
        semgrep_workflow = repository.path / ".github" / "workflows"
        if semgrep_config.exists():
            score += 15
            tools_found.append("Semgrep")
            evidence.append("✓ Semgrep SAST configured")
        elif semgrep_workflow.exists():
            semgrep_files = list(semgrep_workflow.glob("*semgrep*.yml")) + list(
                semgrep_workflow.glob("*semgrep*.yaml")
            )
            if semgrep_files:
                score += 15
                tools_found.append("Semgrep")
                evidence.append("✓ Semgrep SAST in GitHub Actions")

        # 7. Security policy (5 points bonus)
        security_md = repository.path / "SECURITY.md"
        if security_md.exists():
            score += 5
            evidence.append("✓ SECURITY.md present (vulnerability disclosure policy)")

        # Determine status
        if score >= 60:
            status = "pass"
            remediation = None
        elif score >= 30:
            status = "pass"  # Partial credit
            remediation = Remediation(
                summary="Add more security scanning tools for comprehensive coverage",
                steps=[
                    "Enable Dependabot alerts in GitHub repository settings (or configure Renovate: add renovate.json to repository root)",
                    "Add CodeQL scanning workflow for SAST",
                    "Configure secret detection (detect-secrets, gitleaks)",
                    "Set up language-specific scanners (pip-audit, npm audit, Snyk)",
                ],
                tools=[
                    "Dependabot",
                    "Renovate",
                    "CodeQL",
                    "detect-secrets",
                    "pip-audit",
                    "npm audit",
                ],
                commands=[
                    "gh repo edit --enable-security",  # Enable GitHub security features
                    "pip install detect-secrets  # Python secret detection",
                    "npm audit  # JavaScript dependency audit",
                ],
                examples=[
                    "# .github/dependabot.yml\nversion: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n    schedule:\n      interval: weekly"
                ],
                citations=[
                    Citation(
                        source="OWASP",
                        title="Dependency-Check Project",
                        url="https://owasp.org/www-project-dependency-check/",
                        relevance="Open-source tool for detecting known vulnerabilities in dependencies",
                    ),
                    Citation(
                        source="GitHub",
                        title="Dependabot Documentation",
                        url="https://docs.github.com/en/code-security/dependabot",
                        relevance="Official guide for configuring automated dependency updates and security alerts",
                    ),
                ],
            )
        else:
            status = "fail"
            remediation = Remediation(
                summary="Configure security scanning for dependencies and code",
                steps=[
                    "Enable Dependabot in GitHub repository settings",
                    "Add .github/dependabot.yml configuration file",
                    "Or configure Renovate: add renovate.json to repository root",
                    "Set up CodeQL scanning for SAST",
                    "Add secret detection to pre-commit hooks",
                    "Configure language-specific security scanners",
                ],
                tools=[
                    "Dependabot",
                    "Renovate",
                    "CodeQL",
                    "detect-secrets",
                    "Bandit",
                    "Semgrep",
                ],
                commands=[
                    "gh repo edit --enable-security",
                    "pip install pre-commit detect-secrets",
                    "pre-commit install",
                ],
                examples=[
                    "# .github/dependabot.yml\nversion: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n    schedule:\n      interval: weekly",
                    '# renovate.json\n{\n  "extends": ["config:base"],\n  "schedule": "after 10pm every weekday"\n}',
                    "# .pre-commit-config.yaml\nrepos:\n  - repo: https://github.com/Yelp/detect-secrets\n    rev: v1.4.0\n    hooks:\n      - id: detect-secrets",
                ],
                citations=[
                    Citation(
                        source="OWASP",
                        title="OWASP Top 10",
                        url="https://owasp.org/www-project-top-ten/",
                        relevance="Industry-standard list of critical web application security risks",
                    ),
                    Citation(
                        source="GitHub",
                        title="Security Best Practices",
                        url="https://docs.github.com/en/code-security",
                        relevance="Official GitHub security features and best practices documentation",
                    ),
                ],
            )

        # Summary message
        if tools_found:
            summary = f"Security tools configured: {', '.join(tools_found)}"
        else:
            summary = "No security scanning tools configured"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=min(score, 100),  # Cap at 100
            measured_value=summary,
            threshold="≥60 points (Dependabot/Renovate + SAST or multiple scanners)",
            evidence=evidence if evidence else ["No security scanning tools detected"],
            remediation=remediation,
            error_message=None,
        )
