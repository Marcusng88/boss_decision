from __future__ import annotations

from typing import Any


class NetworkOrchestrator:
    """Phase-1 placeholder for node-turn orchestration."""

    def __init__(self) -> None:
        """Initialize placeholder orchestration state for phase-1."""
        self.ready = False

    def plan_turn(self, _state: dict[str, Any]) -> dict[str, Any]:
        """Return a stub turn-plan response for compatibility with future phases."""
        return {"status": "stub", "note": "Phase-1 mock orchestrator only."}
