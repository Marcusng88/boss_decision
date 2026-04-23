
import { Brain, User } from "lucide-react";
import type { AnalysisResponse, StreamingState } from "@/lib/api";
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
  streaming?: StreamingState;
}

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} items-start`}>
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5
          ${isUser
            ? "bg-primary text-primary-foreground"
            : "bg-gradient-to-br from-blue-500 to-violet-600 text-white shadow-glow"
          }
        `}
      >
        {isUser ? <User className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 ${isUser ? "flex justify-end" : ""}`}>
        {isUser ? (
          <div className="inline-block max-w-[85%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5 text-sm leading-relaxed">
            {message.content}
          </div>
        ) : message.error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 max-w-lg">
            {message.error}
          </div>
        ) : message.streaming ? (
          <DecisionResponse streaming={message.streaming} />
        ) : message.data ? (
          <DecisionResponse data={message.data} stage={message.stage ?? "decision"} />
        ) : (
          <div className="flex items-center gap-2 py-2 text-muted-foreground text-sm">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <span>Starting analysis…</span>
          </div>
        )}
      </div>
    </div>
  );
};
