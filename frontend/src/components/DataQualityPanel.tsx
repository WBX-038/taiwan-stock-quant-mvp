import type { DataPoint } from "../api";

function formatDate(value: string | null) {
  if (!value) return "未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "未知" : date.toLocaleString("zh-TW");
}

export function DataQualityPanel({ dataQuality, warnings }: { dataQuality: Record<string, DataPoint>; warnings: string[] }) {
  return (
    <section className="panel">
      <h2>資料品質</h2>
      <div className="qualityGrid">
        {Object.entries(dataQuality).map(([name, point]) => (
          <article className="qualityItem" key={name}>
            <h3>{name}</h3>
            <p>來源：{point.source}</p>
            <p>更新：{formatDate(point.last_updated)}</p>
            <p>即時：{point.is_realtime ? "是" : "否"}</p>
            <p>延遲：{point.delay_minutes === null ? "未知" : `${point.delay_minutes} 分鐘`}</p>
            <p>信心：{Math.round(point.confidence * 100)}%</p>
            {point.missing_reason && <p className="warningText">{point.missing_reason}</p>}
          </article>
        ))}
      </div>
      {warnings.length > 0 && (
        <div className="warnings">
          <h3>Warnings</h3>
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </section>
  );
}
