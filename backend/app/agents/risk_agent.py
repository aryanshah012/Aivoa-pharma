"""Agent 3 — AI risk assessment (initial triage, never a final regulatory decision).

AI reasoning + structured output; deterministic rule guardrails clamp obviously
inconsistent outputs (e.g. adverse event reported can never be LOW overall).
"""
from app.agents.prompts import RISK_SYSTEM
from app.core.constants import RISK_LEVELS
from app.schemas.complaint import RiskAssessment
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model

_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def _apply_rule_guardrails(payload: dict, extracted: dict) -> dict:
    """Deterministic safety rules layered on top of the AI assessment."""
    if extracted.get("adverse_event_reported") and _ORDER.get(payload.get("overall_risk", "Low"), 0) < _ORDER["High"]:
        payload["overall_risk"] = "High"
        reasoning = payload.setdefault("reasoning", [])
        reasoning.append(
            "Rule guardrail: an adverse event was reported, so overall risk was raised to at least High."
        )
    if "contamination" in (extracted.get("complaint_type") or "").lower() and _ORDER.get(payload.get("overall_risk", "Low"), 0) < _ORDER["Critical"]:
        payload["overall_risk"] = "Critical"
        reasoning = payload.setdefault("reasoning", [])
        reasoning.append(
            "Rule guardrail: contamination complaints require Critical triage pending investigation."
        )
    return payload


def assess_risk(state: dict, llm: LLMService) -> dict:
    extracted = state.get("extracted_data") or {}
    errors: list = list(state.get("errors", []))

    context = (
        "COMPLAINT (structured):\n"
        + "\n".join(f"- {k}: {v}" for k, v in extracted.items() if v is not None)
        + "\n\nRAW COMPLAINT TEXT:\n" + state["raw_text"][:2000]
    )
    try:
        payload = llm.generate_json(RISK_SYSTEM, context)
        payload = _apply_rule_guardrails(payload, extracted)
        assessment = parse_model(RiskAssessment, payload, errors, "risk assessment")
    except LLMError as exc:
        errors.append(f"risk assessment unavailable: {exc}")
        assessment = None

    return {"risk_assessment": assessment.model_dump() if assessment else None, "errors": errors}
