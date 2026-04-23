"""
Legal Agent - Reviews compliance, due process, and policy risk.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class LegalAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        docs = await self.db.get_department_documents("legal")
        evidence.extend(docs)

        if context.get("document_summary"):
            evidence.append(
                {
                    "source": "uploaded_document",
                    "path": context.get("document_path", "(runtime_upload)"),
                    "department": context.get("document_department", "unknown"),
                    "summary": context.get("document_summary"),
                    "tags": context.get("document_tags", []),
                }
            )

        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        findings: List[str] = []
        risks: List[str] = []

        if not evidence:
            return AgentInsight(
                agent_name="Legal",
                findings=["No legal evidence found"],
                risks=["Compliance position unclear without policy evidence"],
                recommendation="Collect legal policy references before final action",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Legal review completed against available policy evidence")

        if "pip" in combined or "due process" in combined:
            findings.append("Due process and PIP sequencing are material to compliance")
        if "termination" in query.lower() or "dismissal" in combined:
            risks.append("Termination action may create legal exposure without documented process")
        if "high" in combined and "risk" in combined:
            risks.append("Policy notes indicate elevated compliance risk")

        recommendation = "Proceed only after due-process checklist is complete"
        if not risks:
            recommendation = "No immediate legal blockers found, proceed with documented controls"

        return AgentInsight(
            agent_name="Legal",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.72,
            evidence_used=evidence,
        )
