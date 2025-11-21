# Coldstart Prompt: Setup GitHub Release Pipeline

## Objective
Set up a production-grade release pipeline following GitHub best practices for automated releases, semantic versioning, changelog generation, and asset management.

## Context
This prompt guides you through establishing a comprehensive release automation workflow that:
- Uses semantic versioning (SemVer)
- Automates changelog generation from conventional commits
- Creates GitHub releases with proper assets
- Publishes to package registries (PyPI, npm, etc.)
- Maintains release notes and documentation
- Follows security and signing best practices

## Prerequisites
- Repository uses conventional commits (enforced via pre-commit hooks)
- Repository has a clear versioning strategy
- CI/CD pipelines are already configured
- Branch protection rules are in place for main/master

## Tasks

### 1. Configure Semantic Release Automation

**Create `.github/workflows/release.yml`:**

```yaml
name: Release

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: write
  issues: write
  pull-requests: write
  packages: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'

      - name: Install semantic-release
        run: |
          npm install -g semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github

      - name: Run semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
```

### 2. Create Semantic Release Configuration

**Create `.releaserc.json`:**

```json
{
  "branches": ["main", "master"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          {
            "path": "dist/**",
            "label": "Distribution files"
          }
        ]
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md", "package.json"],
        "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
      }
    ]
  ]
}
```

### 3. Setup Package Publishing (Language-Specific)

#### For Python Projects:

**Create `.github/workflows/publish-pypi.yml`:**

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://upload.pypi.org/legacy/
```

#### For Node.js Projects:

**Create `.github/workflows/publish-npm.yml`:**

```yaml
name: Publish to npm

on:
  release:
    types: [published]

permissions:
  contents: read
  packages: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 4. Configure Release Drafter (Alternative/Complementary Approach)

**Create `.github/release-drafter.yml`:**

```yaml
name-template: 'v$RESOLVED_VERSION'
tag-template: 'v$RESOLVED_VERSION'
categories:
  - title: '🚀 Features'
    labels:
      - 'feature'
      - 'enhancement'
  - title: '🐛 Bug Fixes'
    labels:
      - 'fix'
      - 'bugfix'
      - 'bug'
  - title: '🧰 Maintenance'
    labels:
      - 'chore'
      - 'dependencies'
  - title: '📚 Documentation'
    labels:
      - 'documentation'
      - 'docs'
  - title: '🔒 Security'
    labels:
      - 'security'
change-template: '- $TITLE @$AUTHOR (#$NUMBER)'
version-resolver:
  major:
    labels:
      - 'major'
      - 'breaking'
  minor:
    labels:
      - 'minor'
      - 'feature'
  patch:
    labels:
      - 'patch'
      - 'fix'
      - 'bugfix'
  default: patch
template: |
  ## Changes

  $CHANGES

  ## Contributors

  $CONTRIBUTORS
```

**Create `.github/workflows/release-drafter.yml`:**

```yaml
name: Release Drafter

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  update_release_draft:
    runs-on: ubuntu-latest
    steps:
      - uses: release-drafter/release-drafter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 5. Add Release Signing and Provenance

**Create `.github/workflows/release-provenance.yml`:**

```yaml
name: Generate SLSA Provenance

on:
  release:
    types: [published]

permissions:
  actions: read
  id-token: write
  contents: write

jobs:
  provenance:
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.9.0
    with:
      base64-subjects: "${{ needs.build.outputs.digests }}"
      upload-assets: true
```

### 6. Create Release Documentation

**Create `docs/RELEASE_PROCESS.md`:**

```markdown
# Release Process

## Overview
This project uses automated semantic releases based on conventional commits.

## Release Types

- **Major (X.0.0)**: Breaking changes (commit prefix: `feat!:` or `fix!:`)
- **Minor (x.Y.0)**: New features (commit prefix: `feat:`)
- **Patch (x.y.Z)**: Bug fixes (commit prefix: `fix:`)

## Automated Release Workflow

1. Commits are merged to `main` branch
2. Semantic-release analyzes commit messages
3. Version is automatically determined
4. CHANGELOG.md is updated
5. Git tag is created
6. GitHub Release is published
7. Package is published to registry

## Manual Release Trigger

To manually trigger a release:
```bash
gh workflow run release.yml
```

## Pre-release Process

For beta/alpha releases:
```bash
git checkout -b beta
git push origin beta
```

Then update `.releaserc.json` to include beta branch.

## Hotfix Process

1. Create hotfix branch from latest release tag
2. Apply fix with conventional commit
3. Merge to main with expedited review
4. Release automation handles versioning

## Rollback Procedure

To rollback a release:
```bash
# Delete the tag locally and remotely
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3

# Delete the GitHub release
gh release delete v1.2.3 --yes

# Revert the release commit
git revert <release-commit-sha>
git push origin main
```
```

### 7. Setup Release Checklist Template

**Create `.github/RELEASE_CHECKLIST.md`:**

```markdown
# Release Checklist

## Pre-Release
- [ ] All tests passing on main branch
- [ ] Documentation is up to date
- [ ] CHANGELOG.md reflects all changes
- [ ] Security vulnerabilities addressed
- [ ] Dependencies are up to date
- [ ] Version number follows SemVer
- [ ] Migration guide written (if breaking changes)

## Release
- [ ] Release workflow triggered
- [ ] GitHub Release created successfully
- [ ] Package published to registry
- [ ] Release assets uploaded
- [ ] Provenance attestation generated

## Post-Release
- [ ] Release announcement published
- [ ] Documentation site updated
- [ ] Social media announcement (if applicable)
- [ ] Dependent projects notified
- [ ] Issue/PR milestones closed
- [ ] Monitor for regression reports
```

### 8. Configure Branch Protection for Releases

**Required settings via GitHub UI or API:**

```bash
# Enable branch protection for main
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test","lint","build"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  --field restrictions=null
```

## Success Criteria

- ✅ Releases are created automatically on merge to main
- ✅ Version numbers follow semantic versioning
- ✅ CHANGELOG.md is automatically updated
- ✅ GitHub Releases include proper release notes
- ✅ Packages are published to registry automatically
- ✅ Release assets are signed and verifiable
- ✅ Documentation is clear for contributors
- ✅ Rollback procedure is documented and tested

## Testing the Pipeline

1. Create a test commit with conventional commit message:
   ```bash
   git commit -m "feat: add test feature for release pipeline"
   ```

2. Push to main (or create PR and merge)

3. Verify:
   - GitHub Actions workflow runs successfully
   - New release appears in GitHub Releases
   - CHANGELOG.md is updated
   - Package version is bumped
   - Registry contains new version

## Maintenance

- Review release workflow quarterly
- Update semantic-release plugins regularly
- Monitor GitHub Actions usage and costs
- Audit release permissions and tokens
- Test rollback procedure annually

## Resources

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions: Publishing packages](https://docs.github.com/en/actions/publishing-packages)
- [SLSA Framework](https://slsa.dev/)
- [Sigstore for signing](https://www.sigstore.dev/)

## Troubleshooting

### Release workflow fails
- Check conventional commit format
- Verify GITHUB_TOKEN permissions
- Review semantic-release configuration

### Package publish fails
- Verify registry credentials
- Check package name availability
- Review version conflict errors

### Version not incrementing
- Ensure commits use conventional format
- Check branch configuration in .releaserc.json
- Verify no `[skip ci]` in commit messages
