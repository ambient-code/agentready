# AgentReady Documentation

This directory contains the complete GitHub Pages documentation site for AgentReady.

## Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── _layouts/                # Page templates
│   ├── default.html         # Base layout
│   ├── home.html            # Homepage layout
│   └── page.html            # Standard page layout
├── assets/
│   └── css/
│       └── style.css        # Custom styles
├── index.md                 # Homepage
├── user-guide.md            # User documentation
├── developer-guide.md       # Contributor guide
├── attributes.md            # Attribute reference
├── api-reference.md         # API documentation
├── examples.md              # Examples and showcase
├── DEPLOYMENT.md            # Deployment instructions
└── README.md                # This file
```

## Local Development

### Prerequisites

- Ruby 2.7+ (3.0+ recommended)
- Bundler
- Jekyll

### Setup

```bash
# Navigate to docs directory
cd docs/

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Or with live reload
bundle exec jekyll serve --livereload

# Visit http://localhost:4000
```

### Making Changes

1. **Edit Markdown files** (*.md)
2. **Jekyll auto-regenerates** site (if using --livereload)
3. **Refresh browser** to see changes
4. **Commit when satisfied**

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick deploy**:

1. Enable GitHub Pages in repository settings
2. Select `docs/` directory as source
3. Push changes to main branch
4. Visit `https://yourusername.github.io/agentready`

## Content Guidelines

### Adding New Pages

1. Create new `.md` file in `docs/`:

   ```markdown
   ---
   layout: page
   title: Page Title
   ---

   # Page Title

   Content here...
   ```

2. Add to navigation in `_config.yml`:

   ```yaml
   navigation:
     - title: Page Title
       url: /page-url
   ```

### Markdown Formatting

- Use `#` for h1, `##` for h2, etc.
- Code blocks with triple backticks: ` ```python `
- Links: `[text](url)` or `[text]({{ '/page' | relative_url }})`
- Images: `![alt]({{ '/assets/images/file.png' | relative_url }})`

### Front Matter

All pages should have front matter:

```yaml
---
layout: page  # or 'home' for homepage
title: Page Title
---
```

## Styling

Custom styles in `assets/css/style.css` using CSS variables for:

- Colors (certification levels, status indicators)
- Typography (fonts, sizes, weights)
- Spacing (consistent padding/margins)
- Components (buttons, grids, tables)

**Design system**:

- Primary color: `#2563eb` (blue)
- Font: System fonts for speed
- Responsive: Mobile-first design
- Accessible: WCAG AA compliant

## Testing

### Link Checking

```bash
# Install html-proofer
gem install html-proofer

# Build site
bundle exec jekyll build

# Test links
htmlproofer ./_site --disable-external
```

### Markdown Linting

```bash
# Install markdownlint
npm install -g markdownlint-cli

# Lint all Markdown files
markdownlint docs/*.md
```

## Maintenance

### Updating Dependencies

```bash
# Update Gemfile.lock
bundle update

# Test locally
bundle exec jekyll serve

# Commit if working
git add Gemfile.lock
git commit -m "chore: Update Jekyll dependencies"
```

### Checking for Broken Links

Periodically check for broken external links:

```bash
# Build and test
bundle exec jekyll build
htmlproofer ./_site --external_only --http-status-ignore "999"
```

## Support

- **Jekyll Docs**: <https://jekyllrb.com/docs/>
- **GitHub Pages**: <https://docs.github.com/en/pages>
- **Markdown Guide**: <https://www.markdownguide.org/>

## Contributing

Contributions to documentation are welcome!

1. Fork repository
2. Create feature branch
3. Make changes in `docs/`
4. Test locally
5. Submit pull request

**See main [CLAUDE.md](../CLAUDE.md) for development workflow.**

---

**Questions?** Open an issue or discussion on GitHub.
