"""
Manager Agent — synthesizes all domain agent insights into a final decision
using LLM-powered conservative / aggressive perspective reasoning.
"""
import json
import asyncio
from typing import Dict, List, Any
from .base_agent import AgentInsight
from .llm_client import llm_json

SYNTHESIS_SYSTEM = """You are the Manager Agent of an AI business decision engine.
You receive structured insights from specialist agents (HR, Sales, Legal, Finance, Marketing,
Supply Chain) and must synthesize them into a balanced executive decision.

Return ONLY valid JSON with no extra text:
{
  "conservative": {
    "recommendation": "short headline recommendation (≤10 words)",
    "reasoning": "2-3 sentence rationale emphasizing risk mitigation and legal compliance"
  },
  "aggressive": {
    "recommendation": "short headline recommendation (≤10 words)",
    "reasoning": "2-3 sentence rationale emphasizing speed, cost-cutting, opportunity capture"
  },
  "final_decision": {
    "verdict": "CLEAR ACTION HEADLINE IN CAPS (≤8 words)",
    "reasoning": "2-3 sentence rationale for the final balanced decision",
    "risk_level": "Low or Medium or High",
    "confidence_score": 78
  }
}
Weigh all agent inputs. Prefer conservative when legal/compliance risks are high.
"""


class ManagerAgent:
    """Orchestrates domain agents and synthesizes the final decision via LLM."""

    def __init__(self, db_service):
        self.db = db_service
        self._agent_registry = self._build_registry()

    def _build_registry(self) -> dict:
        from .hr_agent import HRAgent
        from .sales_agent import SalesAgent
        from .legal_agent import LegalAgent
        from .finance_agent import FinanceAgent
        from .marketing_agent import MarketingAgent
        from .supply_chain_agent import SupplyChainAgent
        return {
            "hr": HRAgent(self.db),
            "sales": SalesAgent(self.db),
            "legal": LegalAgent(self.db),
            "finance": FinanceAgent(self.db),
            "marketing": MarketingAgent(self.db),
            "supply_chain": SupplyChainAgent(self.db),
        }

    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run selected agents in parallel, then synthesize with LLM.
        context must include 'agents' list from intent detector.
        """
        agent_names: List[str] = context.get("agents", list(self._agent_registry.keys()))

        # Run selected agents concurrently
        tasks = {
            name: self._agent_registry[name].run(query, context)
            for name in agent_names
            if name in self._agent_registry
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        agent_insights: List[AgentInsight] = [
            r for r in results if isinstance(r, AgentInsight)
        ]

        if not agent_insights:
            return self._empty_result(query)

        synthesis = await self._synthesize_with_llm(agent_insights, query)

        return {
            "agent_insights": [i.model_dump() for i in agent_insights],
            "conservative_view": synthesis["conservative"],
            "aggressive_view": synthesis["aggressive"],
            "final_decision": synthesis["final_decision"],
        }

    async def _synthesize_with_llm(
        self, insights: List[AgentInsight], query: str
    ) -> Dict[str, Any]:
        summary = "\n\n".join(
            f"[{i.agent_name} Agent]\n"
            f"Findings: {'; '.join(i.findings[:3])}\n"
            f"Risks: {'; '.join(i.risks[:2])}\n"
            f"Recommendation: {i.recommendation}\n"
            f"Confidence: {i.confidence:.0%}"
            for i in insights
        )
        user_msg = f"Query: {query}\n\nAgent Insights:\n{summary}"

        try:
            result = await llm_json(SYNTHESIS_SYSTEM, user_msg, temperature=0.3)
            result.setdefault("conservative", {
                "recommendation": "Proceed cautiously",
                "reasoning": "Multiple risks identified. Take a phased approach."
            })
            result.setdefault("aggressive", {
                "recommendation": "Act decisively",
                "reasoning": "Delay carries opportunity cost. Move now with safeguards."
            })
            fd = result.setdefault("final_decision", {})
            fd.setdefault("verdict", "PROCEED WITH CAUTION")
            fd.setdefault("reasoning", "Balanced analysis suggests a measured approach.")
            fd.setdefault("risk_level", "Medium")
            avg_conf = sum(i.confidence for i in insights) / len(insights)
            fd.setdefault("confidence_score", round(avg_conf * 100))
            return result
        except Exception:
            return self._rule_based_synthesis(insights)

    def _rule_based_synthesis(self, insights: List[AgentInsight]) -> Dict[str, Any]:
        avg_conf = sum(i.confidence for i in insights) / len(insights)
        all_risks = [r for i in insights for r in i.risks]
        all_recs = [i.recommendation for i in insights]
        return {
            "conservative": {
                "recommendation": "Proceed cautiously with documented safeguards",
                "reasoning": (
                    "Multiple agent risks flagged. "
                    "Conservative approach protects against legal and financial exposure. "
                    "Implement protective measures before acting."
                ),
            },
            "aggressive": {
                "recommendation": "Act decisively to capture opportunity",
                "reasoning": (
                    "Agent analysis supports action. "
                    "Delay creates opportunity cost. "
                    "Accept calculated risk for faster outcome."
                ),
            },
            "final_decision": {
                "verdict": "PROCEED WITH STRUCTURED PLAN",
                "reasoning": (
                    "Agent consensus points toward action with safeguards. "
                    f"Key risks: {'; '.join(all_risks[:2]) if all_risks else 'none critical'}. "
                    "Execute with clear milestones and exit criteria."
                ),
                "risk_level": "High" if len(all_risks) > 4 else "Medium",
                "confidence_score": round(avg_conf * 100),
            },
        }

    def _empty_result(self, query: str) -> Dict[str, Any]:
        return {
            "agent_insights": [],
            "conservative_view": {
                "recommendation": "Gather more information",
                "reasoning": "Insufficient data to make a recommendation.",
            },
            "aggressive_view": {
                "recommendation": "Defer decision",
                "reasoning": "No agent data available to support action.",
            },
            "final_decision": {
                "verdict": "INSUFFICIENT DATA",
                "reasoning": "No agent insights were returned. Please refine your query.",
                "risk_level": "High",
                "confidence_score": 0,
            },
        }
