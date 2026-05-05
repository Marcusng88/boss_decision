"""
Marketing Agent - Evaluates campaign performance and market messaging impact.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class MarketingAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []
        docs = await self.db.get_department_documents("marketing")
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
                agent_name="Marketing",
                findings=["No marketing evidence found"],
                risks=["Campaign decision confidence is low without channel metrics"],
                recommendation="Collect campaign ROI and conversion evidence first",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Marketing signals reviewed from local knowledge and uploaded context")
        if "roi" in combined:
            findings.append("ROI signal detected in evidence")
        if "segmentation" in combined or "audience" in combined:
            findings.append("Audience targeting issue signal detected")

        if "below target" in combined or "drop" in combined or "underperform" in combined:
            risks.append("Campaign effectiveness risk is elevated")

        recommendation = "Run controlled optimization cycle before scaling spend"
        if "reallocate" in combined:
            recommendation = "Reallocate budget and run A/B creative tests immediately"

        return AgentInsight(
            agent_name="Marketing",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.76,
            evidence_used=evidence,
        )
