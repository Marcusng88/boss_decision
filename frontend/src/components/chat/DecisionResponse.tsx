
import { useState, useEffect } from "react";
import { CheckCircle2, TrendingDown, Zap } from "lucide-react";
import type { AnalysisResponse, StreamingState } from "@/lib/api";
import { AgentCard, AgentCardSkeleton } from "./AgentCard";
import { AgentAvatar, AGENT_COLORS } from "./AgentAvatar";

// Typewriter hook for smooth text reveal
function useTypewriter(text: string, speed = 18) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    setDisplayed("");
    if (!text) return;
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(timer);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed]);
  return displayed;
}

const riskBadge = (r: string) => {
  if (r === "High") return "bg-red-100 text-red-700 border border-red-200";
  if (r === "Medium") return "bg-amber-100 text-amber-700 border border-amber-200";
  return "bg-emerald-100 text-emerald-700 border border-emerald-200";
};

// Status line shown while streaming
const ThinkingBar = ({ status, agents_invoked, active_agents }: {
  status: string;
  agents_invoked: string[];
  active_agents: string[];
}) => (
  <div className="space-y-2">
    <p className="text-sm font-medium text-foreground">{status}</p>
    {agents_invoked.length > 0 && (
      <div className="flex flex-wrap gap-1">
        {agents_invoked.map((a) => {
          const isRunning = active_agents.includes(a);
          const colors = AGENT_COLORS[a] || AGENT_COLORS.hr;
          return (
            <span
              key={a}
              className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-medium transition-all
                ${isRunning
                  ? `bg-gradient-to-r ${colors.gradient} text-white shadow-sm`
                  : "bg-gray-100 text-gray-500"
                }`}
            >
              <AgentAvatar agentName={a} size={12} />
              <span className="capitalize">{a.replace("_", " ")}</span>
              {isRunning && (
                <svg className="w-2.5 h-2.5 animate-spin ml-0.5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
            </span>
          );
        })}
      </div>
    )}
  </div>
);

// --- Shared synthesis components ---

interface PerspectiveView { recommendation: string; reasoning: string; }

const PerspectivesPanel = ({
  conservative,
  aggressive,
}: {
  conservative: PerspectiveView;
  aggressive: PerspectiveView;
}) => (
  <div className="space-y-2 animate-fade-in-up">
    <p className="text-sm font-semibold text-gray-700">What to do next?</p>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <TrendingDown className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Play it safe</span>
        </div>
        <p className="text-xs font-semibold text-gray-800 mb-1">{conservative.recommendation}</p>
        <p className="text-xs text-gray-500 leading-relaxed">{conservative.reasoning}</p>
      </div>
      <div className="rounded-xl border border-orange-200 bg-orange-50 p-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Zap className="w-3.5 h-3.5 text-orange-500" />
          <span className="text-[10px] font-bold text-orange-600 uppercase tracking-wider">Move fast</span>
        </div>
        <p className="text-xs font-semibold text-gray-800 mb-1">{aggressive.recommendation}</p>
        <p className="text-xs text-gray-500 leading-relaxed">{aggressive.reasoning}</p>
      </div>
    </div>
  </div>
);

const FinalDecisionPanel = ({
  verdict,
  reasoning,
  risk_level,
  confidence_score,
}: {
  verdict: string;
  reasoning: string;
  risk_level: string;
  confidence_score: number;
  agentCount?: number;
}) => (
  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 animate-fade-in-up">
    <div className="flex items-center gap-2 mb-2">
      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
      <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Recommended action</span>
      <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full ${riskBadge(risk_level)}`}>
        {risk_level} risk
      </span>
    </div>
    <p className="text-sm font-bold text-gray-900 mb-1.5 leading-snug">{verdict}</p>
    <p className="text-xs text-gray-600 leading-relaxed">{reasoning}</p>
    <div className="mt-3 flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-gray-200 overflow-hidden">
        <div
          className="h-full rounded-full bg-emerald-400 transition-all duration-700"
          style={{ width: `${confidence_score}%` }}
        />
      </div>
      <span className="text-[10px] text-gray-400 font-medium shrink-0">{confidence_score}% confidence</span>
    </div>
  </div>
);

// --- Streaming mode component ---
interface StreamingResponseProps {
  state: StreamingState;
}

const StreamingDecisionView = ({ state }: StreamingResponseProps) => {
  const verdict = useTypewriter(
    state.final_decision?.verdict ?? "",
    20
  );

  return (
    <div className="space-y-4 w-full">
      {/* Thinking bar */}
      {!state.isDone && (
        <ThinkingBar
          status={state.status}
          agents_invoked={state.agents_invoked}
          active_agents={state.active_agents}
        />
      )}

      {/* Completed agent cards + skeleton for running ones */}
      {(state.agent_insights.length > 0 || state.active_agents.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {state.agent_insights.map((insight, i) => (
            <AgentCard
              key={insight.agent_name}
              insight={insight}
              style={{ animationDelay: `${i * 80}ms` }}
            />
          ))}
          {state.active_agents.map((a) => (
            <AgentCardSkeleton key={a} agentName={a} />
          ))}
        </div>
      )}

      {/* Perspectives */}
      {state.conservative_view && state.aggressive_view && (
        <PerspectivesPanel
          conservative={state.conservative_view}
          aggressive={state.aggressive_view}
        />
      )}

      {/* Final decision */}
      {state.final_decision && (
        <FinalDecisionPanel
          verdict={verdict || state.final_decision.verdict}
          reasoning={state.final_decision.reasoning}
          risk_level={state.final_decision.risk_level}
          confidence_score={state.final_decision.confidence_score}
          agentCount={state.agent_insights.length}
        />
      )}
    </div>
  );
};

// --- Static mode (loaded from history) ---
type Stage = "thinking" | "agents" | "perspectives" | "decision";

interface StaticResponseProps {
  data: AnalysisResponse;
  stage: Stage;
}

const StaticDecisionView = ({ data, stage }: StaticResponseProps) => {
  const showAgents = stage !== "thinking";
  const showPerspectives = stage === "perspectives" || stage === "decision";
  const showDecision = stage === "decision";
  const verdict = useTypewriter(showDecision ? data.final_decision.verdict : "", 20);

  return (
    <div className="space-y-4 w-full">
      <div className="flex flex-wrap gap-1.5 items-center">
        <span className="text-xs text-muted-foreground">Agents consulted:</span>
        {data.agents_invoked.map((a) => {
          const colors = AGENT_COLORS[a] || AGENT_COLORS.hr;
          return (
            <span key={a} className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium bg-gradient-to-r ${colors.gradient} text-white`}>
              <AgentAvatar agentName={a} size={12} />
              {a.replace("_", " ")}
            </span>
          );
        })}
      </div>

      {showAgents && data.agent_insights.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.agent_insights.map((insight, i) => (
            <AgentCard
              key={insight.agent_name}
              insight={insight}
              style={{ animationDelay: `${i * 100}ms` }}
            />
          ))}
        </div>
      )}

      {showPerspectives && (
        <PerspectivesPanel
          conservative={data.conservative_view}
          aggressive={data.aggressive_view}
        />
      )}

      {showDecision && (
        <FinalDecisionPanel
          verdict={verdict || data.final_decision.verdict}
          reasoning={data.final_decision.reasoning}
          risk_level={data.final_decision.risk_level}
          confidence_score={data.final_decision.confidence_score}
          agentCount={data.agent_insights.length}
        />
      )}
    </div>
  );
};

// --- Main export ---
interface DecisionResponseProps {
  data?: AnalysisResponse;
  stage?: Stage;
  streaming?: StreamingState;
}

export const DecisionResponse = ({ data, stage, streaming }: DecisionResponseProps) => {
  if (streaming) return <StreamingDecisionView state={streaming} />;
  if (data && stage) return <StaticDecisionView data={data} stage={stage} />;
  return null;
};
