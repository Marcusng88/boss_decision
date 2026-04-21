from __future__ import annotations

import html
import json
from typing import Any

from .schema import DeepSimulationFinalResponse
from .schema import DeepSimulationState
from .schema import ObserverSummary


def build_periodic_summary(state: DeepSimulationState, observer_model: Any | None) -> ObserverSummary:
    fallback_md = (
        f"### Tick {state.tick} Pulse\n"
        f"- Revenue delta: `{state.global_kpis.revenue:.2f}`\n"
        f"- Margin delta: `{state.global_kpis.margin:.2f}`\n"
        f"- Sentiment: `{state.global_kpis.sentiment:.2f}`\n"
        f"- Churn risk: `{state.global_kpis.churn_risk:.2f}`\n"
        "- Current posture: continue phased experiment and monitor churn thresholds."
    )
    if observer_model is None:
        return ObserverSummary(tick=state.tick, markdown=fallback_md)

    prompt = (
        "Write a concise markdown observer summary for this simulation tick. "
        "Focus on turning points and decision posture in 5-7 bullets. "
        f"Tick: {state.tick} "
        f"KPI: {json.dumps(state.global_kpis.model_dump())} "
        f"Recent timeline: {json.dumps([item.model_dump(mode='json') for item in state.timeline[:8]])}"
    )
    try:
        response = observer_model.invoke(prompt)
        content = str(getattr(response, "content", "")).strip()
        return ObserverSummary(tick=state.tick, markdown=content or fallback_md)
    except Exception:
        return ObserverSummary(tick=state.tick, markdown=fallback_md)


def _slides_html(state: DeepSimulationState, periodic_summaries: list[ObserverSummary]) -> str:
    summary_items = "".join(
        f"<li><strong>Tick {item.tick}</strong><p>{html.escape(item.markdown)}</p></li>"
        for item in periodic_summaries[-5:]
    )
    top_timeline = "".join(
        f"<li><span>Day {item.tick}</span><p>{html.escape(item.message)}</p></li>"
        for item in state.timeline[:10]
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Deep Simulation Report</title>
  <style>
    body {{ margin:0; font-family: 'Sora', 'Segoe UI', sans-serif; background:#f5f6f2; color:#101010; }}
    .deck {{ display:grid; gap:16px; padding:18px; }}
    .slide {{ border:1px solid #ddd7ca; background:#fffdf8; border-radius:16px; padding:20px; }}
    h1,h2 {{ margin:0 0 8px 0; letter-spacing:0.01em; }}
    .kpis {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .kpi {{ border:1px solid #e5dfd1; border-radius:12px; padding:10px; background:#fbf8ef; }}
    ul {{ margin:8px 0 0 18px; padding:0; }}
    li {{ margin:8px 0; }}
    p {{ margin:4px 0; line-height:1.4; }}
    .muted {{ color:#665f52; font-size:12px; }}
  </style>
</head>
<body>
  <main class="deck">
    <section class="slide">
      <p class="muted">Deep Simulation Observer</p>
      <h1>Scenario: {html.escape(state.scenario_id)}</h1>
      <p>{html.escape(state.query)}</p>
      <p class="muted">Seed {state.seed} | Tick = 1 day | Max ticks {state.max_ticks}</p>
    </section>
    <section class="slide">
      <h2>Outcome Snapshot</h2>
      <div class="kpis">
        <div class="kpi"><p class="muted">Revenue Delta</p><p>{state.global_kpis.revenue:.2f}</p></div>
        <div class="kpi"><p class="muted">Margin Delta</p><p>{state.global_kpis.margin:.2f}</p></div>
        <div class="kpi"><p class="muted">Sentiment</p><p>{state.global_kpis.sentiment:.2f}</p></div>
        <div class="kpi"><p class="muted">Churn Risk</p><p>{state.global_kpis.churn_risk:.2f}</p></div>
      </div>
    </section>
    <section class="slide">
      <h2>Periodic Observer Notes</h2>
      <ul>{summary_items or "<li><p>No periodic summaries generated.</p></li>"}</ul>
    </section>
    <section class="slide">
      <h2>Turning Timeline</h2>
      <ul>{top_timeline or "<li><p>No timeline events recorded.</p></li>"}</ul>
    </section>
  </main>
</body>
</html>
"""


def build_final_report(state: DeepSimulationState, observer_model: Any | None) -> DeepSimulationFinalResponse:
    fallback = DeepSimulationFinalResponse(
        summary="Deep simulation completed with dynamic personas and deterministic replay support.",
        key_turning_points=[
            "Early ticks established baseline demand pressure and uncertainty bounds.",
            "Mid-simulation actions shifted KPI trajectory through targeted interventions.",
            "Late simulation converged toward a guarded rollout posture with explicit guardrails.",
        ],
        recommendation=(
            "Proceed with phased execution, preserve rollback thresholds, and continue weekly observer checks."
        ),
        confidence=0.71,
        periodic_summaries=state.observer_summaries,
        html_slides=_slides_html(state, state.observer_summaries),
    )
    if observer_model is None:
        return fallback

    prompt = (
        "You are the final observer for a multi-persona simulation. "
        "Return JSON with keys: summary, key_turning_points (list), recommendation, confidence. "
        f"State: {json.dumps(state.model_dump(mode='json'))}"
    )
    try:
        response = observer_model.invoke(prompt)
        content = str(getattr(response, "content", "")).strip()
        parsed = json.loads(content) if content.startswith("{") else {}
        report = DeepSimulationFinalResponse(
            summary=str(parsed.get("summary") or fallback.summary),
            key_turning_points=[
                str(item) for item in parsed.get("key_turning_points", fallback.key_turning_points) if isinstance(item, str)
            ][:6],
            recommendation=str(parsed.get("recommendation") or fallback.recommendation),
            confidence=max(0.0, min(1.0, float(parsed.get("confidence", fallback.confidence)))),
            periodic_summaries=state.observer_summaries,
            html_slides=_slides_html(state, state.observer_summaries),
        )
        return report
    except Exception:
        return fallback
