import { useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle } from "lucide-react";

import { analyzeStock, type AnalysisResponse } from "./api";
import { DataQualityPanel } from "./components/DataQualityPanel";
import { Disclaimer } from "./components/Disclaimer";
import { FactorBreakdown } from "./components/FactorBreakdown";
import { SearchBox } from "./components/SearchBox";
import { SummaryCard } from "./components/SummaryCard";
import "./styles.css";

function App() {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runAnalysis(query: string) {
    setLoading(true);
    setError(null);
    try {
      setResult(await analyzeStock(query));
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失敗，請稍後再試。");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <section className="topbar">
        <div>
          <p className="eyebrow">Taiwan Listed / OTC Quant MVP</p>
          <h1>台灣上市櫃股票量化評分</h1>
        </div>
      </section>
      <SearchBox loading={loading} onSearch={runAnalysis} />
      {error && (
        <div className="error">
          <AlertTriangle size={18} aria-hidden="true" />
          {error}
        </div>
      )}
      {result ? (
        <>
          <SummaryCard result={result} />
          <FactorBreakdown result={result} />
          <DataQualityPanel dataQuality={result.data_quality} warnings={result.warnings} />
          <Disclaimer text={result.disclaimer} />
        </>
      ) : (
        <section className="empty">
          <strong>輸入股票名稱或代號開始分析</strong>
          <span>範例：台積電、2330、群聯、8299</span>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(<App />);
