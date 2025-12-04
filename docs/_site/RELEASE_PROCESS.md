# Release Process

## Overview

AgentReady uses automated semantic releases based on conventional commits. Releases are created automatically when commits are merged to the `main` branch.

## Release Types

Releases follow [Semantic Versioning](https://semver.org/):

- **Major (X.0.0)**: Breaking changes (commit prefix: `feat!:` or `fix!:` or `BREAKING CHANGE:`)
- **Minor (x.Y.0)**: New features (commit prefix: `feat:`)
- **Patch (x.y.Z)**: Bug fixes (commit prefix: `fix:`)

## Automated Release Workflow

When commits are merged to `main`:

1. **Semantic-release analyzes** commit messages since the last release
2. **Version is determined** based on conventional commit types
3. **CHANGELOG.md is updated** with release notes
4. **pyproject.toml version** is bumped automatically
5. **Git tag is created** (e.g., `v1.0.0`)
6. **GitHub Release is published** with release notes
7. **Changes are committed** back to main with `[skip ci]`

## Conventional Commit Format

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Common Types

- `feat:` - New feature (triggers minor release)
- `fix:` - Bug fix (triggers patch release)
- `docs:` - Documentation changes (no release)
- `chore:` - Maintenance tasks (no release)
- `refactor:` - Code refactoring (no release)
- `test:` - Test changes (no release)
- `ci:` - CI/CD changes (no release)

### Breaking Changes

To trigger a major version bump, use one of these:

```bash
# With ! after type
feat!: redesign assessment API

# With BREAKING CHANGE footer
feat: update scoring algorithm

BREAKING CHANGE: Assessment.score is now a float instead of int
```

## Manual Release Trigger

To manually trigger a release without a commit:

```bash
# Trigger release workflow via GitHub CLI
gh workflow run release.yml

# Or via GitHub UI
# Actions → Release → Run workflow → Run workflow
```

## Pre-release Process

For alpha/beta releases (not yet configured):

```bash
# Future: Create pre-release from beta branch
git checkout -b beta
git push origin beta
```

Then update `.releaserc.json` to include beta branch configuration.

## Hotfix Process

For urgent production fixes:

1. **Create hotfix branch** from the latest release tag:

   ```bash
   git checkout -b hotfix/critical-bug v1.2.3
   ```

2. **Apply fix** with conventional commit:

   ```bash
   git commit -m "fix: resolve critical security issue"
   ```

3. **Push and create PR** to main:

   ```bash
   git push origin hotfix/critical-bug
   gh pr create --base main --title "fix: critical security hotfix"
   ```

4. **Merge to main** - Release automation handles versioning

## Rollback Procedure

To rollback a release:

### 1. Delete the tag and release

```bash
# Delete tag locally
git tag -d v1.2.3

# Delete tag remotely
git push origin :refs/tags/v1.2.3

# Delete GitHub release
gh release delete v1.2.3 --yes
```

### 2. Revert the release commit

```bash
# Find the release commit
git log --oneline | grep "chore(release)"

# Revert it
git revert <release-commit-sha>
git push origin main
```

### 3. Restore previous version

Edit `pyproject.toml` to restore the previous version number and commit.

## Release Checklist

Before a major release, ensure:

- [ ] All tests passing on main branch
- [ ] Documentation is up to date
- [ ] Security vulnerabilities addressed
- [ ] Dependencies are up to date (run `uv pip list --outdated`)
- [ ] Self-assessment score is current
- [ ] Migration guide written (if breaking changes)
- [ ] Examples updated for new features

## Monitoring Releases

After a release is published:

1. **Verify GitHub Release** - Check release notes are accurate
2. **Monitor issues** - Watch for regression reports
3. **Check workflows** - Ensure no failures in release workflow
4. **Update milestones** - Close completed milestone, create next one

## Troubleshooting

### Release workflow fails

- Check commit message format matches conventional commits
- Verify `GITHUB_TOKEN` has sufficient permissions
- Review semantic-release logs in Actions tab
- Ensure no merge conflicts in CHANGELOG.md

### Version not incrementing

- Ensure commits use conventional commit format (`feat:`, `fix:`, etc.)
- Check that commits aren't marked `[skip ci]`
- Verify `.releaserc.json` branch configuration matches current branch
- Review semantic-release dry-run output

### CHANGELOG conflicts

If CHANGELOG.md has merge conflicts:

1. Resolve conflicts manually
2. Commit the resolution
3. Semantic-release will include the fix in next release

## Resources

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Release Documentation](https://semantic-release.gitbook.io/)
- [GitHub Actions: Publishing packages](https://docs.github.com/en/actions/publishing-packages)

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2025-11-21 | Initial release with core assessment engine |

---

**Last Updated**: 2025-11-21
**Maintained By**: AgentReady Team
