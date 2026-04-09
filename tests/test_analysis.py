import pytest
import pandas as pd
from analysis import connect_db, extract_data, compute_kpis, run_statistical_tests


@pytest.fixture(scope="module")
def data_dict():
    """Extract data once for all tests"""
    engine = connect_db()
    return extract_data(engine)


def test_extraction_returns_dataframes(data_dict):
    """Check extraction returns correct structure"""
    assert isinstance(data_dict, dict)

    expected_tables = ["customers", "products", "orders", "order_items"]
    for table in expected_tables:
        assert table in data_dict
        assert isinstance(data_dict[table], pd.DataFrame)

    # Check cleaning
    assert (data_dict["orders"]["status"] != "cancelled").all()
    assert (data_dict["order_items"]["quantity"] <= 100).all()


def test_kpi_computation_returns_expected_keys(data_dict):
    """Check KPI structure"""
    kpis = compute_kpis(data_dict)

    expected_keys = [
        "total_revenue",
        "aov_by_city",
        "monthly_revenue",
        "mom_growth",
        "revenue_by_category"
    ]

    for key in expected_keys:
        assert key in kpis

    assert isinstance(kpis["total_revenue"], (int, float))
    assert len(kpis["aov_by_city"]) > 0
    assert len(kpis["monthly_revenue"]) > 0


def test_statistical_test_returns_pvalue(data_dict):
    """Check statistical results"""
    results = run_statistical_tests(data_dict)

    assert isinstance(results, dict)
    assert len(results) > 0

    found_p = False
    for test_name, result in results.items():
        if "p_value" in result:
            p = result["p_value"]
            assert isinstance(p, (int, float))
            assert 0 <= p <= 1
            found_p = True

    assert found_p