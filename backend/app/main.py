from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import AnalysisResponse, CandlePoint, DataPoint
from app.services.scoring import build_scores
from app.services.ticker_resolver import TickerResolver
from app.services.yahoo_provider import YahooProvider


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resolver = TickerResolver()
provider = YahooProvider()
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

CURATED_BUSINESS_FOCUS: dict[str, str] = {
    "2330": "全球晶圓代工龍頭，市佔約 72.3%；核心受惠先進製程、AI/HPC 與高階封裝需求。",
}


def value_as_dataframe(point: DataPoint) -> pd.DataFrame:
    return point.value if isinstance(point.value, pd.DataFrame) else pd.DataFrame()


def has_usable_history(point: DataPoint) -> bool:
    return isinstance(point.value, pd.DataFrame) and not point.value.empty and point.missing_reason is None


def fetch_symbol_bundle(symbol: str) -> tuple[DataPoint, DataPoint, DataPoint]:
    return (
        provider.get_price_history(symbol, period="2y"),
        provider.get_info(symbol),
        provider.get_fast_info(symbol),
    )


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def make_chart_data(history: pd.DataFrame, rows: int = 90) -> list[CandlePoint]:
    if history is None or history.empty:
        return []
    required = ["Open", "High", "Low", "Close"]
    if not all(column in history.columns for column in required):
        return []
    frame = history.tail(rows)
    candles: list[CandlePoint] = []
    for index, row in frame.iterrows():
        candles.append(
            CandlePoint(
                date=pd.Timestamp(index).strftime("%Y-%m-%d"),
                open=finite_number(row.get("Open")),
                high=finite_number(row.get("High")),
                low=finite_number(row.get("Low")),
                close=finite_number(row.get("Close")),
                volume=finite_number(row.get("Volume")),
            )
        )
    return candles


def business_focus_from_info(info: dict[str, Any]) -> str | None:
    code = str(info.get("symbol") or "").split(".")[0]
    if not code:
        code = str(info.get("code") or info.get("公司代號") or "").strip()
    if code in CURATED_BUSINESS_FOCUS:
        return CURATED_BUSINESS_FOCUS[code]

    summary = info.get("longBusinessSummary") or info.get("businessSummary")
    if isinstance(summary, str) and summary.strip():
        text = " ".join(summary.split())
        first_sentence = text.split(". ")[0].strip()
        return (first_sentence or text)[:180]

    parts: list[str] = []
    industry = info.get("industryCategory") or info.get("industry") or info.get("sector")
    if industry:
        parts.append(f"產業分類：{industry}")

    monthly_yoy = info.get("monthlyRevenueYoY")
    cumulative_yoy = info.get("cumulativeRevenueYoY")
    revenue_notes = []
    if monthly_yoy is not None:
        revenue_notes.append(f"最新月營收年增 {float(monthly_yoy) * 100:.2f}%")
    if cumulative_yoy is not None:
        revenue_notes.append(f"累計營收年增 {float(cumulative_yoy) * 100:.2f}%")
    if revenue_notes:
        parts.append("；".join(revenue_notes))

    if parts:
        return "；".join(parts) + "。"

    pieces = []
    sector = info.get("sector")
    industry = info.get("industry")
    if sector:
        pieces.append(f"Sector: {sector}")
    if industry:
        pieces.append(f"Industry: {industry}")
    return "；".join(pieces) if pieces else None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/analyze", response_model=AnalysisResponse)
def analyze(query: str) -> AnalysisResponse:
    try:
        resolved = resolver.resolve(query)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    selected_symbol = resolved.symbol
    history_point, info_point, fast_info_point = fetch_symbol_bundle(selected_symbol)
    symbol_attempt_warnings: list[str] = []

    if not has_usable_history(history_point):
        symbol_attempt_warnings.append(f"{selected_symbol}: {history_point.missing_reason or '沒有可用價格資料'}")
        for candidate in resolved.attempted_symbols:
            if candidate == selected_symbol:
                continue
            candidate_history, candidate_info, candidate_fast_info = fetch_symbol_bundle(candidate)
            if has_usable_history(candidate_history):
                selected_symbol = candidate
                history_point = candidate_history
                info_point = candidate_info
                fast_info_point = candidate_fast_info
                break
            symbol_attempt_warnings.append(f"{candidate}: {candidate_history.missing_reason or '沒有可用價格資料'}")

    if not has_usable_history(history_point) and len(resolved.attempted_symbols) > 1:
        raise HTTPException(status_code=404, detail=f"找不到「{query}」的上市 .TW 或上櫃 .TWO 可用市場資料。")

    benchmark_point = provider.get_price_history("^TWII", period="2y")
    history = value_as_dataframe(history_point)
    info = info_point.value if isinstance(info_point.value, dict) else {}
    fast_info = fast_info_point.value if isinstance(fast_info_point.value, dict) else {}
    company_name = resolved.company_name or info.get("longName") or info.get("shortName") or selected_symbol
    info.setdefault("symbol", selected_symbol)
    industry_category = info.get("industryCategory") or info.get("industry") or info.get("sector")

    scores = build_scores(history, info, value_as_dataframe(benchmark_point))
    warnings = [
        "主評分加入基本面健康度，用 PE、PB、殖利率、ROE、負債權益比檢查題材股是否有基本面支撐。",
        "缺資料子因子會從主評分排除並重分配權重，不再用 50 分作假中性分。",
        "K 線圖使用同一份非即時公開價格資料；資料可能延遲、缺漏或受限流。",
        "產業分類優先使用 TWSE/TPEx 月營收公開資料，其次使用 yfinance industry/sector。",
    ]
    warnings.extend(symbol_attempt_warnings)

    for point_name, point in {
        "price_history": history_point,
        "info": info_point,
        "fast_info": fast_info_point,
        "benchmark_history": benchmark_point,
    }.items():
        if point.missing_reason:
            warnings.append(f"{point_name}: {point.missing_reason}")

    factor_scores = scores["factor_scores"]
    low_confidence_count = sum(1 for factor in factor_scores.values() if factor.status == "low_confidence")
    missing_count = sum(1 for factor in factor_scores.values() if factor.status == "missing")
    confidence = max(0.1, round(0.85 - low_confidence_count * 0.08 - missing_count * 0.12, 2))

    return AnalysisResponse(
        query=query,
        resolved_symbol=selected_symbol,
        company_name=company_name,
        industry_category=industry_category,
        business_focus=business_focus_from_info(info),
        chart_data=make_chart_data(history),
        final_score=scores["final_score"],
        rating=scores["rating"],
        confidence=confidence,
        factor_scores=factor_scores,
        subfactor_scores=scores["subfactor_scores"],
        adjusted_weights=scores["adjusted_weights"],
        data_quality={
            "price_history": history_point.model_copy(update={"value": "dataframe" if history_point.value is not None else None}),
            "info": info_point.model_copy(update={"value": {"available_keys": sorted(info.keys())[:80]}}),
            "fast_info": fast_info_point.model_copy(update={"value": fast_info}),
            "benchmark_history": benchmark_point.model_copy(update={"value": "dataframe" if benchmark_point.value is not None else None}),
        },
        warnings=warnings,
        disclaimer=settings.disclaimer,
    )
