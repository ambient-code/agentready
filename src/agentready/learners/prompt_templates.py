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
3. For `deterministic_enforcement`: Include .pre-commit-config.yaml and .claude/settings.json
4. For `standard_project_layout`: Show directory tree + key files
5. For `lock_files`: Include requirements.txt, poetry.lock, or go.sum

Limit to 3-5 files, max 100 lines per file to stay under token limits.
"""
