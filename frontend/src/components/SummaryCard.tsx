import type { AnalysisResponse } from "../api";

function displayScore(value: number | null) {
  return value === null ? "資料不足" : value.toFixed(2);
}

export function SummaryCard({ result }: { result: AnalysisResponse }) {
  return (
    <section className="summary">
      <div>
        <p className="eyebrow">{result.resolved_symbol}</p>
        <h1>{result.company_name ?? result.resolved_symbol}</h1>
      </div>
      <div className="scoreBlock">
        <span className="score">{displayScore(result.final_score)}</span>
        <span className="rating">{result.rating}</span>
      </div>
      <div className="metaGrid">
        <div>
          <span>模型信心</span>
          <strong>{Math.round(result.confidence * 100)}%</strong>
        </div>
        <div>
          <span>可用權重</span>
          <strong>{Math.round(Object.values(result.adjusted_weights).reduce((sum, value) => sum + value, 0))}%</strong>
        </div>
      </div>
    </section>
  );
}
