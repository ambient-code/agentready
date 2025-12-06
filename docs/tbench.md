---
layout: default
title: Terminal-Bench Evaluation Results
description: Systematic A/B testing of AgentReady assessors against Terminal-Bench performance
---

# Terminal-Bench Eval Harness Results

> **Systematic A/B testing** of each AgentReady assessor's impact on [Terminal-Bench](https://tbench.ai) (tbench.ai) performance

---

## 📊 Overview

<div class="stats-cards">
  <div class="stat-card">
    <h3 id="total-assessors">-</h3>
    <p>Assessors Tested</p>
  </div>
  <div class="stat-card">
    <h3 id="significant-count">-</h3>
    <p>Significant Improvements</p>
  </div>
  <div class="stat-card">
    <h3 id="significance-rate">-%</h3>
    <p>Significance Rate</p>
  </div>
  <div class="stat-card">
    <h3 id="baseline-score">-</h3>
    <p>Baseline Score</p>
  </div>
</div>

---

## 🎯 Impact by Tier

<div class="chart-container">
  <canvas id="tierImpactChart"></canvas>
</div>

<div class="tier-legend">
  <p><strong>Tier 1 (Essential):</strong> Most critical for AI assistance</p>
  <p><strong>Tier 2 (Critical):</strong> Major impact on development velocity</p>
  <p><strong>Tier 3 (Important):</strong> Meaningful quality improvements</p>
  <p><strong>Tier 4 (Advanced):</strong> Polish and optimization</p>
</div>

---

## 🏆 Top Performing Assessors

<div class="table-wrapper">
  <table id="topAssessorsTable">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Assessor</th>
        <th>Tier</th>
        <th>Delta Score</th>
        <th>Effect Size</th>
        <th>Significant?</th>
      </tr>
    </thead>
    <tbody>
      <!-- Populated by JavaScript -->
    </tbody>
  </table>
</div>

---

## 📈 Complete Results

<div class="table-wrapper">
  <table id="allAssessorsTable" class="sortable">
    <thead>
      <tr>
        <th data-sort="number">Rank</th>
        <th data-sort="string">Assessor</th>
        <th data-sort="number">Tier</th>
        <th data-sort="number">Delta Score (%)</th>
        <th data-sort="number">Effect Size (Cohen's d)</th>
        <th data-sort="number">P-value</th>
        <th data-sort="string">Significant?</th>
        <th data-sort="number">Fixes Applied</th>
      </tr>
    </thead>
    <tbody>
      <!-- Populated by JavaScript -->
    </tbody>
  </table>
</div>

---

## 📖 Methodology

<details>
<summary><strong>Click to expand methodology details</strong></summary>

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

</details>

---

## 🔗 Related Resources

- [Terminal-Bench Official Site](https://tbench.ai)
- [AgentReady Attributes](/agentready/attributes)
- [User Guide](/agentready/user-guide)
- [GitHub Repository](https://github.com/ambient-code/agentready)

---

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<script>
// Load data and render dashboard
async function loadDashboard() {
  try {
    // Load all data files
    const [stats, tierImpacts, rankedAssessors, baseline] = await Promise.all([
      fetch('/agentready/_data/tbench/stats.json').then(r => r.json()),
      fetch('/agentready/_data/tbench/tier_impacts.json').then(r => r.json()),
      fetch('/agentready/_data/tbench/ranked_assessors.json').then(r => r.json()),
      fetch('/agentready/_data/tbench/baseline.json').then(r => r.json()),
    ]);

    // Update overview cards
    document.getElementById('total-assessors').textContent = stats.total_assessors_tested;
    document.getElementById('significant-count').textContent = stats.significant_improvements;
    document.getElementById('significance-rate').textContent = stats.significance_rate.toFixed(0) + '%';
    document.getElementById('baseline-score').textContent = baseline.mean_score.toFixed(2);

    // Render tier impact chart
    renderTierChart(tierImpacts);

    // Render tables
    renderTopAssessorsTable(rankedAssessors.slice(0, 5));
    renderAllAssessorsTable(rankedAssessors);

  } catch (error) {
    console.error('Error loading dashboard data:', error);
    const container = document.querySelector('.stats-cards');
    container.textContent = '';
    const errorMsg = document.createElement('p');
    errorMsg.style.color = 'red';
    errorMsg.textContent = '⚠️ Error loading dashboard data. Run agentready eval-harness dashboard to generate data.';
    container.appendChild(errorMsg);
  }
}

function renderTierChart(tierData) {
  const ctx = document.getElementById('tierImpactChart').getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: tierData.map(t => 'Tier ' + t.tier + ': ' + t.tier_name),
      datasets: [{
        label: 'Average Impact (% points)',
        data: tierData.map(t => t.delta),
        backgroundColor: [
          'rgba(139, 92, 246, 0.8)',
          'rgba(99, 102, 241, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(6, 182, 212, 0.8)',
        ],
        borderColor: [
          'rgb(139, 92, 246)',
          'rgb(99, 102, 241)',
          'rgb(59, 130, 246)',
          'rgb(6, 182, 212)',
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Average Assessor Impact by Tier',
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Impact: ' + context.parsed.y.toFixed(2) + '% points';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Delta Score (% points)'
          }
        }
      }
    }
  });
}

function renderTopAssessorsTable(assessors) {
  const tbody = document.querySelector('#topAssessorsTable tbody');
  tbody.textContent = '';

  assessors.forEach((a, i) => {
    const row = document.createElement('tr');

    // Rank
    const rankCell = document.createElement('td');
    const rankStrong = document.createElement('strong');
    rankStrong.textContent = String(i + 1);
    rankCell.appendChild(rankStrong);
    row.appendChild(rankCell);

    // Assessor name
    const nameCell = document.createElement('td');
    nameCell.textContent = a.assessor_name;
    row.appendChild(nameCell);

    // Tier
    const tierCell = document.createElement('td');
    tierCell.textContent = 'Tier ' + a.tier;
    row.appendChild(tierCell);

    // Delta score
    const deltaCell = document.createElement('td');
    deltaCell.className = a.delta_score >= 0 ? 'positive' : 'negative';
    deltaCell.textContent = (a.delta_score >= 0 ? '+' : '') + a.delta_score.toFixed(2);
    row.appendChild(deltaCell);

    // Effect size
    const effectCell = document.createElement('td');
    effectCell.textContent = Math.abs(a.effect_size).toFixed(3);
    row.appendChild(effectCell);

    // Significant
    const sigCell = document.createElement('td');
    sigCell.textContent = a.is_significant ? '✅ Yes' : '❌ No';
    row.appendChild(sigCell);

    tbody.appendChild(row);
  });
}

function renderAllAssessorsTable(assessors) {
  const tbody = document.querySelector('#allAssessorsTable tbody');
  tbody.textContent = '';

  assessors.forEach((a, i) => {
    const row = document.createElement('tr');

    // Rank
    const rankCell = document.createElement('td');
    rankCell.textContent = String(i + 1);
    row.appendChild(rankCell);

    // Assessor name
    const nameCell = document.createElement('td');
    nameCell.textContent = a.assessor_name;
    row.appendChild(nameCell);

    // Tier
    const tierCell = document.createElement('td');
    tierCell.textContent = 'Tier ' + a.tier;
    row.appendChild(tierCell);

    // Delta score
    const deltaCell = document.createElement('td');
    deltaCell.className = a.delta_score >= 0 ? 'positive' : 'negative';
    deltaCell.textContent = (a.delta_score >= 0 ? '+' : '') + a.delta_score.toFixed(2);
    row.appendChild(deltaCell);

    // Effect size
    const effectCell = document.createElement('td');
    effectCell.textContent = Math.abs(a.effect_size).toFixed(3);
    row.appendChild(effectCell);

    // P-value
    const pvalueCell = document.createElement('td');
    pvalueCell.textContent = (a.p_value === null || isNaN(a.p_value)) ? 'N/A' : a.p_value.toFixed(4);
    row.appendChild(pvalueCell);

    // Significant
    const sigCell = document.createElement('td');
    sigCell.textContent = a.is_significant ? '✅' : '❌';
    row.appendChild(sigCell);

    // Fixes applied
    const fixesCell = document.createElement('td');
    fixesCell.textContent = String(a.fixes_applied);
    row.appendChild(fixesCell);

    tbody.appendChild(row);
  });
}

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboard);
</script>

<style>
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}

.stat-card {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.stat-card h3 {
  margin: 0;
  font-size: 2rem;
  color: #6366f1;
}

.stat-card p {
  margin: 0.5rem 0 0 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.chart-container {
  position: relative;
  height: 400px;
  margin: 2rem 0;
}

.tier-legend {
  background: #f8f9fa;
  border-left: 4px solid #6366f1;
  padding: 1rem;
  margin: 1rem 0;
  font-size: 0.9rem;
}

.tier-legend p {
  margin: 0.5rem 0;
}

.table-wrapper {
  overflow-x: auto;
  margin: 2rem 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

th {
  background: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

tbody tr:hover {
  background: #f8f9fa;
}

.positive {
  color: #22c55e;
  font-weight: 600;
}

.negative {
  color: #ef4444;
  font-weight: 600;
}

details {
  margin: 2rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

summary {
  cursor: pointer;
  font-weight: 600;
  padding: 0.5rem;
}

summary:hover {
  color: #6366f1;
}
</style>
