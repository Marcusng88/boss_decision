from __future__ import annotations

from typing import Any


def build_observer_answer(question: str, summary: str) -> dict[str, Any]:
    """Compose a grounded phase-1 observer response for the observer-chat API.

    Args:
        question: User question submitted after simulation completion.
        summary: Stored observer summary extracted from stream artifacts.

    Returns:
        Answer payload with a single citation pointing to `observer_summary`.
    """
    answer = (
        f"Observer answer (phase-1 mock): {question} | "
        f"Grounding source: observer_summary in session_state.jsonl. {summary}"
    )
    return {
        "answer": answer,
        "citations": [{"event_type": "observer_summary", "source": "session_state.jsonl"}],
    }
