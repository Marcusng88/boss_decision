from __future__ import annotations

from typing import Any

from .schema import DeepSimulationState
from .schema import TickEvent


def progress_event(state: DeepSimulationState, summary: str) -> dict[str, Any]:
    return {
        "type": "progress",
        "tick": state.tick,
        "max_ticks": state.max_ticks,
        "summary": summary,
    }


def world_event(state: DeepSimulationState) -> dict[str, Any]:
    return {
        "type": "world",
        "tick": state.tick,
        "state": {
            "tick": state.tick,
            "max_ticks": state.max_ticks,
            "kpi": state.global_kpis.model_dump(),
            "scores": state.agent_scores,
            "positions": state.agent_positions,
            "agents": [agent.model_dump() for agent in state.agents],
            "personas": [persona.model_dump() for persona in state.personas],
            "timeline": [item.model_dump(mode="json") for item in state.timeline],
            "map": state.map.model_dump(),
        },
    }


def timeline_event(tick: int, message: str) -> dict[str, Any]:
    return {
        "type": "timeline",
        "tick": tick,
        "message": message,
    }


def agent_chunk_event(tick: int, persona_id: str, chunk: str) -> dict[str, Any]:
    return {
        "type": "agent_chunk",
        "tick": tick,
        "persona_id": persona_id,
        "chunk": chunk,
    }


def tool_call_event(tick: int, persona_id: str, tool_call: str) -> dict[str, Any]:
    return {
        "type": "agent_tool_call",
        "tick": tick,
        "persona_id": persona_id,
        "tool_call": tool_call,
    }


def tick_event_to_stream(event: TickEvent) -> dict[str, Any]:
    return {
        "type": "tick_event",
        "tick": event.tick,
        "event_type": event.type,
        "source": event.source,
        "payload": event.payload,
        "ts": event.ts.isoformat(),
    }
