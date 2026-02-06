"""Learning service for extracting patterns and generating skills."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from agentready.learners import PatternExtractor, SkillGenerator
from agentready.models import Assessment, DiscoveredSkill, Finding

logger = logging.getLogger(__name__)


class LearningService:
    """Orchestrates continuous learning workflow for skill extraction.

    Coordinates pattern extraction from assessments and skill generation
    in various output formats.
    """

    def __init__(
        self,
        min_confidence: float = 70.0,
        output_dir: Path | str = ".skills-proposals",
    ):
        """Initialize learning service.

        Args:
            min_confidence: Minimum confidence score to include skills (0-100)
            output_dir: Directory for generated skill files
        """
        self.min_confidence = min_confidence
        self.output_dir = Path(output_dir)
        self.skill_generator = SkillGenerator(output_dir=self.output_dir)

    def load_assessment(self, assessment_file: Path) -> Assessment:
        """Load assessment from JSON file.

        Args:
            assessment_file: Path to assessment JSON file

        Returns:
            Loaded Assessment object

        Raises:
            FileNotFoundError: If assessment file doesn't exist
            ValueError: If assessment file is invalid JSON
        """
        if not assessment_file.exists():
            raise FileNotFoundError(f"Assessment file not found: {assessment_file}")

        with open(assessment_file, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in assessment file: {e}")

        # For now, we work with the dict directly
        # In future, could deserialize to Assessment object
        return data

    def extract_patterns_from_file(
        self,
        assessment_file: Path,
        attribute_ids: list[str] | None = None,
        enable_llm: bool = False,
        llm_budget: int = 5,
        llm_max_retries: int = 3,
    ) -> list[DiscoveredSkill]:
        """Extract patterns from an assessment file.

        Args:
            assessment_file: Path to assessment JSON file
            attribute_ids: Optional list of specific attributes to extract
            enable_llm: Enable LLM enrichment
            llm_budget: Max number of skills to enrich with LLM
            llm_max_retries: Maximum retry attempts for LLM rate limits

        Returns:
            List of discovered skills meeting confidence threshold
        """
        # Load assessment (returns dict for now)
        assessment_data = self.load_assessment(assessment_file)

        # Convert to Assessment object for pattern extraction
        # For MVP, we'll work with the dict and create Finding objects manually
        # In future, add proper deserialization
        from agentready.models import Attribute, Finding, Repository

        # Reconstruct Assessment object from dict
        repo_data = assessment_data["repository"]

        # Try to use the path from the assessment data if it's a valid git repo
        # Otherwise use the parent directory of the assessment file
        repo_path_from_json = Path(repo_data.get("path", ""))
        if repo_path_from_json.exists() and (repo_path_from_json / ".git").exists():
            actual_repo_path = repo_path_from_json
        else:
            # Fallback: assume assessment is in .agentready/ subdirectory
            actual_repo_path = assessment_file.parent.parent

        repo = Repository(
            path=actual_repo_path,
            name=repo_data.get("name", "unknown"),
            url=repo_data.get("url"),
            branch=repo_data.get("branch", "unknown"),
            commit_hash=repo_data.get("commit_hash", "unknown"),
            languages=repo_data.get("languages", {}),
            total_files=repo_data["total_files"],
            total_lines=repo_data["total_lines"],
        )

        findings = []
        for finding_data in assessment_data["findings"]:
            # Reconstruct Attribute
            attr_data = finding_data["attribute"]

            attribute = Attribute(
                id=attr_data["id"],
                name=attr_data["name"],
                category=attr_data.get("category", "Unknown"),
                tier=attr_data["tier"],
                description=attr_data["description"],
                criteria=attr_data.get("criteria", ""),
                default_weight=attr_data.get("default_weight", 1.0),
            )

            # Reconstruct Finding
            finding = Finding(
                attribute=attribute,
                status=finding_data["status"],
                score=finding_data.get("score"),
                measured_value=finding_data.get("measured_value"),
                threshold=finding_data.get("threshold"),
                evidence=finding_data.get("evidence", []),
                remediation=None,  # Skip complex Remediation reconstruction for now
                error_message=finding_data.get("error_message"),
            )
            findings.append(finding)

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.fromisoformat(assessment_data["timestamp"]),
            overall_score=assessment_data["overall_score"],
            certification_level=assessment_data["certification_level"],
            attributes_assessed=assessment_data["attributes_assessed"],
            attributes_not_assessed=assessment_data.get(
                "attributes_skipped", assessment_data.get("attributes_not_assessed", 0)
            ),
            attributes_total=assessment_data["attributes_total"],
            findings=findings,
            config=None,  # Skip config for now
            duration_seconds=assessment_data["duration_seconds"],
        )

        # Extract patterns
        extractor = PatternExtractor(assessment, min_score=self.min_confidence)

        if attribute_ids:
            discovered_skills = extractor.extract_specific_patterns(attribute_ids)
        else:
            discovered_skills = extractor.extract_all_patterns()

        # Filter by min confidence
        discovered_skills = [
            s for s in discovered_skills if s.confidence >= self.min_confidence
        ]

        # Optionally enrich with LLM
        if enable_llm and discovered_skills:
            discovered_skills = self._enrich_with_llm(
                discovered_skills, assessment, llm_budget, llm_max_retries
            )

        return discovered_skills

    def generate_skills(
        self, skills: list[DiscoveredSkill], output_format: str = "json"
    ) -> list[Path]:
        """Generate skill files in specified format.

        Args:
            skills: List of discovered skills
            output_format: Format to generate (json, skill_md, github_issues, all)

        Returns:
            List of generated file paths
        """
        generated_files = []

        if output_format == "json":
            json_file = self._generate_json(skills)
            generated_files.append(json_file)

        elif output_format == "skill_md":
            for skill in skills:
                skill_file = self.skill_generator.generate_skill_file(skill)
                generated_files.append(skill_file)

        elif output_format == "github_issues":
            for skill in skills:
                issue_file = self.skill_generator.generate_github_issue(skill)
                generated_files.append(issue_file)

        elif output_format == "markdown":
            for skill in skills:
                report_file = self.skill_generator.generate_markdown_report(skill)
                generated_files.append(report_file)

        elif output_format == "all":
            # Generate JSON summary
            json_file = self._generate_json(skills)
            generated_files.append(json_file)

            # Generate all formats for each skill
            for skill in skills:
                results = self.skill_generator.generate_all_formats(skill)
                generated_files.extend(results.values())

        return generated_files

    def _generate_json(self, skills: list[DiscoveredSkill]) -> Path:
        """Generate JSON file with discovered skills.

        Args:
            skills: List of discovered skills

        Returns:
            Path to generated JSON file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "generated_at": datetime.now().isoformat(),
            "skill_count": len(skills),
            "min_confidence": self.min_confidence,
            "discovered_skills": [skill.to_dict() for skill in skills],
        }

        json_file = self.output_dir / "discovered-skills.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return json_file

    def _enrich_with_llm(
        self,
        skills: list[DiscoveredSkill],
        assessment: Assessment,
        budget: int,
        max_retries: int = 3,
    ) -> list[DiscoveredSkill]:
        """Enrich top N skills with LLM analysis.

        Args:
            skills: List of discovered skills
            assessment: Full assessment with findings
            budget: Max skills to enrich
            max_retries: Maximum retry attempts for LLM rate limits

        Returns:
            List with top skills enriched
        """
        from anthropic import Anthropic

        from agentready.learners.llm_enricher import LLMEnricher

        # Security: Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("LLM enrichment enabled but ANTHROPIC_API_KEY not set")
            return skills

        # Security: Clear API key from environment to prevent exposure
        # API keys should not persist in os.environ where they could be logged
        try:
            del os.environ["ANTHROPIC_API_KEY"]
        except KeyError:
            pass  # Already removed or never existed

        # Initialize LLM enricher
        client = Anthropic(api_key=api_key)
        enricher = LLMEnricher(client)

        # Security: Clear API key from local scope after client creation
        api_key = None

        # Enrich top N skills
        enriched_skills = []
        for i, skill in enumerate(skills):
            if i < budget:
                # Find the finding for this skill
                finding = self._find_finding_for_skill(assessment, skill)
                if finding:
                    try:
                        enriched = enricher.enrich_skill(
                            skill,
                            assessment.repository,
                            finding,
                            max_retries=max_retries,
                        )
                        enriched_skills.append(enriched)
                    except Exception as e:
                        logger.warning(f"Enrichment failed for {skill.skill_id}: {e}")
                        enriched_skills.append(skill)  # Fallback to original
                else:
                    enriched_skills.append(skill)
            else:
                # Beyond budget, keep original
                enriched_skills.append(skill)

        return enriched_skills

    def _find_finding_for_skill(
        self, assessment: Assessment, skill: DiscoveredSkill
    ) -> Finding | None:
        """Find the Finding that generated a skill."""
        for finding in assessment.findings:
            if finding.attribute.id == skill.source_attribute_id:
                return finding
        return None

    def run_full_workflow(
        self,
        assessment_file: Path,
        output_format: str = "all",
        attribute_ids: list[str] | None = None,
        enable_llm: bool = False,
        llm_budget: int = 5,
        llm_max_retries: int = 3,
    ) -> dict:
        """Run complete learning workflow: extract + generate.

        Args:
            assessment_file: Path to assessment JSON
            output_format: Format for generated skills
            attribute_ids: Optional specific attributes to extract
            enable_llm: Enable LLM enrichment
            llm_budget: Max skills to enrich with LLM
            llm_max_retries: Maximum retry attempts for LLM rate limits

        Returns:
            Dictionary with workflow results
        """
        # Extract patterns
        skills = self.extract_patterns_from_file(
            assessment_file,
            attribute_ids,
            enable_llm=enable_llm,
            llm_budget=llm_budget,
            llm_max_retries=llm_max_retries,
        )

        # Generate output files
        generated_files = self.generate_skills(skills, output_format)

        return {
            "skills_discovered": len(skills),
            "min_confidence": self.min_confidence,
            "output_format": output_format,
            "generated_files": [str(f) for f in generated_files],
            "skills": skills,
        }
