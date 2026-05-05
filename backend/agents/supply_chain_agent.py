"""
Supply Chain Agent - Evaluates logistics, inventory, and operational delivery risk.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class SupplyChainAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        try:
            docs = await self.db.get_department_documents("supply_chain")
            evidence.extend(docs)
        except Exception:
            pass

        try:
            docs_ops = await self.db.get_department_documents("operations")
            evidence.extend(docs_ops)
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
                agent_name="Supply Chain",
                findings=["No operations or supply chain evidence found"],
                risks=["Delivery feasibility is uncertain without logistics evidence"],
                recommendation="Collect inventory levels and lead-time data before committing to any delivery or scaling plan",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Operational evidence reviewed for delivery risk and capacity constraints")
        if "inventory" in combined or "stock" in combined:
            findings.append("Inventory or stock level signals detected in evidence")
        if "logistics" in combined or "lead time" in combined:
            findings.append("Logistics or lead-time data present — delivery schedule can be estimated")
        if "supplier" in combined:
            findings.append("Supplier dependency signals detected")
        if "warehouse" in combined or "fulfillment" in combined:
            findings.append("Fulfillment and warehousing data available for capacity assessment")

        if "delay" in combined or "shortage" in combined:
            risks.append("Potential supply disruption risk — shortages or delays flagged in evidence")
        if "critical" in combined and "delay" in combined:
            risks.append("Critical path delay detected — immediate bottleneck mitigation required")
        if "single source" in combined or "single supplier" in combined:
            risks.append("Single-source supplier dependency creates concentration risk")

        recommendation = "Proceed with phased rollout and monitor fulfillment KPIs closely"
        if "critical" in combined and "delay" in combined:
            recommendation = "Do not scale operations until a bottleneck mitigation plan is in place and validated"
        elif risks:
            recommendation = "Address identified supply-chain risks before scaling — prepare contingency supplier options"

        return AgentInsight(
            agent_name="Supply Chain",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.74,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze supply chain evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        evidence_parts: List[str] = []
        for e in evidence:
            summary = e.get("summary", "")
            if summary:
                evidence_parts.append(f"Operations/supply chain evidence: {summary}")
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No supply chain evidence found."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="supply chain and operations risk analyst",
            domain_focus=(
                "Inventory levels, logistics lead times, supplier dependencies, "
                "fulfillment capacity, delivery schedule risk, and operational bottleneck identification."
            ),
            fallback_insight=fallback,
        )
