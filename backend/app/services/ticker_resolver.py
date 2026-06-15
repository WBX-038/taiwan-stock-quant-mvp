from dataclasses import dataclass


TAIWAN_STOCKS: dict[str, tuple[str, str]] = {
    "台積電": ("2330.TW", "台灣積體電路製造"),
    "鴻海": ("2317.TW", "鴻海精密"),
    "聯發科": ("2454.TW", "聯發科技"),
    "聯電": ("2303.TW", "聯華電子"),
    "台達電": ("2308.TW", "台達電子"),
    "中華電": ("2412.TW", "中華電信"),
    "富邦金": ("2881.TW", "富邦金融控股"),
    "國泰金": ("2882.TW", "國泰金融控股"),
    "長榮": ("2603.TW", "長榮海運"),
    "陽明": ("2609.TW", "陽明海運"),
    "欣興": ("3037.TW", "欣興電子"),
    "廣達": ("2382.TW", "廣達電腦"),
    "緯創": ("3231.TW", "緯創資通"),
    "兆豐金": ("2886.TW", "兆豐金融控股"),
    "玉山金": ("2884.TW", "玉山金融控股"),
    "中信金": ("2891.TW", "中國信託金融控股"),
    "元大金": ("2885.TW", "元大金融控股"),
    "華碩": ("2357.TW", "華碩電腦"),
    "大立光": ("3008.TW", "大立光電"),
    "群聯": ("8299.TWO", "群聯電子"),
}

CODE_TO_SYMBOL = {symbol.split(".")[0]: (symbol, name) for symbol, name in TAIWAN_STOCKS.values()}


@dataclass(frozen=True)
class ResolvedTicker:
    symbol: str
    company_name: str | None
    attempted_symbols: list[str]


class TickerResolver:
    def __init__(self, stock_mapping: dict[str, tuple[str, str]] | None = None) -> None:
        self.stock_mapping = stock_mapping or TAIWAN_STOCKS
        self.code_mapping = {symbol.split(".")[0]: (symbol, name) for symbol, name in self.stock_mapping.values()}

    def resolve(self, query: str) -> ResolvedTicker:
        clean = (query or "").strip()
        if not clean:
            raise ValueError("請輸入股票名稱或代號。")

        if "." in clean and clean.upper().endswith((".TW", ".TWO")):
            code = clean.split(".")[0]
            name = self.code_mapping.get(code, (None, None))[1]
            return ResolvedTicker(symbol=clean.upper(), company_name=name, attempted_symbols=[clean.upper()])

        if clean in self.stock_mapping:
            symbol, name = self.stock_mapping[clean]
            return ResolvedTicker(symbol=symbol, company_name=name, attempted_symbols=[symbol])

        if clean.isdigit():
            if clean in self.code_mapping:
                symbol, name = self.code_mapping[clean]
                return ResolvedTicker(symbol=symbol, company_name=name, attempted_symbols=[f"{clean}.TW", f"{clean}.TWO"])
            return ResolvedTicker(symbol=f"{clean}.TW", company_name=None, attempted_symbols=[f"{clean}.TW", f"{clean}.TWO"])

        raise ValueError(f"找不到「{query}」對應的台股代號，請輸入內建清單中的股票名稱或上市櫃代號。")
