from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class DeepSimulationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    max_ticks: int = Field(default=5, ge=1, le=240)
    seed: Optional[int] = Field(default=None, ge=0, le=2_147_483_647)
    scenario_id: str = Field(default="pricing_war_v1", min_length=1, max_length=120)
    min_personas: int = Field(default=3, ge=1, le=12)
    max_personas: int = Field(default=6, ge=1, le=12)
    summary_cadence_ticks: int = Field(default=7, ge=1, le=30)


class WorldZone(BaseModel):
    id: str
    name: str
    x: float = Field(ge=0.0, le=100.0)
    y: float = Field(ge=0.0, le=100.0)
    radius: float = Field(default=12.0, ge=2.0, le=40.0)


class WorldMap(BaseModel):
    width: int = 100
    height: int = 100
    zones: list[WorldZone] = Field(default_factory=list)


class KPIState(BaseModel):
    revenue: float = 0.0
    margin: float = 0.0
    sentiment: float = 0.0
    churn_risk: float = 0.0


class PersonaProfile(BaseModel):
    id: str
    name: str
    role: str
    objective: str
    system_prompt: str
    allowed_paths: list[str] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.1, le=4.0)


class AgentSnapshot(BaseModel):
    id: str
    name: str
    role: str
    x: float
    y: float
    status: Literal["idle", "thinking", "acting", "done"]
    tool_calls: list[str] = Field(default_factory=list)
    transcript: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AgentObservation(BaseModel):
    persona_id: str
    tick: int
    local_view: dict[str, Any] = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)


class ActionIntent(BaseModel):
    persona_id: str
    tick: int
    action_type: Literal["move", "price_adjust", "spend_shift", "campaign", "procurement", "wait"] = "wait"
    args: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale_md: str = ""
    requested_via_tool: bool = False


class TimelineEvent(BaseModel):
    id: str
    tick: int
    message: str
    source: str = "engine"
    ts: datetime = Field(default_factory=datetime.utcnow)


class TickEvent(BaseModel):
    tick: int
    ts: datetime = Field(default_factory=datetime.utcnow)
    type: Literal[
        "agent_thought",
        "tool_call",
        "intent_submitted",
        "intent_rejected",
        "world_delta",
        "kpi_delta",
        "observer_summary",
    ]
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ObserverSummary(BaseModel):
    tick: int
    markdown: str


class DeepSimulationState(BaseModel):
    query: str
    scenario_id: str
    seed: int
    tick: int
    max_ticks: int
    tick_duration_days: int = 1
    map: WorldMap
    agents: list[AgentSnapshot]
    personas: list[PersonaProfile]
    global_kpis: KPIState
    agent_scores: dict[str, float] = Field(default_factory=dict)
    agent_positions: dict[str, int] = Field(default_factory=dict)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    tick_events: list[TickEvent] = Field(default_factory=list)
    observer_summaries: list[ObserverSummary] = Field(default_factory=list)
    done: bool = False


class DeepSimulationFinalResponse(BaseModel):
    summary: str
    key_turning_points: list[str] = Field(default_factory=list)
    recommendation: str
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    periodic_summaries: list[ObserverSummary] = Field(default_factory=list)
    html_slides: str = ""
