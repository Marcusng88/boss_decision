import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent, type WheelEvent } from "react";
import {
  AlertTriangle,
  Bot,
  ChartLine,
  Compass,
  MessageSquareText,
  Network,
  Pause,
  Play,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { chatNetworkObserver, injectNetworkShock, streamNetworkSimulator, type NetworkSimulatorStreamEvent } from "@/lib/simulator-client";

type NodeType = "business" | "consumer" | "supplier" | "competitor" | "community" | "bank" | "regulator" | "platform";
type EdgeType = "transaction" | "influence" | "trust" | "dependency" | "information";
type NodeStatus = "stable" | "active" | "strained" | "watch";

interface NetworkNode {
  id: string;
  label: string;
  type: NodeType;
  buildingIcon: string;
  personaIcon: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  influence: number;
  status: NodeStatus;
  lastAction: string;
}

interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  weight: number;
  lastTick: number;
}

interface SessionEvent {
  id: string;
  day: number;
  source: string;
  kind: "action" | "message" | "shock" | "observer";
  summary: string;
}

interface ChatMessage {
  role: "user" | "observer";
  text: string;
}

interface NetworkKpis {
  revenue_delta: number;
  cost_delta: number;
  risk_delta: number;
}

const NODE_TYPE_STYLE: Record<NodeType, { color: string; ring: string }> = {
  business: { color: "#e9772e", ring: "rgba(233,119,46,0.35)" },
  consumer: { color: "#2f7f73", ring: "rgba(47,127,115,0.35)" },
  supplier: { color: "#5f7d36", ring: "rgba(95,125,54,0.35)" },
  competitor: { color: "#bd4a2d", ring: "rgba(189,74,45,0.35)" },
  community: { color: "#577ea4", ring: "rgba(87,126,164,0.35)" },
  bank: { color: "#7d5aa7", ring: "rgba(125,90,167,0.35)" },
  regulator: { color: "#5b6775", ring: "rgba(91,103,117,0.35)" },
  platform: { color: "#7f6d42", ring: "rgba(127,109,66,0.35)" },
};

const EDGE_COLORS: Record<EdgeType, string> = {
  transaction: "#e08a3e",
  influence: "#4f8ec2",
  trust: "#2c9a7c",
  dependency: "#a06acc",
  information: "#c2a84f",
};

const SHOCK_CATALOG = [
  "Competitor launched emergency discount campaign",
  "Supplier lead time slipped by 2 days",
  "Community sentiment dipped after price rumor",
  "Regulator announced temporary promotion guideline review",
];

const INITIAL_QUERY = "Can I increase my price by 10% without damaging retention?";
const DEFAULT_DAYS = 16;
const BUILDING_ICON_COUNT = 60;
const PERSONA_ICON_COUNT = 49;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function randomPick<T>(rows: T[]): T {
  return rows[Math.floor(Math.random() * rows.length)];
}

function stableHash(value: string): number {
  let hash = 0;
  for (let idx = 0; idx < value.length; idx += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(idx);
    hash |= 0;
  }
  return Math.abs(hash);
}

function buildingIconPath(index: number): string {
  return `/assets/buildings/building_${String(index + 1).padStart(2, "0")}.png`;
}

function personaIconPath(index: number): string {
  return `/assets/personas/persona_${String(index + 1).padStart(2, "0")}.png`;
}

function pickNodeIcons(nodeId: string, type: NodeType): { buildingIcon: string; personaIcon: string } {
  const typeSeed = stableHash(type);
  const nodeSeed = stableHash(nodeId);
  const buildingIndex = (typeSeed + nodeSeed) % BUILDING_ICON_COUNT;
  const personaIndex = nodeSeed % PERSONA_ICON_COUNT;
  return {
    buildingIcon: buildingIconPath(buildingIndex),
    personaIcon: personaIconPath(personaIndex),
  };
}

function asNodeType(value: string): NodeType {
  if (value in NODE_TYPE_STYLE) return value as NodeType;
  return "business";
}

function asEdgeType(value: string): EdgeType {
  if (value in EDGE_COLORS) return value as EdgeType;
  return "information";
}

function asNodeStatus(value: string): NodeStatus {
  if (value === "stable" || value === "active" || value === "strained" || value === "watch") return value;
  return "stable";
}

function buildInitialNodes(): NetworkNode[] {
  const definitions: Array<[string, string, NodeType]> = [
    ["n_business_hq", "SME HQ", "business"],
    ["n_consumer_stu", "Student Cluster", "consumer"],
    ["n_consumer_young", "Young Professional", "consumer"],
    ["n_supplier_mat", "Raw Supplier", "supplier"],
    ["n_supplier_log", "Logistics Vendor", "supplier"],
    ["n_comp_fast", "Fast Competitor", "competitor"],
    ["n_comp_prem", "Premium Competitor", "competitor"],
    ["n_bank_local", "Local Bank", "bank"],
    ["n_reg_trade", "Trade Regulator", "regulator"],
    ["n_community_campus", "Campus Community", "community"],
    ["n_platform_social", "Social Platform", "platform"],
    ["n_platform_market", "Marketplace", "platform"],
  ];

  const centerX = 420;
  const centerY = 270;
  const radius = 195;

  return definitions.map(([id, label, type], idx) => {
    const icons = pickNodeIcons(id, type);
    const angle = (idx / definitions.length) * Math.PI * 2;
    const jitterX = (Math.random() - 0.5) * 42;
    const jitterY = (Math.random() - 0.5) * 42;
    return {
      id,
      label,
      type,
      ...icons,
      x: centerX + Math.cos(angle) * radius + jitterX,
      y: centerY + Math.sin(angle) * radius + jitterY,
      vx: 0,
      vy: 0,
      influence: 0.45 + Math.random() * 0.4,
      status: "stable",
      lastAction: "waiting for scenario run",
    };
  });
}

function buildInitialEdges(): NetworkEdge[] {
  const rows: Array<[string, string, EdgeType, number]> = [
    ["n_business_hq", "n_consumer_stu", "transaction", 0.82],
    ["n_business_hq", "n_consumer_young", "transaction", 0.68],
    ["n_business_hq", "n_supplier_mat", "dependency", 0.73],
    ["n_business_hq", "n_supplier_log", "dependency", 0.66],
    ["n_business_hq", "n_platform_market", "transaction", 0.57],
    ["n_business_hq", "n_platform_social", "information", 0.52],
    ["n_comp_fast", "n_consumer_stu", "influence", 0.61],
    ["n_comp_prem", "n_consumer_young", "influence", 0.58],
    ["n_community_campus", "n_consumer_stu", "trust", 0.69],
    ["n_reg_trade", "n_business_hq", "information", 0.51],
    ["n_bank_local", "n_business_hq", "dependency", 0.46],
    ["n_platform_social", "n_community_campus", "information", 0.48],
    ["n_platform_market", "n_comp_fast", "transaction", 0.54],
  ];

  return rows.map(([source, target, type, weight], idx) => ({
    id: `edge_${idx + 1}`,
    source,
    target,
    type,
    weight,
    lastTick: 0,
  }));
}

function nodeById(nodes: NetworkNode[], id: string): NetworkNode | undefined {
  return nodes.find((item) => item.id === id);
}

function formatNodeType(type: NodeType): string {
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function NetworkSimulationSection() {
  const [query, setQuery] = useState(INITIAL_QUERY);
  const [maxDays, setMaxDays] = useState(DEFAULT_DAYS);
  const [currentDay, setCurrentDay] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<NetworkNode[]>(() => buildInitialNodes());
  const [edges, setEdges] = useState<NetworkEdge[]>(() => buildInitialEdges());
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState("n_business_hq");
  const [observerReport, setObserverReport] = useState("");
  const [observerReady, setObserverReady] = useState(false);
  const [kpis, setKpis] = useState<NetworkKpis>({ revenue_delta: 0, cost_delta: 0, risk_delta: 0 });
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const canvasRef = useRef<HTMLDivElement | null>(null);
  const streamAbortRef = useRef<AbortController | null>(null);
  const dragCanvasRef = useRef<{ active: boolean; startX: number; startY: number }>({
    active: false,
    startX: 0,
    startY: 0,
  });
  const dragNodeRef = useRef<{ nodeId: string; pointerId: number } | null>(null);

  const selectedNode = useMemo(
    () => nodeById(nodes, selectedNodeId) ?? nodes[0],
    [nodes, selectedNodeId],
  );

  const outgoingEdges = useMemo(
    () => edges.filter((edge) => edge.source === selectedNode?.id || edge.target === selectedNode?.id),
    [edges, selectedNode?.id],
  );

  useEffect(() => {
    return () => {
      streamAbortRef.current?.abort();
    };
  }, []);

  function appendSessionEvent(event: SessionEvent) {
    setEvents((prev) => [event, ...prev].slice(0, 220));
  }

  function applyStreamEvent(event: NetworkSimulatorStreamEvent) {
    if (event.session_id) setSessionId(event.session_id);
    if (event.type === "status") {
      const message = typeof event.message === "string" ? event.message : "status";
      appendSessionEvent({
        id: `status_${Math.random().toString(36).slice(2, 8)}`,
        day: currentDay,
        source: "System",
        kind: "message",
        summary: message,
      });
      return;
    }

    if (event.type === "progress") {
      setCurrentDay(event.tick ?? 0);
      return;
    }

    if (event.type === "network_state") {
      const state = event.state as {
        nodes?: Array<Record<string, unknown>>;
        edges?: Array<Record<string, unknown>>;
        kpis?: { revenue_delta?: number; cost_delta?: number; risk_delta?: number };
      } | undefined;

      if (state?.nodes) {
        setNodes(
          state.nodes.map((node) => {
            const id = String(node.node_id ?? "");
            const type = asNodeType(String(node.node_type ?? "business"));
            return {
              id,
              label: String(node.label ?? node.node_id ?? "Node"),
              type,
              ...pickNodeIcons(id, type),
              x: Number(node.x ?? 120),
              y: Number(node.y ?? 120),
              vx: 0,
              vy: 0,
              influence: Number(node.influence ?? 0.5),
              status: asNodeStatus(String(node.status ?? "stable")),
              lastAction: "awaiting action",
            };
          }),
        );
      }
      if (state?.edges) {
        setEdges(
          state.edges.map((edge) => ({
            id: String(edge.edge_id ?? ""),
            source: String(edge.source ?? ""),
            target: String(edge.target ?? ""),
            type: asEdgeType(String(edge.edge_type ?? "information")),
            weight: Number(edge.weight ?? 0.5),
            lastTick: event.tick ?? 0,
          })),
        );
      }
      if (state?.kpis) {
        setKpis({
          revenue_delta: Number(state.kpis.revenue_delta ?? 0),
          cost_delta: Number(state.kpis.cost_delta ?? 0),
          risk_delta: Number(state.kpis.risk_delta ?? 0),
        });
      }
      return;
    }

    if (event.type === "node_action") {
      const action = event.action as { source_node_id?: string; action_type?: string; rationale?: string } | undefined;
      const sourceId = String(action?.source_node_id ?? "unknown");
      const actionLabel = String(action?.action_type ?? "action");
      const rationale = String(action?.rationale ?? "");
      appendSessionEvent({
        id: `evt_${event.tick ?? 0}_${Math.random().toString(36).slice(2, 8)}`,
        day: event.tick ?? 0,
        source: sourceId,
        kind: "action",
        summary: `${actionLabel}${rationale ? `: ${rationale}` : ""}`,
      });
      setNodes((prev) =>
        prev.map((node) =>
          node.id === sourceId
            ? { ...node, lastAction: actionLabel, status: "active" }
            : node,
        ),
      );
      return;
    }

    if (event.type === "node_message") {
      const message = event.message as { node_id?: string; text?: string } | undefined;
      appendSessionEvent({
        id: `msg_${event.tick ?? 0}_${Math.random().toString(36).slice(2, 8)}`,
        day: event.tick ?? 0,
        source: String(message?.node_id ?? "node"),
        kind: "message",
        summary: String(message?.text ?? "node message"),
      });
      return;
    }

    if (event.type === "edge_update") {
      const edge = event.edge as { edge_id?: string; weight?: number } | undefined;
      const edgeId = String(edge?.edge_id ?? "");
      setEdges((prev) =>
        prev.map((item) =>
          item.id === edgeId
            ? { ...item, weight: Number(edge?.weight ?? item.weight), lastTick: event.tick ?? item.lastTick }
            : item,
        ),
      );
      return;
    }

    if (event.type === "shock_event") {
      const shock = event.shock as { summary?: string } | undefined;
      appendSessionEvent({
        id: `shock_${event.tick ?? 0}_${Math.random().toString(36).slice(2, 8)}`,
        day: event.tick ?? 0,
        source: "User",
        kind: "shock",
        summary: String(shock?.summary ?? "Shock injected"),
      });
      return;
    }

    if (event.type === "observer_summary") {
      setObserverReport(event.summary ?? "Observer summary unavailable.");
      setObserverReady(true);
      appendSessionEvent({
        id: `obs_${Math.random().toString(36).slice(2, 8)}`,
        day: currentDay,
        source: "Observer",
        kind: "observer",
        summary: event.summary ?? "Observer summary",
      });
      return;
    }

    if (event.type === "error") {
      setStreamError(event.error ?? "Stream error");
      setIsRunning(false);
      return;
    }

    if (event.type === "done") {
      setIsRunning(false);
    }
  }

  function resetSimulation() {
    streamAbortRef.current?.abort();
    setIsRunning(false);
    setSessionId(null);
    setStreamError(null);
    setCurrentDay(0);
    setNodes(buildInitialNodes());
    setEdges(buildInitialEdges());
    setEvents([]);
    setObserverReady(false);
    setObserverReport("");
    setKpis({ revenue_delta: 0, cost_delta: 0, risk_delta: 0 });
    setChatMessages([]);
  }

  function startSimulation() {
    resetSimulation();
    setStreamError(null);
    setIsRunning(true);
    const controller = new AbortController();
    streamAbortRef.current = controller;

    void streamNetworkSimulator(
      {
        query,
        max_ticks: maxDays,
        seed: 7,
        min_nodes: 15,
        max_nodes: 30,
        scenario_id: "business_network_v1",
      },
      {
        signal: controller.signal,
        onEvent: (event) => applyStreamEvent(event),
      },
    )
      .catch((error: unknown) => {
        const message =
          error instanceof Error ? error.message : "Failed to start network simulation stream.";
        setStreamError(message);
        setIsRunning(false);
      })
      .finally(() => {
        setIsRunning(false);
      });
  }

  function stopSimulation() {
    streamAbortRef.current?.abort();
    setIsRunning(false);
  }

  async function injectShock() {
    if (!sessionId) return;
    const shock = randomPick(SHOCK_CATALOG);
    try {
      await injectNetworkShock(sessionId, {
        shock_type: "market_disruption",
        summary: shock,
        severity: 0.6,
        targets: [],
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to inject shock.";
      setStreamError(message);
    }
  }

  async function sendObserverMessage() {
    const text = chatInput.trim();
    if (!text || !observerReady || !sessionId) return;
    setChatMessages((prev) => [...prev, { role: "user", text }]);
    setChatInput("");
    try {
      const response = await chatNetworkObserver(sessionId, text);
      setChatMessages((prev) => [...prev, { role: "observer", text: response.answer }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Observer chat failed.";
      setChatMessages((prev) => [...prev, { role: "observer", text: message }]);
    }
  }

  function handleWheel(event: WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const direction = event.deltaY > 0 ? -0.08 : 0.08;
    setZoom((prev) => clamp(prev + direction, 0.55, 1.85));
  }

  function handleCanvasPointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (dragNodeRef.current) return;
    dragCanvasRef.current = {
      active: true,
      startX: event.clientX - offset.x,
      startY: event.clientY - offset.y,
    };
  }

  function handleCanvasPointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragCanvasRef.current.active) return;
    setOffset({
      x: event.clientX - dragCanvasRef.current.startX,
      y: event.clientY - dragCanvasRef.current.startY,
    });
  }

  function handleCanvasPointerUp() {
    dragCanvasRef.current.active = false;
  }

  function handleNodePointerDown(event: ReactPointerEvent<SVGElement>, nodeId: string) {
    event.stopPropagation();
    dragNodeRef.current = { nodeId, pointerId: event.pointerId };
    setSelectedNodeId(nodeId);
  }

  function handleSvgPointerMove(event: ReactPointerEvent<SVGSVGElement>) {
    const drag = dragNodeRef.current;
    if (!drag) return;
    const svgRect = event.currentTarget.getBoundingClientRect();
    const rawX = (event.clientX - svgRect.left - offset.x) / zoom;
    const rawY = (event.clientY - svgRect.top - offset.y) / zoom;
    setNodes((prev) =>
      prev.map((node) =>
        node.id === drag.nodeId
          ? { ...node, x: clamp(rawX, 40, 800), y: clamp(rawY, 30, 520), vx: 0, vy: 0 }
          : node,
      ),
    );
  }

  function handleSvgPointerUp(event: ReactPointerEvent<SVGSVGElement>) {
    const drag = dragNodeRef.current;
    if (drag && drag.pointerId === event.pointerId) {
      dragNodeRef.current = null;
    }
  }

  return (
    <section className="grid gap-4 px-4 py-5 lg:grid-cols-[300px_1fr_360px]">
      <aside className="space-y-4 rounded-3xl border border-border bg-card/75 p-4 shadow-card">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Scenario Input</p>
          <h2 className='mt-1 text-2xl text-foreground [font-family:"Iowan_Old_Style",Georgia,serif]'>Network Command Desk</h2>
        </div>
        <div className="space-y-3">
          <label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Decision Scenario</label>
          <Input value={query} onChange={(event) => setQuery(event.target.value)} />
          <label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Days</label>
          <Input
            type="number"
            min={1}
            max={90}
            value={maxDays}
            onChange={(event) => setMaxDays(clamp(Number(event.target.value || DEFAULT_DAYS), 1, 90))}
          />
        </div>

        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
          <Button className="h-10" onClick={() => startSimulation()}>
            <Play className="mr-2 h-4 w-4" />
            Run Simulation
          </Button>
          <Button variant="outline" className="h-10" onClick={() => (isRunning ? stopSimulation() : startSimulation())}>
            {isRunning ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
            {isRunning ? "Stop" : "Run Again"}
          </Button>
          <Button variant="outline" className="h-10" onClick={injectShock} disabled={!sessionId || !isRunning}>
            <Plus className="mr-2 h-4 w-4" />
            Inject Shock
          </Button>
          <Button variant="ghost" className="h-10" onClick={resetSimulation}>
            Reset
          </Button>
        </div>

        <div className="rounded-2xl border border-border bg-background/70 p-3">
          <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Session State</p>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Session</span>
            <span className="font-semibold text-foreground">{sessionId ? sessionId.slice(-8) : "-"}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Current day</span>
            <span className="font-semibold text-foreground">{currentDay}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Nodes</span>
            <span className="font-semibold text-foreground">{nodes.length}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Edges</span>
            <span className="font-semibold text-foreground">{edges.length}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Events</span>
            <span className="font-semibold text-foreground">{events.length}</span>
          </div>
        </div>

        {streamError && (
          <div className="rounded-xl border border-warning/40 bg-warning/10 p-2 text-xs text-foreground">
            <p className="font-semibold">Stream Error</p>
            <p className="mt-1 text-muted-foreground">{streamError}</p>
          </div>
        )}

        <div className="rounded-2xl border border-border bg-background/70 p-3">
          <p className="mb-2 text-xs uppercase tracking-[0.16em] text-muted-foreground">Recent Events</p>
          <ScrollArea className="h-44">
            <div className="space-y-2">
              {events.slice(0, 20).map((event) => (
                <div key={event.id} className="rounded-xl border border-border/70 bg-card/70 p-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">D{event.day}</span>
                    <Badge variant="outline" className="text-[10px] uppercase">{event.kind}</Badge>
                  </div>
                  <p className="mt-1 text-muted-foreground">{event.source}</p>
                  <p className="text-foreground">{event.summary}</p>
                </div>
              ))}
              {events.length === 0 && <p className="text-xs text-muted-foreground">No events yet. Run simulation to stream timeline.</p>}
            </div>
          </ScrollArea>
        </div>
      </aside>

      <div className="rounded-3xl border border-border bg-card/80 p-3 shadow-card">
        <div className="mb-2 flex items-center justify-between px-2">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Live Graph</p>
            <p className='text-lg text-foreground [font-family:"Iowan_Old_Style",Georgia,serif]'>Economic Relationship Network</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-primary/15 text-primary hover:bg-primary/15">
              <Network className="mr-1 h-3 w-3" />
              Interactive
            </Badge>
            <Badge variant="outline">
              <Compass className="mr-1 h-3 w-3" />
              Zoom {zoom.toFixed(2)}x
            </Badge>
          </div>
        </div>
        <div
          ref={canvasRef}
          className="relative h-[560px] overflow-hidden rounded-2xl border border-border/80 bg-[radial-gradient(circle_at_12%_18%,rgba(233,119,46,0.12),transparent_34%),radial-gradient(circle_at_84%_76%,rgba(60,131,123,0.15),transparent_38%),linear-gradient(180deg,rgba(250,246,239,0.95),rgba(241,235,224,0.94))]"
          onWheel={handleWheel}
          onPointerDown={handleCanvasPointerDown}
          onPointerMove={handleCanvasPointerMove}
          onPointerUp={handleCanvasPointerUp}
          onPointerLeave={handleCanvasPointerUp}
        >
          <svg className="h-full w-full touch-none" onPointerMove={handleSvgPointerMove} onPointerUp={handleSvgPointerUp}>
            <g transform={`translate(${offset.x}, ${offset.y}) scale(${zoom})`}>
              {edges.map((edge) => {
                const source = nodeById(nodes, edge.source);
                const target = nodeById(nodes, edge.target);
                if (!source || !target) return null;
                const isSelected =
                  selectedNode?.id === source.id || selectedNode?.id === target.id;
                return (
                  <line
                    key={edge.id}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke={EDGE_COLORS[edge.type]}
                    strokeOpacity={isSelected ? 0.85 : 0.46}
                    strokeWidth={1.2 + edge.weight * (isSelected ? 3 : 2)}
                    strokeDasharray={edge.type === "information" ? "5 5" : edge.type === "influence" ? "2 6" : ""}
                  />
                );
              })}

              {nodes.map((node) => {
                const style = NODE_TYPE_STYLE[node.type];
                const isSelected = selectedNode?.id === node.id;
                const radius = isSelected ? 31 : 25 + node.influence * 5;
                const iconSize = isSelected ? 52 : 44;
                const personaSize = isSelected ? 22 : 18;
                return (
                  <g key={node.id} onClick={() => setSelectedNodeId(node.id)}>
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={radius + 7}
                      fill={style.ring}
                      opacity={isSelected ? 0.8 : 0.5}
                      pointerEvents="none"
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={radius}
                      fill={style.color}
                      stroke={isSelected ? "#111827" : "rgba(17,24,39,0.4)"}
                      strokeWidth={isSelected ? 2.4 : 1.1}
                      opacity={0.35}
                    />
                    <image
                      href={node.buildingIcon}
                      x={node.x - iconSize / 2}
                      y={node.y - iconSize / 2}
                      width={iconSize}
                      height={iconSize}
                      style={{ imageRendering: "pixelated", pointerEvents: "none" }}
                    />
                    <image
                      href={node.personaIcon}
                      x={node.x + iconSize / 2 - personaSize}
                      y={node.y - iconSize / 2 - personaSize * 0.25}
                      width={personaSize}
                      height={personaSize}
                      style={{ imageRendering: "pixelated", pointerEvents: "none" }}
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={radius}
                      fill="transparent"
                      stroke="transparent"
                      onPointerDown={(event) => handleNodePointerDown(event, node.id)}
                      style={{ cursor: "grab" }}
                    />
                    <text
                      x={node.x}
                      y={node.y + radius + 14}
                      textAnchor="middle"
                      fontSize={11}
                      fill="rgba(17,24,39,0.84)"
                      style={{ userSelect: "none" }}
                    >
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>
      </div>

      <aside className="space-y-4 rounded-3xl border border-border bg-card/75 p-4 shadow-card">
        <div className="rounded-2xl border border-border bg-background/80 p-3">
          <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Node Inspector</p>
          {selectedNode && (
            <div className="mt-2 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-lg text-foreground">{selectedNode.label}</h3>
                <Badge variant="outline">{formatNodeType(selectedNode.type)}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-muted text-foreground hover:bg-muted">{selectedNode.status}</Badge>
                <span className="text-xs text-muted-foreground">Influence {(selectedNode.influence * 100).toFixed(0)}%</span>
              </div>
              <p className="rounded-xl border border-border/80 bg-card/70 p-2 text-xs text-foreground">{selectedNode.lastAction}</p>
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Connected edges</p>
              <ScrollArea className="h-28 rounded-xl border border-border/70 bg-card/60 p-2">
                <div className="space-y-2">
                  {outgoingEdges.map((edge) => (
                    <div key={edge.id} className="rounded-lg border border-border/70 bg-background/80 p-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">{edge.type}</span>
                        <span className="text-muted-foreground">w={edge.weight.toFixed(2)}</span>
                      </div>
                      <p className="text-muted-foreground">{edge.source} {"->"} {edge.target}</p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-border bg-background/80 p-3">
          <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Final Observer Summary</p>
          <div className="mt-2 rounded-xl border border-border/70 bg-card/70 p-3 text-sm text-foreground">
            {!observerReady && (
              <p className="flex items-center gap-2 text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                Report will appear after simulation completes.
              </p>
            )}
            {observerReady && <p>{observerReport}</p>}
          </div>
          <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
            <div className="rounded-lg border border-border/70 bg-card/60 p-2">
              <p className="text-muted-foreground">Revenue</p>
              <p className="font-semibold text-foreground">{(kpis.revenue_delta * 100).toFixed(2)}%</p>
            </div>
            <div className="rounded-lg border border-border/70 bg-card/60 p-2">
              <p className="text-muted-foreground">Cost</p>
              <p className="font-semibold text-foreground">{(kpis.cost_delta * 100).toFixed(2)}%</p>
            </div>
            <div className="rounded-lg border border-border/70 bg-card/60 p-2">
              <p className="text-muted-foreground">Risk</p>
              <p className="font-semibold text-foreground">{(kpis.risk_delta * 100).toFixed(2)}%</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-background/80 p-3">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Observer Chat</p>
            <Badge variant={observerReady ? "default" : "outline"} className="text-[10px]">
              {observerReady ? "Ready" : "Locked"}
            </Badge>
          </div>
          <ScrollArea className="mt-2 h-36 rounded-xl border border-border/70 bg-card/70 p-2">
            <div className="space-y-2">
              {chatMessages.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  Chat unlocks after simulation. Questions will be grounded to this session timeline.
                </p>
              )}
              {chatMessages.map((message, idx) => (
                <div
                  key={`${message.role}-${idx}`}
                  className={`rounded-lg px-2 py-1.5 text-xs ${
                    message.role === "observer"
                      ? "border border-primary/30 bg-primary/10 text-foreground"
                      : "border border-border/70 bg-background text-foreground"
                  }`}
                >
                  <p className="mb-1 font-semibold uppercase tracking-[0.12em] text-muted-foreground">{message.role}</p>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
          <div className="mt-2 flex gap-2">
            <Input
              placeholder="Ask observer after run..."
              value={chatInput}
              disabled={!observerReady}
              onChange={(event) => setChatInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") sendObserverMessage();
              }}
            />
            <Button size="icon" disabled={!observerReady || !chatInput.trim()} onClick={sendObserverMessage}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="rounded-lg border border-border bg-card/70 p-2 text-center">
            <ChartLine className="mx-auto h-4 w-4 text-primary" />
            <p className="mt-1 text-muted-foreground">Metric Deltas</p>
          </div>
          <div className="rounded-lg border border-border bg-card/70 p-2 text-center">
            <MessageSquareText className="mx-auto h-4 w-4 text-primary" />
            <p className="mt-1 text-muted-foreground">Node Dialog</p>
          </div>
          <div className="rounded-lg border border-border bg-card/70 p-2 text-center">
            <Bot className="mx-auto h-4 w-4 text-primary" />
            <p className="mt-1 text-muted-foreground">Observer Agent</p>
          </div>
        </div>
        <div className="rounded-xl border border-warning/40 bg-warning/10 p-2 text-xs text-foreground">
          <p className="inline-flex items-center gap-1 font-semibold">
            <AlertTriangle className="h-3 w-3" />
            Backend stream mode
          </p>
          <p className="mt-1 text-muted-foreground">
            Graph updates now come from `/api/network-simulator/stream` and session shock/chat endpoints.
          </p>
        </div>
        <div className="rounded-xl border border-success/40 bg-success/10 p-2 text-xs text-foreground">
          <p className="inline-flex items-center gap-1 font-semibold">
            <ShieldCheck className="h-3 w-3" />
            2D board untouched
          </p>
          <p className="mt-1 text-muted-foreground">Current deep 2D arena remains available in its original tab.</p>
        </div>
      </aside>
    </section>
  );
}
