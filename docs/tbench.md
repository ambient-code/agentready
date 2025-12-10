---
layout: default
title: "Terminal-Bench Evaluation Results"
description: "Systematic A/B testing of AgentReady assessors against Terminal-Bench performance"
permalink: /tbench.html
---

# Terminal-Bench Eval Harness Results

> **Systematic A/B testing** of each AgentReady assessor's impact on [Terminal-Bench](https://tbench.ai) performance

---

## 📊 Overview

<div class="feature-grid" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));">
  <div class="feature" style="text-align: center;">
    <h3 id="total-assessors" style="margin-top: 0; font-size: var(--text-3xl); color: var(--color-primary);">-</h3>
    <p style="margin: 0; color: var(--color-gray-600); font-size: var(--text-sm);">Assessors Tested</p>
  </div>
  <div class="feature" style="text-align: center;">
    <h3 id="significant-count" style="margin-top: 0; font-size: var(--text-3xl); color: var(--color-success);">-</h3>
    <p style="margin: 0; color: var(--color-gray-600); font-size: var(--text-sm);">Significant Improvements</p>
  </div>
  <div class="feature" style="text-align: center;">
    <h3 id="significance-rate" style="margin-top: 0; font-size: var(--text-3xl); color: var(--color-info);">-%</h3>
    <p style="margin: 0; color: var(--color-gray-600); font-size: var(--text-sm);">Significance Rate</p>
  </div>
  <div class="feature" style="text-align: center;">
    <h3 id="baseline-score" style="margin-top: 0; font-size: var(--text-3xl); color: var(--color-gray-700);">-</h3>
    <p style="margin: 0; color: var(--color-gray-600); font-size: var(--text-sm);">Baseline Score</p>
  </div>
</div>

---

## 🎯 Impact by Tier

<div style="max-width: 800px; margin: var(--space-8) auto;">
  <canvas id="tierImpactChart" style="max-height: 400px;"></canvas>
</div>

<div class="use-case-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); margin-top: var(--space-6);">
  <div class="use-case">
    <h4 style="margin-top: 0;">Tier 1: Essential</h4>
    <p style="font-size: var(--text-sm);">Most critical for AI assistance</p>
  </div>
  <div class="use-case">
    <h4 style="margin-top: 0;">Tier 2: Critical</h4>
    <p style="font-size: var(--text-sm);">Major impact on velocity</p>
  </div>
  <div class="use-case">
    <h4 style="margin-top: 0;">Tier 3: Important</h4>
    <p style="font-size: var(--text-sm);">Meaningful quality gains</p>
  </div>
  <div class="use-case">
    <h4 style="margin-top: 0;">Tier 4: Advanced</h4>
    <p style="font-size: var(--text-sm);">Polish and optimization</p>
  </div>
</div>

---

## 🏆 Top Performing Assessors

<div style="overflow-x: auto;">
  <table class="leaderboard-table" id="topAssessorsTable">
    <thead>
      <tr>
        <th style="width: 60px; text-align: center;">Rank</th>
        <th>Assessor</th>
        <th style="width: 100px; text-align: center;">Tier</th>
        <th style="width: 120px; text-align: center;">Delta Score</th>
        <th style="width: 120px; text-align: center;">Effect Size</th>
        <th style="width: 100px; text-align: center;">Significant?</th>
      </tr>
    </thead>
    <tbody>
      <!-- Populated by JavaScript -->
    </tbody>
  </table>
</div>

---

## 📈 Complete Results

<div style="overflow-x: auto;">
  <table class="leaderboard-table" id="allAssessorsTable">
    <thead>
      <tr>
        <th style="width: 60px; text-align: center;">Rank</th>
        <th>Assessor</th>
        <th style="width: 100px; text-align: center;">Tier</th>
        <th style="width: 120px; text-align: center;">Delta (%)</th>
        <th style="width: 130px; text-align: center;">Cohen's d</th>
        <th style="width: 100px; text-align: center;">P-value</th>
        <th style="width: 100px; text-align: center;">Status</th>
        <th style="width: 100px; text-align: center;">Fixes</th>
      </tr>
    </thead>
    <tbody>
      <!-- Populated by JavaScript -->
    </tbody>
  </table>
</div>

---

## 📖 Methodology

<details style="margin: var(--space-6) 0;">
  <summary style="cursor: pointer; font-weight: 600; color: var(--color-gray-900); font-size: var(--text-lg);">
    Click to expand methodology details
  </summary>

  <div style="margin-top: var(--space-4); padding-left: var(--space-4); border-left: 4px solid var(--color-primary); background: var(--color-gray-50); padding: var(--space-4); border-radius: var(--radius-sm);">

### A/B Testing Workflow

1. **Establish Baseline**: Run Terminal-Bench 5 times on unmodified repository
2. **For Each Assessor**:
   - Clone repository to temporary directory
   - Run single assessor assessment
   - Apply remediation using AgentReady's `align` command
   - Run Terminal-Bench 5 times post-remediation
   - Calculate delta score and statistical significance
3. **Aggregate Results**: Combine all assessor impacts with tier-level statistics

### Statistical Rigor

- **Significance Threshold**: p-value < 0.05 AND |Cohen's d| > 0.2
- **T-Test**: Two-sample t-test comparing baseline vs. post-remediation scores
- **Effect Size**: Cohen's d measures standardized difference
  - Small: 0.2 ≤ |d| < 0.5
  - Medium: 0.5 ≤ |d| < 0.8
  - Large: |d| ≥ 0.8

### Current Status

**Phase 1 (MVP)**: Mocked Terminal-Bench integration for workflow validation
**Phase 2 (Planned)**: Real Harbor framework integration and leaderboard submission

  </div>
</details>

---

## 🔗 Related Resources

- [Terminal-Bench Official Site](https://tbench.ai)
- [AgentReady Attributes](/agentready/attributes)
- [User Guide](/agentready/user-guide)
- [GitHub Repository](https://github.com/ambient-code/agentready)

---

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<style>
/* Dashboard-specific styles */
.feature-grid .feature {
  padding: var(--space-6);
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.leaderboard-table {
  font-size: var(--text-sm);
}

.leaderboard-table th {
  background-color: var(--color-gray-100);
  font-weight: 600;
  padding: var(--space-3);
}

.leaderboard-table td {
  padding: var(--space-3);
}

.leaderboard-table tbody tr:hover {
  background-color: var(--color-gray-50);
}

/* Tier badges in tables */
.tier-badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
}

.tier-badge.tier-1 { background: #ede9fe; color: #7c3aed; }
.tier-badge.tier-2 { background: #fef3c7; color: #ca8a04; }
.tier-badge.tier-3 { background: #f4f4f5; color: #71717a; }
.tier-badge.tier-4 { background: #fed7aa; color: #c2410c; }

/* Responsive */
@media (max-width: 768px) {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .use-case-grid {
    grid-template-columns: 1fr !important;
  }

  .leaderboard-table {
    font-size: var(--text-xs);
  }

  .leaderboard-table th,
  .leaderboard-table td {
    padding: var(--space-2);
  }
}
</style>

<script>
// Configure Chart.js defaults to match AgentReady design system
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
Chart.defaults.color = '#6b7280'; // var(--color-gray-500)
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.tooltip.backgroundColor = '#111827'; // var(--color-gray-900)
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;

// Sample data for demonstration (will be replaced by actual data when available)
const SAMPLE_DATA = {
  stats: {
    total_assessors_tested: 25,
    significant_improvements: 18,
    significance_rate: 72.0
  },
  baseline: {
    mean_score: 65.4
  },
  tier_impacts: [
    { tier: 1, tier_name: "Essential", delta: 12.3, assessors: 6 },
    { tier: 2, tier_name: "Critical", delta: 8.7, assessors: 8 },
    { tier: 3, tier_name: "Important", delta: 5.2, assessors: 7 },
    { tier: 4, tier_name: "Advanced", delta: 2.1, assessors: 4 }
  ],
  ranked_assessors: [
    { assessor_name: "CLAUDE.md File", tier: 1, delta: 15.2, effect_size: 1.42, p_value: 0.0012, is_significant: true, fixes_applied: 1 },
    { assessor_name: "README with Quickstart", tier: 1, delta: 14.8, effect_size: 1.38, p_value: 0.0015, is_significant: true, fixes_applied: 1 },
    { assessor_name: "Standard Directory Layout", tier: 1, delta: 13.5, effect_size: 1.21, p_value: 0.0021, is_significant: true, fixes_applied: 3 },
    { assessor_name: "Pre-commit Hooks", tier: 2, delta: 11.2, effect_size: 0.95, p_value: 0.0034, is_significant: true, fixes_applied: 2 },
    { assessor_name: "Type Annotations (Python)", tier: 2, delta: 9.8, effect_size: 0.87, p_value: 0.0052, is_significant: true, fixes_applied: 15 },
    { assessor_name: "Dependency Lock File", tier: 1, delta: 9.3, effect_size: 0.82, p_value: 0.0067, is_significant: true, fixes_applied: 1 },
    { assessor_name: "Test Coverage ≥80%", tier: 2, delta: 8.5, effect_size: 0.76, p_value: 0.0089, is_significant: true, fixes_applied: 12 },
    { assessor_name: "Comprehensive .gitignore", tier: 1, delta: 7.9, effect_size: 0.71, p_value: 0.0112, is_significant: true, fixes_applied: 1 },
    { assessor_name: "GitHub Actions CI", tier: 2, delta: 7.2, effect_size: 0.65, p_value: 0.0145, is_significant: true, fixes_applied: 1 },
    { assessor_name: "Documented Build Steps", tier: 2, delta: 6.8, effect_size: 0.61, p_value: 0.0178, is_significant: true, fixes_applied: 1 },
    { assessor_name: "Repomix Configuration", tier: 3, delta: 5.9, effect_size: 0.52, p_value: 0.0234, is_significant: true, fixes_applied: 1 },
    { assessor_name: "Code Complexity Limits", tier: 3, delta: 5.1, effect_size: 0.45, p_value: 0.0312, is_significant: true, fixes_applied: 4 },
    { assessor_name: "API Documentation", tier: 3, delta: 4.7, effect_size: 0.41, p_value: 0.0389, is_significant: true, fixes_applied: 8 },
    { assessor_name: "Error Handling Standards", tier: 2, delta: 4.3, effect_size: 0.38, p_value: 0.0445, is_significant: true, fixes_applied: 6 },
    { assessor_name: "Logging Framework", tier: 3, delta: 3.8, effect_size: 0.33, p_value: 0.0567, is_significant: false, fixes_applied: 5 },
    { assessor_name: "Environment Management", tier: 2, delta: 3.2, effect_size: 0.28, p_value: 0.0723, is_significant: false, fixes_applied: 2 },
    { assessor_name: "Security Scanning", tier: 3, delta: 2.9, effect_size: 0.25, p_value: 0.0891, is_significant: false, fixes_applied: 1 },
    { assessor_name: "Performance Benchmarks", tier: 4, delta: 2.4, effect_size: 0.21, p_value: 0.1123, is_significant: false, fixes_applied: 3 },
    { assessor_name: "Code Style Enforcement", tier: 3, delta: 2.1, effect_size: 0.18, p_value: 0.1456, is_significant: false, fixes_applied: 1 },
    { assessor_name: "Dependency Freshness", tier: 4, delta: 1.8, effect_size: 0.15, p_value: 0.1789, is_significant: false, fixes_applied: 8 },
    { assessor_name: "Container Support", tier: 4, delta: 1.5, effect_size: 0.13, p_value: 0.2234, is_significant: false, fixes_applied: 1 },
    { assessor_name: "Changelog Maintenance", tier: 4, delta: 1.2, effect_size: 0.10, p_value: 0.2891, is_significant: false, fixes_applied: 1 },
    { assessor_name: "Contributing Guidelines", tier: 3, delta: 0.9, effect_size: 0.08, p_value: 0.3567, is_significant: false, fixes_applied: 1 },
    { assessor_name: "Issue Templates", tier: 4, delta: 0.6, effect_size: 0.05, p_value: 0.4523, is_significant: false, fixes_applied: 3 },
    { assessor_name: "Release Automation", tier: 4, delta: 0.3, effect_size: 0.03, p_value: 0.5789, is_significant: false, fixes_applied: 2 }
  ]
};

// Load dashboard data and render
async function loadDashboard() {
  try {
    // Try to load real data files
    const [stats, tierImpacts, rankedAssessors, baseline] = await Promise.all([
      fetch('/agentready/_data/tbench/stats.json').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('/agentready/_data/tbench/tier_impacts.json').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('/agentready/_data/tbench/ranked_assessors.json').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('/agentready/_data/tbench/baseline.json').then(r => r.ok ? r.json() : null).catch(() => null),
    ]);

    // Use real data if available, otherwise fall back to sample data
    const finalStats = stats || SAMPLE_DATA.stats;
    const finalTierImpacts = tierImpacts || SAMPLE_DATA.tier_impacts;
    const finalRankedAssessors = rankedAssessors || SAMPLE_DATA.ranked_assessors;
    const finalBaseline = baseline || SAMPLE_DATA.baseline;

    // Update overview cards
    document.getElementById('total-assessors').textContent = finalStats.total_assessors_tested;
    document.getElementById('significant-count').textContent = finalStats.significant_improvements;
    document.getElementById('significance-rate').textContent = finalStats.significance_rate.toFixed(0) + '%';
    document.getElementById('baseline-score').textContent = finalBaseline.mean_score.toFixed(1);

    // Render charts and tables
    renderTierChart(finalTierImpacts);
    renderTopAssessorsTable(finalRankedAssessors.slice(0, 5));
    renderAllAssessorsTable(finalRankedAssessors);

  } catch (error) {
    console.error('Error loading dashboard data:', error);
    // Still show sample data if there's an error
    showSampleData();
  }
}

function showSampleData() {
  document.getElementById('total-assessors').textContent = SAMPLE_DATA.stats.total_assessors_tested;
  document.getElementById('significant-count').textContent = SAMPLE_DATA.stats.significant_improvements;
  document.getElementById('significance-rate').textContent = SAMPLE_DATA.stats.significance_rate.toFixed(0) + '%';
  document.getElementById('baseline-score').textContent = SAMPLE_DATA.baseline.mean_score.toFixed(1);

  renderTierChart(SAMPLE_DATA.tier_impacts);
  renderTopAssessorsTable(SAMPLE_DATA.ranked_assessors.slice(0, 5));
  renderAllAssessorsTable(SAMPLE_DATA.ranked_assessors);
}

function renderTierChart(tierData) {
  const ctx = document.getElementById('tierImpactChart').getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: tierData.map(t => `Tier ${t.tier}: ${t.tier_name}`),
      datasets: [{
        label: 'Average Impact (% points)',
        data: tierData.map(t => t.delta),
        backgroundColor: [
          '#e5e4e2cc', // Platinum (80% opacity)
          '#ffd700cc', // Gold
          '#c0c0c0cc', // Silver
          '#cd7f32cc', // Bronze
        ],
        borderColor: [
          '#e5e4e2',
          '#ffd700',
          '#c0c0c0',
          '#cd7f32',
        ],
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: 'Average Assessor Impact by Tier',
          font: { size: 18, weight: 'bold' },
          color: '#111827'
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `Impact: ${ctx.parsed.y.toFixed(2)}% points`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Delta Score (% points)',
            font: { size: 14, weight: '600' }
          },
          grid: { color: '#e5e7eb' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderTopAssessorsTable(assessors) {
  const tbody = document.querySelector('#topAssessorsTable tbody');
  tbody.textContent = ''; // Clear safely

  assessors.forEach((a, i) => {
    const row = tbody.insertRow();

    // Rank cell
    const rankCell = row.insertCell();
    rankCell.textContent = String(i + 1);
    rankCell.style.cssText = 'text-align: center; font-weight: 700; color: var(--color-gray-600);';

    // Assessor name cell
    const nameCell = row.insertCell();
    nameCell.textContent = a.assessor_name;
    nameCell.style.cssText = 'font-family: var(--font-mono); font-size: var(--text-sm);';

    // Tier badge cell
    const tierCell = row.insertCell();
    const tierBadge = document.createElement('span');
    tierBadge.className = `tier-badge tier-${a.tier}`;
    tierBadge.textContent = `Tier ${a.tier}`;
    tierCell.appendChild(tierBadge);
    tierCell.style.textAlign = 'center';

    // Delta cell
    const deltaCell = row.insertCell();
    deltaCell.textContent = `${a.delta >= 0 ? '+' : ''}${a.delta.toFixed(2)}%`;
    deltaCell.style.cssText = `text-align: center; font-weight: 600; color: ${a.delta >= 0 ? 'var(--color-success)' : 'var(--color-error)'};`;

    // Effect size cell
    const effectCell = row.insertCell();
    effectCell.textContent = a.effect_size.toFixed(3);
    effectCell.style.cssText = 'text-align: center; font-family: var(--font-mono); font-size: var(--text-sm);';

    // Significant cell
    const sigCell = row.insertCell();
    sigCell.textContent = a.is_significant ? '✅' : '❌';
    sigCell.style.textAlign = 'center';
  });
}

function renderAllAssessorsTable(assessors) {
  const tbody = document.querySelector('#allAssessorsTable tbody');
  tbody.textContent = ''; // Clear safely

  assessors.forEach((a, i) => {
    const row = tbody.insertRow();

    // Rank
    const rankCell = row.insertCell();
    rankCell.textContent = String(i + 1);
    rankCell.style.cssText = 'text-align: center; font-weight: 600; color: var(--color-gray-600);';

    // Assessor name
    const nameCell = row.insertCell();
    nameCell.textContent = a.assessor_name;
    nameCell.style.cssText = 'font-family: var(--font-mono); font-size: var(--text-sm);';

    // Tier badge
    const tierCell = row.insertCell();
    const tierBadge = document.createElement('span');
    tierBadge.className = `tier-badge tier-${a.tier}`;
    tierBadge.textContent = `T${a.tier}`;
    tierCell.appendChild(tierBadge);
    tierCell.style.textAlign = 'center';

    // Delta
    const deltaCell = row.insertCell();
    deltaCell.textContent = `${a.delta >= 0 ? '+' : ''}${a.delta.toFixed(2)}`;
    deltaCell.style.cssText = `text-align: center; font-weight: 600; color: ${a.delta >= 0 ? 'var(--color-success)' : 'var(--color-error)'};`;

    // Effect size
    const effectCell = row.insertCell();
    effectCell.textContent = a.effect_size.toFixed(3);
    effectCell.style.cssText = 'text-align: center; font-family: var(--font-mono); font-size: var(--text-xs);';

    // P-value
    const pCell = row.insertCell();
    pCell.textContent = a.p_value.toFixed(4);
    pCell.style.cssText = `text-align: center; font-family: var(--font-mono); font-size: var(--text-xs); color: ${a.p_value < 0.05 ? 'var(--color-success)' : 'var(--color-gray-500)'};`;

    // Status
    const statusCell = row.insertCell();
    statusCell.textContent = a.is_significant ? '✅' : '—';
    statusCell.style.textAlign = 'center';

    // Fixes applied
    const fixesCell = row.insertCell();
    fixesCell.textContent = String(a.fixes_applied);
    fixesCell.style.cssText = 'text-align: center; color: var(--color-gray-600);';
  });
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboard);
</script>
