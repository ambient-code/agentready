"""Configuration for GitHub integration features."""

from dataclasses import dataclass, field


@dataclass
class BadgeConfig:
    """Configuration for repository badges."""

    enabled: bool = True
    style: str = "flat-square"  # flat, flat-square, plastic, for-the-badge, social
    label: str = "AgentReady"


@dataclass
class ActionsConfig:
    """Configuration for GitHub Actions integration."""

    enabled: bool = True
    trigger_on: list[str] = field(
        default_factory=lambda: ["pull_request", "push"]
    )  # pull_request, push, workflow_dispatch
    post_comment: bool = True
    update_status: bool = True
    upload_artifacts: bool = True
    retention_days: int = 30


@dataclass
class StatusChecksConfig:
    """Configuration for GitHub status checks."""

    enabled: bool = True
    min_score: float = 75.0  # Minimum score to pass check
    require_improvement: bool = False  # Require score improvement on PRs
    use_checks_api: bool = True  # Use Checks API (preferred) vs Status API


@dataclass
class CommentsConfig:
    """Configuration for PR comments."""

    enabled: bool = True
    show_delta: bool = True  # Show score change
    show_trend: bool = False  # Show ASCII trend chart (requires historical data)
    collapse_details: bool = True  # Collapse detailed findings
    compact_mode: bool = False  # Use compact one-line format


@dataclass
class GitHubIntegrationConfig:
    """Complete GitHub integration configuration."""

    badge: BadgeConfig = field(default_factory=BadgeConfig)
    actions: ActionsConfig = field(default_factory=ActionsConfig)
    status_checks: StatusChecksConfig = field(default_factory=StatusChecksConfig)
    comments: CommentsConfig = field(default_factory=CommentsConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "GitHubIntegrationConfig":
        """
        Create config from dictionary (e.g., loaded from YAML).

        Args:
            data: Dictionary with config data

        Returns:
            GitHubIntegrationConfig instance
        """
        badge_data = data.get("badge", {})
        actions_data = data.get("actions", {})
        status_data = data.get("status_checks", {})
        comments_data = data.get("comments", {})

        return cls(
            badge=BadgeConfig(**badge_data),
            actions=ActionsConfig(**actions_data),
            status_checks=StatusChecksConfig(**status_data),
            comments=CommentsConfig(**comments_data),
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "badge": {
                "enabled": self.badge.enabled,
                "style": self.badge.style,
                "label": self.badge.label,
            },
            "actions": {
                "enabled": self.actions.enabled,
                "trigger_on": self.actions.trigger_on,
                "post_comment": self.actions.post_comment,
                "update_status": self.actions.update_status,
                "upload_artifacts": self.actions.upload_artifacts,
                "retention_days": self.actions.retention_days,
            },
            "status_checks": {
                "enabled": self.status_checks.enabled,
                "min_score": self.status_checks.min_score,
                "require_improvement": self.status_checks.require_improvement,
                "use_checks_api": self.status_checks.use_checks_api,
            },
            "comments": {
                "enabled": self.comments.enabled,
                "show_delta": self.comments.show_delta,
                "show_trend": self.comments.show_trend,
                "collapse_details": self.comments.collapse_details,
                "compact_mode": self.comments.compact_mode,
            },
        }

    def should_post_comment(self) -> bool:
        """Check if PR comments should be posted."""
        return self.comments.enabled and self.actions.enabled

    def should_update_status(self) -> bool:
        """Check if status checks should be updated."""
        return self.status_checks.enabled and self.actions.enabled

    def get_status_state(self, score: float) -> str:
        """
        Determine status state based on score and configuration.

        Args:
            score: Assessment score (0-100)

        Returns:
            Status state: "success", "failure", or "error"
        """
        if score >= self.status_checks.min_score:
            return "success"
        elif score >= 60:
            return "error"  # Warning state
        else:
            return "failure"
