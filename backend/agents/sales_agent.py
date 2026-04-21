"""
Sales Agent - Analyzes revenue contribution, deal pipeline, sales performance.
Jialih's responsibility.
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
        
        # If target is an employee, get their sales records
        if context.get('target_type') == 'employee' and context.get('target_id'):
            employee_id = context['target_id']
            
            # Get sales records
            sales_records = await self.db.get_employee_sales_records(employee_id)
            evidence.extend([
                {
                    'source': 'sales_record',
                    'type': 'deal',
                    'record_id': record['sales_id'],
                    'data': record
                }
                for record in sales_records
            ])
        
        return evidence
    
    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Analyze sales evidence and produce insights.
        
        TODO (Jialih): Implement LLM-powered analysis
        - Use LangChain for structured sales analysis
        - Compare to team benchmarks
        - Analyze pipeline health
        - Assess revenue impact
        """
        
        # Extract sales records
        sales_records = [e['data'] for e in evidence if e['source'] == 'sales_record']
        
        if not sales_records:
            return AgentInsight(
                agent_name="Sales",
                findings=["No sales records found for analysis"],
                risks=["Cannot assess sales performance without data"],
                recommendation="Insufficient data for sales assessment",
                confidence=0.0,
                evidence_used=[]
            )
        
        # Basic rule-based analysis (TODO: Replace with LLM)
        findings = []
        risks = []
        
        # Calculate revenue by period
        closed_deals = [r for r in sales_records if r['deal_stage'] == 'closed']
        total_revenue = sum(r['amount'] for r in closed_deals)
        deal_count = len(closed_deals)
        
        findings.append(f"Total closed deals: {deal_count}")
        findings.append(f"Total revenue contribution: RM {total_revenue:,.2f}")
        
        if deal_count > 0:
            avg_deal_size = total_revenue / deal_count
            findings.append(f"Average deal size: RM {avg_deal_size:,.2f}")
        
        # Analyze by period
        period_revenue = {}
        for record in closed_deals:
            period = record['period']
            period_revenue[period] = period_revenue.get(period, 0) + record['amount']
        
        if period_revenue:
            findings.append(f"Revenue by period: {period_revenue}")
            
            # Check for declining trend
            periods = sorted(period_revenue.keys())
            if len(periods) >= 2:
                latest = period_revenue[periods[-1]]
                previous = period_revenue[periods[-2]]
                
                if latest < previous * 0.5:
                    risks.append("Revenue declining significantly quarter-over-quarter")
                    findings.append("Sales performance trending down")
        
        # Check pipeline health
        pipeline_deals = [r for r in sales_records if r['deal_stage'] == 'pipeline']
        lost_deals = [r for r in sales_records if r['deal_stage'] == 'lost']
        
        findings.append(f"Active pipeline: {len(pipeline_deals)} deals")
        findings.append(f"Lost deals: {len(lost_deals)}")
        
        if len(pipeline_deals) < 2:
            risks.append("Pipeline health weak - insufficient active opportunities")
        
        # Generate recommendation
        if total_revenue < 50000 and deal_count < 3:
            recommendation = "Sales performance below team standards - revenue contribution insufficient"
            if len(pipeline_deals) < 2:
                recommendation += ". Pipeline also weak - indicates systemic performance issue"
        elif total_revenue < 100000:
            recommendation = "Sales performance acceptable but below top performers"
        else:
            recommendation = "Sales performance meeting or exceeding expectations"
        
        return AgentInsight(
            agent_name="Sales",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.80,
            evidence_used=evidence
        )
