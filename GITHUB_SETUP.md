# 推到 GitHub

如果你的電腦已安裝 Git，請在 PowerShell 執行下列指令。

先進入專案資料夾：

```powershell
cd "C:\Users\Wang Boxiang\Documents\Codex\2026-06-11\mvp-web-app-2330-ticker-7"
```

初始化 Git：

```powershell
git init
git add .
git commit -m "Initial Taiwan stock quant MVP"
```

到 GitHub 建立一個新的 repository，例如：

```text
taiwan-stock-quant-mvp
```

然後把 GitHub 顯示的 remote 指令貼回 PowerShell，通常像這樣：

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/taiwan-stock-quant-mvp.git
git push -u origin main
```

推上 GitHub 後，再到 Render 連接這個 repository，Render 會讀取 `render.yaml` 部署公開網站。

## 如果你的電腦沒有 Git

可以改用 GitHub 網頁上傳：

1. 到 GitHub 建立新 repository。
2. 按 `Add file`。
3. 上傳本資料夾中的檔案。
4. 不要上傳 `.venv_app`、`work`、`outputs`。

建議仍安裝 Git，因為部署與後續更新會比較穩。
