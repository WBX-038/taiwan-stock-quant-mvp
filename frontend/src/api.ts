export type FactorStatus = "ok" | "missing" | "low_confidence";

export type DataPoint = {
  value: unknown;
  source: string;
  last_updated: string | null;
  is_realtime: boolean;
  delay_minutes: number | null;
  confidence: number;
  missing_reason: string | null;
};

export type SubFactorScore = {
  raw_value: unknown;
  score_0_to_100: number | null;
  status: FactorStatus;
  reason: string;
};

export type FactorScore = {
  score_0_to_100: number | null;
  status: FactorStatus;
  available_subfactors: number;
  total_subfactors: number;
  reason: string;
};

export type CandlePoint = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export type AnalysisResponse = {
  query: string;
  resolved_symbol: string;
  company_name: string | null;
  industry_category: string | null;
  business_focus: string | null;
  chart_data: CandlePoint[];
  final_score: number | null;
  rating: string;
  confidence: number;
  factor_scores: Record<string, FactorScore>;
  subfactor_scores: Record<string, Record<string, SubFactorScore>>;
  adjusted_weights: Record<string, number>;
  data_quality: Record<string, DataPoint>;
  warnings: string[];
  disclaimer: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function analyzeStock(query: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/analyze?query=${encodeURIComponent(query)}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ?? "分析失敗，請稍後再試。");
  }
  return body as AnalysisResponse;
}
