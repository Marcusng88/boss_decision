import { useState } from "react";
import { Brain, FileText, Radar, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { InputPanel } from "@/components/decision/InputPanel";
import { DataRetrieved } from "@/components/decision/DataRetrieved";
import { AgentInsights } from "@/components/decision/AgentInsights";
import { SubagentViews } from "@/components/decision/SubagentViews";
import { FinalDecision } from "@/components/decision/FinalDecision";
import { SimulationLauncherCard } from "@/components/simulator/SimulationLauncherCard";
import { analyzeDecision, AnalysisResult } from "@/lib/decision-engine";

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

  const handleAnalyze = async (query: string) => {
    setActiveQuery(query);
    const r = await analyzeDecision(query, { allowMockFallback: true });
    setResult(r);
    setStage("data");
    setTimeout(() => setStage("agents"), 1100);
    setTimeout(() => setStage("subagents"), 2400);
    setTimeout(() => setStage("decision"), 3700);
  };

  const showAny = stage !== "idle" && result;

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -left-28 top-24 h-72 w-72 rounded-full bg-accent/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-12 h-80 w-80 rounded-full bg-primary/20 blur-3xl" />

      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="container max-w-7xl py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl leading-none text-foreground">
                Boardroom Atlas
              </h1>
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                Strategic Intelligence Console
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/documents")}
              className="bg-card text-foreground border-border hover:bg-accent/50"
            >
              <FileText className="w-4 h-4 mr-2" />
              Documents
            </Button>
            <div className="hidden md:flex items-center gap-2 rounded-full border border-border bg-card/70 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              Runtime online
            </div>
          </div>
        </div>
      </header>

      <main className="container max-w-7xl py-8">
        <section className="relative mb-8 overflow-hidden rounded-[2rem] border border-border bg-card/70 p-6 shadow-card md:p-8">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_0%,hsl(var(--primary)/0.16),transparent_38%),radial-gradient(circle_at_90%_20%,hsl(var(--accent)/0.14),transparent_34%)]" />
          <div className="relative flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div className="max-w-2xl">
              <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                Decision Intelligence
              </p>
              <h2 className="text-4xl leading-tight text-foreground md:text-5xl">
                Run fast, transparent multi-agent debates for high-stakes calls.
              </h2>
              <p className="mt-3 text-sm text-muted-foreground md:text-base">
                Start with a leadership prompt, inspect each specialist perspective, then open all three simulators
                in one continuous page.
              </p>
            </div>
            <div className="grid w-full max-w-sm grid-cols-2 gap-3 text-sm md:text-base">
              <div className="rounded-2xl border border-border bg-background/70 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Pipelines</p>
                <p className="mt-1 flex items-center gap-2 font-semibold text-foreground">
                  <Radar className="h-4 w-4 text-primary" />
                  Decision + 3 Simulators
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-background/70 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Mode</p>
                <p className="mt-1 font-semibold text-foreground">Unified Live Page</p>
              </div>
            </div>
          </div>
        </section>

        <div className="grid lg:grid-cols-[350px_1fr] gap-6">
          <InputPanel onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />

          <div className="space-y-5 min-w-0">
            {!showAny && (
              <div className="rounded-[1.6rem] border border-dashed border-border bg-card/65 p-12 text-center">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow mb-4">
                  <Brain className="w-7 h-7 text-primary-foreground" />
                </div>
                <h2 className="text-4xl text-foreground mb-2">
                  Ready to reason
                </h2>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Enter a strategic question on the left. The engine will pull signals, consult specialist agents,
                  debate options, and deliver a final recommendation.
                </p>
              </div>
            )}

            {showAny && (
              <>
                <div className="rounded-2xl bg-card/80 border border-border px-5 py-4 shadow-card animate-fade-in-up">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-[0.18em] mb-1">
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

        <div className="mt-12">
          <SimulationLauncherCard query={activeQuery} />
        </div>
      </main>
    </div>
  );
};

export default Index;
