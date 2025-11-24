---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(git:*), Bash(python:*)
description: AgentReady-specific code review with attribute mapping and score impact analysis
disable-model-invocation: false
---

Provide an AgentReady-specific code review for the given pull request.

This command extends the standard `/code-review` with agentready project-specific concerns:
- Map findings to the 25 agentready attributes (from agent-ready-codebase-attributes.md)
- Calculate impact on self-assessment score (current: 80.0/100 Gold)
- Generate remediation commands (agentready bootstrap, black, pytest, etc.)
- Link to relevant CLAUDE.md sections
- Categorize by severity with confidence scoring

## Process

Follow these steps precisely:

1. **Eligibility Check** (Haiku agent)
   - Check if PR is closed, draft, or already reviewed
   - Skip if automated PR (dependabot, renovate) unless it touches assessors
   - If ineligible, exit early

2. **Context Gathering** (Haiku agent)
   - List all CLAUDE.md files (root + modified directories)
   - Get full PR diff and metadata
   - Return concise summary of changes

3. **Parallel AgentReady-Focused Review** (5 Sonnet agents)
   Launch 5 parallel agents to independently review:

   **Agent #1: CLAUDE.md Compliance Audit**
   - Check adherence to CLAUDE.md development workflows
   - Verify pre-push linting (black, isort, ruff)
   - Verify test requirements (pytest, >80% coverage)
   - Check branch verification, conventional commits

   **Agent #2: AgentReady-Specific Bug Scan**
   Focus on agentready assessment logic:
   - TOCTOU bugs in file system operations
   - AST parsing correctness (false positives/negatives in assessors)
   - Measurement accuracy issues
   - Type annotation correctness
   - Error handling patterns (try-except, graceful degradation)

   **Agent #3: Historical Context Analysis**
   - Read git blame for modified assessor files
   - Check for regression in assessment accuracy
   - Verify attribute scoring logic hasn't changed unintentionally

   **Agent #4: Previous PR Comment Analysis**
   - Review comments on past PRs touching same files
   - Check for recurring issues

   **Agent #5: Code Comment Compliance**
   - Verify changes follow inline comment guidance

4. **Attribute Mapping** (Haiku agent for each issue)
   For each issue found:
   - Map to specific agentready attribute ID (e.g., "2.3 Type Annotations")
   - Determine tier (1=Essential, 2=Critical, 3=Important, 4=Advanced)
   - Calculate score impact using tier weights (Tier 1: 50%, Tier 2: 30%, etc.)
   - Generate remediation command (black, pytest, agentready bootstrap --fix)
   - Link to CLAUDE.md section

5. **Confidence Scoring** (parallel Haiku agents)
   For each issue, score 0-100 confidence:
   - 0: False positive
   - 25: Might be real, unverified
   - 50: Verified but minor
   - 75: Very likely real, important
   - 90: Critical issue (auto-fix candidate)
   - 100: Blocker (definitely auto-fix)

   **Critical Issue Criteria** (confidence ≥90):
   - Security vulnerabilities (path traversal, injection)
   - TOCTOU race conditions
   - Assessment accuracy bugs (false positives/negatives)
   - Type safety violations causing runtime errors
   - Missing error handling leading to crashes

6. **Filter Issues**
   - Keep issues with confidence ≥80 for reporting
   - Flag issues with confidence ≥90 as "auto-fix candidates"
   - Calculate aggregate score impact

7. **Final Eligibility Check** (Haiku agent)
   - Verify PR is still eligible for review
   - Check if PR was updated during review

8. **Post Review Comment** (using gh pr comment)
   Use the custom AgentReady format (see below)

## AgentReady Review Output Format

Use this format precisely:

---

### 🤖 AgentReady Code Review

**PR Status**: [X issues found] ([Y 🔴 Critical], [Z 🟡 Major], [W 🔵 Minor])
**Score Impact**: Current 80.0/100 → [calculated score] if all issues fixed
**Certification**: Gold → [Platinum/Gold/Silver/Bronze] potential

---

#### 🔴 Critical Issues (Confidence ≥90) - Auto-Fix Recommended

##### 1. [Brief description]
**Attribute**: [ID Name] (Tier [N]) - [Link to CLAUDE.md section]
**Confidence**: [90-100]%
**Score Impact**: [−X.X points]
**Location**: [GitHub permalink with full SHA]

**Issue Details**:
[Concise explanation with code snippet if relevant]

**Remediation**:
```bash
# Automated fix available via:
# (Will be applied automatically if this is a blocker/critical)
[specific command: black file.py, pytest tests/test_foo.py, etc.]
```

---

#### 🟡 Major Issues (Confidence 80-89) - Manual Review Required

##### 2. [Brief description]
**Attribute**: [ID Name] (Tier [N])
**Confidence**: [80-89]%
**Score Impact**: [−X.X points]
**Location**: [GitHub permalink]

[Details and remediation as above]

---

#### Summary

- **Auto-Fix Candidates**: [N critical issues] flagged for automatic resolution
- **Manual Review**: [M major issues] require human judgment
- **Total Score Improvement Potential**: +[X.X points] if all issues addressed
- **AgentReady Assessment**: Run `agentready assess .` after fixes to verify score

---

🤖 Generated with [Claude Code](https://claude.ai/code)

<sub>- If this review was useful, react with 👍. Otherwise, react with 👎.</sub>

---

## False Positive Examples

Avoid flagging:
- Pre-existing issues (not in PR diff)
- Intentional functionality changes
- Issues caught by CI (linters, tests, type checkers)
- Pedantic style issues not in CLAUDE.md
- General code quality unless explicitly in CLAUDE.md
- Issues with lint-ignore comments
- Code on unmodified lines

## AgentReady-Specific Focus Areas

**High Priority**:
1. File system race conditions (TOCTOU in scanning logic)
2. Assessment accuracy (false positives/negatives)
3. Type annotations (Python 3.11+ compatibility)
4. Error handling (graceful degradation)
5. Test coverage (>80% for new code)

**Medium Priority**:
6. CLAUDE.md workflow compliance
7. Conventional commit format
8. Documentation updates (docstrings, CLAUDE.md)

**Low Priority**:
9. Performance optimization
10. Code organization/structure

## Notes

- Use `gh` CLI for all GitHub operations
- Always link to code with full SHA (not `HEAD` or branch names)
- Link format: `https://github.com/owner/repo/blob/[full-sha]/path#L[start]-L[end]`
- Provide ≥1 line context before/after issue location
- Make todo list first
- Calculate score impact using tier-based weighting from agentready scoring algorithm
