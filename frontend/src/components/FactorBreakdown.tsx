import type { AnalysisResponse, FactorStatus } from "../api";

const FACTOR_LABELS: Record<string, string> = {
  Momentum: "動量",
  FundamentalHealth: "基本面健康度",
  TrendQuality: "趨勢品質",
  Growth: "市場成長",
  Volatility: "波動風險",
  Liquidity: "流動性/市場關注",
  MarketRelative: "相對大盤",
  RiskReward: "風險報酬",
};

function statusLabel(status: FactorStatus) {
  if (status === "ok") return "可用";
  if (status === "low_confidence") return "低信心";
  return "缺資料";
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) return "missing";
  if (typeof value === "number") return Number.isFinite(value) ? value.toFixed(4) : "missing";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function FactorBreakdown({ result }: { result: AnalysisResponse }) {
  return (
    <section className="panel">
      <h2>7 大因子</h2>
      <div className="factorGrid">
        {Object.entries(result.factor_scores).map(([factor, data]) => (
          <article className="factorCard" key={factor}>
            <div className="factorTop">
              <h3>{FACTOR_LABELS[factor] ?? factor}</h3>
              <span className={`pill ${data.status}`}>{statusLabel(data.status)}</span>
            </div>
            <div className="factorScore">{data.score_0_to_100 === null ? "missing" : data.score_0_to_100.toFixed(2)}</div>
            <p>
              {data.available_subfactors}/{data.total_subfactors} 子因子可用
            </p>
            <small>調整後權重：{result.adjusted_weights[factor]?.toFixed(2) ?? "0.00"}%</small>
          </article>
        ))}
      </div>
      <h2>子因子明細</h2>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>因子</th>
              <th>子因子</th>
              <th>原始值</th>
              <th>分數</th>
              <th>狀態</th>
              <th>原因</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(result.subfactor_scores).flatMap(([factor, subs]) =>
              Object.entries(subs).map(([name, sub]) => (
                <tr key={`${factor}-${name}`}>
                  <td>{FACTOR_LABELS[factor] ?? factor}</td>
                  <td>{name}</td>
                  <td>{formatValue(sub.raw_value)}</td>
                  <td>{sub.score_0_to_100 === null ? "missing" : sub.score_0_to_100.toFixed(2)}</td>
                  <td>
                    <span className={`pill ${sub.status}`}>{statusLabel(sub.status)}</span>
                  </td>
                  <td>{sub.reason}</td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
