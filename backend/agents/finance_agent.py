"""Finance Agent — budgets, costs, financial KPIs, ROI."""
import json
import re
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

    async def _resolve_employee_id(self, context: Dict[str, Any]):
        if context.get("target_type") == "employee":
            if context.get("target_id"):
                return int(context["target_id"])
            if context.get("target_name"):
                raw = re.sub(r"employee\s*#?\d*\s*", "", str(context["target_name"]),
                             flags=re.IGNORECASE).strip()
                if raw and not raw.isdigit():
                    try:
                        results = await self.db.search_employees_by_name(raw)
                        if results:
                            return results[0].get("employee_id")
                    except Exception:
                        pass
        return None

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []

        # Uploaded document context
        if context.get("document_summary"):
            evidence.append({
                "source": "uploaded_document",
                "path": context.get("document_path", "(runtime_upload)"),
                "department": context.get("document_department", "Finance"),
                "summary": context.get("document_summary"),
                "tags": context.get("document_tags", []),
            })

        emp_id = await self._resolve_employee_id(context)

        if emp_id:
            # Employee-specific: try employee records first
            try:
                records = await self.db.get_finance_records(employee_id=emp_id)
                if records:
                    evidence.extend([
                        {"source": "finance_record", "type": "employee_finance",
                         "record_id": r.get("finance_id"), "data": r}
                        for r in records
                    ])
            except Exception:
                pass

            # Fall back to department-level records as context
            if not any(e["source"] == "finance_record" for e in evidence):
                try:
                    employee = await self.db.get_employee(emp_id)
                    dept_id = employee.get("dept_id") if employee else None
                    if dept_id:
                        records = await self.db.get_finance_records(dept_id=dept_id)
                        if records:
                            evidence.extend([
                                {"source": "finance_record", "type": "department_finance",
                                 "record_id": r.get("finance_id"), "data": r}
                                for r in records[:10]
                            ])
                except Exception:
                    pass
            return evidence

        # General / company-wide query
        try:
            records = await self.db.fetch_finance_limited(limit=20)
            evidence.extend([
                {"source": "finance_record", "type": "general_finance",
                 "record_id": r.get("finance_id"), "data": r}
                for r in records
            ])
        except Exception:
            pass

        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        # Combine DB records + document context
        finance_evidence = [e for e in evidence if e.get("source") == "finance_record"]
        doc_summaries = [e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")]

        if not finance_evidence and not doc_summaries:
            return AgentInsight(
                agent_name="Finance", emoji="💰",
                findings=["No financial records found in the database"],
                risks=["Financial impact cannot be quantified without data"],
                recommendation="Establish financial tracking records before proceeding",
                confidence=0.0,
                evidence_used=evidence,
            )

        source_type = finance_evidence[0].get("type", "general") if finance_evidence else "document_only"
        context_note = ""
        if source_type == "department_finance":
            context_note = "\n(Note: showing department-level records; employee-specific records unavailable)"
        elif source_type == "general_finance":
            context_note = "\n(Note: showing general company finance records)"

        data_str = json.dumps([e["data"] for e in finance_evidence], default=str, indent=2)
        doc_str = "\n".join(doc_summaries) if doc_summaries else ""
        user_msg = (
            f"Query: {query}{context_note}\n\nFinancial Records:\n{data_str[:6000]}"
            + (f"\n\nUploaded document context:\n{doc_str}" if doc_str else "")
        )

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
                findings=[f"{len(finance_evidence)} financial record(s) analyzed ({source_type.replace('_', ' ')})"]
                         + (["Document context reviewed"] if doc_summaries else []),
                risks=["Validate financial projections before committing"],
                recommendation="Assess full cost-benefit before proceeding",
                confidence=0.55,
                evidence_used=evidence,
                data_summary="Financial review",
            )
