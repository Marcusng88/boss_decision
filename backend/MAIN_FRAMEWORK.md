# Multi-Agent Framework - Implementation Guide

## 1) Purpose

This document is the implementation contract for the backend multi-agent decision engine.

Current state in this repository:
- FastAPI endpoints exist in `main.py`
- Domain agents exist in `agents/` (`HRAgent`, `SalesAgent`)
- `ManagerAgent` exists and can orchestrate domain agents
- Graph orchestration files are not implemented yet (`backend/graph/` is currently empty)

Target state:
- `/api/analyze` runs a complete multi-agent pipeline
- Evidence and final decision are persisted
- Optional LangGraph orchestration can be added without breaking API contracts

## 2) Runtime Flow (Current Target)

```text
Client -> POST /api/analyze
       -> create decision_case
       -> run ManagerAgent.orchestrate(query, context)
       -> collect domain insights (HR + Sales for now)
       -> produce final decision (persona-aware)
       -> persist decision_output + evidence links
       -> return response to frontend
```

## 3) File Responsibilities

### `main.py`
- API boundary and request validation
- Dependency wiring (DB service, agents, manager)
- Endpoint response formatting

### `agents/base_agent.py`
- Shared interface for all domain agents
- Standard output model via `AgentInsight`

### `agents/hr_agent.py`
- Retrieve and analyze HR evidence
- Output HR findings, risks, recommendation, confidence

### `agents/sales_agent.py`
- Retrieve and analyze sales evidence
- Output sales findings, risks, recommendation, confidence

### `agents/manager_agent.py`
- Run all configured agents
- Generate conservative and aggressive views
- Produce final recommendation and rationale

### `db.py`
- All DB reads/writes (decision case, evidence retrieval, decision output persistence)

## 4) Core Data Contracts

### Analyze Request (already used)

```json
{
  "query": "Should we terminate employee 102 for sustained underperformance?",
  "context": "Quarterly review cycle",
  "target_type": "employee",
  "target_id": 102,
  "submitted_by": "ceo@company.com"
}
```

### Agent Insight (from `AgentInsight`)

```json
{
  "agent_name": "HR",
  "findings": ["Average performance score: 2.1/5"],
  "risks": ["PIP not initiated"],
  "recommendation": "Initiate mandatory 60-day PIP",
  "confidence": 0.75,
  "evidence_used": [{"source": "hr_record", "record_id": 12}]
}
```

### Manager Output Shape (from `ManagerAgent.orchestrate`)

```json
{
  "agent_insights": ["...AgentInsight dicts..."],
  "conservative_view": "...",
  "aggressive_view": "...",
  "final_decision": {
    "recommendation": "...",
    "risk_level": "Medium",
    "confidence_score": 77.5,
    "rationale": "...",
    "manager_persona": "conservative"
  }
}
```

### `/api/analyze` Response Contract (implementation-friendly)

```json
{
  "status": "completed",
  "case_id": 123,
  "query": "...",
  "final_decision": {
    "recommendation": "...",
    "risk_level": "Medium",
    "confidence_score": 77.5,
    "rationale": "...",
    "manager_persona": "conservative"
  },
  "agent_insights": ["..."],
  "conservative_view": "...",
  "aggressive_view": "..."
}
```

## 5) Minimal Implementation Plan

### Step 1: Wire agents in `main.py`
- Instantiate `HRAgent(db)` and `SalesAgent(db)`
- Instantiate `ManagerAgent([hr_agent, sales_agent])`
- In `/api/analyze`, call:

```python
result = await manager.orchestrate(
    query=request.query,
    context={
        "target_type": request.target_type,
        "target_id": request.target_id,
        "context": request.context,
        "submitted_by": request.submitted_by,
    },
)
```

### Step 2: Persist outputs
- Save manager final decision to `decision_output`
- Save evidence links (if your schema separates evidence mapping)

### Step 3: Return stable API payload
- Replace placeholder `"processing"` response with completed payload
- Keep keys stable for frontend integration

### Step 4: Add failure boundaries
- If one agent fails: include degraded insight with low confidence, continue orchestration
- If orchestration fails: return HTTP 500 with case_id if created

## 6) Suggested Error Handling Rules

- Validation errors: FastAPI/Pydantic default 422
- DB read/write failures: 500 with actionable message
- Missing target data: do not crash; return low-confidence agent insight
- Confidence bounds: enforce `0.0 <= confidence <= 1.0`

## 7) Optional LangGraph Integration (Next Phase)

Use LangGraph only after the non-graph pipeline is stable.

Proposed graph nodes:
- `retrieve_context`
- `run_hr_agent`
- `run_sales_agent`
- `manager_synthesis`
- `persist_result`

Graph state shape:

```python
class DecisionState(TypedDict):
    query: str
    context: dict
    case_id: int
    agent_insights: list[dict]
    conservative_view: str
    aggressive_view: str
    final_decision: dict
```

## 8) Done Criteria

Implementation is complete when all are true:
- `/api/analyze` executes HR + Sales + Manager end-to-end
- Returns `status: "completed"` with final decision
- Decision output is persisted in DB
- At least one integration test covers successful flow
- At least one failure-path test covers partial agent failure

## 9) Quick Checklist

- [ ] Replace `/api/analyze` placeholder with manager orchestration
- [ ] Persist final decision record
- [ ] Return frontend-ready response schema
- [ ] Add tests for success and degraded mode
- [ ] Document any schema assumptions in `database/README.md`

---

This guide intentionally reflects the current repository (HR + Sales + Manager) and avoids documenting components that are not yet implemented.