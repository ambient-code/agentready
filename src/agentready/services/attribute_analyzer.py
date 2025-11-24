"""Attribute correlation analysis with Plotly Express heatmap."""

import json
from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px
from scipy.stats import pearsonr


class AttributeAnalyzer:
    """Analyze correlation between AgentReady attributes and SWE-bench performance."""

    def analyze(
        self,
        result_files: List[Path],
        output_file: Path = None,
        heatmap_file: Path = None,
    ) -> dict:
        """
        Analyze correlation and generate heatmap.

        Args:
            result_files: List of experiment result JSON files
            output_file: Where to save analysis.json
            heatmap_file: Where to save heatmap.html

        Returns:
            Analysis dict with correlation and top attributes
        """
        # Load all results
        results = []
        for f in result_files:
            with open(f) as fp:
                results.append(json.load(fp))

        # Calculate overall correlation
        agentready_scores = [r["agentready_score"] for r in results]
        swebench_scores = [r["swebench_score"] for r in results]

        correlation, p_value = pearsonr(agentready_scores, swebench_scores)

        # Create DataFrame for heatmap
        heatmap_data = {}
        for result in results:
            config = result["config_name"]
            agent = result["agent"]
            score = result["swebench_score"]

            if config not in heatmap_data:
                heatmap_data[config] = {}
            heatmap_data[config][agent] = score

        df = pd.DataFrame(heatmap_data)

        # Generate interactive heatmap
        if heatmap_file:
            self._create_heatmap(df, heatmap_file)

        # Prepare analysis output
        analysis = {
            "correlation": {
                "overall": round(correlation, 3),
                "p_value": round(p_value, 6),
            },
            "top_attributes": self._rank_attributes(results),
            "heatmap_path": str(heatmap_file) if heatmap_file else None,
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(analysis, f, indent=2)

        return analysis

    def _create_heatmap(self, df: pd.DataFrame, output_path: Path):
        """Create interactive Plotly Express heatmap."""

        # Calculate deltas from baseline
        if "baseline" in df.columns:
            baseline = df["baseline"].values
            delta_df = df.copy()
            for col in df.columns:
                delta_df[col] = df[col] - baseline
        else:
            delta_df = df.copy()

        # Transpose: configs as rows, agents as columns
        df_t = df.T
        delta_t = delta_df.T

        # Create heatmap
        fig = px.imshow(
            df_t,
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=45,
            labels=dict(x="Agent", y="Configuration", color="Pass Rate (%)"),
            text_auto=".1f",
            aspect="auto",
            zmin=35,
            zmax=55,
        )

        # Add custom hover with deltas
        hover_text = []
        for i, config in enumerate(df_t.index):
            row_text = []
            for j, agent in enumerate(df_t.columns):
                score = df_t.iloc[i, j]
                delta = delta_t.iloc[i, j]
                text = (
                    f"<b>Agent:</b> {agent}<br>"
                    f"<b>Config:</b> {config}<br>"
                    f"<b>Score:</b> {score:.1f}%<br>"
                    f"<b>Delta from baseline:</b> {delta:+.1f}pp"
                )
                row_text.append(text)
            hover_text.append(row_text)

        fig.update_traces(
            hovertemplate="%{customdata}<extra></extra>", customdata=hover_text
        )

        # Customize layout
        fig.update_layout(
            title="SWE-bench Performance: AgentReady Configurations",
            xaxis_title="Agent",
            yaxis_title="Configuration",
            width=900,
            height=600,
            font=dict(size=12),
        )

        # Save standalone HTML
        fig.write_html(output_path)
        print(f"✓ Interactive heatmap saved to: {output_path}")

    def _rank_attributes(self, results: List[dict]) -> List[dict]:
        """Rank attributes by impact."""
        config_impacts = {}
        baseline_scores = {}

        for result in results:
            agent = result["agent"]
            config = result["config_name"]
            score = result["swebench_score"]

            if config == "baseline":
                baseline_scores[agent] = score
            elif agent in baseline_scores:
                delta = score - baseline_scores[agent]
                if config not in config_impacts:
                    config_impacts[config] = []
                config_impacts[config].append(delta)

        # Calculate average improvement per config
        ranked = []
        for config, deltas in config_impacts.items():
            avg_delta = sum(deltas) / len(deltas)
            ranked.append({"config": config, "avg_improvement": round(avg_delta, 1)})

        ranked.sort(key=lambda x: x["avg_improvement"], reverse=True)
        return ranked[:5]
