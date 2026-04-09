"""Tests for the KPI dashboard analysis.

Write at least 3 tests:
1. test_extraction_returns_dataframes — extract_data returns a dict of DataFrames
2. test_kpi_computation_returns_expected_keys — compute_kpis returns a dict with your 5 KPI names
3. test_statistical_test_returns_pvalue — run_statistical_tests returns results with p-values
"""
import pytest
import pandas as pd
from analysis import connect_db, extract_data, compute_kpis, run_statistical_tests


@pytest.fixture(scope="module")
def data_dict():
    """Fixture to extract data once for all tests."""
    engine = connect_db()
    return extract_data(engine)


def test_extraction_returns_dataframes(data_dict):
    """Connect to the database, extract data, and verify the result is a dict of DataFrames."""
    assert isinstance(data_dict, dict), "extract_data should return a dictionary"
    
    expected_tables = ["customers", "products", "orders", "order_items"]
    for table in expected_tables:
        assert table in data_dict, f"Missing table: {table}"
        assert isinstance(data_dict[table], pd.DataFrame), f"{table} should be a pandas DataFrame"
    
    # Check that filters were applied (no cancelled orders, quantity <= 100)
    assert (data_dict["orders"]["status"] != "cancelled").all(), "Cancelled orders should be excluded"
    assert (data_dict["order_items"]["quantity"] <= 100).all(), "Quantities > 100 should be excluded"


def test_kpi_computation_returns_expected_keys(data_dict):
    """Compute KPIs and verify the result contains all expected KPI names."""
    kpi_results = compute_kpis(data_dict)
    
    assert isinstance(kpi_results, dict), "compute_kpis should return a dictionary"
    
    expected_keys = [
        "total_revenue",
        "aov_by_city",
        "monthly_revenue",
        "mom_growth",
        "revenue_by_category"
    ]
    
    for key in expected_keys:
        assert key in kpi_results, f"Missing KPI key: {key}"
    
    # Basic value checks
    assert isinstance(kpi_results["total_revenue"], (int, float)), "Total revenue should be numeric"
    assert len(kpi_results["aov_by_city"]) > 0, "AOV by city should not be empty"
    assert len(kpi_results["monthly_revenue"]) > 0, "Monthly revenue should not be empty"


def test_statistical_test_returns_pvalue(data_dict):
    """Run statistical tests and verify results include p-values."""
    stat_results = run_statistical_tests(data_dict)
    
    assert isinstance(stat_results, dict), "run_statistical_tests should return a dictionary"
    assert len(stat_results) >= 1, "At least one statistical test should be present"
    
    # Check that at least one test has a valid p-value
    pvalues_found = False
    for test_name, result in stat_results.items():
        if "p_value" in result:
            p_val = result["p_value"]
            assert isinstance(p_val, (int, float)), f"p_value in {test_name} should be numeric"
            assert 0 <= p_val <= 1, f"p_value in {test_name} should be between 0 and 1"
            pvalues_found = True
    
    assert pvalues_found, "At least one test result should contain a p-value"


# Optional: Run the tests directly if file is executed
if __name__ == "__main__":
    pytest.main([__file__, "-v"])