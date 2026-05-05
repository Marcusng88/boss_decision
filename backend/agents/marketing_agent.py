"""
Marketing Agent - Evaluates campaign performance, ROI, market positioning.
- If a document is uploaded: use it as primary evidence.
- If no document: fetch from Supabase marketing records.
"""
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentInsight
from .llm_client import llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a marketing performance and campaign strategy analyst for an AI business decision engine.
Analyze the marketing data provided and return ONLY valid JSON:
{
  "findings": ["finding1", "finding2", "finding3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "single actionable marketing recommendation",
  "confidence": 0.80,
  "data_summary": "brief 3-5 word summary",
  "metric_value": "key metric e.g. 'RM 12k spend, 240 conversions'",
  "trend": "up or down or flat"
}
Focus on: campaign ROI, spend efficiency, channel mix, audience reach, conversion rates, and market positioning.
"""


class MarketingAgent(BaseAgent):

    def __init__(self, db_service, llm=None, company_db: Optional[Any] = None):
        super().__init__(db_service, llm)
        self._company_db = company_db

    @staticmethod
    def _is_heuristic_summary(summary: str) -> bool:
        """Return True if document summary is a heuristic stub with no real content."""
        if not summary:
            return True
        markers = ["heuristic classification", "llm parse failed", "no llm", "classification applied", "none type"]
        lower = summary.lower()
        return any(m in lower for m in markers)

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []
        doc_summary = context.get("document_summary", "")
        has_real_document = bool(doc_summary) and not self._is_heuristic_summary(doc_summary)

        if has_real_document:
            # Good document — use as primary evidence, skip DB
            evidence.append({
                "source": "uploaded_document",
                "summary": doc_summary,
                "department": context.get("document_department", "Marketing"),
                "tags": context.get("document_tags", []),
            })
            return evidence

        # No document OR heuristic-only summary — fetch from Supabase
        if doc_summary and not has_real_document:
            logger.info("MarketingAgent: document summary is heuristic-only, falling back to Supabase")

        db = self._company_db or self.db
        try:
            rows = await db.fetch_marketing_records(limit=40)
            for row in rows:
                evidence.append({
                    "source": "supabase_marketing_record",
                    "record_id": row.get("marketing_id"),
                    "data": row,
                })
            if rows:
                logger.info("MarketingAgent: loaded %d marketing records from Supabase", len(rows))
            else:
                logger.info("MarketingAgent: no marketing records found in Supabase")
        except Exception as exc:
            logger.warning("MarketingAgent: failed to load marketing records: %s", exc)

        return evidence

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        records = [e["data"] for e in evidence if e.get("source") == "supabase_marketing_record" and e.get("data")]
        doc_summaries = [e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")]

        findings: List[str] = []
        risks: List[str] = []

        if doc_summaries:
            findings.append("Marketing document reviewed for campaign context")
            combined = " ".join(doc_summaries).lower()
            if "roi" in combined or "return" in combined:
                findings.append("ROI or return metrics mentioned in document")
            if "spend" in combined or "budget" in combined:
                findings.append("Budget or spend data present in document")
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=findings,
                risks=["Validate document data against live campaign records"],
                recommendation="Review campaign ROI from uploaded report and align with current spend allocation",
                confidence=0.65,
                evidence_used=evidence,
                data_summary="Document-based review",
            )

        if not records:
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=["No marketing records found in the database"],
                risks=["Campaign performance cannot be assessed without data"],
                recommendation="Establish marketing tracking records before evaluating campaigns",
                confidence=0.0,
                evidence_used=evidence,
            )

        total_spend = sum(r.get("amount", 0) for r in records if r.get("metric_name") == "spend")
        total_conversions = sum(r.get("amount", 0) for r in records if r.get("metric_name") == "conversions")
        channels = list({r.get("channel") for r in records if r.get("channel")})

        findings.append(f"Marketing records reviewed: {len(records)} entries across {len(channels)} channel(s)")
        if total_spend:
            findings.append(f"Total campaign spend tracked: RM {total_spend:,.0f}")
        if total_conversions:
            findings.append(f"Total conversions tracked: {total_conversions:,.0f}")
        if channels:
            findings.append(f"Active channels: {', '.join(channels[:5])}")

        metric_value = ""
        if total_spend and total_conversions and total_spend > 0:
            cpa = total_spend / total_conversions
            findings.append(f"Estimated cost per acquisition: RM {cpa:,.2f}")
            metric_value = f"RM {total_spend:,.0f} spend, {total_conversions:,.0f} conversions"
            if cpa > 500:
                risks.append("High cost per acquisition — campaign efficiency needs optimization")

        return AgentInsight(
            agent_name="Marketing", emoji="📣",
            findings=findings,
            risks=risks or ["Monitor channel mix and ROI per campaign period"],
            recommendation="Review campaign ROI and optimize spend allocation across top-performing channels",
            confidence=0.75,
            evidence_used=evidence,
            data_summary=f"{len(records)} records, {len(channels)} channels",
            metric_value=metric_value,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        fallback = self._rule_based_analyze(evidence, query)

        if not evidence:
            return fallback

        evidence_parts: List[str] = []
        for e in evidence:
            if e.get("source") == "uploaded_document":
                evidence_parts.append(f"Document: {e.get('summary', '')}")
            elif e.get("source") == "supabase_marketing_record" and e.get("data"):
                d = e["data"]
                evidence_parts.append(
                    f"Campaign: {d.get('campaign_name')} | channel: {d.get('channel')} | "
                    f"metric: {d.get('metric_name')} = {d.get('amount')} | period: {d.get('period')}"
                )
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No marketing evidence retrieved."

        user_msg = f"Query: {query}\n\nMarketing Data:\n{evidence_summary[:6000]}"
        try:
            result = await llm_json(SYSTEM_PROMPT, user_msg)
            return AgentInsight(
                agent_name="Marketing", emoji="📣",
                findings=result.get("findings", []),
                risks=result.get("risks", []),
                recommendation=result.get("recommendation", "Review campaign strategy"),
                confidence=float(result.get("confidence", 0.75)),
                evidence_used=evidence,
                data_summary=result.get("data_summary", "Marketing analysis"),
                metric_value=result.get("metric_value", ""),
                trend=result.get("trend", "flat"),
            )
        except Exception:
            return fallback
