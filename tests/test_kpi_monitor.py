import sys
import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# FIX IMPORT
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis import connect_db, extract_data, compute_kpis


# =========================
# LOAD CONFIG
# =========================
def load_config():
    with open("config.json") as f:
        return json.load(f)


# =========================
# COMPUTE VALUES
# =========================
def compute_all_kpis(df):

    total_revenue = df["revenue"].sum()

    order_value = df.groupby("order_id")["revenue"].sum()
    aov = order_value.mean()

    monthly = df.groupby("order_month")["revenue"].sum().reset_index()

    mom = monthly.copy()
    mom["growth"] = mom["revenue"].pct_change() * 100

    category = df.groupby("category")["revenue"].sum().reset_index()

    return total_revenue, aov, monthly, mom, category


# =========================
# CREATE DASHBOARD
# =========================
def build_dashboard(kpis, config):

    df = kpis["order_value"]

    cities = ["All"] + sorted(df["city"].dropna().unique())

    def filter_df(city):
        if city == "All":
            return df
        return df[df["city"] == city]

    # =========================
    # INITIAL DATA
    # =========================
    filtered = filter_df("All")
    total_revenue, aov, monthly, mom, category = compute_all_kpis(filtered)

    # =========================
    # FIGURE
    # =========================
    fig = go.Figure()

    # ========= GAUGE 1 =========
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=float(total_revenue),
        title={"text": "Total Revenue"},
        domain={'x': [0, 0.3], 'y': [0.6, 1]},
        gauge={
            'axis': {'range': [0, 70000]},
            'steps': [
                {'range': [0, config["total_revenue"]["yellow"]], 'color': "red"},
                {'range': [config["total_revenue"]["yellow"], config["total_revenue"]["green"]], 'color': "yellow"},
                {'range': [config["total_revenue"]["green"], 70000], 'color': "green"},
            ]
        }
    ))

    # ========= GAUGE 2 =========
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=float(aov),
        title={"text": "AOV"},
        domain={'x': [0.35, 0.65], 'y': [0.6, 1]},
        gauge={
            'axis': {'range': [0, 200]},
            'steps': [
                {'range': [0, config["aov"]["yellow"]], 'color': "red"},
                {'range': [config["aov"]["yellow"], config["aov"]["green"]], 'color': "yellow"},
                {'range': [config["aov"]["green"], 200], 'color': "green"},
            ]
        }
    ))

    # ========= GAUGE 3 (MoM) =========
    latest_growth = mom["growth"].dropna().iloc[-1]

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=float(latest_growth),
        title={"text": "MoM Growth %"},
        domain={'x': [0.7, 1], 'y': [0.6, 1]},
        gauge={
            'axis': {'range': [-50, 200]},
            'steps': [
                {'range': [-50, 0], 'color': "red"},
                {'range': [0, 50], 'color': "yellow"},
                {'range': [50, 200], 'color': "green"},
            ]
        }
    ))

    # ========= MONTHLY TREND =========
    monthly_fig = px.line(monthly, x="order_month", y="revenue")

    for trace in monthly_fig.data:
        fig.add_trace(trace)

    # ========= CATEGORY =========
    cat_fig = px.bar(category, x="category", y="revenue")

    for trace in cat_fig.data:
        fig.add_trace(trace)

    # =========================
    # DROPDOWN
    # =========================
    buttons = []

    for city in cities:
        filtered = filter_df(city)
        tr, aov, monthly, mom, category = compute_all_kpis(filtered)

        latest_growth = mom["growth"].dropna().iloc[-1]

        buttons.append(dict(
            label=city,
            method="update",
            args=[
                {
                    "value": [
                        float(tr),
                        float(aov),
                        float(latest_growth)
                    ]
                },
                {
                    "title": f"KPI Dashboard - {city}"
                }
            ]
        ))

    fig.update_layout(
        title="KPI Monitoring Dashboard",
        updatemenus=[dict(
            buttons=buttons,
            direction="down",
            x=0,
            y=1.2
        )],
        height=800
    )

    # SAVE
    os.makedirs("output", exist_ok=True)
    fig.write_html("output/kpi_monitor_dashboard.html", encoding="utf-8")

    print("✅ Dashboard saved successfully")


# =========================
# MAIN
# =========================
def main():
    print("🚀 Running KPI Monitor...")

    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)
    config = load_config()

    build_dashboard(kpis, config)


if __name__ == "__main__":
    main()