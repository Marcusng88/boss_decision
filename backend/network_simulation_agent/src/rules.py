from __future__ import annotations

from typing import Any


def validate_action(action: dict[str, Any]) -> tuple[bool, str]:
    """Validate that a node action contains required phase-1 contract fields.

    Args:
        action: Candidate action payload emitted by a node.

    Returns:
        Tuple of `(is_valid, reason)` where `reason` is `"ok"` or missing-field details.
    """
    required = {"action_type", "source_node_id", "payload", "rationale", "confidence"}
    missing = sorted(required - set(action.keys()))
    if missing:
        return False, f"missing fields: {', '.join(missing)}"
    return True, "ok"
