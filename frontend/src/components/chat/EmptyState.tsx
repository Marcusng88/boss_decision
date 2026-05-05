
import { AgentAvatar, AGENT_COLORS } from "./AgentAvatar";

const AGENTS = [
  { id: "hr", label: "HR" },
  { id: "legal", label: "Legal" },
  { id: "sales", label: "Sales" },
  { id: "finance", label: "Finance" },
  { id: "marketing", label: "Marketing" },
  { id: "supply_chain", label: "Supply" },
];

const SAMPLES = [
  { icon: "hr", text: "Should we fire employee #1023?" },
  { icon: "legal", text: "What's the legal risk of expanding to Singapore?" },
  { icon: "sales", text: "How is our Q1 sales pipeline performing?" },
  { icon: "marketing", text: "Should we approve the new marketing campaign?" },
];

interface EmptyStateProps {
  onSample: (q: string) => void;
}

export const EmptyState = ({ onSample }: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center h-full gap-8 px-4 py-10 text-center">
    {/* Header */}
    <div className="space-y-2">
      <h2 className="text-3xl font-black text-foreground tracking-tight">
        AI Boss Decision Engine
      </h2>
      <p className="text-sm text-muted-foreground max-w-md leading-relaxed">
        Select agents below, ask any strategic question, and your specialist team
        will consult the data and deliver a clear, evidence-backed recommendation.
      </p>
    </div>

    {/* Cartoon agent showcase */}
    <div className="flex gap-4 flex-wrap justify-center">
      {AGENTS.map((agent, i) => {
        const colors = AGENT_COLORS[agent.id];
        return (
          <div
            key={agent.id}
            className="flex flex-col items-center gap-2 animate-fade-in-up"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div
              className={`rounded-2xl p-1.5 bg-gradient-to-br ${colors.gradient} shadow-lg hover:scale-110 transition-transform cursor-default`}
              style={{ filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.15))" }}
            >
              <AgentAvatar agentName={agent.id} size={52} />
            </div>
            <span className={`text-[10px] font-bold uppercase tracking-wide ${colors.text}`}>
              {agent.label}
            </span>
          </div>
        );
      })}
    </div>

    {/* Sample queries */}
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
      {SAMPLES.map((s, i) => {
        const colors = AGENT_COLORS[s.icon];
        return (
          <button
            key={s.text}
            onClick={() => onSample(s.text)}
            className={`
              flex items-center gap-3 text-left px-4 py-3 rounded-2xl border
              bg-white hover:shadow-md transition-all duration-200 hover:-translate-y-0.5
              ${colors.light} group animate-fade-in-up
            `}
            style={{ animationDelay: `${(i + AGENTS.length) * 60}ms` }}
          >
            <div className="shrink-0">
              <AgentAvatar agentName={s.icon} size={32} />
            </div>
            <span className="text-sm text-gray-700 group-hover:text-gray-900 transition-colors leading-snug">
              {s.text}
            </span>
          </button>
        );
      })}
    </div>
  </div>
);
