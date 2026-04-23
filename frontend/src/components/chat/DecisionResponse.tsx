import { Shield, Flame, CheckCircle2, AlertTriangle } from "lucide-react";
import type { AnalysisResponse } from "@/lib/api";
import { AgentCard } from "./AgentCard";

type Stage = "thinking" | "agents" | "perspectives" | "decision";

interface DecisionResponseProps {
  data: AnalysisResponse;
  stage: Stage;
}

const riskColor = (r: string) =>
  r === "High"
    ? "bg-destructive/10 text-destructive border-destructive/20"
    : r === "Medium"
    ? "bg-warning/10 text-warning border-warning/20"
    : "bg-success/10 text-success border-success/20";

export const DecisionResponse = ({ data, stage }: DecisionResponseProps) => {
  const showAgents = stage !== "thinking";
  const showPerspectives = stage === "perspectives" || stage === "decision";
  const showDecision = stage === "decision";

  return (
    <div className="space-y-4 w-full max-w-3xl">
      {/* Agents invoked label */}
      <div className="flex flex-wrap gap-1.5 items-center">
        <span className="text-xs text-muted-foreground">Agents consulted:</span>
        {data.agents_invoked.map((a) => (
          <span
            key={a}
            className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium border border-primary/20"
          >
            {a.replace("_", " ")}
          </span>
        ))}
      </div>

      {/* Agent insight cards */}
      {showAgents && data.agent_insights.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.agent_insights.map((insight, i) => (
            <AgentCard
              key={insight.agent_name}
              insight={insight}
              style={{ animationDelay: `${i * 120}ms` }}
            />
          ))}
        </div>
      )}

      {/* Conservative vs Aggressive perspectives */}
      {showPerspectives && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in-up">
          <div className="rounded-xl border border-conservative/30 bg-conservative/5 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-conservative" />
              <span className="text-xs font-semibold text-conservative uppercase tracking-wide">
                Conservative
              </span>
            </div>
            <p className="text-sm font-semibold text-foreground mb-1.5">
              {data.conservative_view.recommendation}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {data.conservative_view.reasoning}
            </p>
          </div>

          <div className="rounded-xl border border-aggressive/30 bg-aggressive/5 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-4 h-4 text-aggressive" />
              <span className="text-xs font-semibold text-aggressive uppercase tracking-wide">
                Aggressive
              </span>
            </div>
            <p className="text-sm font-semibold text-foreground mb-1.5">
              {data.aggressive_view.recommendation}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {data.aggressive_view.reasoning}
            </p>
          </div>
        </div>
      )}

      {/* Final decision */}
      {showDecision && (
        <div className="rounded-2xl bg-gradient-decision p-5 text-white animate-fade-in-up shadow-elevated">
          <div className="flex items-center gap-2 mb-1 opacity-80">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-widest">Final Decision</span>
          </div>
          <h3 className="text-xl font-black tracking-tight mb-2">
            {data.final_decision.verdict}
          </h3>
          <p className="text-sm opacity-90 leading-relaxed mb-4">
            {data.final_decision.reasoning}
          </p>
          <div className="flex items-center gap-4 pt-3 border-t border-white/20">
            <div>
              <p className="text-xs opacity-60 mb-1">Risk Level</p>
              <span
                className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${riskColor(
                  data.final_decision.risk_level
                )}`}
              >
                {data.final_decision.risk_level}
              </span>
            </div>
            <div className="flex-1">
              <p className="text-xs opacity-60 mb-1">Confidence</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full bg-white/20">
                  <div
                    className="h-full rounded-full bg-white"
                    style={{ width: `${data.final_decision.confidence_score}%` }}
                  />
                </div>
                <span className="text-sm font-bold">
                  {data.final_decision.confidence_score}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
