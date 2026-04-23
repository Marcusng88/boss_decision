
import { useRef, useEffect, KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { AgentSelector } from "./AgentSelector";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled?: boolean;
  selectedAgents: string[];
  onAgentsChange: (agents: string[]) => void;
}

export const ChatInput = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled,
  selectedAgents,
  onAgentsChange,
}: ChatInputProps) => {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 160)}px`;
    }
  }, [value]);

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) onSubmit();
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
      {/* Agent selector row */}
      <div className="px-4 pt-3">
        <AgentSelector selected={selectedAgents} onChange={onAgentsChange} />
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2 px-4 pb-3">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKey}
          placeholder={
            selectedAgents.length > 0
              ? `Ask ${selectedAgents.map((a) => a.replace("_", " ")).join(", ")} agents…`
              : "Ask a strategic decision question…"
          }
          disabled={disabled || isLoading}
          className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none leading-relaxed max-h-40 disabled:opacity-60"
        />
        <button
          onClick={onSubmit}
          disabled={isLoading || !value.trim() || disabled}
          className="w-9 h-9 rounded-xl bg-gradient-primary text-white flex items-center justify-center shadow-glow transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:shadow-none disabled:scale-100 shrink-0"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
};
