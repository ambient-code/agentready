"""LLM-powered skill enrichment using Claude API."""

import hashlib
import json
import logging
import random
from pathlib import Path
from time import sleep

from anthropic import Anthropic, APIError, RateLimitError

from agentready.models import DiscoveredSkill, Finding, Repository
from agentready.services.llm_cache import LLMCache

from .code_sampler import CodeSampler
from .prompt_templates import PATTERN_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class LLMEnricher:
    """Enriches discovered skills using Claude API."""

    def __init__(
        self,
        client: Anthropic,
        cache_dir: Path | None = None,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """Initialize LLM enricher.

        Args:
            client: Anthropic API client
            cache_dir: Cache directory (default: .agentready/llm-cache)
            model: Claude model to use
        """
        self.client = client
        self.model = model
        self.cache = LLMCache(cache_dir or Path(".agentready/llm-cache"))
        self.code_sampler = None  # Set per-repository

    def enrich_skill(
        self,
        skill: DiscoveredSkill,
        repository: Repository,
        finding: Finding,
        use_cache: bool = True,
        max_retries: int = 3,
        _retry_count: int = 0,
    ) -> DiscoveredSkill:
        """Enrich skill with LLM-generated content.

        Args:
            skill: Basic skill from heuristic extraction
            repository: Repository being assessed
            finding: Finding that generated this skill
            use_cache: Whether to use cached responses
            max_retries: Maximum retry attempts for rate limits (default: 3)
            _retry_count: Internal retry counter (do not set manually)

        Returns:
            Enriched DiscoveredSkill with LLM-generated content, or original
            skill if enrichment fails after max retries
        """
        # Generate cache key
        evidence_str = "".join(finding.evidence) if finding.evidence else ""
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()[:16]
        cache_key = LLMCache.generate_key(skill.skill_id, finding.score, evidence_hash)

        # Check cache first
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Using cached enrichment for {skill.skill_id}")
                return cached

        # Initialize code sampler for this repository
        self.code_sampler = CodeSampler(repository)

        # Get relevant code samples
        code_samples = self.code_sampler.get_relevant_code(finding)

        # Call Claude API
        try:
            enrichment_data = self._call_claude_api(
                skill, finding, repository, code_samples
            )

            # Merge enrichment into skill
            enriched_skill = self._merge_enrichment(skill, enrichment_data)

            # Cache result
            if use_cache:
                self.cache.set(cache_key, enriched_skill)

            logger.info(f"Successfully enriched {skill.skill_id}")
            return enriched_skill

        except RateLimitError as e:
            # Check if max retries exceeded
            if _retry_count >= max_retries:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for {skill.skill_id}. "
                    f"Falling back to heuristic skill. "
                    f"Check API quota: https://console.anthropic.com/settings/limits"
                )
                return skill  # Graceful fallback to heuristic skill

            # Calculate backoff with jitter to prevent thundering herd
            retry_after = int(getattr(e, "retry_after", 60))
            jitter = random.uniform(0, min(retry_after * 0.1, 5))
            total_wait = retry_after + jitter

            logger.warning(
                f"Rate limit hit for {skill.skill_id} "
                f"(retry {_retry_count + 1}/{max_retries}): {e}"
            )
            logger.info(f"Retrying after {total_wait:.1f} seconds...")

            sleep(total_wait)

            return self.enrich_skill(
                skill, repository, finding, use_cache, max_retries, _retry_count + 1
            )

        except APIError as e:
            # Security: Sanitize error message to prevent API key exposure
            error_msg = str(e)
            # Anthropic errors shouldn't contain keys, but sanitize to be safe
            safe_error = error_msg if len(error_msg) < 200 else error_msg[:200]
            logger.error(f"API error enriching {skill.skill_id}: {safe_error}")
            return skill  # Fallback to original heuristic skill

        except Exception as e:
            # Security: Sanitize generic errors that might expose sensitive data
            error_msg = str(e)
            safe_error = error_msg if len(error_msg) < 200 else error_msg[:200]
            logger.error(f"Unexpected error enriching {skill.skill_id}: {safe_error}")
            return skill  # Fallback to original heuristic skill

    def _call_claude_api(
        self,
        skill: DiscoveredSkill,
        finding: Finding,
        repository: Repository,
        code_samples: str,
    ) -> dict:
        """Call Claude API for pattern extraction.

        Args:
            skill: Basic skill
            finding: Associated finding
            repository: Repository context
            code_samples: Code samples from repository

        Returns:
            Parsed JSON response from Claude
        """
        # Build prompt
        prompt = PATTERN_EXTRACTION_PROMPT.format(
            repo_name=repository.name,
            attribute_name=finding.attribute.name,
            attribute_description=finding.attribute.description,
            tier=finding.attribute.tier,
            score=finding.score,
            primary_language=getattr(repository, "primary_language", "Unknown"),
            evidence=(
                "\n".join(finding.evidence)
                if finding.evidence
                else "No evidence available"
            ),
            code_samples=code_samples,
        )

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON (handle markdown code blocks if present)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            return {}

    def _merge_enrichment(
        self, skill: DiscoveredSkill, enrichment: dict
    ) -> DiscoveredSkill:
        """Merge LLM enrichment data into DiscoveredSkill.

        Args:
            skill: Original skill
            enrichment: LLM response data

        Returns:
            New DiscoveredSkill with enriched content
        """
        if not enrichment:
            return skill

        # Update description if provided
        description = enrichment.get("skill_description", skill.description)

        # Update pattern summary (from instructions or keep original)
        instructions = enrichment.get("instructions", [])
        pattern_summary = skill.pattern_summary
        if instructions:
            pattern_summary = f"{skill.pattern_summary}\n\nDetailed implementation steps provided by LLM analysis."

        # Format code examples
        code_examples = []
        for example in enrichment.get("code_examples", []):
            if isinstance(example, dict):
                formatted = f"File: {example.get('file_path', 'unknown')}\n{example.get('code', '')}\n\nExplanation: {example.get('explanation', '')}"
                code_examples.append(formatted)
            elif isinstance(example, str):
                code_examples.append(example)

        # If no LLM examples, keep original
        if not code_examples:
            code_examples = skill.code_examples

        # Create new skill with enriched data
        # Store enrichment in code_examples for now (can extend DiscoveredSkill model later)
        enriched_examples = code_examples.copy()

        # Append best practices and anti-patterns as additional "examples"
        best_practices = enrichment.get("best_practices", [])
        if best_practices:
            enriched_examples.append(
                "=== BEST PRACTICES ===\n"
                + "\n".join(f"- {bp}" for bp in best_practices)
            )

        anti_patterns = enrichment.get("anti_patterns", [])
        if anti_patterns:
            enriched_examples.append(
                "=== ANTI-PATTERNS TO AVOID ===\n"
                + "\n".join(f"- {ap}" for ap in anti_patterns)
            )

        # Add instructions as first example
        if instructions:
            enriched_examples.insert(
                0,
                "=== INSTRUCTIONS ===\n"
                + "\n".join(f"{i+1}. {step}" for i, step in enumerate(instructions)),
            )

        return DiscoveredSkill(
            skill_id=skill.skill_id,
            name=skill.name,
            description=description,
            confidence=skill.confidence,
            source_attribute_id=skill.source_attribute_id,
            reusability_score=skill.reusability_score,
            impact_score=skill.impact_score,
            pattern_summary=pattern_summary,
            code_examples=enriched_examples,
            citations=skill.citations,
        )
