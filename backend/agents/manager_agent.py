"""
Manager Agent - Orchestrates domain agents and synthesizes final decision.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from .base_agent import AgentInsight
from services.llm_client import UnifiedLLMClient


class ManagerAgent:
    """Manager orchestrator with dynamic LLM routing and TLDR synthesis."""

    def __init__(self, agents: List[Any], llm=None):
        self.agents = agents
        self.llm = llm
        self.agent_registry = self._build_agent_registry(agents)
        self.router_client = UnifiedLLMClient.from_settings()
        self.router_init_error = None if self.router_client else "API key not configured"
        self.supported_departments = [
            "hr",
            "sales",
            "legal",
            "finance",
            "marketing",
            "supply_chain",
            "operations",
        ]

    def _build_agent_registry(self, agents: List[Any]) -> Dict[str, Any]:
        registry: Dict[str, Any] = {}
        for agent in agents:
            canonical = self._canonical_agent_name(getattr(agent, "agent_name", agent.__class__.__name__))
            registry[canonical] = agent
        return registry

    def _canonical_agent_name(self, raw_name: str) -> str:
        lowered = (raw_name or "").strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "hragent": "hr",
            "hr": "hr",
            "salesagent": "sales",
            "sales": "sales",
            "legalagent": "legal",
            "legal": "legal",
            "financeagent": "finance",
            "finance": "finance",
            "marketingagent": "marketing",
            "marketing": "marketing",
            "supplychainagent": "supply_chain",
            "supplychain": "supply_chain",
            "supply_chain": "supply_chain",
            "operationsagent": "operations",
            "operations": "operations",
            "operation": "operations",
        }
        lowered = lowered.replace("_agent", "agent")
        return aliases.get(lowered, lowered)

    @staticmethod
    def _extract_json_object(raw: str) -> Dict[str, Any] | None:
        text = (raw or "").strip()
        if not text:
            return None

        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except Exception:
                return None

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None

        return None

    def _derive_agents_from_text(self, text: str) -> List[str]:
        lowered = (text or "").lower()
        candidates = {
            "hr": ["hr", "human resources", "people ops"],
            "legal": ["legal", "law", "compliance", "labor"],
            "sales": ["sales", "pipeline", "revenue"],
            "marketing": ["marketing", "campaign", "brand"],
            "finance": ["finance", "budget", "cost", "cash"],
            "supply_chain": ["supply", "logistics", "inventory", "operations"],
            "operations": ["operations", "process", "fulfillment"],
        }
        selected: List[str] = []
        for dept, hints in candidates.items():
            if any(h in lowered for h in hints):
                selected.append(dept)
        return list(dict.fromkeys(selected))

    async def route_agents(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select target departments dynamically with LLM."""
        doc_summary = context.get("document_summary")
        doc_department = context.get("document_department")
        allowed = ", ".join(self.supported_departments)

        llm_error = None
        if self.router_client is not None:
            system_prompt = "You are a business manager router. Return strict JSON only."
            user_prompt = f"""
Pick the MINIMUM departments required to answer this business query.

Allowed departments: [{allowed}]
User query: {query}
Optional extracted document department: {doc_department}
Optional extracted document summary: {doc_summary}
Optional target_type: {context.get('target_type')}
Optional target_id: {context.get('target_id')}

Output JSON schema:
{{
  "selected_agents": ["hr", "legal"],
  "reasoning": "short explanation",
  "confidence": 0.0
}}
""".strip()
            try:
                parsed, model_used = await self.router_client.acomplete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,
                    max_tokens=500,
                )
                selected_raw = parsed.get("selected_agents", [])
                selected = [
                    self._canonical_agent_name(name)
                    for name in selected_raw
                    if self._canonical_agent_name(name) in self.supported_departments
                ]
                selected = list(dict.fromkeys(selected))
                if selected:
                    return {
                        "selected_agents": selected,
                        "reasoning": parsed.get("reasoning", "LLM routing completed"),
                        "confidence": float(parsed.get("confidence", 0.7)),
                        "route_source": "llm",
                        "model_used": model_used,
                    }
                llm_error = "LLM returned no valid selected_agents"
            except Exception as exc:
                llm_error = str(exc)

            # Text-mode fallback for providers that occasionally return non-JSON/empty output.
            try:
                text_output = await self.router_client.acomplete_text(
                    system_prompt="You are a business manager router.",
                    user_prompt=(
                        f"Choose minimum departments from [{allowed}] for this query: {query}. "
                        "If uncertain, mention 1-2 departments and why in one sentence."
                    ),
                    temperature=0.1,
                    max_tokens=180,
                )
                parsed = self._extract_json_object(text_output.text)
                if parsed:
                    selected = [
                        self._canonical_agent_name(name)
                        for name in parsed.get("selected_agents", [])
                        if self._canonical_agent_name(name) in self.supported_departments
                    ]
                else:
                    selected = [
                        s for s in self._derive_agents_from_text(text_output.text)
                        if s in self.supported_departments
                    ]

                if selected:
                    return {
                        "selected_agents": selected,
                        "reasoning": (text_output.text or "LLM text routing fallback used")[:240],
                        "confidence": 0.62,
                        "route_source": "llm",
                        "model_used": text_output.model,
                    }
            except Exception as exc:
                llm_error = f"{llm_error} | text_fallback: {str(exc)}" if llm_error else str(exc)

        selected = []
        if isinstance(doc_department, str):
            canonical = self._canonical_agent_name(doc_department)
            if canonical in self.supported_departments:
                selected.append(canonical)

        target_type = (context.get("target_type") or "").strip().lower()
        if not selected and target_type == "employee":
            selected = ["hr", "legal"]

        if not selected:
            selected = ["hr", "sales"]

        return {
            "selected_agents": selected,
            "reasoning": "Fallback routing used because LLM routing was unavailable.",
            "confidence": 0.45,
            "route_source": "fallback",
            "route_error": llm_error or self.router_init_error,
        }

    async def _llm_subagent_reply(self, department: str, query: str, context: Dict[str, Any]) -> AgentInsight:
        """Generate a lightweight simulated sub-agent insight via LLM."""
        label = department.replace("_", " ").title()

        if self.router_client is None:
            return AgentInsight(
                agent_name=label,
                findings=[f"{label} agent selected but LLM client is unavailable."],
                risks=["Sub-agent analysis is degraded due to missing LLM configuration."],
                recommendation=f"Configure an API key to enable dynamic {label} analysis.",
                confidence=0.3,
                evidence_used=[{"source": "manager_router", "detail": "llm_not_configured"}],
            )

        system_prompt = (
            "You are a specialized business sub-agent. Return strict JSON only with concise, practical analysis."
        )
        user_prompt = f"""
Department role: {label}
Business query: {query}
Context JSON: {context}

Return JSON only:
{{
  "findings": ["point 1", "point 2"],
  "risks": ["risk 1", "risk 2"],
  "recommendation": "single-line recommendation",
  "confidence": 0.0
}}
""".strip()

        try:
            parsed, _ = await self.router_client.acomplete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=800,
            )
            findings = parsed.get("findings") or [f"{label} analysis completed."]
            risks = parsed.get("risks") or [f"No major {label.lower()} risk flagged."]
            recommendation = parsed.get("recommendation") or f"Proceed with {label.lower()} guardrails."
            confidence = float(parsed.get("confidence", 0.7))

            return AgentInsight(
                agent_name=label,
                findings=[str(x) for x in findings][:4],
                risks=[str(x) for x in risks][:4],
                recommendation=str(recommendation),
                confidence=max(0.0, min(confidence, 1.0)),
                evidence_used=[
                    {
                        "source": "unified_llm",
                        "detail": f"dynamic_sub_agent_{department}",
                    }
                ],
            )
        except Exception as exc:
            try:
                text_output = await self.router_client.acomplete_text(
                    system_prompt=f"You are the {label} business sub-agent.",
                    user_prompt=(
                        f"Query: {query}\n"
                        f"Context: {context}\n"
                        "List exactly 2 findings, 1 key risk, and 1 recommendation. "
                        "Use plain numbered lines: '1. ...', '2. ...', 'Risk: ...', 'Recommendation: ...'"
                    ),
                    temperature=0.25,
                    max_tokens=400,
                )
                body = (text_output.text or "").strip()
                if body:
                    import re as _re
                    # Parse structured numbered/labelled lines robustly.
                    findings: list[str] = []
                    risk_line = ""
                    rec_line = ""
                    for raw_line in body.splitlines():
                        stripped = raw_line.strip(" -\t")
                        if not stripped:
                            continue
                        lower = stripped.lower()
                        if lower.startswith("risk"):
                            risk_line = _re.sub(r'^risk[:\s]*', '', stripped, flags=_re.IGNORECASE).strip()
                        elif lower.startswith("recommendation") or lower.startswith("recommend"):
                            rec_line = _re.sub(r'^recommend\w*[:\s]*', '', stripped, flags=_re.IGNORECASE).strip()
                        else:
                            # Strip leading "1. " / "2. " / "- " prefixes.
                            clean = _re.sub(r'^[\d]+[.)\s]+', '', stripped).strip()
                            if clean and len(findings) < 3:
                                findings.append(clean)

                    if not findings:
                        findings = [body[:200]]
                    if not rec_line:
                        rec_line = findings[-1] if findings else body[:180]
                    risk_str = risk_line or f"Structured JSON parse failed; used text-mode fallback for {label.lower()} analysis."

                    return AgentInsight(
                        agent_name=label,
                        findings=findings[:3],
                        risks=[risk_str],
                        recommendation=rec_line,
                        confidence=0.58,
                        evidence_used=[{"source": "llm_text_fallback", "detail": f"{department}_non_json_response"}],
                    )
            except Exception:
                pass

            return AgentInsight(
                agent_name=label,
                findings=[
                    f"{label} analysis completed with reduced confidence (LLM service temporarily unavailable).",
                    "Rule-based assessment applied using available context.",
                ],
                risks=[
                    f"LLM-enhanced {label.lower()} analysis could not be completed — using fallback policy rules.",
                    "Verify LLM API connectivity and retry for a higher-confidence assessment.",
                ],
                recommendation=(
                    f"Proceed cautiously: {label} considerations apply to this decision. "
                    "Consult the relevant department lead for a detailed review given the reduced AI confidence."
                ),
                confidence=0.35,
                evidence_used=[{"source": "fallback", "detail": f"{department}_degraded_analysis"}],
            )

    async def orchestrate_dynamic(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically route and execute selected agents with manager TLDR output."""
        routing = await self.route_agents(query, context)
        selected_names: List[str] = routing.get("selected_agents", [])
        force_simple_llm = bool(context.get("force_simple_llm_subagents", True))

        agent_insights: List[AgentInsight] = []
        for name in selected_names:
            if force_simple_llm:
                insight = await self._llm_subagent_reply(name, query, context)
                agent_insights.append(insight)
                continue

            agent = self.agent_registry.get(name)
            if agent is None:
                insight = await self._llm_subagent_reply(name, query, context)
                agent_insights.append(insight)
                continue

            try:
                insight = await agent.run(query, context)
            except Exception as exc:
                insight = AgentInsight(
                    agent_name=getattr(agent, "agent_name", agent.__class__.__name__),
                    findings=["Agent execution failed"],
                    risks=[f"{agent.__class__.__name__} unavailable during analysis"],
                    recommendation="Proceed with degraded confidence and gather more evidence",
                    confidence=0.2,
                    evidence_used=[{"source": "error", "detail": str(exc)}],
                )
            agent_insights.append(insight)

        conservative_view = self._generate_conservative_view(agent_insights, query)
        aggressive_view = self._generate_aggressive_view(agent_insights, query)
        final_decision = self._synthesize_decision(
            agent_insights,
            conservative_view,
            aggressive_view,
            persona="conservative",
        )

        if len(agent_insights) > 1:
            final_decision["tldr"] = self._build_tldr(agent_insights, final_decision)

        return {
            "routing": routing,
            "agent_insights": [insight.model_dump() for insight in agent_insights],
            "conservative_view": conservative_view,
            "aggressive_view": aggressive_view,
            "final_decision": final_decision,
        }

    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy full-orchestration path."""
        agent_insights = []
        for agent in self.agents:
            try:
                insight = await agent.run(query, context)
            except Exception as exc:
                insight = AgentInsight(
                    agent_name=getattr(agent, "agent_name", agent.__class__.__name__),
                    findings=["Agent execution failed"],
                    risks=[f"{agent.__class__.__name__} unavailable during analysis"],
                    recommendation="Proceed with degraded confidence and gather more evidence",
                    confidence=0.2,
                    evidence_used=[{"source": "error", "detail": str(exc)}],
                )
            agent_insights.append(insight)

        conservative_view = self._generate_conservative_view(agent_insights, query)
        aggressive_view = self._generate_aggressive_view(agent_insights, query)

        final_decision = self._synthesize_decision(
            agent_insights,
            conservative_view,
            aggressive_view,
            persona="conservative",
        )

        return {
            "agent_insights": [insight.model_dump() for insight in agent_insights],
            "conservative_view": conservative_view,
            "aggressive_view": aggressive_view,
            "final_decision": final_decision,
        }

    def _build_tldr(self, insights: List[AgentInsight], final_decision: Dict[str, Any]) -> str:
        risk = final_decision.get("risk_level", "Medium")
        confidence = final_decision.get("confidence_score", 0)
        departments = ", ".join(i.agent_name for i in insights)
        return (
            f"Departments consulted: {departments}. "
            f"Recommendation: {final_decision.get('recommendation', 'No recommendation')}. "
            f"Risk: {risk}. Confidence: {confidence}%."
        )

    def _generate_conservative_view(self, insights: List[AgentInsight], query: str) -> str:
        all_risks = []
        for insight in insights:
            all_risks.extend(insight.risks)

        conservative = "Conservative perspective: "
        if "pip" in str(all_risks).lower():
            conservative += "Legal/process risk too high without completed performance process. "
        if "termination" in query.lower() or "fire" in query.lower():
            conservative += "Replacement and transition cost may outweigh short-term gains. "
        conservative += "Recommend controlled steps, documentation, and measurable checkpoints."
        return conservative

    def _generate_aggressive_view(self, insights: List[AgentInsight], query: str) -> str:
        all_findings = []
        for insight in insights:
            all_findings.extend(insight.findings)

        aggressive = "Aggressive perspective: "
        if "underperform" in str(all_findings).lower():
            aggressive += "Sustained underperformance suggests urgent action. "
        if any(k in query.lower() for k in ["acquire", "expand", "launch"]):
            aggressive += "Delays can increase competitive opportunity cost. "
        aggressive += "Recommend decisive execution with risk controls in parallel."
        return aggressive

    def _synthesize_decision(
        self,
        insights: List[AgentInsight],
        conservative_view: str,
        aggressive_view: str,
        persona: str = "balanced",
    ) -> Dict[str, Any]:
        max_risk = "Low"
        for insight in insights:
            for risk in insight.risks:
                lower = risk.lower()
                if any(keyword in lower for keyword in ["legal", "termination", "compliance", "high"]):
                    max_risk = "High"
                elif max_risk != "High" and any(
                    keyword in lower for keyword in ["declining", "weak", "underperformance", "medium"]
                ):
                    max_risk = "Medium"

        avg_confidence = sum(insight.confidence for insight in insights) / len(insights) if insights else 0.0

        rationale = "Multi-agent analysis:\n\n"
        for insight in insights:
            rationale += f"**{insight.agent_name} Agent:** {' '.join(insight.findings[:2])}\n"
            if insight.risks:
                rationale += f"Risks: {insight.risks[0]}\n"
            rationale += f"Recommendation: {insight.recommendation}\n\n"

        if persona == "conservative":
            final_recommendation = self._extract_conservative_recommendation(conservative_view)
            rationale += f"\n**Manager Decision (Conservative):** {conservative_view}"
        elif persona == "aggressive":
            final_recommendation = self._extract_aggressive_recommendation(aggressive_view)
            rationale += f"\n**Manager Decision (Aggressive):** {aggressive_view}"
        else:
            final_recommendation = self._extract_balanced_recommendation(insights)
            rationale += "\n**Manager Decision (Balanced):** Weighing both perspectives."

        return {
            "recommendation": final_recommendation,
            "risk_level": max_risk,
            "confidence_score": round(avg_confidence * 100, 2),
            "rationale": rationale,
            "manager_persona": persona,
        }

    def _extract_conservative_recommendation(self, view: str) -> str:
        if "without completed performance process" in view.lower() or "pip" in view:
            return "DO NOT TERMINATE YET - Run a 60-day documented PIP first"
        return "Proceed with caution - implement protective measures first"

    def _extract_aggressive_recommendation(self, view: str) -> str:
        if "underperformance" in view.lower():
            return "TERMINATE - Sustained performance issue and action justified"
        return "Proceed decisively - delay creates opportunity cost"

    def _extract_balanced_recommendation(self, insights: List[AgentInsight]) -> str:
        return "Proceed with phased approach - validate before full commitment"
