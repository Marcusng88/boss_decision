# 📊 AI Ingestion & Marketing Agent Module

## 📌 Overview

This module handles two core capabilities in the multi-agent system:

1. **AI Ingestion Pipeline**

   * Reads unstructured business files (PDF, Word)
   * Uses Gemini LLM to extract structured business data
   * Stores results in **Supabase (PostgreSQL)** for agent access

2. **Marketing Agent**

   * Analyzes cross-department data (HR, Sales, Campaigns)
   * Generates actionable marketing insights
   * Writes outputs back into the shared database

---

# 🧠 1. AI Ingestion Pipeline

## 🎯 Purpose

Transform raw business documents into structured, queryable knowledge stored in Supabase.

---

## 🔄 Workflow

```text
Upload File → Extract Content → Gemini LLM → Structured JSON → Supabase Storage → Agent Access
```

---

## ⚙️ Processing Steps

### Step 1: Direct LLM-Based File Reading

* Use Gemini LLM to directly process uploaded files (`.pdf`, `.docx`)
* Leverage Gemini’s native multimodal capabilities to interpret document structure, layout, and content
* Avoid manual text extraction where possible to preserve formatting and contextual information

---

### Step 2: LLM Extraction (Gemini)

The system prompts Gemini to extract:

```json
{
  "document_type": "",
  "department": "",
  "summary": "",
  "entities": [],
  "tags": [],
  "relationships": []
}
```

---

### Step 3: Database Storage (Supabase)

Structured data is stored across normalized tables:

#### Documents Table

```json
{
  "id": "doc_123",
  "department": "Marketing",
  "document_type": "campaign_report",
  "summary": "...",
  "raw_json": {}
}
```

#### Entities Table

```json
{
  "id": "entity_001",
  "doc_id": "doc_123",
  "type": "campaign",
  "name": "Spring Sale",
  "value": null
}
```

#### Relationships Table

```json
{
  "id": "rel_001",
  "source_doc": "doc_123",
  "target": "sales",
  "relation_type": "affects",
  "confidence": 0.7
}
```

---

## 🗄️ Storage Architecture

```bash
Supabase (PostgreSQL)
├── documents
├── entities
├── relationships
├── marketing_insights
```

---

## 🔌 Data Access Layer (Replaces MCP)

Agents interact with data via a database service layer:

### Available Operations

* `get_all_documents()`
* `insert_document(data)`
* `insert_entities(data)`
* `insert_relationships(data)`
* `insert_marketing_insight(data)`

---

## ✅ Output Example

```json
{
  "document_type": "campaign_report",
  "department": "Marketing",
  "summary": "Campaign ROI below expectations",
  "entities": [
    {"type": "campaign", "name": "Spring Sale"},
    {"type": "metric", "name": "ROI", "value": "low"}
  ],
  "tags": ["campaign", "ROI"],
  "relationships": [
    {"type": "affects", "target": "sales", "confidence": 0.7}
  ]
}
```

---

# 📈 2. Marketing Agent

## 🎯 Purpose

Generate business-driven marketing insights using structured multi-department data stored in Supabase.

---

## 🧠 Core Capabilities

* Reads structured data from database
* Identifies marketing-relevant signals
* Performs cross-domain reasoning
* Outputs actionable strategies

---

## 🔄 Workflow

```text
Query Database → Filter Relevant Data → Analyze Patterns → Generate Insight → Store Result
```

---

## 🔍 Data Sources

The agent consumes:

* Marketing campaign data
* Sales performance data
* HR performance indicators

---

## 🧪 Filtering Logic

Documents are selected based on:

* Tags (campaign, ROI, sales, customer)
* Department relevance
* Entity types

---

## 🧠 Insight Generation

### Example reasoning:

| Input Signals                   | Output Insight       |
| ------------------------------- | -------------------- |
| Low ROI + Active Campaign       | Campaign ineffective |
| Sales Drop + High Spend         | Poor targeting       |
| HR Low Performance + Sales Drop | Execution issue      |

---

## 📝 Output Storage

Marketing insights are stored in:

```json
{
  "id": "insight_001",
  "summary": "Campaign underperforming",
  "actions": [
    "Adjust targeting",
    "Refine segmentation"
  ]
}
```

---

## 🚀 Example Output

```json
{
  "summary": "Marketing campaign underperforming due to low ROI",
  "actions": [
    "Adjust audience targeting",
    "Reallocate budget",
    "Optimize campaign messaging"
  ]
}
```

---

# 🔗 Cross-Agent Interaction

## With Manager Agent

* Receives processed documents
* Provides insights for orchestration decisions

## With Other Agents

* HR → employee performance impact
* Sales → revenue signals
* Legal → compliance constraints

---

# ⚠️ Design Considerations

### 1. LLM Reliability

* Validate JSON outputs
* Handle malformed responses

### 2. Data Consistency

* Enforce schema across all agents
* Use consistent IDs

### 3. Scalability

* Supabase enables querying, indexing, and analytics
* Supports future vector search integration

---

# 🔮 Future Improvements

* Direct Gemini file upload (no parsing)
* Vector embeddings + semantic search
* Relationship graph visualization
* LLM-based reasoning (replace rule logic)
* Real-time streaming ingestion

---

# ✅ Summary

This module enables:

✔ Unstructured → Structured transformation
✔ Centralized knowledge via Supabase
✔ Cross-department intelligence
✔ Scalable multi-agent collaboration

---

**Owner:** AI Ingestion & Marketing Agent
**LLM:** Gemini (migratable to GLM)
**Framework:** LangChain
**Storage:** Supabase (PostgreSQL)