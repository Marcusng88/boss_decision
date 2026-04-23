import { Brain } from "lucide-react";

const SAMPLES = [
  { icon: "👤", text: "Should we fire employee #1023?" },
  { icon: "🌏", text: "Should we expand to the Singapore market?" },
  { icon: "🏢", text: "Should we acquire competitor BetaCorp?" },
  { icon: "📦", text: "Should we approve emergency procurement for Q4?" },
];

interface EmptyStateProps {
  onSample: (q: string) => void;
}

export const EmptyState = ({ onSample }: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center h-full gap-8 px-4 py-12 text-center">
    <div>
      <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow mb-4">
        <Brain className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-foreground mb-2">AI Boss Decision Engine</h2>
      <p className="text-sm text-muted-foreground max-w-md">
        Ask any strategic business question. Specialist agents will consult the data,
        debate perspectives, and deliver a clear recommendation.
      </p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
      {SAMPLES.map((s) => (
        <button
          key={s.text}
          onClick={() => onSample(s.text)}
          className="flex items-start gap-3 text-left px-4 py-3 rounded-xl border border-border bg-card hover:bg-accent/50 hover:border-primary/30 transition-colors shadow-card group"
        >
          <span className="text-lg mt-0.5">{s.icon}</span>
          <span className="text-sm text-foreground/80 group-hover:text-foreground transition-colors leading-snug">
            {s.text}
          </span>
        </button>
      ))}
    </div>
  </div>
);
