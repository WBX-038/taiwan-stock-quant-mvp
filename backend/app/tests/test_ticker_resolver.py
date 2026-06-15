import pytest

from app.services.ticker_resolver import TickerResolver


def test_resolve_chinese_name_to_symbol() -> None:
    resolved = TickerResolver().resolve("台積電")
    assert resolved.symbol == "2330.TW"
    assert resolved.company_name == "台灣積體電路製造"


def test_resolve_code_tries_tw_then_two() -> None:
    resolved = TickerResolver().resolve("2330")
    assert resolved.symbol == "2330.TW"
    assert resolved.attempted_symbols == ["2330.TW", "2330.TWO"]


def test_resolve_unknown_code_keeps_tw_and_two_attempts() -> None:
    resolved = TickerResolver().resolve("9999")
    assert resolved.symbol == "9999.TW"
    assert resolved.company_name is None
    assert resolved.attempted_symbols == ["9999.TW", "9999.TWO"]


def test_resolve_otc_code_uses_two_from_mapping() -> None:
    resolved = TickerResolver().resolve("8299")
    assert resolved.symbol == "8299.TWO"
    assert resolved.attempted_symbols == ["8299.TW", "8299.TWO"]


def test_resolve_unknown_name_has_clear_error() -> None:
    with pytest.raises(ValueError, match="找不到"):
        TickerResolver().resolve("不存在股票")
