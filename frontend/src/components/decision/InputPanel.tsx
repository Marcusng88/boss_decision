import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Loader2, Wand2 } from "lucide-react";

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
    <aside className="h-fit rounded-[1.6rem] border border-border bg-card/80 p-6 shadow-card lg:sticky lg:top-24">
      <div className="mb-1 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-primary shadow-glow">
          <Sparkles className="w-4 h-4 text-primary-foreground" />
        </div>
        <h2 className="text-3xl leading-none text-foreground">Ask the Engine</h2>
      </div>
      <p className="mb-4 text-sm text-muted-foreground">
        Pose a strategic decision and watch each specialist layer form a recommendation.
      </p>

      <label className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">Decision query</label>
      <Textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. Should we fire employee #1023?"
        className="mt-2 min-h-[130px] resize-none rounded-xl border-border bg-background/80 text-base leading-relaxed focus-visible:ring-primary"
        disabled={isAnalyzing}
      />

      <Button
        onClick={handleSubmit}
        disabled={isAnalyzing || !query.trim()}
        className="mt-4 h-11 w-full border-0 bg-gradient-primary font-semibold text-primary-foreground shadow-elevated transition-smooth hover:shadow-glow"
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Wand2 className="mr-2 h-4 w-4" />
            Analyze Decision
          </>
        )}
      </Button>

      <div className="mt-6 border-t border-border pt-6">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">Try a sample</p>
        <div className="flex flex-col gap-2">
          {SAMPLE_QUERIES.map((s) => (
            <button
              key={s}
              onClick={() => !isAnalyzing && setQuery(s)}
              disabled={isAnalyzing}
              className="rounded-lg border border-border bg-secondary/85 px-3 py-2 text-left text-sm text-secondary-foreground transition-smooth hover:border-accent/30 hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
};
