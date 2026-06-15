import math

import numpy as np
import pandas as pd


def finite_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def close_series(history: pd.DataFrame) -> pd.Series:
    if history is None or history.empty:
        return pd.Series(dtype="float64")
    column = "Adj Close" if "Adj Close" in history.columns else "Close"
    if column not in history.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(history[column], errors="coerce").dropna()


def calculate_return(history: pd.DataFrame, trading_days: int) -> float | None:
    closes = close_series(history)
    if len(closes) <= trading_days:
        return None
    start = finite_float(closes.iloc[-trading_days - 1])
    end = finite_float(closes.iloc[-1])
    if start is None or end is None or start == 0:
        return None
    return end / start - 1


def calculate_rsi(history: pd.DataFrame, period: int = 14) -> float | None:
    closes = close_series(history)
    if len(closes) <= period:
        return None
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    last_loss = finite_float(loss.iloc[-1])
    last_gain = finite_float(gain.iloc[-1])
    if last_loss is None or last_gain is None:
        return None
    if last_loss == 0:
        return 100.0
    rs = last_gain / last_loss
    return finite_float(100 - (100 / (1 + rs)))


def calculate_macd_histogram(history: pd.DataFrame) -> float | None:
    closes = close_series(history)
    if len(closes) < 35:
        return None
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return finite_float((macd - signal).iloc[-1])


def annualized_volatility(history: pd.DataFrame, window: int = 30) -> float | None:
    closes = close_series(history)
    if len(closes) <= window:
        return None
    returns = closes.pct_change().dropna().tail(window)
    vol = returns.std() * np.sqrt(252)
    return finite_float(vol)


def max_drawdown(history: pd.DataFrame) -> float | None:
    closes = close_series(history)
    if closes.empty:
        return None
    running_max = closes.cummax()
    drawdown = closes / running_max - 1
    return finite_float(drawdown.min())


def atr_ratio(history: pd.DataFrame, period: int = 14) -> float | None:
    if history is None or history.empty or not {"High", "Low", "Close"}.issubset(history.columns):
        return None
    high = pd.to_numeric(history["High"], errors="coerce")
    low = pd.to_numeric(history["Low"], errors="coerce")
    close = pd.to_numeric(history["Close"], errors="coerce")
    if len(close.dropna()) <= period:
        return None
    prev_close = close.shift(1)
    true_range = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = true_range.rolling(period).mean().iloc[-1]
    last_close = close.dropna().iloc[-1]
    if not last_close:
        return None
    return finite_float(atr / last_close)


def rolling_correlation(left_history: pd.DataFrame, right_history: pd.DataFrame, days: int = 126) -> float | None:
    left = close_series(left_history).pct_change().dropna().tail(days)
    right = close_series(right_history).pct_change().dropna().tail(days)
    joined = pd.concat([left.rename("left"), right.rename("right")], axis=1, join="inner").dropna()
    if len(joined) < 30:
        return None
    return finite_float(joined["left"].corr(joined["right"]))


def relative_strength_3m(stock_history: pd.DataFrame, benchmark_history: pd.DataFrame) -> float | None:
    stock_return = calculate_return(stock_history, 63)
    benchmark_return = calculate_return(benchmark_history, 63)
    if stock_return is None or benchmark_return is None:
        return None
    return finite_float(stock_return - benchmark_return)


def price_position_52w(history: pd.DataFrame) -> float | None:
    closes = close_series(history).tail(252)
    if len(closes) < 30:
        return None
    low = finite_float(closes.min())
    high = finite_float(closes.max())
    current = finite_float(closes.iloc[-1])
    if low is None or high is None or current is None or high == low:
        return None
    return finite_float((current - low) / (high - low))


def positive_day_ratio(history: pd.DataFrame, days: int = 126) -> float | None:
    closes = close_series(history)
    if len(closes) < 30:
        return None
    returns = closes.pct_change().dropna().tail(days)
    if returns.empty:
        return None
    return finite_float((returns > 0).mean())


def return_stability(history: pd.DataFrame, days: int = 126) -> float | None:
    closes = close_series(history)
    if len(closes) < 30:
        return None
    returns = closes.pct_change().dropna().tail(days)
    std = finite_float(returns.std())
    mean = finite_float(returns.mean())
    if std is None or mean is None or std == 0:
        return None
    return finite_float(mean / std)


def moving_average_alignment(history: pd.DataFrame) -> float | None:
    closes = close_series(history)
    if len(closes) < 200:
        return None
    current = finite_float(closes.iloc[-1])
    ma50 = finite_float(closes.tail(50).mean())
    ma200 = finite_float(closes.tail(200).mean())
    if current is None or ma50 is None or ma200 is None:
        return None
    score = 0
    if current > ma50:
        score += 0.5
    if ma50 > ma200:
        score += 0.5
    return finite_float(score)


def average_trading_value(history: pd.DataFrame, days: int = 20) -> float | None:
    if history is None or history.empty or not {"Close", "Volume"}.issubset(history.columns):
        return None
    close = pd.to_numeric(history["Close"], errors="coerce")
    volume = pd.to_numeric(history["Volume"], errors="coerce")
    value = (close * volume).dropna().tail(days)
    if value.empty:
        return None
    return finite_float(value.mean())


def volume_trend(history: pd.DataFrame, short_days: int = 20, long_days: int = 60) -> float | None:
    if history is None or history.empty or "Volume" not in history.columns:
        return None
    volume = pd.to_numeric(history["Volume"], errors="coerce").dropna()
    if len(volume) < long_days:
        return None
    long_avg = finite_float(volume.tail(long_days).mean())
    short_avg = finite_float(volume.tail(short_days).mean())
    if long_avg is None or short_avg is None or long_avg == 0:
        return None
    return finite_float(short_avg / long_avg - 1)
