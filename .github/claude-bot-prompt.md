# Claude Bot Automation Context

This file provides additional instructions for the automated Claude Code Action when implementing issues assigned to `claude-bot`.

## Automation Workflow

When assigned an issue, you should:

1. **Create feature branch**: Always create a feature branch from `main` (never push to main directly)
2. **Follow TDD**: Write tests before implementation when applicable
3. **Run linters**: Always run `black`, `isort`, `ruff` before committing
4. **Run tests**: Ensure all tests pass with `pytest`
5. **Commit frequently**: Use conventional commits with clear, succinct messages
6. **Open PR**: Create a pull request for review (don't merge automatically)

## Implementation Standards

- **Python**: Follow PEP 8, use type hints, support Python 3.11+
- **Testing**: Maintain >80% coverage for new code
- **Documentation**: Update docstrings and CLAUDE.md as needed
- **Security**: Never expose secrets, validate inputs, follow OWASP guidelines

## PR Template

When creating pull requests, include:
- Summary of changes
- Test plan
- Breaking changes (if any)
- Related issues/tickets

## Auto-Fix Critical Issues Workflow

When running in the `auto-fix-criticals` job (triggered after code review):

1. **Read review results**: Parse `.review-results.json` for findings with confidence ≥90
2. **Fix atomically**: Apply one fix at a time, validate, then commit
3. **Validation sequence**:
   - Run `black .` and `isort .` to format code
   - Run `ruff check .` to check for linting issues
   - Run `pytest` to ensure tests pass
   - If any step fails, revert changes and skip to next issue
4. **Commit format** (atomic, one issue per commit):
   ```
   fix(scope): brief description of fix

   - Detailed change 1
   - Detailed change 2

   Resolves critical issue #N from code review
   Confidence: XX%

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
5. **Update review comment**: Mark each fixed issue with "✅ Fixed in [commit sha]"
6. **Push to PR branch**: Use `git push origin HEAD` (never push to main)

### Critical Issue Categories (Auto-Fix Candidates)

Fix these automatically when confidence ≥90:

- **Security vulnerabilities**: Path traversal, injection attacks, exposed secrets
- **TOCTOU bugs**: Race conditions in file operations
- **Assessment accuracy**: False positives/negatives in assessor logic
- **Type safety**: Missing type hints causing runtime errors
- **Error handling**: Missing try-except blocks leading to crashes

### Do NOT Auto-Fix

Even with high confidence, skip these (require human judgment):

- Architectural changes (refactoring, design patterns)
- Performance optimizations (unless causing timeout/OOM)
- Breaking API changes
- Test modifications (unless fixing obvious typos)
- Multi-file refactors (too risky for automation)

## Important Context

- This is an open-source project under MIT license
- Target audience: Software engineering teams using AI-assisted development
- Code quality and user experience are paramount
- Prefer simple, focused solutions over complex abstractions

---

**Note**: CLAUDE.md is automatically read by the action. This file provides automation-specific guidance that supplements the project-level instructions.
