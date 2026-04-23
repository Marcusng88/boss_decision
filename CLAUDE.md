# CLAUDE.md

## Project Summary

**Project**: AI Boss Decision Engine  
**Type**: Hackathon multi-agent decision support system  
**Repository**: Monorepo with React frontend + Python FastAPI backend + PostgreSQL/Supabase database

This project simulates realistic executive decision-making using specialized domain agents (HR, Sales, Legal, Finance, Marketing, Supply Chain) and a Manager Agent that synthesizes recommendations into one explainable decision.

Primary example decisions include:
- Employee termination (e.g., John Tan / employee `1023`)
- Market expansion (e.g., Singapore phased entry)
- Emergency procurement approvals

---

## High-Level Architecture

The system flow follows this pipeline:

1. **User Query** → Chat interface sends query to `POST /api/analyze`
2. **Intent Detection** → LLM determines which agents to invoke + extracts entity context
3. **Parallel Agent Execution** → Selected domain agents run concurrently via `asyncio.gather`
4. **Evidence Retrieval** → Each agent fetches relevant Supabase tables
5. **LLM Analysis** → Each agent calls Zhipu GLM to analyze its evidence
6. **Manager Synthesis** → Manager agent calls LLM to generate conservative/aggressive/final decision
7. **Persist + Return** → Decision saved to `decision_case` + `decision_output`, full JSON returned
8. **Frontend Display** → Staged animated reveal (agent cards → perspectives → final decision)

Core design principle: **decisions must be evidence-linked and auditable**, not just free-form LLM output.

---

## Repository Layout

- `frontend/`: React + TypeScript + Vite — ChatGPT-style chat interface
- `frontend/src/components/chat/`: New chat UI components (AgentCard, DecisionResponse, ChatInput, ChatSidebar, etc.)
- `frontend/src/lib/api.ts`: Typed API client calling `POST /api/analyze`
- `backend/`: FastAPI API, Supabase integration, full multi-agent system
- `backend/agents/`: All 6 domain agents + manager + intent detector + LLM client
- `backend/database/`: PostgreSQL schema and seed data + database docs

---

## LLM Configuration

**Primary LLM: Zhipu AI / GLM (OpenAI-compatible)**

Set in `backend/.env`:
```
ZHIPU_API_KEY=sk-bbedded01c987a960652f6c7a8fb3c82469cac8d356cf861
ZHIPU_BASE_URL=https://api.ilmu.ai/v1
ZHIPU_MODEL=ilmu-glm-5.1
```

The LLM client lives in `backend/agents/llm_client.py`. It uses the `openai` Python SDK with a custom base URL. All agents call `llm_json(system_prompt, user_msg)` which returns a parsed JSON dict.

---

## Backend (Python) — Current Implementation

### Runtime & Config

- `backend/config.py` — pydantic-settings config; includes Supabase + Zhipu AI fields
- `backend/main.py` — FastAPI app; CORS allows `:8080`, `:8081`, `:3000`, `:5173`
- Virtual environment: `backend/.venv/` — run with `.venv/Scripts/python.exe main.py`

### API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Status check |
| `GET /api/health` | Health + Supabase connectivity |
| `GET /api/employees/{id}` | Employee profile + HR + sales records |
| `GET /api/cases/{case_id}` | Decision case evidence + output |
| `POST /api/analyze` | **Main endpoint** — full multi-agent pipeline, returns structured decision |

### `POST /api/analyze` Flow

1. `detect_intent(query)` → `{agents, target_type, target_id, query_category}`
2. `db.create_decision_case(...)` → `case_id`
3. `manager.orchestrate(query, context)` → runs selected agents in parallel
4. `db.save_decision_output(...)` → persists to Supabase
5. Returns `AnalyzeResponse` with `agent_insights`, `conservative_view`, `aggressive_view`, `final_decision`

### Database Service Layer (`backend/db.py`)

Methods for all tables:

| Method | Table |
|---|---|
| `get_employee(id)` | `employee` |
| `get_employee_hr_records(id)` | `hr_record` |
| `get_employee_sales_records(id)` | `sales_record` |
| `get_legal_policies(category?)` | `legal_policy` ← **renamed from `legal_record`** |
| `get_legal_contracts(employee_id?)` | `legal_contract` |
| `get_legal_cases(employee_id?)` | `legal_cases` |
| `get_finance_records(employee_id?, dept_id?)` | `finance_record` |
| `get_marketing_records(period?)` | `marketing_record` |
| `get_supply_records(period?)` | `supply_record` |
| `create_decision_case(...)` | `decision_case` |
| `save_decision_output(...)` | `decision_output` |

---

## Agent System (Python)

### Base Contract (`backend/agents/base_agent.py`)

`AgentInsight` Pydantic model fields:
- `agent_name`, `emoji`, `findings`, `risks`, `recommendation`, `confidence`
- `evidence_used`, `data_summary`, `metric_value`, `trend` ("up"/"down"/"flat")

### All Implemented Agents

| Agent | File | Tables Queried | LLM? |
|---|---|---|---|
| HR | `hr_agent.py` | `employee`, `hr_record` | ✅ (rule-based fallback) |
| Sales | `sales_agent.py` | `sales_record` | ✅ |
| Legal | `legal_agent.py` | `legal_policy`, `legal_contract`, `legal_cases` | ✅ |
| Finance | `finance_agent.py` | `finance_record` | ✅ |
| Marketing | `marketing_agent.py` | `marketing_record` | ✅ |
| Supply Chain | `supply_chain_agent.py` | `supply_record` | ✅ |
| Manager | `manager_agent.py` | — (orchestrator) | ✅ LLM synthesis |

### Intent Detector (`backend/agents/intent_detector.py`)

- Calls Zhipu LLM with agent domain descriptions
- Returns `{agents: [...], target_type, target_id, query_category}`
- Falls back to keyword matching if LLM fails

### Manager Agent (`backend/agents/manager_agent.py`)

- Builds agent registry on init (all 6 domain agents)
- `orchestrate(query, context)`: runs selected agents via `asyncio.gather`
- LLM synthesis produces `conservative`, `aggressive`, `final_decision`
- Rule-based fallback if LLM fails

---

## Data Layer

### Supabase Tables (active, as of 2026-04-23)

| Table | Domain |
|---|---|
| `employee` | Core entity (cross-domain anchor) |
| `department` | Org structure |
| `hr_record` | Performance, attendance, warnings, PIP |
| `sales_record` | Deals, revenue, pipeline |
| `finance_record` | Budget, costs, KPIs |
| `marketing_record` | Campaigns, ROI |
| `supply_record` | Inventory, procurement |
| `legal_policy` | Policies, compliance rules (was `legal_record`) |
| `legal_contract` | Employee contracts |
| `legal_cases` | Legal case history |
| `source_document` | OCR pipeline tracking |
| `decision_case` | User decision queries |
| `case_evidence` | Evidence links for explainability |
| `decision_output` | Final manager verdicts |

**Important:** The legal table was renamed from `legal_record` to `legal_policy` in Supabase. All db.py methods and the legal agent already use the new name.

---

## Frontend (React + Vite + Tailwind)

### New Chat Interface (`frontend/src/`)

Completely redesigned as a ChatGPT/Gemini-style chat interface:

| Component | Location | Purpose |
|---|---|---|
| `Index.tsx` | `pages/` | Main container, conversation state, API calls |
| `ChatSidebar.tsx` | `components/chat/` | Conversation history, New Chat |
| `ChatMessage.tsx` | `components/chat/` | User/assistant message bubbles |
| `ChatInput.tsx` | `components/chat/` | Auto-resize textarea, Enter to send |
| `DecisionResponse.tsx` | `components/chat/` | Staged reveal: agents → perspectives → decision |
| `AgentCard.tsx` | `components/chat/` | Individual agent insight card with metric + trend |
| `EmptyState.tsx` | `components/chat/` | Welcome screen with sample queries |
| `api.ts` | `lib/` | Typed fetch client for `POST /api/analyze` |

### Staged Animation Flow

When API response arrives, reveal happens in 3 stages:
1. `agents` (0ms) — Agent insight cards appear
2. `perspectives` (1400ms) — Conservative vs Aggressive views
3. `decision` (2200ms) — Final decision gradient card

### Frontend API Contract

`POST /api/analyze` response fields consumed by frontend:
```typescript
{
  agents_invoked: string[]
  agent_insights: { agent_name, emoji, findings, risks, recommendation,
                    confidence, data_summary, metric_value, trend }[]
  conservative_view: { recommendation, reasoning }
  aggressive_view: { recommendation, reasoning }
  final_decision: { verdict, reasoning, risk_level, confidence_score }
}
```

---

## Setup & Run

### Backend

```bash
cd backend
# Activate venv
.venv/Scripts/python.exe main.py
# or: .venv/Scripts/python.exe -m uvicorn main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:8080 (or 8081 if 8080 is occupied)
```

### Environment Variables (`backend/.env`)

```
SUPABASE_URL=https://fjxhldbbjkxczjiyjtam.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
ZHIPU_API_KEY=sk-bbedded01c987a960652f6c7a8fb3c82469cac8d356cf861
ZHIPU_BASE_URL=https://api.ilmu.ai/v1
ZHIPU_MODEL=ilmu-glm-5.1
```

---

## Current State

### Working Today ✅

- Full intent detection → agent selection → parallel execution → LLM analysis → manager synthesis
- All 6 domain agents implemented with Zhipu LLM + rule-based fallback
- `POST /api/analyze` returns real AI-generated decisions based on Supabase data
- ChatGPT-style chat interface with conversation history and animated agent reveal
- Supabase connected: all tables accessible including `legal_policy`, `legal_contract`, `legal_cases`

### Still Needed

- OCR/ingestion pipeline (Kai Huang's task)
- Vector retrieval for semantic evidence search
- Integration tests for `/api/analyze` happy path
- `/extra-usage` plan for sustained hackathon sessions

---

## Team Ownership

- **Keith**: DB structure, backend foundation, finance agent
- **Kai Huang**: OCR + AI extraction/classification pipeline
- **Marcus**: Manager personas and synthesis strategy
- **Yihao**: HR + Legal agents, chat UI redesign
- **Jialih**: Sales + Marketing + Supply Chain agents

---

## Practical Notes

- `legal_policy` table (not `legal_record`) — already updated everywhere in code
- All agents gracefully degrade: LLM failure → rule-based fallback → still returns `AgentInsight`
- Manager agent lazy-loads domain agents on first instantiation
- CORS allows `localhost:8080` and `localhost:8081` (Vite may use either)
- 78% of session usage comes from subagent-heavy operations — spawn subagents sparingly
