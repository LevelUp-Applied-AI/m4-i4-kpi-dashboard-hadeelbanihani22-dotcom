import json
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis import connect_db, extract_data, compute_kpis


# =========================
# Load config
# =========================
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


# =========================
# Status logic
# =========================
def get_status(value, thresholds):
    if value >= thresholds["green"]:
        return "green"
    elif value >= thresholds["yellow"]:
        return "yellow"
    else:
        return "red"


# =========================
# Gauge
# =========================
def create_gauge(title, value, target):
    return go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title},
        delta={"reference": target},
        gauge={
            "axis": {"range": [0, max(value * 1.5, target * 1.5)]},
            "bar": {"color": "blue"},
            "steps": [
                {"range": [0, target * 0.5], "color": "red"},
                {"range": [target * 0.5, target], "color": "yellow"},
                {"range": [target, target * 1.5], "color": "green"},
            ],
        },
    )


# =========================
# MAIN
# =========================
def main():
    print(" Running KPI Monitor...")

    config = load_config()

    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)

    # KPIs
    total_revenue = kpis["total_revenue"]
    mom_growth = kpis["mom_growth"].iloc[-1]
    aov = kpis["aov_by_city"].mean()

    monthly = kpis["monthly_revenue"]
    category = kpis["revenue_by_category"]

    # =========================
    # Status
    # =========================
    statuses = {
        "total_revenue": get_status(total_revenue, config["total_revenue"]),
        "mom_growth": get_status(mom_growth, config["mom_growth"]),
        "aov": get_status(aov, config["aov"]),
    }

    print("KPI Status:")
    for k, v in statuses.items():
        print(f"{k}: {v}")

    # =========================
    # FIGURE (حل مشكلة overlap)
    # =========================
    fig = make_subplots(
        rows=2, cols=3,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
            [{"type": "xy", "colspan": 2}, None, {"type": "xy"}]
        ],
        subplot_titles=(
            "Total Revenue",
            "MoM Growth",
            "Average Order Value",
            "Monthly Revenue Trend",
            "",
            "Revenue by Category"
        )
    )

    # Gauges
    fig.add_trace(create_gauge("", total_revenue, config["total_revenue"]["green"]), row=1, col=1)
    fig.add_trace(create_gauge("", mom_growth, config["mom_growth"]["green"]), row=1, col=2)
    fig.add_trace(create_gauge("", aov, config["aov"]["green"]), row=1, col=3)

    # Monthly trend
    fig.add_trace(
        go.Scatter(
            x=monthly.index.astype(str),
            y=monthly.values,
            mode="lines+markers",
            name="Monthly Revenue"
        ),
        row=2, col=1
    )

    # Category revenue
    fig.add_trace(
        go.Bar(
            x=category.index,
            y=category.values,
            name="Category Revenue"
        ),
        row=2, col=3
    )

    # =========================
    # Layout
    # =========================
    fig.update_layout(
        height=700,
        title="KPI Monitoring Dashboard",
        showlegend=False
    )

    # =========================
    # Dropdown
    # =========================
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {"label": "All",
                     "method": "update",
                     "args": [{"visible": [True, True, True, True, True]}]},

                    {"label": "Gauges Only",
                     "method": "update",
                     "args": [{"visible": [True, True, True, False, False]}]},

                    {"label": "Charts Only",
                     "method": "update",
                     "args": [{"visible": [False, False, False, True, True]}]},
                ],
                "direction": "down",
                "x": 0,
                "y": 1.2
            }
        ]
    )

    # Save
    os.makedirs("output", exist_ok=True)
    fig.write_html("output/kpi_monitor.html")

    print(" Dashboard saved to output/kpi_monitor.html")

    return statuses


if __name__ == "__main__":
    main()