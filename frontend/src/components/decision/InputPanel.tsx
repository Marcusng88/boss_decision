import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Loader2, Upload, FileText, X } from "lucide-react";

interface InputPanelProps {
  onAnalyze: (payload: {
    query: string;
    context?: string;
    targetType?: string;
    targetId?: number;
    allowMockFallback: boolean;
    document?: File;
  }) => void;
  isAnalyzing: boolean;
}

const SAMPLE_QUERIES = [
  "Should we fire employee #1023?",
  "Should we acquire competitor BetaCorp?",
  "Should we expand to the Singapore market?",
];

export const InputPanel = ({ onAnalyze, isAnalyzing }: InputPanelProps) => {
  const [query, setQuery] = useState("Should we fire employee #1023?");
  const [context, setContext] = useState("");
  const [targetType, setTargetType] = useState("employee");
  const [targetId, setTargetId] = useState("102");
  const [allowMockFallback, setAllowMockFallback] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | undefined>(undefined);

  const handleSubmit = () => {
    if (!query.trim() || isAnalyzing) return;
    onAnalyze({
      query: query.trim(),
      context: context.trim() || undefined,
      targetType: targetType.trim() || undefined,
      targetId: targetId.trim() ? Number(targetId) : undefined,
      allowMockFallback,
      document: selectedFile,
    });
  };

  return (
    <aside className="bg-card/90 rounded-3xl shadow-elevated border border-border/70 p-6 h-fit lg:sticky lg:top-6 backdrop-blur-sm">
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

      <div className="mt-3 rounded-xl border border-dashed border-border bg-background/70 p-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
          Upload file for manager analysis
        </p>
        <label className="flex items-center justify-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm text-secondary-foreground cursor-pointer hover:bg-accent hover:text-accent-foreground transition-smooth">
          <Upload className="w-4 h-4" />
          Choose file
          <input
            type="file"
            className="hidden"
            onChange={(e) => setSelectedFile(e.target.files?.[0])}
            disabled={isAnalyzing}
          />
        </label>

        {selectedFile && (
          <div className="mt-2 flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground">
            <span className="inline-flex items-center gap-1.5 truncate pr-2">
              <FileText className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">{selectedFile.name}</span>
            </span>
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setSelectedFile(undefined)}
              disabled={isAnalyzing}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3">
        <input
          value={targetType}
          onChange={(e) => setTargetType(e.target.value)}
          placeholder="target_type"
          className="h-10 rounded-lg border border-border bg-background px-3 text-sm"
          disabled={isAnalyzing}
        />
        <input
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          placeholder="target_id"
          className="h-10 rounded-lg border border-border bg-background px-3 text-sm"
          disabled={isAnalyzing}
        />
      </div>

      <Textarea
        value={context}
        onChange={(e) => setContext(e.target.value)}
        placeholder="Optional context for manager routing"
        className="mt-3 min-h-[72px] resize-none text-sm bg-background border-border"
        disabled={isAnalyzing}
      />

      <label className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <input
          type="checkbox"
          checked={allowMockFallback}
          onChange={(e) => setAllowMockFallback(e.target.checked)}
          disabled={isAnalyzing}
        />
        Enable mock fallback if backend call fails
      </label>

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
