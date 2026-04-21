import { Bot } from "lucide-react";
import { StageCard } from "./StageCard";
import { AgentInsight } from "@/lib/decision-engine";

interface Props {
  status: "pending" | "loading" | "done";
  agents: AgentInsight[];
}

export const AgentInsights = ({ status, agents }: Props) => {
  return (
    <StageCard
      icon={<Bot className="w-5 h-5" />}
      title="Agent Insights"
      subtitle="Domain-specialist agents weigh in"
      status={status}
      accent="accent"
    >
      <div className="grid sm:grid-cols-3 gap-3">
        {agents.map((a, i) => (
          <div
            key={a.name}
            className="rounded-xl border border-border bg-background p-4 animate-fade-in-up"
            style={{ animationDelay: `${i * 120}ms` }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{a.emoji}</span>
              <span className="text-sm font-semibold text-foreground">{a.name}</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{a.insight}</p>
          </div>
        ))}
      </div>
    </StageCard>
  );
};
