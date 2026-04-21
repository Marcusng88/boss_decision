# Database Setup

This folder contains the PostgreSQL/Supabase database schema and seed data for the AI Boss Decision Engine.

## Files

- `schema.sql` - Complete PostgreSQL schema with all tables, foreign keys, and indexes
- `seed.sql` - Realistic sample data (43 employees, 50+ records per table, 3 decision cases)

## Quick Start

### Option 1: Supabase Dashboard (Recommended)

1. **Create Supabase Project**: Go to [https://supabase.com](https://supabase.com) and create a new project
2. **Run Schema**:
   - Open Supabase Dashboard → SQL Editor
   - Copy contents of `schema.sql`
   - Paste and run
3. **Load Seed Data**:
   - Copy contents of `seed.sql`
   - Paste and run in SQL Editor
4. **Verify**:
   ```sql
   SELECT COUNT(*) FROM employee;  -- Should return 43
   SELECT COUNT(*) FROM decision_case;  -- Should return 3
   ```

### Option 2: Local PostgreSQL (Development)

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from https://www.postgresql.org/download/
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres -c "CREATE DATABASE decision_engine;"

# Load schema and seed data
psql -U postgres -d decision_engine -f backend/database/schema.sql
psql -U postgres -d decision_engine -f backend/database/seed.sql

# Verify
psql -U postgres -d decision_engine -c "SELECT COUNT(*) FROM employee;"
```

### Option 3: Node.js Script (Supabase Connection)

```javascript
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

const supabase = createClient(
  'YOUR_SUPABASE_URL',
  'YOUR_SUPABASE_SERVICE_KEY'
);

async function initDB() {
  const schema = fs.readFileSync('./backend/database/schema.sql', 'utf8');
  const seed = fs.readFileSync('./backend/database/seed.sql', 'utf8');
  
  // Run via Supabase REST API or use pg client
  console.log('Run schema and seed files in Supabase SQL Editor');
}

initDB();
```

### Option 4: Python Script (PostgreSQL)

```python
import psycopg2

conn = psycopg2.connect(
    host="YOUR_SUPABASE_HOST",
    database="postgres",
    user="postgres",
    password="YOUR_PASSWORD"
)
cursor = conn.cursor()

# Load schema
with open('backend/database/schema.sql', 'r') as f:
    cursor.execute(f.read())

# Load seed data
with open('backend/database/seed.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
conn.close()
print('Database initialized!')
```

## Database Structure

### Core Entities
- `department` - Agent-aligned departments (7 depts: Engineering, Sales, Marketing, HR, Finance, Legal, Supply Chain)
- `employee` - Central employee entity (enables cross-domain linking across all tables)
- `source_document` - Original documents (OCR pipeline tracking + explainability)

### Domain-Specific Records
- `hr_record` - Performance reviews, attendance, warnings, PIP status
- `sales_record` - Revenue contribution, deals closed, pipeline
- `finance_record` - Salaries, budgets, expenses, KPIs
- `marketing_record` - Campaign metrics, ROI, channels
- `supply_record` - Inventory levels, demand forecasts, procurement
- `legal_record` - Company policies, compliance rules, legal constraints

### Decision System
- `decision_case` - User queries submitted to the system
- `case_evidence` - Links cases to relevant records (explainability layer)
- `decision_output` - Final manager verdicts with multi-agent rationale

## Sample Data Overview

### Single Company: TechVenture Solutions (SaaS Platform)
- **43 employees** across 7 departments
- **Department structure (agent-aligned)**:
  - Engineering (101): 12 employees
  - Sales (102): 10 employees (includes underperformer John Tan #1023)
  - Marketing (103): 7 employees
  - HR (104): 4 employees
  - Finance (105): 5 employees
  - Legal (106): 2 employees
  - Supply Chain (107): 3 employees

### Key Data Volumes (Realistic IDs)
- Employees: 1001-1050 range (43 active)
- Source documents: 501-525 (25 documents)
- HR records: 2001-2040 (40 performance reviews)
- Sales records: 3001-3043 (43 deals across Q3 2025 - Q1 2026)
- Finance records: 4001-4034 (34 salary/budget records)
- Marketing records: 5001-5032 (32 campaign metrics)
- Supply records: 6001-6030 (30 inventory/procurement records)
- Legal records: 7001-7012 (12 company policies)

### Main Demo Scenarios

#### Case 8001: Terminate Underperforming Employee?
- **Target**: John Tan (employee_id 1023), Sales Executive
- **Context**: 2 consecutive bad performance reviews (Q4 2025: 2.1/5, Q1 2026: 2.0/5)
- **Evidence**: 15 linked records (HR reviews, sales data, legal policies, financial costs)
- **Decision**: "DO NOT TERMINATE - Initiate 60-day PIP first" (Conservative stance)
- **Reasoning**: Legal requires PIP completion before termination. Replacement cost RM 77k + 3-month ramp outweighs immediate savings.

#### Case 8002: Singapore Market Expansion?
- **Context**: 3 inbound enterprise leads, competitor entered market Q4 2025
- **Evidence**: 5 linked records (legal requirements, financial capacity, marketing reach)
- **Decision**: "EXPAND - Phased entry via remote sales pod (6 months), then full office if KPIs hit"
- **Reasoning**: Demand signals real but unproven. RM 400k pilot limits risk vs RM 1.8M full commitment.

#### Case 8003: Emergency AWS Credit Procurement?
- **Context**: Current inventory 850k, forecast 950k, 11% shortage flagged
- **Evidence**: 5 linked records (supply shortage, infrastructure budget, legal emergency procurement policy)
- **Decision**: "APPROVE - Order 200k credits immediately (RM 200k)"
- **Reasoning**: Service downtime risk (RM 400k/week) far exceeds procurement cost.

## Sample Queries

```sql
-- Get all sales employees
SELECT * FROM employee WHERE dept_id = 102;

-- Get performance records for John Tan (employee 1023)
SELECT * FROM hr_record WHERE employee_id = 1023 ORDER BY period;

-- Sales leaderboard (Q1 2026)
SELECT e.name, e.role, SUM(s.amount) as total_revenue, COUNT(s.sales_id) as deals_closed
FROM employee e
JOIN sales_record s ON e.employee_id = s.employee_id
WHERE s.period = '2026-Q1' AND s.deal_stage = 'closed'
GROUP BY e.employee_id
ORDER BY total_revenue DESC;

-- Get complete evidence for case 8001 (Fire John Tan?)
SELECT ce.evidence_id, ce.source_table, ce.record_id, ce.relevance_score, ce.notes
FROM case_evidence ce
WHERE ce.case_id = 8001
ORDER BY ce.relevance_score DESC;

-- Get decision output with full reasoning
SELECT decision_id, recommendation, risk_level, confidence_score, 
       rationale, conservative_view, aggressive_view
FROM decision_output 
WHERE case_id = 8001;

-- Cross-table employee analysis (John Tan)
SELECT 
  'HR' as source, period, performance_score as value 
FROM hr_record WHERE employee_id = 1023
UNION ALL
SELECT 
  'Sales' as source, period, amount as value 
FROM sales_record WHERE employee_id = 1023 AND deal_stage = 'closed'
ORDER BY period;
```

## Integration with Frontend

The frontend (in `../frontend/src/lib/decision-engine.ts`) currently uses **mock data**.

To connect it to this real database:

1. Create a backend API (Node.js/Express, FastAPI, etc.)
2. Expose endpoints:
   - `POST /api/analyze` - Submit a query, trigger agent pipeline
   - `GET /api/cases/:id` - Get case details + evidence
   - `GET /api/employees/:id` - Get employee profile + records
3. Update `decision-engine.ts` to call your API instead of returning hardcoded results

## Next Steps (for Keith's Data Agent)

1. **Choose backend stack**: Node.js + Express, Python + FastAPI, or similar
2. **Create API layer**:
   - Database connection module
   - Evidence retrieval endpoints (SQL + vector search)
   - Agent orchestration endpoints
3. **Connect to frontend**: Replace mock `analyze()` function with real API calls
4. **OCR pipeline**: Integrate GLM-4V or similar for PDF → structured data
5. **Vector DB**: Add Chroma/FAISS for semantic search on unstructured text

## Troubleshooting

**Error: "table X already exists"**
- Drop the database and recreate: `rm decision_engine.db && sqlite3 decision_engine.db < schema.sql`

**No data returned from queries**
- Verify seed data loaded: `sqlite3 decision_engine.db "SELECT COUNT(*) FROM company;"`
- Should return: 3

**Foreign key constraint errors**
- SQLite requires `PRAGMA foreign_keys = ON;` to enforce constraints
- Add this to your connection setup in backend code

## Schema Changes

When modifying the schema:

1. Update `schema.sql`
2. Update `seed.sql` if needed
3. Drop and recreate database (during development)
4. For production: write migration scripts (ALTER TABLE statements)
