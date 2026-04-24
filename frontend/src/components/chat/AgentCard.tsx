
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { AgentInsightData } from "@/lib/api";
import { AgentAvatar, AGENT_COLORS } from "./AgentAvatar";

const TrendIcon = ({ trend }: { trend: string }) => {
  if (trend === "up") return <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />;
  if (trend === "down") return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
  return <Minus className="w-3.5 h-3.5 text-gray-400" />;
};

interface AgentCardProps {
  insight: AgentInsightData;
  style?: React.CSSProperties;
  isActive?: boolean;
}

export const AgentCard = ({ insight, style, isActive }: AgentCardProps) => {
  const key = insight.agent_name.toLowerCase().replace(/\s+/g, "_");
  const colors = AGENT_COLORS[key] || AGENT_COLORS.hr;
  const pct = Math.round(insight.confidence * 100);

  return (
    <div
      className="rounded-2xl overflow-hidden shadow-md border border-white/60 animate-fade-in-up bg-white"
      style={style}
    >
      {/* Gradient header with cartoon avatar */}
      <div className={`relative bg-gradient-to-br ${colors.gradient} p-4 flex items-start gap-3`}>
        {/* Avatar */}
        <div className="relative shrink-0 drop-shadow-lg" style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.25))" }}>
          <AgentAvatar agentName={key} size={56} />
          {isActive && (
            <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-yellow-300 border-2 border-white animate-pulse" />
          )}
        </div>

        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <h3 className="text-white font-bold text-sm leading-tight">
            {insight.agent_name} Agent
          </h3>
          <p className="text-white/75 text-xs leading-snug line-clamp-2">
            {insight.data_summary || "Analyzing data..."}
          </p>
          {insight.metric_value && (
            <div className="inline-flex self-start items-center gap-1 bg-white/20 backdrop-blur-sm rounded-xl px-2.5 py-1">
              <TrendIcon trend={insight.trend} />
              <span className="text-white font-bold text-xs leading-tight">{insight.metric_value}</span>
            </div>
          )}
        </div>
      </div>

      {/* Card body */}
      <div className="p-4 space-y-3">
        {/* Findings */}
        <div className="space-y-1.5">
          {insight.findings.slice(0, 3).map((f, i) => (
            <p key={i} className="text-xs text-gray-700 flex gap-2">
              <span className={`${colors.text} font-bold mt-0.5 shrink-0`}>•</span>
              <span className="leading-relaxed">{f}</span>
            </p>
          ))}
        </div>

        {/* Recommendation */}
        <div className={`rounded-xl ${colors.light} border px-3 py-2`}>
          <p className={`text-xs font-semibold ${colors.text} italic leading-snug`}>
            "{insight.recommendation}"
          </p>
        </div>

        {/* Confidence bar */}
        <div className="space-y-1">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">Confidence</span>
            <span className={`text-xs font-bold ${colors.text}`}>{pct}%</span>
          </div>
          <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${colors.gradient} transition-all duration-700`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Skeleton card shown while an agent is running
export const AgentCardSkeleton = ({ agentName }: { agentName: string }) => {
  const key = agentName.toLowerCase().replace(/\s+/g, "_");
  const colors = AGENT_COLORS[key] || AGENT_COLORS.hr;

  return (
    <div className="rounded-2xl overflow-hidden shadow-md border border-white/60 bg-white animate-pulse">
      <div className={`relative bg-gradient-to-br ${colors.gradient} p-4 flex items-center gap-3 opacity-70`}>
        <div className="shrink-0">
          <AgentAvatar agentName={key} size={56} />
        </div>
        <div className="flex-1 space-y-1.5">
          <div className="h-3.5 bg-white/30 rounded-md w-3/4" />
          <div className="h-2.5 bg-white/20 rounded-md w-1/2" />
        </div>
        {/* spinning indicator */}
        <div className="shrink-0">
          <svg className="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        </div>
      </div>
      <div className="p-4 space-y-2">
        <div className="h-2.5 bg-gray-100 rounded w-full" />
        <div className="h-2.5 bg-gray-100 rounded w-5/6" />
        <div className="h-2.5 bg-gray-100 rounded w-4/6" />
        <div className="h-8 bg-gray-50 rounded-xl mt-2" />
        <div className="h-2 bg-gray-100 rounded-full mt-2" />
      </div>
    </div>
  );
};
