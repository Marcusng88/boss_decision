const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface AgentInsightData {
  agent_name: string;
  emoji: string;
  findings: string[];
  risks: string[];
  recommendation: string;
  confidence: number;
  data_summary: string;
  metric_value: string;
  trend: "up" | "down" | "flat";
}

export interface PerspectiveView {
  recommendation: string;
  reasoning: string;
}

export interface FinalDecision {
  verdict: string;
  reasoning: string;
  risk_level: "Low" | "Medium" | "High";
  confidence_score: number;
}

export interface AnalysisResponse {
  case_id: number | null;
  query: string;
  agents_invoked: string[];
  agent_insights: AgentInsightData[];
  conservative_view: PerspectiveView;
  aggressive_view: PerspectiveView;
  final_decision: FinalDecision;
}

export async function analyzeDecision(query: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}
