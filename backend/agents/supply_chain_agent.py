"""
Supply Chain Agent - Checks inventory availability and restock risk.
"""
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentInsight


class SupplyChainAgent(BaseAgent):
    """
    Supply chain domain specialist agent.
    Focuses on: inventory availability, supplier visibility, and restock alerts.
    """

    LOW_INVENTORY_THRESHOLD = 1000

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve supply-related evidence by supply_id.
        """
        evidence: List[Dict[str, Any]] = []

        supply_id = context.get("supply_id")
        if not supply_id and context.get("target_type") in {"supply", "supply_record"}:
            supply_id = context.get("target_id")

        if not supply_id:
            return evidence

        supply_record = await self.db.get_supply_record(int(supply_id))
        if not supply_record:
            return evidence

        evidence.append(
            {
                "source": "supply_record",
                "type": "inventory",
                "record_id": supply_record["supply_id"],
                "data": supply_record,
            }
        )
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Analyze inventory level and determine whether restock notification is required.
        """
        if not evidence:
            return AgentInsight(
                agent_name="SupplyChain",
                findings=["No supply records found for analysis"],
                risks=["Cannot assess inventory availability without supply data"],
                recommendation="Insufficient data for supply chain assessment",
                confidence=0.0,
                evidence_used=[],
            )

        record = evidence[0]["data"]
        item_name = record.get("item_name", "Unknown item")
        supplier_name = record.get("supplier_name") or "Unknown supplier"
        inventory_level = record.get("inventory_level")
        unit_cost = record.get("unit_cost")

        findings = [
            f"Supply item: {item_name}",
            f"Current inventory level: {inventory_level}",
            f"Supplier: {supplier_name}",
            f"Unit price per item: RM {unit_cost:,.2f}" if unit_cost is not None else "Unit price per item: Not available",
        ]
        risks: List[str] = []

        if inventory_level is None:
            risks.append("Inventory level is missing; restock trigger cannot be evaluated reliably")
            recommendation = "Verify inventory tracking data before taking procurement action"
            confidence = 0.6
        elif inventory_level < self.LOW_INVENTORY_THRESHOLD:
            risks.append(
                f"Low inventory detected: {inventory_level} is below threshold {self.LOW_INVENTORY_THRESHOLD}"
            )
            recommendation = (
                f"Trigger restock notification for {item_name} and coordinate replenishment with {supplier_name}"
            )
            confidence = 0.92
        else:
            recommendation = f"Inventory is sufficient for {item_name}; restock notification not required"
            confidence = 0.9

        return AgentInsight(
            agent_name="SupplyChain",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=confidence,
            evidence_used=evidence,
        )
