"""
Multi-agent system for decision support.
"""
from .base_agent import BaseAgent, AgentInsight
from .hr_agent import HRAgent
from .sales_agent import SalesAgent
from .legal_agent import LegalAgent
from .finance_agent import FinanceAgent
from .marketing_agent import MarketingAgent
from .supply_chain_agent import SupplyChainAgent
from .manager_agent import ManagerAgent
from .intent_detector import detect_intent

__all__ = [
    "BaseAgent", "AgentInsight",
    "HRAgent", "SalesAgent", "LegalAgent",
    "FinanceAgent", "MarketingAgent", "SupplyChainAgent",
    "ManagerAgent", "detect_intent",
]
