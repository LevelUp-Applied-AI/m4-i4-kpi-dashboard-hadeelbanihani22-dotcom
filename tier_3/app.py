import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analysis import connect_db, extract_data, compute_kpis

# =========================
# Load Data
# =========================
engine = connect_db()
data = extract_data(engine)
kpis = compute_kpis(data)

df = kpis["df"]

# =========================
# App Setup
# =========================
app = dash.Dash(__name__)
app.title = "KPI Dashboard"

# =========================
# Layout
# =========================
app.layout = html.Div([

    html.H1("Amman Digital Market Dashboard"),

    dcc.Dropdown(
        id="city_filter",
        options=[{"label": c, "value": c} for c in df["city"].unique()],
        value=None,
        placeholder="Select City",
        style={"width": "50%"}
    ),

    dcc.Tabs([

        # =========================
        # PAGE 1
        # =========================
        dcc.Tab(label="KPI Overview", children=[
            dcc.Graph(id="kpi_cards")
        ]),

        # =========================
        # PAGE 2
        # =========================
        dcc.Tab(label="Time Series", children=[
            dcc.Graph(id="time_series")
        ]),

        # =========================
        # PAGE 3
        # =========================
        dcc.Tab(label="Cohort Analysis", children=[
            dcc.Graph(id="cohort_chart")
        ])

    ])

])


# =========================
# CALLBACK
# =========================
@app.callback(
    Output("kpi_cards", "figure"),
    Output("time_series", "figure"),
    Output("cohort_chart", "figure"),
    Input("city_filter", "value")
)
def update_dashboard(city):

    # =========================
    # Filter
    # =========================
    if city:
        dff = df[df["city"] == city]
    else:
        dff = df.copy()

    # =========================
    # KPIs
    # =========================
    total_revenue = dff["revenue"].sum()
    aov = dff.groupby("order_id")["revenue"].sum().mean()

    # =========================
    # KPI FIGURE (FIXED 🔥)
    # =========================
    fig_kpi = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]]
    )

    fig_kpi.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=total_revenue,
            title={"text": "Total Revenue"}
        ),
        row=1, col=1
    )

    fig_kpi.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=aov,
            title={"text": "Average Order Value"}
        ),
        row=1, col=2
    )

    fig_kpi.update_layout(height=400)

    # =========================
    # TIME SERIES
    # =========================
    monthly = dff.groupby("order_month")["revenue"].sum()

    fig_time = go.Figure()

    fig_time.add_trace(go.Scatter(
        x=monthly.index.astype(str),
        y=monthly.values,
        mode="lines+markers"
    ))

    fig_time.update_layout(
        title="Monthly Revenue Trend",
        xaxis_title="Month",
        yaxis_title="Revenue"
    )

    # =========================
    # COHORT
    # =========================
    cohort = dff.groupby(["category", "city"])["revenue"].sum().unstack(fill_value=0)

    fig_cohort = go.Figure(data=go.Heatmap(
        z=cohort.values,
        x=cohort.columns,
        y=cohort.index,
        colorscale="Viridis"
    ))

    fig_cohort.update_layout(
        title="Revenue Distribution by Category & City"
    )

    return fig_kpi, fig_time, fig_cohort


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
    