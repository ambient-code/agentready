# 🚀 Eval Harness Quick Reference

## Commands

### 1. Establish Baseline
```bash
agentready eval-harness baseline . --iterations 3 --verbose
```
**Output**: Baseline score (mean ± std dev) from 3 Terminal-Bench runs
**Files**: `.agentready/eval_harness/baseline/summary.json` + 3 run files

---

### 2. Test Single Assessor
```bash
agentready eval-harness test-assessor --assessor-id claude_md_file --iterations 3 --verbose
```
**Output**: Delta score, p-value, effect size, significance status
**Files**: `.agentready/eval_harness/assessors/claude_md_file/impact.json` + 3 run files

---

### 3. Test All Tier 1 Assessors
```bash
agentready eval-harness run-tier --tier 1 --iterations 3 --verbose
```
**Output**: Tests all 5 Tier 1 assessors sequentially
**Files**: Impact files for each assessor in `assessors/*/`

---

### 4. Aggregate Results
```bash
agentready eval-harness summarize --verbose
```
**Output**: Ranked list of assessors by impact, tier statistics
**Files**: `.agentready/eval_harness/summary.json`

---

### 5. Generate Dashboard
```bash
agentready eval-harness dashboard --verbose
```
**Output**: 5 Jekyll-compatible JSON files for GitHub Pages
**Files**: `docs/_data/tbench/{summary,ranked_assessors,tier_impacts,baseline,stats}.json`

---

## File Structure

```
.agentready/eval_harness/
├── baseline/
│   ├── run_001.json
│   ├── run_002.json
│   ├── run_003.json
│   └── summary.json
├── assessors/
│   ├── claude_md_file/
│   │   ├── run_001.json
│   │   ├── run_002.json
│   │   ├── run_003.json
│   │   └── impact.json
│   └── .../
└── summary.json

docs/_data/tbench/
├── summary.json           (5.7 KB)
├── ranked_assessors.json  (2.2 KB)
├── tier_impacts.json      (282 B)
├── baseline.json          (131 B)
└── stats.json            (139 B)
```

---

## Statistical Criteria

### Significance
**Statistically Significant** if BOTH:
- P-value < 0.05 (95% confidence)
- |Cohen's d| > 0.2 (meaningful effect size)

### Effect Size
- |d| < 0.2: **Negligible**
- 0.2 ≤ |d| < 0.5: **Small**
- 0.5 ≤ |d| < 0.8: **Medium**
- |d| ≥ 0.8: **Large**

---

## Example Output

### Baseline
```
✅ Baseline established successfully!

Results:
  Mean Score:   58.35
  Std Dev:      0.00
  Median:       58.35
  Min:          58.35
  Max:          58.35
  Iterations:   3
```

### Assessor Test
```
📊 Results:
  Assessor:          CLAUDE.md Configuration Files (Tier 1)
  Baseline Score:    58.35
  Post-Fix Score:    58.35
  Delta:             +0.00 points
  P-value:           nan
  Effect Size (d):   0.000
  Significant:       ❌ NO
  Effect Magnitude:  negligible
```

### Summary
```
🏆 Assessors Ranked by Impact:
   1. Type Annotations                    +0.00 | Sig: ❌ | Fixes: 0
   2. CLAUDE.md Configuration Files       +0.00 | Sig: ❌ | Fixes: 0
   3. Standard Project Layouts            +0.00 | Sig: ❌ | Fixes: 0
   4. Lock Files for Reproducibility      +0.00 | Sig: ❌ | Fixes: 0
   5. README Structure                    +0.00 | Sig: ❌ | Fixes: 0
```

---

## Dashboard Views

### Overview Cards
- Total Assessors Tested: **5**
- Significant Improvements: **0**
- Significance Rate: **0%**
- Baseline Score: **58.35**

### Tier Impact Chart
Chart.js bar chart showing average delta by tier (all +0.00 in demo)

### Complete Results Table
Sortable table with:
- Rank, Assessor, Tier
- Delta, Effect Size, P-value
- Significance Status

---

## Test Status

```bash
pytest tests/unit/test_eval_harness*.py tests/integration/test_eval_harness*.py -v
```

**Result**: 56/56 tests passing ✅
- 6 CLI tests
- 13 model tests
- 32 service tests
- 5 integration tests

---

## Next Steps

### Phase 1 (Complete) ✅
- Mocked Terminal-Bench integration
- CLI commands
- Dashboard
- Tests
- Documentation

### Phase 2 (Next)
- Real Terminal-Bench integration
- Harbor framework client
- Actual benchmark submissions

### Backlog
- GitHub Actions automation
- Scale to all 25 assessors
- Advanced analytics

---

**Quick Start**: `agentready eval-harness --help`
**Full Demo**: See `DEMO_EVAL_HARNESS.md`
**Summary**: See `DEMO_SUMMARY.md`
