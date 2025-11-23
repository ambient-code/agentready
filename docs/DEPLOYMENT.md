# GitHub Pages Deployment Guide

Complete instructions for deploying AgentReady documentation to GitHub Pages.

## Quick Start

1. **Enable GitHub Pages** in repository settings
2. **Configure source**: `docs/` directory from `main` branch
3. **Wait for deployment** (~2 minutes)
4. **Visit**: `https://yourusername.github.io/agentready`

---

## Detailed Setup Instructions

### Step 1: Repository Configuration

1. **Navigate to repository settings**:
   - Go to your AgentReady repository on GitHub
   - Click "Settings" tab
   - Click "Pages" in left sidebar

2. **Configure source**:
   - **Source**: Deploy from a branch
   - **Branch**: `main` (or your default branch)
   - **Folder**: `/docs`
   - Click "Save"

3. **Optional: Custom domain**:
   - Add custom domain if desired
   - Configure DNS records (see GitHub documentation)

### Step 2: Update _config.yml

Edit `docs/_config.yml` to match your repository:

```yaml
# Site settings
title: AgentReady
description: Repository Quality Assessment for AI-Assisted Development

# Repository information
repository: YOUR_USERNAME/agentready
github_username: YOUR_USERNAME

# URLs
baseurl: ""  # Subpath (e.g., "/agentready" if not on root domain)
url: "https://YOUR_USERNAME.github.io"  # Base hostname
```

**Important**:

- Replace `YOUR_USERNAME` with your GitHub username
- If using custom domain, update `url` accordingly
- Set `baseurl` to `/agentready` if repository is not organization homepage

### Step 3: Verify Configuration

```bash
# Test locally with Jekyll (optional)
cd docs/

# Install Jekyll (if not already installed)
gem install bundler jekyll

# Create Gemfile
cat > Gemfile << 'EOF'
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "jekyll-seo-tag"
gem "jekyll-sitemap"
EOF

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Visit http://localhost:4000 in browser
```

### Step 4: Commit and Push

```bash
# From repository root
git add docs/
git commit -m "docs: Add GitHub Pages documentation site"
git push origin main
```

### Step 5: Monitor Deployment

1. **Go to Actions tab** in GitHub repository
2. **Wait for "pages-build-deployment" workflow** to complete
3. **Deployment time**: Usually 1-3 minutes
4. **Check status**:
   - Green check: Deployment successful
   - Red X: Deployment failed (check logs)

### Step 6: Visit Your Site

Once deployment completes:

- **URL**: `https://yourusername.github.io/agentready`
- **Custom domain** (if configured): `https://your-domain.com`

---

## Troubleshooting

### Issue: 404 Not Found

**Possible causes**:

1. GitHub Pages not enabled in settings
2. Wrong branch/folder selected
3. Deployment still in progress
4. `baseurl` misconfigured in `_config.yml`

**Solutions**:

```bash
# Check _config.yml
grep -E "baseurl|url" docs/_config.yml

# Verify branch is correct
git branch --show-current

# Check GitHub Actions logs for errors
# (visit /actions tab in repository)
```

### Issue: Broken Links

**Cause**: Incorrect `baseurl` in `_config.yml`

**Solution**:

```yaml
# For repository named "agentready" at github.io/agentready
baseurl: "/agentready"
url: "https://yourusername.github.io"

# For custom domain or organization site
baseurl: ""
url: "https://your-domain.com"
```

**Test links**:

```bash
# Search for absolute URLs (should use relative_url filter)
grep -r "href=\"/" docs/*.md

# Correct format:
# href="{{ '/user-guide' | relative_url }}"
```

### Issue: CSS Not Loading

**Cause**: CSS file not found due to path issues

**Solution**:

1. **Verify file exists**:

   ```bash
   ls docs/assets/css/style.css
   ```

2. **Check layout references**:

   ```html
   <!-- Should be: -->
   <link rel="stylesheet" href="{{ '/assets/css/style.css' | relative_url }}">

   <!-- Not: -->
   <link rel="stylesheet" href="/assets/css/style.css">
   ```

3. **Clear browser cache** and refresh

### Issue: Jekyll Build Failure

**Check GitHub Actions logs**:

1. Go to repository → Actions tab
2. Click latest workflow run
3. Expand failed step
4. Look for error messages

**Common errors**:

**YAML syntax error**:

```
Error: Invalid YAML in _config.yml
```

**Solution**: Validate YAML syntax with online validator

**Missing plugin**:

```
Error: jekyll-seo-tag not found
```

**Solution**: Add to `_config.yml`:

```yaml
plugins:
  - jekyll-seo-tag
  - jekyll-sitemap
```

**Liquid syntax error**:

```
Error: Liquid Exception in layouts/default.html
```

**Solution**: Check for missing `{% endfor %}`, `{% endif %}`, etc.

---

## Local Development

### Setup Jekyll Locally

```bash
# Install Ruby (required for Jekyll)
# macOS: Already installed
# Linux: apt-get install ruby-full
# Windows: Use RubyInstaller

# Install Bundler and Jekyll
gem install bundler jekyll

# Navigate to docs directory
cd docs/

# Create Gemfile (if not exists)
cat > Gemfile << 'EOF'
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "jekyll-seo-tag"
gem "jekyll-sitemap"
gem "webrick"  # Required for Ruby 3.0+
EOF

# Install dependencies
bundle install

# Serve site locally
bundle exec jekyll serve

# Or with live reload
bundle exec jekyll serve --livereload

# Visit http://localhost:4000
```

### Development Workflow

```bash
# 1. Make changes to Markdown files
vim docs/user-guide.md

# 2. Jekyll auto-regenerates (if using --livereload)
# Or manually restart server

# 3. View changes in browser (refresh if needed)

# 4. Commit when satisfied
git add docs/user-guide.md
git commit -m "docs: Update user guide installation section"
git push
```

### Testing Links Locally

```bash
# Install html-proofer
gem install html-proofer

# Build site
bundle exec jekyll build

# Test all links
htmlproofer ./_site --disable-external

# Test including external links (slower)
htmlproofer ./_site
```

---

## Custom Domain Setup

### 1. Add CNAME File

```bash
# Create CNAME file in docs/
echo "docs.agentready.dev" > docs/CNAME

# Commit
git add docs/CNAME
git commit -m "docs: Add custom domain CNAME"
git push
```

### 2. Configure DNS

Add DNS records at your domain registrar:

**For apex domain (example.com)**:

```
A    @    185.199.108.153
A    @    185.199.109.153
A    @    185.199.110.153
A    @    185.199.111.153
```

**For subdomain (docs.example.com)**:

```
CNAME    docs    yourusername.github.io.
```

### 3. Enable HTTPS

1. Go to repository Settings → Pages
2. Check "Enforce HTTPS"
3. Wait for certificate provisioning (~24 hours)

### 4. Update _config.yml

```yaml
url: "https://docs.agentready.dev"
baseurl: ""
```

---

## Automation & CI/CD

### Auto-Deploy on Push

GitHub Pages automatically deploys when you push to `main` branch.

**No additional configuration needed!**

### Custom GitHub Actions Workflow (Optional)

Create `.github/workflows/docs.yml` for advanced control:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.1'
          bundler-cache: true

      - name: Build Jekyll site
        run: |
          cd docs
          bundle install
          bundle exec jekyll build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_site
```

---

## Content Updates

### Adding New Pages

1. **Create Markdown file** in `docs/`:

   ```bash
   cat > docs/new-page.md << 'EOF'
   ---
   layout: page
   title: New Page
   ---

   # New Page

   Content goes here.
   EOF
   ```

2. **Add to navigation** in `_config.yml`:

   ```yaml
   navigation:
     # ... existing items ...
     - title: New Page
       url: /new-page
   ```

3. **Commit and push**:

   ```bash
   git add docs/new-page.md docs/_config.yml
   git commit -m "docs: Add new page"
   git push
   ```

### Updating Existing Content

```bash
# Edit file
vim docs/user-guide.md

# Preview locally (optional)
bundle exec jekyll serve

# Commit and push
git add docs/user-guide.md
git commit -m "docs: Update installation instructions"
git push

# GitHub Pages auto-deploys in ~2 minutes
```

---

## Performance Optimization

### Image Optimization

```bash
# Optimize images before adding
brew install imageoptim-cli  # macOS
imageoptim docs/assets/images/*.png

# Or use online tools:
# - TinyPNG (https://tinypng.com)
# - Squoosh (https://squoosh.app)
```

### Caching

GitHub Pages automatically sets cache headers for static assets.

**No additional configuration needed.**

### Minimize File Sizes

```bash
# Minify CSS (if not using Jekyll plugins)
npm install -g csso-cli
csso docs/assets/css/style.css -o docs/assets/css/style.min.css
```

---

## Monitoring & Analytics

### Google Analytics (Optional)

1. **Get tracking ID** from Google Analytics
2. **Add to _config.yml**:

   ```yaml
   google_analytics: UA-XXXXXXXXX-X
   ```

3. **Tracking script auto-added** by jekyll-seo-tag plugin

### GitHub Traffic

View built-in analytics:

1. Go to repository Insights tab
2. Click "Traffic"
3. See page views and visitor stats

---

## Backup & Versioning

### Site Backups

Your documentation is version-controlled in git. **No separate backup needed.**

To download static site:

```bash
# Build site locally
bundle exec jekyll build

# Copy _site directory
cp -r docs/_site ~/backups/agentready-docs-$(date +%Y%m%d)
```

### Rollback

```bash
# Revert to previous commit
git log --oneline docs/  # Find commit hash
git revert <commit-hash>
git push

# Or reset to specific commit (destructive)
git reset --hard <commit-hash>
git push --force  # Use with caution
```

---

## Support

- **Jekyll Documentation**: <https://jekyllrb.com/docs/>
- **GitHub Pages Docs**: <https://docs.github.com/en/pages>
- **Jekyll Themes**: <https://github.com/topics/jekyll-theme>
- **Troubleshooting**: <https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/troubleshooting-jekyll-build-errors-for-github-pages-sites>

---

## Next Steps

After deploying:

1. **Test all pages** and links
2. **Share URL** with team/community
3. **Set up custom domain** (optional)
4. **Enable analytics** (optional)
5. **Add to README** as documentation link

**Documentation URL**: Add to main README.md:

```markdown
## Documentation

Complete documentation available at: https://yourusername.github.io/agentready

- [User Guide](https://yourusername.github.io/agentready/user-guide)
- [Developer Guide](https://yourusername.github.io/agentready/developer-guide)
- [API Reference](https://yourusername.github.io/agentready/api-reference)
```

---

**Ready to deploy?** Follow steps 1-6 above. Deployment typically completes in under 3 minutes.
