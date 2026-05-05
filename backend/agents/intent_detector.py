"""
Intent detection: determines which agents to invoke and extracts entity context.
"""
import re
from .llm_client import llm_json

SYSTEM_PROMPT = """You are an intent classifier for a multi-agent business decision engine.

Available specialist agents and their domains:
- hr: employee performance, attendance, warnings, PIP status, termination grounds
- sales: revenue, deals closed, pipeline health, quota attainment
- legal: policies, contracts, legal cases, compliance rules, termination law
- finance: budgets, costs, salaries, financial KPIs, ROI
- marketing: campaigns, market expansion, brand metrics, marketing ROI
- supply_chain: inventory, procurement, vendors, supply shortages

Analyze the query and respond with ONLY valid JSON (no markdown, no explanation):
{
  "agents": ["agent1", "agent2"],
  "target_type": "employee",
  "target_id": 1023,
  "target_name": "employee #1023",
  "query_category": "termination"
}

Rules:
- agents: list of agent names to invoke (1-6 agents, choose only relevant ones)
- target_type: "employee", "department", "market", "competitor", "vendor", "general"
- target_id: integer extracted from query, or null if none
- target_name: human-readable name of the target entity
- query_category: short label like "termination", "acquisition", "expansion", "procurement", "performance", "compliance"
"""


async def detect_intent(query: str) -> dict:
    """Use LLM to detect intent and return context dict."""
    try:
        result = await llm_json(SYSTEM_PROMPT, query, temperature=0.1)
        # Ensure required keys exist with sensible defaults
        return {
            "agents": result.get("agents", ["hr"]),
            "target_type": result.get("target_type", "general"),
            "target_id": result.get("target_id"),
            "target_name": result.get("target_name", ""),
            "query_category": result.get("query_category", "general"),
        }
    except Exception:
        # Fallback: simple keyword detection
        return _fallback_detect(query)


def _fallback_detect(query: str) -> dict:
    """Simple keyword-based fallback intent detection."""
    q = query.lower()

    agents = []
    if any(w in q for w in ["fire", "terminat", "performance", "pip", "warning", "employ"]):
        agents += ["hr", "legal", "sales"]
    if any(w in q for w in ["acqui", "merger", "buy", "purchase"]):
        agents += ["finance", "legal", "marketing"]
    if any(w in q for w in ["expand", "market", "launch", "enter"]):
        agents += ["marketing", "finance", "legal", "supply_chain"]
    if any(w in q for w in ["vendor", "supplier", "procurement", "inventory"]):
        agents += ["supply_chain", "finance", "legal"]
    if not agents:
        agents = ["hr", "finance"]

    # Extract employee ID
    target_id = None
    m = re.search(r'#(\d+)', query)
    if m:
        target_id = int(m.group(1))

    target_type = "employee" if target_id else "general"

    return {
        "agents": list(dict.fromkeys(agents)),  # deduplicate preserving order
        "target_type": target_type,
        "target_id": target_id,
        "target_name": f"employee #{target_id}" if target_id else "",
        "query_category": "general",
    }
