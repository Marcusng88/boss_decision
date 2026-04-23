import { ArrowUpRight, Brain, ChevronLeft, Package, ShieldCheck, Truck } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const SUPPLY_CHAIN_SIMULATION_QUERY =
  "How can we reduce supply chain risk and shorten lead times without increasing total landed cost?";

const SupplyChainAgent = () => {
  const supplyChainSimulationHref = `/simulation-live?query=${encodeURIComponent(SUPPLY_CHAIN_SIMULATION_QUERY)}`;

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_10%_2%,rgba(23,162,155,0.2),transparent_38%),radial-gradient(circle_at_90%_8%,rgba(56,189,248,0.14),transparent_36%),linear-gradient(180deg,rgba(240,250,250,0.98),rgba(233,245,244,0.98))]">
      <div className="pointer-events-none absolute -left-24 top-12 h-72 w-72 rounded-full bg-accent/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-20 h-80 w-80 rounded-full bg-primary/15 blur-3xl" />

      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="container max-w-7xl py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl leading-none text-foreground">Supply Chain Agent</h1>
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Operations Risk Workspace</p>
            </div>
          </div>
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card/70 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-foreground hover:bg-card"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back to Landing
          </Link>
        </div>
      </header>

      <main className="container max-w-7xl py-10">
        <section className="relative overflow-hidden rounded-[2rem] border border-border bg-card/75 p-6 shadow-card md:p-8">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_8%_0%,hsl(var(--accent)/0.2),transparent_34%)]" />
          <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/75 px-3 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                <Truck className="h-3.5 w-3.5 text-primary" />
                Logistics Intelligence
              </p>
              <h2 className="mt-4 text-4xl leading-tight text-foreground md:text-5xl">
                Stress-test your operations before disruptions become losses.
              </h2>
              <p className="mt-3 max-w-2xl text-sm text-muted-foreground md:text-base">
                This workspace focuses on lead-time reliability, supplier resilience, and inventory posture.
                Move into a live simulation to pressure-test contingency plans end to end.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button asChild className="h-11 border border-primary/30 bg-primary px-5 text-primary-foreground hover:bg-primary/90">
                  <Link to={supplyChainSimulationHref}>
                    Launch Supply Chain Simulation
                    <ArrowUpRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" className="h-11 border-border bg-background/80 px-5">
                  <Link to="/">Return to Boardroom Atlas</Link>
                </Button>
              </div>
            </div>

            <div className="grid gap-3">
              <div className="rounded-2xl border border-border bg-background/70 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Transport Reliability</p>
                <p className="mt-1 flex items-center gap-2 text-base font-semibold text-foreground">
                  <Truck className="h-4 w-4 text-primary" />
                  Route and carrier variability
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-background/70 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Inventory Posture</p>
                <p className="mt-1 flex items-center gap-2 text-base font-semibold text-foreground">
                  <Package className="h-4 w-4 text-primary" />
                  Safety stock and stockout risk
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-background/70 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Supplier Health</p>
                <p className="mt-1 flex items-center gap-2 text-base font-semibold text-foreground">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  Multi-source resilience checks
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default SupplyChainAgent;
