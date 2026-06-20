"""Warp Profiler — HTML Dashboard Generator.

Produces a standalone HTML report with embedded Chart.js
to visualize the complexity degradation curves.
"""

from __future__ import annotations
import json

from pyregex.domain.warp.models import BenchProfile


class HtmlExporter:
    """Exports a BenchProfile to a standalone Chart.js HTML report."""

    def export(self, profile: BenchProfile, filepath: str) -> None:
        """Write profile data to an HTML file at filepath."""
        time_data = [{"x": t.input_length, "y": t.time_ms} for t in profile.ticks]
        mem_data = [
            {"x": t.input_length, "y": t.memory_alloc_bytes / 1024.0}
            for t in profile.ticks
        ]  # KB

        color = "rgba(75, 192, 192, 1)"  # safe (green)
        bg_color = "rgba(75, 192, 192, 0.2)"

        if (
            "EXPONENTIAL" in profile.base_complexity.value
            or "QUADRATIC" in profile.base_complexity.value
            or "CUBIC" in profile.base_complexity.value
        ):
            color = "rgba(255, 99, 132, 1)"  # danger (red)
            bg_color = "rgba(255, 99, 132, 0.2)"

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Warp Profiler - {profile.pattern}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ border-bottom: 1px solid #30363d; padding-bottom: 20px; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; margin-top: 10px; }}
        .safe {{ color: #2ea043; }}
        .danger {{ color: #ff7b72; }}
        .chart-container {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; margin-bottom: 20px; height: 400px; }}
        .code {{ font-family: monospace; background: #21262d; padding: 4px 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Warp Profiler Dossier</h1>
            <p>Empirical Performance Analysis for: <span class="code">{profile.pattern}</span></p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div>Empirical Complexity</div>
                <div class="stat-value {"danger" if color == "rgba(255, 99, 132, 1)" else "safe"}">
                    {profile.base_complexity.value}
                </div>
                <div style="font-size: 12px; color: #8b949e; margin-top: 5px;">R² Fit: {profile.r_squared:.4f}</div>
            </div>
            <div class="stat-card">
                <div>Max Execution Time</div>
                <div class="stat-value">{max(t.time_ms for t in profile.ticks):.2f} ms</div>
            </div>
            <div class="stat-card">
                <div>Peak Memory Alloc</div>
                <div class="stat-value">{profile.max_memory_alloc_bytes / 1024.0:.2f} KB</div>
            </div>
            <div class="stat-card">
                <div>Timeout Hit</div>
                <div class="stat-value {"danger" if profile.timeout_hit else "safe"}">
                    {"YES" if profile.timeout_hit else "NO"}
                </div>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="timeChart"></canvas>
        </div>
        
        <div class="chart-container">
            <canvas id="memChart"></canvas>
        </div>
    </div>

    <script>
        const commonOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{
                    type: 'linear',
                    position: 'bottom',
                    title: {{ display: true, text: 'Payload Length (chars)', color: '#c9d1d9' }},
                    grid: {{ color: '#30363d' }},
                    ticks: {{ color: '#8b949e' }}
                }},
                y: {{
                    title: {{ display: true, color: '#c9d1d9' }},
                    grid: {{ color: '#30363d' }},
                    ticks: {{ color: '#8b949e' }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '#c9d1d9' }} }}
            }}
        }};

        // Time Chart
        const timeCtx = document.getElementById('timeChart').getContext('2d');
        const timeData = {json.dumps(time_data)};
        
        const timeOps = JSON.parse(JSON.stringify(commonOptions));
        timeOps.scales.y.title.text = 'Execution Time (ms)';

        new Chart(timeCtx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Regex Engine CPU Time',
                    data: timeData,
                    backgroundColor: '{color}',
                    borderColor: '{color}',
                    showLine: true,
                    tension: 0.4
                }}]
            }},
            options: timeOps
        }});

        // Memory Chart
        const memCtx = document.getElementById('memChart').getContext('2d');
        const memData = {json.dumps(mem_data)};
        
        const memOps = JSON.parse(JSON.stringify(commonOptions));
        memOps.scales.y.title.text = 'Memory Allocation Delta (KB)';

        new Chart(memCtx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Regex Engine Memory Footprint',
                    data: memData,
                    backgroundColor: 'rgba(54, 162, 235, 1)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    showLine: true,
                    tension: 0.1
                }}]
            }},
            options: memOps
        }});
    </script>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_template)
