
import { useState, useEffect } from "react";
import { Shield, Flame, CheckCircle2 } from "lucide-react";
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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in-up">
          <div className="rounded-2xl border border-blue-200 bg-blue-50/60 p-4 backdrop-blur-sm">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">Conservative</span>
            </div>
            <p className="text-sm font-semibold text-gray-800 mb-1.5">
              {state.conservative_view.recommendation}
            </p>
            <p className="text-xs text-gray-600 leading-relaxed">
              {state.conservative_view.reasoning}
            </p>
          </div>
          <div className="rounded-2xl border border-orange-200 bg-orange-50/60 p-4 backdrop-blur-sm">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-4 h-4 text-orange-600" />
              <span className="text-xs font-bold text-orange-700 uppercase tracking-wider">Aggressive</span>
            </div>
            <p className="text-sm font-semibold text-gray-800 mb-1.5">
              {state.aggressive_view.recommendation}
            </p>
            <p className="text-xs text-gray-600 leading-relaxed">
              {state.aggressive_view.reasoning}
            </p>
          </div>
        </div>
      )}

      {/* Final decision */}
      {state.final_decision && (
        <div className="rounded-2xl bg-gradient-to-br from-slate-800 via-blue-900 to-violet-900 p-5 text-white animate-fade-in-up shadow-xl">
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-widest">Final Decision</span>
          </div>
          <h3 className="text-lg font-black tracking-tight mb-2 leading-tight">
            {verdict || state.final_decision.verdict}
          </h3>
          <p className="text-sm opacity-85 leading-relaxed mb-4">
            {state.final_decision.reasoning}
          </p>
          <div className="flex items-center gap-5 pt-3 border-t border-white/20">
            <div>
              <p className="text-[10px] opacity-50 mb-1 uppercase tracking-wide">Risk Level</p>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${riskBadge(state.final_decision.risk_level)}`}>
                {state.final_decision.risk_level}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <p className="text-[10px] opacity-50 uppercase tracking-wide">Confidence</p>
                <span className="text-xs font-bold opacity-90">{state.final_decision.confidence_score}%</span>
              </div>
              <div className="h-2 rounded-full bg-white/15 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-300 to-violet-300 transition-all duration-1000"
                  style={{ width: `${state.final_decision.confidence_score}%` }}
                />
              </div>
            </div>
          </div>
        </div>
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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in-up">
          <div className="rounded-2xl border border-blue-200 bg-blue-50/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">Conservative</span>
            </div>
            <p className="text-sm font-semibold text-gray-800 mb-1.5">{data.conservative_view.recommendation}</p>
            <p className="text-xs text-gray-600 leading-relaxed">{data.conservative_view.reasoning}</p>
          </div>
          <div className="rounded-2xl border border-orange-200 bg-orange-50/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-4 h-4 text-orange-600" />
              <span className="text-xs font-bold text-orange-700 uppercase tracking-wider">Aggressive</span>
            </div>
            <p className="text-sm font-semibold text-gray-800 mb-1.5">{data.aggressive_view.recommendation}</p>
            <p className="text-xs text-gray-600 leading-relaxed">{data.aggressive_view.reasoning}</p>
          </div>
        </div>
      )}

      {showDecision && (
        <div className="rounded-2xl bg-gradient-to-br from-slate-800 via-blue-900 to-violet-900 p-5 text-white animate-fade-in-up shadow-xl">
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-widest">Final Decision</span>
          </div>
          <h3 className="text-lg font-black tracking-tight mb-2">{verdict || data.final_decision.verdict}</h3>
          <p className="text-sm opacity-85 leading-relaxed mb-4">{data.final_decision.reasoning}</p>
          <div className="flex items-center gap-5 pt-3 border-t border-white/20">
            <div>
              <p className="text-[10px] opacity-50 mb-1 uppercase tracking-wide">Risk Level</p>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${riskBadge(data.final_decision.risk_level)}`}>
                {data.final_decision.risk_level}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <p className="text-[10px] opacity-50 uppercase tracking-wide">Confidence</p>
                <span className="text-xs font-bold opacity-90">{data.final_decision.confidence_score}%</span>
              </div>
              <div className="h-2 rounded-full bg-white/15 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-300 to-violet-300 transition-all duration-1000"
                  style={{ width: `${data.final_decision.confidence_score}%` }}
                />
              </div>
            </div>
          </div>
        </div>
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
