"""
Supply Chain Agent - Evaluates logistics, inventory, and operational delivery risk.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class SupplyChainAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        docs = await self.db.get_department_documents("supply_chain")
        evidence.extend(docs)
        docs_ops = await self.db.get_department_documents("operations")
        evidence.extend(docs_ops)

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
                agent_name="Supply_Chain",
                findings=["No operations/supply-chain evidence found"],
                risks=["Delivery feasibility uncertain without logistics evidence"],
                recommendation="Collect inventory and lead-time evidence before commitment",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Operational evidence reviewed for delivery risk and capacity")
        if "inventory" in combined or "stock" in combined:
            findings.append("Inventory signal detected")
        if "logistics" in combined or "lead time" in combined:
            findings.append("Logistics lead-time signal detected")

        if "delay" in combined or "shortage" in combined:
            risks.append("Potential disruption risk in supply flow")

        recommendation = "Proceed with phased rollout and monitor fulfillment KPIs"
        if "critical" in combined and "delay" in combined:
            recommendation = "Do not scale until bottleneck mitigation plan is in place"

        return AgentInsight(
            agent_name="Supply_Chain",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.74,
            evidence_used=evidence,
        )
