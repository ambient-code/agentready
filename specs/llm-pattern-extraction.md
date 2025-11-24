# LLM-Powered Pattern Extraction - Implementation Specification

**Status**: Ready for Implementation
**Priority**: P1 (High Value)
**Estimated Effort**: 1-2 weeks
**Dependencies**: `anthropic>=0.74.0`

---

## Overview

Enhance AgentReady's continuous learning loop with Claude API integration to generate high-quality, context-aware skills instead of using hardcoded heuristics.

**Current State**: Pattern extraction uses hardcoded skill descriptions, generic 3-step instructions, and evidence strings as "code examples"

**Target State**: LLM analyzes actual repository code to generate detailed instructions, real code examples with file paths, best practices, and anti-patterns

**Architecture**: Hybrid approach - heuristics for discovery, optional LLM enrichment for top N skills

---

## Requirements

### Functional Requirements

1. **Opt-in LLM Enrichment**: Users must explicitly enable with `--enable-llm` flag
2. **API Key Management**: Use `ANTHROPIC_API_KEY` environment variable
3. **Selective Enrichment**: Enrich only top N skills (default: 5) to control cost
4. **Caching**: Cache LLM responses for 7 days to avoid redundant API calls
5. **Graceful Fallback**: If LLM enrichment fails, fall back to heuristic-generated skill
6. **Code Sample Extraction**: Read relevant files from repository for analysis
7. **Structured Output**: LLM returns JSON matching expected schema

### Non-Functional Requirements

1. **Performance**: 2-6 seconds per skill enrichment, parallelizable
2. **Reliability**: Handle API rate limits with exponential backoff
3. **Maintainability**: Prompts stored in separate templates file
4. **Testability**: Mock Anthropic client in unit tests

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     LearningService                          │
│                                                              │
│  1. extract_patterns_from_file()                            │
│     ├─> PatternExtractor (heuristics)                       │
│     │   └─> Returns list[DiscoveredSkill]                   │
│     │                                                        │
│     └─> If --enable-llm:                                    │
│         ├─> LLMEnricher.enrich_skill() for top N           │
│         │   ├─> CodeSampler.get_relevant_code()            │
│         │   ├─> LLMCache.get() [check cache]               │
│         │   ├─> Anthropic API call [if cache miss]         │
│         │   └─> LLMCache.set() [save response]             │
│         │                                                    │
│         └─> Merge enriched skills back into list            │
│                                                              │
│  2. generate_skills() [unchanged]                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Assessment JSON
    ↓
PatternExtractor (heuristic extraction)
    ↓
List[DiscoveredSkill] (basic skills with placeholders)
    ↓
[IF --enable-llm]
    ↓
LLMEnricher
    ├─> CodeSampler → Read relevant .py files from repo
    ├─> PromptTemplates → Build analysis prompt
    ├─> LLMCache.get() → Check cache
    ├─> Anthropic API → Call Claude Sonnet 4.5
    ├─> Parse JSON response
    ├─> Merge into DiscoveredSkill
    └─> LLMCache.set() → Save for 7 days
    ↓
List[DiscoveredSkill] (enriched with LLM content)
    ↓
SkillGenerator → Generate SKILL.md files
```

---

## Implementation Plan

### Phase 1: Core Infrastructure

**File**: `src/agentready/learners/prompt_templates.py`

```python
"""Prompt templates for LLM-powered pattern extraction."""

PATTERN_EXTRACTION_PROMPT = """You are analyzing a high-scoring repository to extract a reusable pattern as a Claude Code skill.

## Context
Repository: {repo_name}
Attribute: {attribute_name} ({attribute_description})
Tier: {tier} (1=Essential, 4=Advanced)
Score: {score}/100
Primary Language: {primary_language}

## Evidence from Assessment
{evidence}

## Code Samples from Repository
{code_samples}

---

## Task

Extract this pattern as a Claude Code skill with the following components:

### 1. Skill Description (1-2 sentences)
Write an invocation-optimized description that helps Claude Code decide when to use this skill.
Focus on WHAT problem it solves and WHEN to apply it.

### 2. Step-by-Step Instructions (5-10 steps)
Provide concrete, actionable steps. Each step should:
- Start with an action verb
- Include specific commands or code where applicable
- Define success criteria for that step

Be explicit. Do not assume prior knowledge.

### 3. Code Examples (2-3 examples)
Extract real code snippets from the repository that demonstrate this pattern.
For EACH example:
- Include the file path
- Show the relevant code (10-50 lines)
- Explain WHY this demonstrates the pattern

### 4. Best Practices (3-5 principles)
Derive best practices from the successful implementation you analyzed.
What made this repository score {score}/100?

### 5. Anti-Patterns to Avoid (2-3 mistakes)
What common mistakes did this repository avoid?
What would have reduced the score?

---

## Output Format

Return ONLY valid JSON matching this schema:

{{
  "skill_description": "One sentence explaining what and when",
  "instructions": [
    "Step 1: Specific action with command",
    "Step 2: Next action with success criteria",
    ...
  ],
  "code_examples": [
    {{
      "file_path": "relative/path/to/file.py",
      "code": "actual code snippet",
      "explanation": "Why this demonstrates the pattern"
    }},
    ...
  ],
  "best_practices": [
    "Principle 1 derived from this repository",
    ...
  ],
  "anti_patterns": [
    "Common mistake this repo avoided",
    ...
  ]
}}

## Rules

1. NEVER invent code - only use code from the samples provided
2. Be specific - use exact file paths, line numbers, command syntax
3. Focus on actionable guidance, not theory
4. Derive insights from THIS repository, not general knowledge
5. Return ONLY the JSON object, no markdown formatting
"""

CODE_SAMPLING_GUIDANCE = """When selecting code samples to analyze:

1. For `claude_md_file`: Include the CLAUDE.md file itself
2. For `type_annotations`: Sample 3-5 .py files with type hints
3. For `pre_commit_hooks`: Include .pre-commit-config.yaml
4. For `standard_project_layout`: Show directory tree + key files
5. For `lock_files`: Include requirements.txt, poetry.lock, or go.sum

Limit to 3-5 files, max 100 lines per file to stay under token limits.
"""
```

---

**File**: `src/agentready/learners/code_sampler.py`

```python
"""Smart code sampling from repositories for LLM analysis."""

import logging
from pathlib import Path
from agentready.models import Repository, Finding

logger = logging.getLogger(__name__)

class CodeSampler:
    """Extracts relevant code samples from repository for LLM analysis."""

    # Mapping of attribute IDs to file patterns to sample
    ATTRIBUTE_FILE_PATTERNS = {
        "claude_md_file": ["CLAUDE.md"],
        "readme_file": ["README.md"],
        "type_annotations": ["**/*.py"],  # Sample Python files
        "pre_commit_hooks": [".pre-commit-config.yaml", ".github/workflows/*.yml"],
        "standard_project_layout": ["**/", "src/", "tests/", "docs/"],  # Directory structure
        "lock_files": ["requirements.txt", "poetry.lock", "package-lock.json", "go.sum", "Cargo.lock"],
        "test_coverage": ["pytest.ini", "pyproject.toml", ".coveragerc"],
        "conventional_commits": [".github/workflows/*.yml"],  # CI configs
        "gitignore": [".gitignore"],
    }

    def __init__(self, repository: Repository, max_files: int = 5, max_lines_per_file: int = 100):
        """Initialize code sampler.

        Args:
            repository: Repository to sample from
            max_files: Maximum number of files to include
            max_lines_per_file: Maximum lines per file to prevent token overflow
        """
        self.repository = repository
        self.max_files = max_files
        self.max_lines_per_file = max_lines_per_file

    def get_relevant_code(self, finding: Finding) -> str:
        """Get relevant code samples for a finding.

        Args:
            finding: The finding to get code for

        Returns:
            Formatted string with code samples
        """
        attribute_id = finding.attribute.id
        patterns = self.ATTRIBUTE_FILE_PATTERNS.get(attribute_id, [])

        if not patterns:
            logger.warning(f"No file patterns defined for {attribute_id}")
            return "No code samples available"

        # Collect files matching patterns
        files_to_sample = []
        for pattern in patterns:
            if pattern.endswith("/"):
                # Directory listing
                files_to_sample.append(self._get_directory_tree(pattern))
            else:
                # File pattern
                matching_files = list(self.repository.path.glob(pattern))
                files_to_sample.extend(matching_files[:self.max_files])

        # Format as string
        return self._format_code_samples(files_to_sample)

    def _get_directory_tree(self, dir_pattern: str) -> dict:
        """Get directory tree structure."""
        base_path = self.repository.path / dir_pattern.rstrip("/")
        if not base_path.exists():
            return {}

        tree = {"type": "directory", "path": str(base_path.relative_to(self.repository.path)), "children": []}

        for item in base_path.iterdir():
            if item.is_file():
                tree["children"].append({"type": "file", "name": item.name})
            elif item.is_dir() and not item.name.startswith("."):
                tree["children"].append({"type": "directory", "name": item.name})

        return tree

    def _format_code_samples(self, files: list) -> str:
        """Format files as readable code samples."""
        samples = []

        for file_item in files[:self.max_files]:
            if isinstance(file_item, dict):
                # Directory tree
                samples.append(f"## Directory Structure: {file_item['path']}\n")
                samples.append(self._format_tree(file_item))
            elif isinstance(file_item, Path):
                # Regular file
                try:
                    rel_path = file_item.relative_to(self.repository.path)
                    content = file_item.read_text(encoding="utf-8", errors="ignore")

                    # Truncate if too long
                    lines = content.splitlines()
                    if len(lines) > self.max_lines_per_file:
                        lines = lines[:self.max_lines_per_file]
                        lines.append("... (truncated)")

                    samples.append(f"## File: {rel_path}\n")
                    samples.append("```\n" + "\n".join(lines) + "\n```\n")

                except Exception as e:
                    logger.warning(f"Could not read {file_item}: {e}")

        return "\n".join(samples) if samples else "No code samples available"

    def _format_tree(self, tree: dict, indent: int = 0) -> str:
        """Format directory tree as text."""
        lines = []
        prefix = "  " * indent

        for child in tree.get("children", []):
            if child["type"] == "file":
                lines.append(f"{prefix}├── {child['name']}")
            elif child["type"] == "directory":
                lines.append(f"{prefix}├── {child['name']}/")

        return "\n".join(lines)
```

---

**File**: `src/agentready/services/llm_cache.py`

```python
"""LLM response caching to avoid redundant API calls."""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from agentready.models import DiscoveredSkill

logger = logging.getLogger(__name__)

class LLMCache:
    """Caches LLM enrichment responses."""

    def __init__(self, cache_dir: Path, ttl_days: int = 7):
        """Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time-to-live in days (default: 7)
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = ttl_days

    def get(self, cache_key: str) -> DiscoveredSkill | None:
        """Get cached skill if exists and not expired.

        Args:
            cache_key: Unique cache key

        Returns:
            Cached DiscoveredSkill or None if miss/expired
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            logger.debug(f"Cache miss: {cache_key}")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check expiration
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > timedelta(days=self.ttl_days):
                logger.info(f"Cache expired: {cache_key}")
                cache_file.unlink()  # Delete expired cache
                return None

            logger.info(f"Cache hit: {cache_key}")
            return DiscoveredSkill(**data["skill"])

        except Exception as e:
            logger.warning(f"Cache read error for {cache_key}: {e}")
            return None

    def set(self, cache_key: str, skill: DiscoveredSkill):
        """Save skill to cache.

        Args:
            cache_key: Unique cache key
            skill: DiscoveredSkill to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            data = {
                "cached_at": datetime.now().isoformat(),
                "skill": skill.to_dict(),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached: {cache_key}")

        except Exception as e:
            logger.warning(f"Cache write error for {cache_key}: {e}")

    @staticmethod
    def generate_key(attribute_id: str, score: float, evidence_hash: str) -> str:
        """Generate cache key from finding attributes.

        Args:
            attribute_id: Attribute ID (e.g., "claude_md_file")
            score: Finding score
            evidence_hash: Hash of evidence list

        Returns:
            Cache key string
        """
        key_data = f"{attribute_id}_{score}_{evidence_hash}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
```

---

**File**: `src/agentready/learners/llm_enricher.py`

```python
"""LLM-powered skill enrichment using Claude API."""

import json
import logging
import hashlib
from pathlib import Path
from anthropic import Anthropic, APIError, RateLimitError
from time import sleep

from agentready.models import DiscoveredSkill, Repository, Finding
from .code_sampler import CodeSampler
from .prompt_templates import PATTERN_EXTRACTION_PROMPT
from ..services.llm_cache import LLMCache

logger = logging.getLogger(__name__)

class LLMEnricher:
    """Enriches discovered skills using Claude API."""

    def __init__(
        self,
        client: Anthropic,
        cache_dir: Path | None = None,
        model: str = "claude-sonnet-4-5-20250929"
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
        use_cache: bool = True
    ) -> DiscoveredSkill:
        """Enrich skill with LLM-generated content.

        Args:
            skill: Basic skill from heuristic extraction
            repository: Repository being assessed
            finding: Finding that generated this skill
            use_cache: Whether to use cached responses

        Returns:
            Enriched DiscoveredSkill with LLM-generated content
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
            enrichment_data = self._call_claude_api(skill, finding, repository, code_samples)

            # Merge enrichment into skill
            enriched_skill = self._merge_enrichment(skill, enrichment_data)

            # Cache result
            if use_cache:
                self.cache.set(cache_key, enriched_skill)

            logger.info(f"Successfully enriched {skill.skill_id}")
            return enriched_skill

        except RateLimitError as e:
            logger.warning(f"Rate limit hit for {skill.skill_id}: {e}")
            # Exponential backoff
            retry_after = int(getattr(e, 'retry_after', 60))
            logger.info(f"Retrying after {retry_after} seconds...")
            sleep(retry_after)
            return self.enrich_skill(skill, repository, finding, use_cache)

        except APIError as e:
            logger.error(f"API error enriching {skill.skill_id}: {e}")
            return skill  # Fallback to original heuristic skill

        except Exception as e:
            logger.error(f"Unexpected error enriching {skill.skill_id}: {e}")
            return skill  # Fallback to original heuristic skill

    def _call_claude_api(
        self,
        skill: DiscoveredSkill,
        finding: Finding,
        repository: Repository,
        code_samples: str
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
            primary_language=getattr(repository, 'primary_language', 'Unknown'),
            evidence="\n".join(finding.evidence) if finding.evidence else "No evidence available",
            code_samples=code_samples
        )

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
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

    def _merge_enrichment(self, skill: DiscoveredSkill, enrichment: dict) -> DiscoveredSkill:
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
            enriched_examples.append("=== BEST PRACTICES ===\n" + "\n".join(f"- {bp}" for bp in best_practices))

        anti_patterns = enrichment.get("anti_patterns", [])
        if anti_patterns:
            enriched_examples.append("=== ANTI-PATTERNS TO AVOID ===\n" + "\n".join(f"- {ap}" for ap in anti_patterns))

        # Add instructions as first example
        if instructions:
            enriched_examples.insert(0, "=== INSTRUCTIONS ===\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(instructions)))

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
```

---

### Phase 2: Service Integration

**File**: `src/agentready/services/learning_service.py` (modifications)

```python
# Add imports at top
import os
from anthropic import Anthropic

# Modify extract_patterns_from_file method signature
def extract_patterns_from_file(
    self,
    assessment_file: Path,
    attribute_ids: list[str] | None = None,
    enable_llm: bool = False,
    llm_budget: int = 5
) -> list[DiscoveredSkill]:
    """Extract patterns from an assessment file.

    Args:
        assessment_file: Path to assessment JSON
        attribute_ids: Optional list of specific attributes to extract
        enable_llm: Enable LLM enrichment
        llm_budget: Max number of skills to enrich with LLM

    Returns:
        List of discovered skills meeting confidence threshold
    """
    # ... existing code to load assessment and create Assessment object ...

    # Extract patterns using heuristics
    extractor = PatternExtractor(assessment, min_score=self.min_confidence)

    if attribute_ids:
        discovered_skills = extractor.extract_specific_patterns(attribute_ids)
    else:
        discovered_skills = extractor.extract_all_patterns()

    # Filter by min confidence
    discovered_skills = [s for s in discovered_skills if s.confidence >= self.min_confidence]

    # Optionally enrich with LLM
    if enable_llm and discovered_skills:
        discovered_skills = self._enrich_with_llm(
            discovered_skills,
            assessment,
            llm_budget
        )

    return discovered_skills

def _enrich_with_llm(
    self,
    skills: list[DiscoveredSkill],
    assessment: Assessment,
    budget: int
) -> list[DiscoveredSkill]:
    """Enrich top N skills with LLM analysis.

    Args:
        skills: List of discovered skills
        assessment: Full assessment with findings
        budget: Max skills to enrich

    Returns:
        List with top skills enriched
    """
    from anthropic import Anthropic
    from agentready.learners.llm_enricher import LLMEnricher

    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("LLM enrichment enabled but ANTHROPIC_API_KEY not set")
        return skills

    # Initialize LLM enricher
    client = Anthropic(api_key=api_key)
    enricher = LLMEnricher(client)

    # Enrich top N skills
    enriched_skills = []
    for i, skill in enumerate(skills):
        if i < budget:
            # Find the finding for this skill
            finding = self._find_finding_for_skill(assessment, skill)
            if finding:
                try:
                    enriched = enricher.enrich_skill(skill, assessment.repository, finding)
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

def _find_finding_for_skill(self, assessment: Assessment, skill: DiscoveredSkill) -> Finding | None:
    """Find the Finding that generated a skill."""
    for finding in assessment.findings:
        if finding.attribute.id == skill.source_attribute_id:
            return finding
    return None

# Modify run_full_workflow to pass through LLM params
def run_full_workflow(
    self,
    assessment_file: Path,
    output_format: str = "all",
    attribute_ids: list[str] | None = None,
    enable_llm: bool = False,
    llm_budget: int = 5
) -> dict:
    """Run complete learning workflow: extract + generate.

    Args:
        assessment_file: Path to assessment JSON
        output_format: Format for generated skills
        attribute_ids: Optional specific attributes to extract
        enable_llm: Enable LLM enrichment
        llm_budget: Max skills to enrich with LLM

    Returns:
        Dictionary with workflow results
    """
    # Extract patterns
    skills = self.extract_patterns_from_file(
        assessment_file,
        attribute_ids,
        enable_llm=enable_llm,
        llm_budget=llm_budget
    )

    # ... rest of method unchanged ...
```

---

### Phase 3: CLI Enhancement

**File**: `src/agentready/cli/extract_skills.py` (modifications)

```python
# Add new options to extract-skills command
@click.option(
    "--enable-llm",
    is_flag=True,
    help="Enable LLM-powered skill enrichment (requires ANTHROPIC_API_KEY)",
)
@click.option(
    "--llm-budget",
    type=int,
    default=5,
    help="Maximum number of skills to enrich with LLM (default: 5)",
)
@click.option(
    "--llm-no-cache",
    is_flag=True,
    help="Bypass LLM response cache (always call API)",
)
def extract_skills(repository, output_format, output_dir, attribute, min_confidence, verbose, enable_llm, llm_budget, llm_no_cache):
    """Extract reusable patterns and generate Claude Code skills.

    ... existing docstring ...
    """

    # ... existing setup code ...

    # Display LLM status in header
    if enable_llm:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            click.echo(f"LLM enrichment: ENABLED (budget: {llm_budget} skills)")
            if llm_no_cache:
                click.echo("LLM cache: DISABLED")
        else:
            click.echo("⚠️  LLM enrichment: DISABLED (ANTHROPIC_API_KEY not set)")
            enable_llm = False

    # Run learning workflow with LLM params
    try:
        results = learning_service.run_full_workflow(
            assessment_file=assessment_file,
            output_format=output_format,
            attribute_ids=list(attribute) if attribute else None,
            enable_llm=enable_llm,
            llm_budget=llm_budget,
        )
    except Exception as e:
        click.echo(f"\nError during learning: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # ... existing results display ...

    # Show LLM info if used
    if enable_llm and results["skills_discovered"] > 0:
        enriched_count = min(llm_budget, results["skills_discovered"])
        click.echo(f"\n🤖 LLM-enriched {enriched_count} skill(s)")
```

---

### Phase 4: Testing

**File**: `tests/unit/learners/test_llm_enricher.py`

```python
"""Tests for LLM enrichment functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from anthropic import Anthropic

from agentready.learners.llm_enricher import LLMEnricher
from agentready.models import DiscoveredSkill, Repository, Finding, Attribute, Citation

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock(spec=Anthropic)

    # Mock response
    mock_response = Mock()
    mock_response.content = [Mock(text=json.dumps({
        "skill_description": "Enhanced description from LLM",
        "instructions": [
            "Step 1: Do something specific",
            "Step 2: Verify it worked",
            "Step 3: Commit the changes"
        ],
        "code_examples": [
            {
                "file_path": "src/example.py",
                "code": "def example():\n    pass",
                "explanation": "This shows the pattern"
            }
        ],
        "best_practices": [
            "Always use type hints",
            "Test your code"
        ],
        "anti_patterns": [
            "Don't use global variables",
            "Avoid mutable defaults"
        ]
    }))]

    client.messages.create.return_value = mock_response
    return client

@pytest.fixture
def basic_skill():
    """Basic skill from heuristic extraction."""
    return DiscoveredSkill(
        skill_id="test-skill",
        name="Test Skill",
        description="Basic description",
        confidence=95.0,
        source_attribute_id="test_attribute",
        reusability_score=100.0,
        impact_score=50.0,
        pattern_summary="Test pattern",
        code_examples=["Basic example"],
        citations=[]
    )

@pytest.fixture
def sample_repository(tmp_path):
    """Sample repository."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Create .git directory
    (repo_path / ".git").mkdir()

    # Create a sample file
    (repo_path / "test.py").write_text("def test():\n    pass")

    return Repository(
        path=repo_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 1},
        total_files=1,
        total_lines=2
    )

@pytest.fixture
def sample_finding():
    """Sample finding."""
    attr = Attribute(
        id="test_attribute",
        name="Test Attribute",
        category="Testing",
        tier=1,
        description="A test attribute",
        criteria="Must pass",
        default_weight=1.0
    )

    return Finding(
        attribute=attr,
        status="pass",
        score=95.0,
        measured_value="passing",
        threshold="pass",
        evidence=["Test evidence 1", "Test evidence 2"],
        remediation=None,
        error_message=None
    )

def test_enrich_skill_success(mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path):
    """Test successful skill enrichment."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Verify API was called
    assert mock_anthropic_client.messages.create.called

    # Verify enrichment
    assert enriched.description == "Enhanced description from LLM"
    assert len(enriched.code_examples) > len(basic_skill.code_examples)

def test_enrich_skill_uses_cache(mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path):
    """Test that second enrichment uses cache."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # First call
    enriched1 = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)
    first_call_count = mock_anthropic_client.messages.create.call_count

    # Second call (should use cache)
    enriched2 = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)
    second_call_count = mock_anthropic_client.messages.create.call_count

    # Verify cache was used
    assert second_call_count == first_call_count

def test_enrich_skill_api_error_fallback(basic_skill, sample_repository, sample_finding, tmp_path):
    """Test fallback to original skill on API error."""
    client = Mock(spec=Anthropic)
    client.messages.create.side_effect = Exception("API Error")

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Should return original skill
    assert enriched.skill_id == basic_skill.skill_id
    assert enriched.description == basic_skill.description
```

---

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    "anthropic>=0.74.0",
    # ... existing dependencies
]
```

---

## Success Criteria

1. **LLM Integration Works**:
   - `agentready extract-skills . --enable-llm` successfully calls Claude API
   - Enriched skills have detailed instructions (5-10 steps)
   - Code examples include real file paths from repository

2. **Caching Works**:
   - First run calls API
   - Second run uses cache (verify no API calls)
   - Cache respects 7-day TTL

3. **Graceful Fallback**:
   - Works without `ANTHROPIC_API_KEY` (uses heuristics)
   - API errors don't crash, fallback to heuristic skills
   - Rate limit errors retry with backoff

4. **CLI Integration**:
   - `--enable-llm` flag works
   - `--llm-budget` limits enrichment count
   - Verbose output shows which skills were enriched

5. **Test Coverage**:
   - Unit tests pass with mocked Anthropic client
   - Integration test enriches at least 1 skill
   - Tests cover cache hit/miss, API errors, fallback

---

## Example Usage

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Run assessment
agentready assess .

# Extract skills with LLM enrichment
agentready extract-skills . --enable-llm --llm-budget 5 --verbose

# Expected output:
# 🧠 AgentReady Skill Extraction
# ==================================================
# Repository: /Users/jeder/repos/agentready
# LLM enrichment: ENABLED (budget: 5 skills)
#
# Enriching skill 1/5: setup-claude-md... ✓
# Enriching skill 2/5: implement-type-annotations... ✓ (cached)
#
# ==================================================
# ✅ Discovered 5 skill(s) with confidence ≥70%
# 🤖 LLM-enriched 5 skill(s)
```

---

## Implementation Checklist

- [ ] Add `anthropic>=0.74.0` to pyproject.toml
- [ ] Create `src/agentready/learners/prompt_templates.py`
- [ ] Create `src/agentready/learners/code_sampler.py`
- [ ] Create `src/agentready/services/llm_cache.py`
- [ ] Create `src/agentready/learners/llm_enricher.py`
- [ ] Modify `src/agentready/services/learning_service.py`
- [ ] Modify `src/agentready/cli/extract_skills.py`
- [ ] Create `tests/unit/learners/test_llm_enricher.py`
- [ ] Run linters (black, isort, ruff)
- [ ] Test on AgentReady repository (dogfooding)
- [ ] Update CLAUDE.md with LLM enrichment documentation
- [ ] Update README.md with API key setup instructions

---

## Notes

- **Cost**: Not tracking tokens/cost in this version to simplify implementation
- **Model**: Using `claude-sonnet-4-5-20250929` (latest Sonnet 4.5)
- **Rate Limiting**: Basic exponential backoff on RateLimitError
- **Caching**: Simple file-based cache with 7-day TTL
- **Code Sampling**: Limits to 5 files, 100 lines per file to manage token usage
- **Fallback**: Always preserves heuristic behavior if LLM fails

---

**Ready for Implementation**: This spec provides all necessary code, architecture decisions, and implementation steps to add Claude API support to AgentReady's continuous learning loop.
