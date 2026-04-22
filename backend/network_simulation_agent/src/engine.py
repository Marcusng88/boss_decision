from __future__ import annotations

import random
from pathlib import Path
from typing import Any
from typing import AsyncIterator

from .memory import append_event
from .memory import build_session_id
from .memory import get_run_dir
from .memory import SESSION_STATE_SCHEMA_VERSION
from .schema import NetworkSimulatorRequest
from .schema import ShockEvent
from .rules import validate_action
from .stream_adapter import make_event
from .stream_adapter import progress_event
from .stream_adapter import status_event

NODE_TYPES = ["business", "consumer", "supplier", "competitor", "community", "bank", "regulator", "platform"]
EDGE_TYPES = ["transaction", "influence", "trust", "dependency", "information"]
NODE_STATUSES = ["stable", "active", "strained", "watch"]
ACTION_TYPES = [
    "observe",
    "message",
    "price_adjust",
    "budget_shift",
    "negotiate_supply",
    "community_campaign",
    "risk_mitigation",
    "wait",
]


class SessionStore:
    """In-memory session metadata for phase-1 mock flow."""

    def __init__(self) -> None:
        """Initialize per-session containers for queued shocks and observer reports."""
        self.shocks_by_session: dict[str, list[ShockEvent]] = {}
        self.observer_reports: dict[str, str] = {}

    def queue_shock(self, session_id: str, shock: ShockEvent) -> None:
        """Queue a shock event to be consumed on the next tick for a session."""
        self.shocks_by_session.setdefault(session_id, []).append(shock)

    def pop_shocks(self, session_id: str) -> list[ShockEvent]:
        """Return and clear all queued shocks for the given session."""
        queued = self.shocks_by_session.get(session_id, [])
        self.shocks_by_session[session_id] = []
        return queued

    def set_observer_report(self, session_id: str, report: str) -> None:
        """Persist the latest observer summary text for post-run chat."""
        self.observer_reports[session_id] = report

    def get_observer_report(self, session_id: str) -> str | None:
        """Fetch a previously stored observer summary for a session, if available."""
        return self.observer_reports.get(session_id)


SESSION_STORE = SessionStore()


class NetworkSimulationEngine:
    def __init__(self, request: NetworkSimulatorRequest, session_id: str | None = None) -> None:
        """Create a simulation engine with deterministic RNG and initialized graph state.

        Args:
            request: Validated simulation request parameters.
            session_id: Optional session id; generated automatically when omitted.
        """
        self.request = request
        self.session_id = session_id or build_session_id()
        self.rng = random.Random(request.seed or 7)
        self.base_dir = Path(__file__).resolve().parents[2] / "network_simulation_agent"
        get_run_dir(self.base_dir, self.session_id)
        self.event_seq = 0
        self.nodes = self._build_nodes()
        self.edges = self._build_edges()
        self.kpis = {
            "revenue_delta": 0.0,
            "cost_delta": 0.0,
            "risk_delta": 0.0,
        }

    def _build_nodes(self) -> list[dict[str, Any]]:
        """Build initial node state list using bounded request size and seeded randomness."""
        count = max(self.request.min_nodes, min(self.request.max_nodes, 18))
        nodes: list[dict[str, Any]] = []
        for idx in range(count):
            ntype = NODE_TYPES[idx % len(NODE_TYPES)]
            nodes.append(
                {
                    "node_id": f"node_{idx+1}",
                    "label": f"{ntype.title()} {idx+1}",
                    "node_type": ntype,
                    "influence": round(self.rng.uniform(0.3, 0.95), 3),
                    "status": "stable",
                    "x": round(self.rng.uniform(40, 820), 2),
                    "y": round(self.rng.uniform(30, 520), 2),
                }
            )
        return nodes

    def _build_edges(self) -> list[dict[str, Any]]:
        """Build initial directed edge list with deterministic source/target mapping."""
        edges: list[dict[str, Any]] = []
        edge_count = max(12, min(len(self.nodes) * 2, 48))
        for idx in range(edge_count):
            source_idx = idx % len(self.nodes)
            target_idx = (idx * 3 + 5) % len(self.nodes)
            if source_idx == target_idx:
                target_idx = (target_idx + 1) % len(self.nodes)
            edges.append(
                {
                    "edge_id": f"edge_{idx+1}",
                    "source": self.nodes[source_idx]["node_id"],
                    "target": self.nodes[target_idx]["node_id"],
                    "edge_type": EDGE_TYPES[idx % len(EDGE_TYPES)],
                    "weight": round(self.rng.uniform(0.25, 0.9), 3),
                }
            )
        return edges

    def _node_lookup(self) -> dict[str, dict[str, Any]]:
        """Build an in-memory lookup table for node objects by id."""
        return {node["node_id"]: node for node in self.nodes}

    def _clamp(self, value: float, lo: float, hi: float) -> float:
        """Clamp numeric values to a bounded range."""
        return max(lo, min(hi, value))

    def _action_effects(self, action_type: str) -> dict[str, float]:
        """Return deterministic KPI deltas associated with each action type."""
        return {
            "observe": {"revenue_delta": 0.001, "cost_delta": 0.0, "risk_delta": -0.001},
            "message": {"revenue_delta": 0.0015, "cost_delta": 0.0005, "risk_delta": -0.0008},
            "price_adjust": {"revenue_delta": 0.005, "cost_delta": 0.0015, "risk_delta": 0.002},
            "budget_shift": {"revenue_delta": 0.0025, "cost_delta": -0.0015, "risk_delta": 0.001},
            "negotiate_supply": {"revenue_delta": 0.002, "cost_delta": -0.0035, "risk_delta": -0.0005},
            "community_campaign": {"revenue_delta": 0.002, "cost_delta": 0.003, "risk_delta": -0.002},
            "risk_mitigation": {"revenue_delta": 0.001, "cost_delta": 0.001, "risk_delta": -0.004},
            "wait": {"revenue_delta": -0.0008, "cost_delta": 0.0, "risk_delta": 0.0008},
        }.get(action_type, {"revenue_delta": 0.0, "cost_delta": 0.0, "risk_delta": 0.0})

    def _apply_kpi_delta(self, delta: dict[str, float]) -> None:
        """Accumulate and clamp KPI deltas into a stable numeric range."""
        self.kpis["revenue_delta"] = round(self._clamp(self.kpis["revenue_delta"] + delta["revenue_delta"], -1.0, 1.0), 4)
        self.kpis["cost_delta"] = round(self._clamp(self.kpis["cost_delta"] + delta["cost_delta"], -1.0, 1.0), 4)
        self.kpis["risk_delta"] = round(self._clamp(self.kpis["risk_delta"] + delta["risk_delta"], -1.0, 1.0), 4)

    def _apply_shock(self, shock: ShockEvent) -> None:
        """Apply a queued shock event to node statuses and KPIs."""
        severity = self._clamp(float(shock.severity), 0.0, 1.0)
        target_ids = set(shock.targets)

        for node in self.nodes:
            if target_ids and node["node_id"] not in target_ids:
                continue
            node["influence"] = round(self._clamp(node["influence"] - (0.06 * severity), 0.0, 1.0), 3)
            node["status"] = "strained" if severity >= 0.5 else "watch"

        self._apply_kpi_delta(
            {
                "revenue_delta": round(-0.01 * severity, 4),
                "cost_delta": round(0.012 * severity, 4),
                "risk_delta": round(0.018 * severity, 4),
            }
        )

    def _sample_action(self, tick: int) -> dict[str, Any]:
        """Generate one deterministic node action for the current tick."""
        actor = self.rng.choice(self.nodes)
        target = self.rng.choice(self.nodes)
        action_type = self.rng.choice(ACTION_TYPES)
        action = {
            "action_type": action_type,
            "source_node_id": actor["node_id"],
            "target_node_id": target["node_id"],
            "payload": {"delta": round(self.rng.uniform(-0.15, 0.2), 3), "tick": tick},
            "rationale": f"{actor['label']} executed {action_type} from local role constraints.",
            "confidence": round(self.rng.uniform(0.45, 0.92), 3),
        }
        return action

    def _resolve_action(self, action: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Validate and apply action effects, returning action event and optional rejection."""
        is_valid, reason = validate_action(action)
        rejection: dict[str, Any] | None = None
        if not is_valid:
            rejection = {
                "status": "rejected",
                "reason": reason,
                "action": action,
            }
            return action, rejection

        source_id = str(action["source_node_id"])
        nodes = self._node_lookup()
        source = nodes.get(source_id)
        if source:
            source["status"] = self.rng.choice(NODE_STATUSES)
            source["influence"] = round(self._clamp(source["influence"] + self.rng.uniform(-0.03, 0.03), 0.0, 1.0), 3)

        self._apply_kpi_delta(self._action_effects(str(action["action_type"])))
        return action, {}

    def _update_edge(self, tick: int) -> dict[str, Any]:
        """Apply deterministic edge weight drift for one selected edge."""
        touched_edge = self.rng.choice(self.edges)
        touched_edge["weight"] = round(
            self._clamp(touched_edge["weight"] + self.rng.uniform(-0.08, 0.08), 0.05, 1.0), 3
        )
        touched_edge["last_tick"] = tick
        return touched_edge

    def _llm_state_digest(self, tick: int) -> dict[str, Any]:
        """Build compact shared state context designed for LLM node consumption."""
        node_status_counts: dict[str, int] = {status: 0 for status in NODE_STATUSES}
        for node in self.nodes:
            node_status_counts[str(node["status"])] += 1

        top_edges = sorted(self.edges, key=lambda edge: edge["weight"], reverse=True)[:6]
        dominant_links = [
            f"{edge['source']} -> {edge['target']} ({edge['edge_type']}, w={edge['weight']:.2f})" for edge in top_edges
        ]
        summary = (
            f"Tick {tick}/{self.request.max_ticks}. Revenue {self.kpis['revenue_delta']:+.2%}, "
            f"Cost {self.kpis['cost_delta']:+.2%}, Risk {self.kpis['risk_delta']:+.2%}. "
            f"Status distribution: {node_status_counts}."
        )
        return {
            "summary": summary,
            "node_status_counts": node_status_counts,
            "dominant_links": dominant_links,
            "kpis": self.kpis.copy(),
            "edge_semantics": {
                "transaction": "commercial flow between parties",
                "influence": "behavior/decision pressure signal",
                "trust": "relationship confidence strength",
                "dependency": "operational reliance and bottleneck risk",
                "information": "news or narrative propagation channel",
            },
        }

    def _append_event(self, event: dict[str, Any], tick: int | None = None) -> None:
        """Append one canonical record to `session_state.jsonl` with LLM-readable context."""
        self.event_seq += 1
        payload = dict(event)
        canonical = {
            "schema_version": SESSION_STATE_SCHEMA_VERSION,
            "session_id": self.session_id,
            "seq": self.event_seq,
            "type": payload.get("type", "unknown"),
            "tick": tick,
            "ts": payload.get("ts"),
            "event": payload,
            "shared_state": {
                "query": self.request.query,
                "scenario_id": self.request.scenario_id,
                "seed": self.request.seed,
                "max_ticks": self.request.max_ticks,
                "kpis": self.kpis.copy(),
            },
            "llm_context": self._llm_state_digest(tick=tick or 0),
        }
        append_event(self.base_dir, self.session_id, canonical)

    async def run_stream(self) -> AsyncIterator[dict[str, Any]]:
        """Run the simulation tick loop and yield canonical stream events.

        Yields:
            Event dictionaries covering lifecycle, actions, graph updates, and final summary.
        """
        header = make_event(
            "status",
            session_id=self.session_id,
            message="Network simulation stream started.",
            query=self.request.query,
            scenario_id=self.request.scenario_id,
            seed=self.request.seed,
            run_header={
                "session_id": self.session_id,
                "seed": self.request.seed,
                "model": "phase2-deterministic-engine",
                "prompt_version": "network_v2",
                "start_ts": None,
            },
        )
        if isinstance(header.get("run_header"), dict):
            header["run_header"]["start_ts"] = header.get("ts")
        self._append_event(header, tick=0)
        yield header

        for tick in range(1, self.request.max_ticks + 1):
            progress = progress_event(tick=tick, max_ticks=self.request.max_ticks, summary=f"Tick {tick} executing.")
            progress["session_id"] = self.session_id
            self._append_event(progress, tick=tick)
            yield progress

            queued_shocks = SESSION_STORE.pop_shocks(self.session_id)
            for shock in queued_shocks:
                self._apply_shock(shock)
                shock_event = make_event(
                    "shock_event",
                    session_id=self.session_id,
                    tick=tick,
                    shock=shock.model_dump(mode="json"),
                )
                self._append_event(shock_event, tick=tick)
                yield shock_event

            action_payload = self._sample_action(tick=tick)
            resolved_action, rejection = self._resolve_action(action_payload)

            action_event = make_event(
                "node_action",
                session_id=self.session_id,
                tick=tick,
                action=resolved_action,
            )
            self._append_event(action_event, tick=tick)
            yield action_event

            if rejection:
                rejection_event = make_event(
                    "node_message",
                    session_id=self.session_id,
                    tick=tick,
                    message={
                        "node_id": str(resolved_action.get("source_node_id", "unknown")),
                        "text": f"Action rejected by rules: {rejection.get('reason', 'unknown reason')}",
                    },
                )
                self._append_event(rejection_event, tick=tick)
                yield rejection_event

            source_node_id = str(resolved_action.get("source_node_id", "unknown"))
            source_node = next((item for item in self.nodes if item["node_id"] == source_node_id), None)
            message = make_event(
                "node_message",
                session_id=self.session_id,
                tick=tick,
                message={
                    "node_id": source_node_id,
                    "text": (
                        f"{source_node['label']} reports pressure in {source_node['node_type']} cluster."
                        if source_node
                        else "Node reported local condition change."
                    ),
                },
            )
            self._append_event(message, tick=tick)
            yield message

            touched_edge = self._update_edge(tick=tick)
            edge_event = make_event(
                "edge_update",
                session_id=self.session_id,
                tick=tick,
                edge=touched_edge,
            )
            self._append_event(edge_event, tick=tick)
            yield edge_event

            network_state = make_event(
                "network_state",
                session_id=self.session_id,
                tick=tick,
                state={
                    "tick": tick,
                    "max_ticks": self.request.max_ticks,
                    "nodes": self.nodes,
                    "edges": self.edges,
                    "kpis": self.kpis.copy(),
                    "llm_context": self._llm_state_digest(tick=tick),
                },
            )
            self._append_event(network_state, tick=tick)
            yield network_state

        summary_text = (
            "Mock observer summary: controlled price increase is viable when paired with retention actions and "
            "supplier coordination. Validate with segment-level demand elasticity before rollout."
        )
        observer_summary = make_event(
            "observer_summary",
            session_id=self.session_id,
            summary=summary_text,
            confidence=0.67,
        )
        self._append_event(observer_summary, tick=self.request.max_ticks)
        SESSION_STORE.set_observer_report(self.session_id, summary_text)
        yield observer_summary

        final_event = make_event(
            "final",
            session_id=self.session_id,
            result={
                "session_id": self.session_id,
                "query": self.request.query,
                "max_ticks": self.request.max_ticks,
                "summary": summary_text,
                "kpis": self.kpis.copy(),
            },
        )
        self._append_event(final_event, tick=self.request.max_ticks)
        yield final_event

        done = status_event("Network simulation stream completed.")
        done["type"] = "done"
        done["session_id"] = self.session_id
        self._append_event(done, tick=self.request.max_ticks)
        yield done

    async def run_to_completion(self) -> dict[str, Any]:
        """Consume the stream to completion and return the final result payload."""
        final_payload: dict[str, Any] = {"session_id": self.session_id}
        async for event in self.run_stream():
            if event.get("type") == "final":
                result = event.get("result")
                if isinstance(result, dict):
                    final_payload.update(result)
        return final_payload
