import { CheckCircle2, AlertTriangle, Gauge } from "lucide-react";
import { Decision } from "@/lib/decision-engine";

interface Props {
  decision: Decision;
}

export const FinalDecision = ({ decision }: Props) => {
  const riskColor = {
    Low: "text-success bg-success/10 border-success/20",
    Medium: "text-warning bg-warning/10 border-warning/20",
    High: "text-destructive bg-destructive/10 border-destructive/20",
  }[decision.risk];

  return (
    <section className="relative overflow-hidden rounded-[1.8rem] bg-gradient-decision p-8 text-primary-foreground shadow-elevated animate-scale-in">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_hsl(var(--primary-glow)/0.25),_transparent_60%)]" />

      <div className="relative">
        <div className="mb-3 flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-[0.18em] opacity-90">Final Decision</span>
        </div>

        <h2 className="mb-4 text-5xl leading-[0.95] md:text-6xl">{decision.verdict}</h2>

        <p className="mb-6 max-w-2xl text-base leading-relaxed opacity-95 md:text-lg">{decision.reasoning}</p>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-primary-foreground/25 bg-background/95 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-foreground/70">
              <AlertTriangle className="h-3.5 w-3.5" />
              Risk Level
            </div>
            <div className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-bold ${riskColor}`}>
              {decision.risk}
            </div>
          </div>

          <div className="rounded-xl border border-primary-foreground/25 bg-background/95 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-foreground/70">
              <Gauge className="h-3.5 w-3.5" />
              Confidence
            </div>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-foreground">{decision.confidence}%</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-gradient-primary transition-all duration-1000"
                  style={{ width: `${decision.confidence}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
