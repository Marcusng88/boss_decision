export interface SimulatorRequest {
  query: string;
  structured_data?: Record<string, unknown>;
  documents?: string[];
  business_context?: Record<string, unknown>;
}

export interface SimulatorStreamEvent {
  type: "status" | "update" | "custom" | "final" | "error" | "done";
  message?: string;
  nodes?: string[];
  updates?: Record<string, unknown>;
  event?: string;
  data?: Record<string, unknown>;
  response?: unknown;
  state?: Record<string, unknown>;
  error?: string;
}

export interface DeepSimulatorRequest {
  query: string;
  max_ticks?: number;
  seed?: number;
  scenario_id?: string;
}

export interface DeepSimulatorStreamEvent {
  type:
    | "status"
    | "progress"
    | "world"
    | "agent_tool_call"
    | "agent_chunk"
    | "timeline"
    | "final"
    | "error"
    | "done";
  message?: string;
  max_ticks?: number;
  tick?: number;
  summary?: string;
  state?: Record<string, unknown>;
  persona_id?: string;
  tool_call?: string;
  chunk?: string;
  response?: Record<string, unknown>;
  error?: string;
}

interface StreamHandlers {
  onEvent: (event: SimulatorStreamEvent) => void;
}

interface DeepStreamHandlers {
  onEvent: (event: DeepSimulatorStreamEvent) => void;
  signal?: AbortSignal;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function streamSimulator(
  request: SimulatorRequest,
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/simulator/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Simulator stream request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const parsed = JSON.parse(trimmed) as SimulatorStreamEvent;
      handlers.onEvent(parsed);
      if (parsed.type === "done") return;
    }
  }
}

export async function streamDeepSimulator(
  request: DeepSimulatorRequest,
  handlers: DeepStreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/deep-simulator/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal: handlers.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Deep simulator stream request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const parsed = JSON.parse(trimmed) as DeepSimulatorStreamEvent;
      handlers.onEvent(parsed);
      if (parsed.type === "done") return;
    }
  }
}
