from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


FactorStatus = Literal["ok", "missing", "low_confidence"]


class DataPoint(BaseModel):
    value: Any = None
    source: str
    last_updated: datetime | None = None
    is_realtime: bool = False
    delay_minutes: int | None = None
    confidence: float = Field(default=0.65, ge=0, le=1)
    missing_reason: str | None = None


class SubFactorScore(BaseModel):
    raw_value: Any = None
    score_0_to_100: float | None = None
    status: FactorStatus
    reason: str


class FactorScore(BaseModel):
    score_0_to_100: float | None = None
    status: FactorStatus
    available_subfactors: int
    total_subfactors: int
    reason: str


class CandlePoint(BaseModel):
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None


class AnalysisResponse(BaseModel):
    query: str
    resolved_symbol: str
    company_name: str | None = None
    industry_category: str | None = None
    business_focus: str | None = None
    chart_data: list[CandlePoint]
    final_score: float | None = None
    rating: str
    confidence: float
    factor_scores: dict[str, FactorScore]
    subfactor_scores: dict[str, dict[str, SubFactorScore]]
    adjusted_weights: dict[str, float]
    data_quality: dict[str, DataPoint]
    warnings: list[str]
    disclaimer: str
