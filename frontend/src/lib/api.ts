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

export interface StreamingState {
  status: string;
  agents_invoked: string[];
  active_agents: string[];
  agent_insights: AgentInsightData[];
  conservative_view?: PerspectiveView;
  aggressive_view?: PerspectiveView;
  final_decision?: FinalDecision;
  isDone: boolean;
}

export interface StreamCallbacks {
  onStatus: (message: string) => void;
  onIntent: (agents: string[]) => void;
  onAgentStart: (agent: string) => void;
  onAgentDone: (insight: AgentInsightData) => void;
  onSynthesis: (conservative: PerspectiveView, aggressive: PerspectiveView) => void;
  onComplete: (result: AnalysisResponse) => void;
  onError: (err: string) => void;
}

export async function analyzeDecisionStream(
  query: string,
  selectedAgents: string[],
  callbacks: StreamCallbacks
): Promise<void> {
  const body: Record<string, unknown> = { query };
  if (selectedAgents.length > 0) body.selected_agents = selectedAgents;

  const response = await fetch(`${API_BASE}/api/analyze/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Request failed: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6)) as {
              type: string;
              message?: string;
              agents?: string[];
              agent?: string;
              insight?: AgentInsightData;
              conservative?: PerspectiveView;
              aggressive?: PerspectiveView;
              result?: AnalysisResponse;
              error?: string;
            };

            switch (data.type) {
              case "status":
                callbacks.onStatus(data.message ?? "");
                break;
              case "intent":
                callbacks.onIntent(data.agents ?? []);
                break;
              case "agent_start":
                callbacks.onAgentStart(data.agent ?? "");
                break;
              case "agent_done":
                if (data.insight) callbacks.onAgentDone(data.insight);
                break;
              case "synthesis":
                if (data.conservative && data.aggressive)
                  callbacks.onSynthesis(data.conservative, data.aggressive);
                break;
              case "complete":
                if (data.result) callbacks.onComplete(data.result);
                break;
              case "error":
                callbacks.onError(data.message ?? data.error ?? "Unknown error");
                break;
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function analyzeDecision(query: string, selectedAgents?: string[]): Promise<AnalysisResponse> {
  const body: Record<string, unknown> = { query };
  if (selectedAgents && selectedAgents.length > 0) body.selected_agents = selectedAgents;

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<AnalysisResponse>;
}
