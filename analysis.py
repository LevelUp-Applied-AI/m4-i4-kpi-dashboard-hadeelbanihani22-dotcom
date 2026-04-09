import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine


# -------------------------------
# 1. CONNECT
# -------------------------------
def connect_db():
    return create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/amman_market")


# -------------------------------
# 2. EXTRACT + CLEAN
# -------------------------------
def extract_data(engine):
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

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items
    }


# -------------------------------
# 3. KPI COMPUTATION
# -------------------------------
def compute_kpis(data):
    customers = data["customers"]
    products = data["products"]
    orders = data["orders"]
    order_items = data["order_items"]

    df = order_items.merge(orders, on="order_id") \
                    .merge(products, on="product_id") \
                    .merge(customers[["customer_id", "city"]], on="customer_id", how="left")

    df["city"] = df["city"].fillna("Unknown")
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["order_month"] = pd.to_datetime(df["order_date"]).dt.to_period("M")

    total_revenue = df["revenue"].sum()

    revenue_by_city = df.groupby("city")["revenue"].sum().sort_values(ascending=False)

    monthly_revenue = df.groupby("order_month")["revenue"].sum()

    mom_growth = monthly_revenue.pct_change() * 100

    revenue_by_category = df.groupby("category")["revenue"].sum().sort_values(ascending=False)

    order_value = df.groupby(["order_id", "city"])["revenue"].sum().reset_index()
    aov_by_city = order_value.groupby("city")["revenue"].mean()

    return {
        "total_revenue": total_revenue,
        "aov_by_city": aov_by_city,
        "monthly_revenue": monthly_revenue,
        "mom_growth": mom_growth,
        "revenue_by_category": revenue_by_category,
        "df": df,
        "order_value": order_value,
        "revenue_by_city": revenue_by_city
    }


# -------------------------------
# 4. STATISTICAL TESTS
# -------------------------------
def run_statistical_tests(data_dict):
    kpis = compute_kpis(data_dict)
    df = kpis["df"]
    order_value = kpis["order_value"]

    results = {}

    # ANOVA
    cat_orders = df.groupby(["order_id", "category"])["revenue"].sum().reset_index()
    groups = [g["revenue"].values for _, g in cat_orders.groupby("category")]

    f_stat, p_val = stats.f_oneway(*groups)

    results["anova_category"] = {
        "p_value": float(p_val),
        "interpretation": "Significant" if p_val < 0.05 else "Not significant"
    }

    # T-test
    amman = order_value[order_value["city"] == "Amman"]["revenue"]
    others = order_value[order_value["city"] != "Amman"]["revenue"]

    t_stat, p_val = stats.ttest_ind(amman, others, equal_var=False)

    results["ttest_city"] = {
        "p_value": float(p_val),
        "interpretation": "Significant" if p_val < 0.05 else "Not significant"
    }

    return results


# -------------------------------
# 5. VISUALIZATION  (المهم)
# -------------------------------
def create_visualizations(kpis):
    os.makedirs("output", exist_ok=True)

    sns.set_palette("colorblind")
    sns.set_style("whitegrid")

    df = kpis["df"]

    # Trend + Growth
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    kpis["monthly_revenue"].plot(ax=axes[0], marker="o")
    axes[0].set_title("Finding: Revenue shows strong upward trend")

    kpis["mom_growth"].plot(kind="bar", ax=axes[1])
    axes[1].set_title("Month-over-Month Growth (%)")

    plt.tight_layout()
    plt.savefig("output/01_trend_growth.png")
    plt.close()

    # Category
    plt.figure()
    sns.barplot(
        x=kpis["revenue_by_category"].values,
        y=kpis["revenue_by_category"].index
    )
    plt.title("Finding: Electronics dominates revenue")
    plt.savefig("output/02_category.png")
    plt.close()

    # City
    plt.figure()
    rev_city = kpis["revenue_by_city"]

    sns.barplot(
        x=rev_city.index,
        y=rev_city.values
    )

    plt.title("Finding: Amman generates the highest total revenue")
    plt.xticks(rotation=45)
    plt.savefig("output/03_revenue_city.png")
    plt.close()

    # Boxplot
    plt.figure()
    sns.boxplot(data=df, x="category", y="revenue")
    plt.xticks(rotation=45)
    plt.title("Finding: Variation in order values across categories")
    plt.savefig("output/04_boxplot.png")
    plt.close()

    # Heatmap
    pivot = df.pivot_table(values="revenue", index="category", columns="city", aggfunc="sum")

    plt.figure()
    sns.heatmap(pivot, cmap="viridis")
    plt.title("Finding: Revenue distribution across category and city")
    plt.savefig("output/05_heatmap.png")
    plt.close()


# -------------------------------
# 6. MAIN
# -------------------------------
def main():
    print("Starting KPI Dashboard...\n")

    engine = connect_db()
    data = extract_data(engine)

    kpis = compute_kpis(data)

    stats_results = run_statistical_tests(data)

    create_visualizations(kpis)  #  مهم

    print("\nTotal Revenue:", round(kpis["total_revenue"], 2))
    print("Latest MoM Growth:", round(kpis["mom_growth"].iloc[-1], 2), "%")
    print("\nStatistical Results:", stats_results)

    print("\nAll tasks completed successfully")


if __name__ == "__main__":
    main()