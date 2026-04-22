# Network Simulation Agent (Phase 1)

Phase-1 backend skeleton for the network simulation feature.

## Implemented now

- Contracts and schemas for request/shock/chat payloads.
- Deterministic mock tick stream with NDJSON event types:
  - `status`, `progress`, `network_state`, `node_action`, `node_message`,
    `edge_update`, `shock_event`, `observer_summary`, `final`, `done`
- Session artifacts:
  - `backend/network_simulation_agent/runs/{session_id}/session_state.jsonl`
- API integration points:
  - `POST /api/network-simulator/run`
  - `POST /api/network-simulator/stream`
  - `POST /api/network-simulator/{session_id}/shock`
  - `POST /api/network-simulator/{session_id}/observer-chat`

## Deferred to phase 2+

- Real deterministic world-transition math.
- Persistent shock queue + replay guarantees.
- LLM-driven node turns and observer grounding with event ids.
