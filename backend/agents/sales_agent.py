"""
Sales Agent - Analyzes revenue contribution, deal pipeline, sales performance.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class SalesAgent(BaseAgent):
    """
    Sales domain specialist agent.
    Focuses on: revenue contribution, deals closed, pipeline health, quota attainment.
    """

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve sales-related evidence.

        For employee decisions:
        - Sales records (revenue, deals closed)
        - Pipeline status
        - Deal win/loss analysis
        """
        evidence = []

        # Injected document context
        if context.get("document_summary"):
            evidence.append(
                {
                    "source": "uploaded_document",
                    "path": context.get("document_path", "(runtime_upload)"),
                    "department": context.get("document_department", "Sales"),
                    "summary": context.get("document_summary"),
                    "tags": context.get("document_tags", []),
                }
            )

        # If target is an employee, get their sales records
        if context.get("target_type") == "employee" and context.get("target_id"):
            employee_id = context["target_id"]
            sales_records = await self.db.get_employee_sales_records(employee_id)
            evidence.extend(
                [
                    {
                        "source": "sales_record",
                        "type": "deal",
                        "record_id": record["sales_id"],
                        "data": record,
                    }
                    for record in sales_records
                ]
            )

        return evidence

    # ------------------------------------------------------------------
    # Rule-based core analysis
    # ------------------------------------------------------------------

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Produce structured insights from pure rule-based logic."""
        sales_records = [e["data"] for e in evidence if e.get("source") == "sales_record"]
        doc_summaries = [
            e["summary"] for e in evidence if e.get("source") == "uploaded_document" and e.get("summary")
        ]

        findings: List[str] = []
        risks: List[str] = []

        # Document context signals
        if doc_summaries:
            combined_doc = " ".join(doc_summaries).lower()
            findings.append("Sales-related document reviewed for performance context")
            if "revenue" in combined_doc or "sales" in combined_doc:
                findings.append("Revenue or sales performance mentioned in uploaded document")

        if not sales_records:
            recommendation = (
                "No sales database records found; assessment based on uploaded document context only"
                if doc_summaries
                else "Insufficient data for sales assessment — retrieve sales records before making decisions"
            )
            return AgentInsight(
                agent_name="Sales",
                findings=findings or ["No sales records found in the database"],
                risks=risks or ["Cannot assess sales performance without data"],
                recommendation=recommendation,
                confidence=0.2 if doc_summaries else 0.0,
                evidence_used=evidence,
            )

        closed_deals = [r for r in sales_records if r.get("deal_stage") == "closed"]
        pipeline_deals = [r for r in sales_records if r.get("deal_stage") == "pipeline"]
        lost_deals = [r for r in sales_records if r.get("deal_stage") == "lost"]

        total_revenue = sum(r.get("amount", 0) for r in closed_deals)
        deal_count = len(closed_deals)

        findings.append(f"Total closed deals: {deal_count}")
        findings.append(f"Total revenue contribution: RM {total_revenue:,.2f}")

        if deal_count > 0:
            avg_deal_size = total_revenue / deal_count
            findings.append(f"Average deal size: RM {avg_deal_size:,.2f}")

        period_revenue: dict = {}
        for record in closed_deals:
            period = record.get("period", "unknown")
            period_revenue[period] = period_revenue.get(period, 0) + record.get("amount", 0)

        if period_revenue:
            findings.append(f"Revenue by period: {period_revenue}")
            periods = sorted(period_revenue.keys())
            if len(periods) >= 2:
                latest = period_revenue[periods[-1]]
                previous = period_revenue[periods[-2]]
                if previous > 0 and latest < previous * 0.5:
                    risks.append("Revenue declined >50% quarter-over-quarter — significant performance deterioration")
                    findings.append("Sales performance trending down sharply")

        findings.append(f"Active pipeline: {len(pipeline_deals)} deals | Lost deals: {len(lost_deals)}")
        if len(pipeline_deals) < 2:
            risks.append("Pipeline health is weak — insufficient active opportunities")

        if total_revenue < 50000 and deal_count < 3:
            recommendation = "Sales performance is below team standards; revenue contribution is insufficient"
            if len(pipeline_deals) < 2:
                recommendation += ". Weak pipeline indicates a systemic performance issue"
        elif total_revenue < 100000:
            recommendation = "Sales performance is acceptable but below top-performer benchmarks"
        else:
            recommendation = "Sales performance is meeting or exceeding expectations"

        return AgentInsight(
            agent_name="Sales",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.80,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze sales evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        evidence_parts: List[str] = []
        for e in evidence:
            if e.get("source") == "uploaded_document":
                evidence_parts.append(f"Document summary: {e.get('summary', '')}")
            elif e.get("source") == "sales_record":
                data = e.get("data", {})
                evidence_parts.append(
                    f"Deal — stage: {data.get('deal_stage')}, amount: {data.get('amount')}, period: {data.get('period')}"
                )
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No sales evidence retrieved."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="sales performance analyst",
            domain_focus=(
                "Revenue contribution, deal pipeline health, quota attainment, "
                "closed/lost/pipeline deal ratios, and quarter-over-quarter trend analysis."
            ),
            fallback_insight=fallback,
        )
