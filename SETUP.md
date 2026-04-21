# Setup Guide - AI Boss Decision Engine

Complete setup instructions for the monorepo.

## Prerequisites

- **Node.js** 18+ (for frontend)
- **Supabase Account** (for cloud database) - [https://supabase.com](https://supabase.com)
- **Git** (already installed based on your repo)

## Step-by-Step Setup

### 1. Database Setup (10 minutes)

#### Option A: Supabase Cloud (Recommended for collaboration)

```bash
# 1. Create Supabase project at https://supabase.com
# 2. Navigate to SQL Editor in Supabase Dashboard
# 3. Open schema.sql from backend/database/ folder
# 4. Copy entire contents and paste into SQL Editor
# 5. Click "Run" to create tables
# 6. Open seed.sql from backend/database/ folder
# 7. Copy entire contents and paste into SQL Editor
# 8. Click "Run" to load data

# 9. Verify in Supabase Table Editor or SQL Editor:
SELECT COUNT(*) FROM employee;
-- Expected: 43

SELECT COUNT(*) FROM decision_case;
-- Expected: 3

SELECT COUNT(*) FROM sales_record WHERE deal_stage = 'closed';
-- Expected: 38
```

#### Option B: Local PostgreSQL (Alternative)

```bash
# Install PostgreSQL if not already installed
# Windows: Download from https://www.postgresql.org/download/
# Or use: winget install PostgreSQL.PostgreSQL

# Create database
psql -U postgres -c "CREATE DATABASE decision_engine;"

# Load schema and seed
cd "c:\Users\user\Documents\UM ACADEMICS Y2S2\UMH\boss_decision\backend\database"
psql -U postgres -d decision_engine -f schema.sql
psql -U postgres -d decision_engine -f seed.sql

# Verify
psql -U postgres -d decision_engine -c "SELECT COUNT(*) FROM employee;"
```

### 2. Frontend Setup (5 minutes)

```bash
# Navigate to frontend folder
cd ..\..\frontend

# Install dependencies (using npm)
npm install

# Start development server
npm run dev
```

Visit `http://localhost:8080` in your browser.

### 3. Verify Everything Works

#### Frontend Check:
1. Open `http://localhost:8080`
2. You should see "AI Decision Engine" header
3. Enter a query like: "Should we fire employee 4?"
4. Watch the staged animation (Data → Agents → Subagents → Decision)

**Note**: Frontend currently uses **mock data**. The real database is ready but not yet connected.

#### Database Check (Supabase SQL Editor or psql):
```sql
-- Check employee John Tan (the underperformer in demo)
SELECT * FROM employee WHERE employee_id = 1023;

-- Check his performance records
SELECT * FROM hr_record WHERE employee_id = 1023 ORDER BY period;

-- Check decision case 8001 (fire employee scenario)
SELECT * FROM decision_output WHERE case_id = 8001;

-- Sales leaderboard Q1 2026
SELECT e.name, SUM(s.amount) as revenue 
FROM employee e 
JOIN sales_record s ON e.employee_id = s.employee_id 
WHERE s.period = '2026-Q1' AND s.deal_stage = 'closed' 
GROUP BY e.name 
ORDER BY revenue DESC;
```

## Folder Structure After Setup

```
boss_decision/
├── frontend/
│   ├── node_modules/       (created after npm install)
│   ├── src/
│   ├── package.json
│   └── ...
├── backend/
│   └── database/
│       ├── schema.sql      (PostgreSQL/Supabase schema)
│       ├── seed.sql        (seed data)
│       └── README.md       (database docs)
├── README.md
└── SETUP.md (this file)
```

## Common Issues

### Issue: Supabase SQL syntax error
**Solution**:
- Make sure you're using the latest `schema.sql` (PostgreSQL syntax, not SQLite)
- Run `schema.sql` BEFORE `seed.sql`
- If tables already exist, run `DROP TABLE` statements first (they're in schema.sql)

### Issue: Foreign key constraint violation
**Solution**:
```sql
-- Drop all tables and recreate (in Supabase SQL Editor)
-- Copy the DROP statements from schema.sql and run first
DROP TABLE IF EXISTS decision_output CASCADE;
DROP TABLE IF EXISTS case_evidence CASCADE;
-- ... (all DROP statements)

-- Then run full schema.sql again
```

### Issue: Frontend port 8080 already in use
**Solution**:
Edit `frontend/vite.config.ts`, change port to 3000 or another available port.

### Issue: npm install fails
**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

### Issue: Supabase connection in backend
**Solution**:
```bash
# Install Supabase client
cd backend
npm install @supabase/supabase-js

# Or for Python
pip install supabase
```

Create `.env` file in `backend/`:
```
SUPABASE_URL=your_project_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

## Next Steps

### For Keith (Data Agent + Backend)
1. Choose backend framework (Express/FastAPI)
2. Create API endpoints:
   - `POST /api/analyze` (submit query)
   - `GET /api/cases/:id` (get case details)
3. Connect to SQLite database
4. Update frontend to call real API

**Example Node.js setup**:
```bash
cd backend
npm init -y
npm install express sqlite3 cors
# Create index.js, routes/, controllers/
```

### For Kai Haung (OCR Pipeline)
1. Set up GLM-4V API integration
2. Create PDF/image upload endpoint
3. Implement: File → OCR → LLM → Structured data extraction
4. Insert into `source_document` + domain tables

### For Marcus (Manager Personas)
1. Review `src/lib/decision-engine.ts`
2. Implement conservative vs aggressive reasoning strategies
3. Add persona selection UI (optional)

### For Yihao (HR + Legal Agents)
1. Create agent modules in `backend/agents/`
2. Implement evidence retrieval queries
3. Format output as structured insights

### For Jialih (Sales + Marketing + Supply Chain Agents)
1. Similar to Yihao's task
2. Focus on domain-specific metrics
3. Coordinate with Keith on API structure

## Testing the System End-to-End (Future)

Once backend is connected:

```bash
# Terminal 1: Start backend
cd backend
npm start  # or python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Test API directly
curl -X POST http://localhost:3000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Should we fire employee 4?"}'
```

## Development Workflow

1. **Make changes** in `frontend/` or `backend/`
2. **Test locally**: Frontend auto-reloads on save (Vite HMR)
3. **Commit changes**: `git add . && git commit -m "description"`
4. **Push to GitHub**: `git push origin main`
5. **Coordinate**: Use issues/PRs for task tracking

## Questions?

- **Architecture**: See `questionstoconsider.md`
- **Database**: See `backend/database/README.md`
- **Frontend components**: See `frontend/src/components/`
- **Git workflow**: Standard feature branches + PRs

---

**Ready to build!** 🚀
