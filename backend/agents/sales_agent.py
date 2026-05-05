"""Sales Agent — revenue, deals, pipeline, quota attainment."""
import json
import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are a Sales performance analyst for an AI business decision engine.
Analyze the sales records provided and return ONLY valid JSON with no extra text:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable recommendation",
  "confidence": 0.80,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. 'RM 45,200 revenue'",
  "trend": "up or down or flat"
}
Focus on: total revenue, deal count, pipeline health, win/loss ratio, trend vs team average.
Currency is Malaysian Ringgit (RM).
"""


class SalesAgent(BaseAgent):

    def _extract_period(self, query: str) -> str | None:
        """Extract period like '2026-Q1' from query text."""
        # Match explicit "2026-Q1" format
        m = re.search(r'(20\d{2})[-\s]?(Q[1-4])', query, re.IGNORECASE)
        if m:
            return f"{m.group(1)}-{m.group(2).upper()}"
        # Match standalone quarter like "Q1", "Q3" — assume current year 2026
        m = re.search(r'\b(Q[1-4])\b', query, re.IGNORECASE)
        if m:
            return f"2026-{m.group(1).upper()}"
        return None

    async def _resolve_employee_id(self, context: Dict[str, Any]) -> int | None:
        """Resolve employee_id from context — direct ID first, name search as fallback."""
        if context.get('target_type') == 'employee':
            if context.get('target_id'):
                return int(context['target_id'])
            if context.get('target_name'):
                raw = re.sub(r'employee\s*#?\d*\s*', '', str(context['target_name']),
                             flags=re.IGNORECASE).strip()
                if raw and not raw.isdigit():
                    try:
                        results = await self.db.search_employees_by_name(raw)
                        if results:
                            return results[0].get('employee_id')
                    except Exception:
                        pass
        return None

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        period = self._extract_period(query)
        employee_id = await self._resolve_employee_id(context)

        if employee_id:
            records = await self.db.get_employee_sales_records(employee_id, period=period)
            evidence.extend([
                {'source': 'sales_record', 'type': 'deal',
                 'record_id': r.get('sales_id'), 'data': r}
                for r in records
            ])
        else:
            # General or department-level query — fetch all sales records
            records = await self.db.get_all_sales_records(period=period)
            evidence.extend([
                {'source': 'sales_record', 'type': 'deal',
                 'record_id': r.get('sales_id'), 'data': r}
                for r in records
            ])
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        sales_records = [e['data'] for e in evidence if e['source'] == 'sales_record']

        if not sales_records:
            return AgentInsight(
                agent_name="Sales", emoji="📊",
                findings=["No sales records found"],
                risks=["Cannot assess sales performance without data"],
                recommendation="Gather sales records before proceeding",
                confidence=0.0,
            )

        data_str = json.dumps(sales_records, default=str, indent=2)
        user_msg = f"Query: {query}\n\nSales Records:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Sales", emoji="📊",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "See findings above"),
                confidence=float(result.get("confidence", 0.75)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Sales performance"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            return self._rule_based(sales_records, evidence)

    def _rule_based(self, records, evidence) -> AgentInsight:
        closed = [r for r in records if r.get('deal_stage') == 'closed']
        pipeline = [r for r in records if r.get('deal_stage') == 'pipeline']
        lost = [r for r in records if r.get('deal_stage') == 'lost']
        total_rev = sum(r.get('amount', 0) for r in closed)
        findings = [
            f"Closed deals: {len(closed)}",
            f"Total revenue: RM {total_rev:,.0f}",
            f"Pipeline: {len(pipeline)} deals | Lost: {len(lost)} deals",
        ]
        risks = []
        if total_rev < 50000:
            risks.append("Revenue below minimum performance threshold (RM 50k)")
        if len(pipeline) < 2:
            risks.append("Pipeline too thin — insufficient active opportunities")
        rec = (
            "Sales performance below standards; revenue contribution insufficient"
            if total_rev < 50000 else
            "Sales performance acceptable; monitor pipeline progression"
        )
        trend = "down" if total_rev < 50000 else "flat"
        return AgentInsight(
            agent_name="Sales", emoji="📊",
            findings=findings, risks=risks, recommendation=rec,
            confidence=0.75, evidence_used=evidence,
            data_summary="Sales revenue review",
            metric_value=f"RM {total_rev:,.0f}", trend=trend,
        )
