"""Container and virtualization setup assessors."""

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class ContainerSetupAssessor(BaseAssessor):
    """Tier 4 Advanced - Container/virtualization setup with conditional applicability.

    Only applies if Dockerfile or Containerfile is detected in the repository.
    If no container files found, returns not_applicable (doesn't affect score).
    """

    @property
    def attribute_id(self) -> str:
        return "container_setup"

    @property
    def tier(self) -> int:
        return 4

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Container/Virtualization Setup",
            category="Build & Development",
            tier=self.tier,
            description="Container configuration for consistent development environments",
            criteria="Dockerfile/Containerfile, docker-compose.yml, .dockerignore, multi-stage builds",
            default_weight=0.01,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Only applicable if container files are present.

        This ensures the assessor doesn't penalize repositories that don't use containers.
        """
        container_files = ["Dockerfile", "Containerfile"]
        return any((repository.path / f).exists() for f in container_files)

    def assess(self, repository: Repository) -> Finding:
        """Check for container setup best practices."""
        if not self.is_applicable(repository):
            return Finding.not_applicable(
                self.attribute,
                reason="No container files detected (Dockerfile/Containerfile not found)",
            )

        score = 0
        evidence = []

        # 1. Dockerfile or Containerfile exists (40 points)
        dockerfile = None
        if (repository.path / "Dockerfile").exists():
            dockerfile = repository.path / "Dockerfile"
            score += 40
            evidence.append("✓ Dockerfile present")
        elif (repository.path / "Containerfile").exists():
            dockerfile = repository.path / "Containerfile"
            score += 40
            evidence.append("✓ Containerfile present (Podman)")

        # 2. Multi-stage build (10 points bonus)
        if dockerfile:
            try:
                content = dockerfile.read_text()
                from_count = content.count("FROM ")

                if from_count > 1:
                    score += 10
                    evidence.append(
                        "✓ Multi-stage build detected (optimized image size)"
                    )
                elif from_count == 1:
                    evidence.append(
                        "ℹ️ Single-stage build (consider multi-stage for smaller images)"
                    )
            except Exception:
                pass

        # 3. Docker Compose configuration (30 points)
        compose_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]
        found_compose = [f for f in compose_files if (repository.path / f).exists()]

        if found_compose:
            score += 30
            evidence.append(f"✓ Docker Compose configured ({', '.join(found_compose)})")

        # 4. .dockerignore file (20 points)
        dockerignore = repository.path / ".dockerignore"
        if dockerignore.exists():
            try:
                size = dockerignore.stat().st_size
                if size > 0:
                    score += 20
                    evidence.append(
                        "✓ .dockerignore present (excludes unnecessary files)"
                    )
                else:
                    evidence.append("⚠️ .dockerignore is empty")
            except OSError:
                pass
        else:
            evidence.append(
                "ℹ️ No .dockerignore file (consider adding to reduce image size)"
            )

        # Determine status
        if score >= 70:
            status = "pass"
            remediation = None
        elif score >= 40:
            status = "pass"  # Partial credit
            remediation = Remediation(
                summary="Improve container configuration",
                steps=[
                    "Add docker-compose.yml for multi-service development",
                    "Create .dockerignore to exclude build artifacts and secrets",
                    "Consider multi-stage builds to reduce image size",
                ],
                tools=["docker", "podman", "docker-compose"],
                commands=[
                    "docker build -t myapp .",
                    "docker-compose up -d",
                ],
                examples=[
                    "# .dockerignore example\n.git\n.venv\n__pycache__\n*.pyc\n.env\nnode_modules",
                    '# Multi-stage Dockerfile example\nFROM node:18 AS builder\nWORKDIR /app\nCOPY . .\nRUN npm ci && npm run build\n\nFROM node:18-alpine\nWORKDIR /app\nCOPY --from=builder /app/dist ./dist\nCMD ["node", "dist/index.js"]',
                ],
                citations=[
                    Citation(
                        source="Docker",
                        title="Dockerfile Best Practices",
                        url="https://docs.docker.com/develop/develop-images/dockerfile_best-practices/",
                        relevance="Official Docker guide for writing efficient and secure Dockerfiles",
                    ),
                ],
            )
        else:
            status = "fail"
            remediation = Remediation(
                summary="Complete container setup with best practices",
                steps=[
                    "Add docker-compose.yml for local development",
                    "Create .dockerignore to exclude unnecessary files",
                    "Use multi-stage builds for production images",
                    "Document container usage in README",
                ],
                tools=["docker", "podman", "docker-compose"],
                commands=[
                    "touch .dockerignore",
                    "touch docker-compose.yml",
                ],
                examples=[
                    "# docker-compose.yml example\nversion: '3.8'\nservices:\n  app:\n    build: .\n    ports:\n      - \"8000:8000\"\n    volumes:\n      - .:/app\n    environment:\n      - DEBUG=true",
                ],
                citations=[
                    Citation(
                        source="Docker",
                        title="Docker Compose Documentation",
                        url="https://docs.docker.com/compose/",
                        relevance="Official guide for defining and running multi-container applications",
                    ),
                ],
            )

        return Finding(
            attribute=self.attribute,
            status=status,
            score=min(score, 100),  # Cap at 100
            measured_value=f"{score} points",
            threshold="≥70 points (Dockerfile + compose + .dockerignore)",
            evidence=evidence,
            remediation=remediation,
            error_message=None,
        )
