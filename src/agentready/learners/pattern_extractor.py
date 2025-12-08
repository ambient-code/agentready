"""Pattern extraction from assessment findings."""

from agentready.models import Assessment, DiscoveredSkill, Finding


class PatternExtractor:
    """Extracts reusable patterns from high-scoring assessment findings.

    Uses heuristic-based analysis to identify successful implementations
    that could be extracted as Claude Code skills.
    """

    # Minimum score threshold for pattern extraction
    MIN_SCORE_THRESHOLD = 80.0

    # Tier-based impact scores (how much each tier contributes to overall score)
    TIER_IMPACT_SCORES = {
        1: 50.0,  # Tier 1 (Essential) - highest impact
        2: 30.0,  # Tier 2 (Critical)
        3: 15.0,  # Tier 3 (Important)
        4: 5.0,  # Tier 4 (Advanced) - lowest impact
    }

    # Skill ID to human-readable name mapping for top tier-1 skills
    SKILL_NAMES = {
        "claude_md_file": {
            "skill_id": "setup-claude-md",
            "name": "Setup CLAUDE.md Configuration",
            "description": "Create comprehensive CLAUDE.md files with tech stack, standard commands, repository structure, and boundaries to optimize repositories for AI-assisted development",
        },
        "type_annotations": {
            "skill_id": "implement-type-annotations",
            "name": "Implement Type Annotations",
            "description": "Add comprehensive type hints to Python/TypeScript code to improve IDE support, catch errors early, and enable better AI code understanding",
        },
        "pre_commit_hooks": {
            "skill_id": "setup-pre-commit-hooks",
            "name": "Setup Pre-commit Hooks",
            "description": "Configure pre-commit hooks with formatters and linters to automatically enforce code quality standards before each commit",
        },
        "standard_project_layout": {
            "skill_id": "structure-repository-layout",
            "name": "Structure Repository Layout",
            "description": "Organize code according to language-specific standard project layouts to improve navigation and AI code understanding",
        },
        "lock_files": {
            "skill_id": "create-dependency-lock-files",
            "name": "Create Dependency Lock Files",
            "description": "Generate lock files to pin exact dependency versions for reproducible builds and consistent development environments",
        },
    }

    def __init__(self, assessment: Assessment, min_score: float = MIN_SCORE_THRESHOLD):
        """Initialize pattern extractor.

        Args:
            assessment: The assessment to extract patterns from
            min_score: Minimum finding score to consider (default: 80.0)
        """
        self.assessment = assessment
        self.min_score = min_score

    def extract_all_patterns(self) -> list[DiscoveredSkill]:
        """Extract all reusable patterns from the assessment.

        Returns:
            List of discovered skills, sorted by confidence (highest first)
        """
        discovered_skills = []

        for finding in self.assessment.findings:
            if self._should_extract_pattern(finding):
                skill = self._create_skill_from_finding(finding)
                if skill:
                    discovered_skills.append(skill)

        # Sort by confidence descending
        discovered_skills.sort(key=lambda s: s.confidence, reverse=True)

        return discovered_skills

    def extract_specific_patterns(
        self, attribute_ids: list[str]
    ) -> list[DiscoveredSkill]:
        """Extract patterns only from specific attributes.

        Args:
            attribute_ids: List of attribute IDs to extract patterns from

        Returns:
            List of discovered skills for specified attributes
        """
        discovered_skills = []

        for finding in self.assessment.findings:
            if finding.attribute.id in attribute_ids and self._should_extract_pattern(
                finding
            ):
                skill = self._create_skill_from_finding(finding)
                if skill:
                    discovered_skills.append(skill)

        # Sort by confidence descending
        discovered_skills.sort(key=lambda s: s.confidence, reverse=True)

        return discovered_skills

    def _should_extract_pattern(self, finding: Finding) -> bool:
        """Determine if a finding should have its pattern extracted.

        Args:
            finding: The finding to evaluate

        Returns:
            True if pattern should be extracted
        """
        # Only extract from passing findings with high scores
        if finding.status != "pass":
            return False

        if finding.score < self.min_score:
            return False

        # Skip if attribute not in our known skills mapping
        if finding.attribute.id not in self.SKILL_NAMES:
            return False

        return True

    def _create_skill_from_finding(self, finding: Finding) -> DiscoveredSkill | None:
        """Create a DiscoveredSkill from a high-scoring finding.

        Args:
            finding: The finding to convert to a skill

        Returns:
            DiscoveredSkill object or None if skill info not found
        """
        attribute_id = finding.attribute.id
        skill_info = self.SKILL_NAMES.get(attribute_id)

        if not skill_info:
            return None

        # Calculate confidence (directly from score)
        confidence = finding.score

        # Calculate impact based on tier
        tier = finding.attribute.tier
        impact_score = self.TIER_IMPACT_SCORES.get(tier, 5.0)

        # Calculate reusability (for now, use a simple heuristic based on tier)
        # Tier 1 attributes are more reusable across projects
        reusability_score = 100.0 - (tier - 1) * 20.0  # T1=100, T2=80, T3=60, T4=40

        # Extract code examples from finding details
        code_examples = self._extract_code_examples(finding)

        # Create pattern summary from finding
        pattern_summary = self._create_pattern_summary(finding)

        # Citations are not stored in current Attribute model, use empty list
        citations = []

        return DiscoveredSkill(
            skill_id=skill_info["skill_id"],
            name=skill_info["name"],
            description=skill_info["description"],
            confidence=confidence,
            source_attribute_id=attribute_id,
            reusability_score=reusability_score,
            impact_score=impact_score,
            pattern_summary=pattern_summary,
            code_examples=code_examples,
            citations=citations,
        )

    def _extract_code_examples(self, finding: Finding) -> list[str]:
        """Extract code examples from finding details.

        Args:
            finding: The finding to extract examples from

        Returns:
            List of code example strings
        """
        examples = []

        # Use evidence as examples
        if finding.evidence:
            for item in finding.evidence:
                if item and item.strip():
                    examples.append(item)

        # Add remediation steps as examples if available
        if finding.remediation and finding.remediation.steps:
            for step in finding.remediation.steps:
                if step.strip():
                    examples.append(step)

        return examples[:3]  # Limit to 3 examples

    def _create_pattern_summary(self, finding: Finding) -> str:
        """Create a human-readable pattern summary from a finding.

        Args:
            finding: The finding to summarize

        Returns:
            Pattern summary string
        """
        # Use the attribute's description as the pattern summary
        if finding.attribute.description:
            return finding.attribute.description

        # Fallback to finding evidence
        if finding.evidence and len(finding.evidence) > 0:
            evidence_str = "; ".join(finding.evidence[:2])
            return f"This repository successfully implements {finding.attribute.name}. {evidence_str}"

        # Final fallback
        return f"This repository successfully implements {finding.attribute.name} at a high level ({finding.score:.1f}/100)."
