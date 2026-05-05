"""
Supabase database client and helper functions.
"""
from supabase import create_client, Client
from functools import lru_cache
from config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance."""
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )


class DatabaseService:
    """Service class for database operations."""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    async def get_employee(self, employee_id: int):
        """Get employee with related records."""
        response = self.client.table('employee') \
            .select('*, department:dept_id(*)') \
            .eq('employee_id', employee_id) \
            .single() \
            .execute()
        return response.data
    
    async def get_employee_hr_records(self, employee_id: int):
        """Get HR performance records for an employee."""
        response = self.client.table('hr_record') \
            .select('*') \
            .eq('employee_id', employee_id) \
            .order('period', desc=True) \
            .execute()
        return response.data
    
    async def get_employee_sales_records(self, employee_id: int, period: str = None):
        """Get sales records for an employee."""
        query = self.client.table('sales_record') \
            .select('*') \
            .eq('employee_id', employee_id)
        
        if period:
            query = query.eq('period', period)
        
        response = query.order('period', desc=True).execute()
        return response.data
    
    async def get_legal_policies(self, category: str = None):
        """Get legal policies, optionally filtered by category."""
        query = self.client.table('legal_policy').select('*')
        
        if category:
            query = query.eq('policy_category', category)
        
        response = query.execute()
        return response.data
    
    async def get_case_evidence(self, case_id: int):
        """Get all evidence linked to a decision case."""
        response = self.client.table('case_evidence') \
            .select('*') \
            .eq('case_id', case_id) \
            .order('relevance_score', desc=True) \
            .execute()
        return response.data
    
    async def get_decision_output(self, case_id: int):
        """Get decision output for a case."""
        response = self.client.table('decision_output') \
            .select('*') \
            .eq('case_id', case_id) \
            .single() \
            .execute()
        return response.data
    
    async def create_decision_case(self, question: str, context: str = None, 
                                  target_type: str = None, target_id: int = None,
                                  submitted_by: str = None):
        """Create a new decision case."""
        response = self.client.table('decision_case') \
            .insert({
                'question': question,
                'context': context,
                'target_type': target_type,
                'target_id': target_id,
                'submitted_by': submitted_by,
                'status': 'processing'
            }) \
            .execute()
        return response.data[0]
    
    async def save_case_evidence(self, case_id: int, source_table: str, 
                                record_id: int, relevance_score: float,
                                retrieval_method: str = 'sql_query', notes: str = None):
        """Save evidence linking for a case."""
        response = self.client.table('case_evidence') \
            .insert({
                'case_id': case_id,
                'source_table': source_table,
                'record_id': record_id,
                'relevance_score': relevance_score,
                'retrieval_method': retrieval_method,
                'notes': notes
            }) \
            .execute()
        return response.data[0]
    
    async def save_decision_output(self, case_id: int, recommendation: str,
                                  risk_level: str, confidence_score: float,
                                  rationale: str, conservative_view: str = None,
                                  aggressive_view: str = None, 
                                  manager_persona: str = 'balanced',
                                  ai_justification: str = None):
        """Save final decision output."""
        response = self.client.table('decision_output') \
            .insert({
                'case_id': case_id,
                'recommendation': recommendation,
                'risk_level': risk_level,
                'confidence_score': confidence_score,
                'rationale': rationale,
                'conservative_view': conservative_view,
                'aggressive_view': aggressive_view,
                'manager_persona': manager_persona,
                'ai_justification': ai_justification
            }) \
            .execute()
        
        # Update case status to completed
        self.client.table('decision_case') \
            .update({'status': 'completed'}) \
            .eq('case_id', case_id) \
            .execute()
        
        return response.data[0]
