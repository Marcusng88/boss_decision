import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  ChevronRight,
  Eye,
  EyeOff,
  Gauge,
  Loader2,
  Orbit,
  Rocket,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { streamSimulator, SimulatorStreamEvent } from "@/lib/simulator-client";

const defaultPrompt = "Should we increase price by 10% for student segment next quarter?";
const LAST_RUN_STORAGE_KEY = "simulator:last-run";

const FLOW = [
  { id: "parse_decision", label: "Parse Decision", narrative: "Interpreting leadership intent and constraints." },
  { id: "build_scenario", label: "Build Scenario", narrative: "Building simulation context and operating assumptions." },
  { id: "select_personas", label: "Spawn Personas", narrative: "Selecting specialist subagents for debate." },
  { id: "persona_worker", label: "Persona Debate", narrative: "Running deep-agent subagent analyses in parallel." },
  { id: "collect_results", label: "Collect Signals", narrative: "Merging persona outputs into unified view." },
  { id: "aggregate_impacts", label: "Impact Rollup", narrative: "Computing weighted KPI movement and signal ranks." },
  { id: "scenario_branch_worker", label: "Branch Stress Test", narrative: "Simulating optimistic, base, and downside branches." },
  { id: "generate_recommendation", label: "Synthesis", narrative: "Writing recommendation from combined evidence." },
  { id: "format_response", label: "Compose Output", narrative: "Preparing final board-ready recommendation payload." },
] as const;

type FlowNode = (typeof FLOW)[number]["id"];
type StepState = "idle" | "active" | "done";
type PersonaState = "queued" | "running" | "done" | "fallback";

interface PersonaCard {
  persona_id: string;
  confidence: number;
  risks: string[];
  opportunities: string[];
  rationale: string;
  kpi_deltas: Record<string, number>;
  status: PersonaState;
  stream: string[];
}

interface SimulatorSectionProps {
  initialQuery?: string;
}

const FLOW_NODE_SET = new Set<FlowNode>(FLOW.map((step) => step.id));

function initFlowState(): Record<FlowNode, StepState> {
  return FLOW.reduce(
    (acc, step) => {
      acc[step.id] = "idle";
      return acc;
    },
    {} as Record<FlowNode, StepState>,
  );
}

function normalizePersona(data: unknown): PersonaCard | null {
  if (!data || typeof data !== "object") return null;
  const raw = data as Record<string, unknown>;
  const persona_id = typeof raw.persona_id === "string" ? raw.persona_id : "unknown";
  const confidence = typeof raw.confidence === "number" ? raw.confidence : 0;
  const risks = Array.isArray(raw.risks) ? raw.risks.filter((r): r is string => typeof r === "string") : [];
  const opportunities = Array.isArray(raw.opportunities)
    ? raw.opportunities.filter((o): o is string => typeof o === "string")
    : [];
  const rationale = typeof raw.rationale === "string" ? raw.rationale : "";
  const kpi_deltas = raw.kpi_deltas && typeof raw.kpi_deltas === "object" ? (raw.kpi_deltas as Record<string, number>) : {};
  const isFallback = risks.some((risk) => risk.toLowerCase().includes("fallback"));

  return {
    persona_id,
    confidence,
    risks,
    opportunities,
    rationale,
    kpi_deltas,
    status: isFallback ? "fallback" : "done",
    stream: [],
  };
}

function clipText(input: string, max = 170): string {
  const text = input.trim().replace(/\s+/g, " ");
  if (text.length <= max) return text;
  return `${text.slice(0, max)}...`;
}

function titleizePersonaId(personaId: string): string {
  return personaId
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusTone(status: PersonaState): string {
  if (status === "done") return "bg-success/15 text-success border-success/30";
  if (status === "fallback") return "bg-warning/15 text-warning border-warning/30";
  if (status === "running") return "bg-primary/15 text-primary border-primary/30";
  return "bg-muted text-muted-foreground border-border";
}

function flowTone(state: StepState): string {
  if (state === "done") return "border-success/50 bg-success/10 text-success";
  if (state === "active") return "border-primary/60 bg-primary/10 text-primary";
  return "border-border bg-background/70 text-muted-foreground";
}

function findLikelyPersonaFromToken(text: string, personaIds: string[]): string | null {
  const lower = text.toLowerCase();
  const match = personaIds.find((id) => lower.includes(id.toLowerCase().replace(/_/g, " ")));
  return match ?? null;
}

export function SimulatorSection({ initialQuery }: SimulatorSectionProps) {
  const [query, setQuery] = useState(initialQuery?.trim() || defaultPrompt);
  const [isRunning, setIsRunning] = useState(false);
  const [flowState, setFlowState] = useState<Record<FlowNode, StepState>>(initFlowState());
  const [personas, setPersonas] = useState<Record<string, PersonaCard>>({});
  const [personaOrder, setPersonaOrder] = useState<string[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState("");
  const [topRisks, setTopRisks] = useState<string[]>([]);
  const [topOpportunities, setTopOpportunities] = useState<string[]>([]);
  const [kpiDeltas, setKpiDeltas] = useState<Record<string, number>>({});
  const [liveFeed, setLiveFeed] = useState<string[]>([]);
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [showTechTrace, setShowTechTrace] = useState(false);

  useEffect(() => {
    if (!isRunning) return;
    const timer = window.setInterval(() => setNow(Date.now()), 200);
    return () => window.clearInterval(timer);
  }, [isRunning]);

  const elapsedSeconds = useMemo(() => {
    if (!startedAt) return 0;
    return Math.max(0, (now - startedAt) / 1000);
  }, [startedAt, now]);

  const selectedPersonaCard = selectedPersona ? personas[selectedPersona] ?? null : null;

  const progressValue = useMemo(() => {
    const doneCount = FLOW.filter((step) => flowState[step.id] === "done").length;
    const activeCount = FLOW.filter((step) => flowState[step.id] === "active").length;
    return Math.round(((doneCount + activeCount * 0.45) / FLOW.length) * 100);
  }, [flowState]);

  const swarmConfidence = useMemo(() => {
    const list = Object.values(personas).filter((persona) => persona.status === "done" || persona.status === "fallback");
    if (list.length === 0) return 0;
    const avg = list.reduce((sum, persona) => sum + persona.confidence, 0) / list.length;
    return Math.round(avg * 100);
  }, [personas]);

  const applyNodeUpdate = (node: string) => {
    if (!FLOW_NODE_SET.has(node as FlowNode)) return;
    const flowNode = node as FlowNode;
    setFlowState((prev) => {
      const next = { ...prev };
      for (const step of FLOW) {
        if (next[step.id] === "active") next[step.id] = "done";
      }
      if (next[flowNode] !== "done") next[flowNode] = "active";
      return next;
    });
  };

  const appendEventLog = (entry: string) => {
    setEventLog((prev) => [...prev, entry].slice(-80));
  };

  const appendFeed = (line: string) => {
    setLiveFeed((prev) => [...prev, line].slice(-70));
  };

  const markPersonaRunning = (personaId: string) => {
    setPersonas((prev) => {
      const item = prev[personaId];
      if (!item) return prev;
      if (item.status === "done" || item.status === "fallback") return prev;
      return {
        ...prev,
        [personaId]: {
          ...item,
          status: "running",
        },
      };
    });
  };

  const appendPersonaStream = (personaId: string, line: string) => {
    setPersonas((prev) => {
      const item = prev[personaId];
      if (!item) return prev;
      return {
        ...prev,
        [personaId]: {
          ...item,
          stream: [...item.stream, line].slice(-8),
        },
      };
    });
  };

  const handleEvent = (event: SimulatorStreamEvent) => {
    if (event.type === "status" && event.message) {
      appendEventLog(event.message);
      appendFeed(`System: ${event.message}`);
      return;
    }

    if (event.type === "token" && event.text) {
      const tokenText = clipText(event.text, 200);
      const nodeName = typeof event.node === "string" && event.node ? event.node : "model_stream";
      appendFeed(`${nodeName}: ${tokenText}`);

      const personaIds = personaOrder.length > 0 ? personaOrder : Object.keys(personas);
      const personaFromToken = findLikelyPersonaFromToken(tokenText, personaIds);
      const runningPersona = personaIds.find((id) => personas[id]?.status === "running");
      const queuedPersona = personaIds.find((id) => personas[id]?.status === "queued");
      const targetPersona = personaFromToken ?? runningPersona ?? queuedPersona ?? null;

      if (targetPersona) {
        markPersonaRunning(targetPersona);
        appendPersonaStream(targetPersona, tokenText);
      }
      return;
    }

    if (event.type === "update") {
      if (event.nodes?.length) {
        event.nodes.forEach((node) => {
          applyNodeUpdate(node);
          appendEventLog(`Node update: ${node}`);
        });
      }

      if (event.updates && typeof event.updates === "object") {
        const payload = event.updates as Record<string, unknown>;

        const selectPayload = payload.select_personas as Record<string, unknown> | undefined;
        if (selectPayload && Array.isArray(selectPayload.selected_personas)) {
          const personaIds = selectPayload.selected_personas
            .map((item) => (item && typeof item === "object" ? (item as Record<string, unknown>).id : null))
            .filter((id): id is string => typeof id === "string");

          if (personaIds.length > 0) {
            setPersonaOrder(personaIds);
            setPersonas((prev) => {
              const next = { ...prev };
              personaIds.forEach((id) => {
                if (!next[id]) {
                  next[id] = {
                    persona_id: id,
                    confidence: 0,
                    risks: [],
                    opportunities: [],
                    rationale: "Subagent queued for specialist analysis.",
                    kpi_deltas: {},
                    status: "queued",
                    stream: [],
                  };
                }
              });
              return next;
            });
            setSelectedPersona((current) => current ?? personaIds[0]);
            appendFeed(`Orchestrator: Spawned ${personaIds.length} subagents.`);
          }
        }

        const workerPayload = payload.persona_worker as Record<string, unknown> | undefined;
        if (workerPayload && Array.isArray(workerPayload.persona_stream_events)) {
          workerPayload.persona_stream_events.forEach((evt) => {
            if (!evt || typeof evt !== "object") return;
            const row = evt as Record<string, unknown>;
            const personaId = typeof row.persona_id === "string" ? row.persona_id : null;
            const text = typeof row.text === "string" ? clipText(row.text, 180) : "";
            const nodeName = typeof row.node === "string" && row.node ? row.node : "subagent";
            if (!personaId || !text) return;
            markPersonaRunning(personaId);
            appendPersonaStream(personaId, text);
            appendFeed(`${titleizePersonaId(personaId)} · ${nodeName}: ${text}`);
          });
        }

        if (workerPayload && Array.isArray(workerPayload.persona_results)) {
          const parsed = workerPayload.persona_results
            .map((item) => normalizePersona(item))
            .filter((item): item is PersonaCard => item !== null);

          if (parsed.length > 0) {
            setPersonas((prev) => {
              const next = { ...prev };
              parsed.forEach((persona) => {
                const existingStream = next[persona.persona_id]?.stream ?? [];
                next[persona.persona_id] = {
                  ...persona,
                  stream: existingStream,
                };
              });
              return next;
            });
            setSelectedPersona((current) => current ?? parsed[0].persona_id);

            parsed.forEach((persona) => {
              const personaName = titleizePersonaId(persona.persona_id);
              const statusWord = persona.status === "fallback" ? "fallback" : "completed";
              appendFeed(`${personaName}: ${statusWord} analysis.`);
            });
          }
        }

        const impactsPayload = payload.aggregate_impacts as Record<string, unknown> | undefined;
        if (impactsPayload && impactsPayload.kpi_rollup && typeof impactsPayload.kpi_rollup === "object") {
          setKpiDeltas(impactsPayload.kpi_rollup as Record<string, number>);
        }

        const recommendationPayload = payload.generate_recommendation as Record<string, unknown> | undefined;
        if (recommendationPayload && typeof recommendationPayload.recommendation === "string") {
          setRecommendation(recommendationPayload.recommendation);
        }
      }
      return;
    }

    if (event.type === "final") {
      const payload = (event.response ?? event.state ?? null) as Record<string, unknown> | null;
      const response = (payload?.response ?? payload) as Record<string, unknown> | undefined;
      if (typeof response?.recommendation === "string") setRecommendation(response.recommendation);
      if (Array.isArray(response?.ranked_risks)) setTopRisks((response.ranked_risks as string[]).slice(0, 5));
      if (Array.isArray(response?.ranked_opportunities)) setTopOpportunities((response.ranked_opportunities as string[]).slice(0, 5));
      if (response?.kpi_deltas && typeof response.kpi_deltas === "object") {
        setKpiDeltas(response.kpi_deltas as Record<string, number>);
      }

      const personaRows = Array.isArray(response?.persona_reactions) ? response.persona_reactions : [];
      const parsed = personaRows.map((item) => normalizePersona(item)).filter((item): item is PersonaCard => item !== null);
      if (parsed.length > 0) {
        setPersonas((prev) => {
          const next = { ...prev };
          parsed.forEach((persona) => {
            const existing = next[persona.persona_id];
            next[persona.persona_id] = {
              ...persona,
              stream: existing?.stream ?? [],
            };
          });
          return next;
        });
      }

      appendFeed("System: Recommendation package finalized.");

      try {
        localStorage.setItem(
          LAST_RUN_STORAGE_KEY,
          JSON.stringify({
            query: query.trim(),
            recommendation: typeof response?.recommendation === "string" ? response.recommendation : undefined,
            status: "ok",
            completedAt: new Date().toISOString(),
          }),
        );
      } catch {
        // no-op
      }
      return;
    }

    if (event.type === "error") {
      setError(event.error ?? "Unknown simulator error.");
      appendFeed(`System error: ${event.error ?? "Unknown simulator error."}`);
    }
  };

  const runSimulation = async () => {
    if (!query.trim() || isRunning) return;

    setIsRunning(true);
    setFlowState(initFlowState());
    setPersonas({});
    setPersonaOrder([]);
    setSelectedPersona(null);
    setRecommendation("");
    setTopRisks([]);
    setTopOpportunities([]);
    setKpiDeltas({});
    setLiveFeed([]);
    setEventLog([]);
    setError(null);
    const started = Date.now();
    setStartedAt(started);
    setNow(started);

    try {
      await streamSimulator({ query: query.trim() }, { onEvent: handleEvent });
      setFlowState((prev) => {
        const next = { ...prev };
        FLOW.forEach((step) => {
          if (next[step.id] === "active") next[step.id] = "done";
        });
        return next;
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reach simulator stream endpoint.";
      setError(message);
      try {
        localStorage.setItem(
          LAST_RUN_STORAGE_KEY,
          JSON.stringify({
            query: query.trim(),
            status: "error",
            completedAt: new Date().toISOString(),
          }),
        );
      } catch {
        // no-op
      }
    } finally {
      setIsRunning(false);
    }
  };

  const orderedPersonas = (personaOrder.length > 0 ? personaOrder : Object.keys(personas))
    .map((id) => personas[id])
    .filter((item): item is PersonaCard => Boolean(item));

  return (
    <section className="overflow-hidden rounded-[2rem] border border-border bg-card/85 shadow-elevated">
      <div className="relative border-b border-border px-6 py-6 md:px-10 bg-[radial-gradient(circle_at_8%_0%,rgba(233,119,46,0.32),transparent_48%),radial-gradient(circle_at_84%_10%,rgba(22,154,142,0.28),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(252,246,238,0.98))]">
        <div className="absolute inset-0 opacity-10 [background-image:linear-gradient(to_right,rgba(28,28,28,0.2)_1px,transparent_1px),linear-gradient(to_bottom,rgba(28,28,28,0.2)_1px,transparent_1px)] [background-size:34px_34px]" />
        <div className="relative grid gap-4 xl:grid-cols-[1.1fr_0.9fr] xl:items-end">
          <div>
            <p className="text-[0.65rem] uppercase tracking-[0.32em] text-primary">Mission Control</p>
            <h2 className="mt-2 text-4xl leading-none text-foreground md:text-5xl">Simulation Command Deck</h2>
            <p className="mt-3 max-w-2xl text-sm text-muted-foreground">
              Live orchestration of deep-agent subagents, timeline progression, and recommendation synthesis.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-background/75 p-3">
              <p className="text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground">Runtime</p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Orbit className="h-4 w-4 text-primary" />
                {isRunning ? "Live" : "Standby"}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-background/75 p-3">
              <p className="text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground">Elapsed</p>
              <p className="mt-1 text-sm font-semibold text-foreground">{elapsedSeconds.toFixed(1)}s</p>
            </div>
            <div className="rounded-xl border border-border bg-background/75 p-3">
              <p className="text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground">Swarm Confidence</p>
              <p className="mt-1 text-sm font-semibold text-foreground">{swarmConfidence}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 p-6 md:p-10 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <label className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Scenario Prompt</label>
            <div className="mt-3 flex flex-col gap-3 sm:flex-row">
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="h-12 border-border bg-card text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
                placeholder="Enter a business simulation question"
                style={{ fontFamily: '"IBM Plex Mono", monospace' }}
              />
              <Button
                onClick={runSimulation}
                disabled={isRunning}
                className="h-12 min-w-44 border border-primary/30 bg-primary px-5 font-semibold text-primary-foreground hover:bg-primary/90"
                style={{ fontFamily: '"IBM Plex Mono", monospace' }}
              >
                {isRunning ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Running
                  </>
                ) : (
                  <>
                    <Rocket className="mr-2 h-4 w-4" />
                    Launch Simulation
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <Activity className="h-4 w-4 text-primary" />
                Process Rail
              </p>
              <Badge variant="secondary" className="bg-card text-foreground">
                {progressValue}% complete
              </Badge>
            </div>
            <Progress value={progressValue} className="h-2 bg-muted" />
            <div className="mt-4 space-y-2">
              {FLOW.map((step, idx) => {
                const state = flowState[step.id];
                return (
                  <div key={step.id} className={`rounded-xl border p-3 transition-all ${flowTone(state)}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold">
                          {idx + 1}. {step.label}
                        </p>
                        <p className="mt-1 text-xs leading-relaxed opacity-85">{step.narrative}</p>
                      </div>
                      <Badge className={state === "done" ? "bg-success/20 text-success" : state === "active" ? "bg-primary/20 text-primary animate-pulse-glow" : "bg-muted text-muted-foreground"}>
                        {state}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <p className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <Sparkles className="h-4 w-4 text-primary" />
              Live Agent Comms
            </p>
            <div className="max-h-56 space-y-2 overflow-auto">
              {liveFeed.length === 0 && <p className="text-sm text-muted-foreground">Waiting for stream events...</p>}
              {liveFeed.map((line, index) => (
                <div key={`${line}-${index}`} className="rounded-md border border-border bg-card/75 px-3 py-2 text-xs text-foreground" style={{ fontFamily: '"IBM Plex Mono", monospace' }}>
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <Bot className="h-4 w-4 text-primary" />
                Subagent Swarm Board
              </p>
              <Badge variant="secondary" className="bg-card text-foreground">
                {orderedPersonas.length} active
              </Badge>
            </div>
            <div className="grid max-h-72 gap-2 overflow-auto sm:grid-cols-2">
              {orderedPersonas.length === 0 && <p className="text-sm text-muted-foreground">No personas spawned yet.</p>}
              {orderedPersonas.map((persona) => {
                const selected = selectedPersona === persona.persona_id;
                const lastStream = persona.stream[persona.stream.length - 1];
                return (
                  <button
                    key={persona.persona_id}
                    type="button"
                    onClick={() => setSelectedPersona(persona.persona_id)}
                    className={`rounded-xl border p-3 text-left transition-all ${
                      selected ? "border-primary bg-primary/10 shadow-card" : "border-border bg-card/75 hover:bg-card"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-foreground">{titleizePersonaId(persona.persona_id)}</p>
                        <p className="text-[0.65rem] uppercase tracking-[0.14em] text-muted-foreground">{persona.persona_id}</p>
                      </div>
                      <Badge className={statusTone(persona.status)}>{persona.status}</Badge>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">Confidence {Math.round(persona.confidence * 100)}%</p>
                    <p className="mt-2 text-xs leading-relaxed text-foreground">
                      {lastStream ? clipText(lastStream, 110) : "Awaiting subagent stream..."}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <p className="mb-3 text-xs uppercase tracking-[0.22em] text-muted-foreground">Subagent Inspector</p>
            {!selectedPersonaCard && <p className="text-sm text-muted-foreground">Select a persona card to inspect detailed reasoning.</p>}
            {selectedPersonaCard && (
              <div className="space-y-4 text-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-base font-semibold text-foreground">{titleizePersonaId(selectedPersonaCard.persona_id)}</p>
                    <p className="text-xs text-muted-foreground">{selectedPersonaCard.persona_id}</p>
                  </div>
                  <Badge className={statusTone(selectedPersonaCard.status)}>{selectedPersonaCard.status}</Badge>
                </div>

                <div className="rounded-xl border border-border bg-card/70 p-3">
                  <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Rationale</p>
                  <p className="mt-2 text-sm leading-relaxed text-foreground">
                    {selectedPersonaCard.rationale || "No rationale available yet."}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-border bg-card/70 p-3">
                    <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      <ShieldAlert className="h-3.5 w-3.5 text-warning" />
                      Risks
                    </p>
                    <div className="space-y-1">
                      {(selectedPersonaCard.risks.length > 0 ? selectedPersonaCard.risks : ["No risk signals yet."]).map((risk, index) => (
                        <p key={`${risk}-${index}`} className="text-xs text-foreground">
                          {risk}
                        </p>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl border border-border bg-card/70 p-3">
                    <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      <TrendingUp className="h-3.5 w-3.5 text-success" />
                      Opportunities
                    </p>
                    <div className="space-y-1">
                      {(selectedPersonaCard.opportunities.length > 0 ? selectedPersonaCard.opportunities : ["No upside signals yet."]).map((item, index) => (
                        <p key={`${item}-${index}`} className="text-xs text-foreground">
                          {item}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card/70 p-3">
                  <p className="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">Subagent Stream Snippets</p>
                  <div className="space-y-1">
                    {(selectedPersonaCard.stream.length > 0 ? selectedPersonaCard.stream : ["No stream snippets captured yet."]).map((line, index) => (
                      <p key={`${line}-${index}`} className="text-xs text-foreground" style={{ fontFamily: '"IBM Plex Mono", monospace' }}>
                        {line}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <Gauge className="h-4 w-4 text-primary" />
              Outcome Composer
            </p>
            <p className="rounded-xl border border-border bg-card/70 p-3 text-sm leading-relaxed text-foreground">
              {recommendation || "Recommendation is still synthesizing..."}
            </p>
            {(topRisks.length > 0 || topOpportunities.length > 0) && (
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-border bg-card/70 p-3">
                  <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Top Risks</p>
                  <div className="mt-2 space-y-1">
                    {topRisks.slice(0, 3).map((risk, index) => (
                      <p key={`${risk}-${index}`} className="text-xs text-foreground">
                        {risk}
                      </p>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-card/70 p-3">
                  <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Top Opportunities</p>
                  <div className="mt-2 space-y-1">
                    {topOpportunities.slice(0, 3).map((item, index) => (
                      <p key={`${item}-${index}`} className="text-xs text-foreground">
                        {item}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {Object.keys(kpiDeltas).length > 0 && (
              <div className="mt-3 rounded-xl border border-border bg-card/70 p-3">
                <p className="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">KPI Deltas</p>
                <div className="space-y-1">
                  {Object.entries(kpiDeltas)
                    .slice(0, 5)
                    .map(([metric, value]) => (
                      <p key={metric} className="flex items-center justify-between text-xs text-foreground">
                        <span>{metric}</span>
                        <span className={Number(value) >= 0 ? "text-success" : "text-warning"}>
                          {Number(value) > 0 ? "+" : ""}
                          {Number(value).toFixed(2)}
                        </span>
                      </p>
                    ))}
                </div>
              </div>
            )}
          </div>

          {error && <div className="rounded-xl border border-red-500/30 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <div className="rounded-2xl border border-border bg-background/80 p-4">
            <button
              type="button"
              onClick={() => setShowTechTrace((prev) => !prev)}
              className="flex w-full items-center justify-between text-left"
            >
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Technical Trace</p>
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                {showTechTrace ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                {showTechTrace ? "Hide" : "Show"}
                <ChevronRight className={`h-3.5 w-3.5 transition ${showTechTrace ? "rotate-90" : ""}`} />
              </span>
            </button>
            {showTechTrace && (
              <div className="mt-3 max-h-36 space-y-1 overflow-auto">
                {eventLog.length === 0 && <p className="text-xs text-muted-foreground">No node events captured yet.</p>}
                {eventLog.map((entry, index) => (
                  <p key={`${entry}-${index}`} className="rounded border border-border bg-card/70 px-2 py-1 text-xs text-foreground" style={{ fontFamily: '"IBM Plex Mono", monospace' }}>
                    {entry}
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
