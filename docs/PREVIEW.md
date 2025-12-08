# Demo Preview Guide

Two ways to preview AgentReady demo sites: Quick (slides only) or Full (Jekyll server with all demos).

---

## Quick Preview (No Setup)

**Fastest option** - Just open the slides in your browser:

```bash
# macOS
open docs/demos/slides.html

# Linux
xdg-open docs/demos/slides.html

# Or manually: Double-click docs/demos/slides.html
```

**What you'll see**:
- 13 reveal.js slides with Night theme
- Keyboard navigation (← → Space)
- Syntax-highlighted code
- No Mermaid diagrams (slides don't use them)

---

## Full Preview (Complete Experience)

**Requires**: Ruby, Bundler, Jekyll (see installation below)

### Start Jekyll Server

```bash
# From repository root
make docs-serve

# OR manually:
cd docs
bundle exec jekyll serve --livereload
```

### View Demos

Open in browser: http://localhost:4000/agentready/demos/

**Available demos**:
- **Hub** (`/demos/`) - Landing page with 4 demo cards
- **Walkthrough** (`/demos/walkthrough`) - Complete guide with Mermaid diagrams
- **Slides** (`/demos/slides`) - reveal.js presentation
- **Terminal Demo** (`/demos/terminal-demo`) - asciinema player (recording needed)

**Features**:
- Live reload (changes auto-refresh)
- Mermaid diagrams rendered
- Full navigation menu
- All Jekyll includes/layouts

### Stop Server

Press `Ctrl+C` in terminal

---

## Installation (First Time Only)

### macOS

```bash
# 1. Install Ruby via Homebrew
brew install ruby

# 2. Add to PATH (one-time)
echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 3. Install Bundler
gem install bundler

# 4. Install Jekyll dependencies
cd docs
bundle install
```

### Ubuntu/Debian

```bash
# 1. Install Ruby
sudo apt-get install ruby-full build-essential

# 2. Configure gem path (avoid sudo)
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 3. Install Bundler
gem install bundler

# 4. Install Jekyll dependencies
cd docs
bundle install
```

---

## Troubleshooting

### Port 4000 already in use

```bash
# Find process using port 4000
lsof -i :4000

# Kill it
kill -9 <PID>

# Or use different port
bundle exec jekyll serve --port 4001
```

### Mermaid diagrams not rendering

- Wait 2-3 seconds after page load (CDN initialization)
- Check browser console for errors
- Try hard refresh: Cmd+Shift+R (macOS) or Ctrl+Shift+R (Linux)

### Slides keyboard navigation not working

- Click anywhere on the slides first (focus required)
- Use Space, ← →, or click the controls

---

## Quick Commands

```bash
# Generate slides (if changed DEMO_SUMMARY.md)
make demo-slides

# Validate all demo files
make demo-validate

# Start Jekyll server
make docs-serve

# Open slides directly
open docs/demos/slides.html
```

---

**Setup Date**: 2025-12-07
**Ruby**: 3.4.7 (Homebrew)
**Jekyll**: 3.9.5
**Bundler**: 2.5.23
