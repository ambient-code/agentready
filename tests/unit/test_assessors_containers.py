"""Tests for container assessors."""

import subprocess

from agentready.assessors.containers import ContainerSetupAssessor
from agentready.models.repository import Repository


class TestContainerSetupAssessor:
    """Test ContainerSetupAssessor."""

    def test_not_applicable_without_container_files(self, tmp_path):
        """Test that assessor returns not_applicable when no container files."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        (tmp_path / "src").mkdir()

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"
        assert "No container files detected" in finding.evidence[0]

    def test_dockerfile_only(self, tmp_path):
        """Test detection of Dockerfile only."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(
            "FROM python:3.12\nCOPY . /app\nRUN pip install -r requirements.txt\n"
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 40  # Dockerfile = 40 points
        assert finding.status == "pass"  # Partial credit
        assert any("Dockerfile present" in e for e in finding.evidence)
        assert finding.remediation is not None  # Should suggest improvements

    def test_containerfile_podman(self, tmp_path):
        """Test detection of Containerfile (Podman)."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Containerfile
        containerfile = tmp_path / "Containerfile"
        containerfile.write_text("FROM python:3.12\nCOPY . /app\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 40  # Containerfile = 40 points
        assert any("Containerfile present" in e for e in finding.evidence)

    def test_multi_stage_build(self, tmp_path):
        """Test detection of multi-stage builds."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create multi-stage Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(
            """FROM node:18 AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/index.js"]
"""
        )

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

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 50  # Dockerfile (40) + multi-stage bonus (10)
        assert any("Multi-stage build" in e for e in finding.evidence)

    def test_docker_compose(self, tmp_path):
        """Test detection of Docker Compose configuration."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Dockerfile
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")

        # Create docker-compose.yml
        compose = tmp_path / "docker-compose.yml"
        compose.write_text(
            """version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
"""
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 70  # Dockerfile (40) + compose (30)
        assert finding.status == "pass"
        assert any("Docker Compose" in e for e in finding.evidence)
        assert finding.remediation is None  # No remediation needed

    def test_dockerignore_file(self, tmp_path):
        """Test detection of .dockerignore file."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Dockerfile
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")

        # Create .dockerignore
        dockerignore = tmp_path / ".dockerignore"
        dockerignore.write_text(
            """.git
.venv
__pycache__
*.pyc
.env
node_modules
"""
        )

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 60  # Dockerfile (40) + .dockerignore (20)
        assert any(".dockerignore present" in e for e in finding.evidence)

    def test_empty_dockerignore(self, tmp_path):
        """Test that empty .dockerignore doesn't get points."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Dockerfile
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")

        # Create empty .dockerignore
        dockerignore = tmp_path / ".dockerignore"
        dockerignore.write_text("")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 40  # Only Dockerfile
        assert any(".dockerignore is empty" in e for e in finding.evidence)

    def test_comprehensive_container_setup(self, tmp_path):
        """Test repository with comprehensive container setup."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Multi-stage Dockerfile
        (tmp_path / "Dockerfile").write_text(
            """FROM python:3.12 AS builder
RUN pip install build

FROM python:3.12-slim
COPY --from=builder /app /app
"""
        )

        # docker-compose.yml
        (tmp_path / "docker-compose.yml").write_text(
            "version: '3.8'\nservices:\n  app:\n    build: .\n"
        )

        # .dockerignore
        (tmp_path / ".dockerignore").write_text(".git\n.venv\n__pycache__\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        # Perfect score: Dockerfile (40) + multi-stage (10) + compose (30) + dockerignore (20) = 100
        assert finding.score == 100
        assert finding.status == "pass"
        assert finding.remediation is None
        assert len(finding.evidence) >= 4  # All features detected

    def test_compose_yaml_variant(self, tmp_path):
        """Test detection of compose.yaml variant."""
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        # Create Dockerfile
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")

        # Create compose.yaml (not docker-compose.yaml)
        compose = tmp_path / "compose.yaml"
        compose.write_text("services:\n  app:\n    build: .\n")

        repo = Repository(
            path=tmp_path,
            name="test-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        assessor = ContainerSetupAssessor()
        finding = assessor.assess(repo)

        assert finding.score == 70  # Dockerfile (40) + compose (30)
        assert any("Docker Compose" in e for e in finding.evidence)
