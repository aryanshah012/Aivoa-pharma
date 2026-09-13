"""Agent 5 — AI investigation suggestions (hypotheses, never confirmed root causes)."""
from app.agents.prompts import ROOT_CAUSE_SYSTEM
from app.schemas.complaint import RootCauseAnalysis
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model


def suggest_root_causes(state: dict, llm: LLMService) -> dict:
    errors: list = list(state.get("errors", []))
    context = (
        "COMPLAINT TEXT:\n" + state["raw_text"][:2000]
        + "\n\nEXTRACTED DATA:\n"
        + "\n".join(
            f"- {k}: {v}" for k, v in (state.get("extracted_data") or {}).items() if v is not None
        )
    )
    try:
        payload = llm.generate_json(ROOT_CAUSE_SYSTEM, context, max_tokens=800)
        analysis = parse_model(RootCauseAnalysis, payload, errors, "root cause suggestions")
    except LLMError as exc:
        errors.append(f"root cause suggestions unavailable: {exc}")
        analysis = None

    return {
        "root_cause_analysis": analysis.model_dump() if analysis else None,
        "errors": errors,
    }
