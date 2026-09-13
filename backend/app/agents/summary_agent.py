"""Agent 7 — short + management complaint summaries."""
from app.agents.prompts import SUMMARY_SYSTEM
from app.schemas.complaint import SummaryResult
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model


def generate_summary(state: dict, llm: LLMService) -> dict:
    errors: list = list(state.get("errors", []))
    risk = (state.get("risk_assessment") or {}).get("overall_risk", "unknown")
    context = "AI risk level: " + str(risk) + "\n\nCOMPLAINT TEXT:\n" + state["raw_text"][:2000]
    try:
        payload = llm.generate_json(SUMMARY_SYSTEM, context, max_tokens=500)
        summary = parse_model(SummaryResult, payload, errors, "summary")
    except LLMError as exc:
        errors.append(f"summary unavailable: {exc}")
        summary = None

    return {"summary": summary.model_dump() if summary else None, "errors": errors}
