export interface SimulatorRequest {
  query: string;
  structured_data?: Record<string, unknown>;
  documents?: string[];
  business_context?: Record<string, unknown>;
}

export interface SimulatorStreamEvent {
  type: "status" | "update" | "token" | "final" | "error" | "done";
  message?: string;
  nodes?: string[];
  text?: string;
  response?: unknown;
  state?: Record<string, unknown>;
  error?: string;
}

interface StreamHandlers {
  onEvent: (event: SimulatorStreamEvent) => void;
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
