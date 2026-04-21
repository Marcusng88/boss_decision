# AI Boss Decision Engine

Multi-agent decision support system for strategic business questions. Uses domain-specialist agents (HR, Sales, Legal, Finance, Marketing, Supply Chain) to analyze company data and produce explainable decisions.

## Project Overview

**Goal**: Simulate realistic company decision-making using AI agents that retrieve evidence, debate perspectives, and synthesize a final recommendation.

**Example queries**:
- "Should we fire employee John Tan?"
- "Should we expand to Singapore market?"
- "Should we acquire BetaCorp?"

**Key Features**:
- **7-stage pipeline**: Data acquisition → OCR → Structuring → Retrieval → Multi-agent reasoning → Manager decision → Explainable output
- **Entity linking**: Cross-domain data relationships (HR ↔ Sales ↔ Legal)
- **Evidence tracking**: Every decision shows which records were used
- **Manager personas**: Conservative vs Aggressive decision strategies

## Repository Structure

```
boss_decision/
├── frontend/              # React + Vite + TypeScript UI
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── lib/           # Decision engine (currently mock)
│   │   └── pages/         # Main app page
│   ├── package.json
│   └── vite.config.ts
│
├── backend/               # Backend services (to be implemented)
│   └── database/          # SQLite schema + seed data
│       ├── schema.sql     # Full database schema
│       ├── seed.sql       # Sample data (3 companies, 22 employees)
│       └── README.md      # Database setup instructions
│
├── databasestructure.md   # Database design doc
├── questionstoconsider.md # Architecture + design decisions
└── README.md              # This file
```

## Quick Start

### 1. Frontend (UI Demo)

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to see the UI.

**Current state**: UI is fully functional with **mock data**. Enter any question to see the multi-stage reasoning flow.

### 2. Database Setup

```bash
cd backend/database
sqlite3 decision_engine.db < schema.sql
sqlite3 decision_engine.db < seed.sql
```

See [`backend/database/README.md`](backend/database/README.md) for details.

**Current state**: Schema + seed data ready. **Not yet connected to frontend**.

### 3. Backend API (Next Step)

**Status**: Not yet implemented.

**What's needed**:
- API server (Express, FastAPI, or similar)
- Database connection layer
- Evidence retrieval endpoints
- Agent orchestration logic
- OCR pipeline integration (GLM-4V or similar)

See [Task Distribution](#task-distribution) below.

## Architecture (7 Stages)

See [`questionstoconsider.md`](questionstoconsider.md) for full details.

1. **Data Acquisition**: Simulate messy company documents (PDFs, images, CSVs)
2. **Data Normalization**: OCR → LLM → Structured Markdown
3. **Data Structuring & Linking**: Entity resolution (cross-table relationships)
4. **Knowledge Storage & Retrieval**: SQL DB + Vector DB (semantic search)
5. **Multi-Agent Reasoning**: Domain agents produce structured insights
6. **Manager Decision Engine**: Aggregate conflicting recommendations → final verdict
7. **User Interaction**: Chat interface + structured output panels

## Database Schema

See [`databasestructure.md`](databasestructure.md) for entity descriptions.

**Core entities**:
- `company`, `department`, `employee`
- `source_document` (OCR tracking)

**Domain records**:
- `hr_record`, `sales_record`, `finance_record`, `marketing_record`, `supply_record`, `legal_record`

**Decision tracking**:
- `decision_case` (user queries)
- `case_evidence` (explainability: which records were used)
- `decision_output` (final verdict + reasoning)

## Task Distribution (Phase 1)

| Person | Task |
| --- | --- |
| **Keith** | Data Agent + database structure + data source + basic UI |
| **Kai Haung** | AI extraction & classification (OCR → structured data) |
| **Marcus** | Subagent personas (manager decision strategies) |
| **Yihao** | Human Resource Agent + Legal Agent |
| **Jialih** | Sales Agent + Marketing Agent + Supply Chain Agent |

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query
- **Routing**: React Router

### Backend (In Progress)
- **Database**: PostgreSQL (Supabase cloud)
- **API**: Node.js + Express OR Python + FastAPI (to be implemented)
- **OCR/LLM**: GLM-4V (Kai Haung's task)
- **Vector DB**: Chroma OR FAISS (semantic search)

## Development Roadmap

### ✅ Completed
- [x] Frontend UI with mock data
- [x] Database schema design
- [x] Seed data (3 companies, realistic scenarios)
- [x] Monorepo structure

### 🚧 In Progress
- [ ] Backend API scaffolding (Keith)
- [ ] OCR pipeline (Kai Haung)
- [ ] Manager personas (Marcus)
- [ ] Agent implementations (Yihao, Jialih)

### 📋 Next Steps
1. **Create backend API**:
   - Database connection module
   - `/api/analyze` endpoint (submit query)
   - `/api/cases/:id` endpoint (get case + evidence)
2. **Connect frontend to backend**:
   - Replace mock `analyze()` in `src/lib/decision-engine.ts`
   - Add API client (fetch/axios)
3. **Implement evidence retrieval**:
   - SQL queries for structured data
   - Vector search for semantic matching
4. **Build agent pipeline**:
   - HR Agent, Sales Agent, Legal Agent, etc.
   - Manager aggregation logic
5. **Add OCR pipeline**:
   - File upload endpoint
   - PDF/image → structured data extraction

## Demo Scenarios (Pre-loaded)

### Scenario 1: Fire Employee?
- **Query**: "Should we fire employee John Tan (ID 4)?"
- **Context**: Underperforming sales exec, 2 consecutive bad reviews
- **Decision**: "DO NOT FIRE — Initiate 60-day PIP"
- **Reasoning**: Replacement cost (RM 65k) > savings. PIP preserves optionality.

### Scenario 2: Market Expansion?
- **Query**: "Should we expand to Singapore market?"
- **Context**: 3 inbound enterprise leads, setup cost RM 1.8M
- **Decision**: "EXPAND — Phased entry (remote sales pod first)"
- **Reasoning**: Demand signals strong but unproven. De-risk with 6-month test.

### Scenario 3: Emergency Procurement?
- **Query**: "Should we emergency-procure forklift batteries?"
- **Context**: Critical shortage in 4 weeks, operations downtime risk
- **Decision**: "APPROVE — Order 30 batteries immediately"
- **Reasoning**: Downtime cost (RM 400k/week) >> procurement cost (RM 85k).

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test locally
4. Submit PR with description

## Team Communication

- **Design decisions**: See `questionstoconsider.md`
- **Database changes**: Update `schema.sql` + `seed.sql`, document in PR
- **Frontend changes**: Follow existing component patterns in `src/components/`
- **Backend changes**: Document API endpoints in `backend/README.md` (to be created)

## Questions?

See [`questionstoconsider.md`](questionstoconsider.md) for detailed architecture discussions and design rationale.

---

**Hackathon Goal**: Demonstrate a working multi-agent decision system with real data retrieval, explainable reasoning, and a polished UI.
