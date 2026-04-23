"""
HR Agent - Analyzes employee performance, attendance, warnings, PIP status.
"""
import json
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class HRAgent(BaseAgent):
    """
    HR domain specialist agent.
    Focuses on: performance reviews, attendance, warnings, PIP status, termination policies.
    """

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve HR-related evidence.

        For employee termination decisions:
        - Performance reviews (last 2-4 quarters)
        - Attendance records
        - Warning history
        - PIP status
        """
        evidence = []

        # Injected document context (uploaded file)
        if context.get("document_summary"):
            evidence.append(
                {
                    "source": "uploaded_document",
                    "path": context.get("document_path", "(runtime_upload)"),
                    "department": context.get("document_department", "HR"),
                    "summary": context.get("document_summary"),
                    "tags": context.get("document_tags", []),
                }
            )

        # If target is an employee, get their HR records
        if context.get("target_type") == "employee" and context.get("target_id"):
            employee_id = context["target_id"]
            hr_records = await self.db.get_employee_hr_records(employee_id)
            evidence.extend(
                [
                    {
                        "source": "hr_record",
                        "type": "performance_review",
                        "record_id": record["hr_id"],
                        "data": record,
                    }
                    for record in hr_records
                ]
            )

        return evidence

    # ------------------------------------------------------------------
    # Rule-based core analysis
    # ------------------------------------------------------------------

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Produce a structured AgentInsight from pure rule-based logic."""
        hr_records = [e["data"] for e in evidence if e.get("source") == "hr_record"]
        doc_summaries = [
            e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")
        ]

        findings: List[str] = []
        risks: List[str] = []

        # --- Uploaded document signals ---
        if doc_summaries:
            combined_doc = " ".join(doc_summaries).lower()
            findings.append("HR document uploaded and reviewed for performance context")
            if "pip" in combined_doc:
                findings.append("PIP (Performance Improvement Plan) is mentioned in the uploaded document")
            if "warning" in combined_doc:
                findings.append("Warning history referenced in the document")
            if "attendance" in combined_doc:
                findings.append("Attendance issues noted in the uploaded document")
            if "underperform" in combined_doc or "below" in combined_doc:
                risks.append("Document indicates sustained underperformance — high unfair dismissal risk without prior PIP")
            if "high" in combined_doc and "risk" in combined_doc:
                risks.append("Document flags elevated compliance or legal risk")

        # --- Database HR record signals ---
        if hr_records:
            recent_scores = [r["performance_score"] for r in hr_records[:3] if r.get("performance_score")]
            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                findings.append(f"Average performance score (last 3 reviews): {avg_score:.1f}/5.0")
                if avg_score < 2.5:
                    findings.append("Performance consistently below expectations (< 2.5/5)")
                    risks.append("Sustained underperformance documented across multiple review periods")

            total_warnings = sum(r.get("warning_count", 0) for r in hr_records)
            if total_warnings > 0:
                findings.append(f"Total formal warnings issued: {total_warnings}")
                risks.append("Disciplinary action history on record")

            pip_records = [r for r in hr_records if r.get("pip_status")]
            if pip_records:
                latest_pip = pip_records[0]["pip_status"]
                findings.append(f"PIP status: {latest_pip}")
                if not latest_pip:
                    risks.append("PIP not initiated — required before performance-based termination per HR policy")

            # Recommendation logic
            if recent_scores and sum(recent_scores) / len(recent_scores) < 2.5 and total_warnings >= 2:
                if not pip_records or not pip_records[0].get("pip_status"):
                    recommendation = "Do not fire employee yet; initiate a formal Performance Improvement Plan (PIP) first to comply with HR policy and mitigate unfair dismissal risks."
                else:
                    recommendation = "Performance grounds for termination exist if PIP has been formally completed and failed."
            else:
                recommendation = "Performance issues present but documentation insufficient for termination — schedule formal review and issue written warning if not already done."
        else:
            # Fallback when only document context is present
            recommendation = (
                "Do not fire employee yet; initiate a formal Performance Improvement Plan (PIP) first to comply with HR policy and mitigate unfair dismissal risks."
                if risks
                else "HR records not available from database; base decision on uploaded document context only."
            )

        if not findings:
            findings = ["No HR evidence found in database or uploaded documents"]
        if not risks:
            risks = ["Insufficient evidence to assess risk — proceed with caution"]

        return AgentInsight(
            agent_name="HR",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.75 if (hr_records or doc_summaries) else 0.0,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze HR evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        # Build a compact evidence summary for the LLM
        evidence_parts: List[str] = []
        for e in evidence:
            if e.get("source") == "uploaded_document":
                evidence_parts.append(f"Document summary: {e.get('summary', '')}")
            elif e.get("source") == "hr_record":
                data = e.get("data", {})
                evidence_parts.append(
                    f"HR Record — score: {data.get('performance_score')}, "
                    f"warnings: {data.get('warning_count')}, pip_status: {data.get('pip_status')}"
                )
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No HR evidence retrieved."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="HR compliance and performance management specialist",
            domain_focus=(
                "Employee performance history, attendance records, warning counts, "
                "PIP (Performance Improvement Plan) status, and HR policy compliance "
                "before any termination decision."
            ),
            fallback_insight=fallback,
        )
