import numpy as np
import pandas as pd

from app.services.indicators import calculate_macd_histogram, calculate_return, calculate_rsi
from app.services.yahoo_provider import sanitize_dataframe


def make_history(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": values,
            "High": [v * 1.02 for v in values],
            "Low": [v * 0.98 for v in values],
            "Close": values,
            "Adj Close": values,
            "Volume": [1000] * len(values),
        }
    )


def test_empty_yfinance_dataframe_does_not_crash() -> None:
    cleaned = sanitize_dataframe(pd.DataFrame())
    assert cleaned.empty
    assert "Close" in cleaned.columns


def test_rsi_calculation_returns_value() -> None:
    history = make_history([100 + i + (i % 3) for i in range(40)])
    rsi = calculate_rsi(history)
    assert rsi is not None
    assert 0 <= rsi <= 100


def test_macd_calculation_returns_value() -> None:
    history = make_history([100 + i * 0.5 for i in range(80)])
    macd = calculate_macd_histogram(history)
    assert macd is not None


def test_returns_calculation() -> None:
    history = make_history([100] * 21 + [110])
    result = calculate_return(history, 21)
    assert result is not None
    assert abs(result - 0.1) < 1e-9


def test_sanitize_nan_and_inf() -> None:
    history = pd.DataFrame({"Close": [1, np.nan, np.inf]})
    cleaned = sanitize_dataframe(history)
    assert cleaned["Close"].iloc[1] is None
    assert cleaned["Close"].iloc[2] is None
