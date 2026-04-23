"""HR Agent — performance, attendance, warnings, PIP status."""
import json
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are an HR specialist analyst for an AI business decision engine.
Analyze the HR records provided and return ONLY valid JSON with no extra text:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable recommendation",
  "confidence": 0.75,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. '2.1/5 score'",
  "trend": "up or down or flat"
}
Focus on: performance scores, attendance, warning history, PIP status, termination eligibility.
"""


class HRAgent(BaseAgent):

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        if context.get('target_type') == 'employee' and context.get('target_id'):
            employee_id = context['target_id']
            try:
                employee = await self.db.get_employee(employee_id)
                if employee:
                    evidence.append({'source': 'employee', 'type': 'profile', 'data': employee})
            except Exception:
                pass
            hr_records = await self.db.get_employee_hr_records(employee_id)
            evidence.extend([
                {'source': 'hr_record', 'type': 'performance_review',
                 'record_id': r.get('hr_id'), 'data': r}
                for r in hr_records
            ])
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        hr_records = [e['data'] for e in evidence if e['source'] == 'hr_record']

        if not hr_records:
            return AgentInsight(
                agent_name="HR", emoji="👤",
                findings=["No HR records found"],
                risks=["Insufficient HR data for analysis"],
                recommendation="Gather HR records before proceeding",
                confidence=0.0,
            )

        # Build data summary for LLM
        data_str = json.dumps(hr_records, default=str, indent=2)
        user_msg = f"Query: {query}\n\nHR Records:\n{data_str}"

        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="HR", emoji="👤",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "See findings above"),
                confidence=float(result.get("confidence", 0.7)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "HR performance data"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception as e:
            # Fallback rule-based
            return self._rule_based(hr_records, evidence, str(e))

    def _rule_based(self, hr_records, evidence, error_note="") -> AgentInsight:
        findings, risks = [], []
        scores = [r['performance_score'] for r in hr_records[:3] if r.get('performance_score')]
        if scores:
            avg = sum(scores) / len(scores)
            findings.append(f"Average performance score: {avg:.1f}/5.0")
            if avg < 2.5:
                findings.append("Performance consistently below 2.5/5 threshold")
                risks.append("Sustained underperformance documented")
        warnings = sum(r.get('warning_count', 0) for r in hr_records)
        if warnings > 0:
            findings.append(f"Total warnings issued: {warnings}")
            risks.append("Disciplinary history on record")
        pip = next((r.get('pip_status') for r in hr_records if r.get('pip_status')), None)
        if pip:
            findings.append(f"PIP status: {pip}")
        if not pip:
            risks.append("PIP not yet initiated — required before termination per policy")

        avg_score = sum(scores) / len(scores) if scores else 3.0
        rec = (
            "Initiate mandatory 60-day PIP before considering termination"
            if avg_score < 2.5 else
            "Performance issues present; monitor closely"
        )
        metric = f"{avg_score:.1f}/5 score" if scores else "N/A"
        trend = "down" if len(scores) >= 2 and scores[0] < scores[-1] else "flat"
        return AgentInsight(
            agent_name="HR", emoji="👤",
            findings=findings, risks=risks, recommendation=rec,
            confidence=0.70, evidence_used=evidence,
            data_summary="HR performance review", metric_value=metric, trend=trend,
        )
