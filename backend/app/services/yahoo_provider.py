from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from app.config import settings
from app.models import DataPoint
from app.services.data_provider import MarketDataProvider, empty_history


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): sanitize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_value(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, pd.DataFrame)) else False:
        return None
    return value


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return empty_history()
    cleaned = df.replace([np.inf, -np.inf], np.nan).astype(object)
    return cleaned.where(pd.notnull(cleaned), None)


def parse_number(value: Any, percent: bool = False) -> float | None:
    if value in (None, "", "-", "--", "N/A"):
        return None
    try:
        result = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result / 100 if percent else result


class YahooProvider(MarketDataProvider):
    source = "yfinance"

    def _point(
        self,
        value: Any,
        missing_reason: str | None = None,
        source: str | None = None,
        confidence: float | None = None,
    ) -> DataPoint:
        return DataPoint(
            value=value,
            source=source or self.source,
            last_updated=datetime.now(timezone.utc),
            is_realtime=False,
            delay_minutes=settings.yahoo_delay_minutes,
            confidence=confidence if confidence is not None else settings.default_confidence,
            missing_reason=missing_reason,
        )

    def _ticker(self, symbol: str):
        import yfinance as yf

        cache_path = Path(settings.yfinance_cache_path)
        if not cache_path.is_absolute():
            cache_path = Path(__file__).resolve().parents[3] / "work" / "yfinance_cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        yf.cache.set_cache_location(str(cache_path))
        return yf.Ticker(symbol)

    def _chart_history(self, symbol: str, period: str = "2y") -> DataPoint:
        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={"range": period, "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            if response.status_code != 200:
                return self._point(empty_history(), f"Yahoo chart API HTTP {response.status_code}", "yahoo_chart_api", 0.60)

            payload = response.json()
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                error = (payload.get("chart") or {}).get("error") or {}
                return self._point(empty_history(), error.get("description") or "Yahoo chart API returned no data.", "yahoo_chart_api", 0.60)

            item = result[0]
            timestamps = item.get("timestamp") or []
            quote = (((item.get("indicators") or {}).get("quote") or [{}])[0]) or {}
            adjclose = (((item.get("indicators") or {}).get("adjclose") or [{}])[0] or {}).get("adjclose")
            if not timestamps or not quote:
                return self._point(empty_history(), "Yahoo chart API missing time-series fields.", "yahoo_chart_api", 0.60)

            df = pd.DataFrame(
                {
                    "Open": quote.get("open"),
                    "High": quote.get("high"),
                    "Low": quote.get("low"),
                    "Close": quote.get("close"),
                    "Adj Close": adjclose if adjclose is not None else quote.get("close"),
                    "Volume": quote.get("volume"),
                },
                index=pd.to_datetime(timestamps, unit="s", utc=True).tz_convert("Asia/Taipei").tz_localize(None),
            )
            df = sanitize_dataframe(df.dropna(subset=["Close"], how="all"))
            if df.empty:
                return self._point(empty_history(), "Yahoo chart API returned empty price history.", "yahoo_chart_api", 0.60)
            return self._point(df, source="yahoo_chart_api", confidence=0.60)
        except Exception as exc:
            return self._point(empty_history(), f"Yahoo chart API failed: {exc}", "yahoo_chart_api", 0.60)

    def _recent_dates(self) -> list[datetime]:
        today = datetime.now(timezone.utc).astimezone().replace(tzinfo=None)
        return [today - timedelta(days=days) for days in range(0, 21)]

    def _twse_valuation(self, code: str) -> dict[str, Any]:
        for day in self._recent_dates():
            date = day.strftime("%Y%m%d")
            try:
                response = requests.get(
                    "https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d",
                    params={"date": date, "selectType": "ALL", "response": "json"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15,
                )
                payload = response.json()
            except Exception:
                continue
            if payload.get("stat") != "OK":
                continue
            for row in payload.get("data") or []:
                if str(row[0]).strip() == code:
                    return {
                        "shortName": str(row[1]).strip(),
                        "currentPrice": parse_number(row[2]),
                        "dividendYield": parse_number(row[3], percent=True),
                        "trailingPE": parse_number(row[5]),
                        "priceToBook": parse_number(row[6]),
                        "_valuationSource": "TWSE BWIBBU",
                        "_valuationDate": date,
                    }
        return {}

    def _tpex_valuation(self, code: str) -> dict[str, Any]:
        for day in self._recent_dates():
            date = day.strftime("%Y/%m/%d")
            try:
                response = requests.get(
                    "https://www.tpex.org.tw/www/zh-tw/afterTrading/peQryDate",
                    params={"date": date, "response": "json"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15,
                )
                payload = response.json()
            except Exception:
                continue
            tables = payload.get("tables") or []
            rows = tables[0].get("data") if tables else []
            for row in rows or []:
                if str(row[0]).strip() == code:
                    return {
                        "shortName": str(row[1]).strip(),
                        "trailingPE": parse_number(row[2]),
                        "dividendYield": parse_number(row[5], percent=True),
                        "priceToBook": parse_number(row[6]),
                        "_valuationSource": "TPEx peQryDate",
                        "_valuationDate": date,
                    }
        return {}

    def _public_valuation(self, symbol: str) -> dict[str, Any]:
        code = symbol.split(".")[0]
        if symbol.endswith(".TWO"):
            return self._tpex_valuation(code)
        if symbol.endswith(".TW"):
            return self._twse_valuation(code)
        return {}

    def _monthly_revenue_growth(self, symbol: str) -> dict[str, Any]:
        code = symbol.split(".")[0]
        if symbol.endswith(".TWO"):
            url = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O"
            source = "TPEx monthly revenue"
        elif symbol.endswith(".TW"):
            url = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"
            source = "TWSE monthly revenue"
        else:
            return {}

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=20)
            if response.status_code != 200:
                return {}
            rows = response.json()
        except Exception:
            return {}

        for row in rows if isinstance(rows, list) else []:
            if str(row.get("公司代號", "")).strip() == code:
                monthly_yoy = parse_number(row.get("營業收入-去年同月增減(%)"), percent=True)
                cumulative_yoy = parse_number(row.get("累計營業收入-前期比較增減(%)"), percent=True)
                result: dict[str, Any] = {
                    "shortName": row.get("公司名稱"),
                    "industryCategory": row.get("產業別"),
                    "_revenueSource": source,
                    "_revenueDate": row.get("出表日期"),
                    "_revenueMonth": row.get("資料年月"),
                }
                if monthly_yoy is not None:
                    result["revenueGrowth"] = monthly_yoy
                    result["monthlyRevenueYoY"] = monthly_yoy
                if cumulative_yoy is not None:
                    result["cumulativeRevenueYoY"] = cumulative_yoy
                return result
        return {}

    def _company_profile(self, symbol: str) -> dict[str, Any]:
        code = symbol.split(".")[0]
        if symbol.endswith(".TWO"):
            url = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
            source = "TPEx company profile"
        elif symbol.endswith(".TW"):
            url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
            source = "TWSE company profile"
        else:
            return {}

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=20)
            if response.status_code != 200:
                return {}
            rows = response.json()
        except Exception:
            return {}

        for row in rows if isinstance(rows, list) else []:
            row_code = row.get("公司代號") or row.get("SecuritiesCompanyCode")
            if str(row_code or "").strip() != code:
                continue
            return {
                "companyFullName": row.get("公司名稱") or row.get("CompanyName"),
                "shortName": row.get("公司簡稱") or row.get("CompanyAbbreviation"),
                "chairman": row.get("董事長") or row.get("Chairman"),
                "generalManager": row.get("總經理") or row.get("GeneralManager"),
                "listingDate": row.get("上市日期") or row.get("DateOfListing"),
                "incorporationDate": row.get("成立日期") or row.get("DateOfIncorporation"),
                "paidInCapital": parse_number(row.get("實收資本額") or row.get("Paidin.Capital.NTDollars")),
                "companyWebsite": row.get("網址") or row.get("URL"),
                "_profileSource": source,
            }
        return {}

    def get_price_history(self, symbol: str, period: str = "2y") -> DataPoint:
        try:
            df = self._ticker(symbol).history(period=period, auto_adjust=False, timeout=10)
            df = sanitize_dataframe(df)
            if not df.empty:
                return self._point(df)
            fallback = self._chart_history(symbol, period)
            if fallback.missing_reason is None:
                return fallback
            return self._point(empty_history(), f"yfinance returned empty price history; {fallback.missing_reason}")
        except Exception as exc:
            fallback = self._chart_history(symbol, period)
            if fallback.missing_reason is None:
                return fallback
            return self._point(empty_history(), f"yfinance price history failed: {exc}; {fallback.missing_reason}")

    def get_info(self, symbol: str) -> DataPoint:
        warnings: list[str] = []
        info: dict[str, Any] = {}
        try:
            info = self._ticker(symbol).info or {}
        except Exception as exc:
            warnings.append(f"yfinance info failed: {exc}")

        public_valuation = self._public_valuation(symbol)
        if public_valuation:
            for key, value in public_valuation.items():
                if info.get(key) in (None, "", "-", "--"):
                    info[key] = value

        public_revenue = self._monthly_revenue_growth(symbol)
        if public_revenue:
            for key, value in public_revenue.items():
                if info.get(key) in (None, "", "-", "--"):
                    info[key] = value

        public_profile = self._company_profile(symbol)
        if public_profile:
            for key, value in public_profile.items():
                if info.get(key) in (None, "", "-", "--"):
                    info[key] = value

        if info:
            source = "yfinance"
            confidence = settings.default_confidence
            if public_valuation or public_revenue or public_profile:
                source = "yfinance+twse_tpex_public"
                confidence = 0.70
            reason = "; ".join(warnings) if warnings else None
            return self._point(sanitize_value(info), reason, source=source, confidence=confidence)

        if warnings:
            return self._point({}, "; ".join(warnings))
        return self._point({}, f"No info returned for {symbol}.")

    def get_fast_info(self, symbol: str) -> DataPoint:
        try:
            fast_info = dict(self._ticker(symbol).fast_info or {})
            if not fast_info:
                return self._point({}, f"No fast_info returned for {symbol}.")
            return self._point(sanitize_value(fast_info))
        except Exception as exc:
            return self._point({}, f"yfinance fast_info failed: {exc}")
