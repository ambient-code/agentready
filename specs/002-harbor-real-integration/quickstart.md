# Quickstart: Harbor Framework Integration

**Feature**: Harbor Framework Real Integration for Terminal-Bench Eval Harness
**Target Audience**: Developers and researchers using AgentReady eval harness
**Time to Complete**: ~10 minutes

---

## Prerequisites

- ✅ Python 3.11+ installed
- ✅ Docker installed and running (`docker --version`)
- ✅ Anthropic API key (get from https://console.anthropic.com)
- ✅ AgentReady installed (`agentready --version`)

---

## Step 1: Install Harbor Framework

```bash
# Install Harbor CLI (preferred method)
uv tool install harbor

# Alternative: pip install
pip install harbor

# Verify installation
harbor --version
```

**Expected Output**:
```
Harbor v2.0.0
```

---

## Step 2: Configure API Authentication

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Verify Docker is running
docker ps

# Enable real Harbor integration (instead of mocked)
export TBENCH_USE_REAL=1
```

**Important**: Keep your API key secure. Never commit it to git. Consider using `.env` files or secret managers.

---

## Step 3: Run Your First Baseline Benchmark

```bash
# Run baseline evaluation on a repository
agentready tbench baseline /path/to/your/repository

# Example with a specific repository
agentready tbench baseline ~/repos/my-python-project
```

**What Happens**:
1. AgentReady calls Harbor framework via subprocess
2. Harbor launches Docker container with your repository
3. Terminal-Bench runs coding tasks using Claude Code agent
4. Results are parsed and displayed

**Expected Output**:
```
Running Terminal-Bench baseline for /path/to/your/repository...
Using model: anthropic/claude-haiku-4-5
Using agent: claude-code

Benchmark Results:
  Score: 0.78 (78% accuracy)
  Resolved: 39 tasks
  Unresolved: 11 tasks
  Pass@1: 0.72
  Pass@3: 0.78

Duration: 8m 32s
```

**Time Estimate**: 5-10 minutes for typical repositories (<10k files)

---

## Step 4: Test an Assessor's Impact

```bash
# Test if adding CLAUDE.md improves benchmark score
agentready tbench test-assessor --assessor claude_md ~/repos/my-python-project
```

**What Happens**:
1. Runs baseline benchmark (no changes)
2. Applies assessor fix (adds CLAUDE.md if missing)
3. Runs delta benchmark (with CLAUDE.md)
4. Calculates score improvement

**Expected Output**:
```
Testing assessor: claude_md

Baseline Results:
  Score: 0.78 (78% accuracy)

Applying assessor fix...
  ✅ Created CLAUDE.md with project context

Delta Results:
  Score: 0.84 (84% accuracy)

Improvement: +0.06 (+6 percentage points)
Statistical Significance: ✅ Yes (p < 0.05)
```

**Time Estimate**: 10-20 minutes (runs two full benchmarks)

---

## Step 5: Aggregate Results Across Repositories

```bash
# After running benchmarks on multiple repositories, aggregate results
agentready tbench summarize
```

**Expected Output**:
```
Assessor Effectiveness Summary

Assessor ID       | Mean Δ | Median Δ | Std Δ | Sample Size | Significant?
------------------|--------|----------|-------|-------------|-------------
claude_md         | +0.12  | +0.10    | 0.05  | 15          | ✅ Yes
test_coverage     | +0.08  | +0.07    | 0.06  | 15          | ✅ Yes
dependency_pinning| +0.02  | +0.01    | 0.08  | 12          | ❌ No

Top 5 High-Impact Assessors:
1. claude_md (+12% average improvement)
2. test_coverage (+8% average improvement)
3. gitignore (+5% average improvement)
4. readme_structure (+4% average improvement)
5. type_annotations (+3% average improvement)

Recommended Actions:
- ✅ Keep: claude_md, test_coverage, gitignore (high impact)
- ⚠️  Review: dependency_pinning (no significant impact)
```

---

## Common Issues & Troubleshooting

### Issue 1: "Harbor not found"

**Symptom**: `FileNotFoundError: harbor command not found`

**Solution**:
```bash
# Ensure Harbor is in PATH
which harbor

# If not found, reinstall
uv tool install harbor

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

---

### Issue 2: "Docker daemon not running"

**Symptom**: `RuntimeError: Cannot connect to Docker daemon`

**Solution**:
```bash
# Start Docker Desktop (Mac/Windows)
open -a Docker  # Mac
# Or start Docker service (Linux)
sudo systemctl start docker

# Verify Docker is running
docker ps
```

---

### Issue 3: "API key invalid"

**Symptom**: `AuthenticationError: Invalid API key`

**Solution**:
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Verify key format (starts with sk-ant-)
```

---

### Issue 4: "Benchmark timeout"

**Symptom**: `TimeoutExpired: Command timed out after 3600 seconds`

**Solution**:
- Large repositories (>50k files) may exceed 1-hour timeout
- Consider reducing repository size or increasing timeout (future configuration option)
- Check Docker resource limits (Docker Desktop → Preferences → Resources)

---

## Advanced Usage

### Custom Model Selection

```bash
# Use Claude Sonnet instead of Haiku (higher quality, slower, more expensive)
export TBENCH_MODEL="anthropic/claude-sonnet-4-5"
agentready tbench baseline ~/repos/my-project
```

### Parallel Repository Evaluation

```bash
# Evaluate multiple repositories in parallel (4 workers)
agentready tbench batch ~/repos/*/ --workers 4
```

**Note**: Parallel batch evaluation is a future enhancement (Phase 3). Current implementation processes repositories sequentially.

---

## Cost Estimation

**Per Repository Benchmark**:
- Model: Claude Haiku 4.5
- Duration: ~10 minutes
- Tasks: ~50 Terminal-Bench tasks
- Estimated Cost: $0.30 - $0.50 USD

**Batch Evaluation** (10 repositories × 35 assessors):
- Total runs: 350 benchmarks
- Estimated total cost: ~$105 - $175 USD
- Time estimate: ~24 hours with 4-worker parallelism

**Cost Reduction Tips**:
- Use mocked integration for development/testing (`export TBENCH_USE_REAL=0`)
- Test on smaller repositories first (<5k files)
- Use sample size of 5-10 repositories for initial assessor validation

---

## Next Steps

1. ✅ Completed quickstart? → Run benchmarks on your repositories
2. ⏭️ Want batch evaluation? → See `docs/tbench/batch-evaluation.md` (Phase 3)
3. ⏭️ Need help? → See `docs/tbench/troubleshooting.md`
4. ⏭️ Contributing? → See `CONTRIBUTING.md` for development setup

---

## Further Reading

- [Harbor Framework Documentation](https://harborframework.com/docs)
- [Terminal-Bench GitHub](https://github.com/laude-institute/terminal-bench)
- [AgentReady Eval Harness Methodology](../../docs/tbench/methodology.md)
- [Assessor Refinement Results](../../docs/tbench/assessor-refinement-results.md)

---

**Document Status**: Complete
**Last Updated**: 2025-12-09
**Estimated Time**: 10 minutes setup + 10-20 minutes first benchmark
