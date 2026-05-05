import { ArrowUpRight, Brain, FileText, Radar, Sparkles, TrendingUp, Truck } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { SimulationLauncherCard } from "@/components/simulator/SimulationLauncherCard";

const Index = () => {
  const navigate = useNavigate();
  const activeQuery = "";

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -left-28 top-24 h-72 w-72 rounded-full bg-accent/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-12 h-80 w-80 rounded-full bg-primary/20 blur-3xl" />

      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="w-full max-w-[95%] mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
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

      <main className="w-full max-w-[95%] mx-auto px-4 sm:px-6 py-8">
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

        <section className="mb-8 grid gap-4 md:grid-cols-2">
          <Link
            to="/agents/sales"
            className="group relative overflow-hidden rounded-[1.6rem] border border-border bg-card/80 p-5 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-primary/40"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_90%_5%,hsl(var(--primary)/0.18),transparent_32%)] opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <div className="relative">
              <p className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/80 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                <TrendingUp className="h-3.5 w-3.5 text-primary" />
                Sales Agent
              </p>
              <h3 className="mt-4 text-2xl leading-tight text-foreground">Revenue command center</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Explore pipeline health, conversion pressure, and deal velocity with a specialist sales lens.
              </p>
              <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                Open Sales Agent
                <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
            </div>
          </Link>

          <Link
            to="/agents/supply-chain"
            className="group relative overflow-hidden rounded-[1.6rem] border border-border bg-card/80 p-5 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-accent/50"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_0%,hsl(var(--accent)/0.18),transparent_34%)] opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <div className="relative">
              <p className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/80 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                <Truck className="h-3.5 w-3.5 text-accent-foreground" />
                Supply Chain Agent
              </p>
              <h3 className="mt-4 text-2xl leading-tight text-foreground">Operational resilience cockpit</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Review lead-time volatility, supplier risk, and inventory balance before operations decisions.
              </p>
              <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-foreground">
                Open Supply Chain Agent
                <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
            </div>
          </Link>
        </section>

        <div className="mt-12">
          <SimulationLauncherCard query={activeQuery} />
        </div>
      </main>
    </div>
  );
};

export default Index;


