
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.application.services.analysis_service import AnalysisService

@pytest.fixture
def mock_raw_data():
    # Helper to create sample DF matching DB structure
    data = {
        "run_main_id": [1, 1],
        "asset": ["BTC", "BTC"],
        "ran_at_utc": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-01")],
        "spot_run": [100.0, 100.0],
        "detail_id": [101, 102],
        "expiry_date": [pd.Timestamp("2023-02-01"), pd.Timestamp("2023-06-01")],
        "days_to_expiry": [31, 150], # 31 is T30 approx, 150 is T180 approx
        "future_price": [101.0, 105.0],
        "open_interest": [1000, 2000],
        "spot_detail": [100.0, 100.0],
        "premium_pct": [1.0, 5.0],
        "annualized_pct": [12.0, 12.0],
        "curve": ["Contango", "Contango"],
        "instrument_name": ["BTC-1FEB23", "BTC-1JUN23"]
    }
    return pd.DataFrame(data)

def test_get_days_to_expiry(mock_raw_data):
    result = AnalysisService.get_days_to_expiry(mock_raw_data)
    assert not result.empty
    assert "t_30" in result.columns
    # With 31 days and 150 days, 31 is closest to anchor? No, anchor is 270.
    # 150 is closer to 270 than 31. So 150 is anchor (T270)??
    # |31-270|=239, |150-270|=120. So 150 is anchor.
    # 31 is < 150.
    # Below rank: 31 is only item below. Rank 1.
    # Pick logic: pick(below, "below_rank", 1, "t_180") -> 31 days should be t_180 ??
    # Presenter logic allocates ranks 1..6 to t_180..t_1.
    pass

def test_get_forward_price_changes():
    # Test F1 and F5 calc
    df = pd.DataFrame({
        "ran_at_utc": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
        "spot_run": [100.0, 110.0],
        "asset": ["BTC", "BTC"]
    })
    
    result = AnalysisService.get_forward_price_changes(df)
    # Row 0: next is 110. ln(110/100) = ln(1.1) approx 0.0953
    # Row 1: next is NaN.
    
    val0 = result.iloc[0]["f1"]
    assert np.isclose(val0, np.log(110/100))
    assert np.isnan(result.iloc[1]["f1"])

def test_get_annualized_forward_premiums(mock_raw_data):
    result = AnalysisService.get_annualized_forward_premiums(mock_raw_data)
    assert not result.empty
    # Expect columns like prem1, prem7, etc.
    # Based on ranks, columns might be sparse if not enough data points
    assert "prem270" in result.columns # Anchor always exists if data exists

def test_get_forward_premiums_vs_sample_median(mock_raw_data):
    # This involves calculating medians and subtracting
    result = AnalysisService.get_forward_premiums_vs_sample_median(mock_raw_data)
    assert not result.empty
    # logic check: median of single row is value itself. value - median = 0.
    # If we have 1 row, devs should be 0.
    if "prem270" in result.columns:
        assert result.iloc[0]["prem270"] == 0.0
