# Align AgentReady with wg-agentic-sdlc Best Practices

| | |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-05-20 |
| **Author** | Bill Murdock (with assistance from Claude Code) |

## Context

The wg-agentic-sdlc working group (Red Hat Global Engineering's agentic SDLC
community of practice) maintains a [best practices guide](https://gitlab.cee.redhat.com/global-engineering/wg-agentic-sdlc/-/tree/main/best-practices)
(Red Hat internal, requires VPN access) covering repository scaffolding for
AI coding agents, AI tool effective habits, multi-agent workflows, threat
modeling, security baselines, and more. AgentReady assesses repositories against 33 attributes
(post-[PR #382](https://github.com/ambient-code/agentready/pull/382)) across 4 tiers. This ADR documents a systematic cross-reference
between the two, identifies gaps in both directions, and proposes alignment
actions.

[PR #382](https://github.com/ambient-code/agentready/pull/382) (v2.0.0 rebalancing) added 4 new assessors and reweighted attributes
based on 2025-2026 research evidence, closing several previously identified
gaps. This ADR captures what remains.

A separate cross-reference was performed against
[etirelli/ai-scaffolding](https://github.com/etirelli/ai-scaffolding), which
implements the same best practices as a Claude Code skill (`.claude/skills/
repo.check/SKILL.md`). That skill checks 14 practices across 4 tiers using
PASS/WARN/FAIL scoring. Comparing its approach against AgentReady's
programmatic assessors surfaced additional scoring philosophy differences
documented in Part 3 below.

## Gap Analysis

### Part 1: In the Best Practices but Missing or Incomplete in AgentReady

#### High-impact gaps

| # | Best Practice | BP Tier | AgentReady Status | Feasibility | Gap Detail |
|---|---|---|---|---|---|
| 1 | **Context file length validation** | T1 | Partial | Feasible using rules. Count lines. | CLAUDEmdAssessor checks existence/sections but does NOT check length. ProgressiveDisclosureAssessor checks root <150 lines, but only for repos >50K LOC. The BP says <150 lines recommended, hard cap 300, for ALL repos. |
| 2 | **Auto-generated context file detection** | T1 | Missing | Not feasible. Length (gap #1) is the best available proxy. | ETH Zurich research (cited in [PR #382](https://github.com/ambient-code/agentready/pull/382)) shows auto-gen hurts -3% and costs +20-23%. No assessor flags auto-generation markers. However, reliable detection is not practical: a well-prompted LLM produces output indistinguishable from human-written files. Neither the etirelli skill nor the BP document attempt detection. Context file length validation (gap #1) is the best available proxy, since the harm from auto-generated files comes primarily from excessive length and noise. |
| 3 | **Continuous improvement loop** | T3 | Missing | Not feasible. Team process with no reliable repo artifact. | The BP recommends treating every code review comment on an AI-generated PR as a signal about what context files are missing: add rules to AGENTS.md or lint configs, track common agent failure modes and fix root causes, and periodically audit context files to remove lines that no longer prevent real failures. Addy Osmani frames it as "treat AGENTS.md as a living list of codebase smells you haven't fixed yet." This is fundamentally a team process, not a repo artifact. Possible proxies (e.g., checking whether CLAUDE.md has been updated recently, or whether commits touch context files alongside code) are weak signals: a team could update context files regularly for bad reasons, or rarely because they're already good. The etirelli skill also excludes this as "cannot be automated." Note that running `agentready assess` periodically is itself a form of continuous improvement feedback, so AgentReady contributes to this loop indirectly even without a dedicated assessor. |
| 4 | **Architectural boundary lint rules** | T3 | Missing | Feasible using rules. Check linter configs for specific rule names. | The BP recommends enforcing module boundaries via lint rules: ESLint `no-restricted-imports`, Go `depguard`/`gomodguard`, Python `import-linter`, or `dependency-cruiser`. The Factory.ai insight is "agents write code; linters write the law." Without boundary enforcement, agents freely import across module boundaries and create coupling that humans would catch in review. This is distinct from cyclomatic complexity or separation of concerns, which measure code structure rather than enforcing architectural contracts. AgentReady mentions architectural boundaries in remediation text but does not assess whether boundary lint rules are configured. The etirelli skill includes this as check 3.3 with an N/A threshold for small repos (<20 files). This is practically assessable by checking linter configs for import restriction rules. |
| 5 | **Module-level test filtering** | T1 detail | Missing | Partially feasible using rules. Can check for pytest markers, separate directories, Makefile targets, and context file keywords. Heuristics are language-specific and incomplete. | The BP emphasizes that agents need fast, targeted test feedback, not just a full test suite. This means separating unit tests (agent-runnable, no external dependencies) from integration tests (infrastructure-dependent), and providing module-level filtering (e.g., `make test-unit PACKAGE=auth`). When an agent changes one module, running the full suite wastes time and produces noisy failures from unrelated code. TestExecutionAssessor checks that a runner exists and test files are present, but not whether tests are organized for selective execution. An additional signal is whether CLAUDE.md or AGENTS.md documents module-level or single-file test commands; keyword matching against context files can serve as substantiating evidence, though not as a hard gate (a repo may have good test filtering without documenting it). AI-powered semantic analysis of context files could improve accuracy but should be addressed in a separate ADR. |
| 6 | **Readable CI output** | T1 detail | Missing | Feasible using AI, but would require triggering a CI run and analyzing the output. Not assessable from a repo snapshot alone. | The BP says CI failure messages should point to specific problems, not be buried in build logs. This matters for agents because they parse CI output to self-correct. However, CI output quality depends on the specific run, not the static config. The best proxy from a repo snapshot would be checking for CI config features like descriptive step names, explicit error formatting, or annotation commands (`::error`), but these are weak signals. |
| 7 | **Threat model documentation** | BP security | Missing | Feasible using rules for file existence and section structure. AI could assess whether the content is meaningful. | The BP defines a structured THREAT_MODEL.md with 8 sections: system context, assets (with sensitivity levels), entry points and trust boundaries, threats (with actor/impact/likelihood/status/controls), deprioritized threats with rationale, open questions, provenance, and recommended mitigations. The structured format enables AI agents to perform focused security scanning: entry points tell the agent where attacker-controlled input enters, threats tell it what to look for, and deprioritized items tell it what to suppress. Without this, agents either skip security analysis or do unfocused whole-repo scanning. The question is whether this belongs in AgentReady's scope (repo readiness for AI development) or is better suited to a security-focused tool. |
| 8 | **Multi-agent workflow support** | T4 | Missing | Not feasible. No standardized repo artifacts; configuration lives in orchestration layers outside the repo. | The BP describes patterns like git worktrees for parallel agent isolation (multiple agents working on the same repo without merge conflicts), writer/reviewer patterns (one agent implements, another reviews), and plan/execute patterns (stronger model plans, faster model executes). ProgressiveDisclosureAssessor is adjacent (path-scoped rules help multi-agent coordination) but does not check for worktree setup or workflow definitions. The etirelli skill excludes this as "cannot be automated." The challenge is that multi-agent workflows are configured in the orchestration layer (CI, scripts, team config), not in standardized repo artifacts. A lightweight check could look for documented multi-agent patterns in context files or `.claude/settings.json` team config, but this is a weak signal since most teams doing multi-agent work configure it outside the repo. |
| 9 | **Repository access documentation** | BP access | Missing | Partially feasible using rules to detect access-related sections in context files. AI could evaluate completeness. | The BP recommends adding a machine-readable `## Agent Access` section to context files that documents: which platform hosts the repo (GitHub, GitLab, internal GitLab), which CLI tool to use (`gh`, `glab`), authentication requirements, and example commands. This prevents agents from trying the wrong tool (e.g., using `gh` against an internal GitLab instance, or `WebFetch` against a private repo that requires authenticated API access). Most relevant for organizations with mixed hosting platforms. |
| 10 | **Skill overlays depth** | T4 | Partial | Mostly feasible using rules (count skills, check frontmatter for path-scoping). AI could assess content quality. | PatternReferencesAssessor checks for `.claude/skills/` presence. The BP goes deeper: skills should use `context: fork` for isolated subagent execution, be path-scoped to load only when relevant files are touched, and cover specific workflows (build-test-verify, git-commit, create-pull-request, add-api-endpoint, deploy). The etirelli skill requires 3+ skills for PASS and correlates skill count with context file size (>150 lines without skills = FAIL). AgentReady could improve by checking skill count, path-scoping in skill frontmatter, and the context-size correlation. |
| 11 | **Design doc enforcement on architectural changes** | T2 detail | Missing | Partially feasible using rules (check hooks or AGENTS.md for enforcement references). Cannot verify the enforcement is effective. | DesignIntentAssessor checks that design docs exist (design/ or docs/design/ directories with intent-related keywords). The BP goes further: teams should enforce that architectural changes include corresponding design doc updates. This could be implemented as a hook that checks whether changed files have corresponding design docs, a skill that validates design doc currency as part of PR workflow, or an AGENTS.md rule requiring design doc review with architectural changes. |

#### Lower-impact or scope-boundary gaps

| # | Best Practice | Why It May Be Out of Scope |
|---|---|---|
| 12 | AI tool effective habits (model selection, compaction, subagents) | User behavior, not repo properties. AgentReady assesses repos. |
| 13 | IBM AI Security Baseline | Organizational standard, not repo-level check. |
| 14 | CISA agentic AI guidance | Regulatory guidance, not repo assessment. |
| 15 | AEM integration patterns | Domain-specific (Adobe content management). |
| 16 | Multi-agent blind testing harness | Process/workflow pattern, not a repo property. |
| 17 | Skill overlay generation (dynamic vs static) | Infrastructure decision, not assessable from repo. |

### Part 2: In AgentReady but NOT in the Best Practices

AgentReady assesses several attributes that the BP does not mention. For
each, we recommend either keeping it in AgentReady and adding it to the BP,
or dropping it from AgentReady.

| # | AgentReady Assessor | Tier/Weight | Analysis | Disposition |
|---|---|---|---|---|
| 1 | **DependencyPinningAssessor** | T1/5% | Reproducible builds are critical for agents. Non-deterministic dependency resolution causes "works on my machine" failures that are especially hard for agents to diagnose since they cannot interactively explore environment differences. Lock files are a concrete, universally applicable practice. | Keep and add to BP. Fits naturally under a dependency management section. |
| 2 | **DependencySecurityAssessor** | T1/5% | Agents generate code that pulls dependencies. Without scanning, agents can introduce supply chain vulnerabilities. The BP already has IBM/CISA security sections; dependency scanning is a concrete, assessable practice that complements those. | Keep and add to BP. Fits alongside the existing security content. |
| 3 | **ConventionalCommitsAssessor** | T2/3% | Agents need to know commit conventions to avoid style violations that trigger CI failures or reviewer pushback. However, this is really a specific case of deterministic enforcement (already in BP) applied to commit messages. The agent-specific value is real but narrow. | Keep and add to BP, folded into the existing "deterministic enforcement" section rather than standing alone. |
| 4 | **GitignoreAssessor** | T2/3% | Agents create files prolifically. Without a comprehensive .gitignore, agents commit build artifacts, IDE files, and potentially secrets. The risk is concrete and somewhat agent-specific: agents are less likely than humans to notice they're staging files that shouldn't be committed. | Keep and add to BP. A brief mention under "file organization" would suffice. |
| 5 | **FileSizeLimitsAssessor** | T2/3% | Large source files exceed what agents can hold in context, leading to incomplete understanding and errors. The BP covers context file length but not source file length. The agent-specific impact is direct: agents hit context window limits that humans do not. | Keep and add to BP. Could be mentioned under "file organization" since the BP already discusses that topic. |
| 6 | **READMEAssessor** | T1/5% | Most agents read the README before or alongside AGENTS.md. A poor or missing README means agents start with incomplete project understanding. The BP focuses on AGENTS.md/CLAUDE.md as the primary context source but does not acknowledge README's role. | Keep and add to BP as a supplementary context source. The BP should note that agents read READMEs and that README quality contributes to agent orientation. |
| 7 | **InlineDocumentationAssessor** | T2/3% | Docstrings help agents understand function intent without reading full implementations, which saves context window space and reduces misinterpretation. Complements type annotations (already in BP): types tell agents what a function accepts and returns, docstrings tell agents what it does and when to use it. | Keep and add to BP as a complement to the existing type annotations section. |
| 8 | **ArchitectureDecisionsAssessor** | T3/3% | ADRs provide a structured, discoverable format for the design rationale that the BP's design intent section recommends capturing. The BP covers design intent but does not mention ADRs as a format. ADRs are particularly agent-friendly because they follow a predictable structure (Context, Decision, Consequences) that agents can parse reliably. | Keep and add to BP. Mention under design intent as one recommended format for capturing rationale. |
| 9 | **StructuredLoggingAssessor** | T3/2% | Agents debugging runtime issues benefit from parseable, structured logs over free-text logs. JSON logs are greppable and filterable, which helps agents diagnose problems faster. Agents are more dependent on machine-readable output than humans, who can visually scan unstructured logs. | Keep and add to BP. Could be mentioned under a "machine-readable output" principle alongside the existing machine-readable API surfaces section. |
| 10 | **RepomixConfigAssessor** | T3/2% | Repomix generates AI-friendly repo context files, which is directly agent-relevant. However, it is one specific tool among several (e.g., `aider --map`), and checking for a single vendor's config file is not a universal practice. No other assessor is this vendor-specific. | Drop from AgentReady. If AI context generation tooling becomes standardized, consider a generalized assessor, but a single-vendor config check does not belong in a universal assessment framework. |
| 11 | **CyclomaticComplexityAssessor** | T3/2% | High-complexity functions are harder for agents to understand, modify, and test correctly. Agents cannot "step through" complex logic the way a human debugger can, so high complexity has an outsized impact on agent error rates. Overlaps with SeparationOfConcernsAssessor and FileSizeLimitsAssessor but measures a distinct property (control flow complexity). | Keep and add to BP. Could be mentioned under code organization alongside file size and separation of concerns. |
| 12 | **CodeSmellsAssessor** | T4/1% | Checks for long methods, large classes, unused variables. However, this significantly overlaps with CyclomaticComplexityAssessor (long methods), FileSizeLimitsAssessor (large files), and SeparationOfConcernsAssessor (god objects). The incremental value over those three assessors is minimal. | Drop from AgentReady or consolidate into the overlapping assessors. The specific smells it checks for are already covered by more targeted assessors. |
| 13 | **ContainerSetupAssessor** | T4/1% | Containers provide reproducible, isolated environments that agents can spin up and test in. Agents benefit more from reproducible environments than humans do, since agents cannot manually work around environment inconsistencies. Already conditional (returns N/A if no container files found), so it does not penalize projects where containers are irrelevant. | Keep and add to BP with a note that this is conditional. The BP covers reproducible environments via dependency pinning and one-command setup; containers are another implementation of the same principle. Applicable only to projects that use containers. |
| 14 | **BranchProtectionAssessor** | T4/0.5% | Branch protection prevents agents from pushing directly to main, which is a safety guardrail. However, this is currently a stub that returns not_applicable pending GitHub API integration. A perpetual stub adds no value. | Drop from AgentReady in its current state. If implemented, reconsider: a safety guardrail assessor has merit in principle, and the BP's deterministic enforcement section could include branch protection as an example. |
| 15 | **IssuePRTemplatesAssessor** | T4/1% | Agents create PRs and issues frequently. Templates give agents structure to follow, reducing the chance of missing required information (test plans, acceptance criteria, reviewer checklists). Agents follow templates more literally than humans, so templates are more effective as agent guardrails than as human guardrails. | Keep and add to BP. Templates function as lightweight deterministic enforcement for PR/issue creation, which fits naturally under the existing enforcement section. |
| 16 | **ConciseDocumentationAssessor** | T2/3% | Documentation density matters for agents consuming docs within context windows. Verbose, redundant documentation wastes tokens and dilutes signal. However, this significantly overlaps with context file length validation (gap #1) and FileSizeLimitsAssessor. The distinct contribution is measuring information density, not just length, but "information density" is a subjective judgment that is difficult to assess programmatically with rules. | Drop from AgentReady. The concern is already covered by context file length validation and FileSizeLimitsAssessor. Measuring information density (as opposed to length) requires subjective judgment that does not lend itself to reliable programmatic assessment. |

### Part 3: Insights from etirelli/ai-scaffolding Skill

The [etirelli/ai-scaffolding](https://github.com/etirelli/ai-scaffolding)
repo implements the same BP document as a Claude Code skill with 14 checks.
Comparing its approach against AgentReady's programmatic assessors reveals
several scoring philosophy differences and additional gaps not captured in
Parts 1-2.

#### Scoring philosophy differences

| Area | etirelli Skill | AgentReady | Implication |
|---|---|---|---|
| **Hook prioritization** | WARN for pre-commit hooks without agent-specific hooks. Agent hooks (`.claude/settings.json`) required for PASS. | DeterministicEnforcementAssessor scores pre-commit at 60 pts, `.claude/settings.json` at 30 pts. | AgentReady has this inverted. The BP insight is "context file instructions are advisory; hooks are deterministic," and agent-specific hooks matter more than git hooks for agent workflows. |
| **Type checking** | Checks whether strict mode is *enabled* in config (`strict: true` in tsconfig, `disallow_untyped_defs` in mypy). | TypeAnnotationsAssessor checks *coverage percentage* of annotations in function signatures. | These are complementary: strict mode prevents new violations, coverage measures current state. AgentReady could add strict mode detection. |
| **Skills depth** | Requires 3+ skills with SKILL.md for PASS. Correlates with context file size (>150 lines without skills = FAIL). | PatternReferencesAssessor checks for presence of `.claude/skills/` but not a minimum count or correlation with context file length. | AgentReady should consider a minimum skill count and the context-size correlation. |
| **Test command documentation** | Verifies test command is documented in CLAUDE.md/AGENTS.md/README, not just that a test runner config exists. | TestExecutionAssessor checks for runner config and test files but not documentation of the command. | Agents need to *find* the command, not just have one available. |

#### Additional gaps surfaced

| # | Finding | Detail |
|---|---|---|
| 1 | **Consistent naming patterns** | Skill check 2.5 looks for mixed naming conventions in the same directory (camelCase and snake_case coexisting). AgentReady's StandardLayoutAssessor checks directory structure but not naming consistency. Inconsistent naming reduces "glob-ability" for agents. |
| 2 | **Non-automatable practices acknowledged** | The skill explicitly excludes continuous improvement loop (3.4) and multi-agent workflows (4.2) as "cannot be automated." This confirms that AgentReady should consider marking these as known assessment limitations rather than planning assessors for them. |

### Tier disagreements

| Attribute | Best Practices Tier | AgentReady Tier | Notes |
|---|---|---|---|
| Component-level context files | T3 | T4 | BP considers this important for large repos at scale. AgentReady treats it as advanced. |
| Design intent | T2 | T3 | BP emphasizes "do this month" urgency. AgentReady places it lower. |

## Proposals

### Proposal A: Enhance Existing AgentReady Assessors

Items marked *(etirelli)* were identified by cross-referencing the
ai-scaffolding skill.

1. **CLAUDEmdAssessor: Add length validation.** Check context file line count
   for all repos. Recommend <150 lines, warn at >300. Currently only
   ProgressiveDisclosureAssessor checks this and only for repos >50K LOC.

2. **TestExecutionAssessor: Check test organization and documentation.**
   Look for evidence of unit/integration test separation (separate directories,
   markers like `@pytest.mark.integration`, test filtering in Makefile/scripts).
   Also scan CLAUDE.md/AGENTS.md for keywords indicating module-level or
   single-file test commands (e.g., `pytest path/`, `go test ./pkg/`,
   `--testPathPattern`). Context file mentions serve as substantiating evidence,
   not a hard gate. *(etirelli: context file keywords as evidence.)* Note:
   heuristics are language-specific and incomplete. AI-powered semantic analysis
   of context files could improve accuracy but is out of scope here and should
   be addressed in a separate ADR.

3. **TestExecutionAssessor: Check test command documentation.** *(etirelli)*
   Verify that the test command is documented in CLAUDE.md/AGENTS.md/README,
   not just that a runner config exists. Agents need to *find* the command.

4. **PatternReferencesAssessor: Check skill depth.** *(etirelli)* Beyond
   presence of `.claude/skills/`, require a minimum count (3+) for full credit
   and correlate with context file length (>150 lines without skills should
   warn).

5. **DeterministicEnforcementAssessor: Reprioritize hook scoring.** *(etirelli)*
   Currently scores pre-commit at 60 pts and `.claude/settings.json` hooks at
   30 pts. The BP and the etirelli skill both prioritize agent-specific hooks
   over traditional git hooks. Consider inverting or at least equalizing: agent
   hooks should score higher because they are deterministic for agent workflows,
   while pre-commit hooks only fire on git commit.

6. **TypeAnnotationsAssessor: Add strict mode detection.** *(etirelli)* In
   addition to measuring annotation coverage, check whether the type checker
   is configured in strict mode (`strict: true` in tsconfig,
   `disallow_untyped_defs` in mypy). Strict mode prevents new violations;
   coverage measures current state. Both matter.

7. **StandardLayoutAssessor: Check naming consistency.** *(etirelli)* Look
   for mixed naming conventions in the same directory (camelCase vs snake_case
   files coexisting). Inconsistent naming reduces "glob-ability" for agents.

8. **DesignIntentAssessor: Check for enforcement.** Look for hooks or lint
   rules that require design doc updates alongside architectural changes.

9. **CLAUDEmdAssessor: Check for repository access documentation.** Scan
   context files for an agent access section documenting platform, CLI tool,
   and authentication requirements. Most relevant for organizations with
   mixed hosting platforms (e.g., GitHub and internal GitLab).

### Proposal B: New AgentReady Assessors

New attributes for the assessment framework.

1. **ArchitecturalBoundaryAssessor (T3, 2%).** Check for import restriction
   configs: ESLint `no-restricted-imports`, Go `depguard`, Python
   `import-linter`, or similar. The BP principle is "agents write code; linters
   write the law" (Factory.ai). Feasible using rules.

2. **ThreatModelAssessor (T3 or T4, 1-2%).** Check for THREAT_MODEL.md or
   equivalent with structured sections (assets, entry points, threats). The BP
   provides a detailed 8-section schema. Could start with existence check and
   basic structure validation. Feasible using rules for structure; AI could
   assess content quality.

### Proposal C: Remove AgentReady Assessors

Based on the Part 2 analysis, these assessors should be removed or
consolidated.

1. **RepomixConfigAssessor (T3, 2%).** Remove. Single-vendor config check
   does not belong in a universal assessment framework.

2. **CodeSmellsAssessor (T4, 1%).** Remove or consolidate. The specific
   smells it checks for are already covered by CyclomaticComplexityAssessor,
   FileSizeLimitsAssessor, and SeparationOfConcernsAssessor.

3. **BranchProtectionAssessor (T4, 0.5%).** Remove. Currently a stub that
   returns not_applicable. If implemented in the future, reconsider.

4. **ConciseDocumentationAssessor (T2, 3%).** Remove. Redundant with context
   file length validation and FileSizeLimitsAssessor. Measuring information
   density (as opposed to length) requires subjective judgment that does not
   lend itself to reliable programmatic assessment.

### Proposal D: Recommendations for the Best Practices Document

Suggestions to bring back to the wg-agentic-sdlc working group, derived
from AgentReady attributes the BP does not cover.

1. **Add dependency management section.** Dependency pinning (lock files) and
   dependency security scanning are directly relevant to agent workflows.
   Agents pull dependencies when scaffolding projects and need reproducible,
   secure environments.

2. **Add .gitignore guidance under file organization.** Agents create files
   prolifically. A comprehensive .gitignore prevents agents from committing
   build artifacts, IDE files, and secrets.

3. **Add README as supplementary context source.** The BP focuses on
   AGENTS.md/CLAUDE.md. Agents also read READMEs for orientation and README
   quality contributes to agent effectiveness.

4. **Add conventional commits under deterministic enforcement.** Commit
   conventions enforced via commitlint or pre-commit hooks are a specific
   case of deterministic enforcement already covered by the BP.

5. **Add ADRs under design intent.** Architecture Decision Records provide a
   structured, agent-friendly format (Context, Decision, Consequences) for
   capturing the design rationale the BP already recommends documenting.

6. **Add inline documentation as complement to type annotations.** Types
   tell agents what a function accepts and returns; docstrings tell agents
   what it does and when to use it. Both contribute to agent understanding.

7. **Add file size limits under file organization.** The BP covers context
   file length but not source file length. Large source files exceed agent
   context windows.

8. **Add structured logging under machine-readable output.** Agents
   debugging runtime issues benefit from parseable, structured logs. Fits
   alongside the existing machine-readable API surfaces section.

9. **Add cyclomatic complexity under code organization.** High-complexity
   functions have outsized impact on agent error rates because agents cannot
   use debuggers or step through complex control flow interactively.

10. **Add container setup as conditional practice under reproducible
    environments.** For projects that use containers, container quality
    directly affects whether agents can spin up and test in clean
    environments. Applicable only when container files are present.

11. **Add issue/PR templates under deterministic enforcement.** Agents
    create PRs and issues frequently. Templates function as lightweight
    structure that agents follow more literally than humans.

### Proposal E: Tier Realignment

Review the tier placement of two attributes where AgentReady and the best
practices disagree.

1. **Progressive disclosure (component-level context):** Currently T4 in
   AgentReady, T3 in BP. Consider elevating to T3 given that large repos are
   where agent readiness matters most.

2. **Design intent:** Currently T3 in AgentReady, T2 in BP. Consider
   elevating to T2 given the BP emphasis on "do this month" urgency and the
   fundamental challenge that agents can discover what code does but not why
   it was designed that way.

### Known assessment limitations

These BP practices appear as gaps in Part 1 but cannot be assessed from a
repo snapshot. Document them as limitations, not gaps to close.

1. **Auto-generated context file detection (Part 1, gap #2).** Reliable
   detection is not practical since well-prompted LLMs produce output
   indistinguishable from human-written files. Context file length validation
   (Proposal A.1) is the best available proxy.

2. **Continuous improvement loop (Part 1, gap #3).** This is a team process,
   not a repo artifact. Running `agentready assess` periodically contributes
   to this loop indirectly. Both AgentReady and the etirelli skill exclude
   this.

3. **Readable CI output (Part 1, gap #6).** CI output quality depends on
   actual runs, not static config. Would require triggering a CI run and
   applying AI to analyze the output.

4. **Multi-agent workflow support (Part 1, gap #8).** No standardized repo
   artifacts exist for multi-agent workflows; configuration lives in
   orchestration layers outside the repo. Both AgentReady and the etirelli
   skill exclude this.

## Decision

Pending review and discussion.

## Consequences

If adopted:

- Context file length validation would apply to all repos, not just large ones
- Two new assessors (architectural boundaries, threat models) would fill
  the most significant coverage gaps
- Four redundant, vendor-specific, or unimplemented assessors would be
  removed, freeing 6.5% of weight for rebalancing
- 11 recommendations (covering 12 AgentReady attributes, with dependency
  pinning and security combined) would go to the wg-agentic-sdlc working
  group
- Weight rebalancing would be required (total must equal 100%)
