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

1. **User Query + Agent Selection** → Chat interface sends query + optional `selected_agents` to `POST /api/analyze/stream`
2. **Intent Detection** → LLM determines which agents to invoke + extracts entity context (overridden if user selected agents manually)
3. **Parallel Agent Execution** → Selected domain agents run concurrently via `asyncio.gather`
4. **Evidence Retrieval** → Each agent fetches relevant Supabase tables (with multi-level fallbacks)
5. **LLM Analysis** → Each agent calls Zhipu GLM to analyze its evidence; results streamed via SSE as each completes
6. **Manager Synthesis** → Manager agent calls LLM to generate conservative/aggressive/final decision
7. **Persist + Return** → Decision saved to `decision_case` + `decision_output`, full JSON returned
8. **Frontend Display** → Agent cards appear one-by-one as they stream in; typewriter effect on final verdict

Core design principle: **decisions must be evidence-linked and auditable**, not just free-form LLM output.

---

## Repository Layout

- `frontend/`: React + TypeScript + Vite — ChatGPT/Gemini-style chat interface with streaming
- `frontend/src/components/chat/`: Chat UI components (AgentCard, AgentAvatar, AgentSelector, DecisionResponse, ChatInput, ChatSidebar, etc.)
- `frontend/src/lib/api.ts`: Typed API client — supports both SSE streaming (`analyzeDecisionStream`) and standard fetch (`analyzeDecision`)
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
| `POST /api/analyze` | Standard endpoint — full pipeline, waits for all agents, returns structured decision |
| `POST /api/analyze/stream` | **Preferred endpoint** — SSE streaming; yields events as each agent completes |

### `POST /api/analyze/stream` SSE Event Flow

```
data: {"type": "status", "message": "Detecting intent…"}
data: {"type": "intent", "agents": ["hr", "legal"]}
data: {"type": "agent_start", "agent": "hr"}
data: {"type": "agent_start", "agent": "legal"}
data: {"type": "agent_done", "agent": "hr", "insight": {...}}
data: {"type": "agent_done", "agent": "legal", "insight": {...}}
data: {"type": "status", "message": "Synthesizing perspectives…"}
data: {"type": "synthesis", "conservative": {...}, "aggressive": {...}}
data: {"type": "complete", "result": {...full AnalysisResponse...}}
```

Both endpoints accept `selected_agents: string[]` in the request body to override auto-detection.

### `POST /api/analyze` Flow (non-streaming)

1. `detect_intent(query)` → `{agents, target_type, target_id, query_category}`
2. Override agents if `selected_agents` provided in request
3. `db.create_decision_case(...)` → `case_id`
4. `manager.orchestrate(query, context)` → runs selected agents in parallel
5. `db.save_decision_output(...)` → persists to Supabase
6. Returns `AnalyzeResponse` with `agent_insights`, `conservative_view`, `aggressive_view`, `final_decision`

### Database Service Layer (`backend/db.py`)

Methods for all tables:

| Method | Table |
|---|---|
| `get_employee(id)` | `employee` |
| `search_employees_by_name(name)` | `employee` — ILIKE search across name fields |
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

| Agent | File | Tables Queried | LLM? | Fallback Strategy |
|---|---|---|---|---|
| HR | `hr_agent.py` | `employee`, `hr_record` | ✅ | Rule-based; name search if no ID |
| Sales | `sales_agent.py` | `sales_record` | ✅ | Rule-based |
| Legal | `legal_agent.py` | `legal_policy`, `legal_contract`, `legal_cases` | ✅ | Generic compliance findings |
| Finance | `finance_agent.py` | `finance_record` | ✅ | Employee → dept → general records cascade |
| Marketing | `marketing_agent.py` | `marketing_record` | ✅ | Rule-based |
| Supply Chain | `supply_chain_agent.py` | `supply_record` | ✅ | Rule-based |
| Manager | `manager_agent.py` | — (orchestrator) | ✅ LLM synthesis | Rule-based synthesis |

### HR Agent Data Retrieval (`hr_agent.py`)

Three-step lookup:
1. Direct `employee_id` lookup if `target_id` is set
2. Name-based ILIKE search via `search_employees_by_name()` if `target_name` is set but no ID
3. Returns informative message if employee found but no HR records exist

### Finance Agent Data Retrieval (`finance_agent.py`)

Three-level cascade:
1. Employee-level `finance_record` (filtered by `employee_id`)
2. Department-level `finance_record` (via employee's `dept_id`) if employee records are empty
3. General recent `finance_record` rows as last resort

### Intent Detector (`backend/agents/intent_detector.py`)

- Calls Zhipu LLM with agent domain descriptions
- Returns `{agents: [...], target_type, target_id, query_category}`
- Falls back to keyword matching if LLM fails
- `selected_agents` in the request body overrides this entirely

### Manager Agent (`backend/agents/manager_agent.py`)

- Builds agent registry on init (all 6 domain agents)
- `orchestrate(query, context)`: runs selected agents via `asyncio.gather`
- `_synthesize_with_llm(insights, query)`: LLM produces `conservative`, `aggressive`, `final_decision`
- `_rule_based_synthesis(insights)`: fallback if LLM fails
- `_empty_result(query)`: fallback if no agents return insights

---

## Data Layer

### Supabase Tables (active, as of 2026-04-23)

| Table | Domain |
|---|---|
| `employee` | Core entity (cross-domain anchor) |
| `department` | Org structure |
| `hr_record` | Performance, attendance, warnings, PIP |
| `sales_record` | Deals, revenue, pipeline |
| `finance_record` | Budget, costs, KPIs — may be at dept level, not per-employee |
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

### Chat Interface (`frontend/src/`)

| Component | Location | Purpose |
|---|---|---|
| `Index.tsx` | `pages/` | Main container; uses SSE streaming, incremental state updates |
| `ChatSidebar.tsx` | `components/chat/` | Conversation history, New Chat |
| `ChatMessage.tsx` | `components/chat/` | Renders user bubbles + streaming/static assistant responses |
| `ChatInput.tsx` | `components/chat/` | Auto-resize textarea + AgentSelector row above input |
| `AgentSelector.tsx` | `components/chat/` | Gemini-style toggle pill chips for each agent |
| `AgentAvatar.tsx` | `components/chat/` | Custom SVG cartoon characters per department; exports `AGENT_COLORS` |
| `AgentCard.tsx` | `components/chat/` | Cartoon-styled insight card with gradient header; `AgentCardSkeleton` for in-progress |
| `DecisionResponse.tsx` | `components/chat/` | Streaming mode (live build-up) + static mode (history replay); typewriter on verdict |
| `EmptyState.tsx` | `components/chat/` | Welcome screen showing 6 cartoon agents + sample queries |
| `api.ts` | `lib/` | `analyzeDecisionStream()` (SSE) + `analyzeDecision()` (standard fetch) |

### Streaming Frontend Flow

1. User submits query (optional: selects agents via chips)
2. Message immediately shows streaming state with live "thinking bar"
3. Backend SSE events arrive → state updated incrementally:
   - `intent` → shows which agents will run with status badges
   - `agent_start` → agent shows as spinning skeleton card
   - `agent_done` → skeleton replaced with filled cartoon card
   - `synthesis` → Conservative/Aggressive panels fade in
   - `complete` → final decision card appears with typewriter verdict
4. On complete, `streaming` state replaced with `data + stage: 'decision'` for persistence

### Cartoon Agent Avatars (`AgentAvatar.tsx`)

Each agent has a distinct custom SVG character:

| Agent | Key Design Elements | Gradient |
|---|---|---|
| HR | Purple buns, clipboard | `violet-500 → purple-700` |
| Legal | White lawyer wig, scales | `blue-600 → blue-900` |
| Sales | Spiky hair, rising chart | `emerald-400 → green-700` |
| Finance | Round glasses, calculator | `yellow-400 → amber-600` |
| Marketing | Wild star hair, megaphone | `pink-400 → rose-700` |
| Supply Chain | Hard hat, box/package | `orange-400 → red-600` |

`AGENT_COLORS` exported from `AgentAvatar.tsx` provides per-agent `gradient`, `ring`, `text`, `light` Tailwind classes used across `AgentCard`, `AgentSelector`, `DecisionResponse`, and `EmptyState`.

### Frontend API Contract

`POST /api/analyze` and `POST /api/analyze/stream` both accept:
```typescript
{
  query: string
  selected_agents?: string[]   // overrides auto-detect
}
```

Response shape (both endpoints):
```typescript
{
  case_id: number | null
  query: string
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
.venv/Scripts/python.exe main.py
# or: .venv/Scripts/python.exe -m uvicorn main:app --reload
# API at http://localhost:8000  |  Docs at http://localhost:8000/docs
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

### Working ✅

- Full intent detection → agent selection → parallel execution → LLM analysis → manager synthesis
- All 6 domain agents with Zhipu LLM + rule-based fallback
- **SSE streaming**: `POST /api/analyze/stream` streams agent results as they complete
- **Agent selector**: User can manually choose agents via toggle chips; overrides auto-detect
- **Cartoon agent avatars**: Custom SVG characters per department in all cards + empty state
- **Live progress display**: Spinning placeholders while agents run, cards appear one-by-one
- **Typewriter effect** on final decision verdict
- **Finance data cascade**: Employee → dept → general records fallback
- **HR name search**: `search_employees_by_name()` handles queries without explicit employee ID
- ChatGPT/Gemini-style chat with conversation history sidebar
- Supabase connected: all tables accessible

### Still Needed

- OCR/ingestion pipeline (Kai Huang's task)
- Vector retrieval for semantic evidence search
- Integration tests for `/api/analyze/stream` happy path
- `/extra-usage` plan for sustained hackathon sessions

---

## Team Ownership

- **Keith**: DB structure, backend foundation, finance agent
- **Kai Huang**: OCR + AI extraction/classification pipeline
- **Marcus**: Manager personas and synthesis strategy
- **Yihao**: HR + Legal agents, chat UI redesign, streaming architecture, cartoon UI
- **Jialih**: Sales + Marketing + Supply Chain agents

---

## Practical Notes

- `legal_policy` table (not `legal_record`) — already updated everywhere in code
- All agents gracefully degrade: LLM failure → rule-based fallback → still returns `AgentInsight`
- Manager agent lazy-loads domain agents on first instantiation
- CORS allows `localhost:8080` and `localhost:8081` (Vite may use either)
- Finance records in Supabase may not be keyed to individual employees — agent now cascades to dept/general level automatically
- `AGENT_COLORS` in `AgentAvatar.tsx` is the single source of truth for per-agent color theming across the entire UI
- SSE streaming uses `asyncio.create_task` inside the FastAPI generator — works correctly with uvicorn's async event loop
- 78% of session usage comes from subagent-heavy operations — spawn subagents sparingly
