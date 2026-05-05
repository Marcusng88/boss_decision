"""
Manager Agent - Orchestrates all domain agents and synthesizes final decision.
Marcus's responsibility (subagent personas: conservative vs aggressive).
"""
import json
import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from config import get_settings
from .base_agent import AgentInsight

try:
    from google import genai as google_genai
except Exception:
    google_genai = None


class ManagerAgent:
    """
    Manager agent that:
    1. Orchestrates all domain agents (HR, Sales, Legal, Finance, Marketing, Supply Chain)
    2. Aggregates their insights
    3. Applies decision-making persona (conservative vs aggressive)
    4. Produces final recommendation with rationale
    """
    
    def __init__(self, agents: List[Any], llm=None):
        """
        Initialize manager with domain agents.
        
        Args:
            agents: List of domain agent instances (HRAgent, SalesAgent, etc.)
            llm: LangChain LLM for synthesis (optional)
        """
        self.agents = agents
        self.llm = llm
        self.agent_registry = self._build_agent_registry(agents)
        self.router_init_error = None
        self.router_client = self._build_router_client()
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

    def _build_router_client(self):
        # Ensure local .env is loaded in terminal runs.
        load_dotenv(".env")

        if google_genai is None:
            self.router_init_error = "google.genai import failed"
            return None

        try:
            settings = get_settings()
            api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                self.router_init_error = "GOOGLE_API_KEY not found in settings or env"
                return None

            client = google_genai.Client(api_key=api_key)
            self.router_init_error = None
            return client
        except Exception as exc:
            self.router_init_error = f"router client init failed: {str(exc)}"
            return None

    def _canonical_agent_name(self, raw_name: str) -> str:
        lowered = (raw_name or "").strip().lower().replace(" ", "_")
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
            "operations": "operations",
            "operation": "operations",
        }
        lowered = lowered.replace("_agent", "agent")
        return aliases.get(lowered, lowered)

    def _safe_parse_json_text(self, raw_text: str) -> Dict[str, Any]:
        text = (raw_text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)

    async def route_agents(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select suitable departments using LLM routing first.

        Returns:
            {
              "selected_agents": ["hr", "legal"],
              "reasoning": "...",
              "confidence": 0.86,
              "route_source": "llm|fallback"
            }
        """
        doc_summary = context.get("document_summary")
        doc_department = context.get("document_department")
        allowed = ", ".join(self.supported_departments)

        routing_prompt = f"""
You are a manager router for a business chatbot.

Task:
- Choose the minimum necessary departments to answer the user.
- Use semantic intent and business reasoning (not simple keyword matching).
- Return STRICT JSON only.

Allowed departments:
[{allowed}]

User query:
{query}

Optional extracted document department:
{doc_department}

Optional extracted document summary:
{doc_summary}

Output schema:
{{
  "selected_agents": ["hr", "legal"],
  "reasoning": "short explanation",
  "confidence": 0.0
}}
""".strip()

        llm_error = None
        if self.router_client is not None:
            settings = get_settings()
            model_candidates = [
                settings.llm_model,
                "gemma-4-31b-it"
            ]
            # Preserve order and deduplicate.
            model_candidates = list(dict.fromkeys([m for m in model_candidates if m]))

            for model_name in model_candidates:
                try:
                    response = self.router_client.models.generate_content(
                        model=model_name,
                        contents=routing_prompt,
                        config=google_genai.types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                        ),
                    )
                    parsed = self._safe_parse_json_text(response.text or "")
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
                            "model_used": model_name,
                        }
                    llm_error = f"LLM returned no valid selected_agents with model '{model_name}'"
                except Exception as exc:
                    llm_error = f"{model_name}: {str(exc)}"

        # Fallback uses document classification signal first; only used when LLM is unavailable.
        selected = []
        if isinstance(doc_department, str):
            canonical = self._canonical_agent_name(doc_department)
            if canonical in self.supported_departments:
                selected.append(canonical)

        if not selected:
            selected = ["hr", "sales"]

        return {
            "selected_agents": selected,
            "reasoning": "Fallback routing used because LLM route was unavailable.",
            "confidence": 0.45,
            "route_source": "fallback",
            "route_error": llm_error or self.router_init_error,
        }

    async def orchestrate_dynamic(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically route and execute only selected agents.
        """
        routing = await self.route_agents(query, context)
        selected_names: List[str] = routing.get("selected_agents", [])

        selected_agents: List[Any] = []
        for name in selected_names:
            agent = self.agent_registry.get(name)
            if agent is not None:
                selected_agents.append(agent)

        # If no actual agent implementation exists for routed departments,
        # return placeholder insights to validate manager routing behavior.
        agent_insights: List[AgentInsight] = []
        for name in selected_names:
            if name in self.agent_registry:
                continue
            agent_insights.append(
                AgentInsight(
                    agent_name=name.upper(),
                    findings=[f"{name} agent selected by manager routing"],
                    risks=[f"{name} agent implementation not available yet"],
                    recommendation=f"Implement {name} agent to provide full analysis",
                    confidence=0.35,
                    evidence_used=[{"source": "manager_router", "detail": "selected_without_implementation"}],
                )
            )

        for agent in selected_agents:
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
            persona='conservative'
        )

        return {
            'routing': routing,
            'agent_insights': [insight.dict() for insight in agent_insights],
            'conservative_view': conservative_view,
            'aggressive_view': aggressive_view,
            'final_decision': final_decision
        }
    
    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate all agents and collect their insights.
        
        Args:
            query: User's decision query
            context: Additional context (target_type, target_id, etc.)
        
        Returns:
            Dict with agent_insights, conservative_view, aggressive_view, final_decision
        """
        
        # Run agents sequentially with failure isolation so one failure does not
        # block the entire decision pipeline.
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
        
        # Synthesize decision with different personas
        conservative_view = self._generate_conservative_view(agent_insights, query)
        aggressive_view = self._generate_aggressive_view(agent_insights, query)
        
        # Final decision (balanced by default, TODO: make persona configurable)
        final_decision = self._synthesize_decision(
            agent_insights, 
            conservative_view, 
            aggressive_view,
            persona='conservative'  # or 'balanced', 'aggressive'
        )
        
        return {
            'agent_insights': [insight.dict() for insight in agent_insights],
            'conservative_view': conservative_view,
            'aggressive_view': aggressive_view,
            'final_decision': final_decision
        }
    
    def _generate_conservative_view(self, insights: List[AgentInsight], query: str) -> str:
        """
        Generate conservative decision perspective.
        
        Conservative stance prioritizes:
        - Risk mitigation
        - Cost of action vs inaction
        - Legal compliance
        - Preserving optionality
        
        TODO (Marcus): Implement LLM-powered conservative reasoning
        """
        
        # Extract key risks from all agents
        all_risks = []
        for insight in insights:
            all_risks.extend(insight.risks)
        
        # Rule-based conservative view (TODO: Replace with LLM)
        conservative = "Conservative perspective: "
        
        if "PIP not initiated" in str(all_risks):
            conservative += "Legal risk too high without PIP completion. "
        
        if "replacement cost" in query.lower() or "termination" in query.lower():
            conservative += "Replacement cost and ramp time outweigh short-term savings. "
        
        conservative += "Recommend cautious approach with clear documentation and exit criteria."
        
        return conservative
    
    def _generate_aggressive_view(self, insights: List[AgentInsight], query: str) -> str:
        """
        Generate aggressive decision perspective.
        
        Aggressive stance prioritizes:
        - Speed of action
        - Cutting losses quickly
        - Team morale impact
        - Opportunity cost
        
        TODO: Implement LLM-powered aggressive reasoning
        """
        
        # Extract key findings from all agents
        all_findings = []
        for insight in insights:
            all_findings.extend(insight.findings)
        
        # Rule-based aggressive view (TODO: Replace with LLM)
        aggressive = "Aggressive perspective: "
        
        if "underperformance" in str(all_findings).lower():
            aggressive += "Sustained underperformance documented across multiple quarters. "
        
        if "revenue" in str(all_findings).lower() and "declining" in str(all_findings).lower():
            aggressive += "Poor performance hurts team morale and revenue. "
        
        aggressive += "Recommend decisive action to address performance issue promptly."
        
        return aggressive
    
    def _synthesize_decision(
        self, 
        insights: List[AgentInsight],
        conservative_view: str,
        aggressive_view: str,
        persona: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        Synthesize final decision based on agent insights and persona.
        
        TODO: Implement LLM-powered synthesis with persona weighting
        - Conservative: prioritize legal/risk agents
        - Aggressive: prioritize financial/performance agents
        - Balanced: equal weighting
        
        Args:
            insights: All agent insights
            conservative_view: Conservative perspective
            aggressive_view: Aggressive perspective
            persona: 'conservative', 'balanced', or 'aggressive'
        
        Returns:
            Final decision dict
        """
        
        # Extract agent recommendations
        recommendations = {insight.agent_name: insight.recommendation for insight in insights}
        
        # Determine risk level (highest risk from any agent)
        risk_levels = {'Low': 1, 'Medium': 2, 'High': 3}
        max_risk = 'Low'

        for insight in insights:
            for risk in insight.risks:
                lower = risk.lower()
                if any(keyword in lower for keyword in ['legal', 'termination', 'compliance', 'high']):
                    max_risk = 'High'
                elif max_risk != 'High' and any(keyword in lower for keyword in ['declining', 'weak', 'underperformance', 'medium']):
                    max_risk = 'Medium'
        
        # Calculate confidence (average of all agents)
        avg_confidence = sum(insight.confidence for insight in insights) / len(insights) if insights else 0.0
        
        # Generate rationale by combining agent insights
        rationale = "Multi-agent analysis:\n\n"
        for insight in insights:
            rationale += f"**{insight.agent_name} Agent:** {' '.join(insight.findings[:2])}\n"
            if insight.risks:
                rationale += f"Risks: {insight.risks[0]}\n"
            rationale += f"Recommendation: {insight.recommendation}\n\n"
        
        # Final recommendation based on persona
        if persona == 'conservative':
            final_recommendation = self._extract_conservative_recommendation(insights, conservative_view)
            rationale += f"\n**Manager Decision (Conservative):** {conservative_view}"
        elif persona == 'aggressive':
            final_recommendation = self._extract_aggressive_recommendation(insights, aggressive_view)
            rationale += f"\n**Manager Decision (Aggressive):** {aggressive_view}"
        else:  # balanced
            final_recommendation = self._extract_balanced_recommendation(insights)
            rationale += f"\n**Manager Decision (Balanced):** Weighing both perspectives."
        
        return {
            'recommendation': final_recommendation,
            'risk_level': max_risk,
            'confidence_score': round(avg_confidence * 100, 2),
            'rationale': rationale,
            'manager_persona': persona
        }
    
    def _extract_conservative_recommendation(self, insights: List[AgentInsight], view: str) -> str:
        """Extract key recommendation from conservative perspective."""
        # Simple heuristic (TODO: LLM-based extraction)
        if "PIP" in view:
            return "DO NOT TERMINATE - Initiate 60-day PIP with measurable criteria"
        return "Proceed with caution - implement protective measures first"
    
    def _extract_aggressive_recommendation(self, insights: List[AgentInsight], view: str) -> str:
        """Extract key recommendation from aggressive perspective."""
        # Simple heuristic (TODO: LLM-based extraction)
        if "underperformance" in view.lower():
            return "TERMINATE - Performance issues documented, action justified"
        return "Proceed decisively - delay creates opportunity cost"
    
    def _extract_balanced_recommendation(self, insights: List[AgentInsight]) -> str:
        """Extract balanced recommendation from agent consensus."""
        # Count agent recommendations leaning toward action vs caution
        # TODO: Implement proper consensus logic
        return "Proceed with phased approach - validate before full commitment"
