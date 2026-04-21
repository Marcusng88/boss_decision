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
      icon={<Bot className="h-5 w-5" />}
      title="Agent Insights"
      subtitle="Domain-specialist agents weigh in"
      status={status}
      accent="accent"
    >
      <div className="grid gap-3 sm:grid-cols-3">
        {agents.map((a, i) => (
          <div
            key={a.name}
            className="animate-fade-in-up rounded-xl border border-border bg-background/80 p-4"
            style={{ animationDelay: `${i * 120}ms` }}
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="text-lg">{a.emoji}</span>
              <span className="text-base font-semibold text-foreground">{a.name}</span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">{a.insight}</p>
          </div>
        ))}
      </div>
    </StageCard>
  );
};
