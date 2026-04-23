import { Brain, User, Loader2 } from "lucide-react";
import type { AnalysisResponse } from "@/lib/api";
import { DecisionResponse } from "./DecisionResponse";

type Stage = "thinking" | "agents" | "perspectives" | "decision";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content?: string;
  data?: AnalysisResponse;
  stage?: Stage;
  error?: string;
  isLoading?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

const ThinkingDots = () => (
  <div className="flex items-center gap-1 py-1">
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce"
        style={{ animationDelay: `${i * 150}ms` }}
      />
    ))}
  </div>
);

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} items-start group`}>
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5
          ${isUser
            ? "bg-primary text-primary-foreground"
            : "bg-gradient-primary text-white shadow-glow"
          }
        `}
      >
        {isUser ? <User className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
      </div>

      {/* Message content */}
      <div className={`flex-1 min-w-0 ${isUser ? "flex justify-end" : ""}`}>
        {isUser ? (
          <div className="inline-block max-w-[85%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5 text-sm leading-relaxed">
            {message.content}
          </div>
        ) : message.isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground text-sm py-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Consulting agents…</span>
          </div>
        ) : message.error ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive max-w-lg">
            {message.error}
          </div>
        ) : message.data ? (
          <DecisionResponse data={message.data} stage={message.stage || "decision"} />
        ) : (
          <div className="text-sm text-foreground leading-relaxed py-1">
            <ThinkingDots />
          </div>
        )}
      </div>
    </div>
  );
};
