"""Marketing Agent — campaigns, market expansion, brand metrics."""
import json
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are a Marketing analyst for an AI business decision engine.
Analyze the marketing records provided and return ONLY valid JSON:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable marketing recommendation",
  "confidence": 0.75,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. '34% ROI'",
  "trend": "up or down or flat"
}
Focus on: campaign performance, market penetration, ROI, brand risk, expansion feasibility.
"""


class MarketingAgent(BaseAgent):

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        try:
            records = await self.db.get_marketing_records()
            evidence.extend([
                {'source': 'marketing_record', 'type': 'campaign',
                 'record_id': r.get('marketing_id'), 'data': r}
                for r in records
            ])
        except Exception:
            pass
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        if not evidence:
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=["No marketing records found"],
                risks=["Market feasibility cannot be assessed without data"],
                recommendation="Commission market research before proceeding",
                confidence=0.0,
            )

        data_str = json.dumps([e['data'] for e in evidence], default=str, indent=2)
        user_msg = f"Query: {query}\n\nMarketing Records:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "See marketing analysis"),
                confidence=float(result.get("confidence", 0.70)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Marketing analysis"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=[f"{len(evidence)} marketing campaign records analyzed"],
                risks=["Validate market assumptions before major commitment"],
                recommendation="Pilot campaign recommended before full rollout",
                confidence=0.60,
                evidence_used=evidence,
                data_summary="Campaign performance",
            )
