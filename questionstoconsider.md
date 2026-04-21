🧠 OVERALL VIEW (Before Splitting)

Think of your system as 7 stages:

1. Data Acquisition
2. Data Normalization (OCR → Markdown)
3. Data Structuring & Linking
4. Knowledge Storage & Retrieval
5. Multi-Agent Reasoning
6. Manager Decision Engine
7. User Interaction & Output Layer

Each stage has:

a goal
a technical problem
a design decision you must make
🧩 STAGE 1: DATA ACQUISITION (Raw Input Layer)
🎯 Goal

Simulate real-world messy company data.

🔥 Problems to solve
Where does data come from?
How to simulate multi-format + inconsistent data?
How to ensure it’s rich enough for decision-making?
💡 Decisions
Synthetic vs real vs hybrid (you already leaning hybrid — good)
Types:
HR records
Sales transactions
Inventory logs
Feedback forms
Legal documents
⚠️ Critical Risk

If your data is too simple →
👉 your system looks like a toy

🧩 STAGE 2: DATA NORMALIZATION (OCR → Markdown)
🎯 Goal

Convert everything into a uniform machine-readable format

🔥 Problems
OCR errors (numbers, tables, layout)
Extracting structure from messy text
Converting different formats → same schema
💡 Decisions

Pipeline:

PDF/Image → OCR → LLM → Structured Markdown
Use GLM to:
fix OCR noise
enforce schema
⚠️ Critical Risk

If this fails:
👉 EVERYTHING downstream fails

🧩 STAGE 3: DATA STRUCTURING & LINKING (Your hardest problem)

This is the part you’re struggling with 👇

“how to relate HR + sales + legal + transactions”

🎯 Goal

Turn isolated documents into interconnected knowledge

🔥 Problems
No shared keys across datasets
Same entity appears differently:
“John Tan”
“J. Tan”
“Employee ID: 1023”
Cross-table reasoning:
HR ↔ Sales ↔ Legal
💡 Decisions (VERY IMPORTANT)
You MUST introduce:
👉 Entity Linking Layer

Example:

Employee:
  id: 1023
  name: John Tan
  department: Sales

Then:

HR file → links by employee_id
Sales data → links by employee_id
Legal → links by employee_id
🔧 Implementation Options
Option A (Simple but effective)
Use consistent synthetic IDs
Store in JSON / SQLite
Option B (Advanced, high score)

Use LLM to resolve entity:

“Is John Tan in HR same as J. Tan in sales?”

⚠️ Critical Insight

Without this stage:
👉 Your “multi-agent system” is fake
👉 It becomes just independent summaries

🧩 STAGE 4: KNOWLEDGE STORAGE & RETRIEVAL
🎯 Goal

Allow agents to fetch correct + relevant data

🔥 Problems
How to retrieve relevant info?
How to combine:
structured queries (SQL)
semantic queries (vector search)
💡 Decisions
You NEED dual system:
1. Structured DB (SQLite)
exact queries
relationships
2. Vector DB (FAISS/Chroma)
semantic search
unstructured data
🧠 Retrieval Flow

Example query:

“Should we fire employee 1023?”

System does:

SQL:
HR record
salary
SQL:
sales performance
Vector:
feedback / complaints
Legal rules
⚠️ Critical Risk

If retrieval is wrong:
👉 decision = garbage

🧩 STAGE 5: MULTI-AGENT REASONING
🎯 Goal

Each agent gives domain-specific insight

🔥 Problems
Agents hallucinate
Agents don’t coordinate
Overlapping responsibilities
💡 Decisions
Define CLEAR boundaries:
Sales Agent → revenue + trends
HR Agent → performance + cost
Legal Agent → constraints
🔧 Output format (force structure)
Agent: HR

Findings:
- Employee performance declining

Risk:
- Termination cost: RM 20,000

Recommendation:
- Consider warning before firing
⚠️ Critical Risk

If outputs are inconsistent:
👉 Manager cannot combine them

🧩 STAGE 6: MANAGER DECISION ENGINE (Your CORE)
🎯 Goal

Synthesize all agent outputs into ONE decision

🔥 Problems
Conflicting recommendations
No prioritization
No justification
💡 Decisions
You MUST implement:
1. Aggregation Logic
Compare agent outputs
2. Priority Weights

Example:

Legal > HR > Sales
3. Decision Template
Decision: Fire Employee 1023

Reasoning:
- Sales: revenue ↓ 40%
- HR: repeated underperformance
- Legal: termination allowed

Cost-Benefit:
- Save RM 5,000/month
- Compensation RM 20,000

Final Verdict:
- Proceed with termination
⚠️ This is where you win or lose the hackathon
🧩 STAGE 7: USER INTERACTION & OUTPUT (Your confusion point)

You asked:

Chat? Dashboard? File modification?

Here’s the correct answer:

🎯 Goal

Make user feel:
👉 “This system thinks, not just displays”

💡 Best Design (Hybrid)
1. Chat Interface (PRIMARY)

User asks:

“Should we fire employee 1023?”

System:

triggers pipeline
shows reasoning
2. Structured Output Panel (IMPORTANT)

Not just chat text:

Show:

Decision
Reasoning
Data sources used
Impact
3. OPTIONAL Dashboard (supporting, not main)
KPI trends
summaries
❌ What NOT to do
Pure dashboard → looks like PowerBI
Pure chat → looks like ChatGPT clone
🔄 Does system modify data?

👉 For hackathon:
NO need real modification

Instead:

simulate actions
log decisions

Example:

Action Log:
- Fired Employee 1023 (simulated)
🧠 FINAL STRUCTURE (What You Present)
User Query
   ↓
Manager Agent
   ↓
Task Decomposition
   ↓
Multi-Agent Retrieval + Reasoning
   ↓
Data (SQL + Vector DB)
   ↓
Aggregated Decision
   ↓
Explainable Output


Agent roadmap:
Data Agent
   ↓
HR Agent
Sales Agent
Marketing Agent
Supply Chain Agent
Legal Agent
   ↓
Subagents (Marcus)
   ↓
Manager Agent



Task distribution(phase1):

| Person | Task |
| --- | --- |
| Keith | Data Agent + database structure + data source + basic UI |
| Kai Haung | AI extraction & classification (OCR → structured data) |
| Marcus | Subagent personas (manager decision strategies) |
| Yihao | Human Resource Agent + Legal Agent |
| Jialih | Sales Agent + Marketing Agent + Supply Chain Agent |
