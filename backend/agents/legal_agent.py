"""
Legal Agent - Reviews compliance, due process, and policy risk.
"""
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight


class LegalAgent(BaseAgent):
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        try:
            docs = await self.db.get_department_documents("legal")
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
                agent_name="Legal",
                findings=["No legal or HR policy documents found in the knowledge base"],
                risks=["Compliance position unclear without policy evidence"],
                recommendation="Obtain and review applicable employment law and internal HR policy before taking action",
                confidence=0.35,
                evidence_used=[],
            )

        summaries = [str(item.get("summary", "")).strip() for item in evidence if item.get("summary")]
        combined = " ".join(summaries).lower()

        findings.append("Legal review completed against available policy evidence")

        if "pip" in combined or "due process" in combined:
            findings.append("Due process and PIP sequencing are material to legal compliance")
        if "warning" in combined:
            findings.append("Warning history is a key factor in substantiating dismissal")
        if "unfair dismissal" in combined:
            findings.append("Document explicitly references unfair dismissal risk — must follow formal process")

        if "termination" in query.lower() or "fire" in query.lower() or "dismissal" in combined:
            risks.append("Termination without completed PIP and documented due process creates unfair dismissal liability")
        if "high" in combined and "risk" in combined:
            risks.append("Policy notes indicate elevated legal compliance risk")
        if "pip" in combined and "not initiated" in combined:
            risks.append("PIP has not been started — premature termination is legally indefensible")

        recommendation = "Proceed only after completing the due-process checklist: formal warnings → PIP initiation → PIP outcome assessment → termination if warranted"
        if not risks:
            recommendation = "No immediate legal blockers found; proceed with documented controls and contemporaneous records"

        return AgentInsight(
            agent_name="Legal",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.72,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze legal compliance evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        evidence_parts: List[str] = []
        for e in evidence:
            summary = e.get("summary", "")
            if summary:
                evidence_parts.append(f"Policy/document summary: {summary}")
        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No legal documents found."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="employment law and HR compliance specialist",
            domain_focus=(
                "Legal due-process requirements for employee termination, unfair dismissal risk, "
                "PIP (Performance Improvement Plan) sequencing mandated by HR policy, "
                "and the employer's evidentiary burden to justify termination."
            ),
            fallback_insight=fallback,
        )
