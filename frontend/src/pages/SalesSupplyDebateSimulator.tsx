import { FormEvent, useState } from "react";
import { AlertTriangle, ArrowRight, Brain, ChevronLeft, Loader2, MessageSquareText, ShieldCheck, ShieldX } from "lucide-react";
import { Link } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { runSalesSupplyDebateSimulation, SalesSupplyDebateResponse } from "@/lib/sales-supply-debate-client";

const SalesSupplyDebateSimulator = () => {
  const [itemName, setItemName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SalesSupplyDebateResponse | null>(null);

  const handleRun = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = await runSalesSupplyDebateSimulation({
        item_name: itemName.trim() || undefined,
        max_rounds: 5,
      });
      setResult(payload);
    } catch (requestError) {
      setResult(null);
      setError(requestError instanceof Error ? requestError.message : "Failed to run debate simulator.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_12%_0%,rgba(28,87,161,0.18),transparent_36%),radial-gradient(circle_at_84%_9%,rgba(11,122,101,0.14),transparent_34%),linear-gradient(180deg,rgba(242,246,250,0.98),rgba(234,240,245,0.98))]">
      <div className="pointer-events-none absolute -left-24 top-12 h-72 w-72 rounded-full bg-primary/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-16 h-80 w-80 rounded-full bg-accent/20 blur-3xl" />

      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="container max-w-7xl py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl leading-none text-foreground">Sales vs Supply Debate Simulator</h1>
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">AI-1 Sales Agent and AI-2 Supply Chain Agent</p>
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

      <main className="container max-w-7xl py-10 space-y-6">
        <Card className="border-border/80 bg-card/85">
          <CardHeader>
            <CardTitle className="text-2xl">Debate Runner</CardTitle>
            <CardDescription>
              The simulator reads `supply_record.item_name`, sends item context to Sales AI, then starts a debate loop where Supply Chain AI approves or rejects until a final decision is reached.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-4" onSubmit={handleRun}>
              <div className="md:col-span-2 space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground" htmlFor="item-name-input">
                  Item Name Filter (optional)
                </label>
                <Input
                  id="item-name-input"
                  value={itemName}
                  onChange={(event) => setItemName(event.target.value)}
                  placeholder="Example: Running shoes"
                />
              </div>
              <div className="md:col-span-2 space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground" htmlFor="max-rounds-input">
                  Debate Rounds (Fixed)
                </label>
                <Input
                  id="max-rounds-input"
                  type="number"
                  value={5}
                  disabled
                />
              </div>
              <div className="md:col-span-4 flex justify-end">
                <Button type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Running Debate
                    </>
                  ) : (
                    <>
                      <MessageSquareText className="mr-2 h-4 w-4" />
                      Start Simulation
                    </>
                  )}
                </Button>
              </div>
            </form>
            <p className="mt-3 text-xs text-muted-foreground">
              Item retrieval is fixed to 1 record and debate is fixed to 5 rounds per simulation run.
            </p>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Simulation failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <div className="space-y-4">
            <Card className="bg-card/85">
              <CardHeader>
                <CardTitle className="text-xl">Retrieval and Outcome Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p><span className="font-semibold">Status:</span> {result.status}</p>
                <p><span className="font-semibold">Retrieved item_name values:</span> {result.retrieved_item_names.join(", ") || "-"}</p>
                {result.summary && (
                  <p>
                    <span className="font-semibold">Result:</span> {result.summary.approved} approved / {result.summary.rejected} rejected (total {result.summary.total_items})
                  </p>
                )}
                {result.message && <p className="text-muted-foreground">{result.message}</p>}
              </CardContent>
            </Card>

            {result.simulations.map((session) => (
              <Card key={`${session.supply_id}-${session.item_name}`} className="bg-card/85">
                <CardHeader>
                  <CardTitle className="text-lg">
                    Supply #{session.supply_id} - {session.item_name}
                  </CardTitle>
                  <CardDescription>
                    Inventory {session.inventory_context.inventory_level ?? "-"} | Forecast {session.inventory_context.demand_forecast ?? "-"} | Reorder {session.inventory_context.reorder_point ?? "-"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {session.judge_result && (
                    <Alert>
                      <ShieldCheck className="h-4 w-4" />
                      <AlertTitle>
                        Judge (AI-3): {session.judge_result.winner === "sales" ? "Follow Sales Agent" : "Follow Supply Chain Agent"}
                      </AlertTitle>
                      <AlertDescription>
                        {session.judge_result.rationale} (confidence {Math.round((session.judge_result.confidence ?? 0) * 100)}%)
                      </AlertDescription>
                    </Alert>
                  )}

                  {session.rounds.map((debateRound) => (
                    <div key={`${session.supply_id}-round-${debateRound.round}`} className="rounded-xl border border-border bg-background/70 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">Round {debateRound.round}</p>
                      <div className="mt-2 grid gap-2 md:grid-cols-[1fr_auto_1fr] md:items-start">
                        <div className="rounded-lg border border-border bg-card/80 p-3 text-sm">
                          <p className="font-semibold text-foreground">{debateRound.sales_agent.role} ({debateRound.sales_agent.agent_id})</p>
                          <p className="mt-1 text-foreground">{debateRound.sales_agent.suggestion}</p>
                          {debateRound.sales_agent.market_signal && (
                            <p className="mt-2 text-xs text-muted-foreground">
                              Market signal: {debateRound.sales_agent.market_signal}
                            </p>
                          )}
                        </div>
                        <div className="hidden md:flex items-center justify-center pt-5">
                          <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="rounded-lg border border-border bg-card/80 p-3 text-sm">
                          <p className="font-semibold text-foreground">{debateRound.supply_chain_agent.role} ({debateRound.supply_chain_agent.agent_id})</p>
                          <div className="mt-1">
                            {debateRound.supply_chain_agent.validity === "valid" ? (
                              <Badge className="border border-success/40 bg-success/10 text-foreground">
                                <ShieldCheck className="mr-1 h-3 w-3" />
                                Valid
                              </Badge>
                            ) : (
                              <Badge className="border border-destructive/40 bg-destructive/10 text-foreground">
                                <ShieldX className="mr-1 h-3 w-3" />
                                Invalid
                              </Badge>
                            )}
                          </div>
                          {debateRound.supply_chain_agent.strict_checks?.length > 0 && (
                            <div className="mt-2 space-y-1">
                              {debateRound.supply_chain_agent.strict_checks.slice(0, 3).map((check, idx) => (
                                <p key={`${debateRound.round}-check-${idx}`} className="text-xs text-muted-foreground">
                                  • {check}
                                </p>
                              ))}
                            </div>
                          )}
                          <p className="mt-2 text-foreground">{debateRound.supply_chain_agent.response}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  <Alert variant={session.final_result.status === "approved" ? "default" : "destructive"}>
                    {session.final_result.status === "approved" ? <ShieldCheck className="h-4 w-4" /> : <ShieldX className="h-4 w-4" />}
                    <AlertTitle>{session.final_result.status === "approved" ? "Final: Approved" : "Final: Rejected"}</AlertTitle>
                    <AlertDescription>{session.final_result.conclusion}</AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default SalesSupplyDebateSimulator;
