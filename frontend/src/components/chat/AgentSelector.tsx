
import { AgentAvatar, AGENT_COLORS } from "./AgentAvatar";

export const AVAILABLE_AGENTS = [
  { id: "hr", label: "HR", description: "Performance & people" },
  { id: "legal", label: "Legal", description: "Compliance & contracts" },
  { id: "sales", label: "Sales", description: "Revenue & pipeline" },
  { id: "finance", label: "Finance", description: "Budget & costs" },
  { id: "marketing", label: "Marketing", description: "Campaigns & growth" },
  { id: "supply_chain", label: "Supply Chain", description: "Logistics & vendors" },
];

interface AgentSelectorProps {
  selected: string[];
  onChange: (agents: string[]) => void;
}

export const AgentSelector = ({ selected, onChange }: AgentSelectorProps) => {
  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((a) => a !== id) : [...selected, id]);
  };

  return (
    <div className="flex flex-wrap gap-2 px-1 pb-2">
      <span className="text-xs text-muted-foreground self-center mr-1 shrink-0">Consult:</span>
      {AVAILABLE_AGENTS.map((agent) => {
        const isSelected = selected.includes(agent.id);
        const colors = AGENT_COLORS[agent.id];
        return (
          <button
            key={agent.id}
            onClick={() => toggle(agent.id)}
            title={agent.description}
            className={`
              flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
              border transition-all duration-200 hover:scale-105 active:scale-95
              ${isSelected
                ? `bg-gradient-to-r ${colors.gradient} text-white border-transparent shadow-md`
                : `bg-white ${colors.light} ${colors.text} border hover:shadow-sm`
              }
            `}
          >
            <AgentAvatar agentName={agent.id} size={18} />
            <span>{agent.label}</span>
            {isSelected && (
              <span className="ml-0.5 opacity-90">✓</span>
            )}
          </button>
        );
      })}
      {selected.length > 0 && (
        <button
          onClick={() => onChange([])}
          className="text-xs text-muted-foreground hover:text-foreground px-1 self-center transition-colors"
        >
          clear
        </button>
      )}
    </div>
  );
};
