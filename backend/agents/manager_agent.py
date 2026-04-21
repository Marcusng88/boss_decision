"""
Manager Agent - Orchestrates all domain agents and synthesizes final decision.
Marcus's responsibility (subagent personas: conservative vs aggressive).
"""
from typing import Dict, List, Any
from .base_agent import AgentInsight


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
    
    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate all agents and collect their insights.
        
        Args:
            query: User's decision query
            context: Additional context (target_type, target_id, etc.)
        
        Returns:
            Dict with agent_insights, conservative_view, aggressive_view, final_decision
        """
        
        # Run all agents in parallel (or sequentially for now)
        agent_insights = []
        for agent in self.agents:
            insight = await agent.run(query, context)
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
        
        TODO (Marcus): Implement LLM-powered aggressive reasoning
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
        
        TODO (Marcus): Implement LLM-powered synthesis with persona weighting
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
            'risk_level': 'Medium',  # TODO: Calculate from agent risks
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
