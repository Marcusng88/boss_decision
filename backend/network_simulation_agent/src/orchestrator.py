from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from .model import get_node_turn_model
from .model import get_world_builder_model
from .rules import normalize_action
from .schema import NetworkSimulatorRequest


NODE_TYPES = ["business", "consumer", "supplier", "competitor", "community", "bank", "regulator", "platform"]
EDGE_TYPES = ["transaction", "influence", "trust", "dependency", "information"]


class WorldNodeSpec(BaseModel):
    """Structured node spec emitted by the world-builder model."""

    node_id: str
    label: str
    node_type: str
    influence: float = Field(ge=0, le=1)
    status: str = "stable"
    x: float = Field(ge=20, le=920)
    y: float = Field(ge=20, le=620)
    persona: str


class WorldEdgeSpec(BaseModel):
    """Structured edge spec emitted by the world-builder model."""

    edge_id: str
    source: str
    target: str
    edge_type: str
    weight: float = Field(ge=0, le=1)


class WorldBuildOutput(BaseModel):
    """Schema for model-generated network graph and personas."""

    nodes: list[WorldNodeSpec]
    edges: list[WorldEdgeSpec]
    assumptions: list[str] = Field(default_factory=list)


class NodeActionOutput(BaseModel):
    """Schema for model-generated node action payload."""

    action_type: str
    target_node_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    confidence: float = Field(ge=0, le=1)
    message: str


class NetworkOrchestrator:
    """LLM orchestration for world building and per-node turn decisions."""

    def __init__(self, request: NetworkSimulatorRequest, rng: random.Random) -> None:
        """Store request-scoped dependencies and lazy model handles."""
        self.request = request
        self.rng = rng
        self.world_model = get_world_builder_model()
        self.node_model = get_node_turn_model()
        self.personas: dict[str, str] = {}
        self.assumptions: list[str] = []

    def build_world(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Build initial nodes/edges from LLM output, with deterministic fallback."""
        llm_result = self._build_world_with_llm()
        if llm_result:
            nodes, edges = llm_result
            if nodes and edges:
                return nodes, edges
        return self._fallback_world()

    def actor_order_for_tick(self, tick: int, node_ids: list[str]) -> list[str]:
        """Choose deterministic actor subset for one tick to keep latency stable."""
        if not node_ids:
            return []
        window = max(3, min(8, max(1, len(node_ids) // 4)))
        start = (tick * window) % len(node_ids)
        ordered = node_ids[start:] + node_ids[:start]
        return ordered[:window]

    def build_node_turn(
        self,
        tick: int,
        node: dict[str, Any],
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        kpis: dict[str, float],
        recent_events: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], str]:
        """Generate one node action and companion message from LLM or fallback."""
        action_output = self._build_node_turn_with_llm(
            tick=tick,
            node=node,
            nodes=nodes,
            edges=edges,
            kpis=kpis,
            recent_events=recent_events,
        )
        node_ids = {str(item.get("node_id", "")) for item in nodes}
        source_id = str(node.get("node_id", ""))

        if action_output is None:
            fallback = self._fallback_node_turn(node=node, nodes=nodes, tick=tick)
            action = normalize_action(
                {
                    "action_type": fallback["action_type"],
                    "source_node_id": source_id,
                    "target_node_id": fallback["target_node_id"],
                    "payload": fallback["payload"],
                    "rationale": fallback["rationale"],
                    "confidence": fallback["confidence"],
                },
                node_ids=node_ids,
            )
            return action, str(fallback["message"])

        action = normalize_action(
            {
                "action_type": action_output.action_type,
                "source_node_id": source_id,
                "target_node_id": action_output.target_node_id,
                "payload": action_output.payload,
                "rationale": action_output.rationale,
                "confidence": action_output.confidence,
            },
            node_ids=node_ids,
        )
        return action, action_output.message

    def _build_world_with_llm(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
        """Ask the world-builder LLM to generate nodes, edges, and persona text."""
        if self.world_model is None:
            return None
        node_count = max(self.request.min_nodes, min(self.request.max_nodes, 24))
        context_snippets = self._read_context_snippets(max_chars=6000)
        web_snippets = self._search_snippets(self.request.query) if self.request.allow_internet else []

        prompt = (
            "You are building a business-economic simulation network.\n"
            f"Scenario query: {self.request.query}\n"
            f"Target node count: {node_count}\n"
            "Return realistic roles from business/customer/supplier/community/finance/regulator ecosystems.\n"
            "Constraints:\n"
            "- node_type must be one of: business, consumer, supplier, competitor, community, bank, regulator, platform\n"
            "- edge_type must be one of: transaction, influence, trust, dependency, information\n"
            "- every node must include a short persona instruction in `persona`\n"
            "- use compact ids like node_sme_hq, node_students, edge_1\n"
            "- include at least one business node, one consumer node, one supplier node, and one competitor node\n\n"
            f"Structured context snippets:\n{context_snippets}\n\n"
            f"Web snippets (optional):\n{json.dumps(web_snippets, ensure_ascii=True)}"
        )

        parsed = self._invoke_validated_json(self.world_model, prompt, WorldBuildOutput)
        if parsed is None:
            return None

        self.assumptions = parsed.assumptions[:20]
        nodes = self._sanitize_nodes(parsed.nodes)
        edges = self._sanitize_edges(parsed.edges, nodes)
        if not nodes or not edges:
            return None
        return nodes, edges

    def _build_node_turn_with_llm(
        self,
        tick: int,
        node: dict[str, Any],
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        kpis: dict[str, float],
        recent_events: list[dict[str, Any]],
    ) -> NodeActionOutput | None:
        """Ask node-turn LLM for a typed action and explanatory message."""
        if self.node_model is None:
            return None

        node_id = str(node.get("node_id", ""))
        persona = self.personas.get(node_id, "Act according to your role and current network pressures.")
        nearby_edges = [
            edge for edge in edges if edge.get("source") == node_id or edge.get("target") == node_id
        ][:8]
        prompt = (
            "You control one node inside a live economic network simulation.\n"
            f"Scenario query: {self.request.query}\n"
            f"Tick: {tick}/{self.request.max_ticks}\n"
            f"Your node: {json.dumps(node, ensure_ascii=True)}\n"
            f"Persona: {persona}\n"
            f"Current KPI deltas: {json.dumps(kpis, ensure_ascii=True)}\n"
            f"Connected edges: {json.dumps(nearby_edges, ensure_ascii=True)}\n"
            f"Recent events: {json.dumps(recent_events[-12:], ensure_ascii=True)}\n"
            "Action constraints:\n"
            "- action_type must be one of observe, message, price_adjust, budget_shift, negotiate_supply, "
            "community_campaign, risk_mitigation, wait\n"
            "- keep payload compact and numeric where possible\n"
            "- confidence must be in [0,1]\n"
            "- message should be 1 sentence from this node's perspective\n"
        )
        return self._invoke_validated_json(self.node_model, prompt, NodeActionOutput)

    def _fallback_world(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate deterministic non-LLM world so runtime remains functional without model access."""
        count = max(self.request.min_nodes, min(self.request.max_nodes, 18))
        nodes: list[dict[str, Any]] = []
        for idx in range(count):
            ntype = NODE_TYPES[idx % len(NODE_TYPES)]
            node_id = f"node_{idx+1}"
            nodes.append(
                {
                    "node_id": node_id,
                    "label": f"{ntype.title()} {idx+1}",
                    "node_type": ntype,
                    "influence": round(self.rng.uniform(0.3, 0.95), 3),
                    "status": "stable",
                    "x": round(self.rng.uniform(40, 820), 2),
                    "y": round(self.rng.uniform(30, 520), 2),
                }
            )
            self.personas[node_id] = f"You represent a {ntype} actor optimizing outcomes under uncertainty."

        edges: list[dict[str, Any]] = []
        edge_count = max(12, min(len(nodes) * 2, 48))
        for idx in range(edge_count):
            source_idx = idx % len(nodes)
            target_idx = (idx * 3 + 5) % len(nodes)
            if source_idx == target_idx:
                target_idx = (target_idx + 1) % len(nodes)
            edges.append(
                {
                    "edge_id": f"edge_{idx+1}",
                    "source": nodes[source_idx]["node_id"],
                    "target": nodes[target_idx]["node_id"],
                    "edge_type": EDGE_TYPES[idx % len(EDGE_TYPES)],
                    "weight": round(self.rng.uniform(0.25, 0.9), 3),
                }
            )
        return nodes, edges

    def _fallback_node_turn(self, node: dict[str, Any], nodes: list[dict[str, Any]], tick: int) -> dict[str, Any]:
        """Generate deterministic fallback action/message for one node turn."""
        target = self.rng.choice(nodes)
        action_type = self.rng.choice(
            [
                "observe",
                "message",
                "price_adjust",
                "budget_shift",
                "negotiate_supply",
                "community_campaign",
                "risk_mitigation",
                "wait",
            ]
        )
        return {
            "action_type": action_type,
            "target_node_id": target.get("node_id"),
            "payload": {"tick": tick, "delta": round(self.rng.uniform(-0.12, 0.18), 3)},
            "rationale": f"{node.get('label', node.get('node_id', 'Node'))} selected {action_type} under local pressure.",
            "confidence": round(self.rng.uniform(0.45, 0.9), 3),
            "message": f"{node.get('label', 'Node')} is responding to current market pressure with {action_type}.",
        }

    def _sanitize_nodes(self, raw_nodes: list[WorldNodeSpec]) -> list[dict[str, Any]]:
        """Clean model-generated nodes and clip count/ranges to request bounds."""
        cleaned: list[dict[str, Any]] = []
        seen: set[str] = set()
        for idx, node in enumerate(raw_nodes):
            if len(cleaned) >= self.request.max_nodes:
                break
            node_id = self._clean_id(node.node_id, fallback=f"node_{idx+1}")
            if node_id in seen:
                continue
            seen.add(node_id)
            node_type = node.node_type if node.node_type in NODE_TYPES else "business"
            status = node.status if node.status in {"stable", "active", "strained", "watch"} else "stable"
            cleaned.append(
                {
                    "node_id": node_id,
                    "label": str(node.label)[:120],
                    "node_type": node_type,
                    "influence": round(max(0.0, min(1.0, float(node.influence))), 3),
                    "status": status,
                    "x": round(max(20.0, min(920.0, float(node.x))), 2),
                    "y": round(max(20.0, min(620.0, float(node.y))), 2),
                }
            )
            self.personas[node_id] = str(node.persona)[:800]

        if len(cleaned) < self.request.min_nodes:
            fallback_nodes, _ = self._fallback_world()
            for node in fallback_nodes:
                if len(cleaned) >= self.request.min_nodes:
                    break
                if node["node_id"] in seen:
                    continue
                seen.add(node["node_id"])
                cleaned.append(node)
        return cleaned

    def _sanitize_edges(self, raw_edges: list[WorldEdgeSpec], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Clean model-generated edges and keep only valid links between known nodes."""
        if not nodes:
            return []
        node_ids = {str(node["node_id"]) for node in nodes}
        cleaned: list[dict[str, Any]] = []
        seen: set[str] = set()
        for idx, edge in enumerate(raw_edges):
            if len(cleaned) >= 120:
                break
            source = str(edge.source).strip()
            target = str(edge.target).strip()
            if source not in node_ids or target not in node_ids or source == target:
                continue
            edge_id = self._clean_id(edge.edge_id, fallback=f"edge_{idx+1}")
            if edge_id in seen:
                continue
            seen.add(edge_id)
            edge_type = edge.edge_type if edge.edge_type in EDGE_TYPES else "information"
            cleaned.append(
                {
                    "edge_id": edge_id,
                    "source": source,
                    "target": target,
                    "edge_type": edge_type,
                    "weight": round(max(0.05, min(1.0, float(edge.weight))), 3),
                }
            )

        if not cleaned:
            _, fallback_edges = self._fallback_world()
            for edge in fallback_edges:
                if edge["source"] in node_ids and edge["target"] in node_ids:
                    cleaned.append(edge)
        return cleaned

    def _clean_id(self, raw_id: str, fallback: str) -> str:
        """Normalize arbitrary model ids to predictable snake_case tokens."""
        token = re.sub(r"[^a-zA-Z0-9_]+", "_", str(raw_id).strip().lower())
        token = re.sub(r"_+", "_", token).strip("_")
        if not token:
            return fallback
        return token

    def _read_context_snippets(self, max_chars: int = 4000) -> str:
        """Read compact local context from the configured folder for world-builder grounding."""
        if self.request.data_context_path:
            root = Path(self.request.data_context_path)
            if not root.is_absolute():
                root = Path(__file__).resolve().parents[2] / root
        else:
            root = Path(__file__).resolve().parents[2] / "agent_docs" / "simulator"

        if not root.exists() or not root.is_dir():
            return ""

        snippets: list[str] = []
        remaining = max_chars
        files = sorted(
            [
                p
                for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json", ".csv"}
            ]
        )[:20]
        for path in files:
            if remaining <= 0:
                break
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            chunk = text[: min(len(text), 500)]
            row = f"{path.name}: {chunk}"
            snippets.append(row)
            remaining -= len(row)
        return "\n".join(snippets)

    def _search_snippets(self, query: str) -> list[dict[str, str]]:
        """Fetch bounded web snippets via Tavily when API key is available."""
        api_key = None
        try:
            import os

            api_key = os.getenv("TAVILY_API_KEY")
        except Exception:
            api_key = None
        if not api_key:
            return []

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=3, search_depth="basic")
        except Exception:
            return []

        results = response.get("results") if isinstance(response, dict) else None
        if not isinstance(results, list):
            return []
        snippets: list[dict[str, str]] = []
        for item in results[:3]:
            if not isinstance(item, dict):
                continue
            snippets.append(
                {
                    "title": str(item.get("title", ""))[:120],
                    "url": str(item.get("url", ""))[:200],
                    "content": str(item.get("content", ""))[:400],
                }
            )
        return snippets

    def _invoke_validated_json(self, model: Any, prompt: str, schema_type: type[BaseModel]) -> Any | None:
        """Invoke model and parse output using structured mode first, then JSON fallback."""
        if model is None:
            return None
        try:
            if hasattr(model, "with_structured_output"):
                response = model.with_structured_output(schema_type).invoke(prompt)
                if isinstance(response, schema_type):
                    return response
                return schema_type.model_validate(response)
        except Exception:
            pass

        try:
            response = model.invoke(prompt)
            content = getattr(response, "content", response)
            if isinstance(content, list):
                content = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
            text = str(content)
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            parsed = json.loads(text[start : end + 1])
            return schema_type.model_validate(parsed)
        except Exception:
            return None
