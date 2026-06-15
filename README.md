# 台灣上市櫃股票量化評分 MVP Web App

## 檔案結構

```text
backend/
  requirements.txt
  pytest.ini
  app/
    main.py
    models.py
    config.py
    services/
      ticker_resolver.py
      data_provider.py
      yahoo_provider.py
      indicators.py
      scoring.py
      rating.py
      cache.py
    tests/
      test_ticker_resolver.py
      test_indicators.py
      test_scoring.py
frontend/
  package.json
  index.html
  tsconfig.json
  src/
    App.tsx
    api.ts
    styles.css
    components/
      SearchBox.tsx
      SummaryCard.tsx
      FactorBreakdown.tsx
      DataQualityPanel.tsx
      Disclaimer.tsx
```

## 後端啟動

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 前端啟動

```bash
cd frontend
npm install
npm run dev
```

預設前端會呼叫 `http://127.0.0.1:8000`。

## 測試

```bash
cd backend
pytest
```

## 資料聲明

MVP 使用 `yfinance` 作為主資料源。資料可能延遲、缺漏或受限流影響，不會標示為即時資料。所有 API 回傳都包含 `source`、`last_updated`、`is_realtime`、`delay_minutes`、`confidence` 與 `missing_reason`。

量化模型結果，不構成投資建議。
