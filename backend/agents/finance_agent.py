"""Finance Agent — budgets, costs, financial KPIs, ROI."""
import json
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are a Finance analyst for an AI business decision engine.
Analyze the financial records provided and return ONLY valid JSON:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable financial recommendation",
  "confidence": 0.80,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. 'RM 65k total cost'",
  "trend": "up or down or flat"
}
Focus on: cost of action vs inaction, budget headroom, ROI, financial risk exposure.
Currency is Malaysian Ringgit (RM).
"""


class FinanceAgent(BaseAgent):

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        emp_id = context.get('target_id') if context.get('target_type') == 'employee' else None
        try:
            records = await self.db.get_finance_records(employee_id=emp_id)
            evidence.extend([
                {'source': 'finance_record', 'type': 'financial_metric',
                 'record_id': r.get('finance_id'), 'data': r}
                for r in records
            ])
        except Exception:
            pass
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        if not evidence:
            return AgentInsight(
                agent_name="Finance", emoji="💰",
                findings=["No financial records available"],
                risks=["Financial impact cannot be quantified without data"],
                recommendation="Request finance records for full cost-benefit analysis",
                confidence=0.0,
            )

        data_str = json.dumps([e['data'] for e in evidence], default=str, indent=2)
        user_msg = f"Query: {query}\n\nFinancial Records:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Finance", emoji="💰",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "Review financial impact carefully"),
                confidence=float(result.get("confidence", 0.75)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Financial analysis"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            return AgentInsight(
                agent_name="Finance", emoji="💰",
                findings=[f"{len(evidence)} financial records analyzed"],
                risks=["Validate financial projections before committing"],
                recommendation="Assess full cost-benefit before proceeding",
                confidence=0.60,
                evidence_used=evidence,
                data_summary="Financial review",
            )
