---
layout: default
title: Terminal-Bench Evaluation Methodology
description: Detailed explanation of AgentReady's A/B testing methodology for measuring assessor impact on Terminal-Bench performance
---

# Terminal-Bench Evaluation Methodology

**Systematic A/B testing to measure the impact of AgentReady assessors on agentic development performance**

---

## Table of Contents

- [Overview](#overview)
- [Research Question](#research-question)
- [A/B Testing Workflow](#ab-testing-workflow)
- [Statistical Methods](#statistical-methods)
- [Interpreting Results](#interpreting-results)
- [Limitations](#limitations)
- [Scientific Validity](#scientific-validity)
- [Examples](#examples)
- [FAQ](#faq)

---

## Overview

The AgentReady Eval Harness uses **systematic A/B testing** to empirically measure whether implementing AgentReady's best practices actually improves a repository's performance on [Terminal-Bench](https://tbench.ai) - a benchmark for agentic coding capabilities.

### Key Principles

1. **Evidence-Based**: Empirical measurement replaces assumptions
2. **Systematic**: Each assessor tested independently for isolated impact
3. **Statistical Rigor**: P-values and effect sizes ensure validity
4. **Transparent**: Methodology and results publicly available

---

## Research Question

**Primary Question**: Do AgentReady's best practices improve agentic development performance?

**Specific Questions**:
- Which attributes have the largest impact on Terminal-Bench scores?
- Are higher-tier attributes more impactful than lower-tier ones?
- Do certain assessor combinations create synergistic effects?
- How does repository type (Python vs JavaScript vs Go) affect impact?

---

## A/B Testing Workflow

### Phase 1: Establish Baseline

**Goal**: Measure repository performance before any remediation

**Process**:
1. Run Terminal-Bench on unmodified repository
2. Repeat for N iterations (default: 5)
3. Calculate mean score and standard deviation
4. Store baseline metrics for comparison

**Output**:
```
Baseline: 73.4 ± 2.5 (n=5)
```

---

### Phase 2: Test Individual Assessors

**Goal**: Measure impact of each assessor independently

**For Each Assessor**:

1. **Clone Repository** to fresh temporary directory
2. **Run Single Assessor** assessment (exclude all others)
3. **Apply Remediation** using `agentready align` command
4. **Run Terminal-Bench** post-remediation (N iterations)
5. **Calculate Delta** from baseline
6. **Statistical Analysis** (t-test, effect size)
7. **Store Results** in assessor-specific directory

**Key Design Choice**: Test assessors **individually** rather than cumulatively to isolate each attribute's specific impact.

---

### Phase 3: Aggregate Results

**Goal**: Rank assessors by impact and identify patterns

**Process**:
1. Load all assessor impact results
2. Rank by delta score (highest to lowest)
3. Calculate tier-level averages
4. Identify statistically significant improvements
5. Generate summary report

**Output**:
- Ranked assessor list
- Tier impact analysis
- Significance statistics

---

## Statistical Methods

### Significance Criteria

An assessor's impact is considered **statistically significant** if **BOTH** conditions are met:

1. **P-value < 0.05** (95% confidence that result is not due to chance)
2. **|Cohen's d| > 0.2** (meaningful effect size, not just statistical noise)

### T-Test

**Purpose**: Determine if the difference between baseline and post-remediation scores is statistically significant

**Method**: Two-sample t-test comparing:
- Baseline scores (n=5)
- Post-remediation scores (n=5)

**Formula**:
```
t = (mean_post - mean_baseline) / sqrt((sd_baseline²/n + sd_post²/n))
```

**Interpretation**:
- **p < 0.01**: Very strong evidence of impact
- **p < 0.05**: Strong evidence of impact
- **p ≥ 0.05**: Insufficient evidence (may still have small effect)

### Effect Size (Cohen's d)

**Purpose**: Measure the *magnitude* of impact (independent of sample size)

**Formula**:
```
d = (mean_post - mean_baseline) / pooled_std_dev
```

**Interpretation**:
- **|d| < 0.2**: Negligible effect
- **0.2 ≤ |d| < 0.5**: Small effect
- **0.5 ≤ |d| < 0.8**: Medium effect
- **|d| ≥ 0.8**: Large effect

**Why Both Metrics?**
- **P-value** tells us if the effect is real (not random)
- **Effect size** tells us if the effect is meaningful (large enough to matter)

A large sample can make tiny effects significant (low p-value, small d).
A small sample can miss large effects (high p-value, large d).
We require both to ensure results are both real AND meaningful.

---

## Interpreting Results

### Dashboard Metrics Explained

#### Delta Score
**What**: Change in Terminal-Bench score after applying assessor remediation

**Range**: -100 to +100 (percentage points)

**Examples**:
- `+5.2`: Improvement of 5.2 percentage points
- `-1.3`: Decrease of 1.3 percentage points
- `0.0`: No measurable change

**Interpretation**:
- `+10 or more`: Major improvement
- `+5 to +9.9`: Substantial improvement
- `+1 to +4.9`: Modest improvement
- `-1 to +1`: No meaningful change
- `Below -1`: Regression (remediation may have introduced issues)

#### Significance Status

**✅ Significant**: Both p < 0.05 AND |d| > 0.2
→ *High confidence this assessor has meaningful impact*

**❌ Not Significant**: Either p ≥ 0.05 OR |d| ≤ 0.2
→ *Insufficient evidence of meaningful impact (may still help, but not proven)*

#### Tier Impact

**What**: Average delta score for all assessors in a tier

**Purpose**: Validate that higher-priority tiers have larger impact

**Expected Pattern** (hypothesis):
- **Tier 1 (Essential)**: Highest average impact
- **Tier 2 (Critical)**: High impact
- **Tier 3 (Important)**: Moderate impact
- **Tier 4 (Advanced)**: Lower impact

If this pattern holds, it validates AgentReady's tier prioritization.

---

## Limitations

### Current Phase (Mocked Terminal-Bench)

**Status**: Phase 1 uses **mocked** Terminal-Bench results for workflow validation

**Limitations**:
1. Scores are simulated (deterministic randomness based on repo characteristics)
2. Cannot submit to real Terminal-Bench leaderboard
3. Delta scores are indicative, not actual performance measurements

**Mitigation**: Real Terminal-Bench integration planned for Phase 2

### Statistical Limitations

1. **Small Sample Size**: Default n=5 iterations (balances cost vs. statistical power)
2. **Isolated Testing**: Assessors tested individually (doesn't capture synergistic effects)
3. **Repository Specificity**: Impact may vary by repo type, size, and domain
4. **Temporal Validity**: Terminal-Bench evolves; results may change over time

### Causation vs. Correlation

While A/B testing establishes **correlation** between remediation and score changes, it doesn't prove direct **causation**. Confounding factors (repo complexity, language choice, etc.) may influence results.

---

## Scientific Validity

### Validity Criteria

✅ **Randomness Control**: Deterministic mocking uses repo hash as seed (reproducible)
✅ **Baseline Variance**: Low std dev ensures stable baseline (<10% of mean)
✅ **Statistical Testing**: Both p-values and effect sizes reported
✅ **Transparency**: Full methodology and raw data available
✅ **Repeatability**: Same repo produces same baseline scores

### Confidence Intervals

Future enhancement: Display 95% confidence intervals for delta scores

**Example**:
```
Delta: +5.2 [95% CI: +2.1 to +8.3]
```

This means we're 95% confident the true impact is between +2.1 and +8.3 points.

---

## Examples

### Example 1: Significant Positive Impact

```
Assessor: CLAUDE.md File (claude_md_file)
Tier: 1 (Essential)
Baseline: 73.4 ± 2.5
Post-Remediation: 78.6 ± 2.1
Delta: +5.2
P-value: 0.03
Effect Size (d): 0.62 (medium)
Status: ✅ Significant

Interpretation:
Adding a CLAUDE.md file improved Terminal-Bench performance by 5.2 percentage
points with high statistical confidence (p=0.03) and medium effect size (d=0.62).
This is strong evidence that CLAUDE.md helps AI agents understand codebases.
```

### Example 2: Non-Significant Result

```
Assessor: API Documentation Coverage
Tier: 3 (Important)
Baseline: 73.4 ± 2.5
Post-Remediation: 74.1 ± 3.2
Delta: +0.7
P-value: 0.48
Effect Size (d): 0.09 (negligible)
Status: ❌ Not Significant

Interpretation:
Adding API documentation showed a small improvement (+0.7), but the result is
not statistically significant (p=0.48) and has negligible effect size (d=0.09).
We cannot confidently say this assessor improves Terminal-Bench performance,
though it may still provide other benefits (e.g., human readability).
```

### Example 3: Negative Impact (Regression)

```
Assessor: Example Configuration File
Tier: 4 (Advanced)
Baseline: 73.4 ± 2.5
Post-Remediation: 71.8 ± 2.3
Delta: -1.6
P-value: 0.12
Effect Size (d): -0.28 (small)
Status: ❌ Not Significant (but concerning)

Interpretation:
Adding example configuration actually decreased performance by 1.6 points.
While not statistically significant (p=0.12), the effect size is small (d=-0.28),
suggesting this might be a real regression. Further investigation needed.
```

---

## FAQ

### Q: Why test assessors individually instead of cumulatively?

**A**: Individual testing isolates each assessor's specific impact. Cumulative testing would make it impossible to determine which improvements came from which assessors.

**Trade-off**: We may miss synergistic effects (e.g., CLAUDE.md + tests working better together than individually).

**Future Work**: Phase 5 will include combination testing for synergy detection.

---

### Q: Why 5 iterations instead of more?

**A**: Balances statistical power with computational cost.

- **Fewer iterations** (n=3): Faster but less reliable
- **More iterations** (n=10+): More reliable but expensive
- **n=5**: Good compromise for initial validation

With Terminal-Bench runs taking ~10-30 minutes each, n=5 means ~50-150 minutes per assessor test. For 25 assessors, that's 20-60 hours total.

---

### Q: Can I trust mocked results?

**A**: **For workflow validation: Yes. For real performance claims: No.**

Mocked results prove the eval harness **works correctly** and produces **internally consistent** measurements. However, they don't represent actual Terminal-Bench performance.

Phase 2 will replace mocks with real Terminal-Bench integration.

---

### Q: What if an assessor shows negative impact?

**A**: This could indicate:
1. **Random variance** (check p-value and effect size)
2. **Implementation issue** (remediation may have introduced bugs)
3. **Terminal-Bench limitation** (benchmark may not value that attribute)
4. **Over-optimization** (e.g., too much documentation slows parsing)

Investigate regression results carefully before concluding the assessor is harmful.

---

### Q: How do I run my own evaluation?

**A**: See the [Eval Harness User Guide](/agentready/eval-harness-guide) for step-by-step instructions.

**Quick Start**:
```bash
# 1. Establish baseline
agentready eval-harness baseline

# 2. Test all Tier 1 assessors
agentready eval-harness run-tier --tier 1

# 3. Generate dashboard
agentready eval-harness dashboard

# 4. View results
open docs/_data/tbench/summary.json
```

---

## Related Resources

- [Terminal-Bench Official Site](https://tbench.ai)
- [Eval Harness User Guide](/agentready/eval-harness-guide)
- [AgentReady Attributes](/agentready/attributes)
- [GitHub Repository](https://github.com/ambient-code/agentready)

---

**Last Updated**: 2025-12-06
**Version**: 1.0.0 (Phase 1 - Mocked Terminal-Bench)
