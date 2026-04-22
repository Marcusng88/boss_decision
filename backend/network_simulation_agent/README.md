# Network Simulation Agent (Phase 3)

Phase-3 backend implementation for the network simulation feature.

## Implemented now

- Contracts and schemas for request/shock/chat payloads.
- NDJSON tick stream with event types:
  - `status`, `progress`, `network_state`, `node_action`, `node_message`,
    `edge_update`, `shock_event`, `observer_summary`, `final`, `done`
- Session artifacts:
  - `backend/network_simulation_agent/runs/{session_id}/session_state.jsonl`
- API integration points:
  - `POST /api/network-simulator/run`
  - `POST /api/network-simulator/stream`
  - `POST /api/network-simulator/{session_id}/shock`
  - `POST /api/network-simulator/{session_id}/observer-chat`
- Real tick engine with deterministic KPI/edge transitions.
- LLM world builder for dynamic node/persona/edge generation (with deterministic fallback).
- LLM node-turn action generation with strict action normalization and validation.
- Context grounding from local docs (`data_context_path`) and optional Tavily snippets.

## Deferred to phase 4+

- Observer chat with explicit event-id citation grounding.
- Full Deep Agents tool runtime per node (current node turns are direct chat-model calls).
