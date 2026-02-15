"""Assessment metadata model for execution context and reproducibility."""

import getpass
import os
import socket
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AssessmentMetadata:
    """Metadata about the assessment execution context.

    Captures who ran the assessment, when, with what version, and what command.
    Critical for reproducibility, debugging, and multi-repository workflows.

    Attributes:
        agentready_version: Version of AgentReady used (e.g., "1.0.0")
        research_version: Version of research report/ruleset (e.g., "1.2.0")
        assessment_timestamp: ISO 8601 timestamp of when assessment started
        assessment_timestamp_human: Human-readable timestamp (e.g., "November 21, 2025 at 2:11 AM")
        executed_by: Username and hostname (e.g., "jeder@macbook")
        command: Full CLI command executed (e.g., "agentready assess . --verbose")
        working_directory: Absolute path of current working directory when executed
    """

    agentready_version: str
    research_version: str
    assessment_timestamp: str  # ISO 8601 format
    assessment_timestamp_human: str
    executed_by: str
    command: str
    working_directory: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "agentready_version": self.agentready_version,
            "research_version": self.research_version,
            "assessment_timestamp": self.assessment_timestamp,
            "assessment_timestamp_human": self.assessment_timestamp_human,
            "executed_by": self.executed_by,
            "command": self.command,
            "working_directory": self.working_directory,
        }

    @classmethod
    def create(
        cls, version: str, research_version: str, timestamp: datetime, command: str
    ) -> "AssessmentMetadata":
        """Create metadata from execution context.

        Args:
            version: AgentReady version string
            research_version: Research report version string
            timestamp: Assessment start time
            command: CLI command executed

        Returns:
            AssessmentMetadata instance
        """
        # Get username and hostname
        try:
            username = getpass.getuser()
        except Exception:
            username = "unknown"

        try:
            hostname = socket.gethostname().split(".")[0]  # Short hostname
        except Exception:
            hostname = "unknown"

        executed_by = f"{username}@{hostname}"

        # Format timestamps
        iso_timestamp = timestamp.isoformat()
        if os.name == "nt":
            human_timestamp = timestamp.strftime("%B %d, %Y at %#I:%M %p")
        else:
            human_timestamp = timestamp.strftime("%B %d, %Y at %-I:%M %p")

        # Get current working directory
        try:
            working_dir = os.getcwd()
        except Exception:
            working_dir = "unknown"

        return cls(
            agentready_version=version,
            research_version=research_version,
            assessment_timestamp=iso_timestamp,
            assessment_timestamp_human=human_timestamp,
            executed_by=executed_by,
            command=command,
            working_directory=working_dir,
        )
