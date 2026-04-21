"""
Base agent class for domain-specific analysis.
All agents (HR, Sales, Legal, etc.) inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel


class AgentInsight(BaseModel):
    """Structured output from an agent."""
    agent_name: str
    findings: List[str]
    risks: List[str]
    recommendation: str
    confidence: float  # 0.0 to 1.0
    evidence_used: List[Dict[str, Any]]  # List of record IDs and sources


class BaseAgent(ABC):
    """
    Abstract base class for domain-specific agents.
    Each agent retrieves relevant data and provides structured insights.
    """
    
    def __init__(self, db_service, llm=None):
        """
        Initialize agent with database service and optional LLM.
        
        Args:
            db_service: DatabaseService instance for data retrieval
            llm: LangChain LLM instance (optional, for AI-powered analysis)
        """
        self.db = db_service
        self.llm = llm
        self.agent_name = self.__class__.__name__.replace('Agent', '')
    
    @abstractmethod
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve relevant evidence from database for this agent's domain.
        
        Args:
            query: User's decision query
            context: Additional context (target_type, target_id, etc.)
        
        Returns:
            List of relevant records
        """
        pass
    
    @abstractmethod
    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Analyze evidence and produce structured insights.
        
        Args:
            evidence: Retrieved records
            query: User's decision query
        
        Returns:
            AgentInsight with findings, risks, recommendation
        """
        pass
    
    async def run(self, query: str, context: Dict[str, Any]) -> AgentInsight:
        """
        Execute full agent pipeline: retrieve evidence + analyze.
        
        Args:
            query: User's decision query
            context: Additional context
        
        Returns:
            AgentInsight
        """
        evidence = await self.retrieve_evidence(query, context)
        insight = await self.analyze(evidence, query)
        return insight
