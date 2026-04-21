import { ReactNode } from "react";
import { Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface StageCardProps {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  status: "pending" | "loading" | "done";
  children?: ReactNode;
  accent?: "primary" | "accent" | "warning";
}

export const StageCard = ({
  icon,
  title,
  subtitle,
  status,
  children,
  accent = "primary",
}: StageCardProps) => {
  if (status === "pending") return null;

  const accentRing = {
    primary: "ring-primary/20",
    accent: "ring-accent/20",
    warning: "ring-warning/20",
  }[accent];

  return (
    <section
      className={cn(
        "bg-card rounded-2xl border border-border shadow-card p-6 animate-fade-in-up",
        "ring-1",
        accentRing,
      )}
    >
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center text-primary">
            {icon}
          </div>
          <div>
            <h3 className="text-base font-semibold text-foreground leading-tight">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        <div>
          {status === "loading" ? (
            <div className="flex items-center gap-1.5 text-xs font-medium text-primary px-2.5 py-1 rounded-full bg-primary/10">
              <Loader2 className="w-3 h-3 animate-spin" />
              Working
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs font-medium text-success px-2.5 py-1 rounded-full bg-success/10">
              <Check className="w-3 h-3" />
              Done
            </div>
          )}
        </div>
      </header>

      {status === "done" && <div className="space-y-3">{children}</div>}
      {status === "loading" && (
        <div className="space-y-2">
          <div className="h-3 bg-secondary rounded animate-pulse-glow w-3/4" />
          <div className="h-3 bg-secondary rounded animate-pulse-glow w-1/2" />
        </div>
      )}
    </section>
  );
};
