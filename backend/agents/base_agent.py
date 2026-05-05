"""
Base agent class for domain-specific analysis.
All agents (HR, Sales, Legal, etc.) inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class AgentInsight(BaseModel):
    """Structured output from an agent."""
    agent_name: str
    emoji: str = ""
    findings: List[str]
    risks: List[str]
    recommendation: str
    confidence: float              # 0.0 to 1.0
    evidence_used: List[Dict[str, Any]] = []
    data_summary: str = ""        # brief label for dashboard card
    metric_value: str = ""        # key metric value for display
    trend: str = "flat"           # "up" | "down" | "flat"


class BaseAgent(ABC):
    """Abstract base class for domain-specific agents."""

    def __init__(self, db_service, llm=None):
        self.db = db_service
        self.llm = llm
        self.agent_name = self.__class__.__name__.replace('Agent', '')

    @abstractmethod
    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        pass

    async def run(self, query: str, context: Dict[str, Any]) -> AgentInsight:
        evidence = await self.retrieve_evidence(query, context)
        insight = await self.analyze(evidence, query)
        return insight
