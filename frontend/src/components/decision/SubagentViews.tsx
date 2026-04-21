import { Brain, Shield, Flame } from "lucide-react";
import { StageCard } from "./StageCard";
import { SubagentView } from "@/lib/decision-engine";

interface Props {
  status: "pending" | "loading" | "done";
  views: SubagentView[];
}

export const SubagentViews = ({ status, views }: Props) => {
  return (
    <StageCard
      icon={<Brain className="h-5 w-5" />}
      title="Subagent Perspectives"
      subtitle="Two minds, two strategies debating in parallel"
      status={status}
      accent="warning"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        {views.map((v, i) => {
          const isConservative = v.stance === "conservative";
          return (
            <div
              key={v.stance}
              className="relative overflow-hidden rounded-xl border-2 p-5 animate-fade-in-up"
              style={{
                animationDelay: `${i * 150}ms`,
                borderColor: isConservative ? "hsl(var(--conservative))" : "hsl(var(--aggressive))",
                background: isConservative ? "hsl(var(--conservative) / 0.08)" : "hsl(var(--aggressive) / 0.08)",
              }}
            >
              <div className="mb-3 flex items-center gap-2">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-primary-foreground"
                  style={{
                    background: isConservative ? "hsl(var(--conservative))" : "hsl(var(--aggressive))",
                  }}
                >
                  {isConservative ? <Shield className="h-4 w-4" /> : <Flame className="h-4 w-4" />}
                </div>
                <span className="text-sm font-bold uppercase tracking-[0.16em] text-foreground">
                  {isConservative ? "Conservative" : "Aggressive"}
                </span>
              </div>
              <p className="mb-1 text-base font-semibold text-foreground">{v.recommendation}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{v.reasoning}</p>
            </div>
          );
        })}
      </div>
    </StageCard>
  );
};
