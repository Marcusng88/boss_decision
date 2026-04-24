"""Legal Agent — policies, contracts, compliance, legal cases."""
import json
import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are a Legal compliance analyst for an AI business decision engine.
Analyze the legal data provided (policies, contracts, cases) and return ONLY valid JSON:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable legal recommendation",
  "confidence": 0.80,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. 'RM 20,000 severance'",
  "trend": "up or down or flat"
}
Focus on: applicable policies, contractual obligations, legal risk, compliance requirements,
termination legality, notice periods, severance calculations.
Context is Malaysian employment law.
"""


class LegalAgent(BaseAgent):

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

        # Always fetch relevant policies based on query category
        category_map = {
            "termination": ["termination", "compliance", "performance"],
            "expansion": ["expansion", "compliance"],
            "procurement": ["procurement", "contracts"],
            "acquisition": ["acquisition", "contracts", "compliance"],
        }
        category = context.get("query_category", "")
        cats = category_map.get(category, [])
        all_policies = await self.db.get_legal_policies()
        relevant = [p for p in all_policies if not cats or p.get('policy_category') in cats]
        evidence.extend([
            {'source': 'legal_policy', 'type': 'policy',
             'record_id': p.get('legal_id'), 'data': p}
            for p in relevant
        ])

        # Employee-specific: contracts and legal cases
        emp_id = await self._resolve_employee_id(context)
        if emp_id:
            try:
                contracts = await self.db.get_legal_contracts(employee_id=emp_id)
                evidence.extend([
                    {'source': 'legal_contract', 'type': 'contract',
                     'record_id': c.get('id') or c.get('contract_id'), 'data': c}
                    for c in contracts
                ])
                cases = await self.db.get_legal_cases(employee_id=emp_id)
                evidence.extend([
                    {'source': 'legal_cases', 'type': 'case',
                     'record_id': c.get('id') or c.get('case_id'), 'data': c}
                    for c in cases
                ])
            except Exception:
                pass

        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        if not evidence:
            return AgentInsight(
                agent_name="Legal", emoji="⚖️",
                findings=["No legal records found"],
                risks=["Cannot assess legal risk without policy data"],
                recommendation="Consult legal team directly",
                confidence=0.0,
            )

        data_str = json.dumps(
            [e['data'] for e in evidence],
            default=str, indent=2
        )
        user_msg = f"Query: {query}\n\nLegal Data:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Legal", emoji="⚖️",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "See legal findings above"),
                confidence=float(result.get("confidence", 0.80)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Legal compliance check"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            return AgentInsight(
                agent_name="Legal", emoji="⚖️",
                findings=["Legal policies retrieved", f"{len(evidence)} legal records analyzed"],
                risks=["Ensure compliance with Malaysian Employment Act 1955",
                       "Verify notice period and severance requirements"],
                recommendation="Consult legal policies before proceeding; ensure full compliance",
                confidence=0.65,
                evidence_used=evidence,
                data_summary="Legal policy review",
                metric_value=f"{len(evidence)} records",
            )
