"""
Marketing Agent - Evaluates campaign performance and market messaging impact.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class MarketingAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        try:
            docs = await self.db.get_department_documents("marketing")
            evidence.extend(docs)
        except Exception:
            pass

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

    # ------------------------------------------------------------------
    # Rule-based core analysis
    # ------------------------------------------------------------------

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Produce structured insights from pure rule-based logic."""
        findings: List[str] = []
        risks: List[str] = []

        if not evidence:
            return AgentInsight(
                agent_name="Marketing",
                findings=["No marketing evidence found in the knowledge base"],
                risks=["Campaign decision confidence is low without channel metrics"],
                recommendation="Collect campaign ROI, conversion rate, and audience segmentation data first",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Marketing signals reviewed from knowledge base and uploaded context")
        if "roi" in combined:
            findings.append("ROI metric detected in evidence — campaign profitability can be assessed")
        if "segmentation" in combined or "audience" in combined:
            findings.append("Audience targeting signals detected — segmentation strategy may need review")
        if "conversion" in combined:
            findings.append("Conversion rate data present — funnel performance can be evaluated")

        if "below target" in combined or "drop" in combined or "underperform" in combined:
            risks.append("Campaign effectiveness risk is elevated — current spend may not be justified")
        if "churn" in combined:
            risks.append("Customer churn signal detected — retention-focused marketing may be needed")

        recommendation = "Run a controlled optimization cycle before scaling spend"
        if "reallocate" in combined:
            recommendation = "Reallocate budget to higher-performing channels and run A/B creative tests immediately"
        elif "underperform" in combined:
            recommendation = "Pause underperforming campaigns and diagnose root cause before re-investing"

        return AgentInsight(
            agent_name="Marketing",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.76,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze marketing evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        evidence_parts: List[str] = []
        for e in evidence:
            summary = e.get("summary", "")
            if summary:
                evidence_parts.append(f"Marketing evidence: {summary}")
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No marketing evidence found."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="marketing performance and campaign strategy analyst",
            domain_focus=(
                "Campaign ROI, audience segmentation effectiveness, channel performance, "
                "conversion rates, brand positioning, and budget allocation recommendations."
            ),
            fallback_insight=fallback,
        )
