import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Crown,
  Flame,
  GitBranch,
  Eye,
  EyeOff,
  Gauge,
  ListTree,
  Loader2,
  Orbit,
  Radar,
  Rocket,
  ScanSearch,
  Timer,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  const rationaleFallback = rationale.toLowerCase().includes("fallback");
  const isFallback = risks.some((risk) => risk.toLowerCase().includes("fallback")) || rationaleFallback;

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
  if (status === "done") return "bg-success/15 text-foreground border-success/35";
  if (status === "fallback") return "bg-warning/15 text-foreground border-warning/35";
  if (status === "running") return "bg-primary/15 text-foreground border-primary/35";
  return "bg-muted/80 text-foreground border-border";
}

function statusAccent(status: PersonaState): string {
  if (status === "done") return "from-emerald-500/30 to-emerald-500/5";
  if (status === "fallback") return "from-amber-500/30 to-amber-500/5";
  if (status === "running") return "from-cyan-500/30 to-cyan-500/5";
  return "from-zinc-500/25 to-zinc-500/5";
}

function flowTone(state: StepState): string {
  if (state === "done") return "border-success/50 bg-success/10 text-success";
  if (state === "active") return "border-primary/60 bg-primary/10 text-primary";
  return "border-border bg-background/70 text-muted-foreground";
}

function nodePillTone(state: StepState): string {
  if (state === "done") return "bg-success/15 text-foreground border-success/35";
  if (state === "active") return "bg-primary/15 text-foreground border-primary/35 animate-pulse";
  return "bg-muted text-muted-foreground border-border";
}

function findLikelyPersonaFromToken(text: string, personaIds: string[]): string | null {
  const lower = text.toLowerCase();
  const match = personaIds.find((id) => {
    const normalizedId = id.toLowerCase();
    const idAsSpace = normalizedId.replace(/[_-]/g, " ");
    const idAsDash = normalizedId.replace(/[_ ]/g, "-");
    return lower.includes(normalizedId) || lower.includes(idAsSpace) || lower.includes(idAsDash);
  });
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
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [showTechTrace, setShowTechTrace] = useState(false);
  const streamBufferRef = useRef<Record<string, string>>({});
  const flushTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isRunning) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [isRunning]);

  useEffect(() => {
    return () => {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
      }
    };
  }, []);

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

  const swarmCounts = useMemo(() => {
    const counts = { queued: 0, running: 0, done: 0, fallback: 0 };
    Object.values(personas).forEach((persona) => {
      counts[persona.status] += 1;
    });
    return counts;
  }, [personas]);

  const activeNode = useMemo(() => FLOW.find((step) => flowState[step.id] === "active") ?? null, [flowState]);

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

  const ensurePersonaExists = (personaId: string) => {
    setPersonas((prev) => {
      if (prev[personaId]) return prev;
      return {
        ...prev,
        [personaId]: {
          persona_id: personaId,
          confidence: 0,
          risks: [],
          opportunities: [],
          rationale: "Subagent actively reasoning over scenario details.",
          kpi_deltas: {},
          status: "queued",
          stream: [],
        },
      };
    });
    setPersonaOrder((prev) => (prev.includes(personaId) ? prev : [...prev, personaId]));
  };

  const markPersonaRunning = (personaId: string) => {
    ensurePersonaExists(personaId);
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
    ensurePersonaExists(personaId);
    streamBufferRef.current[personaId] = `${streamBufferRef.current[personaId] ?? ""}${line}`;
    if (flushTimerRef.current !== null) return;
    flushTimerRef.current = window.setTimeout(() => {
      const updates = streamBufferRef.current;
      streamBufferRef.current = {};
      flushTimerRef.current = null;
      const personaIds = Object.keys(updates);
      if (personaIds.length === 0) return;
      setPersonas((prev) => {
        const next = { ...prev };
        personaIds.forEach((id) => {
          const item = next[id];
          if (!item) return;
          const text = updates[id];
          if (!text) return;
          next[id] = {
            ...item,
            stream: [...item.stream, text].slice(-240),
          };
        });
        return next;
      });
    }, 80);
  };

  const flushPersonaStreamBuffer = () => {
    if (flushTimerRef.current !== null) {
      window.clearTimeout(flushTimerRef.current);
      flushTimerRef.current = null;
    }
    const updates = streamBufferRef.current;
    streamBufferRef.current = {};
    const personaIds = Object.keys(updates);
    if (personaIds.length === 0) return;
    setPersonas((prev) => {
      const next = { ...prev };
      personaIds.forEach((id) => {
        const item = next[id];
        if (!item) return;
        const text = updates[id];
        if (!text) return;
        next[id] = {
          ...item,
          stream: [...item.stream, text].slice(-240),
        };
      });
      return next;
    });
  };

  const handleEvent = (event: SimulatorStreamEvent) => {
    if (event.type === "status" && event.message) {
      appendEventLog(event.message);
      return;
    }

    if (event.type === "token" && event.text) {
      const tokenText = event.text;
      const nodeName = typeof event.node === "string" && event.node ? event.node : "model_stream";
      if (showTechTrace) {
        const tokenPreview = clipText(tokenText, 200);
        appendEventLog(`${nodeName}: ${tokenPreview}`);
      }

      const personaIds = personaOrder.length > 0 ? personaOrder : Object.keys(personas);
      const personaFromToken = findLikelyPersonaFromToken(tokenText, personaIds);
      const personaFromMeta = event.meta && typeof event.meta.persona_id === "string" ? event.meta.persona_id : null;
      const personaFromNode = findLikelyPersonaFromToken(nodeName, personaIds);
      const runningPersona = personaIds.find((id) => personas[id]?.status === "running");
      const queuedPersona = personaIds.find((id) => personas[id]?.status === "queued");
      const targetPersona = personaFromMeta ?? personaFromToken ?? personaFromNode ?? runningPersona ?? queuedPersona ?? null;

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
            appendEventLog(`Orchestrator: Spawned ${personaIds.length} subagents.`);
          }
        }

        const workerPayload = payload.persona_worker as Record<string, unknown> | undefined;
        if (workerPayload && Array.isArray(workerPayload.persona_stream_events)) {
          workerPayload.persona_stream_events.forEach((evt) => {
            if (!evt || typeof evt !== "object") return;
            const row = evt as Record<string, unknown>;
            const personaId = typeof row.persona_id === "string" ? row.persona_id : null;
            const text = typeof row.text === "string" ? row.text : "";
            const preview = clipText(text, 180);
            const nodeName = typeof row.node === "string" && row.node ? row.node : "subagent";
            if (!personaId || !text) return;
            markPersonaRunning(personaId);
            appendPersonaStream(personaId, text);
            appendEventLog(`${titleizePersonaId(personaId)} · ${nodeName}: ${preview}`);
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
              appendEventLog(`${personaName}: ${statusWord} analysis.`);
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
      flushPersonaStreamBuffer();
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

      appendEventLog("System: Recommendation package finalized.");

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
      flushPersonaStreamBuffer();
      setError(event.error ?? "Unknown simulator error.");
      appendEventLog(`System error: ${event.error ?? "Unknown simulator error."}`);
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
    setEventLog([]);
    setError(null);
    streamBufferRef.current = {};
    if (flushTimerRef.current !== null) {
      window.clearTimeout(flushTimerRef.current);
      flushTimerRef.current = null;
    }
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

  const selectedPersonaTranscript = selectedPersonaCard
    ? selectedPersonaCard.stream.join("")
    : "";

  return (
    <section className="relative w-full overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_5%,hsl(var(--primary)/0.16),transparent_34%),radial-gradient(circle_at_90%_8%,hsl(var(--warning)/0.14),transparent_34%),radial-gradient(circle_at_50%_75%,hsl(var(--accent)/0.15),transparent_38%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-20 [background-image:linear-gradient(to_right,hsl(var(--foreground)/0.1)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--foreground)/0.1)_1px,transparent_1px)] [background-size:42px_42px]" />
      <div className="relative border-b border-border/80 px-6 py-6 md:px-8">
        <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
          <div>
            <p className="text-[0.62rem] uppercase tracking-[0.35em] text-primary">Strategic War Room</p>
            <h2 className="mt-2 text-4xl leading-[0.95] md:text-5xl" style={{ fontFamily: '"Baskerville Old Face", "Times New Roman", serif' }}>
              Swarm Simulation Reactor
            </h2>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              Realtime node-level execution, deep-agent swarm streams, and final recommendation synthesis.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-card/80 p-3 shadow-card">
              <p className="text-[0.62rem] uppercase tracking-[0.2em] text-muted-foreground">Runtime</p>
              <p className="mt-1 inline-flex items-center gap-2 text-sm font-semibold">
                <Orbit className={`h-4 w-4 ${isRunning ? "text-primary animate-spin" : "text-muted-foreground"}`} />
                {isRunning ? "Hot" : "Idle"}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card/80 p-3 shadow-card">
              <p className="text-[0.62rem] uppercase tracking-[0.2em] text-muted-foreground">Elapsed</p>
              <p className="mt-1 inline-flex items-center gap-2 text-sm font-semibold">
                <Timer className="h-4 w-4 text-warning" />
                {elapsedSeconds.toFixed(1)}s
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card/80 p-3 shadow-card">
              <p className="text-[0.62rem] uppercase tracking-[0.2em] text-muted-foreground">Confidence</p>
              <p className="mt-1 inline-flex items-center gap-2 text-sm font-semibold">
                <Crown className="h-4 w-4 text-success" />
                {swarmConfidence}%
              </p>
            </div>
          </div>
        </div>
        <div className="mt-5 flex flex-col gap-3 lg:flex-row">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-12 border-border bg-card/80 text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
            placeholder="Enter a business simulation question"
            style={{ fontFamily: '"IBM Plex Mono", monospace' }}
          />
          <Button
            onClick={runSimulation}
            disabled={isRunning}
            className="h-12 min-w-52 border border-primary/30 bg-primary px-5 font-semibold text-primary-foreground hover:bg-primary/90"
            style={{ fontFamily: '"IBM Plex Mono", monospace' }}
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Swarm
              </>
            ) : (
              <>
                <Rocket className="mr-2 h-4 w-4" />
                Launch Swarm
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="relative grid gap-5 px-6 py-6 md:px-8 md:py-7 xl:grid-cols-12">
        <aside className="space-y-5 xl:col-span-3">
          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <div className="mb-3 flex items-center justify-between">
              <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <Activity className="h-4 w-4 text-primary" />
                Mission Timeline
              </p>
              <Badge className="border border-border bg-secondary text-secondary-foreground">{progressValue}%</Badge>
            </div>
            <Progress value={progressValue} className="h-2 bg-muted" />
            <div className="mt-4 space-y-2">
              {FLOW.map((step, idx) => {
                const stepStatus = flowState[step.id];
                return (
                  <div key={step.id} className={`rounded-xl border p-3 ${flowTone(stepStatus)}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Phase {idx + 1}</p>
                        <p className="text-sm font-semibold">{step.label}</p>
                        <p className="mt-1 text-xs leading-relaxed opacity-80">{step.narrative}</p>
                      </div>
                      <Badge className={`border ${nodePillTone(stepStatus)}`}>{stepStatus}</Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </aside>

        <main className="space-y-5 xl:col-span-5">
          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <Radar className="h-4 w-4 text-primary" />
                Swarm Stage
              </p>
              <div className="flex flex-wrap gap-2 text-xs">
                <Badge className="border border-border bg-secondary text-secondary-foreground">Queued {swarmCounts.queued}</Badge>
                <Badge className="border border-primary/40 bg-primary/10 text-foreground">Running {swarmCounts.running}</Badge>
                <Badge className="border border-success/40 bg-success/10 text-foreground">Done {swarmCounts.done}</Badge>
                <Badge className="border border-warning/40 bg-warning/10 text-foreground">Fallback {swarmCounts.fallback}</Badge>
              </div>
            </div>
            <div className="grid max-h-[31rem] gap-3 overflow-auto sm:grid-cols-2">
              {orderedPersonas.length === 0 && (
                <div className="rounded-xl border border-border bg-card/75 p-4 text-sm text-muted-foreground">
                  No subagents spawned yet.
                </div>
              )}
              {orderedPersonas.map((persona) => {
                const selected = selectedPersona === persona.persona_id;
                const lastStream = persona.stream[persona.stream.length - 1];
                return (
                  <button
                    key={persona.persona_id}
                    type="button"
                    onClick={() => setSelectedPersona(persona.persona_id)}
                    className={`relative overflow-hidden rounded-xl border text-left transition ${
                      selected
                        ? "border-primary/70 bg-card shadow-[0_0_0_1px_hsl(var(--primary)/0.3),0_18px_34px_-24px_hsl(var(--primary)/0.65)]"
                        : "border-border bg-card/80 hover:border-primary/50 hover:bg-card"
                    }`}
                  >
                    <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${statusAccent(persona.status)} opacity-90`} />
                    <div className="relative p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-foreground">{titleizePersonaId(persona.persona_id)}</p>
                          <p className="text-[0.62rem] uppercase tracking-[0.16em] text-muted-foreground">{persona.persona_id}</p>
                        </div>
                        <Badge className={statusTone(persona.status)}>{persona.status}</Badge>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                        <span>Confidence</span>
                        <span>{Math.round(persona.confidence * 100)}%</span>
                      </div>
                      <div className="mt-1 h-1.5 rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${Math.max(6, Math.min(100, Math.round(persona.confidence * 100)))}%` }}
                        />
                      </div>
                      <p
                        className="mt-3 rounded-md border border-border/70 bg-background/70 px-2 py-2 text-xs leading-relaxed text-foreground"
                        style={{ fontFamily: '"IBM Plex Mono", monospace' }}
                      >
                        {lastStream ? clipText(lastStream, 140) : "Awaiting live stream..."}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <p className="mb-3 inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <Gauge className="h-4 w-4 text-success" />
              Decision Reactor
            </p>
            <div className="rounded-xl border border-border bg-background/70 p-4 text-sm leading-relaxed text-foreground">
              {recommendation || "Aggregator is still composing the final recommendation..."}
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border bg-background/70 p-3">
                <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Top Risks</p>
                <div className="mt-2 space-y-1">
                  {(topRisks.length > 0 ? topRisks.slice(0, 3) : ["No dominant downside signal yet."]).map((risk, index) => (
                    <p key={`${risk}-${index}`} className="text-xs text-foreground">
                      {risk}
                    </p>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border border-border bg-background/70 p-3">
                <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Top Opportunities</p>
                <div className="mt-2 space-y-1">
                  {(topOpportunities.length > 0 ? topOpportunities.slice(0, 3) : ["No dominant upside signal yet."]).map((item, index) => (
                    <p key={`${item}-${index}`} className="text-xs text-foreground">
                      {item}
                    </p>
                  ))}
                </div>
              </div>
            </div>
            {Object.keys(kpiDeltas).length > 0 && (
              <div className="mt-3 rounded-xl border border-border bg-background/70 p-3">
                <p className="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">KPI Deltas</p>
                <div className="space-y-1">
                  {Object.entries(kpiDeltas)
                    .slice(0, 6)
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
        </main>

        <aside className="space-y-5 xl:col-span-4">
          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <p className="mb-3 inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <BrainCircuit className="h-4 w-4 text-primary" />
              Subagent Transcript
            </p>
            {!selectedPersonaCard && <p className="text-sm text-muted-foreground">Select a subagent card to inspect its live stream.</p>}
            {selectedPersonaCard && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-base font-semibold text-foreground">{titleizePersonaId(selectedPersonaCard.persona_id)}</p>
                    <p className="text-xs text-muted-foreground">{selectedPersonaCard.persona_id}</p>
                  </div>
                  <Badge className={statusTone(selectedPersonaCard.status)}>{selectedPersonaCard.status}</Badge>
                </div>
                <div className="rounded-xl border border-border bg-background/80 p-3">
                  <p className="mb-2 inline-flex items-center gap-1 text-xs uppercase tracking-[0.12em] text-muted-foreground">
                    <Flame className="h-3.5 w-3.5 text-primary" />
                    Realtime Markdown
                  </p>
                  <article className="max-h-[24rem] overflow-auto text-sm leading-relaxed text-foreground">
                    {selectedPersonaTranscript ? (
                      <div className="space-y-3 break-words [&_a]:text-primary [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_h1]:text-lg [&_h1]:font-semibold [&_h2]:text-base [&_h2]:font-semibold [&_li]:ml-5 [&_li]:list-disc [&_ol]:ml-5 [&_ol]:list-decimal [&_p]:whitespace-pre-wrap [&_pre]:overflow-auto [&_pre]:rounded-md [&_pre]:border [&_pre]:border-border [&_pre]:bg-muted/40 [&_pre]:p-2">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {selectedPersonaTranscript}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">Waiting for first token...</p>
                    )}
                  </article>
                </div>
              </div>
            )}
          </div>

          {error && <div className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <button
              type="button"
              onClick={() => setShowTechTrace((prev) => !prev)}
              className="flex w-full items-center justify-between text-left"
            >
              <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                <ListTree className="h-4 w-4 text-primary" />
                Trace Console
              </p>
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                {showTechTrace ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                {showTechTrace ? "Hide" : "Show"}
                <ChevronRight className={`h-3.5 w-3.5 transition ${showTechTrace ? "rotate-90" : ""}`} />
              </span>
            </button>
            {showTechTrace && (
              <div className="mt-3 max-h-44 space-y-1 overflow-auto">
                {eventLog.length === 0 && <p className="text-xs text-muted-foreground">No node events captured yet.</p>}
                {eventLog.map((entry, index) => (
                  <p
                    key={`${entry}-${index}`}
                    className="rounded border border-border bg-background/75 px-2 py-1 text-xs text-foreground"
                    style={{ fontFamily: '"IBM Plex Mono", monospace' }}
                  >
                    {entry}
                  </p>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-border bg-card/75 p-4 shadow-card">
            <p className="mb-2 inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
              <ScanSearch className="h-4 w-4 text-primary" />
              Current Focus
            </p>
            <p className="text-sm text-foreground">
              {activeNode ? `${activeNode.label}: ${activeNode.narrative}` : "Awaiting first execution node."}
            </p>
            <p className="mt-2 inline-flex items-center gap-2 text-xs text-muted-foreground">
              <GitBranch className="h-3.5 w-3.5" />
              Branch stress tests activate after impact rollup.
            </p>
          </div>
        </aside>
      </div>
    </section>
  );
}





