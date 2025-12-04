# Triggering CI from Claude Code

**Quick Reference**: How to manually trigger GitHub Actions workflows from Claude Code

---

## Quick Start

```bash
# Trigger test workflow (runs linters + pytest with 90% coverage)
gh workflow run tests.yml

# Trigger specific workflow and watch it
gh workflow run tests.yml && gh run watch

# View recent workflow runs
gh run list --workflow=tests.yml --limit 5

# View logs of most recent run
gh run view --log

# Cancel a running workflow
gh run cancel <run-id>
```

---

## Available Workflows

### 1. Tests (tests.yml) ⭐ **Main CI Workflow**
**Purpose**: Runs linters (black, isort, ruff) and pytest with 90% coverage threshold

```bash
# Trigger tests
gh workflow run tests.yml

# Watch the run in real-time
gh workflow run tests.yml && gh run watch

# View status
gh run list --workflow=tests.yml --limit 3
```

**What it tests**:
- Code formatting (black, isort)
- Linting (ruff)
- Unit tests (pytest)
- Coverage threshold (90% - currently failing at 37%)
- Python 3.11 and 3.12 compatibility

**Use when**:
- After fixing bugs (Issues #102, #104)
- After adding tests (Issue #103)
- Before creating PR
- After merging main branch changes

---

### 2. AgentReady Assessment (agentready-assessment.yml)
**Purpose**: Runs AgentReady self-assessment on the repository

```bash
# Run self-assessment
gh workflow run agentready-assessment.yml

# View results
gh run view --log
```

**Use when**:
- After improving repository structure
- After adding new assessors
- Verifying CLAUDE.md or documentation changes
- Checking impact of code quality improvements

---

### 3. Continuous Learning (continuous-learning.yml)
**Purpose**: Extracts skills from assessment and updates learnings

```bash
# Run learning extraction
gh workflow run continuous-learning.yml

# Check generated skills
gh run view --log
```

**Use when**:
- After completing major features
- After improving test coverage
- Capturing successful patterns for Claude Code skills

---

### 4. Update Docs (update-docs.yml)
**Purpose**: Regenerates GitHub Pages documentation from source files

```bash
# Trigger docs rebuild
gh workflow run update-docs.yml

# View deployment status
gh run list --workflow=update-docs.yml
```

**Use when**:
- After updating CLAUDE.md
- After changing agent-ready-codebase-attributes.md
- After modifying specs/ or contracts/
- After major code changes requiring doc updates

---

### 5. Security Scan (security.yml)
**Purpose**: Runs Bandit security scanner on Python code

```bash
# Run security scan
gh workflow run security.yml
```

**Use when**:
- After fixing security issues (Issue #102)
- After adding subprocess handling
- Before releases
- After modifying LLM enrichment code

---

## Common Workflows

### After Fixing a Bug

```bash
# 1. Commit your fix
git add .
git commit -m "fix: resolve timeout issue in CommandFix"

# 2. Trigger tests to verify fix
gh workflow run tests.yml

# 3. Watch the run
gh run watch

# 4. If tests pass, push
git push
```

### After Adding Tests (Working on Issue #103)

```bash
# 1. Commit new tests
git add tests/
git commit -m "test: add coverage for CLAUDEmdAssessor edge cases"

# 2. Run tests locally first
pytest --cov=src --cov-report=term

# 3. If coverage improves, trigger CI
gh workflow run tests.yml

# 4. Check if closer to 90% threshold
gh run view --log | grep "TOTAL"
```

### Before Creating a PR

```bash
# Run full CI suite
gh workflow run tests.yml
gh workflow run agentready-assessment.yml
gh workflow run security.yml

# Wait for all to complete
gh run list --limit 3

# If all pass, create PR
gh pr create --title "Fix: Command timeout security issue" --body "..."
```

---

## Workflow Status Commands

### View Recent Runs
```bash
# All workflows
gh run list --limit 10

# Specific workflow
gh run list --workflow=tests.yml --limit 5

# Failed runs only
gh run list --status failure --limit 5
```

### Watch Live Run
```bash
# Trigger and watch
gh workflow run tests.yml && gh run watch

# Watch specific run
gh run watch <run-id>

# Watch most recent run
gh run view --log --job <job-id>
```

### View Logs
```bash
# View most recent run
gh run view

# View with logs
gh run view --log

# View specific run
gh run view <run-id> --log

# Download logs for debugging
gh run download <run-id>
```

### Cancel Runs
```bash
# Cancel specific run
gh run cancel <run-id>

# Cancel all running workflows
gh run list --status in_progress | awk '{print $7}' | xargs -n1 gh run cancel
```

---

## Integration with Claude Code

### Pattern: Test-Driven Development

```bash
# 1. Write failing test
# (Claude Code writes test for new feature)

# 2. Run tests locally
pytest tests/unit/test_new_feature.py -v

# 3. Write implementation
# (Claude Code implements feature)

# 4. Run tests locally again
pytest tests/unit/test_new_feature.py -v

# 5. If passing, trigger full CI
gh workflow run tests.yml

# 6. Watch for any integration issues
gh run watch
```

### Pattern: Security Fix Verification

```bash
# 1. Fix security issue (e.g., Issue #102)
# (Claude Code implements timeout fix)

# 2. Run security scan
gh workflow run security.yml

# 3. Run tests
gh workflow run tests.yml

# 4. Both must pass before merge
gh run list --limit 2
```

### Pattern: Coverage Improvement (Issue #103)

```bash
# 1. Check current coverage
pytest --cov=src --cov-report=term

# Output: TOTAL coverage: 37%

# 2. Add tests to improve coverage
# (Claude Code writes tests)

# 3. Check new coverage
pytest --cov=src --cov-report=term

# Output: TOTAL coverage: 45% (+8%)

# 4. Trigger CI to verify
gh workflow run tests.yml

# 5. Check if threshold met (goal: 90%)
gh run view --log | grep "TOTAL"

# 6. Repeat until 90% reached
```

---

## Monitoring CI Status

### GitHub CLI Status Dashboard

```bash
# Create alias for quick status check
alias ci-status='gh run list --limit 5 && echo "" && gh pr status'

# Run it
ci-status
```

### Watch Multiple Workflows

```bash
# Trigger all critical workflows
gh workflow run tests.yml
gh workflow run security.yml
gh workflow run agentready-assessment.yml

# Check status of all
watch -n 5 'gh run list --limit 10'
```

---

## Debugging Failed Runs

### Step 1: Identify Failure
```bash
# View failed runs
gh run list --status failure --limit 3

# Get run ID
gh run list --workflow=tests.yml --limit 1
```

### Step 2: View Logs
```bash
# View logs inline
gh run view <run-id> --log

# Download logs for detailed analysis
gh run download <run-id>

# View specific job logs
gh run view <run-id> --log --job <job-id>
```

### Step 3: Reproduce Locally
```bash
# Run the same commands as CI
black --check .
isort --check .
ruff check .
pytest --cov=src --cov-report=term --cov-fail-under=90
```

### Step 4: Fix and Retry
```bash
# Fix the issue
# (Claude Code makes changes)

# Re-trigger workflow
gh workflow run tests.yml

# Watch for success
gh run watch
```

---

## CI Badges for README

GitHub Actions automatically provides badges:

```markdown
![Tests](https://github.com/ambient-code/agentready/actions/workflows/tests.yml/badge.svg)
![Security](https://github.com/ambient-code/agentready/actions/workflows/security.yml/badge.svg)
![Coverage](https://codecov.io/gh/ambient-code/agentready/branch/main/graph/badge.svg)
```

---

## Common Issues

### Issue: "workflow not found"
**Solution**: Ensure workflow file exists in `.github/workflows/`
```bash
ls -la .github/workflows/
```

### Issue: "Resource not accessible by integration"
**Solution**: Check GitHub App permissions or use PAT
```bash
gh auth status
```

### Issue: Workflow runs but fails immediately
**Solution**: Check workflow syntax and required secrets
```bash
gh workflow view tests.yml
```

---

## Advanced: Workflow Dispatch with Inputs

Some workflows support custom inputs. Example:

```yaml
# In workflow file
workflow_dispatch:
  inputs:
    python-version:
      description: 'Python version to test'
      required: false
      default: '3.11'
```

Trigger with inputs:
```bash
gh workflow run tests.yml -f python-version=3.12
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Run tests | `gh workflow run tests.yml` |
| Watch run | `gh run watch` |
| View recent runs | `gh run list --limit 5` |
| View logs | `gh run view --log` |
| Cancel run | `gh run cancel <run-id>` |
| All workflows | `gh workflow list` |
| Trigger + watch | `gh workflow run tests.yml && gh run watch` |
| Status check | `gh run list --workflow=tests.yml --limit 3` |

---

## Integration with Issue #102, #103, #104

### For Issue #102 (Command Timeout)
```bash
# After implementing fix:
1. pytest tests/unit/test_fix.py -v
2. gh workflow run tests.yml
3. gh workflow run security.yml
4. gh run watch
```

### For Issue #103 (Coverage)
```bash
# After adding tests:
1. pytest --cov=src --cov-report=term
2. gh workflow run tests.yml
3. gh run view --log | grep "TOTAL"
4. Repeat until 90% reached
```

### For Issue #104 (LLM Retry)
```bash
# After implementing bounded retry:
1. pytest tests/unit/test_llm_enricher.py -v
2. gh workflow run tests.yml
3. gh run watch
```

---

**Created**: 2025-11-22
**Last Updated**: 2025-11-22
**Related Issues**: #102, #103, #104
**Workflows Available**: 10 (tests, security, docs, assessment, learning, etc.)
