# Understanding the Database Structure & Seed Data

A comprehensive guide to how the AI Boss Decision Engine database is structured and how all the data connects together.

---

## Table of Contents

1. [What is Seed Data?](#what-is-seed-data)
2. [ID Structure & Ranges](#id-structure--ranges)
3. [Department Structure](#department-structure)
4. [Employee Records (The Core Entity)](#employee-records-the-core-entity)
5. [How Records Link Together](#how-records-link-together)
6. [Cross-Table Relationships](#cross-table-relationships)
7. [Decision Case Flow Example](#decision-case-flow-example)
8. [Data Volumes Summary](#data-volumes-summary)
9. [Powerful Query Examples](#powerful-query-examples)
10. [Common Questions](#common-questions)

---

## What is Seed Data?

**Seed data** = Pre-loaded realistic sample data for testing and demo purposes.

Think of it like this:
- **Empty database** = Empty restaurant (tables exist, but no customers)
- **Seeded database** = Restaurant with customers eating, ordering, paying (you can demo the system)

### What We Created

- **43 employees** across 7 departments
- **300+ records** of their work (performance reviews, sales deals, expenses, etc.)
- **3 complete decision cases** with full evidence chains

### Why We Need This

1. **Testing**: Developers can test features without manual data entry
2. **Demo**: Showcase the system with realistic scenarios
3. **Development**: Build agents with real data to query against
4. **Training**: Team members can understand the system structure

---

## ID Structure & Ranges

We use **realistic ID ranges** instead of starting from 1, 2, 3... to simulate a real company database.

| Table | ID Range | Count | Purpose |
|-------|----------|-------|---------|
| **department** | 101-107 | 7 | Agent-aligned departments |
| **employee** | 1001-1050 | 43 | Core entity (people) |
| **source_document** | 501-525 | 25 | Original documents (OCR tracking) |
| **hr_record** | 2001-2040 | 40 | Performance reviews |
| **sales_record** | 3001-3043 | 43 | Deals & revenue |
| **finance_record** | 4001-4034 | 34 | Salaries & budgets |
| **marketing_record** | 5001-5032 | 32 | Campaign metrics |
| **supply_record** | 6001-6030 | 30 | Inventory & procurement |
| **legal_record** | 7001-7012 | 12 | Company policies |
| **decision_case** | 8001-8003 | 3 | User queries |
| **case_evidence** | 9001-9025 | 25 | Evidence links |
| **decision_output** | 10001-10003 | 3 | Final verdicts |

### Why Not Start from 1?

Real companies don't have employee #1, #2, #3. They might have:
- Employee #1001 (first hire in 2020)
- Employee #1023 (23rd hire in 2023)
- Employee #1050 (50th hire in 2024)

This makes the demo look more realistic and professional.

---

## Department Structure

We have **7 departments**, each aligned with a **specialist agent**.

```sql
INSERT INTO department (dept_id, name, description) VALUES
(101, 'Engineering', 'Software development and DevOps'),
(102, 'Sales', 'Enterprise and SMB sales team'),
(103, 'Marketing', 'Digital marketing and brand'),
(104, 'HR', 'Human resources and talent'),
(105, 'Finance', 'Financial planning and accounting'),
(106, 'Legal', 'Legal compliance and contracts'),
(107, 'Supply Chain', 'Procurement and vendor management');
```

### Why These 7?

Each department = **One specialist agent**:
- **HR Agent** (Yihao) → reads from dept 104
- **Sales Agent** (Jialih) → reads from dept 102
- **Marketing Agent** (Jialih) → reads from dept 103
- **Supply Chain Agent** (Jialih) → reads from dept 107
- **Legal Agent** (Yihao) → reads from dept 106
- **Finance Agent** (Keith) → reads from dept 105
- **Engineering** → supporting dept (provides context)

---

## Employee Records (The Core Entity)

Employees are the **central linking point** for all other data.

### Employee Structure

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `employee_id` | BIGINT | 1023 | Unique ID (primary key) |
| `dept_id` | BIGINT | 102 | Links to department |
| `name` | TEXT | 'John Tan' | Full name |
| `role` | TEXT | 'Sales Executive' | Job title |
| `email` | TEXT | 'john.tan@...' | Contact email |
| `hire_date` | DATE | '2023-08-20' | When they joined |
| `salary` | NUMERIC | 10500.00 | Monthly salary (MYR) |
| `exit_date` | DATE | NULL | If they left (NULL = active) |

### Example: John Tan (The Underperformer)

```sql
INSERT INTO employee VALUES
(1023, 102, 'John Tan', 'Sales Executive', 
 'john.tan@techventure.my', '2023-08-20', 10500.00, NULL);
```

**Decoded:**
- `employee_id: 1023` ← Unique ID for John
- `dept_id: 102` ← He's in Sales department
- `name: 'John Tan'` ← His name
- `role: 'Sales Executive'` ← His job title
- `hire_date: '2023-08-20'` ← Hired Aug 20, 2023 (only 6 months ago)
- `salary: 10500.00` ← Monthly salary RM 10,500
- `exit_date: NULL` ← Still active (not terminated)

### Key Employees by Department

#### Sales Team (dept 102) - 10 employees
- **Sarah Lim (1020)** - Sales Director (boss) - RM 18,000/month
- **John Tan (1023)** - Sales Executive (underperformer) - RM 10,500/month ⚠️
- **David Wong (1021)** - Enterprise Sales (top performer) - RM 11,500/month
- **Muthu Kumar (1024)** - Account Manager - RM 13,800/month
- **Nurul Aisyah (1025)** - Sales Manager - RM 15,000/month

#### Engineering Team (dept 101) - 12 employees
- **Rajesh Menon (1008)** - Engineering Manager - RM 16,500/month
- **Priya Kumar (1003)** - DevOps Lead (star performer) - RM 14,200/month
- **Ahmad Hassan (1001)** - Senior Backend Engineer - RM 12,500/month

#### HR Team (dept 104) - 4 employees
- **Fatimah Zahra (1037)** - HR Director - RM 15,500/month
- **Ahmad Razak (1038)** - HR Manager - RM 12,000/month

---

## How Records Link Together

### The Linking Pattern

Every domain-specific record (HR, Sales, Finance, etc.) **links back to employees** via `employee_id`.

```
                    ┌──────────────┐
                    │   EMPLOYEE   │
                    │  (employee_id)│
                    └───────┬──────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
      ┌─────▼─────┐   ┌────▼────┐   ┌─────▼─────┐
      │ HR_RECORD │   │  SALES  │   │  FINANCE  │
      │           │   │ _RECORD │   │  _RECORD  │
      └───────────┘   └─────────┘   └───────────┘
```

### Example 1: HR Record (Performance Review)

```sql
INSERT INTO hr_record VALUES
(2001, 1023, '2025-Q3', 62, 3, 2.8, 
 'Performance below expectations. Missed Q3 sales target by 45%.',
 0, NULL, '2025-09-25', 1025, 513);
```

**Field Breakdown:**

| Field | Value | Meaning |
|-------|-------|---------|
| `hr_id` | 2001 | Unique ID for this review |
| `employee_id` | **1023** | **⬅️ Links to John Tan** |
| `period` | '2025-Q3' | Q3 2025 review |
| `attendance_days` | 62 | Present 62 days (out of 65 working days) |
| `absence_days` | 3 | Absent 3 days |
| `performance_score` | **2.8** | **Score 2.8/5.0** (below expectations) |
| `performance_summary` | 'Performance below...' | Manager's written notes |
| `warning_count` | 0 | No formal warnings yet |
| `pip_status` | NULL | PIP (Performance Improvement Plan) not started |
| `review_date` | '2025-09-25' | Date review was conducted |
| `reviewer_id` | **1025** | **⬅️ Links to Nurul Aisyah (his manager)** |
| `source_id` | **513** | **⬅️ Links to source document (HR Report Q3)** |

**The Magic of Linking:**
1. `employee_id: 1023` → "This review is **ABOUT** John Tan"
2. `reviewer_id: 1025` → "This review was **DONE BY** Nurul Aisyah"
3. `source_id: 513` → "This data **CAME FROM** document #513 (HR Report Q3 2025)"

### Example 2: Sales Record (Revenue Contribution)

```sql
INSERT INTO sales_record VALUES
(3001, 1023, 102, '2025-Q3', 'Tech Solutions Renewal', 
 'SaaS Platform Enterprise', 18500.00, 'closed', 
 'Tech Solutions Sdn Bhd', 'Kuala Lumpur', '2025-09-15', 514);
```

**Field Breakdown:**

| Field | Value | Meaning |
|-------|-------|---------|
| `sales_id` | 3001 | Unique deal ID |
| `employee_id` | **1023** | **⬅️ Links to John Tan** |
| `dept_id` | 102 | Sales department |
| `period` | '2025-Q3' | Q3 2025 |
| `deal_name` | 'Tech Solutions Renewal' | Deal name |
| `product` | 'SaaS Platform Enterprise' | Product sold |
| `amount` | **18500.00** | **RM 18,500 revenue** |
| `deal_stage` | 'closed' | Deal won (vs 'pipeline' or 'lost') |
| `customer_name` | 'Tech Solutions Sdn Bhd' | Customer company |
| `region` | 'Kuala Lumpur' | Sales region |
| `close_date` | '2025-09-15' | Date deal closed |
| `source_id` | **514** | **⬅️ Links to CRM Export Q3 2025** |

**Why This Matters:**
- John only brought in **RM 18,500** in Q3 2025
- Compare to Sarah Lim (his boss): **RM 195,000** in Q3 2025
- John is in **bottom 10%** of sales team

### Example 3: Finance Record (Salary)

```sql
INSERT INTO finance_record VALUES
(4001, 102, 1023, '2026-Q1', 'salary', 31500.00, 'MYR', 'personnel', NULL, 506);
```

**Field Breakdown:**

| Field | Value | Meaning |
|-------|-------|---------|
| `finance_id` | 4001 | Unique finance record ID |
| `dept_id` | 102 | Sales department |
| `employee_id` | **1023** | **⬅️ Links to John Tan** |
| `period` | '2026-Q1' | Q1 2026 (3 months) |
| `metric_name` | 'salary' | Type of expense |
| `amount` | **31500.00** | **RM 31,500 (3 months × RM 10,500)** |
| `unit` | 'MYR' | Currency |
| `category` | 'personnel' | Budget category |
| `source_id` | 506 | Links to budget document |

---

## Cross-Table Relationships

### The Power of Foreign Keys

Multiple tables reference the **SAME employee**, allowing us to build a complete profile:

```
employee (1023: John Tan)
    │
    ├─→ hr_record (2001, 2002, 2003)
    │   ├─ Q3 2025: Score 2.8/5, no warnings
    │   ├─ Q4 2025: Score 2.1/5, 1 warning
    │   └─ Q1 2026: Score 2.0/5, 2 warnings, PIP recommended
    │
    ├─→ sales_record (3001, 3002, 3003, 3004, 3005)
    │   ├─ Q3 2025: RM 18,500 (closed)
    │   ├─ Q4 2025: RM 8,500 (closed)
    │   ├─ Q1 2026: RM 12,400 (closed)
    │   ├─ Q1 2026: RM 0 (lost deal)
    │   └─ Q1 2026: Pipeline (active)
    │
    ├─→ finance_record (4001)
    │   └─ Q1 2026 salary: RM 31,500
    │
    └─→ case_evidence (9001-9015)
        └─ Used in Case 8001: "Should we fire John Tan?"
```

### Query Example: Get Complete Employee Profile

```sql
-- Basic info
SELECT * FROM employee WHERE employee_id = 1023;

-- Performance history
SELECT * FROM hr_record WHERE employee_id = 1023 ORDER BY period;

-- Sales history
SELECT * FROM sales_record WHERE employee_id = 1023 ORDER BY period;

-- Salary records
SELECT * FROM finance_record WHERE employee_id = 1023;
```

**Result:** Complete 360° view of John Tan's:
- Personal info (name, role, salary, hire date)
- Performance trend (declining from 2.8 → 2.1 → 2.0)
- Sales trend (declining from RM 18.5k → RM 8.5k → RM 12.4k)
- Cost to company (RM 31,500 per quarter)

---

## Decision Case Flow Example

Let's walk through **Case 8001: Should we fire John Tan?** from start to finish.

### Step 1: The Question (decision_case table)

```sql
INSERT INTO decision_case VALUES
(8001, 
 'Should we terminate employee John Tan (ID 1023)?',
 'Sales executive with declining performance over 2 quarters. HR flagged for review.',
 'employee', 1023, 'completed', 'Sarah Lim (Sales Director)', '2026-04-15 10:30:00');
```

**Decoded:**
- `case_id: 8001` ← Unique case ID
- `question: 'Should we terminate...'` ← The decision query
- `context: 'Sales executive with declining...'` ← Additional context
- `target_type: 'employee'` ← Decision is about an employee (not a product/market)
- `target_id: 1023` ← **Specific employee: John Tan**
- `status: 'completed'` ← Decision has been made
- `submitted_by: 'Sarah Lim'` ← Who asked the question
- `created_at: '2026-04-15 10:30:00'` ← When it was submitted

---

### Step 2: Evidence Collection (case_evidence table)

The system retrieved **15 pieces of evidence** across multiple tables:

```sql
-- HR Evidence (Performance Reviews)
INSERT INTO case_evidence VALUES
(9001, 8001, 'hr_record', 2001, 0.92, 'sql_query', 'Q3 2025 underperformance review, score 2.8/5'),
(9002, 8001, 'hr_record', 2002, 0.98, 'sql_query', 'Q4 2025 declining performance, warning issued, score 2.1/5'),
(9003, 8001, 'hr_record', 2003, 0.99, 'sql_query', 'Q1 2026 continued underperformance, score 2.0/5, PIP recommended');

-- Sales Evidence (Revenue Data)
INSERT INTO case_evidence VALUES
(9004, 8001, 'sales_record', 3001, 0.88, 'sql_query', 'Q3 2025 sales: RM 18,500 (below team average)'),
(9005, 8001, 'sales_record', 3002, 0.90, 'sql_query', 'Q4 2025 sales: RM 8,500 (bottom 10% of team)'),
(9006, 8001, 'sales_record', 3003, 0.93, 'sql_query', 'Q1 2026 sales: RM 12,400 (bottom 8% of team)'),
(9007, 8001, 'sales_record', 3004, 0.85, 'sql_query', 'Q1 2026 lost enterprise deal');

-- Legal Evidence (Policies)
INSERT INTO case_evidence VALUES
(9008, 8001, 'legal_record', 7001, 0.95, 'vector_search', 'Performance termination policy: PIP required'),
(9009, 8001, 'legal_record', 7002, 0.92, 'vector_search', 'Severance calculation: min RM 20k for 2.5 years service'),
(9010, 8001, 'legal_record', 7005, 0.90, 'vector_search', 'PIP guidelines: 60-day minimum duration');

-- Finance Evidence (Costs)
INSERT INTO case_evidence VALUES
(9011, 8001, 'finance_record', 4001, 0.80, 'sql_query', 'Current salary cost: RM 10,500/month'),
(9012, 8001, 'finance_record', 4022, 0.78, 'sql_query', 'Severance reserve available: RM 150k'),
(9013, 8001, 'finance_record', 4023, 0.85, 'sql_query', 'Replacement cost estimate: RM 45k'),
(9014, 8001, 'finance_record', 4024, 0.82, 'sql_query', 'Onboarding cost estimate: RM 12k');

-- Comparison Evidence
INSERT INTO case_evidence VALUES
(9015, 8001, 'sales_record', 3006, 0.70, 'sql_query', 'Comparison: Sarah Lim Q1 revenue RM 900k (top performer)');
```

**Breaking Down One Evidence Link:**

| Field | Value | Meaning |
|-------|-------|---------|
| `evidence_id` | 9001 | Unique evidence link ID |
| `case_id` | **8001** | **⬅️ For Case 8001 (Should we fire John?)** |
| `source_table` | 'hr_record' | Evidence is from HR table |
| `record_id` | **2001** | **⬅️ Specific HR record #2001** |
| `relevance_score` | 0.92 | 92% relevant (0.0-1.0 scale) |
| `retrieval_method` | 'sql_query' | Found via SQL (not semantic search) |
| `notes` | 'Q3 2025 underperformance...' | Why it's relevant |

**The Evidence Chain:**

```
case_evidence (9001)
    ↓
    case_id: 8001 → "For Case 8001 (Fire John Tan?)"
    source_table: 'hr_record' → "Evidence is from HR records"
    record_id: 2001 → "Specifically HR record #2001"
        ↓
    hr_record (2001)
        ↓
        employee_id: 1023 → "About John Tan"
        period: '2025-Q3' → "Q3 2025 review"
        performance_score: 2.8 → "Scored 2.8/5"
        performance_summary: "Performance below expectations..."
        source_id: 513 → "From HR Report Q3 2025"
```

---

### Step 3: Agent Analysis (not in database, happens in backend)

The multi-agent system processes the evidence:

1. **HR Agent** (Yihao):
   - Retrieves: hr_record 2001, 2002, 2003
   - Analyzes: Performance declining (2.8 → 2.1 → 2.0)
   - Finds: 2 warnings issued, PIP not started
   - Risk: Legal requires PIP before termination
   - Recommendation: "Initiate 60-day PIP first"

2. **Sales Agent** (Jialih):
   - Retrieves: sales_record 3001, 3002, 3003, 3004
   - Analyzes: Revenue RM 39,400 total across 3 quarters
   - Compares: Bottom 8% of sales team
   - Risk: Pipeline thin (1 active deal only)
   - Recommendation: "Performance below standards"

3. **Legal Agent** (Yihao):
   - Retrieves: legal_record 7001, 7002, 7005
   - Analyzes: Termination policy requires PIP completion
   - Calculates: Severance RM 20,000 minimum
   - Risk: Wrongful termination claim if PIP skipped
   - Recommendation: "PIP mandatory per policy"

4. **Finance Agent** (Keith):
   - Retrieves: finance_record 4001, 4022, 4023, 4024
   - Calculates:
     - Current cost: RM 10,500/month
     - Severance: RM 20,000
     - Replacement: RM 45,000
     - Onboarding: RM 12,000
     - **Total: RM 77,000**
   - Analyzes: Break-even after 7.3 months
   - Recommendation: "Replacement cost high"

5. **Manager Agent** (Marcus):
   - Synthesizes all 4 agent outputs
   - Applies conservative persona
   - Generates two perspectives:
     - **Conservative**: "Do NOT terminate - PIP first"
     - **Aggressive**: "Terminate - underperformance documented"
   - Final decision: Conservative (prioritize legal compliance)

---

### Step 4: Final Decision (decision_output table)

```sql
INSERT INTO decision_output VALUES
(10001, 8001,
 'DO NOT TERMINATE — Initiate mandatory 60-day PIP with measurable exit criteria',
 'Medium', 78,
 '**HR Agent Analysis:** Employee 1023 (John Tan) shows sustained underperformance across two consecutive quarters (Q4 2025: score 2.1/5, Q1 2026: score 2.0/5). Two warnings issued. However, Performance Improvement Plan (PIP) has NOT been initiated, which is mandatory per company policy.

**Sales Agent Analysis:** Revenue contribution critically low: Q3 2025 (RM 18.5k), Q4 2025 (RM 8.5k), Q1 2026 (RM 12.4k). This places employee in bottom 8% of sales team. Comparison: top performer Sarah Lim generated RM 900k in Q1 2026. Lost 1 enterprise deal, pipeline thin.

**Legal Agent Analysis:** Termination for performance is permitted ONLY after: (1) Two consecutive underperformance reviews (SATISFIED), (2) Completion of 60-day PIP (NOT SATISFIED). Company policy mandates PIP before termination. Severance cost: minimum RM 20,000 for 2.5 years of service. Risk: wrongful termination claim if PIP skipped.

**Finance Agent Analysis:** Current cost: RM 10,500/month salary. Termination cost breakdown: Severance RM 20k + Replacement RM 45k + Onboarding RM 12k = Total RM 77k one-time cost. Break-even: 7.3 months.

**Manager Decision (Conservative Stance):** Short-term termination cost (RM 77k total) + 3-month productivity gap during replacement ramp outweighs immediate savings. Legal risk of wrongful termination without PIP completion is significant. Recommendation: Initiate mandatory 60-day PIP immediately with clear metrics.',
 
 'Do NOT terminate - initiate PIP first. Legal risk too high without PIP completion. Replacement cost (RM 77k) + ramp time (3 months) outweighs short-term savings.',
 
 'Terminate immediately - sustained underperformance hurts team morale and revenue. Bottom 8% performer for 2 quarters is clear cause. Severance cost (RM 20k) is acceptable.',
 
 'conservative');
```

**Field Breakdown:**

| Field | Value | Meaning |
|-------|-------|---------|
| `decision_id` | 10001 | Unique decision ID |
| `case_id` | **8001** | **⬅️ For case 8001** |
| `recommendation` | 'DO NOT TERMINATE...' | **Final verdict** |
| `risk_level` | 'Medium' | Risk assessment |
| `confidence_score` | 78 | 78% confidence (0-100 scale) |
| `rationale` | 'HR Agent... Sales Agent...' | **Full multi-agent reasoning** |
| `conservative_view` | 'Do NOT terminate...' | Conservative perspective |
| `aggressive_view` | 'Terminate immediately...' | Aggressive perspective |
| `manager_persona` | 'conservative' | Which stance was chosen |

---

## Data Volumes Summary

| Table | Records | Purpose | Key IDs |
|-------|---------|---------|---------|
| `department` | 7 | Agent-aligned departments | 101-107 |
| `employee` | 43 | Core entity (people) | 1001-1050 |
| `source_document` | 25 | OCR tracking & explainability | 501-525 |
| `hr_record` | 40 | Performance reviews | 2001-2040 |
| `sales_record` | 43 | Deals & revenue | 3001-3043 |
| `finance_record` | 34 | Salaries & budgets | 4001-4034 |
| `marketing_record` | 32 | Campaign metrics | 5001-5032 |
| `supply_record` | 30 | Inventory & procurement | 6001-6030 |
| `legal_record` | 12 | Company policies | 7001-7012 |
| `decision_case` | 3 | User queries | 8001-8003 |
| `case_evidence` | 25 | Evidence links | 9001-9025 |
| `decision_output` | 3 | Final verdicts | 10001-10003 |

**Total: ~300 records, all properly linked via foreign keys**

---

## Powerful Query Examples

### Query 1: Get Complete Employee Profile

```sql
-- Get employee with department
SELECT e.*, d.name as department_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.employee_id = 1023;

-- Get performance history
SELECT period, performance_score, performance_summary, warning_count
FROM hr_record
WHERE employee_id = 1023
ORDER BY period;

-- Get sales history
SELECT period, deal_name, amount, deal_stage
FROM sales_record
WHERE employee_id = 1023
ORDER BY period;
```

**Result:** Complete 360° profile of John Tan

---

### Query 2: Sales Leaderboard (Q1 2026)

```sql
SELECT 
  e.name,
  e.role,
  COUNT(s.sales_id) as deals_closed,
  SUM(s.amount) as total_revenue
FROM employee e
JOIN sales_record s ON e.employee_id = s.employee_id
WHERE s.period = '2026-Q1' AND s.deal_stage = 'closed'
GROUP BY e.employee_id, e.name, e.role
ORDER BY total_revenue DESC;
```

**Result:**
```
Sarah Lim     | Sales Director              | 3 deals | RM 900,000
Muthu Kumar   | Enterprise Account Manager  | 3 deals | RM 355,000
David Wong    | Enterprise Sales Executive  | 2 deals | RM 220,000
...
John Tan      | Sales Executive             | 1 deal  | RM 12,400  ← Bottom
```

---

### Query 3: Get All Evidence for a Decision Case

```sql
SELECT 
  ce.evidence_id,
  ce.source_table,
  ce.record_id,
  ce.relevance_score,
  ce.notes,
  CASE ce.source_table
    WHEN 'hr_record' THEN (
      SELECT performance_summary 
      FROM hr_record 
      WHERE hr_id = ce.record_id
    )
    WHEN 'sales_record' THEN (
      SELECT CONCAT(deal_name, ': RM ', amount) 
      FROM sales_record 
      WHERE sales_id = ce.record_id
    )
    WHEN 'legal_record' THEN (
      SELECT policy_name 
      FROM legal_record 
      WHERE legal_id = ce.record_id
    )
  END as evidence_summary
FROM case_evidence ce
WHERE ce.case_id = 8001
ORDER BY ce.relevance_score DESC;
```

**Result:** All 15 evidence pieces with details, sorted by relevance

---

### Query 4: Compare Employee Performance

```sql
-- Performance trend comparison
SELECT 
  e.name,
  h.period,
  h.performance_score,
  h.warning_count
FROM employee e
JOIN hr_record h ON e.employee_id = h.employee_id
WHERE e.dept_id = 102  -- Sales department
ORDER BY e.name, h.period;
```

**Result:** Side-by-side performance comparison of all sales team members

---

### Query 5: Department Cost Analysis

```sql
SELECT 
  d.name as department,
  COUNT(e.employee_id) as headcount,
  SUM(e.salary) as monthly_cost,
  SUM(e.salary) * 12 as annual_cost
FROM department d
JOIN employee e ON d.dept_id = e.dept_id
WHERE e.exit_date IS NULL  -- Active employees only
GROUP BY d.dept_id, d.name
ORDER BY annual_cost DESC;
```

**Result:**
```
Engineering   | 12 employees | RM 138,500/month | RM 1,662,000/year
Sales         | 10 employees | RM 121,200/month | RM 1,454,400/year
Marketing     | 7 employees  | RM 63,700/month  | RM 764,400/year
...
```

---

## Common Questions

### Q: Why so many sales records for John Tan if he's underperforming?

**A:** To show the **performance trend** over time:
- Q3 2025: RM 18,500 (okay-ish start)
- Q4 2025: RM 8,500 (declining sharply)
- Q1 2026: RM 12,400 (slight recovery but still bottom 8%)

The trend is more important than a single data point. This demonstrates **sustained** underperformance.

---

### Q: What does `relevance_score` mean in case_evidence?

**A:** It's a **0.0 to 1.0 score** indicating how relevant a piece of evidence is to the decision:
- `0.99` = Extremely relevant (core evidence)
- `0.80` = Relevant (supporting evidence)
- `0.50` = Somewhat relevant (contextual)

In the future, **vector search** will automatically calculate these scores based on semantic similarity to the query.

---

### Q: What's the purpose of `source_id`?

**A:** **Explainability & audit trail**. It tracks which **original document** the data came from:
- `source_id: 513` = HR Report Q3 2025
- `source_id: 514` = CRM Export Q3 2025
- `source_id: 507` = Employee Termination Policy v3.1

This allows you to trace back: "Where did this data come from?"

---

### Q: Can I add more employees?

**A:** Yes! Just use the next available ID in the range:

```sql
INSERT INTO employee VALUES
(1051, 102, 'New Employee', 'Sales Executive', 
 'new.employee@techventure.my', '2026-05-01', 11000.00, NULL);
```

Then add related records (HR, sales, etc.) that link to `employee_id: 1051`.

---

### Q: Why are some `employee_id` values NULL in sales_record?

**A:** Some deals are **team deals** not attributed to a single person:

```sql
-- Team deal (no individual attribution)
INSERT INTO sales_record VALUES
(3030, NULL, 102, '2025-Q4', 'Channel Partner Deal', 
 'SaaS Platform Enterprise', 250000.00, 'closed', 
 'Channel Partner Network', 'Multiple', '2025-12-30', 503);
```

This is realistic - not every sale is credited to one person.

---

### Q: How do I query across multiple tables?

**A:** Use **JOINs** to connect related data:

```sql
-- Get employee with all their HR and sales records
SELECT 
  e.name,
  e.role,
  h.period as review_period,
  h.performance_score,
  s.period as sales_period,
  s.amount as sales_revenue
FROM employee e
LEFT JOIN hr_record h ON e.employee_id = h.employee_id
LEFT JOIN sales_record s ON e.employee_id = s.employee_id
WHERE e.employee_id = 1023
ORDER BY h.period, s.period;
```

---

### Q: What if I want to add a new decision case?

**A:** Follow this pattern:

```sql
-- 1. Create the case
INSERT INTO decision_case VALUES
(8004, 'Should we expand to Thailand market?', 
 'Received 5 inbound leads from Thailand in Q1.', 
 'market_expansion', NULL, 'processing', 'James Lim (CFO)', NOW());

-- 2. Link evidence (as agents find relevant data)
INSERT INTO case_evidence VALUES
(9026, 8004, 'marketing_record', 5001, 0.85, 'sql_query', 
 'Q1 2026 international interest signals');

-- 3. Save final decision
INSERT INTO decision_output VALUES
(10004, 8004, 'EXPAND - Start with remote sales pod', 
 'Low', 82, 'Multi-agent analysis...', 
 'Conservative view...', 'Aggressive view...', 'balanced');
```

---

## Visual Relationship Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         DECISION CASE                           │
│                        (User's Question)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   Links to multiple...
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ CASE_EVIDENCE │   │ CASE_EVIDENCE │   │ CASE_EVIDENCE │
│ (HR Record)   │   │ (Sales Record)│   │ (Legal Policy)│
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │  Links to...      │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   HR_RECORD   │   │ SALES_RECORD  │   │ LEGAL_RECORD  │
│  (Review 2001)│   │  (Deal 3001)  │   │ (Policy 7001) │
└───────┬───────┘   └───────┬───────┘   └───────────────┘
        │                   │
        │  About...         │
        └──────────┬────────┘
                   │
                   ▼
           ┌───────────────┐
           │   EMPLOYEE    │
           │ (John Tan)    │
           │ employee_id:  │
           │     1023      │
           └───────────────┘
```

---

## Next Steps

1. **Load the data**: Run `schema.sql` then `seed.sql` in Supabase
2. **Explore with queries**: Try the sample queries above
3. **Build agents**: Use the database service methods in `db.py`
4. **Test decisions**: Create new decision cases and link evidence

---

## Need Help?

- **Database questions**: Check `database/README.md`
- **Backend setup**: Check `backend/README.md` or `backend/SETUP_COMPLETE.md`
- **Main project**: Check root `README.md`

**Happy querying! 🚀**
