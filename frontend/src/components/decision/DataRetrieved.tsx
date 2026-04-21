import { Database } from "lucide-react";
import { StageCard } from "./StageCard";
import { DataItem } from "@/lib/decision-engine";

interface Props {
  status: "pending" | "loading" | "done";
  items: DataItem[];
}

export const DataRetrieved = ({ status, items }: Props) => {
  return (
    <StageCard
      icon={<Database className="w-5 h-5" />}
      title="Data Retrieved"
      subtitle="Cross-system signals pulled in real time"
      status={status}
    >
      <div className="grid sm:grid-cols-3 gap-3">
        {items.map((item, i) => (
          <div
            key={item.source}
            className="rounded-xl border border-border bg-background p-4 animate-fade-in-up"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {item.source}
              </span>
              <span
                className={
                  item.trend === "down"
                    ? "text-destructive text-xs font-medium"
                    : item.trend === "up"
                      ? "text-success text-xs font-medium"
                      : "text-muted-foreground text-xs font-medium"
                }
              >
                {item.trend === "down" ? "▼" : item.trend === "up" ? "▲" : "■"}
              </span>
            </div>
            <p className="text-base font-semibold text-foreground">{item.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
          </div>
        ))}
      </div>
    </StageCard>
  );
};
