# AgentReady Patches

This directory contains patches for upstream dependencies that haven't been released yet.

## harbor-task-filtering-fix.patch

**Status**: Fixed upstream, waiting for release

**Problem**: Harbor's `-t`/`--task-name` flag is ignored, causing all tasks to run instead of filtered subset.

**Upstream Fix**: [Harbor commit f9e6d2e](https://github.com/laude-institute/harbor/commit/f9e6d2e10c72d33373012294c36fd4938c45c26c) (Dec 12, 2025)

**Released**: ❌ Not yet (latest PyPI: 0.1.23 from Dec 11, 2025)

### Option 1: Install from Main (Recommended)

```bash
pip uninstall harbor
pip install git+https://github.com/laude-institute/harbor.git
```

### Option 2: Apply Patch Manually

```bash
# Find Harbor installation
HARBOR_PATH=$(python -c "import harbor, os; print(os.path.dirname(harbor.__file__))")

# Apply patch
cd "$HARBOR_PATH/.."
patch -p1 < /path/to/agentready/patches/harbor-task-filtering-fix.patch
```

### Option 3: Manual Edit

Edit `harbor/models/job/config.py`:

```python
# Line 42: Change
fnmatch(task_id.path.name, pattern_id)
# To:
fnmatch(task_id.get_name(), pattern_id)

# Line 52: Change
fnmatch(task_id.path.name, pattern_id)
# To:
fnmatch(task_id.get_name(), pattern_id)

# Line 76: Change
TaskConfig(path=task_id.path, source=self.path.name)
# To:
TaskConfig(path=task_id.path, source=self.path.expanduser().resolve().name)
```

## When to Remove

Once Harbor 0.1.24 (or later) is released to PyPI, this patch is no longer needed.

Check PyPI: https://pypi.org/project/harbor/#history
