"""
Supply Chain Agent - Evaluates logistics, inventory, and operational delivery risk.
Uses Zhipu AI via the shared _llm_analyze helper.
"""
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentInsight

logger = logging.getLogger(__name__)


class SupplyChainAgent(BaseAgent):

    def __init__(self, db_service, llm=None, company_db: Optional[Any] = None):
        super().__init__(db_service, llm)
        self._company_db = company_db

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        if context.get("document_summary"):
            evidence.append({
                "source": "uploaded_document",
                "path": context.get("document_path", "(runtime_upload)"),
                "department": context.get("document_department", "Operations"),
                "summary": context.get("document_summary"),
                "tags": context.get("document_tags", []),
            })

        db = self._company_db or self.db
        try:
            rows = await db.fetch_supply_limited(limit=12)
            for row in rows:
                evidence.append({
                    "source": "supabase_supply_record",
                    "record_id": row.get("supply_id"),
                    "data": row,
                })
            if rows:
                logger.info("SupplyChainAgent: loaded %d supply records", len(rows))
        except Exception as exc:
            logger.warning("SupplyChainAgent: failed to load supply records: %s", exc)

        return evidence

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        records = [e["data"] for e in evidence if e.get("source") == "supabase_supply_record" and e.get("data")]
        doc_summaries = [e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")]

        findings: List[str] = []
        risks: List[str] = []

        if doc_summaries:
            combined_doc = " ".join(doc_summaries).lower()
            findings.append("Supply chain document reviewed for operational context")
            if "delay" in combined_doc or "shortage" in combined_doc:
                risks.append("Potential supply disruption flagged in uploaded document")
            if "single source" in combined_doc or "single supplier" in combined_doc:
                risks.append("Single-source supplier dependency detected in document")

        if not records:
            return AgentInsight(
                agent_name="Supply Chain",
                findings=findings or ["No supply chain records found in the database"],
                risks=risks or ["Delivery feasibility is uncertain without logistics evidence"],
                recommendation="Collect inventory levels and lead-time data before committing to any delivery or scaling plan",
                confidence=0.2 if doc_summaries else 0.35,
                evidence_used=evidence,
            )

        periods = list({r.get("period") for r in records if r.get("period")})
        item_names = list({r.get("item_name") for r in records if r.get("item_name")})
        statuses = [r.get("status", "") for r in records]

        findings.append(f"Supply records reviewed: {len(records)} entries across {len(periods)} period(s)")
        if item_names:
            findings.append(f"Tracked items: {', '.join(item_names[:5])}")

        delayed = [r for r in records if str(r.get("status", "")).lower() in ("delayed", "critical", "shortage")]
        if delayed:
            risks.append(f"{len(delayed)} supply record(s) flagged as delayed/critical/shortage")

        low_stock = [r for r in records if r.get("quantity") is not None and r.get("quantity", 999) < 10]
        if low_stock:
            risks.append(f"{len(low_stock)} item(s) with critically low stock quantity (<10 units)")

        recommendation = "Proceed with phased rollout and monitor fulfillment KPIs closely"
        if delayed:
            recommendation = "Address identified supply-chain risks before scaling — prepare contingency supplier options"
        if low_stock and delayed:
            recommendation = "Do not scale operations until bottleneck mitigation plan is validated; low stock and delays detected"

        return AgentInsight(
            agent_name="Supply Chain",
            findings=findings,
            risks=risks or ["Monitor supplier lead times and inventory levels regularly"],
            recommendation=recommendation,
            confidence=0.74,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        fallback = self._rule_based_analyze(evidence, query)

        evidence_parts: List[str] = []
        for e in evidence:
            if e.get("source") == "uploaded_document":
                evidence_parts.append(f"Document: {e.get('summary', '')}")
            elif e.get("source") == "supabase_supply_record" and e.get("data"):
                d = e["data"]
                evidence_parts.append(
                    f"Supply record: item={d.get('item_name')} | qty={d.get('quantity')} | "
                    f"status={d.get('status')} | period={d.get('period')}"
                )
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
