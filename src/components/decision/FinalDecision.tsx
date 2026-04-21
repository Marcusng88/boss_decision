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
    <section className="relative rounded-2xl bg-gradient-decision text-primary-foreground p-8 shadow-elevated animate-scale-in overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_hsl(var(--primary-glow)/0.4),_transparent_60%)]" />

      <div className="relative">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle2 className="w-5 h-5" />
          <span className="text-xs font-bold uppercase tracking-widest opacity-90">
            Final Decision
          </span>
        </div>

        <h2 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
          {decision.verdict}
        </h2>

        <p className="text-base md:text-lg opacity-95 mb-6 max-w-2xl leading-relaxed">
          {decision.reasoning}
        </p>

        <div className="grid sm:grid-cols-2 gap-3">
          <div className={`rounded-xl border bg-background/95 p-4 ${riskColor.replace("text-", "").split(" ")[0]}`}>
            <div className="flex items-center gap-2 text-foreground/70 text-xs font-semibold uppercase tracking-wide mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              Risk Level
            </div>
            <div className={`inline-flex items-center px-3 py-1 rounded-full border text-sm font-bold ${riskColor}`}>
              {decision.risk}
            </div>
          </div>

          <div className="rounded-xl bg-background/95 p-4">
            <div className="flex items-center gap-2 text-foreground/70 text-xs font-semibold uppercase tracking-wide mb-2">
              <Gauge className="w-3.5 h-3.5" />
              Confidence
            </div>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-foreground">{decision.confidence}%</span>
              <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-primary rounded-full transition-all duration-1000"
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
