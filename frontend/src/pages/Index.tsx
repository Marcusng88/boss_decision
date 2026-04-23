
import { useState, useRef, useCallback } from "react";
import { Menu, X } from "lucide-react";
import { ChatSidebar, type Conversation } from "@/components/chat/ChatSidebar";
import { ChatMessage, type Message } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { EmptyState } from "@/components/chat/EmptyState";
import { analyzeDecisionStream, type StreamingState } from "@/lib/api";

interface ConversationState {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

export default function Index() {
  const [conversations, setConversations] = useState<ConversationState[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId) ?? null;

  const scrollBottom = () =>
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);

  const patchMsg = useCallback(
    (convId: string, msgId: string, patch: Partial<Message>) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : { ...c, messages: c.messages.map((m) => (m.id === msgId ? { ...m, ...patch } : m)) }
        )
      );
    },
    []
  );

  const patchStreaming = useCallback(
    (convId: string, msgId: string, updater: (s: StreamingState) => StreamingState) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                messages: c.messages.map((m) =>
                  m.id === msgId && m.streaming ? { ...m, streaming: updater(m.streaming) } : m
                ),
              }
        )
      );
    },
    []
  );

  const handleSubmit = useCallback(async () => {
    const query = input.trim();
    if (!query || isLoading) return;
    setInput("");
    setIsLoading(true);

    let convId = activeId;
    if (!convId) {
      convId = crypto.randomUUID();
      setConversations((prev) => [
        {
          id: convId!,
          title: query.slice(0, 50) + (query.length > 50 ? "…" : ""),
          timestamp: new Date(),
          messages: [],
        },
        ...prev,
      ]);
      setActiveId(convId);
    }

    const userMsgId = crypto.randomUUID();
    const asstMsgId = crypto.randomUUID();

    const initStreaming: StreamingState = {
      status: "Connecting to agents…",
      agents_invoked: [],
      active_agents: [],
      agent_insights: [],
      isDone: false,
    };

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== convId) return c;
        return {
          ...c,
          messages: [
            ...c.messages,
            { id: userMsgId, role: "user" as const, content: query },
            { id: asstMsgId, role: "assistant" as const, streaming: initStreaming },
          ],
        };
      })
    );
    scrollBottom();

    const finalConvId = convId;

    try {
      await analyzeDecisionStream(query, selectedAgents, {
        onStatus: (message) => {
          patchStreaming(finalConvId, asstMsgId, (s) => ({ ...s, status: message }));
        },
        onIntent: (agents) => {
          patchStreaming(finalConvId, asstMsgId, (s) => ({
            ...s,
            agents_invoked: agents,
            status: `Consulting ${agents.length} specialist agent${agents.length !== 1 ? "s" : ""}…`,
          }));
          scrollBottom();
        },
        onAgentStart: (agent) => {
          patchStreaming(finalConvId, asstMsgId, (s) => ({
            ...s,
            active_agents: [...s.active_agents, agent],
          }));
        },
        onAgentDone: (insight) => {
          patchStreaming(finalConvId, asstMsgId, (s) => ({
            ...s,
            agent_insights: [...s.agent_insights, insight],
            active_agents: s.active_agents.filter(
              (a) => a !== insight.agent_name.toLowerCase().replace(/\s+/g, "_")
            ),
          }));
          scrollBottom();
        },
        onSynthesis: (conservative, aggressive) => {
          patchStreaming(finalConvId, asstMsgId, (s) => ({
            ...s,
            conservative_view: conservative,
            aggressive_view: aggressive,
            status: "Formulating final decision…",
          }));
          scrollBottom();
        },
        onComplete: (result) => {
          patchMsg(finalConvId, asstMsgId, {
            streaming: undefined,
            data: result,
            stage: "decision" as const,
          });
          scrollBottom();
        },
        onError: (err) => {
          patchMsg(finalConvId, asstMsgId, {
            streaming: undefined,
            error: `Analysis failed: ${err}`,
          });
        },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      patchMsg(finalConvId, asstMsgId, {
        streaming: undefined,
        error: `Analysis failed: ${msg}`,
      });
    } finally {
      setIsLoading(false);
      scrollBottom();
    }
  }, [input, isLoading, activeId, selectedAgents, patchMsg, patchStreaming]);

  const handleNewChat = () => {
    setActiveId(null);
    setInput("");
  };

  const handleSelectConv = (id: string) => {
    setActiveId(id);
    setTimeout(() => bottomRef.current?.scrollIntoView(), 100);
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
      {sidebarOpen && (
        <ChatSidebar
          conversations={sidebarConvs}
          activeId={activeId}
          onSelect={handleSelectConv}
          onNew={handleNewChat}
          onDelete={handleDeleteConv}
        />
      )}

      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-border bg-card/70 backdrop-blur-sm shrink-0">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-1.5 rounded-lg hover:bg-accent transition-colors text-muted-foreground"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
          <p className="text-sm font-bold text-foreground truncate">
            {activeConv ? activeConv.title : "AI Boss Decision Engine"}
          </p>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Engine online
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {!activeConv || activeConv.messages.length === 0 ? (
            <EmptyState onSample={(q) => setInput(q)} />
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
              selectedAgents={selectedAgents}
              onAgentsChange={setSelectedAgents}
            />
            <p className="text-center text-xs text-muted-foreground mt-2">
              {selectedAgents.length > 0
                ? `${selectedAgents.length} agent${selectedAgents.length > 1 ? "s" : ""} selected · results stream as they complete`
                : "Auto-detect agents · HR · Legal · Sales · Finance · Marketing · Supply Chain"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
