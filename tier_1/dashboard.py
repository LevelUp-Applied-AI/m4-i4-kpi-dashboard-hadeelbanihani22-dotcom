import os
import sys
import plotly.express as px

# 🔥 حل مشكلة import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis import connect_db, extract_data, compute_kpis


def main():
    print("Building Interactive KPI Dashboard...")

    # =========================
    # Load data
    # =========================
    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)

    os.makedirs("output", exist_ok=True)

    # =========================
    # 1. Monthly Revenue Trend
    # =========================
    fig1 = px.line(
        x=kpis["monthly_revenue"].index.astype(str),
        y=kpis["monthly_revenue"].values,
        markers=True,
        title="Monthly Revenue Trend",
        labels={"x": "Month", "y": "Revenue (JOD)"}
    )
    fig1.update_layout(template="plotly_white")

    # =========================
    # 2. MoM Growth
    # =========================
    fig2 = px.bar(
        x=kpis["mom_growth"].index.astype(str),
        y=kpis["mom_growth"].values,
        title="Month-over-Month Growth (%)",
        labels={"x": "Month", "y": "Growth %"}
    )
    fig2.update_layout(template="plotly_white")

    # =========================
    # 3. Revenue by Category
    # =========================
    fig3 = px.bar(
        x=kpis["revenue_by_category"].values,
        y=kpis["revenue_by_category"].index,
        orientation='h',
        title="Revenue by Product Category",
        labels={"x": "Revenue (JOD)", "y": "Category"}
    )
    fig3.update_layout(template="plotly_white")

    # =========================
    # 4. AOV by City
    # =========================
    fig4 = px.bar(
        x=kpis["aov_by_city"].index,
        y=kpis["aov_by_city"].values,
        title="Average Order Value by City",
        labels={"x": "City", "y": "AOV (JOD)"}
    )
    fig4.update_layout(template="plotly_white")

    # =========================
    # 5. Scatter (Extra insight)
    # =========================
    fig5 = px.scatter(
        x=kpis["revenue_by_category"].index,
        y=kpis["revenue_by_category"].values,
        size=kpis["revenue_by_category"].values,
        title="Category Revenue Distribution",
        labels={"x": "Category", "y": "Revenue"}
    )
    fig5.update_layout(template="plotly_white")

    # =========================
    # Save Dashboard HTML
    # =========================
    output_file = "output/dashboard.html"

    with open(output_file, "w", encoding="utf-8") as f:  #  حل Unicode
        f.write("<h1>Amman Digital Market - KPI Dashboard</h1>")
        f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(fig2.to_html(full_html=False))
        f.write(fig3.to_html(full_html=False))
        f.write(fig4.to_html(full_html=False))
        f.write(fig5.to_html(full_html=False))

    print(f"Dashboard saved to {output_file}")


if __name__ == "__main__":
    main()