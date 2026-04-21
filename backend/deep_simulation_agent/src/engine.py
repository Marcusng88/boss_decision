from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import AsyncIterator

import yaml

from .observer import build_final_report
from .observer import build_periodic_summary
from .orchestrator import DeepOrchestrator
from .rules import apply_intents_to_kpis
from .rules import resolve_conflicts
from .rules import validate_intent
from .schema import ActionIntent
from .schema import AgentObservation
from .schema import AgentSnapshot
from .schema import DeepSimulationRequest
from .schema import DeepSimulationState
from .schema import KPIState
from .schema import TickEvent
from .schema import TimelineEvent
from .schema import WorldMap
from .schema import WorldZone
from .stream_adapter import agent_chunk_event
from .stream_adapter import progress_event
from .stream_adapter import tick_event_to_stream
from .stream_adapter import timeline_event
from .stream_adapter import tool_call_event
from .stream_adapter import world_event

WORLD_MIN = 4.0
WORLD_MAX = 96.0
SPAWN_X = 50.0
SPAWN_Y = 50.0


def _docs_root() -> Path:
    return Path(__file__).resolve().parents[2] / "agent_docs" / "simulator"


def _scenario_path(scenario_id: str) -> Path:
    return Path(__file__).resolve().parent / "scenarios" / f"{scenario_id}.yaml"


def _load_scenario(scenario_id: str) -> dict[str, Any]:
    path = _scenario_path(scenario_id)
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            return data
    return {
        "id": scenario_id,
        "name": "Tycoon Crisis Sprint",
        "map": {
            "width": 100,
            "height": 100,
            "zones": [
                {"id": "demand_hub", "name": "Demand Hub", "x": 28, "y": 44, "radius": 14, "effects": {"revenue": 0.2}},
                {
                    "id": "supply_yard",
                    "name": "Supply Yard",
                    "x": 72,
                    "y": 35,
                    "radius": 11,
                    "effects": {"margin": 0.2},
                },
                {
                    "id": "brand_garden",
                    "name": "Brand Garden",
                    "x": 58,
                    "y": 74,
                    "radius": 13,
                    "effects": {"sentiment": 0.2},
                },
            ],
        },
        "game_rules": {
            "crisis_trigger_chance": 0.24,
            "daily_base_points": 0.9,
            "move_points_per_step": 0.08,
            "intent_points_multiplier": 1.8,
            "kpi_points_multiplier": 0.75,
        },
        "crisis_cards": [],
    }


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _move(rng: random.Random) -> float:
    return (rng.random() - 0.5) * 7.5


def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


class DeepSimulationEngine:
    def __init__(self, request: DeepSimulationRequest):
        self.request = request
        self.seed = request.seed if request.seed is not None else random.SystemRandom().randint(1, 2_147_483_647)
        self.rng = random.Random(self.seed)
        self.scenario = _load_scenario(request.scenario_id)
        self.orchestrator = DeepOrchestrator(
            query=request.query,
            scenario=self.scenario,
            min_personas=request.min_personas,
            max_personas=request.max_personas,
            rng=self.rng,
            docs_root=_docs_root(),
        )
        self.state = self._build_initial_state()

    def _build_initial_state(self) -> DeepSimulationState:
        map_payload = self.scenario.get("map", {})
        zones = [
            WorldZone(
                id=str(item.get("id") or f"zone_{idx}"),
                name=str(item.get("name") or f"Zone {idx+1}"),
                x=float(item.get("x", 50.0)),
                y=float(item.get("y", 50.0)),
                radius=float(item.get("radius", 10.0)),
            )
            for idx, item in enumerate(map_payload.get("zones", []))
            if isinstance(item, dict)
        ]
        world_map = WorldMap(
            width=int(map_payload.get("width", 100)),
            height=int(map_payload.get("height", 100)),
            zones=zones,
        )
        agents: list[AgentSnapshot] = []
        scores: dict[str, float] = {}
        positions: dict[str, int] = {}
        for persona in self.orchestrator.personas:
            agents.append(
                AgentSnapshot(
                    id=persona.id,
                    name=persona.name,
                    role=persona.role,
                    x=SPAWN_X,
                    y=SPAWN_Y,
                    status="idle",
                    tool_calls=[],
                    transcript="",
                    confidence=0.5,
                )
            )
            scores[persona.id] = 0.0
            positions[persona.id] = 0
        return DeepSimulationState(
            query=self.request.query,
            scenario_id=self.request.scenario_id,
            seed=self.seed,
            tick=0,
            max_ticks=self.request.max_ticks,
            tick_duration_days=1,
            map=world_map,
            agents=agents,
            personas=self.orchestrator.personas,
            global_kpis=KPIState(),
            agent_scores=scores,
            agent_positions=positions,
            timeline=[],
            tick_events=[],
            observer_summaries=[],
            done=False,
        )

    def _agent_by_id(self, persona_id: str) -> AgentSnapshot | None:
        return next((agent for agent in self.state.agents if agent.id == persona_id), None)

    def _record_timeline(self, tick: int, message: str, source: str = "engine") -> None:
        event = TimelineEvent(
            id=f"{tick}-{len(self.state.timeline)+1}",
            tick=tick,
            message=message,
            source=source,
            ts=datetime.now(UTC),
        )
        self.state.timeline.insert(0, event)
        self.state.timeline = self.state.timeline[:180]

    def _record_tick_event(self, tick: int, event_type: str, source: str, payload: dict[str, Any]) -> TickEvent:
        event = TickEvent(tick=tick, type=event_type, source=source, payload=payload)
        self.state.tick_events.append(event)
        self.state.tick_events = self.state.tick_events[-400:]
        return event

    def _observation_for(self, persona_id: str, tick: int) -> AgentObservation:
        agent = self._agent_by_id(persona_id)
        return AgentObservation(
            persona_id=persona_id,
            tick=tick,
            local_view={
                "x": agent.x if agent else 50.0,
                "y": agent.y if agent else 50.0,
                "global_kpis": self.state.global_kpis.model_dump(),
                "recent_timeline": [item.model_dump(mode="json") for item in self.state.timeline[:6]],
                "map_zones": [zone.model_dump() for zone in self.state.map.zones],
            },
            goals=["simulate 1 day and update strategic posture"],
            constraints={
                "tick_equals_days": 1,
                "max_ticks": self.state.max_ticks,
                "allowed_actions": ["move", "price_adjust", "spend_shift", "campaign", "procurement", "wait"],
            },
        )

    def _zone_effects_by_id(self) -> dict[str, dict[str, float]]:
        effects: dict[str, dict[str, float]] = {}
        map_payload = self.scenario.get("map", {})
        for item in map_payload.get("zones", []):
            if not isinstance(item, dict):
                continue
            zone_id = str(item.get("id") or "").strip()
            if not zone_id:
                continue
            raw = item.get("effects")
            if not isinstance(raw, dict):
                effects[zone_id] = {}
                continue
            effects[zone_id] = {
                "revenue": _as_float(raw.get("revenue")),
                "margin": _as_float(raw.get("margin")),
                "sentiment": _as_float(raw.get("sentiment")),
                "churn_risk": _as_float(raw.get("churn_risk")),
            }
        return effects

    def _game_rules(self) -> dict[str, float]:
        raw = self.scenario.get("game_rules")
        if not isinstance(raw, dict):
            return {
                "crisis_trigger_chance": 0.24,
                "daily_base_points": 0.9,
                "move_points_per_step": 0.08,
                "intent_points_multiplier": 1.8,
                "kpi_points_multiplier": 0.75,
            }
        return {
            "crisis_trigger_chance": _as_float(raw.get("crisis_trigger_chance"), 0.24),
            "daily_base_points": _as_float(raw.get("daily_base_points"), 0.9),
            "move_points_per_step": _as_float(raw.get("move_points_per_step"), 0.08),
            "intent_points_multiplier": _as_float(raw.get("intent_points_multiplier"), 1.8),
            "kpi_points_multiplier": _as_float(raw.get("kpi_points_multiplier"), 0.75),
        }

    def _move_agents(self, tick: int, active_persona_ids: set[str]) -> dict[str, int]:
        zones = self.state.map.zones
        rolls_by_persona: dict[str, int] = {}
        if zones:
            zone_count = len(zones)
            for agent in self.state.agents:
                if agent.id in active_persona_ids:
                    roll = self.rng.randint(1, 6)
                    rolls_by_persona[agent.id] = roll
                    current = self.state.agent_positions.get(agent.id, 0)
                    new_idx = (current + roll) % zone_count
                    self.state.agent_positions[agent.id] = new_idx
                    target_zone = zones[new_idx]
                    agent.x = target_zone.x
                    agent.y = target_zone.y
                    self._record_timeline(
                        tick,
                        f"{agent.name} rolled {roll} and moved to {target_zone.name}.",
                        source=f"engine:{agent.id}",
                    )
                elif agent.status != "done":
                    idx = self.state.agent_positions.get(agent.id, 0) % zone_count
                    zone = zones[idx]
                    agent.x = zone.x
                    agent.y = zone.y
        else:
            for agent in self.state.agents:
                if agent.id in active_persona_ids:
                    rolls_by_persona[agent.id] = self.rng.randint(1, 6)
                agent.x = _clamp(agent.x + _move(self.rng), WORLD_MIN, WORLD_MAX)
                agent.y = _clamp(agent.y + _move(self.rng), WORLD_MIN, WORLD_MAX)

        for agent in self.state.agents:
            if agent.id in active_persona_ids:
                if agent.status != "done":
                    agent.status = "thinking"
            elif agent.status != "done":
                agent.status = "idle"
        return rolls_by_persona

    def _apply_zone_effects(self, tick: int, active_persona_ids: set[str]) -> None:
        if not self.state.map.zones:
            return
        zone_effects = self._zone_effects_by_id()
        kpi = self.state.global_kpis.model_copy(deep=True)
        for persona_id in active_persona_ids:
            idx = self.state.agent_positions.get(persona_id, 0) % len(self.state.map.zones)
            zone = self.state.map.zones[idx]
            effect = zone_effects.get(zone.id, {})
            if not effect:
                continue
            confidence = self._agent_by_id(persona_id).confidence if self._agent_by_id(persona_id) else 0.5
            scale = 0.45 + (0.6 * confidence)
            kpi.revenue += _as_float(effect.get("revenue")) * scale
            kpi.margin += _as_float(effect.get("margin")) * scale
            kpi.sentiment += _as_float(effect.get("sentiment")) * scale
            kpi.churn_risk += _as_float(effect.get("churn_risk")) * scale
            self._record_tick_event(
                tick=tick,
                event_type="world_delta",
                source=f"engine:zone:{zone.id}",
                payload={"persona_id": persona_id, "zone_id": zone.id, "effect": effect},
            )
        kpi.churn_risk = max(0.0, kpi.churn_risk)
        self.state.global_kpis = KPIState(
            revenue=round(kpi.revenue, 2),
            margin=round(kpi.margin, 2),
            sentiment=round(kpi.sentiment, 2),
            churn_risk=round(kpi.churn_risk, 2),
        )

    def _run_crisis_phase(self, tick: int, resolved: list[ActionIntent]) -> dict[str, Any] | None:
        cards = self.scenario.get("crisis_cards")
        if not isinstance(cards, list) or not cards:
            return None
        rules = self._game_rules()
        if self.rng.random() > max(0.0, min(1.0, rules["crisis_trigger_chance"])):
            return None
        candidates = [item for item in cards if isinstance(item, dict)]
        if not candidates:
            return None
        card = self.rng.choice(candidates)
        card_id = str(card.get("id") or "crisis")
        title = str(card.get("title") or "Market Shock")
        raw_effects = card.get("effects")
        effects = raw_effects if isinstance(raw_effects, dict) else {}
        counter_actions = [
            str(item) for item in card.get("counter_actions", []) if isinstance(item, str)
        ] if isinstance(card.get("counter_actions"), list) else []
        matched = [intent for intent in resolved if intent.action_type in counter_actions]
        mitigation_ratio = min(0.75, 0.2 * len(matched))
        multiplier = 1.0 - mitigation_ratio
        kpi = self.state.global_kpis.model_copy(deep=True)
        kpi.revenue += _as_float(effects.get("revenue")) * multiplier
        kpi.margin += _as_float(effects.get("margin")) * multiplier
        kpi.sentiment += _as_float(effects.get("sentiment")) * multiplier
        kpi.churn_risk += _as_float(effects.get("churn_risk")) * multiplier
        kpi.churn_risk = max(0.0, kpi.churn_risk)
        self.state.global_kpis = KPIState(
            revenue=round(kpi.revenue, 2),
            margin=round(kpi.margin, 2),
            sentiment=round(kpi.sentiment, 2),
            churn_risk=round(kpi.churn_risk, 2),
        )
        self._record_timeline(
            tick=tick,
            message=f"Crisis card: {title} (mitigation {round(mitigation_ratio * 100)}%).",
            source="engine:crisis",
        )
        return {
            "id": card_id,
            "title": title,
            "effects": {
                "revenue": round(_as_float(effects.get("revenue")) * multiplier, 2),
                "margin": round(_as_float(effects.get("margin")) * multiplier, 2),
                "sentiment": round(_as_float(effects.get("sentiment")) * multiplier, 2),
                "churn_risk": round(_as_float(effects.get("churn_risk")) * multiplier, 2),
            },
            "counter_actions": counter_actions,
            "matched_actions": [intent.action_type for intent in matched],
        }

    def _award_points(
        self,
        tick: int,
        active_ids: set[str],
        rolls: dict[str, int],
        resolved: list[ActionIntent],
        kpi_before: KPIState,
        crisis: dict[str, Any] | None,
    ) -> None:
        rules = self._game_rules()
        intent_by_persona = {intent.persona_id: intent for intent in resolved}
        kpi_shift = (
            (self.state.global_kpis.revenue - kpi_before.revenue)
            + (self.state.global_kpis.margin - kpi_before.margin)
            + (self.state.global_kpis.sentiment - kpi_before.sentiment)
            - (self.state.global_kpis.churn_risk - kpi_before.churn_risk)
        )
        for persona_id in active_ids:
            total = self.state.agent_scores.get(persona_id, 0.0)
            total += rules["daily_base_points"]
            total += rules["move_points_per_step"] * float(rolls.get(persona_id, 0))
            intent = intent_by_persona.get(persona_id)
            if intent is not None:
                total += rules["intent_points_multiplier"] * max(0.1, float(intent.confidence))
            if crisis and intent is not None:
                matched = crisis.get("matched_actions")
                if isinstance(matched, list) and intent.action_type in matched:
                    total += 0.7
            total += rules["kpi_points_multiplier"] * (kpi_shift / max(1, len(active_ids)))
            self.state.agent_scores[persona_id] = round(max(0.0, total), 2)
        self._record_tick_event(
            tick=tick,
            event_type="kpi_delta",
            source="engine:scoring",
            payload={"scores": self.state.agent_scores},
        )

    def _apply_resolved_intents(self, tick: int, intents: list[ActionIntent]) -> list[dict[str, Any]]:
        accepted: list[ActionIntent] = []
        rejections: list[dict[str, Any]] = []
        for intent in intents:
            valid, reason = validate_intent(intent, self.state.global_kpis)
            if valid:
                accepted.append(intent)
                self._record_tick_event(
                    tick=tick,
                    event_type="intent_submitted",
                    source=f"subagent:{intent.persona_id}",
                    payload=intent.model_dump(),
                )
            else:
                rejections.append({"persona_id": intent.persona_id, "reason": reason, "intent": intent.model_dump()})
                self._record_tick_event(
                    tick=tick,
                    event_type="intent_rejected",
                    source=f"engine:{intent.persona_id}",
                    payload={"reason": reason, "intent": intent.model_dump()},
                )
                self._record_timeline(tick, f"{intent.persona_id} intent rejected: {reason}", source="engine")
        if accepted:
            self.state.global_kpis = apply_intents_to_kpis(self.state.global_kpis, accepted)
        return rejections

    async def run_stream(self) -> AsyncIterator[dict[str, Any]]:
        yield {"type": "status", "message": "Deep simulation stream started.", "max_ticks": self.state.max_ticks}
        while not self.state.done:
            self.state.tick += 1
            tick = self.state.tick
            personas = self.orchestrator.select_active_personas_for_tick(
                tick=tick,
                churn_risk=self.state.global_kpis.churn_risk,
            )
            active_ids = {persona.id for persona in personas}
            kpi_before = self.state.global_kpis.model_copy(deep=True)
            rolls = self._move_agents(tick=tick, active_persona_ids=active_ids)
            yield progress_event(
                self.state,
                f"Day {tick}: strategists rolled, moved districts, and are planning actions.",
            )

            candidate_intents: list[ActionIntent] = []
            for persona in personas:
                agent = self._agent_by_id(persona.id)
                if agent is not None:
                    agent.status = "acting"
                observation = self._observation_for(persona.id, tick)
                async for event in self.orchestrator.stream_persona(persona, observation):
                    if event.get("type") == "agent_chunk":
                        chunk = str(event.get("chunk") or "")
                        if chunk and agent is not None:
                            agent.transcript = f"{agent.transcript}{chunk}"
                        self._record_tick_event(
                            tick=tick,
                            event_type="agent_thought",
                            source=f"subagent:{persona.id}",
                            payload={"chunk": chunk[:280]},
                        )
                        yield agent_chunk_event(tick, persona.id, chunk)
                        yield world_event(self.state)
                    elif event.get("type") == "agent_tool_call":
                        call = str(event.get("tool_call") or "tool(...)")
                        if agent is not None:
                            agent.tool_calls.append(call)
                            agent.tool_calls = agent.tool_calls[-12:]
                        tick_event = self._record_tick_event(
                            tick=tick,
                            event_type="tool_call",
                            source=f"subagent:{persona.id}",
                            payload={"tool_call": call},
                        )
                        yield tool_call_event(tick, persona.id, call)
                        yield tick_event_to_stream(tick_event)
                    elif event.get("type") == "persona_complete":
                        transcript = str(event.get("transcript") or "")
                        if transcript and agent is not None and not agent.transcript:
                            agent.transcript = transcript
                        intent_payload = event.get("intent")
                        if isinstance(intent_payload, dict):
                            intent = ActionIntent.model_validate(intent_payload)
                            candidate_intents.append(intent)
                            if agent is not None:
                                agent.confidence = intent.confidence
                        if agent is not None and agent.status != "done":
                            agent.status = "idle"
                        message = f"{persona.name} completed day-{tick} reaction."
                        self._record_timeline(tick, message, source=f"subagent:{persona.id}")
                        yield timeline_event(tick, message)

            resolved = resolve_conflicts(candidate_intents, self.state.personas)
            rejections = self._apply_resolved_intents(tick, resolved)
            self._apply_zone_effects(tick, active_ids)
            crisis = self._run_crisis_phase(tick, resolved)
            self._award_points(tick, active_ids, rolls, resolved, kpi_before, crisis)
            if resolved:
                self._record_timeline(tick, f"Applied {len(resolved)} resolved intent(s).", source="engine")
            if rejections:
                self._record_timeline(tick, f"Rejected {len(rejections)} intent(s) this tick.", source="engine")
            if crisis is not None:
                self._record_timeline(
                    tick,
                    f"{crisis.get('title', 'Crisis')} changed market conditions this day.",
                    source="engine:crisis",
                )

            world_delta_event = self._record_tick_event(
                tick=tick,
                event_type="world_delta",
                source="engine",
                payload={
                    "resolved_intents": [intent.model_dump() for intent in resolved],
                    "rejections": rejections,
                    "crisis": crisis,
                    "scores": self.state.agent_scores,
                },
            )
            yield tick_event_to_stream(world_delta_event)
            yield world_event(self.state)

            kpi_event = self._record_tick_event(
                tick=tick,
                event_type="kpi_delta",
                source="engine",
                payload=self.state.global_kpis.model_dump(),
            )
            yield tick_event_to_stream(kpi_event)

            if tick % self.request.summary_cadence_ticks == 0:
                periodic = build_periodic_summary(self.state, self.orchestrator.observer_model)
                self.state.observer_summaries.append(periodic)
                self.state.observer_summaries = self.state.observer_summaries[-30:]
                summary_event = self._record_tick_event(
                    tick=tick,
                    event_type="observer_summary",
                    source="observer",
                    payload=periodic.model_dump(),
                )
                yield {"type": "observer_summary", "tick": tick, "markdown": periodic.markdown}
                yield tick_event_to_stream(summary_event)

            if tick >= self.state.max_ticks:
                self.state.done = True
                for agent in self.state.agents:
                    agent.status = "done"

        report = build_final_report(self.state, self.orchestrator.observer_model)
        result = {
            "response": report.model_dump(mode="json"),
            "seed": self.seed,
            "state": self.state.model_dump(mode="json"),
        }
        yield {"type": "final", **result}
        yield {"type": "done"}

    async def run_to_completion(self) -> dict[str, Any]:
        final_result: dict[str, Any] | None = None
        async for event in self.run_stream():
            if event.get("type") == "final":
                final_result = event
        if final_result is None:
            report = build_final_report(self.state, self.orchestrator.observer_model)
            final_result = {
                "type": "final",
                "response": report.model_dump(mode="json"),
                "seed": self.seed,
                "state": self.state.model_dump(mode="json"),
            }
        return {
            "response": final_result.get("response", {}),
            "seed": final_result.get("seed", self.seed),
            "state": final_result.get("state", self.state.model_dump(mode="json")),
        }
