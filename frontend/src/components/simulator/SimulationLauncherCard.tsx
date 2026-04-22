import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Clock3, Network, Orbit, Spline } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface SimulationLauncherCardProps {
  query?: string;
}

interface LastRunSummary {
  query: string;
  recommendation?: string;
  status: "ok" | "error";
  completedAt: string;
}

const STORAGE_KEY = "simulator:last-run";

function readLastRun(): LastRunSummary | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LastRunSummary;
    if (!parsed || typeof parsed !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

export function SimulationLauncherCard({ query }: SimulationLauncherCardProps) {
  const [lastRun, setLastRun] = useState<LastRunSummary | null>(null);

  useEffect(() => {
    setLastRun(readLastRun());
    const onStorage = () => setLastRun(readLastRun());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const launchHref = useMemo(() => {
    const trimmed = query?.trim();
    if (!trimmed) return "/simulation-live";
    return `/simulation-live?query=${encodeURIComponent(trimmed)}`;
  }, [query]);

  return (
    <section className="rounded-[1.6rem] border border-border bg-card/75 p-6 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Simulation</p>
          <h3 className="mt-1 text-3xl leading-none text-foreground">Open Live Console</h3>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Run realtime simulation in a dedicated workspace with streaming updates.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild className="h-11 border border-primary/30 bg-primary px-5 text-primary-foreground hover:bg-primary/90">
            <Link to={launchHref} target="_blank" rel="noreferrer">
              <Orbit className="mr-2 h-4 w-4" />
              Open Classic Simulation
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" className="h-11 border border-border bg-card px-5 text-foreground hover:bg-card/80">
            <Link to="/simulation-deep" target="_blank" rel="noreferrer">
              <Spline className="mr-2 h-4 w-4" />
              Open Deep 2D Arena
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" className="h-11 border border-border bg-card px-5 text-foreground hover:bg-card/80">
            <Link to="/simulation-network" target="_blank" rel="noreferrer">
              <Network className="mr-2 h-4 w-4" />
              Open Network Lab
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-border bg-background/70 p-4">
        <p className="mb-2 inline-flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
          <Clock3 className="h-3.5 w-3.5" />
          Last Run Snapshot
        </p>
        {!lastRun && <p className="text-sm text-muted-foreground">No simulation run recorded yet.</p>}
        {lastRun && (
          <div className="space-y-2 text-sm">
            <p className="text-foreground">
              <span className="text-muted-foreground">Status:</span> {lastRun.status === "ok" ? "Completed" : "Error"}
            </p>
            <p className="text-foreground">
              <span className="text-muted-foreground">Query:</span> {lastRun.query}
            </p>
            {lastRun.recommendation && (
              <p className="text-foreground">
                <span className="text-muted-foreground">Recommendation:</span> {lastRun.recommendation}
              </p>
            )}
            <p className="text-muted-foreground">
              {new Date(lastRun.completedAt).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
