"""
Manager Agent - Orchestrates domain agents and synthesizes final decision.
Uses the same AsyncOpenAI/Zhipu path as domain agents (no httpx lock, no 504 risk).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import AgentInsight
from .llm_client import llm_json, llm_text

logger = logging.getLogger(__name__)


class ManagerAgent:
    """Manager orchestrator with dynamic LLM routing and synthesis."""

    SUPPORTED_DEPARTMENTS = ["hr", "sales", "legal", "finance", "marketing", "supply_chain", "operations"]

    def __init__(self, agents: List[Any], llm=None):
        self.agents = agents
        self.llm = llm
        self.agent_registry = self._build_agent_registry(agents)

    def _build_agent_registry(self, agents: List[Any]) -> Dict[str, Any]:
        registry: Dict[str, Any] = {}
        for agent in agents:
            canonical = self._canonical(getattr(agent, "agent_name", agent.__class__.__name__))
            registry[canonical] = agent
        return registry

    @staticmethod
    def _canonical(raw: str) -> str:
        lowered = (raw or "").strip().lower().replace(" ", "_").replace("-", "_").replace("_agent", "agent")
        aliases = {
            "hragent": "hr", "hr": "hr",
            "salesagent": "sales", "sales": "sales",
            "legalagent": "legal", "legal": "legal",
            "financeagent": "finance", "finance": "finance",
            "marketingagent": "marketing", "marketing": "marketing",
            "supplychainagent": "supply_chain", "supplychain": "supply_chain", "supply_chain": "supply_chain",
            "operationsagent": "operations", "operations": "operations", "operation": "operations",
        }
        return aliases.get(lowered, lowered)

    def _agents_from_text(self, text: str) -> List[str]:
        lowered = (text or "").lower()
        found = [d for d in self.SUPPORTED_DEPARTMENTS if d.replace("_", " ") in lowered or d in lowered]
        return list(dict.fromkeys(found))

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    async def route_agents(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        allowed = ", ".join(self.SUPPORTED_DEPARTMENTS)
        doc_dept = context.get("document_department")
        doc_summary = context.get("document_summary")

        system = "You are a business manager router. Return strict JSON only."
        user = f"""
Pick the MINIMUM departments required to answer this business query.

Allowed departments: [{allowed}]
User query: {query}
Document department (if any): {doc_dept}
Document summary (if any): {doc_summary}
Target type: {context.get('target_type')}
Target id: {context.get('target_id')}

Output JSON:
{{
  "selected_agents": ["hr", "legal"],
  "reasoning": "short explanation",
  "confidence": 0.85
}}
""".strip()

        try:
            parsed = await llm_json(system, user, temperature=0.1, max_tokens=300)
            selected = [
                self._canonical(n) for n in parsed.get("selected_agents", [])
                if self._canonical(n) in self.SUPPORTED_DEPARTMENTS
            ]
            selected = list(dict.fromkeys(selected))
            if selected:
                return {
                    "selected_agents": selected,
                    "reasoning": parsed.get("reasoning", "LLM routing completed"),
                    "confidence": float(parsed.get("confidence", 0.8)),
                    "route_source": "llm",
                }
        except Exception as exc:
            logger.warning("Manager routing JSON call failed: %s", exc)

        # Text-mode fallback
        try:
            text = await llm_text(
                "You are a business manager router.",
                f"List the department(s) from [{allowed}] needed to answer: {query}",
                temperature=0.1,
                max_tokens=120,
            )
            selected = [s for s in self._agents_from_text(text) if s in self.SUPPORTED_DEPARTMENTS]
            if selected:
                return {
                    "selected_agents": selected,
                    "reasoning": text[:200],
                    "confidence": 0.6,
                    "route_source": "llm_text",
                }
        except Exception as exc:
            logger.warning("Manager routing text fallback failed: %s", exc)

        # Structural fallback — use document department or target type
        selected = []
        if isinstance(doc_dept, str):
            c = self._canonical(doc_dept)
            if c in self.SUPPORTED_DEPARTMENTS:
                selected.append(c)
        if not selected and (context.get("target_type") or "").lower() == "employee":
            selected = ["hr", "legal"]
        if not selected:
            selected = ["hr", "sales"]
            logger.warning("Manager routing fully degraded — defaulted to %s", selected)

        return {
            "selected_agents": selected,
            "reasoning": "Fallback routing — LLM unavailable.",
            "confidence": 0.4,
            "route_source": "fallback",
        }

    # ------------------------------------------------------------------
    # Sub-agent LLM reply (when agent not in registry)
    # ------------------------------------------------------------------

    async def _llm_subagent_reply(self, department: str, query: str, context: Dict[str, Any]) -> AgentInsight:
        label = department.replace("_", " ").title()
        system = "You are a specialized business sub-agent. Return strict JSON only."
        user = f"""
Department role: {label}
Business query: {query}
Context: {json.dumps({k: v for k, v in context.items() if k != 'document_summary'}, default=str)}

Return JSON:
{{
  "findings": ["point 1", "point 2"],
  "risks": ["risk 1"],
  "recommendation": "single-line recommendation",
  "confidence": 0.7
}}
""".strip()
        try:
            parsed = await llm_json(system, user, temperature=0.3, max_tokens=500)
            return AgentInsight(
                agent_name=label,
                findings=[str(f) for f in (parsed.get("findings") or [])][:4],
                risks=[str(r) for r in (parsed.get("risks") or [])][:4],
                recommendation=str(parsed.get("recommendation") or f"Proceed with {label.lower()} guardrails."),
                confidence=max(0.0, min(float(parsed.get("confidence", 0.7)), 1.0)),
                evidence_used=[{"source": "zhipu_llm", "detail": f"dynamic_{department}"}],
            )
        except Exception as exc:
            logger.warning("LLM sub-agent reply failed for %s: %s", department, exc)
            return AgentInsight(
                agent_name=label,
                findings=[f"{label} analysis completed with reduced confidence."],
                risks=[f"LLM-enhanced {label.lower()} analysis unavailable — using fallback."],
                recommendation=f"Consult {label} team directly for this decision.",
                confidence=0.3,
                evidence_used=[{"source": "fallback", "detail": f"{department}_degraded"}],
            )

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    async def orchestrate_dynamic(
        self,
        query: str,
        context: Dict[str, Any],
        forced_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if forced_agents:
            selected_names = [self._canonical(n) for n in forced_agents]
            routing = {
                "selected_agents": selected_names,
                "reasoning": "User manually selected specific agents.",
                "confidence": 1.0,
                "route_source": "manual",
            }
        else:
            logger.info("[Manager] Routing query: %s...", query[:80])
            routing = await self.route_agents(query, context)
            selected_names = routing.get("selected_agents", [])
            logger.info("[Manager] Selected agents: %s", selected_names)

        force_simple_llm = bool(context.get("force_simple_llm_subagents", False))
        agent_insights: List[AgentInsight] = []

        for name in selected_names:
            logger.info("[Manager] Executing agent: %s", name)
            if force_simple_llm:
                agent_insights.append(await self._llm_subagent_reply(name, query, context))
                continue
            agent = self.agent_registry.get(name)
            if agent is None:
                logger.info("[Manager] Agent '%s' not in registry — using LLM reply.", name)
                agent_insights.append(await self._llm_subagent_reply(name, query, context))
                continue
            try:
                insight = await agent.run(query, context)
            except Exception as exc:
                logger.error("[Manager] Agent '%s' failed: %s", name, exc)
                insight = AgentInsight(
                    agent_name=getattr(agent, "agent_name", name),
                    findings=["Agent execution failed"],
                    risks=[f"{name} unavailable during analysis"],
                    recommendation="Proceed with degraded confidence and gather more evidence",
                    confidence=0.2,
                    evidence_used=[{"source": "error", "detail": str(exc)}],
                )
            agent_insights.append(insight)

        logger.info("[Manager] Synthesizing final decision...")
        conservative_view = await self._generate_conservative_view(agent_insights, query)
        aggressive_view = await self._generate_aggressive_view(agent_insights, query)
        final_decision = await self._synthesize_decision(
            agent_insights, conservative_view, aggressive_view, persona="conservative", query=query
        )
        if len(agent_insights) > 1:
            final_decision["tldr"] = self._build_tldr(agent_insights, final_decision)

        return {
            "routing": routing,
            "agent_insights": [i.model_dump() for i in agent_insights],
            "conservative_view": conservative_view,
            "aggressive_view": aggressive_view,
            "final_decision": final_decision,
        }

    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy full-orchestration path — runs every agent."""
        agent_insights = []
        for agent in self.agents:
            try:
                insight = await agent.run(query, context)
            except Exception as exc:
                insight = AgentInsight(
                    agent_name=getattr(agent, "agent_name", agent.__class__.__name__),
                    findings=["Agent execution failed"],
                    risks=[f"{agent.__class__.__name__} unavailable"],
                    recommendation="Proceed with degraded confidence",
                    confidence=0.2,
                    evidence_used=[{"source": "error", "detail": str(exc)}],
                )
            agent_insights.append(insight)

        conservative_view = await self._generate_conservative_view(agent_insights, query)
        aggressive_view = await self._generate_aggressive_view(agent_insights, query)
        final_decision = await self._synthesize_decision(
            agent_insights, conservative_view, aggressive_view, persona="conservative", query=query
        )
        return {
            "agent_insights": [i.model_dump() for i in agent_insights],
            "conservative_view": conservative_view,
            "aggressive_view": aggressive_view,
            "final_decision": final_decision,
        }

    # ------------------------------------------------------------------
    # Synthesis helpers
    # ------------------------------------------------------------------

    def _build_tldr(self, insights: List[AgentInsight], final_decision: Dict[str, Any]) -> str:
        depts = ", ".join(i.agent_name for i in insights)
        return (
            f"Departments consulted: {depts}. "
            f"Recommendation: {final_decision.get('recommendation', '')}. "
            f"Risk: {final_decision.get('risk_level', 'Medium')}. "
            f"Confidence: {final_decision.get('confidence_score', 0)}%."
        )

    async def _generate_conservative_view(self, insights: List[AgentInsight], query: str) -> str:
        risks = [r for i in insights for r in i.risks]
        findings = [f for i in insights for f in i.findings]
        risk_summary = "; ".join(risks[:3]) if risks else "No specific risks identified."
        finding_summary = "; ".join(findings[:3]) if findings else "No specific findings."
        static_fallback = (
            f"Key risks: {risk_summary}. "
            f"Findings: {finding_summary}. "
            "Recommend controlled steps, thorough documentation, and measurable checkpoints before proceeding."
        )
        system = "You are a conservative business strategist. Give a concise, risk-aware perspective in 2-3 sentences. Plain text only."
        user = f"Query: {query}\nFindings: {findings[:6]}\nRisks: {risks[:6]}\nWrite a conservative perspective."
        try:
            text = await llm_text(system, user, temperature=0.3, max_tokens=200)
            return text or static_fallback
        except Exception:
            return static_fallback

    async def _generate_aggressive_view(self, insights: List[AgentInsight], query: str) -> str:
        findings = [f for i in insights for f in i.findings]
        recs = [i.recommendation for i in insights if i.recommendation]
        finding_summary = "; ".join(findings[:3]) if findings else "No specific findings."
        rec_summary = "; ".join(recs[:2]) if recs else "Proceed decisively."
        static_fallback = (
            f"Key findings: {finding_summary}. "
            f"Opportunities: {rec_summary}. "
            "Recommend decisive execution with clear milestones and risk controls running in parallel."
        )
        system = "You are a growth-oriented business strategist. Give a concise, opportunity-focused perspective in 2-3 sentences. Plain text only."
        user = f"Query: {query}\nFindings: {findings[:6]}\nWrite an aggressive perspective."
        try:
            text = await llm_text(system, user, temperature=0.4, max_tokens=200)
            return text or static_fallback
        except Exception:
            return static_fallback

    async def _synthesize_decision(
        self,
        insights: List[AgentInsight],
        conservative_view: str,
        aggressive_view: str,
        persona: str = "conservative",
        query: str = "",
    ) -> Dict[str, Any]:
        avg_confidence = sum(i.confidence for i in insights) / len(insights) if insights else 0.0

        agent_summary_lines = [
            f"[{i.agent_name}] Findings: {i.findings[:2]} | Risks: {i.risks[:2]} | Rec: {i.recommendation}"
            for i in insights
        ]
        agent_summary = "\n".join(agent_summary_lines) or "No agent insights available."

        system = "You are a senior business manager synthesizing multi-agent analysis. Return strict JSON only."
        user = f"""
Business query: {query}

Agent analyses:
{agent_summary}

Conservative view: {conservative_view}
Aggressive view: {aggressive_view}
Manager persona: {persona}

Return JSON:
{{
  "recommendation": "clear actionable final recommendation",
  "risk_level": "Low | Medium | High",
  "rationale": "2-4 sentence explanation referencing agent findings",
  "confidence": 0.0
}}
""".strip()

        try:
            parsed = await llm_json(system, user, temperature=0.3, max_tokens=600)
            risk_level = parsed.get("risk_level", "Medium")
            if risk_level not in ("Low", "Medium", "High"):
                risk_level = "Medium"
            llm_conf = max(0.0, min(float(parsed.get("confidence", avg_confidence)), 1.0))
            full_rationale = (
                f"Multi-agent analysis:\n{agent_summary}\n\n"
                f"**Manager Decision ({persona.title()}):** {parsed.get('rationale', '')}\n\n"
                f"{conservative_view}\n\n{aggressive_view}"
            )
            return {
                "recommendation": parsed.get("recommendation", "Proceed with caution — consult department leads."),
                "risk_level": risk_level,
                "confidence_score": round(llm_conf * 100, 2),
                "rationale": full_rationale,
                "manager_persona": persona,
            }
        except Exception as exc:
            logger.warning("Decision synthesis LLM call failed: %s", exc)

        # Structural fallback
        risk_level = "High" if avg_confidence < 0.4 else "Medium" if avg_confidence < 0.65 else "Low"
        recs = [i.recommendation for i in insights if i.recommendation]
        rationale = f"Multi-agent analysis:\n{agent_summary}\n\n**Manager Decision ({persona.title()}):** {conservative_view}"
        return {
            "recommendation": recs[0] if recs else "Proceed with phased approach — validate before full commitment.",
            "risk_level": risk_level,
            "confidence_score": round(avg_confidence * 100, 2),
            "rationale": rationale,
            "manager_persona": persona,
        }
