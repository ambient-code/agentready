# Harbor Benchmark Comparison Guide

**Purpose**: Measure the empirical impact of `.claude/agents/doubleagent.md` on Claude Code performance using Harbor's Terminal-Bench.

**Created**: 2025-12-10
**AgentReady Version**: 2.10.0+

---

## Overview

The Harbor comparison tool automates A/B testing of Claude Code performance with and without the `doubleagent.md` agent file. It runs Terminal-Bench tasks twice—once with the agent file disabled, once with it enabled—and generates comprehensive comparison reports.

### What Gets Measured

- **Success Rate**: Percentage of tasks completed successfully
- **Duration**: Average time to complete tasks
- **Statistical Significance**: T-tests and effect sizes (Cohen's d)
- **Per-Task Impact**: Individual task improvements/regressions

---

## Quick Start

### Prerequisites

1. **Harbor Framework** installed:
   ```bash
   uv tool install harbor
   ```

2. **AgentReady** with harbor support:
   ```bash
   uv pip install -e .
   ```

3. **Agent file** exists at `.claude/agents/doubleagent.md`

### Basic Usage

Compare performance on 3 tasks:

```bash
agentready harbor compare \
  -t adaptive-rejection-sampler \
  -t async-http-client \
  -t terminal-file-browser \
  --verbose
```

This will:
1. Run tasks WITHOUT doubleagent.md (agent file disabled)
2. Run tasks WITH doubleagent.md (agent file enabled)
3. Generate comparison reports (JSON, Markdown, HTML)
4. Print summary to console

**Expected Duration**: 10-20 minutes per task (30-60 min total for 3 tasks)

---

## Command Reference

### `agentready harbor compare`

Run Harbor benchmark comparison.

**Options**:
- `-t, --task TASK_NAME` - Task to benchmark (required, repeatable)
- `--model MODEL` - Model identifier (default: `anthropic/claude-sonnet-4-5`)
- `--agent-file PATH` - Path to agent file (default: `.claude/agents/doubleagent.md`)
- `--output-dir DIR` - Output directory (default: `.agentready/harbor_comparisons`)
- `--verbose` - Print detailed Harbor output
- `--open-dashboard` - Open HTML dashboard after completion

**Example**:
```bash
agentready harbor compare \
  -t adaptive-rejection-sampler \
  -t async-http-client \
  --model anthropic/claude-sonnet-4-5 \
  --verbose \
  --open-dashboard
```

### `agentready harbor list`

List all Harbor comparisons in output directory.

**Example**:
```bash
agentready harbor list
```

**Output**:
```
Harbor comparisons in .agentready/harbor_comparisons:

  run_20251210_143022/
    Created:      2025-12-10T14:30:22
    Success Δ:    +33.3%
    Duration Δ:   -21.2%

  run_20251209_091545/
    Created:      2025-12-09T09:15:45
    Success Δ:    +16.7%
    Duration Δ:   -12.5%
```

### `agentready harbor view`

View a specific comparison.

**Usage**:
```bash
agentready harbor view .agentready/harbor_comparisons/comparison_latest.json
```

**Options**:
- `--format summary` - Print summary (default)
- `--format full` - Print full JSON

---

## Output Files

Each comparison generates multiple files in `.agentready/harbor_comparisons/run_TIMESTAMP/`:

### Directory Structure

```
.agentready/harbor_comparisons/
├── run_20251210_143022/
│   ├── without_agent/           # Harbor results without doubleagent.md
│   │   └── [task results]
│   ├── with_agent/              # Harbor results with doubleagent.md
│   │   └── [task results]
│   ├── comparison_20251210_143022.json  # Machine-readable data
│   ├── comparison_20251210_143022.md    # GitHub-Flavored Markdown
│   └── comparison_20251210_143022.html  # Interactive dashboard
├── comparison_latest.json       # Symlink to most recent JSON
├── comparison_latest.md         # Symlink to most recent Markdown
└── comparison_latest.html       # Symlink to most recent HTML
```

### JSON Report

Machine-readable comparison data for further analysis:

```json
{
  "without_agent": {
    "run_id": "without_20251210_143022",
    "agent_file_enabled": false,
    "success_rate": 66.7,
    "avg_duration_sec": 312.5,
    "total_tasks": 3,
    "successful_tasks": 2
  },
  "with_agent": {
    "run_id": "with_20251210_143022",
    "agent_file_enabled": true,
    "success_rate": 100.0,
    "avg_duration_sec": 246.3,
    "total_tasks": 3,
    "successful_tasks": 3
  },
  "deltas": {
    "success_rate_delta": 33.3,
    "avg_duration_delta_pct": -21.2
  },
  "statistical_significance": {
    "success_rate_significant": true,
    "success_rate_p_value": 0.0421,
    "duration_significant": true,
    "duration_p_value": 0.0312,
    "duration_cohens_d": -0.87
  }
}
```

### Markdown Report

GitHub-friendly report perfect for git commits and PRs:

```markdown
# Harbor Benchmark Comparison

**Created**: 2025-12-10T14:30:22
**Tasks**: 3 (adaptive-rejection-sampler, async-http-client, terminal-file-browser)

## Summary

| Metric | Without Agent | With Agent | Delta | Significant? |
|--------|--------------|------------|-------|--------------|
| Success Rate | 66.7% | 100.0% | +33.3% | ✓ (p=0.0421) |
| Avg Duration | 5.2 min | 4.1 min | -21.2% | ✓ (p=0.0312) |

## Per-Task Results

### adaptive-rejection-sampler
- **Without Agent**: ✗ Failed (timeout)
- **With Agent**: ✓ Success (3.8 min)
- **Impact**: +100% success (fixed failure)

...

## Conclusion

The `doubleagent.md` agent file shows **statistically significant improvement**
in both success rate (+33.3%, p=0.04) and execution speed (-21.2%, p=0.03).

**Recommendation**: ✅ **Include `doubleagent.md`** in AgentReady development workflows.
```

### HTML Dashboard

Interactive visualization with Chart.js:

- Side-by-side bar charts (success rates, durations)
- Per-task breakdown table
- Statistical significance indicators
- Self-contained (no external dependencies)

Open with:
```bash
open .agentready/harbor_comparisons/comparison_latest.html
```

---

## Interpreting Results

### Statistical Significance

**P-value < 0.05**: Statistically significant difference (95% confidence)
- ✓ Indicates real improvement, not random variation
- ✗ Difference could be due to chance

**Cohen's d (Effect Size)**:
- **0.2 ≤ |d| < 0.5**: Small effect
- **0.5 ≤ |d| < 0.8**: Medium effect
- **|d| ≥ 0.8**: Large effect

### Sample Size Requirements

- **Minimum**: 3 tasks for statistical tests
- **Recommended**: 5-10 tasks for reliable results
- **Comprehensive**: 20+ tasks for production validation

Small samples (n<3) will show warning about statistical validity.

### Recommendations

Based on comparison results:

| Outcome | Recommendation |
|---------|---------------|
| ✅ Success ↑, p<0.05 | **Include agent file** - Proven improvement |
| ⚠️ Success ↑, p≥0.05 | **Consider including** - Validate with larger sample |
| ❌ No improvement | **Agent file may not help** for tested tasks |

---

## Advanced Usage

### Custom Agent File

Test a different agent file:

```bash
agentready harbor compare \
  -t task1 -t task2 \
  --agent-file .claude/agents/custom-agent.md
```

### Custom Output Directory

Store results in specific location:

```bash
agentready harbor compare \
  -t task1 -t task2 \
  --output-dir experiments/harbor_results
```

### Different Model

Test with Claude Opus:

```bash
agentready harbor compare \
  -t task1 -t task2 \
  --model anthropic/claude-opus-4-5
```

---

## Troubleshooting

### Harbor Not Installed

**Error**: `Harbor framework not installed`

**Solution**:
```bash
uv tool install harbor
```

### Agent File Not Found

**Error**: `Agent file not found: .claude/agents/doubleagent.md`

**Solution**: Ensure agent file exists or specify custom path with `--agent-file`

### No Tasks Specified

**Error**: `At least one task must be specified with -t/--task`

**Solution**: Add tasks with `-t` flag:
```bash
agentready harbor compare -t adaptive-rejection-sampler
```

### Sample Size Too Small

**Warning**: `Sample size too small (n<3). Statistical tests may not be reliable.`

**Solution**: Run more tasks (5-10 recommended) for valid statistical analysis

### Task Timeout

Some tasks may timeout (30-60 min). This is normal for complex tasks. The comparison will continue with partial results.

---

## FAQ

**Q: How long does a comparison take?**

A: Approximately 10-20 minutes per task. For 3 tasks, expect 30-60 minutes total.

**Q: Can I run comparisons in parallel?**

A: Not currently supported. Future versions may support concurrent Harbor execution via Daytona/Modal.

**Q: What if some tasks fail?**

A: Comparison continues with partial results. Failed tasks are marked in reports and excluded from duration averages.

**Q: Can I compare more than 2 configurations?**

A: Currently supports only with/without agent file. Multi-configuration comparison is planned for future versions.

**Q: Where are results stored?**

A: `.agentready/harbor_comparisons/` (gitignored). Reports can be committed for reference, but raw Harbor results are excluded.

**Q: How do I share results with my team?**

A: Commit the Markdown report (`.md` file) or share the HTML dashboard. JSON files are machine-readable for further analysis.

---

## Related Documentation

- **Harbor Framework**: https://harborframework.com/docs
- **Terminal-Bench**: https://terminal-bench.com
- **AgentReady CLAUDE.md**: See "Harbor Comparison" section
- **Plan**: `.claude/plans/vivid-knitting-codd.md` (implementation details)

---

## Quickstart Example

```bash
# Install Harbor
uv tool install harbor

# Run comparison (3 tasks, ~30-60 min)
agentready harbor compare \
  -t adaptive-rejection-sampler \
  -t async-http-client \
  -t terminal-file-browser \
  --verbose \
  --open-dashboard

# View summary
agentready harbor view .agentready/harbor_comparisons/comparison_latest.json

# List all comparisons
agentready harbor list

# Open latest dashboard
open .agentready/harbor_comparisons/comparison_latest.html
```

---

**Last Updated**: 2025-12-10
**AgentReady Version**: 2.10.0+
