"""HR Agent — performance, attendance, warnings, PIP status."""
import json
import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

SYSTEM_PROMPT = """You are an HR specialist analyst for an AI business decision engine.
Analyze the employee profile and HR records provided and return ONLY valid JSON with no extra text:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable recommendation",
  "confidence": 0.75,
  "data_summary": "brief 3-5 word summary e.g. 'Senior engineer, Dept A'",
  "metric_value": "key metric e.g. '2.1/5 score'",
  "trend": "up or down or flat"
}
Cover: employee name/role/department/tenure (from profile), performance scores, attendance, warning history, PIP status.
If the query asks for basic employee info, include position, department, hire date, and employment status in findings.
"""


class HRAgent(BaseAgent):

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []

        # Uploaded document context
        if context.get("document_summary"):
            evidence.append({
                "source": "uploaded_document",
                "path": context.get("document_path", "(runtime_upload)"),
                "department": context.get("document_department", "HR"),
                "summary": context.get("document_summary"),
                "tags": context.get("document_tags", []),
            })

        # Resolve employee_id: direct ID wins, name search as fallback
        employee_id = None
        if context.get("target_type") == "employee" and context.get("target_id"):
            employee_id = int(context["target_id"])
        elif context.get("target_name"):
            raw = re.sub(r"employee\s*#?\d*\s*", "", str(context["target_name"]),
                         flags=re.IGNORECASE).strip()
            if raw and not raw.isdigit():
                try:
                    results = await self.db.search_employees_by_name(raw)
                    if results:
                        employee_id = results[0].get("employee_id")
                except Exception:
                    pass

        if employee_id is None:
            return evidence

        # Employee profile
        try:
            employee = await self.db.get_employee(employee_id)
            if employee:
                evidence.append({"source": "employee", "type": "profile", "data": employee})
        except Exception:
            pass

        # HR records
        try:
            hr_records = await self.db.get_employee_hr_records(employee_id)
            evidence.extend([
                {"source": "hr_record", "type": "performance_review",
                 "record_id": r.get("hr_id"), "data": r}
                for r in hr_records
            ])
        except Exception:
            pass

        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        hr_records = [e["data"] for e in evidence if e["source"] == "hr_record"]
        employee_profile = next((e["data"] for e in evidence if e["source"] == "employee"), None)
        doc_summaries = [e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")]

        # Profile-only fallback (no HR records yet)
        if not hr_records and employee_profile:
            name = employee_profile.get("name") or employee_profile.get("full_name") or "Unknown"
            position = employee_profile.get("position") or employee_profile.get("job_title") or "Unknown position"
            dept = ""
            if isinstance(employee_profile.get("department"), dict):
                dept = employee_profile["department"].get("name", "")
            if not dept:
                dept = str(employee_profile.get("dept_id", "")) or "Not specified"
            hire_date = employee_profile.get("hire_date") or employee_profile.get("start_date") or "Unknown"
            status = employee_profile.get("employment_status") or employee_profile.get("status") or "Active"
            findings = [
                f"Employee: {name} — {position}",
                f"Department: {dept}",
                f"Hire date: {hire_date} | Status: {status}",
                "No performance review records on file",
            ]
            if doc_summaries:
                findings.append("HR document reviewed for additional context")
            return AgentInsight(
                agent_name="HR", emoji="👤",
                findings=findings,
                risks=["Lack of HR records limits performance assessment"],
                recommendation="Initiate formal performance tracking before making personnel decisions",
                confidence=0.3,
                evidence_used=evidence,
                data_summary=f"{name}, {position}",
            )

        if not hr_records and not employee_profile:
            if doc_summaries:
                return self._rule_based_doc_only(doc_summaries, evidence)
            return AgentInsight(
                agent_name="HR", emoji="👤",
                findings=["Employee not found or no HR records available"],
                risks=["Cannot assess performance, attendance, or disciplinary history without data"],
                recommendation="Verify employee ID and gather HR records before proceeding",
                confidence=0.0,
                evidence_used=evidence,
            )

        profile_str = json.dumps(employee_profile, default=str, indent=2) if employee_profile else "Not available"
        data_str = json.dumps(hr_records, default=str, indent=2)
        doc_str = "\n".join(doc_summaries) if doc_summaries else ""
        user_msg = (
            f"Query: {query}\n\nEmployee Profile:\n{profile_str}\n\nHR Records:\n{data_str}"
            + (f"\n\nUploaded document context:\n{doc_str}" if doc_str else "")
        )

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
            return self._rule_based(hr_records, evidence, str(e))

    def _rule_based_doc_only(self, doc_summaries: List[str], evidence: List[Dict]) -> AgentInsight:
        combined = " ".join(doc_summaries).lower()
        findings = ["HR document reviewed for performance context"]
        risks = []
        if "pip" in combined:
            findings.append("PIP (Performance Improvement Plan) mentioned in document")
        if "warning" in combined:
            findings.append("Warning history referenced in document")
        if "underperform" in combined or "below" in combined:
            risks.append("Document indicates sustained underperformance")
        return AgentInsight(
            agent_name="HR", emoji="👤",
            findings=findings,
            risks=risks or ["Insufficient evidence — assess HR records before deciding"],
            recommendation="Initiate formal PIP before any termination to comply with HR policy",
            confidence=0.35,
            evidence_used=evidence,
            data_summary="Document-only review",
        )

    def _rule_based(self, hr_records, evidence, error_note="") -> AgentInsight:
        findings, risks = [], []
        scores = [r["performance_score"] for r in hr_records[:3] if r.get("performance_score")]
        if scores:
            avg = sum(scores) / len(scores)
            findings.append(f"Average performance score: {avg:.1f}/5.0")
            if avg < 2.5:
                findings.append("Performance consistently below 2.5/5 threshold")
                risks.append("Sustained underperformance documented")
        warnings = sum(r.get("warning_count", 0) for r in hr_records)
        if warnings > 0:
            findings.append(f"Total warnings issued: {warnings}")
            risks.append("Disciplinary history on record")
        pip = next((r.get("pip_status") for r in hr_records if r.get("pip_status")), None)
        if pip:
            findings.append(f"PIP status: {pip}")
        if not pip:
            risks.append("PIP not yet initiated — required before termination per policy")

        avg_score = sum(scores) / len(scores) if scores else 3.0
        rec = (
            "Initiate mandatory 60-day PIP before considering termination"
            if avg_score < 2.5 else
            "Performance issues present; monitor closely with structured review"
        )
        metric = f"{avg_score:.1f}/5 score" if scores else "N/A"
        trend = "down" if len(scores) >= 2 and scores[0] < scores[-1] else "flat"
        return AgentInsight(
            agent_name="HR", emoji="👤",
            findings=findings, risks=risks, recommendation=rec,
            confidence=0.70, evidence_used=evidence,
            data_summary="HR performance review", metric_value=metric, trend=trend,
        )
