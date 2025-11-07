"""
Response Formatting Utilities
Creates rich markdown tables, charts, and formatted responses
"""

class MarkdownFormatter:

    @staticmethod
    def create_table(data: list, max_rows: int = 25) -> str:
        """
        Create markdown table from list of dicts
        Automatically limits to max_rows for data protection
        """
        if not data:
            return "*No data to display*"

        # Enforce limit
        data = data[:max_rows]

        # Get headers from first row
        headers = list(data[0].keys())

        # Create header row
        table = "| " + " | ".join(str(h) for h in headers) + " |\n"

        # Create separator
        table += "|" + "|".join("---" for _ in headers) + "|\n"

        # Create data rows
        for row in data:
            table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

        # Add note if data was truncated
        if len(data) == max_rows:
            table += f"\n*Showing top {max_rows} results for data protection*\n"

        return table

    @staticmethod
    def create_ranked_list(data: list, name_key: str, value_key: str,
                          value_label: str = "count", max_items: int = 25) -> str:
        """
        Create numbered ranking list with emphasis
        Example: 1. **Sam West** - 72 wins
        """
        if not data:
            return "*No data to display*"

        data = data[:max_items]

        result = ""
        for i, item in enumerate(data, 1):
            name = item.get(name_key, "Unknown")
            value = item.get(value_key, 0)
            result += f"{i}. **{name}** - {value} {value_label}\n"

        if len(data) == max_items:
            result += f"\n*Top {max_items} shown*\n"

        return result

    @staticmethod
    def create_stats_card(title: str, stats: dict) -> str:
        """
        Create formatted statistics card
        """
        card = f"### {title}\n\n"
        for label, value in stats.items():
            # Format label nicely
            label_formatted = label.replace('_', ' ').title()
            card += f"**{label_formatted}:** {value}\n"
        card += "\n"
        return card

    @staticmethod
    def create_comparison_table(items: list, labels: list) -> str:
        """
        Create side-by-side comparison table
        """
        if not items or len(items) != len(labels):
            return "*Invalid comparison data*"

        table = "| Metric | " + " | ".join(labels) + " |\n"
        table += "|--------|" + "|".join("--------" for _ in labels) + "|\n"

        # Get all unique keys
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())

        for key in sorted(all_keys):
            key_formatted = key.replace('_', ' ').title()
            values = [str(item.get(key, "N/A")) for item in items]
            table += f"| {key_formatted} | " + " | ".join(values) + " |\n"

        return table

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format percentage with proper symbol"""
        return f"{value:.{decimals}f}%"

    @staticmethod
    def format_trend_indicator(current: float, previous: float) -> str:
        """Create trend indicator with emoji"""
        if current > previous:
            diff = current - previous
            return f"📈 +{diff:.1f}"
        elif current < previous:
            diff = previous - current
            return f"📉 -{diff:.1f}"
        else:
            return "➡️ No change"
