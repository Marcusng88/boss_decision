from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from .schema import ActionIntent
from .schema import KPIState
from .schema import PersonaProfile


class ActionIntentOutput(BaseModel):
    action_type: str = "wait"
    args: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.4
    rationale_md: str = ""


def parse_action_intent(
    persona: PersonaProfile,
    tick: int,
    transcript_md: str,
    parser_model: Any | None,
) -> ActionIntent | None:
    if not transcript_md.strip():
        return None

    if parser_model is None:
        return None

    prompt = (
        "Extract a world-changing action intent if present. "
        "If no explicit action is present, return action_type='wait'. "
        "Return only JSON with keys: action_type,args,confidence,rationale_md. "
        "Allowed action_type values: move, price_adjust, spend_shift, campaign, procurement, wait. "
        f"Persona: {json.dumps({'id': persona.id, 'role': persona.role, 'objective': persona.objective})} "
        f"Tick: {tick} "
        f"Transcript: {json.dumps(transcript_md[:4000])}"
    )
    try:
        if hasattr(parser_model, "with_structured_output"):
            structured = parser_model.with_structured_output(ActionIntentOutput)
            parsed = structured.invoke(prompt)
        else:
            response = parser_model.invoke(prompt)
            parsed = ActionIntentOutput.model_validate_json(str(getattr(response, "content", "{}")))
        normalized = parsed if isinstance(parsed, ActionIntentOutput) else ActionIntentOutput.model_validate(parsed)
        if normalized.action_type == "wait":
            return None
        return ActionIntent(
            persona_id=persona.id,
            tick=tick,
            action_type=normalized.action_type,  # type: ignore[arg-type]
            args=normalized.args,
            confidence=max(0.0, min(1.0, float(normalized.confidence))),
            rationale_md=normalized.rationale_md[:1200],
            requested_via_tool=False,
        )
    except Exception:
        return None


def validate_intent(intent: ActionIntent, kpi: KPIState) -> tuple[bool, str]:
    if intent.action_type == "price_adjust":
        delta = intent.args.get("delta_pct")
        if not isinstance(delta, (int, float)):
            return False, "price_adjust requires numeric delta_pct."
        if float(delta) < -25 or float(delta) > 25:
            return False, "delta_pct out of safe bounds (-25 to +25)."
    if intent.action_type == "spend_shift":
        budget = intent.args.get("budget_pct")
        if isinstance(budget, (int, float)) and float(budget) > 60:
            return False, "spend_shift budget_pct too high."
    if intent.action_type == "campaign" and kpi.churn_risk > 8.5:
        return False, "campaign blocked: churn risk already critical."
    return True, "accepted"


def resolve_conflicts(
    intents: list[ActionIntent],
    personas: list[PersonaProfile],
) -> list[ActionIntent]:
    if not intents:
        return []
    weight_by_persona = {persona.id: persona.weight for persona in personas}

    def _score(intent: ActionIntent) -> tuple[float, str]:
        role_weight = weight_by_persona.get(intent.persona_id, 1.0)
        feasibility = 1.0
        if intent.action_type == "procurement":
            feasibility = 0.9
        if intent.action_type == "move":
            feasibility = 1.1
        hybrid = role_weight * float(intent.confidence) * feasibility
        return hybrid, intent.persona_id

    by_type: dict[str, list[ActionIntent]] = {}
    for intent in intents:
        by_type.setdefault(intent.action_type, []).append(intent)

    resolved: list[ActionIntent] = []
    for action_type, bucket in by_type.items():
        if action_type in {"move", "campaign"}:
            resolved.extend(sorted(bucket, key=_score, reverse=True)[:2])
        else:
            resolved.append(sorted(bucket, key=_score, reverse=True)[0])
    return resolved


def apply_intents_to_kpis(kpi: KPIState, intents: list[ActionIntent]) -> KPIState:
    revenue = kpi.revenue
    margin = kpi.margin
    sentiment = kpi.sentiment
    churn_risk = kpi.churn_risk

    for intent in intents:
        confidence_scale = 0.3 + 0.7 * float(intent.confidence)
        if intent.action_type == "price_adjust":
            delta_pct = float(intent.args.get("delta_pct", 0.0))
            revenue += 0.16 * delta_pct * confidence_scale
            margin += 0.23 * delta_pct * confidence_scale
            sentiment -= 0.11 * max(delta_pct, 0.0) * confidence_scale
            churn_risk += 0.09 * max(delta_pct, 0.0) * confidence_scale
        elif intent.action_type == "spend_shift":
            budget_pct = float(intent.args.get("budget_pct", 4.0))
            sentiment += 0.06 * budget_pct * confidence_scale
            revenue += 0.04 * budget_pct * confidence_scale
            margin -= 0.03 * budget_pct * confidence_scale
        elif intent.action_type == "campaign":
            sentiment += 0.48 * confidence_scale
            revenue += 0.22 * confidence_scale
            churn_risk -= 0.21 * confidence_scale
        elif intent.action_type == "procurement":
            margin += 0.33 * confidence_scale
        elif intent.action_type == "move":
            sentiment += 0.12 * confidence_scale

    return KPIState(
        revenue=round(revenue, 2),
        margin=round(margin, 2),
        sentiment=round(sentiment, 2),
        churn_risk=round(max(0.0, churn_risk), 2),
    )
