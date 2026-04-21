import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Loader2 } from "lucide-react";

interface InputPanelProps {
  onAnalyze: (query: string) => void;
  isAnalyzing: boolean;
}

const SAMPLE_QUERIES = [
  "Should we fire employee #1023?",
  "Should we acquire competitor BetaCorp?",
  "Should we expand to the Singapore market?",
];

export const InputPanel = ({ onAnalyze, isAnalyzing }: InputPanelProps) => {
  const [query, setQuery] = useState("Should we fire employee #1023?");

  const handleSubmit = () => {
    if (!query.trim() || isAnalyzing) return;
    onAnalyze(query.trim());
  };

  return (
    <aside className="bg-card rounded-2xl shadow-card border border-border p-6 h-fit lg:sticky lg:top-6">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow">
          <Sparkles className="w-4 h-4 text-primary-foreground" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">Ask the Engine</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Pose a strategic decision. Watch the agents reason.
      </p>

      <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Decision query
      </label>
      <Textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. Should we fire employee #1023?"
        className="mt-2 min-h-[120px] resize-none text-base bg-background border-border focus-visible:ring-primary"
        disabled={isAnalyzing}
      />

      <Button
        onClick={handleSubmit}
        disabled={isAnalyzing || !query.trim()}
        className="w-full mt-4 h-11 bg-gradient-primary text-primary-foreground font-semibold shadow-elevated hover:shadow-glow transition-smooth border-0"
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Analyzing…
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4 mr-2" />
            Analyze Decision
          </>
        )}
      </Button>

      <div className="mt-6 pt-6 border-t border-border">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Try a sample
        </p>
        <div className="flex flex-col gap-2">
          {SAMPLE_QUERIES.map((s) => (
            <button
              key={s}
              onClick={() => !isAnalyzing && setQuery(s)}
              disabled={isAnalyzing}
              className="text-left text-sm px-3 py-2 rounded-lg bg-secondary hover:bg-accent hover:text-accent-foreground transition-smooth text-secondary-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
};
