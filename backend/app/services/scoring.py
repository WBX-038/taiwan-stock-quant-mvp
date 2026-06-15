from collections.abc import Callable
from typing import Any

import pandas as pd

from app.models import FactorScore, SubFactorScore
from app.services.indicators import (
    annualized_volatility,
    atr_ratio,
    average_trading_value,
    calculate_macd_histogram,
    calculate_return,
    calculate_rsi,
    finite_float,
    max_drawdown,
    moving_average_alignment,
    positive_day_ratio,
    price_position_52w,
    relative_strength_3m,
    return_stability,
    rolling_correlation,
    volume_trend,
)
from app.services.rating import rating_from_score

DEFAULT_WEIGHTS = {
    "Momentum": 15.0,
    "FundamentalHealth": 20.0,
    "TrendQuality": 15.0,
    "Growth": 10.0,
    "Volatility": 15.0,
    "Liquidity": 10.0,
    "MarketRelative": 5.0,
    "RiskReward": 10.0,
}


def score_return(value: float | None) -> float | None:
    if value is None:
        return None
    pct = value * 100
    if pct >= 30:
        return 100
    if pct >= 15:
        return 80
    if pct >= 5:
        return 65
    if pct >= 0:
        return 50
    if pct >= -10:
        return 35
    return 20


def score_rsi(value: float | None) -> float | None:
    if value is None:
        return None
    if 45 <= value <= 65:
        return 80
    if 35 <= value <= 75:
        return 65
    if 25 <= value <= 85:
        return 45
    return 25


def score_pe(value: float | None) -> float | None:
    if value is None or value <= 0:
        return None
    if value <= 12:
        return 85
    if value <= 20:
        return 75
    if value <= 35:
        return 55
    if value <= 60:
        return 35
    return 20


def score_pb(value: float | None) -> float | None:
    if value is None or value <= 0:
        return None
    if value <= 1.5:
        return 85
    if value <= 3:
        return 70
    if value <= 5:
        return 50
    return 30


def score_roe(value: float | None) -> float | None:
    if value is None:
        return None
    pct = value * 100
    if pct >= 20:
        return 90
    if pct >= 15:
        return 75
    if pct >= 10:
        return 60
    if pct >= 5:
        return 40
    return 25


def score_volatility(value: float | None) -> float | None:
    if value is None:
        return None
    pct = value * 100
    if pct <= 20:
        return 85
    if pct <= 30:
        return 70
    if pct <= 45:
        return 50
    return 30


def score_drawdown(value: float | None) -> float | None:
    if value is None:
        return None
    pct = value * 100
    if pct >= -10:
        return 85
    if pct >= -20:
        return 70
    if pct >= -35:
        return 50
    return 30


def score_higher_is_better(value: float | None, excellent: float, good: float, ok: float, weak: float) -> float | None:
    if value is None:
        return None
    if value >= excellent:
        return 90
    if value >= good:
        return 75
    if value >= ok:
        return 60
    if value >= weak:
        return 40
    return 25


def score_lower_is_better(value: float | None, excellent: float, good: float, ok: float) -> float | None:
    if value is None or value < 0:
        return None
    if value <= excellent:
        return 85
    if value <= good:
        return 70
    if value <= ok:
        return 50
    return 30


def score_trading_value(value: float | None) -> float | None:
    if value is None:
        return None
    if value >= 1_000_000_000:
        return 90
    if value >= 300_000_000:
        return 75
    if value >= 50_000_000:
        return 60
    if value >= 10_000_000:
        return 40
    return 25


def score_subfactor(raw_value: Any, scorer: Callable[[float | None], float | None], reason: str) -> SubFactorScore:
    value = finite_float(raw_value)
    score = scorer(value)
    if score is None:
        return SubFactorScore(raw_value=value, score_0_to_100=None, status="missing", reason=f"{reason} 缺資料或不適用。")
    return SubFactorScore(raw_value=value, score_0_to_100=float(score), status="ok", reason=reason)


def robust_subfactor(raw_value: Any, scorer: Callable[[float | None], float | None], reason: str) -> SubFactorScore:
    value = finite_float(raw_value)
    score = scorer(value)
    if score is None:
        return SubFactorScore(
            raw_value=value,
            score_0_to_100=None,
            status="missing",
            reason=f"{reason} 缺資料，已從主評分排除並重分配權重。",
        )
    return SubFactorScore(raw_value=value, score_0_to_100=float(score), status="ok", reason=reason)


def average_factor(subscores: dict[str, SubFactorScore]) -> FactorScore:
    total = len(subscores)
    usable = [s.score_0_to_100 for s in subscores.values() if s.score_0_to_100 is not None]
    if not usable:
        return FactorScore(score_0_to_100=None, status="missing", available_subfactors=0, total_subfactors=total, reason="所有子因子皆缺資料。")
    low_confidence = sum(1 for s in subscores.values() if s.status == "low_confidence")
    status = "low_confidence" if low_confidence > total * 0.5 else "ok"
    return FactorScore(
        score_0_to_100=round(sum(usable) / len(usable), 2),
        status=status,
        available_subfactors=len(usable),
        total_subfactors=total,
        reason="多數子因子使用中性替代分。" if status == "low_confidence" else "以穩定可取得子因子平均。",
    )


def keep_available(subscores: dict[str, SubFactorScore]) -> dict[str, SubFactorScore]:
    return {name: score for name, score in subscores.items() if score.score_0_to_100 is not None}


def adjusted_weights(factor_scores: dict[str, FactorScore], weights: dict[str, float] | None = None) -> dict[str, float]:
    base = weights or DEFAULT_WEIGHTS
    usable = {k: v for k, v in base.items() if factor_scores.get(k) and factor_scores[k].score_0_to_100 is not None}
    total = sum(usable.values())
    if total <= 0:
        return {}
    return {k: round(v / total * 100, 4) for k, v in usable.items()}


def final_score(factor_scores: dict[str, FactorScore], weights: dict[str, float] | None = None) -> tuple[float | None, dict[str, float]]:
    adj = adjusted_weights(factor_scores, weights)
    if not adj:
        return None, {}
    score = 0.0
    for factor, weight in adj.items():
        value = factor_scores[factor].score_0_to_100
        if value is not None:
            score += value * weight / 100
    return round(score, 2), adj


def build_scores(history: pd.DataFrame, info: dict[str, Any], benchmark_history: pd.DataFrame | None = None) -> dict[str, Any]:
    benchmark = benchmark_history if benchmark_history is not None else pd.DataFrame()
    return_1m = calculate_return(history, 21)
    return_3m = calculate_return(history, 63)
    return_6m = calculate_return(history, 126)
    return_12m = calculate_return(history, 252)
    rel_strength = relative_strength_3m(history, benchmark)
    vol = annualized_volatility(history)
    drawdown = max_drawdown(history)
    atr = atr_ratio(history)

    raw_subfactor_scores: dict[str, dict[str, SubFactorScore]] = {
        "Momentum": {
            "return_1m": robust_subfactor(return_1m, score_return, "1 個月報酬率"),
            "return_3m": robust_subfactor(return_3m, score_return, "3 個月報酬率"),
            "return_6m": robust_subfactor(return_6m, score_return, "6 個月報酬率"),
            "rsi_14": robust_subfactor(calculate_rsi(history), score_rsi, "RSI 14"),
            "macd_histogram": robust_subfactor(calculate_macd_histogram(history), lambda v: 70 if v is not None and v > 0 else (40 if v is not None else None), "MACD histogram 正負"),
        },
        "FundamentalHealth": {
            "trailing_pe": robust_subfactor(info.get("trailingPE"), score_pe, "本益比；PE <= 0 視為基本面資料不足"),
            "price_to_book": robust_subfactor(info.get("priceToBook"), score_pb, "股價淨值比；避免題材股估值過熱"),
            "dividend_yield": robust_subfactor(info.get("dividendYield"), lambda v: score_higher_is_better(v, 0.05, 0.03, 0.015, 0), "股息殖利率；檢查現金回饋與成熟度"),
            "return_on_equity": robust_subfactor(info.get("returnOnEquity"), score_roe, "ROE；若台股資料源缺漏則採中性分"),
            "debt_to_equity": robust_subfactor(info.get("debtToEquity"), lambda v: score_lower_is_better(v, 50, 120, 250), "負債權益比；避免高槓桿轉機股過度加分"),
        },
        "TrendQuality": {
            "positive_day_ratio_6m": robust_subfactor(positive_day_ratio(history, 126), lambda v: score_higher_is_better(v, 0.56, 0.52, 0.48, 0.44), "6 個月上漲日比例"),
            "return_stability_6m": robust_subfactor(return_stability(history, 126), lambda v: score_higher_is_better(v, 0.10, 0.05, 0.00, -0.05), "6 個月報酬穩定度"),
            "moving_average_alignment": robust_subfactor(moving_average_alignment(history), lambda v: score_higher_is_better(v, 1.0, 0.5, 0.49, 0.0), "收盤價、50 日與 200 日均線結構"),
            "drawdown_quality": robust_subfactor(drawdown, score_drawdown, "回撤控制品質"),
        },
        "Growth": {
            "official_monthly_revenue_yoy": robust_subfactor(info.get("monthlyRevenueYoY") or info.get("revenueGrowth"), lambda v: score_higher_is_better(v, 0.25, 0.12, 0.03, -0.05), "官方月營收年增率"),
            "official_cumulative_revenue_yoy": robust_subfactor(info.get("cumulativeRevenueYoY"), lambda v: score_higher_is_better(v, 0.20, 0.10, 0.02, -0.05), "官方累計營收年增率"),
            "price_growth_1m": robust_subfactor(return_1m, score_return, "1 個月市場驗證成長"),
            "price_growth_3m": robust_subfactor(return_3m, score_return, "3 個月市場驗證成長"),
            "price_growth_6m": robust_subfactor(return_6m, score_return, "6 個月市場驗證成長"),
            "price_growth_12m": robust_subfactor(return_12m, score_return, "12 個月市場驗證成長"),
            "growth_consistency": robust_subfactor(None if return_3m is None or return_6m is None else min(return_3m, return_6m), score_return, "3/6 個月成長一致性；降低單月題材急漲的影響"),
        },
        "Volatility": {
            "annualized_volatility_30d": robust_subfactor(vol, score_volatility, "30 日年化波動率"),
            "max_drawdown": robust_subfactor(drawdown, score_drawdown, "最大回撤"),
            "atr_ratio": robust_subfactor(atr, lambda v: score_lower_is_better(v, 0.025, 0.05, 0.08), "ATR 佔比"),
            "volatility_adjusted_return": robust_subfactor(None if return_3m is None or vol in (None, 0) else return_3m / vol, lambda v: score_higher_is_better(v, 0.8, 0.4, 0.0, -0.4), "3 個月風險調整報酬"),
        },
        "Liquidity": {
            "average_trading_value_20d": robust_subfactor(average_trading_value(history, 20), score_trading_value, "20 日平均成交金額"),
            "volume_trend_20v60": robust_subfactor(volume_trend(history, 20, 60), lambda v: score_higher_is_better(v, 0.50, 0.20, 0.00, -0.30), "20 日成交量相對 60 日趨勢"),
            "price_volume_confirm": robust_subfactor(
                None if return_3m is None or volume_trend(history, 20, 60) is None else return_3m + volume_trend(history, 20, 60),
                score_return,
                "價量確認 proxy：3 個月報酬加上量能趨勢",
            ),
        },
        "MarketRelative": {
            "relative_strength_3m": robust_subfactor(rel_strength, score_return, "相對 ^TWII 3 個月強度；低權重，只作市場驗證"),
            "twii_correlation_6m": robust_subfactor(rolling_correlation(history, benchmark), lambda v: None if v is None else max(25, min(85, 85 - abs(v) * 35)), "與 ^TWII 6 個月日報酬相關性"),
            "relative_trend_confirm": robust_subfactor(None if rel_strength is None or return_3m is None else rel_strength + return_3m, score_return, "相對強度與自身趨勢確認"),
        },
        "RiskReward": {
            "price_position_52w": robust_subfactor(price_position_52w(history), lambda v: score_higher_is_better(v, 0.8, 0.6, 0.35, 0.15), "52 週價格位置"),
            "return_to_drawdown": robust_subfactor(None if return_6m is None or drawdown in (None, 0) else return_6m / abs(drawdown), lambda v: score_higher_is_better(v, 1.5, 0.8, 0.2, -0.2), "6 個月報酬相對最大回撤"),
            "return_to_atr": robust_subfactor(None if return_3m is None or atr in (None, 0) else return_3m / atr, lambda v: score_higher_is_better(v, 8, 4, 1, -1), "3 個月報酬相對 ATR"),
        },
    }
    subfactor_scores = {factor: keep_available(scores) for factor, scores in raw_subfactor_scores.items()}
    subfactor_scores = {factor: scores for factor, scores in subfactor_scores.items() if scores}
    factor_scores = {factor: average_factor(scores) for factor, scores in subfactor_scores.items()}
    total, weights = final_score(factor_scores)
    return {
        "factor_scores": factor_scores,
        "subfactor_scores": subfactor_scores,
        "final_score": total,
        "adjusted_weights": weights,
        "rating": rating_from_score(total),
    }
