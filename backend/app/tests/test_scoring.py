import math

import pandas as pd

from app.services.rating import rating_from_score
from app.services.scoring import average_factor, build_scores, score_pe, score_subfactor


def make_history(start: float = 100, days: int = 300) -> pd.DataFrame:
    values = [start + i * 0.2 for i in range(days)]
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


def test_nan_does_not_enter_average() -> None:
    subs = {
        "ok": score_subfactor(10, lambda value: 80 if value is not None else None, "ok"),
        "nan": score_subfactor(math.nan, lambda value: 80 if value is not None else None, "nan"),
    }
    factor = average_factor(subs)
    assert factor.score_0_to_100 == 80
    assert factor.available_subfactors == 1


def test_missing_fundamentals_are_excluded_not_scored_50() -> None:
    history = make_history()
    scores = build_scores(history, {}, history)
    weights = scores["adjusted_weights"]
    assert scores["final_score"] is not None
    assert round(sum(weights.values()), 2) == 100.00
    assert "FundamentalHealth" not in weights
    assert "Sentiment" not in weights
    assert "Valuation" not in weights


def test_rating_ranges() -> None:
    assert rating_from_score(90) == "強力買進"
    assert rating_from_score(70) == "買進"
    assert rating_from_score(50) == "持有"
    assert rating_from_score(30) == "賣出"
    assert rating_from_score(29) == "強力賣出"


def test_available_fundamentals_enter_score_without_missing_subfactors() -> None:
    history = make_history()
    result = build_scores(
        history,
        {
            "trailingPE": 15,
            "priceToBook": 2.0,
            "dividendYield": 0.03,
            "monthlyRevenueYoY": 0.12,
            "cumulativeRevenueYoY": 0.08,
        },
        history,
    )
    assert "FundamentalHealth" in result["factor_scores"]
    assert result["factor_scores"]["FundamentalHealth"].score_0_to_100 is not None
    assert all(sub.status != "missing" for scores in result["subfactor_scores"].values() for sub in scores.values())
    assert result["final_score"] is not None
    assert not math.isnan(result["final_score"])


def test_negative_pe_is_missing_not_cheap() -> None:
    assert score_pe(-5) is None


def test_final_score_has_no_nan_when_some_factors_missing() -> None:
    history = make_history()
    result = build_scores(history, {"trailingPE": None}, history)
    score = result["final_score"]
    assert score is not None
    assert not math.isnan(score)
