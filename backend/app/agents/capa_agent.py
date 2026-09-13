"""Agent 6 — CAPA recommendations (corrective + preventive + verification)."""
from app.agents.prompts import CAPA_SYSTEM
from app.schemas.complaint import CapaRecommendations
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model


def recommend_capa(state: dict, llm: LLMService) -> dict:
    errors: list = list(state.get("errors", []))
    rca = state.get("root_cause_analysis") or {}
    context = (
        "COMPLAINT TEXT:\n" + state["raw_text"][:2000]
        + "\n\nINVESTIGATION HYPOTHESES:\n"
        + "\n".join(
            f"- {c.get('cause')} ({c.get('confidence')} confidence)"
            for c in rca.get("possible_causes", [])
        )
    )
    try:
        payload = llm.generate_json(CAPA_SYSTEM, context, max_tokens=800)
        capa = parse_model(CapaRecommendations, payload, errors, "CAPA recommendations")
    except LLMError as exc:
        errors.append(f"CAPA recommendations unavailable: {exc}")
        capa = None

    return {
        "capa_recommendations": capa.model_dump() if capa else None,
        "errors": errors,
    }
