"""Pattern and knowledge assessors for skills, design intent, and progressive disclosure."""

import re

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class PatternReferencesAssessor(BaseAssessor):
    """Assesses availability of pattern references for common changes.

    Tier 2 Critical (3% weight) - Pattern references turn novel changes into
    copy-modify changes, which agents handle far more reliably.
    """

    @property
    def attribute_id(self) -> str:
        return "pattern_references"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Pattern References for Common Changes",
            category="Agent Patterns & Knowledge",
            tier=self.tier,
            description="Reference implementations and skills for common change types",
            criteria="3-5 pattern references or skills documented",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for pattern references in skills directories and context files."""
        score = 0.0
        evidence = []

        # Check for .claude/skills/ directory
        skills_dir = repository.path / ".claude" / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            skill_files = list(skills_dir.rglob("SKILL.md"))
            if skill_files:
                score += 60.0
                evidence.append(
                    f".claude/skills/ directory with {len(skill_files)} SKILL.md file(s)"
                )

        # Check for pattern references in context files
        context_files = ["CLAUDE.md", "AGENTS.md"]
        pattern_keywords = [
            r"follow\s+the\s+pattern",
            r"reference\s+implementation",
            r"use\s+.*\s+as\s+a?\s*template",
            r"example\s+in\s+`[^`]+`",
            r"pattern\s+in\s+`[^`]+`",
            r"see\s+`[^`]+`\s+for",
            r"based\s+on\s+`[^`]+`",
        ]

        for filename in context_files:
            filepath = repository.path / filename
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for pattern in pattern_keywords:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    if score < 60:
                        score += 40.0
                    evidence.append(
                        f"Pattern references found in {filename} ({len(matches)} reference(s))"
                    )
                    break

        # Check for docs/examples/ or examples/ directory
        example_dirs = ["examples", "docs/examples", "docs/patterns"]
        for dir_name in example_dirs:
            example_dir = repository.path / dir_name
            if example_dir.exists() and example_dir.is_dir():
                files = list(example_dir.iterdir())
                if files:
                    score = min(score + 20.0, 100.0)
                    evidence.append(f"{dir_name}/ directory with {len(files)} file(s)")

        score = min(score, 100.0)

        if score >= 40:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value=f"{len(evidence)} reference source(s)",
                threshold="pattern references or skills documented",
                evidence=evidence,
                remediation=None if score >= 60 else self._create_remediation(),
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=score,
                measured_value="none found",
                threshold="pattern references or skills documented",
                evidence=evidence or ["No pattern references or skills found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        return Remediation(
            summary="Add pattern references for 3-5 common change types",
            steps=[
                "Identify your 3-5 most common change types (new endpoint, new component, etc.)",
                "For each, point to one real example in the codebase",
                "Create .claude/skills/ directory with SKILL.md files for detailed patterns",
                "Or add a 'Pattern References' section to CLAUDE.md/AGENTS.md",
            ],
            tools=[],
            commands=["mkdir -p .claude/skills"],
            examples=[
                "# In CLAUDE.md:\n## Pattern References\n- New API endpoint: follow the pattern in `src/api/handlers/users.ts`\n- New adapter: see `src/adapters/postgres.py` as reference",
            ],
            citations=[
                Citation(
                    source="Red Hat",
                    title="Repository Scaffolding for AI Coding Agents, Section 2.1",
                    url="",
                    relevance="Pattern references turn novel changes into copy-modify changes",
                ),
                Citation(
                    source="Anthropic",
                    title="Claude Code Skills Documentation",
                    url="https://code.claude.com/docs/en/skills",
                    relevance="Skills system for on-demand pattern knowledge",
                ),
            ],
        )


class DesignIntentAssessor(BaseAssessor):
    """Assesses documentation of architectural intent, preconditions, and invariants.

    Tier 3 Important (2% weight) - Agents can discover what code does but not
    why it was designed that way or what invariants must hold.
    """

    @property
    def attribute_id(self) -> str:
        return "design_intent"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Design Intent Documentation",
            category="Agent Patterns & Knowledge",
            tier=self.tier,
            description="Documented preconditions, invariants, and design rationale",
            criteria="Design docs with architectural intent",
            default_weight=0.02,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for design intent documentation."""
        score = 0.0
        evidence = []

        # Check for design/architecture doc directories
        design_dirs = [
            "docs/design",
            "docs/architecture",
            "docs/decisions",
            "docs/adr",
            ".adr",
            "design",
            "architecture",
        ]

        # Intent keywords used for both design dir content validation
        # and keyword search in context files
        intent_keywords = [
            r"precondition",
            r"invariant",
            r"design\s+rationale",
            r"design\s+decision",
            r"why\s+we\s+chose",
            r"architectural\s+constraint",
            r"must\s+hold",
            r"assumes\s+that",
        ]

        for dir_name in design_dirs:
            design_dir = repository.path / dir_name
            if design_dir.exists() and design_dir.is_dir():
                md_files = list(design_dir.glob("*.md"))
                if md_files:
                    # Check if design docs contain intent language
                    has_intent_content = False
                    for md_file in md_files:
                        try:
                            content = md_file.read_text(encoding="utf-8")
                            if any(
                                re.search(kw, content, re.IGNORECASE)
                                for kw in intent_keywords
                            ):
                                has_intent_content = True
                                break
                        except (OSError, UnicodeDecodeError):
                            continue

                    if has_intent_content:
                        score += 50.0
                        evidence.append(
                            f"{dir_name}/ directory with {len(md_files)} design document(s) containing intent language"
                        )
                    else:
                        score += 15.0
                        evidence.append(
                            f"{dir_name}/ directory exists ({len(md_files)} file(s)) but no intent language found"
                        )
                    break

        # Check for design intent keywords in context/doc files
        docs_to_check = ["CLAUDE.md", "AGENTS.md", "README.md"]
        for filename in docs_to_check:
            filepath = repository.path / filename
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for pattern in intent_keywords:
                if re.search(pattern, content, re.IGNORECASE):
                    score = min(score + 30.0, 100.0)
                    evidence.append(f"Design intent language found in {filename}")
                    break

        score = min(score, 100.0)

        if score >= 50:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value="documented",
                threshold="design docs with preconditions/invariants",
                evidence=evidence,
                remediation=None,
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=score,
                measured_value="not documented" if score == 0 else "minimal",
                threshold="design docs with preconditions/invariants",
                evidence=evidence or ["No design intent documentation found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        return Remediation(
            summary="Document design intent: preconditions, invariants, and rationale",
            steps=[
                "Create docs/design/ directory",
                "For each critical module, document preconditions, invariants, and rationale",
                "Use an AI agent to reverse-engineer initial design docs from code, then enrich with intent",
                "Reference design docs from CLAUDE.md/AGENTS.md",
            ],
            tools=[],
            commands=["mkdir -p docs/design"],
            examples=[
                "# docs/design/event-system.md\n## Invariants\n- Event log is append-only; never mutate or delete entries\n- Events are processed exactly-once via idempotency keys\n\n## Preconditions\n- Auth middleware must validate token before event handlers run\n\n## Rationale\n- Polling instead of webhooks: upstream API has 5s delivery SLA, too slow for our use case",
            ],
            citations=[
                Citation(
                    source="Red Hat",
                    title="Repository Scaffolding for AI Coding Agents, Section 2.3",
                    url="",
                    relevance="Agents cannot infer design intent from code alone",
                ),
            ],
        )


class ProgressiveDisclosureAssessor(BaseAssessor):
    """Assesses use of progressive disclosure for large repos.

    Tier 4 Advanced (1% weight) - For repos >50K lines, path-scoped rules
    and skills keep context lean while providing depth where needed.
    Only applicable for larger repositories.
    """

    @property
    def attribute_id(self) -> str:
        return "progressive_disclosure"

    @property
    def tier(self) -> int:
        return 4  # Advanced

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Progressive Disclosure",
            category="Agent Patterns & Knowledge",
            tier=self.tier,
            description="Path-scoped rules and skills for large repos",
            criteria="Component-level context files for repos >50K lines",
            default_weight=0.01,
        )

    LOC_THRESHOLD = 50000

    def is_applicable(self, repository: Repository) -> bool:
        """Only applicable for repos with substantial code."""
        return repository.total_lines > self.LOC_THRESHOLD

    def assess(self, repository: Repository) -> Finding:
        """Check for progressive disclosure patterns."""
        if not self.is_applicable(repository):
            return Finding.not_applicable(
                self.attribute,
                reason=f"Repository has {repository.total_lines} lines (progressive disclosure relevant for >{self.LOC_THRESHOLD})",
            )

        score = 0.0
        evidence = []

        # Check for .claude/rules/ directory with path-scoped rules
        rules_dir = repository.path / ".claude" / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            rule_files = list(rules_dir.glob("*.md"))
            if rule_files:
                # Check for path-scoped frontmatter
                scoped_count = 0
                for rule_file in rule_files:
                    try:
                        content = rule_file.read_text(encoding="utf-8")
                        if "paths:" in content and "---" in content:
                            scoped_count += 1
                    except (OSError, UnicodeDecodeError):
                        pass

                if scoped_count > 0:
                    score += 50.0
                    evidence.append(
                        f".claude/rules/ with {scoped_count} path-scoped rule file(s)"
                    )
                else:
                    score += 20.0
                    evidence.append(
                        f".claude/rules/ with {len(rule_files)} file(s) (no path-scoped frontmatter)"
                    )

        # Check for subdirectory context files
        sub_context_files = list(repository.path.rglob("CLAUDE.md"))
        sub_context_files.extend(list(repository.path.rglob("AGENTS.md")))
        sub_context_count = sum(
            1 for f in sub_context_files if f.parent != repository.path
        )

        if sub_context_count > 0:
            score = min(score + 30.0, 100.0)
            evidence.append(f"{sub_context_count} subdirectory context file(s)")

        # Check for skills directory
        skills_dir = repository.path / ".claude" / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            skill_count = len(list(skills_dir.rglob("SKILL.md")))
            if skill_count > 0:
                score = min(score + 30.0, 100.0)
                evidence.append(
                    f"{skill_count} SKILL.md file(s) for on-demand knowledge"
                )

        # Check root context file size (should be <150 lines)
        for root_file in ["CLAUDE.md", "AGENTS.md"]:
            root_path = repository.path / root_file
            if root_path.exists():
                try:
                    lines = len(root_path.read_text(encoding="utf-8").splitlines())
                    if lines <= 150:
                        score = min(score + 10.0, 100.0)
                        evidence.append(
                            f"Root {root_file} is {lines} lines (good: <150)"
                        )
                    elif lines > 300:
                        evidence.append(
                            f"Root {root_file} is {lines} lines (consider splitting into skills)"
                        )
                except (OSError, UnicodeDecodeError):
                    pass
                break

        score = min(score, 100.0)

        if score >= 40:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value=f"{len(evidence)} disclosure mechanism(s)",
                threshold="path-scoped rules or skills",
                evidence=evidence,
                remediation=None,
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=score,
                measured_value="not configured",
                threshold="path-scoped rules or skills",
                evidence=evidence
                or [
                    f"Large repo ({repository.total_lines} lines) without progressive disclosure"
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        return Remediation(
            summary="Add path-scoped rules and skills for progressive context disclosure",
            steps=[
                "Keep root CLAUDE.md/AGENTS.md under 150 lines as a routing layer",
                "Create .claude/rules/ with path-scoped frontmatter for module-specific rules",
                "Create .claude/skills/ for on-demand knowledge that loads only when relevant",
                "Add subdirectory context files for frequently-changed modules",
            ],
            tools=[],
            commands=[
                "mkdir -p .claude/rules .claude/skills",
            ],
            examples=[
                '# .claude/rules/api-module.md\n---\npaths:\n  - "src/api/**/*.ts"\n---\n\n# API Module Rules\n- All endpoints use middleware chain in src/api/middleware/\n- Request validation uses zod schemas',
            ],
            citations=[
                Citation(
                    source="Red Hat",
                    title="Repository Scaffolding for AI Coding Agents, Sections 3.1 & 4.1",
                    url="",
                    relevance="Progressive disclosure for large repos",
                ),
                Citation(
                    source="Anthropic",
                    title="Claude Code Skills Documentation",
                    url="https://code.claude.com/docs/en/skills",
                    relevance="Skills load on-demand rather than consuming context every session",
                ),
            ],
        )
