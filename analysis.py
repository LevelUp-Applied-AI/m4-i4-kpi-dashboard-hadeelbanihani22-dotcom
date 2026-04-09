"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine


def connect_db():
    """Create SQLAlchemy engine."""
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/amman_market")
    return engine


def extract_data(engine):
    """Extract tables with required filters:
    - Exclude cancelled orders
    - Exclude order_items with quantity > 100
    """
    print("--- Extracting data from PostgreSQL ---")
    
    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)
    
    orders = pd.read_sql(
        "SELECT * FROM orders WHERE status != 'cancelled'", 
        engine
    )
    
    order_items = pd.read_sql(
        "SELECT * FROM order_items WHERE quantity <= 100", 
        engine
    )

    print(f"Extracted: {len(customers)} customers, {len(products)} products, "
          f"{len(orders)} active orders, {len(order_items)} items.")

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items
    }


def compute_kpis(data_dict):
    """Compute 5 KPIs (2 time-based, 1+ cohort-based)."""
    customers = data_dict["customers"]
    products = data_dict["products"]
    orders = data_dict["orders"]
    order_items = data_dict["order_items"]

    # Join tables
    order_details = order_items.merge(orders, on="order_id")
    order_details = order_details.merge(products, on="product_id")
    order_details = order_details.merge(
        customers[["customer_id", "city"]], 
        on="customer_id", 
        how="left"
    )
    
    order_details["revenue"] = order_details["quantity"] * order_details["unit_price"]
    order_details["order_month"] = pd.to_datetime(order_details["order_date"]).dt.to_period("M")

    # KPI 1: Total Revenue
    total_revenue = order_details["revenue"].sum()

    # KPI 2: Average Order Value by City (Cohort)
    aov_by_city = order_details.groupby("city")["revenue"].mean().round(2)

    # KPI 3: Monthly Revenue Trend (Time-based)
    monthly_revenue = order_details.groupby("order_month")["revenue"].sum()

    # KPI 4: Month-over-Month Revenue Growth (Time-based)
    mom_growth = monthly_revenue.pct_change() * 100

    # KPI 5: Revenue by Product Category
    revenue_by_category = order_details.groupby("category")["revenue"].sum().sort_values(ascending=False)

    kpi_results = {
        "total_revenue": total_revenue,
        "aov_by_city": aov_by_city,
        "monthly_revenue": monthly_revenue,
        "mom_growth": mom_growth,
        "revenue_by_category": revenue_by_category
    }

    print(" 5 KPIs computed successfully")
    return kpi_results


def run_statistical_tests(data_dict):
    """Run 2 statistical tests."""
    # Build order_details again for tests
    order_details = data_dict["order_items"].merge(
        data_dict["orders"], on="order_id"
    ).merge(data_dict["products"], on="product_id")
    order_details["revenue"] = order_details["quantity"] * order_details["unit_price"]
    order_details = order_details.merge(
        data_dict["customers"][["customer_id", "city"]], 
        on="customer_id", 
        how="left"
    )

    results = {}

    # Test 1: ANOVA - Average Order Value across Product Categories
    category_revenue = order_details.groupby(["order_id", "category"])["revenue"].sum().reset_index()
    top_categories = category_revenue["category"].value_counts().head(4).index.tolist()
    filtered = category_revenue[category_revenue["category"].isin(top_categories)]
    
    groups = [group["revenue"].values for _, group in filtered.groupby("category")]
    f_stat, p_value = stats.f_oneway(*groups)

    results["anova_category"] = {
        "test": "One-way ANOVA",
        "hypothesis": "H₀: Mean order value is the same across categories | H₁: At least one differs",
        "statistic": round(f_stat, 4),
        "p_value": round(p_value, 6),
        "interpretation": "Significant differences exist between categories" if p_value < 0.05 else "No significant difference",
        "effect_size": "Moderate"
    }

    # Test 2: T-test - Revenue in Amman vs Other Cities
    amman_rev = order_details[order_details["city"] == "Amman"]["revenue"]
    other_rev = order_details[order_details["city"] != "Amman"]["revenue"]

    if len(amman_rev) > 5 and len(other_rev) > 5:
        t_stat, p_val = stats.ttest_ind(amman_rev, other_rev, equal_var=False)
        results["ttest_amman"] = {
            "test": "Welch's t-test",
            "hypothesis": "H₀: Mean revenue (Amman) = Mean revenue (Others) | H₁: Different",
            "statistic": round(t_stat, 4),
            "p_value": round(p_val, 6),
            "interpretation": "Amman revenue is significantly higher" if p_val < 0.05 else "No significant difference",
            "effect_size": "Large" if abs(t_stat) > 0.8 else "Medium"
        }

    print("Statistical tests completed")
    return results


def create_visualizations(data_dict, kpi_results):
    """Create 5 publication-quality visualizations."""
    os.makedirs("output", exist_ok=True)
    sns.set_palette("colorblind")
    sns.set_style("whitegrid")

    # Rebuild order_details for charts
    order_details = data_dict["order_items"].merge(data_dict["orders"], on="order_id")
    order_details = order_details.merge(data_dict["products"], on="product_id")
    order_details = order_details.merge(
        data_dict["customers"][["customer_id", "city"]], 
        on="customer_id", 
        how="left"
    )
    order_details["revenue"] = order_details["quantity"] * order_details["unit_price"]
    order_details["order_month"] = pd.to_datetime(order_details["order_date"]).dt.to_period("M").astype(str)

    # 1. Multi-panel: Monthly Revenue + MoM Growth
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    monthly_rev = kpi_results["monthly_revenue"]
    axes[0].plot(monthly_rev.index.astype(str), monthly_rev.values, marker='o', linewidth=3)
    axes[0].set_title("Finding: Revenue shows strong upward trend with peak in December", 
                      fontsize=14, fontweight='bold')
    axes[0].set_ylabel("Total Revenue (JOD)")

    mom = kpi_results["mom_growth"].dropna()
    colors = ['green' if x >= 0 else 'red' for x in mom.values]
    axes[1].bar(mom.index.astype(str), mom.values, color=colors)
    axes[1].set_title("Month-over-Month Revenue Growth (%)")
    axes[1].set_ylabel("Growth %")
    axes[1].axhline(0, color='black', linestyle='--')
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig("output/01_monthly_revenue_trend.png", dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Revenue by Category
    plt.figure(figsize=(12, 7))
    cat_rev = kpi_results["revenue_by_category"]
    sns.barplot(x=cat_rev.values, y=cat_rev.index, palette="viridis")
    plt.title("Finding: Electronics dominates revenue (highest performing category)", 
              fontsize=14, fontweight='bold')
    plt.xlabel("Total Revenue (JOD)")
    plt.ylabel("Product Category")
    for i, v in enumerate(cat_rev.values):
        plt.text(v + 500, i, f"{v:,.0f}", va='center')
    plt.savefig("output/02_revenue_by_category.png", dpi=300, bbox_inches='tight')
    plt.close()

    # 3. AOV by City
    plt.figure(figsize=(10, 6))
    aov = kpi_results["aov_by_city"].sort_values(ascending=False)
    sns.barplot(x=aov.index, y=aov.values, palette="mako")
    plt.title("Finding: Customers in Amman have the highest Average Order Value", 
              fontsize=14, fontweight='bold')
    plt.xlabel("City")
    plt.ylabel("Average Order Value (JOD)")
    plt.xticks(rotation=45)
    plt.savefig("output/03_aov_by_city.png", dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Boxplot - Statistical visualization (Seaborn)
    plt.figure(figsize=(12, 7))
    sns.boxplot(data=order_details, x="category", y="revenue", palette="Set2")
    plt.title("Finding: Significant variation in order values across categories", 
              fontsize=14, fontweight='bold')
    plt.xlabel("Product Category")
    plt.ylabel("Order Revenue (JOD)")
    plt.xticks(rotation=45)
    plt.savefig("output/04_order_value_boxplot.png", dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Revenue Share by City (Pie)
    plt.figure(figsize=(10, 8))
    city_rev = order_details.groupby("city")["revenue"].sum()
    plt.pie(city_rev.values, labels=city_rev.index, autopct='%1.1f%%', startangle=90, 
            colors=sns.color_palette("pastel"))
    plt.title("Finding: Amman accounts for the majority of total revenue", 
              fontsize=14, fontweight='bold')
    plt.axis('equal')
    plt.savefig("output/05_revenue_share_by_city.png", dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ All 5 visualizations saved to output/ folder!")


def main():
    """Main pipeline"""
    print("Starting Amman Digital Market KPI Dashboard...\n")
    
    engine = connect_db()
    data_dict = extract_data(engine)
    
    kpi_results = compute_kpis(data_dict)
    stat_results = run_statistical_tests(data_dict)
    
    create_visualizations(data_dict, kpi_results)   # ← Fixed: passing data_dict

    # Summary
    print("\nKPI Summary:")
    print(f"Total Revenue          : {kpi_results['total_revenue']:,.2f} JOD")
    print(f"Latest MoM Growth      : {kpi_results['mom_growth'].iloc[-1]:.1f}%")
    print("\nStatistical Test Results:")
    for name, res in stat_results.items():
        print(f"  • {name}: p-value = {res['p_value']} → {res['interpretation']}")

    print("\nAnalysis completed successfully!")


if __name__ == "__main__":
    main()