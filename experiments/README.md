# SWE-bench Experiments

Quantify AgentReady settings against SWE-bench baseline using both SWE-agent and Claude Code.

## Quick Start

```bash
# 1. Run agent on repository
agentready experiment run-agent sweagent \
  --repo-path /path/to/repo \
  --dataset lite \
  --output predictions_baseline_sweagent.jsonl

# 2. Evaluate predictions
agentready experiment evaluate \
  --predictions predictions_baseline_sweagent.jsonl \
  --output results_baseline_sweagent.json

# 3. Analyze and generate heatmap
agentready experiment analyze \
  --results-dir results/ \
  --heatmap heatmap.html

# 4. View interactive heatmap
open heatmap.html
```

## Pre-configured Experiments

Five configurations available in `configs/`:

1. **baseline.yaml** - No AgentReady changes (control)
2. **claude-md.yaml** - CLAUDE.md only (Tier 1 essential)
3. **types-docs.yaml** - Type annotations + inline documentation
4. **tier1.yaml** - All 5 Tier 1 attributes
5. **full-bootstrap.yaml** - All AgentReady best practices

## Manual Workflow

### Step 1: Prepare Repositories

```bash
# Create experiment repos
mkdir -p repos
cp -r /path/to/original/repo repos/baseline
cp -r /path/to/original/repo repos/claude-md
cp -r /path/to/original/repo repos/tier1
cp -r /path/to/original/repo repos/full-bootstrap

# Apply AgentReady changes
cd repos/claude-md && agentready align . --attributes claude_md_file && cd ../..
cd repos/tier1 && agentready align . --attributes claude_md_file,readme_structure,type_annotations,standard_layout,lock_files && cd ../..
cd repos/full-bootstrap && agentready bootstrap . && cd ../..
```

### Step 2: Run Experiments

```bash
# Create results directory
mkdir -p results

# Run SWE-agent on each config
agentready experiment run-agent sweagent --repo-path repos/baseline --dataset lite --output results/baseline_sweagent.jsonl
agentready experiment run-agent sweagent --repo-path repos/claude-md --dataset lite --output results/claudemd_sweagent.jsonl
agentready experiment run-agent sweagent --repo-path repos/tier1 --dataset lite --output results/tier1_sweagent.jsonl
agentready experiment run-agent sweagent --repo-path repos/full-bootstrap --dataset lite --output results/full_sweagent.jsonl

# Run Claude Code on each config (requires tasks file)
# Note: Claude Code runner needs task-specific workflow
```

### Step 3: Evaluate

```bash
# Evaluate each prediction set
agentready experiment evaluate --predictions results/baseline_sweagent.jsonl --output results/baseline_sweagent.json
agentready experiment evaluate --predictions results/claudemd_sweagent.jsonl --output results/claudemd_sweagent.json
agentready experiment evaluate --predictions results/tier1_sweagent.jsonl --output results/tier1_sweagent.json
agentready experiment evaluate --predictions results/full_sweagent.jsonl --output results/full_sweagent.json
```

### Step 4: Analyze & Visualize

```bash
# Generate correlation analysis and interactive heatmap
agentready experiment analyze \
  --results-dir results/ \
  --output analysis.json \
  --heatmap heatmap.html

# View results
cat analysis.json
open heatmap.html
```

## Output Files

**Predictions** (`*.jsonl`):
- SWE-bench format with instance_id, model, and patch
- Input for evaluation harness

**Results** (`*.json`):
```json
{
  "config_name": "claude-md",
  "agent": "sweagent",
  "agentready_score": 78.3,
  "swebench_score": 45.2,
  "solved": 136,
  "total": 300
}
```

**Analysis** (`analysis.json`):
```json
{
  "correlation": {
    "overall": 0.87,
    "p_value": 0.0001
  },
  "top_attributes": [
    {"config": "claude-md", "avg_improvement": 7.0}
  ]
}
```

**Heatmap** (`heatmap.html`):
- Interactive Plotly visualization
- Hover: Shows config, agent, score, delta from baseline
- Zoom/pan: Built-in
- Standalone HTML (no dependencies)

## SWE-bench Datasets

- **Lite**: 300 tasks (~15-30 min with cache)
- **Full**: 2,294 tasks (~2-4 hours)

## Dependencies

```bash
uv pip install swebench sweagent plotly pandas scipy
```

## Expected Results

Based on sample data, AgentReady improvements should correlate with SWE-bench performance:

- **Baseline**: ~38-39% pass rate
- **CLAUDE.md only**: +7-8pp improvement
- **Full bootstrap**: +14pp improvement

## Next Steps

1. Run experiments on your repositories
2. Analyze which attributes provide best ROI
3. Use findings to prioritize AgentReady improvements
4. Share results with Red Hat AI engineering team
