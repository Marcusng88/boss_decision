# Deep Simulation 2D World Plan (Deep Agents)

## Objective
Build a separate "Deep Simulation" mode where persona subagents act inside a deterministic 2D world over discrete ticks, stream their live progress to UI, and produce an observer report at the end.

## Scope Decisions
- In scope: 2D simulation engine, Deep Agents orchestration, real-time subagent streaming, observer report, replay timeline.
- Out of scope (v1): multiplayer, full game physics, open-world map editing, voice interaction.

## Technical Research Basis (LangChain Deep Agents)
This plan is based on the following Deep Agents docs and APIs:
- Deep Agents overview: https://docs.langchain.com/oss/python/deepagents/overview
- Deep Agents customization (`create_deep_agent` options): https://docs.langchain.com/oss/python/deepagents/customization
- Deep Agents streaming (`stream_mode`, `subgraphs=True`, namespace routing): https://docs.langchain.com/oss/python/deepagents/streaming
- Subagents (specialized + general-purpose + `response_format`): https://docs.langchain.com/oss/python/deepagents/subagents
- Async subagents (non-blocking background tasks): https://docs.langchain.com/oss/python/deepagents/async-subagents
- Backends and permissions (`CompositeBackend`, `FilesystemPermission`): https://docs.langchain.com/oss/python/deepagents/backends
- Harness capabilities (task tool, filesystem, context management): https://docs.langchain.com/oss/python/deepagents/harness
- Frontend patterns for Deep Agents streaming: https://docs.langchain.com/oss/python/deepagents/frontend/overview

## Core Architecture
### 1) Deterministic World Engine
- Owns authoritative `WorldState` and tick progression.
- Applies validated actions in deterministic order.
- Emits typed `TickEvent` objects.

### 2) Supervisor Deep Agent
- Creates coordination decisions, task assignments, and global strategy updates.
- Delegates to persona subagents for per-persona intent.
- Uses Deep Agents subagent tasking for context isolation.

### 3) Persona Subagents
- One subagent per persona (consumer psychologist, ops lead, finance lead, etc.).
- Input: limited local observation + persona memory + goal constraints.
- Output: freeform rationale plus constrained `ActionIntent` payload.

### 4) Action Validator and Resolver
- Validates each `ActionIntent` against world rules (budget, movement bounds, cooldown).
- Resolves conflicts (priority + tie-break rules) before applying updates.

### 5) Observer Agent
- Consumes timeline and KPI series.
- Produces final report with narrative, turning points, and recommendations.

### 6) Streaming Gateway (SSE)
- Streams Deep Agents chunks and world events to frontend in one event bus.
- Routes subagent stream chunks by namespace (`tools:<id>` pattern in docs).

## Data Contracts (v1)
```text
WorldState:
  tick: int
  map: {width, height, zones[]}
  entities: [{id, type, x, y, state, resources}]
  global_kpis: {revenue, margin, sentiment, churn_risk, ...}

AgentObservation:
  persona_id: str
  tick: int
  local_view: {...}
  private_memory_ref: str
  goals: [str]
  constraints: {...}

ActionIntent:
  persona_id: str
  tick: int
  action_type: enum(move|trade|influence|wait)
  args: object
  confidence: float
  rationale_md: str

TickEvent:
  tick: int
  ts: iso8601
  type: enum(agent_thought|tool_call|intent_submitted|intent_rejected|world_delta|kpi_delta)
  source: main|subagent:<id>|engine
  payload: object
```

## Runtime Sequence Per Tick
1. Build `AgentObservation` for each active persona.
2. Supervisor delegates work to persona subagents.
3. Stream subagent tokens and tool events in real time (`stream_mode=["updates","messages"]`, `subgraphs=True`, `version="v2"`).
4. Parse `ActionIntent` from each subagent output.
5. Validate and resolve intents.
6. Apply world update and compute KPI deltas.
7. Emit `TickEvent` and render map updates.
8. Continue until stop condition (`max_ticks` or terminal KPI).

## Deep Agents Implementation Strategy
### A) Supervisor agent
- Use `create_deep_agent` for orchestrator logic.
- Keep supervisor output concise and orchestration-focused.
- Allow delegation to custom persona subagents.

### B) Persona agent behavior
- Keep final transport format as typed `ActionIntent`.
- Keep reasoning freeform markdown for rich UI streaming.
- Do not force all internal reasoning into strict JSON.

### C) Backend and permissions
- Use `CompositeBackend`:
  - default: `StateBackend()` for ephemeral run files.
  - routed: `/memories/` to `StoreBackend(...)` for persistent persona memory.
- Restrict file paths with `FilesystemPermission` allowlists per persona role.

### D) Streaming transport
- Use Deep Agents stream namespaces to map chunks to correct subagent cards.
- Use `messages` for token-level transcript.
- Use `updates` for step/progress and tool lifecycle.

## Suggested Folder Bootstrap
```text
backend/simulator_agent/src/deep_simulation/
  __init__.py
  schema.py              # WorldState/ActionIntent/TickEvent models
  engine.py              # deterministic tick engine
  rules.py               # validation/conflict resolution
  orchestrator.py        # supervisor deep agent orchestration
  personas.py            # persona configs and prompts
  observer.py            # observer report generation
  stream_adapter.py      # normalize deepagents stream chunks to frontend events
  scenarios/
    pricing_war_v1.yaml

backend/simulator_agent/tests/deep_simulation/
  test_engine_ticks.py
  test_action_validation.py
  test_conflict_resolution.py
  test_stream_routing.py

frontend/src/components/simulator/deep/
  DeepSimulationLayout.tsx
  WorldCanvas2D.tsx
  SubagentSwarmPanel.tsx
  AgentTranscriptPanel.tsx
  TimelineBar.tsx
```

## Milestones and Exit Criteria
### M1 - Engine Skeleton (2-3 days)
- Deliver: deterministic tick loop + state schema + one scenario loader.
- Exit: same seed gives identical tick outcomes.

### M2 - Persona Intents (2-4 days)
- Deliver: supervisor + 3 persona subagents + `ActionIntent` parsing.
- Exit: >95% ticks produce valid intents without fallback.

### M3 - Streaming UI (3-5 days)
- Deliver: left-center-right layout, live map, live subagent transcript, tool call timeline.
- Exit: token streaming visible during generation, not only after completion.

### M4 - Observer and Report (1-2 days)
- Deliver: observer summary, KPI chart, key turning points.
- Exit: final report references concrete tick events and KPI deltas.

### M5 - Reliability Pass (2-3 days)
- Deliver: retry policy, timeout handling, graceful degraded mode.
- Exit: no crash under 100-tick runs with 6 subagents.

## Risks and Mitigations
- Risk: LLM output drift breaks action parsing.
- Mitigation: strict action schema at engine boundary; keep freeform only for transcript.

- Risk: stream lag or UI jank.
- Mitigation: event throttling + virtualized transcript rendering + canvas-only world layer.

- Risk: context bloat in long simulations.
- Mitigation: delegate heavy work to subagents and keep supervisor summaries short.

- Risk: unsafe filesystem access.
- Mitigation: route-limited backends + explicit permission rules.

## Open Decisions Before Implementation
- Tick duration mapping (`1 tick = 1 day` vs `1 week`).
- Max active personas per run (recommend start with 4-6).
- Conflict resolution policy (priority vs weighted confidence).
- Observer cadence (final-only vs every 10 ticks).

## Success Metrics (Judge-Facing)
- Real-time subagent streams visible and attributable by persona.
- World state visibly changes per tick in 2D map.
- End report explains why outcomes happened with timeline references.
- Simulation replay is deterministic for the same seed.
