# 部署成大家都能使用的公開網站

這個專案是 FastAPI 後端直接提供網頁 UI，不適合只放 GitHub Pages，因為 GitHub Pages 不能執行 Python 後端。

建議架構：

```text
GitHub repository 放程式碼
Render 讀取 GitHub repository 並執行網站
使用者開 Render 提供的公開網址
```

## 你需要做的事

1. 建立 GitHub repository。
2. 把本專案推上 GitHub。
3. 到 Render 建立 Web Service，連接該 GitHub repository。
4. Render 會使用專案根目錄的 `render.yaml` 部署。

部署成功後會得到類似：

```text
https://taiwan-stock-quant-mvp.onrender.com
```

這個網址別人就可以直接打開使用。

## Render 設定

本專案已附：

```text
render.yaml
Dockerfile
backend/requirements.lock.txt
```

Render Blueprint 會使用：

```text
buildCommand: pip install -r backend/requirements.lock.txt
startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 本機啟動

本機版本仍然使用：

```powershell
& "C:\Users\Wang Boxiang\Documents\Codex\2026-06-11\mvp-web-app-2330-ticker-7\start_app.bat"
```

然後開：

```text
http://127.0.0.1:8000
```

## 注意

- yfinance 可能延遲、缺資料或被限流。
- 價格資料失敗時會嘗試 Yahoo chart API。
- 上市/上櫃基本面資料會嘗試補 TWSE/TPEx 官方公開資料。
- 網站輸出為量化模型結果，不構成投資建議。
