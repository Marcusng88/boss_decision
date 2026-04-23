import { useState, useRef, useEffect, useCallback } from "react";
import { Menu, X } from "lucide-react";
import { ChatSidebar, type Conversation } from "@/components/chat/ChatSidebar";
import { ChatMessage, type Message } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { EmptyState } from "@/components/chat/EmptyState";
import { analyzeDecision, type AnalysisResponse } from "@/lib/api";

type Stage = "thinking" | "agents" | "perspectives" | "decision";

interface ConversationState {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

const STAGE_DELAYS: Record<Stage, number> = {
  thinking: 0,
  agents: 600,
  perspectives: 1400,
  decision: 2200,
};

export default function Index() {
  const [conversations, setConversations] = useState<ConversationState[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId) ?? null;

  const scrollBottom = () =>
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);

  const updateMessages = useCallback(
    (convId: string, updater: (msgs: Message[]) => Message[]) => {
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, messages: updater(c.messages) } : c))
      );
    },
    []
  );

  const handleSubmit = useCallback(async () => {
    const query = input.trim();
    if (!query || isLoading) return;
    setInput("");
    setIsLoading(true);

    // Create or use existing conversation
    let convId = activeId;
    if (!convId) {
      convId = crypto.randomUUID();
      const newConv: ConversationState = {
        id: convId,
        title: query.slice(0, 50) + (query.length > 50 ? "…" : ""),
        timestamp: new Date(),
        messages: [],
      };
      setConversations((prev) => [newConv, ...prev]);
      setActiveId(convId);
    }

    const userMsgId = crypto.randomUUID();
    const asstMsgId = crypto.randomUUID();

    // Add user message + loading assistant message
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== convId) return c;
        return {
          ...c,
          messages: [
            ...c.messages,
            { id: userMsgId, role: "user" as const, content: query },
            { id: asstMsgId, role: "assistant" as const, isLoading: true },
          ],
        };
      })
    );
    scrollBottom();

    try {
      const data: AnalysisResponse = await analyzeDecision(query);

      // Replace loading message with real data, then animate stages
      const animateStage = (stage: Stage) => {
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== convId) return c;
            return {
              ...c,
              messages: c.messages.map((m) =>
                m.id === asstMsgId
                  ? { ...m, isLoading: false, data, stage }
                  : m
              ),
            };
          })
        );
        scrollBottom();
      };

      const stages: Stage[] = ["agents", "perspectives", "decision"];
      stages.forEach((s) => setTimeout(() => animateStage(s), STAGE_DELAYS[s]));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      updateMessages(convId, (msgs) =>
        msgs.map((m) =>
          m.id === asstMsgId
            ? { ...m, isLoading: false, error: `Analysis failed: ${msg}` }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      scrollBottom();
    }
  }, [input, isLoading, activeId, updateMessages]);

  const handleNewChat = () => {
    setActiveId(null);
    setInput("");
  };

  const handleSelectConv = (id: string) => {
    setActiveId(id);
    scrollBottom();
  };

  const handleDeleteConv = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  };

  const sidebarConvs: Conversation[] = conversations.map((c) => ({
    id: c.id,
    title: c.title,
    timestamp: c.timestamp,
  }));

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      {sidebarOpen && (
        <ChatSidebar
          conversations={sidebarConvs}
          activeId={activeId}
          onSelect={handleSelectConv}
          onNew={handleNewChat}
          onDelete={handleDeleteConv}
        />
      )}

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-border bg-card/70 backdrop-blur-sm shrink-0">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-1.5 rounded-lg hover:bg-accent transition-colors text-muted-foreground"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
          <p className="text-sm font-semibold text-foreground truncate">
            {activeConv ? activeConv.title : "AI Boss Decision Engine"}
          </p>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
            Engine online
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {!activeConv || activeConv.messages.length === 0 ? (
            <EmptyState onSample={(q) => { setInput(q); }} />
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
              {activeConv.messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="shrink-0 px-4 pb-4 pt-2 bg-background/80 backdrop-blur-sm border-t border-border">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              value={input}
              onChange={setInput}
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />
            <p className="text-center text-xs text-muted-foreground mt-2">
              Multi-agent reasoning • HR · Legal · Sales · Finance · Marketing · Supply Chain
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
