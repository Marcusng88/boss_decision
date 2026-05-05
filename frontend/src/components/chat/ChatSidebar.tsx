import { Brain, Plus, MessageSquare, Trash2 } from "lucide-react";

export interface Conversation {
  id: string;
  title: string;
  timestamp: Date;
}

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export const ChatSidebar = ({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: ChatSidebarProps) => (
  <aside className="w-64 flex flex-col h-full bg-sidebar border-r border-sidebar-border">
    {/* Brand */}
    <div className="flex items-center gap-2.5 px-4 py-4 border-b border-sidebar-border">
      <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow shrink-0">
        <Brain className="w-4 h-4 text-white" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-bold text-sidebar-foreground truncate">Boss Decision</p>
        <p className="text-xs text-sidebar-foreground/50 truncate">Multi-agent AI</p>
      </div>
    </div>

    {/* New Chat */}
    <div className="p-3">
      <button
        onClick={onNew}
        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
      >
        <Plus className="w-4 h-4" />
        New Chat
      </button>
    </div>

    {/* Conversation list */}
    <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-0.5">
      {conversations.length === 0 && (
        <p className="text-xs text-sidebar-foreground/40 px-2 py-4 text-center">
          No conversations yet
        </p>
      )}
      {conversations.map((conv) => (
        <div
          key={conv.id}
          className={`
            group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-colors
            ${conv.id === activeId
              ? "bg-sidebar-accent text-sidebar-accent-foreground"
              : "text-sidebar-foreground hover:bg-sidebar-accent/60"
            }
          `}
          onClick={() => onSelect(conv.id)}
        >
          <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-60" />
          <span className="flex-1 text-xs truncate">{conv.title}</span>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
            className="opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity p-0.5 rounded"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  </aside>
);
