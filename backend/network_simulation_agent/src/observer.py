from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .memory import get_run_dir
from .memory import read_events

FINAL_REPORT_FILENAME = "final_report.json"
OBSERVER_SUMMARY_FILENAME = "observer_summary.md"
GRAPH_SNAPSHOT_FILENAME = "graph_snapshot.json"


def persist_run_artifacts(
    base_dir: Path,
    session_id: str,
    query: str,
    summary: str,
    kpis: dict[str, float],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    """Persist replayable observer artifacts for a completed session.

    Args:
        base_dir: Root path for the `network_simulation_agent` package.
        session_id: Session identifier.
        query: Original user scenario.
        summary: Final observer summary text.
        kpis: Final KPI deltas dictionary.
        nodes: Final node state list.
        edges: Final edge state list.
    """
    run_dir = get_run_dir(base_dir, session_id)
    final_report = {
        "session_id": session_id,
        "query": query,
        "summary": summary,
        "kpis": kpis,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    (run_dir / FINAL_REPORT_FILENAME).write_text(json.dumps(final_report, indent=2), encoding="utf-8")
    (run_dir / OBSERVER_SUMMARY_FILENAME).write_text(summary, encoding="utf-8")
    graph_snapshot = {"session_id": session_id, "nodes": nodes, "edges": edges}
    (run_dir / GRAPH_SNAPSHOT_FILENAME).write_text(json.dumps(graph_snapshot, indent=2), encoding="utf-8")


def build_observer_answer(base_dir: Path, session_id: str, question: str, summary: str = "") -> dict[str, Any]:
    """Build a grounded observer-chat response with event-level citations.

    Args:
        base_dir: Root path for the `network_simulation_agent` package.
        session_id: Session identifier to read artifacts from.
        question: User question submitted after simulation completion.
        summary: Optional fallback summary from in-memory session store.

    Returns:
        Dictionary with `answer` and `citations`, each citation referencing concrete event ids.
    """
    events = read_events(base_dir=base_dir, session_id=session_id, max_events=600)
    if not events:
        raise ValueError("No session events found for observer grounding.")

    matched = _select_grounding_events(question=question, events=events)
    citations = [_to_citation(item) for item in matched]

    final_result = _extract_final_result(events)
    answer_text = _compose_answer(
        question=question,
        final_result=final_result,
        citations=citations,
        summary=summary,
    )
    return {
        "answer": answer_text,
        "citations": citations,
    }


def _extract_final_result(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract final simulation payload from session events."""
    for item in reversed(events):
        event = item.get("event")
        if isinstance(event, dict) and event.get("type") == "final":
            result = event.get("result")
            if isinstance(result, dict):
                return result
    return {}


def _select_grounding_events(question: str, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select relevant grounding events via simple keyword overlap with deterministic fallback."""
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z]{3,}", question.lower())
        if token not in {"what", "when", "where", "which", "with", "from", "that", "this", "would", "could"}
    }
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in events:
        event = item.get("event")
        if not isinstance(event, dict):
            continue
        text = _event_text(event).lower()
        score = sum(1 for token in tokens if token in text)
        if score > 0:
            scored.append((score, item))

    if scored:
        scored.sort(key=lambda pair: (pair[0], pair[1].get("seq", 0)), reverse=True)
        return [pair[1] for pair in scored[:4]]

    fallback: list[dict[str, Any]] = []
    for item in reversed(events):
        event = item.get("event")
        if not isinstance(event, dict):
            continue
        if event.get("type") in {"observer_summary", "final", "node_action", "network_state"}:
            fallback.append(item)
        if len(fallback) >= 4:
            break
    return list(reversed(fallback))


def _event_text(event: dict[str, Any]) -> str:
    """Return searchable text representation for one canonical event."""
    payload_bits = [
        str(event.get("type", "")),
        str(event.get("summary", "")),
        str(event.get("message", "")),
        str(event.get("action", "")),
        str(event.get("result", "")),
    ]
    return " ".join(payload_bits)


def _to_citation(item: dict[str, Any]) -> dict[str, Any]:
    """Convert one canonical event record to API citation format."""
    event = item.get("event", {})
    event_type = event.get("type", "unknown") if isinstance(event, dict) else "unknown"
    return {
        "source": "session_state.jsonl",
        "seq": item.get("seq"),
        "tick": item.get("tick"),
        "event_type": event_type,
        "excerpt": _event_text(event if isinstance(event, dict) else {})[:240],
    }


def _compose_answer(
    question: str,
    final_result: dict[str, Any],
    citations: list[dict[str, Any]],
    summary: str,
) -> str:
    """Compose concise grounded answer text from final KPI outcome and cited evidence."""
    kpis = final_result.get("kpis") if isinstance(final_result, dict) else {}
    revenue = float(kpis.get("revenue_delta", 0.0)) if isinstance(kpis, dict) else 0.0
    cost = float(kpis.get("cost_delta", 0.0)) if isinstance(kpis, dict) else 0.0
    risk = float(kpis.get("risk_delta", 0.0)) if isinstance(kpis, dict) else 0.0
    summary_text = str(final_result.get("summary") or summary or "No summary available.")
    cited_ids = ", ".join(
        f"seq:{citation.get('seq')}/tick:{citation.get('tick')}" for citation in citations[:3]
    )
    return (
        f"Answer to: {question}\n"
        f"Final KPI trajectory: revenue {revenue:+.2%}, cost {cost:+.2%}, risk {risk:+.2%}.\n"
        f"Observer summary: {summary_text}\n"
        f"Grounded on events: {cited_ids if cited_ids else 'none'}."
    )
