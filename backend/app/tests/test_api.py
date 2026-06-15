import pandas as pd
from fastapi.testclient import TestClient

from app import main
from app.models import DataPoint


def make_history(days: int = 300) -> pd.DataFrame:
    values = [100 + i * 0.2 for i in range(days)]
    return pd.DataFrame(
        {
            "Open": values,
            "High": [v * 1.01 for v in values],
            "Low": [v * 0.99 for v in values],
            "Close": values,
            "Adj Close": values,
            "Volume": [1000] * days,
        }
    )


class FallbackProvider:
    def get_price_history(self, symbol: str, period: str = "2y") -> DataPoint:
        if symbol == "9999.TW":
            return DataPoint(value=pd.DataFrame(), source="test", missing_reason="no TW data")
        return DataPoint(value=make_history(), source="test")

    def get_info(self, symbol: str) -> DataPoint:
        return DataPoint(
            value={
                "shortName": symbol,
                "trailingPE": 15,
                "returnOnEquity": 0.2,
                "revenueGrowth": 0.1,
                "earningsGrowth": 0.1,
            },
            source="test",
        )

    def get_fast_info(self, symbol: str) -> DataPoint:
        return DataPoint(value={}, source="test")


def test_analyze_unknown_code_falls_back_to_two(monkeypatch) -> None:
    monkeypatch.setattr(main, "provider", FallbackProvider())
    client = TestClient(main.app)
    response = client.get("/api/analyze", params={"query": "9999"})
    body = response.json()
    assert response.status_code == 200
    assert body["resolved_symbol"] == "9999.TWO"
    assert body["final_score"] is not None
    assert len(body["chart_data"]) > 0
    assert "industry_category" in body
    assert "business_focus" in body
    assert "FundamentalHealth" in body["factor_scores"]
    assert "TrendQuality" in body["factor_scores"]
    assert "RiskReward" in body["factor_scores"]
