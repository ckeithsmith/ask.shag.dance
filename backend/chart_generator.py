"""
Chart Generation Service
Creates chart URLs from analysis data
"""

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    CHARTS_AVAILABLE = True
except ImportError:
    # Graceful fallback when matplotlib/seaborn not available
    plt = None
    sns = None
    CHARTS_AVAILABLE = False
    print("⚠️ Charts unavailable: matplotlib/seaborn not installed")

from io import BytesIO
import base64
from pathlib import Path
import os

# Set style only if matplotlib is available
if CHARTS_AVAILABLE:
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 10

class ChartGenerator:

    # Chart cache directory
    CHART_DIR = Path("/tmp/ask_shaggy_charts")

    def __init__(self):
        self.CHART_DIR.mkdir(exist_ok=True)

    @staticmethod
    def _save_chart_base64() -> str:
        """Save current figure as base64 data URL"""
        if not CHARTS_AVAILABLE:
            return None
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        return f"data:image/png;base64,{image_base64}"

    def create_line_chart(self, data: list, x_key: str, y_key: str,
                         title: str, x_label: str, y_label: str) -> str:
        """
        Create line chart for trends over time
        Returns: base64 data URL
        """
        if not data:
            return None

        # Extract data
        x_values = [item[x_key] for item in data]
        y_values = [item[y_key] for item in data]

        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(x_values, y_values, marker='o', linewidth=2, markersize=8)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        return self._save_chart_base64()

    def create_bar_chart(self, data: list, label_key: str, value_key: str,
                        title: str, max_bars: int = 20) -> str:
        """
        Create horizontal bar chart for rankings
        Returns: base64 data URL
        """
        if not data:
            return None

        # Limit bars for readability
        data = data[:max_bars]

        # Extract data
        labels = [item[label_key] for item in data]
        values = [item[value_key] for item in data]

        # Create chart
        plt.figure(figsize=(10, max(6, len(labels) * 0.4)))
        bars = plt.barh(labels, values)

        # Color gradient
        colors = plt.cm.viridis(range(len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel('Count', fontsize=12)
        plt.gca().invert_yaxis()  # Highest at top
        plt.tight_layout()

        return self._save_chart_base64()

    def create_comparison_chart(self, categories: list, series_data: dict,
                               title: str) -> str:
        """
        Create grouped bar chart for comparisons
        series_data: {"Series 1": [vals], "Series 2": [vals]}
        Returns: base64 data URL
        """
        import numpy as np

        plt.figure(figsize=(12, 6))

        x = np.arange(len(categories))
        width = 0.8 / len(series_data)  # Bar width

        for i, (label, values) in enumerate(series_data.items()):
            offset = width * i - (width * len(series_data) / 2)
            plt.bar(x + offset, values, width, label=label)

        plt.xlabel('Category', fontsize=12)
        plt.ylabel('Value', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xticks(x, categories, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()

        return self._save_chart_base64()

    def create_trend_chart_with_change(self, data: list, x_key: str,
                                      y_key: str, change_key: str, title: str) -> str:
        """
        Create line chart with change indicators
        Perfect for yearly trends showing YoY change
        """
        if not data:
            return None

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                       gridspec_kw={'height_ratios': [2, 1]})

        # Extract data
        x_values = [item[x_key] for item in data]
        y_values = [item[y_key] for item in data]
        change_values = [item.get(change_key, 0) for item in data]

        # Top chart: Trend line
        ax1.plot(x_values, y_values, marker='o', linewidth=2, markersize=8)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Count', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # Bottom chart: Change bars
        colors = ['green' if c >= 0 else 'red' for c in change_values]
        ax2.bar(x_values, change_values, color=colors, alpha=0.6)
        ax2.axhline(y=0, color='black', linewidth=0.8, linestyle='--')
        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('Change', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return self._save_chart_base64()

# Global instance
chart_generator = ChartGenerator()
