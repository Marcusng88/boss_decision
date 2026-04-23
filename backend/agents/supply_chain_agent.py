"""Supply Chain Agent — inventory, procurement, vendors, shortages."""
import json
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are a Supply Chain analyst for an AI business decision engine.
Analyze the supply chain records provided and return ONLY valid JSON:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable supply chain recommendation",
  "confidence": 0.75,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. '3 shortage flags'",
  "trend": "up or down or flat"
}
Focus on: inventory levels, demand vs supply gaps, vendor risk, procurement lead times, shortage flags.
"""


class SupplyChainAgent(BaseAgent):

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        try:
            records = await self.db.get_supply_records()
            evidence.extend([
                {'source': 'supply_record', 'type': 'inventory',
                 'record_id': r.get('supply_id'), 'data': r}
                for r in records
            ])
        except Exception:
            pass
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        if not evidence:
            return AgentInsight(
                agent_name="Supply Chain", emoji="🔗",
                findings=["No supply chain records found"],
                risks=["Supply risk cannot be quantified without inventory data"],
                recommendation="Gather supply chain data before committing",
                confidence=0.0,
            )

        data_str = json.dumps([e['data'] for e in evidence], default=str, indent=2)
        user_msg = f"Query: {query}\n\nSupply Chain Records:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Supply Chain", emoji="🔗",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "See supply chain analysis"),
                confidence=float(result.get("confidence", 0.70)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Supply chain review"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            shortage_count = sum(1 for e in evidence if e['data'].get('shortage_flag'))
            return AgentInsight(
                agent_name="Supply Chain", emoji="🔗",
                findings=[
                    f"{len(evidence)} supply records analyzed",
                    f"{shortage_count} shortage flag(s) detected",
                ],
                risks=["Address shortages before expanding or committing resources"],
                recommendation="Review shortage items before proceeding",
                confidence=0.60,
                evidence_used=evidence,
                data_summary="Inventory review",
                metric_value=f"{shortage_count} shortages",
                trend="down" if shortage_count > 0 else "flat",
            )
