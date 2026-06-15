import os
from pathlib import Path

from pydantic import BaseModel


def default_cache_path() -> str:
    if os.getenv("RENDER") or os.getenv("PORT"):
        return str(Path("/tmp") / "yfinance_cache")
    return "../work/yfinance_cache"


class Settings(BaseModel):
    app_name: str = "Taiwan Stock Quant MVP"
    cache_db_path: str = os.getenv("CACHE_DB_PATH", "stock_cache.sqlite3")
    yfinance_cache_path: str = os.getenv("YFINANCE_CACHE_PATH", default_cache_path())
    default_confidence: float = float(os.getenv("DEFAULT_CONFIDENCE", "0.65"))
    yahoo_delay_minutes: int | None = 15
    disclaimer: str = "量化模型結果，不構成投資建議。資料可能延遲、缺漏或受來源限制，請自行查證並承擔投資風險。"


settings = Settings()
