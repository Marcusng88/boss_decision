import { useState } from "react";
import { Brain, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { InputPanel } from "@/components/decision/InputPanel";
import { DataRetrieved } from "@/components/decision/DataRetrieved";
import { AgentInsights } from "@/components/decision/AgentInsights";
import { SubagentViews } from "@/components/decision/SubagentViews";
import { FinalDecision } from "@/components/decision/FinalDecision";
import { analyze, AnalysisResult } from "@/lib/decision-engine";

type Stage = "idle" | "data" | "agents" | "subagents" | "decision";

const stageOrder: Stage[] = ["data", "agents", "subagents", "decision"];

const Index = () => {
  const navigate = useNavigate();
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeQuery, setActiveQuery] = useState<string>("");

  const isAnalyzing = stage !== "idle" && stage !== "decision";

  const stageStatus = (s: Stage): "pending" | "loading" | "done" => {
    if (stage === "idle") return "pending";
    const currentIdx = stageOrder.indexOf(stage);
    const targetIdx = stageOrder.indexOf(s);
    if (targetIdx < currentIdx) return "done";
    if (targetIdx === currentIdx) return stage === "decision" ? "done" : "loading";
    return "pending";
  };

  const handleAnalyze = (query: string) => {
    setActiveQuery(query);
    const r = analyze(query);
    setResult(r);
    setStage("data");
    setTimeout(() => setStage("agents"), 1100);
    setTimeout(() => setStage("subagents"), 2400);
    setTimeout(() => setStage("decision"), 3700);
  };

  const showAny = stage !== "idle" && result;

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <header className="border-b border-border bg-card/60 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-7xl py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground leading-tight">
                AI Decision Engine
              </h1>
              <p className="text-xs text-muted-foreground">
                Multi-agent reasoning for company decisions
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/documents")}
              className="bg-gradient-to-r from-orange-400 to-orange-600 text-white border-0 hover:from-orange-500 hover:to-orange-700 shadow-md"
            >
              <FileText className="w-4 h-4 mr-2" />
              Documents
            </Button>
            <div className="hidden md:flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              Engine online
            </div>
          </div>
        </div>
      </header>

      <main className="container max-w-7xl py-8">
        <div className="grid lg:grid-cols-[360px_1fr] gap-6">
          <InputPanel onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />

          <div className="space-y-5 min-w-0">
            {!showAny && (
              <div className="rounded-2xl border-2 border-dashed border-border bg-card/40 p-12 text-center">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow mb-4">
                  <Brain className="w-7 h-7 text-primary-foreground" />
                </div>
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  Ready to reason
                </h2>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Enter a strategic question on the left. The engine will pull data, consult specialist agents, debate perspectives, and deliver a decision.
                </p>
              </div>
            )}

            {showAny && (
              <>
                <div className="rounded-xl bg-card border border-border px-4 py-3 shadow-card animate-fade-in-up">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                    Query
                  </p>
                  <p className="text-base font-medium text-foreground">"{activeQuery}"</p>
                </div>

                <DataRetrieved status={stageStatus("data")} items={result!.data} />
                <AgentInsights status={stageStatus("agents")} agents={result!.agents} />
                <SubagentViews status={stageStatus("subagents")} views={result!.subagents} />

                {stage === "decision" && <FinalDecision decision={result!.decision} />}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
