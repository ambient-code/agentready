# Automated PR Review System

**Status**: Active
**Last Updated**: 2026-03-03
**Workflow**: `.github/workflows/pr-review.yml`

## Overview

Every pull request in the agentready repository receives an automated code review that:

1. **Reviews PRs automatically** - Multi-agent review on PR open/update
2. **Maps findings to AgentReady attributes** - Links issues to the 25 attributes
3. **Calculates score impact** - Shows how fixing issues improves certification

## Security

The workflow uses `pull_request` trigger (not `pull_request_target`) to prevent prompt injection attacks. See [RHOAIENG-51622](https://issues.redhat.com/browse/RHOAIENG-51622) for details.

**Important**: Fork PRs do not receive automated reviews because they don't have access to repository secrets. This is intentional for security.

### For External Contributors

If you're contributing from a fork:
- Push your branch to the main repository instead (e.g., `username/feature-name`)
- Or request manual review from a maintainer

## Workflow

```
PR Opened/Updated (from main repo branch)
    ↓
┌───────────────────────────────────────┐
│ PR Review                             │
│ (pull_request trigger)                │
│                                       │
│ - Minimize old review comments       │
│ - Run /review-agentready command     │
│ - Post review comment with findings  │
└───────────────────────────────────────┘
    ↓
Developer receives review on their PR
```

## Review Output Format

The automated review posts a comment like this:

```markdown
### 🤖 AgentReady Code Review

**PR Status**: 3 issues found (2 🔴 Critical, 1 🟡 Major, 0 🔵 Minor)
**Score Impact**: Current 80.0/100 → 85.2 if all issues fixed
**Certification**: Gold → Platinum potential

---

#### 🔴 Critical Issues (Confidence ≥90) - Auto-Fix Recommended

##### 1. Missing type annotations in assessor method ✅ Fixed in abc123f
**Attribute**: 2.3 Type Annotations (Tier 2) - [CLAUDE.md section](#)
**Confidence**: 92%
**Score Impact**: −3.8 points
**Location**: src/agentready/assessors/new_assessor.py#L15-L30

**Issue Details**:
The `assess()` method lacks return type annotation, causing mypy errors.

**Remediation**:
```bash
# Automated fix available via:
# (Will be applied automatically if this is a blocker/critical)
python -m mypy src/agentready/assessors/new_assessor.py
black src/agentready/assessors/new_assessor.py
```

---

#### 🟡 Major Issues (Confidence 80-89) - Manual Review Required

##### 2. Potential TOCTOU in file read operation
**Attribute**: 3.1 Security Best Practices (Tier 3)
**Confidence**: 85%
**Score Impact**: −2.5 points
**Location**: src/agentready/services/scanner.py#L45-L52

[Details...]

---

#### Summary

- **Auto-Fix Candidates**: 2 critical issues flagged for automatic resolution
- **Manual Review**: 1 major issue requires human judgment
- **Total Score Improvement Potential**: +6.3 points if all issues addressed
- **AgentReady Assessment**: Run `agentready assess .` after fixes to verify score

---

🤖 Generated with [Claude Code](https://claude.ai/code)
```

## Setup

### Required Secrets

Add these to your GitHub repository secrets (Settings → Secrets → Actions):

1. **`ANTHROPIC_API_KEY`** - Your Anthropic API key
   - Get from: https://console.anthropic.com/settings/keys
   - Required for Claude Code Action

2. **`CLAUDE_CODE_OAUTH_TOKEN`** - Claude Code OAuth token
   - Get from: https://claude.ai/code/settings
   - Required for authentication

### Enable the Workflow

The workflow is enabled by default. To disable:

```bash
# Rename to disable
mv .github/workflows/pr-review.yml .github/workflows/pr-review.yml.disabled

# Re-enable later
mv .github/workflows/pr-review.yml.disabled .github/workflows/pr-review.yml
```

## Testing

### Test on Draft PR

1. **Create a test branch** with intentional issues:
   ```bash
   git checkout -b test/automated-review
   ```

2. **Add code with critical issues**:
   ```python
   # src/agentready/assessors/test_assessor.py
   def assess(repository):  # Missing type hints (critical)
       file = open(repo.path + "/test.txt")  # TOCTOU bug (critical)
       data = file.read()  # No error handling (major)
       return data
   ```

3. **Commit and push**:
   ```bash
   git add src/agentready/assessors/test_assessor.py
   git commit -m "test: add intentional issues for review testing"
   git push origin test/automated-review
   ```

4. **Open draft PR**:
   ```bash
   gh pr create --draft --title "Test: Automated Review" --body "Testing automated review + auto-fix workflow"
   ```

5. **Observe workflow**:
   - Check Actions tab for `PR Review`
   - Review comment should be posted on the PR

6. **Verify fixes**:
   ```bash
   git pull origin test/automated-review
   git log --oneline -5  # Should see auto-fix commits
   ```

7. **Clean up**:
   ```bash
   gh pr close --delete-branch
   ```

## Customization

### Adjust Confidence Threshold

Edit `.github/workflows/pr-review-auto-fix.yml`:

```yaml
# Change from 90 to 95 for more conservative auto-fixing
if: needs.review.outputs.has_criticals == 'true'  # confidence ≥90
# to
if: needs.review.outputs.has_criticals == 'true'  # confidence ≥95
```

Also update `.claude/commands/review-agentready.md`:

```markdown
**Critical Issue Criteria** (confidence ≥95):  # Changed from 90
```

### Add Custom Focus Areas

Edit `.claude/commands/review-agentready.md` under "AgentReady-Specific Focus Areas":

```markdown
**High Priority**:
1. File system race conditions (TOCTOU in scanning logic)
2. Assessment accuracy (false positives/negatives)
3. Your custom concern here
```

### Customize Output Format

Edit `src/agentready/github/review_formatter.py`:

```python
class ReviewFormatter:
    def format_review(self, findings: List[ReviewFinding]) -> str:
        # Customize markdown output here
        ...
```

## Troubleshooting

### Review Not Posting

**Symptom**: Workflow runs but no comment appears on PR

**Solutions**:
1. Check GitHub Actions logs for `PR Review`
2. Verify `ANTHROPIC_API_KEY` is set correctly
3. Ensure `pull-requests: write` permission is granted
4. **Fork PRs**: Reviews only run on PRs from branches in the main repo, not forks

### Auto-Fix Not Running

**Symptom**: Review posts but auto-fix job doesn't run

**Solutions**:
1. Verify review found issues with confidence ≥90
2. Check `.review-results.json` artifact was uploaded
3. Review `needs.review.outputs.has_criticals` value in logs

### Fixes Causing Test Failures

**Symptom**: Auto-fix commits but tests fail

**Solutions**:
1. Check the auto-fix logic in `.github/claude-bot-prompt.md`
2. Verify linters run before tests: `black . && isort . && pytest`
3. Consider lowering confidence threshold (fixes might be too aggressive)

### Rate Limiting

**Symptom**: Workflow fails with "rate limit exceeded"

**Solutions**:
1. Reduce number of parallel agents in `/review-agentready` command
2. Add caching for review results (reduce redundant API calls)
3. Implement exponential backoff in workflow

## Architecture

### Multi-Agent Review System

The `/review-agentready` command launches 5 parallel Sonnet agents:

1. **CLAUDE.md Compliance Audit** - Checks development workflow adherence
2. **AgentReady Bug Scan** - Finds TOCTOU, AST parsing, measurement accuracy issues
3. **Historical Context Analysis** - Reviews git blame for regression detection
4. **Previous PR Comment Analysis** - Identifies recurring issues
5. **Code Comment Compliance** - Ensures inline guidance is followed

Each agent's findings are scored 0-100 by parallel Haiku agents (confidence scoring).

### Attribute Mapping

The `ReviewFormatter` maps findings to AgentReady's 25 attributes using keyword analysis:

```python
keyword_map = {
    "type annotation": "2.3",
    "type hint": "2.3",
    "test coverage": "2.8",
    "claude.md": "1.1",
    ...
}
```

### Score Impact Calculation

Score impact uses tier-based weighting:

- Tier 1 (Essential): 50% of total score
- Tier 2 (Critical): 30% of total score
- Tier 3 (Important): 15% of total score
- Tier 4 (Advanced): 5% of total score

Formula: `impact = (tier_weight / num_attrs_in_tier) × 100`

## Integration with Existing Workflows

### Works With

- **Dependabot PRs**: Reviews but skips auto-fix (too risky for dependency updates)
- **GitHub Flow**: Respects feature branch workflow, never pushes to main
- **Conventional Commits**: Auto-fix commits follow the same pattern
- **Pre-commit Hooks**: Auto-fix runs linters same as local development

### Complements

- **CI/CD**: Reviews focus on logic/security; CI checks build/tests/types
- **Manual @claude mentions**: Users can still trigger custom reviews with @claude
- **Code review by humans**: Automated review doesn't replace human judgment

## Future Enhancements

See `BACKLOG.md` for planned features:

- [ ] Historical trend analysis (track score improvement over time)
- [ ] Custom severity thresholds per attribute
- [ ] Integration with AgentReady badges (update on PR merge)
- [ ] Batch review mode (review multiple PRs in org)

## Related Documentation

- **CLAUDE.md** - Project development standards
- **.github/CLAUDE_INTEGRATION.md** - Dual Claude integration guide
- **.github/claude-bot-prompt.md** - Automation-specific instructions
- **src/agentready/github/review_formatter.py** - Review output formatter
- **.claude/commands/review-agentready.md** - Custom slash command

---

**Maintained by**: Jeremy Eder
**Questions?**: Create issue with `automation` label
