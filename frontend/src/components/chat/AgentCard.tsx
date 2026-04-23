import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { AgentInsightData } from "@/lib/api";

const TrendIcon = ({ trend }: { trend: string }) => {
  if (trend === "up") return <TrendingUp className="w-3.5 h-3.5 text-success" />;
  if (trend === "down") return <TrendingDown className="w-3.5 h-3.5 text-destructive" />;
  return <Minus className="w-3.5 h-3.5 text-muted-foreground" />;
};

interface AgentCardProps {
  insight: AgentInsightData;
  style?: React.CSSProperties;
}

export const AgentCard = ({ insight, style }: AgentCardProps) => (
  <div
    className="rounded-xl border border-border bg-card p-4 shadow-card animate-fade-in-up"
    style={style}
  >
    <div className="flex items-start justify-between gap-2 mb-3">
      <div className="flex items-center gap-2">
        <span className="text-xl">{insight.emoji || "🤖"}</span>
        <div>
          <p className="text-sm font-semibold text-foreground">{insight.agent_name} Agent</p>
          <p className="text-xs text-muted-foreground">{insight.data_summary}</p>
        </div>
      </div>
      {insight.metric_value && (
        <div className="flex items-center gap-1 shrink-0">
          <TrendIcon trend={insight.trend} />
          <span className="text-sm font-bold text-foreground">{insight.metric_value}</span>
        </div>
      )}
    </div>

    <div className="space-y-1.5 mb-3">
      {insight.findings.slice(0, 3).map((f, i) => (
        <p key={i} className="text-xs text-foreground/80 flex gap-1.5">
          <span className="text-primary mt-0.5">•</span>
          <span>{f}</span>
        </p>
      ))}
    </div>

    <div className="border-t border-border/50 pt-2.5">
      <p className="text-xs font-medium text-foreground/90 italic">
        "{insight.recommendation}"
      </p>
      <div className="flex items-center gap-1.5 mt-1.5">
        <div className="flex-1 h-1 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-primary"
            style={{ width: `${Math.round(insight.confidence * 100)}%` }}
          />
        </div>
        <span className="text-xs text-muted-foreground shrink-0">
          {Math.round(insight.confidence * 100)}%
        </span>
      </div>
    </div>
  </div>
);
