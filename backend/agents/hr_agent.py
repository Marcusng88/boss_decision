"""
HR Agent - Analyzes employee performance, attendance, warnings, PIP status.
Yihao's responsibility.
"""
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight


class HRAgent(BaseAgent):
    """
    HR domain specialist agent.
    Focuses on: performance reviews, attendance, warnings, PIP status, termination policies.
    """
    
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve HR-related evidence.
        
        For employee termination decisions:
        - Performance reviews (last 2-4 quarters)
        - Attendance records
        - Warning history
        - PIP status
        """
        evidence = []
        
        # If target is an employee, get their HR records
        if context.get('target_type') == 'employee' and context.get('target_id'):
            employee_id = context['target_id']
            
            # Get performance reviews
            hr_records = await self.db.get_employee_hr_records(employee_id)
            evidence.extend([
                {
                    'source': 'hr_record',
                    'type': 'performance_review',
                    'record_id': record['hr_id'],
                    'data': record
                }
                for record in hr_records
            ])
        
        return evidence
    
    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Analyze HR evidence and produce insights.
        
        TODO (Yihao): Implement LLM-powered analysis
        - Use LangChain to structure analysis
        - Generate findings from performance trends
        - Identify risks (legal, morale, etc.)
        - Produce recommendation
        """
        
        # Extract HR records
        hr_records = [e['data'] for e in evidence if e['source'] == 'hr_record']
        
        if not hr_records:
            return AgentInsight(
                agent_name="HR",
                findings=["No HR records found for analysis"],
                risks=["Cannot assess performance without data"],
                recommendation="Insufficient data for HR assessment",
                confidence=0.0,
                evidence_used=[]
            )
        
        # Basic rule-based analysis (TODO: Replace with LLM)
        findings = []
        risks = []
        
        # Analyze performance trend
        recent_scores = [r['performance_score'] for r in hr_records[:3] if r.get('performance_score')]
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            findings.append(f"Average performance score (last 3 reviews): {avg_score:.1f}/5.0")
            
            if avg_score < 2.5:
                findings.append("Performance consistently below expectations (< 2.5/5)")
                risks.append("Sustained underperformance documented")
        
        # Check warnings
        total_warnings = sum(r.get('warning_count', 0) for r in hr_records)
        if total_warnings > 0:
            findings.append(f"Total warnings issued: {total_warnings}")
            risks.append("Disciplinary action history on record")
        
        # Check PIP status
        pip_records = [r for r in hr_records if r.get('pip_status')]
        if pip_records:
            latest_pip = pip_records[0]['pip_status']
            findings.append(f"PIP status: {latest_pip}")
            
            if latest_pip is None or latest_pip == '':
                risks.append("PIP not initiated - required before performance termination per policy")
        
        # Generate recommendation
        if recent_scores and sum(recent_scores) / len(recent_scores) < 2.5 and total_warnings >= 2:
            if not pip_records or pip_records[0]['pip_status'] is None:
                recommendation = "Initiate mandatory 60-day PIP before considering termination"
            else:
                recommendation = "Performance grounds for termination exist if PIP fails"
        else:
            recommendation = "Performance issues present but not severe enough for termination consideration"
        
        return AgentInsight(
            agent_name="HR",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.75,
            evidence_used=evidence
        )
