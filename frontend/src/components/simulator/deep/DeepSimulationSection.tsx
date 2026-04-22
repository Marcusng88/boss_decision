import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  BadgeDollarSign,
  Banknote,
  Building2,
  CheckCircle2,
  Factory,
  GraduationCap,
  Landmark,
  Megaphone,
  Pause,
  Play,
  RotateCcw,
  Info,
  FileText,
  X,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Store,
  TrendingUp,
  Users,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DeepSimulatorStreamEvent, streamDeepSimulator } from "@/lib/simulator-client";

type AgentStatus = "idle" | "thinking" | "acting" | "done";

interface AgentCard {
  id: string;
  name: string;
  role: string;
  objective: string;
  allowedPaths: string[];
  color: string;
  x: number;
  y: number;
  status: AgentStatus;
  toolCalls: string[];
  transcript: string;
  confidence: number;
  score: number;
}

interface TimelineEvent {
  id: string;
  tick: number;
  message: string;
}

interface ScorePoint {
  tick: number;
  [key: string]: number;
}

interface FinalReport {
  summary: string;
  recommendation: string;
  confidence: number;
  key_turning_points: string[];
  persona_observations?: Array<{
    persona_id: string;
    name: string;
    role: string;
    objective: string;
    stance: string;
    evidence: string[];
    suggested_next_action: string;
  }>;
  html_slides: string;
}

interface BoardTile {
  id: string;
  name: string;
  x: number;
  y: number;
}

interface TileVisual {
  icon: LucideIcon;
  accentClass: string;
  iconClass: string;
  blocks: number;
}

interface WorldAgent {
  id?: unknown;
  name?: unknown;
  role?: unknown;
  x?: unknown;
  y?: unknown;
  status?: unknown;
  tool_calls?: unknown;
  transcript?: unknown;
  confidence?: unknown;
}

interface WorldPersona {
  id?: unknown;
  name?: unknown;
  role?: unknown;
  objective?: unknown;
  allowed_paths?: unknown;
}

const DEFAULT_QUERY = "Should we increase price by 10% for student segment next quarter?";
const DEFAULT_MAX_TICKS = 5;
const RUN_TICK_MIN = 1;
const RUN_TICK_MAX = 240;
const SHARED_START_X = 50;
const SHARED_START_Y = 50;

const AGENT_COLOR_OVERRIDES: Record<string, string> = {
  consumer_psychologist_001: "hsl(18 88% 51%)",
  pricing_strategist_001: "hsl(171 66% 36%)",
  market_risk_001: "hsl(38 86% 44%)",
  ops_constraints_001: "hsl(148 62% 34%)",
  brand_positioning_001: "hsl(204 32% 26%)",
};

const PERSONA_COLOR_PALETTE = [
  "hsl(18 88% 51%)",
  "hsl(171 66% 36%)",
  "hsl(38 86% 44%)",
  "hsl(148 62% 34%)",
  "hsl(204 32% 26%)",
  "hsl(12 73% 52%)",
  "hsl(26 79% 46%)",
  "hsl(196 48% 38%)",
  "hsl(163 54% 34%)",
  "hsl(29 69% 40%)",
  "hsl(205 21% 34%)",
  "hsl(8 63% 44%)",
];

const PERSONA_SPRITES = Array.from(
  { length: 49 },
  (_, idx) => `/assets/personas/persona_${String(idx + 1).padStart(2, "0")}.png`,
);

const personaVisualCache = new Map<string, { color: string; avatarUrl: string }>();

function hashString(input: string): number {
  let hash = 0;
  for (let idx = 0; idx < input.length; idx += 1) {
    hash = (hash * 31 + input.charCodeAt(idx)) >>> 0;
  }
  return hash;
}

function getPersonaVisual(personaId: string): { color: string; avatarUrl: string } {
  const cached = personaVisualCache.get(personaId);
  if (cached) return cached;
  const hash = hashString(personaId || "persona");
  const color = AGENT_COLOR_OVERRIDES[personaId] ?? PERSONA_COLOR_PALETTE[hash % PERSONA_COLOR_PALETTE.length];
  const avatarUrl = PERSONA_SPRITES[hash % PERSONA_SPRITES.length];
  const visual = { color, avatarUrl };
  personaVisualCache.set(personaId, visual);
  return visual;
}

const BASE_AGENTS: AgentCard[] = [
  {
    id: "consumer_psychologist_001",
    name: "Consumer Psychologist",
    role: "Demand behavior lead",
    objective: "Understand student demand reaction and churn behavior.",
    allowedPaths: [],
    color: AGENT_COLOR_OVERRIDES.consumer_psychologist_001,
    x: SHARED_START_X,
    y: SHARED_START_Y,
    status: "idle",
    toolCalls: [],
    transcript: "",
    confidence: 0.5,
    score: 0,
  },
  {
    id: "pricing_strategist_001",
    name: "Pricing Strategist",
    role: "Price and promo architect",
    objective: "Model price elasticity and promotion tradeoffs.",
    allowedPaths: [],
    color: AGENT_COLOR_OVERRIDES.pricing_strategist_001,
    x: SHARED_START_X,
    y: SHARED_START_Y,
    status: "idle",
    toolCalls: [],
    transcript: "",
    confidence: 0.5,
    score: 0,
  },
  {
    id: "market_risk_001",
    name: "Market Risk",
    role: "Competitor response radar",
    objective: "Estimate competitor retaliation and market downside.",
    allowedPaths: [],
    color: AGENT_COLOR_OVERRIDES.market_risk_001,
    x: SHARED_START_X,
    y: SHARED_START_Y,
    status: "idle",
    toolCalls: [],
    transcript: "",
    confidence: 0.5,
    score: 0,
  },
  {
    id: "ops_constraints_001",
    name: "Ops Constraints",
    role: "Execution feasibility owner",
    objective: "Validate operational feasibility and rollout limits.",
    allowedPaths: [],
    color: AGENT_COLOR_OVERRIDES.ops_constraints_001,
    x: SHARED_START_X,
    y: SHARED_START_Y,
    status: "idle",
    toolCalls: [],
    transcript: "",
    confidence: 0.5,
    score: 0,
  },
  {
    id: "brand_positioning_001",
    name: "Brand Positioning",
    role: "Narrative and trust steward",
    objective: "Protect brand trust and long-term positioning.",
    allowedPaths: [],
    color: AGENT_COLOR_OVERRIDES.brand_positioning_001,
    x: SHARED_START_X,
    y: SHARED_START_Y,
    status: "idle",
    toolCalls: [],
    transcript: "",
    confidence: 0.5,
    score: 0,
  },
];

const DEFAULT_TILES: BoardTile[] = [
  { id: "demand_hub", name: "Demand Hub", x: 10, y: 10 },
  { id: "campus_square", name: "Campus Square", x: 30, y: 10 },
  { id: "digital_blast", name: "Digital Blast", x: 50, y: 10 },
  { id: "retail_lane", name: "Retail Lane", x: 70, y: 10 },
  { id: "promo_stage", name: "Promo Stage", x: 90, y: 30 },
  { id: "supply_yard", name: "Supply Yard", x: 90, y: 50 },
  { id: "finance_tower", name: "Finance Tower", x: 90, y: 70 },
  { id: "brand_garden", name: "Brand Garden", x: 70, y: 90 },
  { id: "competitor_radar", name: "Competitor Radar", x: 50, y: 90 },
  { id: "compliance_gate", name: "Compliance Gate", x: 30, y: 90 },
  { id: "loyalty_park", name: "Loyalty Park", x: 10, y: 90 },
  { id: "volatility_crossing", name: "Volatility Crossing", x: 10, y: 50 },
];

const TILE_VISUALS: Record<string, TileVisual> = {
  demand_hub: { icon: Building2, accentClass: "bg-slate-600", iconClass: "text-slate-600", blocks: 4 },
  campus_square: { icon: GraduationCap, accentClass: "bg-indigo-600", iconClass: "text-indigo-600", blocks: 3 },
  digital_blast: { icon: ShoppingCart, accentClass: "bg-cyan-600", iconClass: "text-cyan-600", blocks: 3 },
  retail_lane: { icon: Store, accentClass: "bg-emerald-600", iconClass: "text-emerald-600", blocks: 2 },
  promo_stage: { icon: Megaphone, accentClass: "bg-rose-600", iconClass: "text-rose-600", blocks: 3 },
  supply_yard: { icon: Factory, accentClass: "bg-amber-700", iconClass: "text-amber-700", blocks: 4 },
  finance_tower: { icon: Banknote, accentClass: "bg-green-700", iconClass: "text-green-700", blocks: 4 },
  brand_garden: { icon: Sparkles, accentClass: "bg-fuchsia-600", iconClass: "text-fuchsia-600", blocks: 3 },
  competitor_radar: { icon: Users, accentClass: "bg-orange-700", iconClass: "text-orange-700", blocks: 2 },
  compliance_gate: { icon: ShieldCheck, accentClass: "bg-blue-700", iconClass: "text-blue-700", blocks: 3 },
  loyalty_park: { icon: Landmark, accentClass: "bg-teal-700", iconClass: "text-teal-700", blocks: 2 },
  volatility_crossing: { icon: AlertTriangle, accentClass: "bg-red-700", iconClass: "text-red-700", blocks: 2 },
};

function tileVisual(id: string): TileVisual {
  return TILE_VISUALS[id] ?? {
    icon: BadgeDollarSign,
    accentClass: "bg-slate-500",
    iconClass: "text-slate-600",
    blocks: 2,
  };
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function formatSigned(value: number): string {
  if (value > 0) return `+${value.toFixed(2)}`;
  return value.toFixed(2);
}

function humanStatus(status: AgentStatus): string {
  if (status === "done") return "Done";
  if (status === "acting") return "Acting";
  if (status === "thinking") return "Thinking";
  return "Idle";
}

function statusBadgeTone(status: AgentStatus): string {
  if (status === "done") return "border-success/40 bg-success/10 text-foreground";
  if (status === "acting") return "border-primary/50 bg-primary/10 text-foreground";
  if (status === "thinking") return "border-warning/40 bg-warning/10 text-foreground";
  return "border-border bg-secondary text-secondary-foreground";
}

function mapWorldAgents(input: unknown, previous: AgentCard[]): AgentCard[] {
  if (!Array.isArray(input)) return previous;
  const prevById = Object.fromEntries(previous.map((agent) => [agent.id, agent]));
  return input
    .map((row) => {
      if (!row || typeof row !== "object") return null;
      const agent = row as WorldAgent;
      const id = typeof agent.id === "string" ? agent.id : "";
      if (!id) return null;
      const prev = prevById[id];
      const status = agent.status;
      const normalizedStatus: AgentStatus =
        status === "idle" || status === "thinking" || status === "acting" || status === "done"
          ? status
          : prev?.status ?? "idle";
      return {
        id,
        name: typeof agent.name === "string" ? agent.name : prev?.name ?? id,
        role: typeof agent.role === "string" ? agent.role : prev?.role ?? "persona",
        objective: prev?.objective ?? "",
        allowedPaths: prev?.allowedPaths ?? [],
        color: prev?.color ?? getPersonaVisual(id).color,
        x: asNumber(agent.x, prev?.x ?? 50),
        y: asNumber(agent.y, prev?.y ?? 50),
        status: normalizedStatus,
        toolCalls: Array.isArray(agent.tool_calls)
          ? agent.tool_calls.filter((item): item is string => typeof item === "string").slice(-10)
          : prev?.toolCalls ?? [],
        transcript: typeof agent.transcript === "string" ? agent.transcript : prev?.transcript ?? "",
        confidence: asNumber(agent.confidence, prev?.confidence ?? 0.5),
        score: prev?.score ?? 0,
      };
    })
    .filter((item): item is AgentCard => item !== null);
}

function applyPersonaProfiles(input: unknown, previous: AgentCard[]): AgentCard[] {
  if (!Array.isArray(input)) return previous;
  const byId = new Map<string, WorldPersona>();
  for (const row of input) {
    if (!row || typeof row !== "object") continue;
    const persona = row as WorldPersona;
    const id = typeof persona.id === "string" ? persona.id : "";
    if (!id) continue;
    byId.set(id, persona);
  }
  if (byId.size === 0) return previous;
  return previous.map((agent) => {
    const persona = byId.get(agent.id);
    if (!persona) return agent;
    const allowedPaths = Array.isArray(persona.allowed_paths)
      ? persona.allowed_paths.filter((item): item is string => typeof item === "string")
      : agent.allowedPaths;
    return {
      ...agent,
      name: typeof persona.name === "string" ? persona.name : agent.name,
      role: typeof persona.role === "string" ? persona.role : agent.role,
      objective: typeof persona.objective === "string" ? persona.objective : agent.objective,
      allowedPaths,
    };
  });
}

function mapBoardTiles(input: unknown, fallback: BoardTile[]): BoardTile[] {
  if (!Array.isArray(input)) return fallback;
  const parsed = input
    .map((row) => {
      if (!row || typeof row !== "object") return null;
      const item = row as Record<string, unknown>;
      if (typeof item.id !== "string" || typeof item.name !== "string") return null;
      return {
        id: item.id,
        name: item.name,
        x: asNumber(item.x, 50),
        y: asNumber(item.y, 50),
      };
    })
    .filter((item): item is BoardTile => item !== null);
  return parsed.length > 0 ? parsed : fallback;
}

function asScoreMap(input: unknown): Record<string, number> {
  if (!input || typeof input !== "object") return {};
  const out: Record<string, number> = {};
  for (const [key, value] of Object.entries(input as Record<string, unknown>)) {
    out[key] = asNumber(value, 0);
  }
  return out;
}

function PersonaAvatar({
  personaId,
  name,
  size = 24,
  className = "",
}: {
  personaId: string;
  name: string;
  size?: number;
  className?: string;
}) {
  const visual = getPersonaVisual(personaId);
  return (
    <span
      className={`inline-flex items-center justify-center overflow-hidden rounded-lg border-2 bg-white ${className}`}
      style={{ width: size, height: size, borderColor: visual.color }}
    >
      <img
        src={visual.avatarUrl}
        alt={name}
        className="h-full w-full object-contain"
        style={{ imageRendering: "pixelated" }}
        draggable={false}
      />
    </span>
  );
}

export function DeepSimulationSection() {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [requestedTicks, setRequestedTicks] = useState(DEFAULT_MAX_TICKS);
  const [tick, setTick] = useState(0);
  const [maxTicks, setMaxTicks] = useState(DEFAULT_MAX_TICKS);
  const [running, setRunning] = useState(false);
  const [progressSummary, setProgressSummary] = useState("Ready to run the tycoon crisis simulation.");
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentCard[]>(BASE_AGENTS);
  const [selectedAgentId, setSelectedAgentId] = useState(BASE_AGENTS[0].id);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [boardTiles, setBoardTiles] = useState<BoardTile[]>(DEFAULT_TILES);
  const [kpi, setKpi] = useState({ revenue: 0, margin: 0, sentiment: 0, churn_risk: 0 });
  const [scoreSeries, setScoreSeries] = useState<ScorePoint[]>([]);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [showResultCard, setShowResultCard] = useState(false);
  const [showInfoCard, setShowInfoCard] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const lastWorldTickRef = useRef(0);
  const timelineRef = useRef<TimelineEvent[]>([]);
  const lastWorldUiTsRef = useRef(0);

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? null,
    [agents, selectedAgentId],
  );

  const progressPct = maxTicks > 0 ? Math.min(100, Math.round((tick / maxTicks) * 100)) : 0;

  const stopStream = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setRunning(false);
  };

  const resetSimulation = () => {
    stopStream();
    setError(null);
    setTick(0);
    setMaxTicks(DEFAULT_MAX_TICKS);
    setRequestedTicks(DEFAULT_MAX_TICKS);
    setProgressSummary("Ready to run the tycoon crisis simulation.");
    setAgents(BASE_AGENTS);
    setSelectedAgentId(BASE_AGENTS[0].id);
    setTimeline([]);
    timelineRef.current = [];
    setBoardTiles(DEFAULT_TILES);
    setKpi({ revenue: 0, margin: 0, sentiment: 0, churn_risk: 0 });
    lastWorldTickRef.current = 0;
    setScoreSeries([]);
    setFinalReport(null);
    setShowResultCard(false);
    setShowInfoCard(false);
    lastWorldUiTsRef.current = 0;
  };

  const handleEvent = (event: DeepSimulatorStreamEvent) => {
    if (event.type === "status") {
      if (typeof event.max_ticks === "number") setMaxTicks(event.max_ticks);
      if (typeof event.message === "string") setProgressSummary(event.message);
      return;
    }

    if (event.type === "progress") {
      if (typeof event.tick === "number") setTick(event.tick);
      if (typeof event.max_ticks === "number") setMaxTicks(event.max_ticks);
      if (typeof event.summary === "string") setProgressSummary(event.summary);
      return;
    }

    if (event.type === "timeline") {
      if (typeof event.tick !== "number" || typeof event.message !== "string") return;
      const row: TimelineEvent = {
        id: `${event.tick}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        tick: event.tick,
        message: event.message,
      };
      setTimeline((prev) => {
        const next = [row, ...prev].slice(0, 160);
        timelineRef.current = next;
        return next;
      });
      return;
    }

    if (event.type === "world") {
      if (!event.state || typeof event.state !== "object") return;
      const state = event.state;
      const stateTick = typeof state.tick === "number" ? state.tick : tick;
      if (typeof state.tick === "number") setTick(state.tick);
      if (typeof state.max_ticks === "number") setMaxTicks(state.max_ticks);

      const currentKpi = {
        revenue: 0,
        margin: 0,
        sentiment: 0,
        churn_risk: 0,
      };
      if (state.kpi && typeof state.kpi === "object") {
        const k = state.kpi as Record<string, unknown>;
        currentKpi.revenue = asNumber(k.revenue, 0);
        currentKpi.margin = asNumber(k.margin, 0);
        currentKpi.sentiment = asNumber(k.sentiment, 0);
        currentKpi.churn_risk = asNumber(k.churn_risk, 0);
      }
      setKpi(currentKpi);

      if (state.map && typeof state.map === "object") {
        const mapState = state.map as Record<string, unknown>;
        setBoardTiles((prev) => mapBoardTiles(mapState.zones, prev));
      }

      const scores = asScoreMap((state as Record<string, unknown>).scores);
      const now = Date.now();
      const shouldPaintHeavy = now - lastWorldUiTsRef.current > 140 || stateTick !== lastWorldTickRef.current;

      setAgents((prev) => {
        const next = mapWorldAgents(state.agents, prev);
        const withPersonaProfiles = applyPersonaProfiles((state as Record<string, unknown>).personas, next);
        const withScores = withPersonaProfiles.map((agent) => ({ ...agent, score: scores[agent.id] ?? agent.score }));
        return withScores.length > 0 ? withScores : prev;
      });

      if (Object.keys(scores).length > 0 && stateTick > 0) {
        setScoreSeries((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.tick === stateTick) {
            const merged = { ...last, ...scores };
            return [...prev.slice(0, -1), merged];
          }
          return [...prev, { tick: stateTick, ...scores }].slice(-180);
        });
      }

      if (!shouldPaintHeavy) return;
      lastWorldUiTsRef.current = now;
      lastWorldTickRef.current = stateTick;

      if (Array.isArray(state.timeline)) {
        const timelineRows = state.timeline
          .map((row) => {
            if (!row || typeof row !== "object") return null;
            const data = row as Record<string, unknown>;
            if (typeof data.id !== "string" || typeof data.tick !== "number" || typeof data.message !== "string") {
              return null;
            }
            return { id: data.id, tick: data.tick, message: data.message };
          })
          .filter((item): item is TimelineEvent => item !== null);
        if (timelineRows.length > 0) {
          const trimmed = timelineRows.slice(0, 160);
          timelineRef.current = trimmed;
          setTimeline(trimmed);
        }
      }

      return;
    }

    if (event.type === "agent_tool_call") {
      if (typeof event.persona_id !== "string" || typeof event.tool_call !== "string") return;
      const personaId = event.persona_id;
      setAgents((prev) =>
        prev.map((agent) =>
          agent.id === personaId
            ? { ...agent, toolCalls: [...agent.toolCalls, event.tool_call!].slice(-10), status: "acting" }
            : agent,
        ),
      );
      setSelectedAgentId((current) => current || personaId);
      return;
    }

    if (event.type === "agent_chunk") {
      if (typeof event.persona_id !== "string") return;
      const personaId = event.persona_id;
      const chunk = typeof event.chunk === "string" ? event.chunk : "";
      setAgents((prev) =>
        prev.map((agent) =>
          agent.id === personaId
            ? { ...agent, status: "acting", transcript: chunk ? `${agent.transcript}${chunk}` : agent.transcript }
            : agent,
        ),
      );
      setSelectedAgentId((current) => current || personaId);
      return;
    }

    if (event.type === "final") {
      if (event.response && typeof event.response === "object") {
        const response = event.response as Record<string, unknown>;
        const summary = typeof response.summary === "string" ? response.summary : "Simulation completed.";
        const recommendation = typeof response.recommendation === "string" ? response.recommendation : "";
        const confidence = asNumber(response.confidence, 0.6);
        const keyTurningPoints = Array.isArray(response.key_turning_points)
          ? response.key_turning_points.filter((item): item is string => typeof item === "string")
          : [];
        const personaObservations = Array.isArray(response.persona_observations)
          ? response.persona_observations.filter(
              (item): item is NonNullable<FinalReport["persona_observations"]>[number] =>
                !!item && typeof item === "object" && typeof (item as Record<string, unknown>).persona_id === "string",
            )
          : [];
        const htmlSlides = typeof response.html_slides === "string" ? response.html_slides : "";
        setFinalReport({
          summary,
          recommendation,
          confidence,
          key_turning_points: keyTurningPoints,
          persona_observations: personaObservations,
          html_slides: htmlSlides,
        });
        setProgressSummary(summary);
      }
      setAgents((prev) => prev.map((agent) => ({ ...agent, status: "done" })));
      return;
    }

    if (event.type === "error") {
      setError(event.error ?? "Deep simulation stream failed.");
      setRunning(false);
      return;
    }

    if (event.type === "done") {
      setRunning(false);
    }
  };

  const startSimulation = async () => {
    if (running || !query.trim()) return;
    setError(null);
    setTick(0);
    setMaxTicks(requestedTicks);
    setProgressSummary("Setting up dynamic districts and crisis deck...");
    setAgents(BASE_AGENTS.map((agent) => ({ ...agent, transcript: "", toolCalls: [], status: "idle", score: 0 })));
    setTimeline([]);
    timelineRef.current = [];
    setKpi({ revenue: 0, margin: 0, sentiment: 0, churn_risk: 0 });
    lastWorldTickRef.current = 0;
    setScoreSeries([]);
    setFinalReport(null);
    setShowResultCard(false);
    setShowInfoCard(false);
    lastWorldUiTsRef.current = 0;
    setRunning(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamDeepSimulator(
        { query: query.trim(), max_ticks: requestedTicks, scenario_id: "pricing_war_v1" },
        { onEvent: handleEvent, signal: controller.signal },
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        const message = err instanceof Error ? err.message : "Failed to stream deep simulation.";
        setError(message);
      }
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setRunning(false);
    }
  };

  useEffect(() => {
    if (!selectedAgent && agents.length > 0) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgent]);

  const sortedAgents = useMemo(() => [...agents].sort((a, b) => b.score - a.score), [agents]);

  const exportFinalHtml = () => {
    if (!finalReport?.html_slides) return;
    const blob = new Blob([finalReport.html_slides], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `deep-simulation-report-day-${tick || maxTicks}.html`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="w-full text-foreground">
      <div className="border-b border-border/70 px-5 py-3 md:px-8">
        <div className="mb-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-[width] duration-300" style={{ width: `${progressPct}%` }} />
        </div>
        <p className="text-[11px] font-light tracking-[0.08em] text-muted-foreground">
          Day {tick}/{maxTicks} | {progressSummary}
        </p>
      </div>

      <div className="grid h-[calc(100vh-10.8rem)] gap-4 px-5 py-5 md:px-8 lg:grid-cols-[1.2fr_1.5fr_1.2fr]">
        <aside className="flex h-full min-h-0 min-w-0 flex-col rounded-2xl border border-border bg-card/85 p-4">
          <div className="mb-3 flex flex-col gap-2">
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-9 border-border bg-background/80 text-foreground placeholder:text-muted-foreground"
              placeholder="Ask a deep simulation question..."
            />
            <div className="grid grid-cols-[1fr_auto] items-center gap-2 rounded-xl border border-border bg-background/70 px-2 py-2">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Ticks Before End</p>
              <Input
                type="number"
                min={RUN_TICK_MIN}
                max={RUN_TICK_MAX}
                step={1}
                value={requestedTicks}
                onChange={(event) => {
                  const next = Number(event.target.value);
                  if (!Number.isFinite(next)) return;
                  const bounded = Math.max(RUN_TICK_MIN, Math.min(RUN_TICK_MAX, Math.floor(next)));
                  setRequestedTicks(bounded);
                }}
                className="h-8 w-24 border-border bg-background text-right text-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={startSimulation} disabled={running} className="h-9 border border-primary/35 bg-primary px-3 text-primary-foreground hover:bg-primary/90">
                <Play className="mr-1.5 h-3.5 w-3.5" /> Start
              </Button>
              <Button onClick={stopStream} disabled={!running} variant="secondary" className="h-9 px-3">
                <Pause className="mr-1.5 h-3.5 w-3.5" /> Pause
              </Button>
              <Button onClick={resetSimulation} variant="outline" className="h-9 px-3">
                <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> Reset
              </Button>
              <Button
                onClick={() => setShowResultCard(true)}
                disabled={!finalReport}
                variant="outline"
                className="h-9 px-3"
              >
                <FileText className="mr-1.5 h-3.5 w-3.5" /> Result
              </Button>
              <Button onClick={() => setShowInfoCard(true)} variant="outline" className="h-9 px-3">
                <Info className="mr-1.5 h-3.5 w-3.5" /> Info
              </Button>
            </div>
            {error ? <p className="text-xs text-destructive">{error}</p> : null}
          </div>

          <div className="mb-3 grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-border bg-background/80 p-2.5">
              <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Revenue</p>
              <p className="mt-1 text-sm font-semibold">{formatSigned(kpi.revenue)}%</p>
            </div>
            <div className="rounded-xl border border-border bg-background/80 p-2.5">
              <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Margin</p>
              <p className="mt-1 text-sm font-semibold">{formatSigned(kpi.margin)}%</p>
            </div>
            <div className="rounded-xl border border-border bg-background/80 p-2.5">
              <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Brand Trust</p>
              <p className="mt-1 text-sm font-semibold">{formatSigned(kpi.sentiment)}</p>
            </div>
            <div className="rounded-xl border border-border bg-background/80 p-2.5">
              <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Churn Risk</p>
              <p className="mt-1 text-sm font-semibold">{formatSigned(kpi.churn_risk)}</p>
            </div>
          </div>

          <div className="mb-3 h-56 rounded-xl border border-border bg-background/80 p-2.5">
            <div className="mb-1.5 flex items-center justify-between">
              <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground">Strategist Score Lines</p>
              <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {sortedAgents.map((agent) => (
                <span
                  key={`legend-${agent.id}`}
                  className="inline-flex items-center gap-1 rounded-full border border-border bg-card/80 px-1.5 py-0.5 text-[10px] text-foreground"
                >
                  <PersonaAvatar personaId={agent.id} name={agent.name} size={16} />
                  <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: agent.color }} />
                  {agent.name}
                </span>
              ))}
            </div>
            <ResponsiveContainer width="100%" height="74%">
              <LineChart data={scoreSeries} margin={{ top: 4, right: 8, bottom: 6, left: -16 }}>
                <XAxis dataKey="tick" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={30} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid hsl(var(--border))",
                    background: "hsl(var(--card))",
                    fontSize: 11,
                  }}
                />
                {sortedAgents.map((agent) => (
                  <Line
                    key={`line-${agent.id}`}
                    type="monotone"
                    dataKey={agent.id}
                    stroke={agent.color}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

        </aside>

        <main className="flex h-full min-h-0 min-w-0 flex-col rounded-2xl border border-border bg-card/85 p-4 overflow-hidden">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">District Board</p>
              <p className="text-sm text-muted-foreground">Daily roll, district effects, crisis mitigation.</p>
            </div>
            <Badge className="border border-primary/45 bg-primary/10 text-foreground">
              <Sparkles className="mr-1 h-3 w-3" /> Live Strategy Feed
            </Badge>
          </div>

          <div className="relative mb-4 h-[320px] flex-none overflow-hidden rounded-xl border border-border bg-[radial-gradient(circle_at_18%_0%,rgba(233,119,46,0.18),transparent_34%),radial-gradient(circle_at_88%_90%,rgba(22,154,142,0.18),transparent_32%),linear-gradient(180deg,hsl(var(--background)),hsl(var(--muted)))]">
            <div className="pointer-events-none absolute inset-2 rounded-xl border border-border/50 shadow-inner" />
            <div className="pointer-events-none absolute inset-0 opacity-25 [background-image:linear-gradient(to_right,rgba(28,28,28,0.13)_1px,transparent_1px),linear-gradient(to_bottom,rgba(28,28,28,0.13)_1px,transparent_1px)] [background-size:28px_28px]" />
            <div className="pointer-events-none absolute inset-[7%] rounded-[18px] border border-dashed border-border/65" />
            <div className="pointer-events-none absolute inset-[16%] rounded-[16px] border border-border/35" />

            {boardTiles.map((tile) => (
              <div
                key={tile.id}
                className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${tile.x}%`, top: `${tile.y}%` }}
              >
                {(() => {
                  const visual = tileVisual(tile.id);
                  const TileIcon = visual.icon;
                  return (
                    <div className="w-24 overflow-hidden rounded-md border border-border/90 bg-background/95 shadow-[0_6px_18px_rgba(0,0,0,0.12)]">
                      <div className={`h-1 w-full ${visual.accentClass}`} />
                      <div className="px-1.5 pb-1.5 pt-1">
                        <div className="flex items-center gap-1">
                          <TileIcon className={`h-3.5 w-3.5 ${visual.iconClass}`} />
                          <p className="line-clamp-1 text-[9px] font-semibold uppercase tracking-[0.06em] text-foreground">
                            {tile.name}
                          </p>
                        </div>
                        <div className="mt-1 flex gap-0.5">
                          {Array.from({ length: visual.blocks }).map((_, idx) => (
                            <span
                              key={`${tile.id}-b-${idx}`}
                              className="h-1.5 flex-1 rounded-[2px] border border-border/70 bg-muted"
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            ))}

            {agents.map((agent) => {
              const isSelected = agent.id === selectedAgentId;
              return (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => setSelectedAgentId(agent.id)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 transition-transform hover:scale-105"
                  style={{ left: `${agent.x}%`, top: `${agent.y}%` }}
                  title={agent.name}
                >
                  <span
                    className={`inline-flex rounded-xl border-2 bg-card/95 p-0.5 shadow-lg ${isSelected ? "ring-2 ring-primary/70" : ""}`}
                    style={{ borderColor: agent.color }}
                  >
                    <PersonaAvatar personaId={agent.id} name={agent.name} size={30} />
                  </span>
                </button>
              );
            })}
          </div>

          <div className="min-h-0 min-w-0 flex-1 overflow-y-auto overflow-x-hidden rounded-xl border border-border bg-background/85 p-3 sim-scroll">
            {!selectedAgent && <p className="text-sm text-muted-foreground">Select a strategist to inspect their live reasoning.</p>}
            {selectedAgent && (
              <>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Selected Strategist</p>
                    <p className="inline-flex items-center gap-2 text-base font-semibold">
                      <PersonaAvatar personaId={selectedAgent.id} name={selectedAgent.name} size={20} />
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: selectedAgent.color }} />
                      {selectedAgent.name}
                    </p>
                    <p className="text-xs text-muted-foreground">{selectedAgent.role}</p>
                    {selectedAgent.objective ? (
                      <p className="mt-1 text-xs leading-relaxed text-foreground">{selectedAgent.objective}</p>
                    ) : null}
                    {selectedAgent.allowedPaths.length > 0 ? (
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        Context scope: {selectedAgent.allowedPaths.slice(0, 2).join(", ")}
                      </p>
                    ) : null}
                  </div>
                  <Badge className={statusBadgeTone(selectedAgent.status)}>{humanStatus(selectedAgent.status)}</Badge>
                </div>

                <details open={selectedAgent.status !== "done"}>
                  <summary className="mb-2 cursor-pointer rounded-md border border-border bg-card/80 px-2 py-1 text-xs text-muted-foreground">
                    Tool calls ({selectedAgent.toolCalls.length})
                  </summary>
                  <div className="space-y-1.5">
                    {selectedAgent.toolCalls.length === 0 && <p className="text-xs text-muted-foreground">No tool calls yet.</p>}
                    {selectedAgent.toolCalls.map((call, idx) => (
                      <div key={`${call}-${idx}`} className="rounded-md border border-border bg-background/80 px-2 py-1.5">
                        <p className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                          <Wrench className="h-3 w-3" /> Tool call
                        </p>
                        <p className="text-xs text-foreground">{call}</p>
                      </div>
                    ))}
                  </div>
                </details>

                <div className="mt-3">
                  <p className="mb-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                    {selectedAgent.status === "done" ? "Final Response" : "Live Response"}
                  </p>
                  <div className="min-w-0 break-words text-sm leading-relaxed text-foreground [&_*]:max-w-full [&_a]:text-primary [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_li]:ml-5 [&_li]:list-disc [&_ol]:ml-5 [&_ol]:list-decimal [&_p]:whitespace-pre-wrap [&_p]:break-words [&_pre]:max-w-full [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:border [&_pre]:border-border [&_pre]:bg-muted/40 [&_pre]:p-2">
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {selectedAgent.transcript || "Awaiting transcript stream..."}
                    </ReactMarkdown>
                  </div>
                </div>

              </>
            )}
          </div>
        </main>

        <aside className="flex h-full min-h-0 min-w-0 flex-col rounded-2xl border border-border bg-card/85 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Strategist Swarm</p>
            <Badge className="border border-border bg-secondary text-secondary-foreground">{agents.length}</Badge>
          </div>

          <div className="mb-3 rounded-xl border border-border bg-background/80 p-2.5">
            <p className="text-[11px] uppercase tracking-[0.13em] text-muted-foreground">Scoreboard</p>
            <div className="mt-2 space-y-1.5">
              {sortedAgents.map((agent, idx) => (
                <div key={`rank-${agent.id}`} className="flex items-center justify-between rounded-md border border-border bg-card/85 px-2 py-1.5 text-xs">
                  <span className="inline-flex items-center gap-1.5 text-foreground">
                    <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-muted text-[10px]">{idx + 1}</span>
                    <PersonaAvatar personaId={agent.id} name={agent.name} size={18} />
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: agent.color }} />
                    {agent.name}
                  </span>
                  <span className="font-semibold" style={{ color: agent.color }}>{agent.score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto pr-1 sim-scroll">
            <div className="space-y-2">
              {agents.map((agent) => {
                const selected = selectedAgentId === agent.id;
                const latestTool = agent.toolCalls.length > 0 ? agent.toolCalls[agent.toolCalls.length - 1] : "No tool use yet";
                const preview = (agent.transcript || "Waiting for response...").replace(/\s+/g, " ").slice(0, 170);
                return (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => setSelectedAgentId(agent.id)}
                    className={`w-full rounded-xl border p-3 text-left transition ${selected ? "bg-card shadow-[0_0_0_1px_hsl(var(--primary)/0.25)]" : "bg-card/80 hover:border-primary/40 hover:bg-card"}`}
                    style={{ borderColor: selected ? agent.color : undefined }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="inline-flex items-center gap-2 text-sm font-semibold">
                        <PersonaAvatar personaId={agent.id} name={agent.name} size={18} />
                        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: agent.color }} />
                        {agent.name}
                      </p>
                      <Badge className={statusBadgeTone(agent.status)}>
                        {agent.status === "done" ? <CheckCircle2 className="mr-1 h-3 w-3" /> : null}
                        {humanStatus(agent.status)}
                      </Badge>
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground">Confidence {Math.round(agent.confidence * 100)}% | Score {agent.score.toFixed(2)}</p>
                    {agent.objective ? <p className="mt-1 text-[11px] text-muted-foreground">{agent.objective}</p> : null}
                    <p className="mt-2 rounded-md border border-border bg-background/80 px-2 py-1.5 text-[11px] text-muted-foreground">
                      Current move: {latestTool}
                    </p>
                    <p className="mt-2 rounded-md border border-border bg-background/80 px-2 py-1.5 text-xs text-foreground">
                      {preview}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      </div>

      {showResultCard && finalReport ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-card p-4 shadow-2xl sim-scroll">
            <div className="mb-2 flex items-start justify-between gap-2">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Simulation Result</p>
                <p className="text-lg font-semibold text-foreground">Observer Final Report</p>
              </div>
              <button
                type="button"
                className="rounded-md border border-border bg-background p-1 text-muted-foreground hover:text-foreground"
                onClick={() => setShowResultCard(false)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mb-3 flex items-center justify-between gap-2 rounded-xl border border-border bg-background/80 px-3 py-2">
              <p className="text-sm font-semibold text-foreground">{finalReport.summary}</p>
              <Badge className="border border-primary/40 bg-primary/10 text-foreground">
                Confidence {Math.round(finalReport.confidence * 100)}%
              </Badge>
            </div>

            {finalReport.recommendation ? (
              <div className="mb-3 rounded-xl border border-border bg-background/80 p-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Recommendation</p>
                <p className="mt-1 text-sm leading-relaxed text-foreground">{finalReport.recommendation}</p>
              </div>
            ) : null}

            {finalReport.key_turning_points.length > 0 ? (
              <div className="mb-3 rounded-xl border border-border bg-background/80 p-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Turning Points</p>
                <ul className="mt-2 space-y-1 text-xs text-foreground">
                  {finalReport.key_turning_points.slice(0, 8).map((point, idx) => (
                    <li key={`result-turn-${idx}`} className="rounded-md border border-border bg-card px-2 py-1.5">
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {finalReport.persona_observations && finalReport.persona_observations.length > 0 ? (
              <div className="mb-3 rounded-xl border border-border bg-background/80 p-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Persona Breakdown</p>
                <div className="mt-2 space-y-2">
                  {finalReport.persona_observations.slice(0, 10).map((persona) => (
                    <div key={`result-persona-${persona.persona_id}`} className="rounded-md border border-border bg-card px-2 py-2">
                      <p className="text-xs font-semibold text-foreground">
                        {persona.name} | {persona.role}
                      </p>
                      <p className="text-xs text-muted-foreground">{persona.objective}</p>
                      <p className="mt-1 text-xs text-foreground">{persona.stance}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {finalReport.html_slides ? (
              <Button variant="outline" className="h-8 px-2.5 text-xs" onClick={exportFinalHtml}>
                Export Final HTML Report
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {showInfoCard ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-border bg-card p-4 shadow-2xl">
            <div className="mb-3 flex items-start justify-between gap-2">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">How The Game Works</p>
                <p className="text-lg font-semibold text-foreground">Deep Simulation Rules</p>
              </div>
              <button
                type="button"
                className="rounded-md border border-border bg-background p-1 text-muted-foreground hover:text-foreground"
                onClick={() => setShowInfoCard(false)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="max-h-[65vh] space-y-3 overflow-y-auto rounded-xl border border-border bg-background/80 p-3 text-sm leading-relaxed text-foreground sim-scroll">
              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Objective</p>
                <p>
                  Run a multi-day strategy simulation to test a business decision under uncertainty. The goal is not to
                  "beat" a game board, but to learn which strategy mix improves `revenue`, `margin`, and `sentiment`
                  while controlling `churn_risk`.
                </p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Setup</p>
                <p>`1 tick = 1 day` in simulation time.</p>
                <p>You choose the number of ticks before start. More ticks = deeper scenario evolution.</p>
                <p>Personas are generated dynamically by the orchestrator, based on your query and scenario context.</p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Per-Tick Flow</p>
                <p>1. Active strategists are selected for the day.</p>
                <p>2. Each active strategist rolls and moves to a district tile.</p>
                <p>3. District effects apply pressure or boosts to KPI dimensions.</p>
                <p>4. Strategists think in real time, may call tools, and may submit action intents.</p>
                <p>5. Intents are validated and conflicts resolved; accepted intents change world KPIs.</p>
                <p>6. Crisis card may trigger and create external shock (mitigated by matching actions).</p>
                <p>7. Scores update from move quality, intent confidence, and KPI contribution.</p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">KPI Rules</p>
                <p><strong>Revenue</strong>: top-line impact from pricing, demand, and campaign effects.</p>
                <p><strong>Margin</strong>: unit-economics efficiency and cost discipline.</p>
                <p><strong>Brand Trust (Sentiment)</strong>: customer perception trajectory.</p>
                <p><strong>Churn Risk</strong>: likelihood of customer loss; lower is better.</p>
                <p>
                  Good runs usually raise `revenue/margin/sentiment` while keeping `churn_risk` flat or declining.
                </p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Action & Validation Rules</p>
                <p>Allowed intent categories include `move`, `price_adjust`, `spend_shift`, `campaign`, `procurement`, `wait`.</p>
                <p>Low-quality or invalid intents can be rejected by engine constraints.</p>
                <p>When multiple intents conflict, resolver keeps the strongest compatible set.</p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Crisis Rules</p>
                <p>Crisis cards represent exogenous market shocks (competitor move, supply issue, sentiment event).</p>
                <p>
                  If strategist intents include matching counter-actions, shock impact is partially mitigated;
                  otherwise KPI downside applies at near full force.
                </p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">How To Read The UI</p>
                <p><strong>Left panel</strong>: controls, KPI snapshots, score trends.</p>
                <p><strong>Center panel</strong>: board state + selected strategist live transcript and tool calls.</p>
                <p><strong>Right panel</strong>: all strategist cards with confidence, score, current move, preview.</p>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">End Of Simulation</p>
                <p>
                  When the final tick completes, `Result` unlocks. Open it to view observer summary, turning points,
                  per-persona observations, and recommendation.
                </p>
                <p>Use export to download the final HTML slides report for presentation/replay.</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
