export interface DataItem {
  source: string;
  label: string;
  value: string;
  trend: "up" | "down" | "flat";
}

export interface AgentInsight {
  name: string;
  emoji: string;
  insight: string;
}

export interface SubagentView {
  stance: "conservative" | "aggressive";
  recommendation: string;
  reasoning: string;
}

export interface Decision {
  verdict: string;
  reasoning: string;
  risk: "Low" | "Medium" | "High";
  confidence: number;
}

export interface AnalysisResult {
  data: DataItem[];
  agents: AgentInsight[];
  subagents: SubagentView[];
  decision: Decision;
}

const fireEmployeeResult: AnalysisResult = {
  data: [
    { source: "HR", label: "Performance trending down 6 mo.", value: "Score 2.1 / 5", trend: "down" },
    { source: "Sales", label: "Revenue contribution this Q", value: "RM 12,400", trend: "down" },
    { source: "Legal", label: "Severance & compliance cost", value: "RM 20,000", trend: "flat" },
  ],
  agents: [
    { name: "HR Agent", emoji: "👤", insight: "Employee underperforming for two consecutive review cycles. PIP not completed." },
    { name: "Sales Agent", emoji: "📉", insight: "Revenue contribution is in the bottom 8% of the team. Pipeline thin." },
    { name: "Legal Agent", emoji: "⚖️", insight: "Termination permitted with documented cause. Severance ~RM 20k required." },
  ],
  subagents: [
    {
      stance: "conservative",
      recommendation: "Do not fire — coach first",
      reasoning: "Short-term replacement cost (RM 45k+) and onboarding risk outweigh the savings. Try a 60-day PIP.",
    },
    {
      stance: "aggressive",
      recommendation: "Fire — performance issue",
      reasoning: "Sustained underperformance hurts team morale and revenue. Cut losses now and backfill from active pipeline.",
    },
  ],
  decision: {
    verdict: "DO NOT FIRE — Initiate 60-day PIP",
    reasoning:
      "Short-term termination cost (RM 65k including replacement & ramp) outweighs near-term benefit. A structured Performance Improvement Plan preserves optionality with measurable exit criteria.",
    risk: "Medium",
    confidence: 78,
  },
};

const acquireResult: AnalysisResult = {
  data: [
    { source: "Finance", label: "Acquisition price", value: "RM 4.2M", trend: "flat" },
    { source: "Market", label: "BetaCorp YoY growth", value: "+34%", trend: "up" },
    { source: "Legal", label: "Antitrust risk", value: "Low", trend: "flat" },
  ],
  agents: [
    { name: "Finance Agent", emoji: "💰", insight: "Cash reserves cover the deal at 1.8x EBITDA — within healthy range." },
    { name: "Strategy Agent", emoji: "♟️", insight: "Eliminates a fast-growing competitor and adds 22% market share." },
    { name: "Legal Agent", emoji: "⚖️", insight: "No regulatory blockers. Standard reps & warranties expected." },
  ],
  subagents: [
    {
      stance: "conservative",
      recommendation: "Negotiate down to RM 3.5M",
      reasoning: "Pay a fair multiple. Walk away if seller refuses — organic growth is a viable alternative.",
    },
    {
      stance: "aggressive",
      recommendation: "Acquire immediately at full price",
      reasoning: "Speed wins. Closing fast prevents a competing bid and locks in market consolidation.",
    },
  ],
  decision: {
    verdict: "ACQUIRE — Counter at RM 3.8M",
    reasoning:
      "Strategic upside is significant and financing is available, but a 10% price reduction protects margin. Strong walk-away position keeps leverage.",
    risk: "Medium",
    confidence: 84,
  },
};

const expansionResult: AnalysisResult = {
  data: [
    { source: "Market", label: "TAM in Singapore", value: "USD 180M", trend: "up" },
    { source: "Ops", label: "Setup cost (yr 1)", value: "RM 1.8M", trend: "flat" },
    { source: "Legal", label: "Regulatory complexity", value: "Moderate", trend: "flat" },
  ],
  agents: [
    { name: "Market Agent", emoji: "🌏", insight: "Demand signals strong; 3 enterprise leads already inbound from SG." },
    { name: "Ops Agent", emoji: "⚙️", insight: "Hiring market is competitive but feasible. Need a country lead first." },
    { name: "Legal Agent", emoji: "⚖️", insight: "Pte Ltd entity required. Data residency rules manageable." },
  ],
  subagents: [
    {
      stance: "conservative",
      recommendation: "Start with a remote sales pod",
      reasoning: "Validate demand for 6 months before opening an office. Limits downside to ~RM 400k.",
    },
    {
      stance: "aggressive",
      recommendation: "Launch full office in Q1",
      reasoning: "First-mover advantage in a hot market. Inbound leads suggest product-market fit already exists.",
    },
  ],
  decision: {
    verdict: "EXPAND — Phased entry, sales pod first",
    reasoning:
      "Inbound demand is real but unproven at scale. A 6-month remote pod de-risks the move while preserving a fast path to a full office if KPIs hit.",
    risk: "Low",
    confidence: 82,
  },
};

export function analyze(query: string): AnalysisResult {
  const q = query.toLowerCase();
  if (q.includes("acqui") || q.includes("buy") || q.includes("merger")) return acquireResult;
  if (q.includes("expand") || q.includes("market") || q.includes("launch")) return expansionResult;
  return fireEmployeeResult;
}
