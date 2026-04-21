import { useMemo, useState } from "react";
import { Loader2, Orbit, Radio, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { streamSimulator, SimulatorStreamEvent } from "@/lib/simulator-client";

const defaultPrompt = "Should we increase price by 10% for student segment next quarter?";

export function SimulatorSection() {
  const [query, setQuery] = useState(defaultPrompt);
  const [isRunning, setIsRunning] = useState(false);
  const [tokens, setTokens] = useState("");
  const [updates, setUpdates] = useState<string[]>([]);
  const [finalResponse, setFinalResponse] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  const elapsed = useMemo(() => {
    if (!startedAt) return null;
    return ((Date.now() - startedAt) / 1000).toFixed(1);
  }, [startedAt, isRunning]);

  const handleEvent = (event: SimulatorStreamEvent) => {
    if (event.type === "token" && event.text) {
      setTokens((prev) => prev + event.text);
      return;
    }
    if (event.type === "update" && event.nodes?.length) {
      setUpdates((prev) => [...prev, ...event.nodes]);
      return;
    }
    if (event.type === "final") {
      setFinalResponse(event.response ?? event.state ?? null);
      return;
    }
    if (event.type === "error") {
      setError(event.error ?? "Unknown simulator error.");
    }
  };

  const runSimulation = async () => {
    if (!query.trim() || isRunning) return;
    setIsRunning(true);
    setTokens("");
    setUpdates([]);
    setFinalResponse(null);
    setError(null);
    setStartedAt(Date.now());

    try {
      await streamSimulator({ query: query.trim() }, { onEvent: handleEvent });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reach simulator stream endpoint.";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section className="mt-12 overflow-hidden rounded-[2rem] border border-border bg-card/80 shadow-card">
      <div className="relative border-b border-border px-6 py-6 md:px-10 bg-[radial-gradient(circle_at_top,rgba(233,119,46,0.2),transparent_58%),linear-gradient(180deg,rgba(255,255,255,0.95),rgba(252,246,238,0.95))]">
        <div className="absolute inset-0 opacity-10 [background-image:repeating-linear-gradient(90deg,transparent,transparent_36px,rgba(40,40,40,0.25)_36px,rgba(40,40,40,0.25)_37px)]" />
        <div className="relative flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[0.65rem] uppercase tracking-[0.32em] text-primary">Simulator stream</p>
            <h2 className="mt-2 text-4xl leading-none text-foreground md:text-5xl">Live Multi-Agent Arena</h2>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Streams backend simulator events in real time through the bridge endpoint, with no edits inside the
              simulator folder.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-background/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-foreground">
              <Radio className="h-3.5 w-3.5 text-primary" />
              Stream {isRunning ? "active" : "idle"}
            </span>
            {elapsed && <span className="text-xs text-muted-foreground">{elapsed}s</span>}
          </div>
        </div>
      </div>

      <div className="grid gap-6 p-6 md:p-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <label className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Prompt</label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-12 border-border bg-background text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
              placeholder="Enter a business simulation question"
              style={{ fontFamily: '"IBM Plex Mono", monospace' }}
            />
            <Button
              onClick={runSimulation}
              disabled={isRunning}
              className="h-12 min-w-36 border border-primary/30 bg-primary px-5 font-semibold text-primary-foreground hover:bg-primary/90"
              style={{ fontFamily: '"IBM Plex Mono", monospace' }}
            >
              {isRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Streaming
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Run Simulator
                </>
              )}
            </Button>
          </div>

          <div className="rounded-xl border border-border bg-background/70 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">Token stream</p>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-foreground" style={{ fontFamily: '"IBM Plex Mono", monospace' }}>
              {tokens || "Waiting for streamed model tokens..."}
            </pre>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-background/70 p-4">
            <p className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <Orbit className="h-4 w-4 text-primary" />
              Node updates
            </p>
            <div className="max-h-40 space-y-2 overflow-auto">
              {updates.length === 0 && <p className="text-sm text-muted-foreground">No graph updates yet.</p>}
              {updates.map((node, index) => (
                <div
                  key={`${node}-${index}`}
                  className="animate-fade-in-up rounded-md border border-border bg-card/75 px-3 py-2 text-sm text-foreground"
                  style={{ fontFamily: '"IBM Plex Mono", monospace', animationDelay: `${Math.min(index, 8) * 45}ms` }}
                >
                  {node}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-background/70 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">Final response</p>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-xs text-foreground" style={{ fontFamily: '"IBM Plex Mono", monospace' }}>
              {finalResponse ? JSON.stringify(finalResponse, null, 2) : "Waiting for final payload..."}
            </pre>
          </div>

          {error && <div className="rounded-xl border border-red-500/30 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        </div>
      </div>
    </section>
  );
}
