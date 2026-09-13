"""Agent 2 — completeness.

Deterministic where possible (required-field check runs in plain Python),
LLM used only to phrase useful follow-up questions.
"""
from app.agents.prompts import FOLLOWUP_QUESTIONS_SYSTEM
from app.core.constants import IMPORTANT_FIELDS, REQUIRED_FIELDS
from app.schemas.complaint import CompletenessResult
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model

# 60% of the score comes from required fields, 40% from important fields.
_WEIGHT_REQUIRED = 60 / len(REQUIRED_FIELDS)
_WEIGHT_IMPORTANT = 40 / len(IMPORTANT_FIELDS)


def check_required_fields(extracted: dict) -> tuple[list[str], list[str], list[str]]:
    """Deterministic completeness check. Returns (present_labels, missing_labels, missing_keys)."""
    present, missing_labels, missing_keys = [], [], []
    for key, label in list(REQUIRED_FIELDS.items()) + list(IMPORTANT_FIELDS.items()):
        value = extracted.get(key)
        is_empty = value is None or (isinstance(value, str) and not value.strip())
        if is_empty:
            missing_keys.append(key)
            missing_labels.append(label)
        else:
            present.append(label)
    return present, missing_labels, missing_keys


def evaluate_completeness(state: dict, llm: LLMService) -> dict:
    extracted = state.get("extracted_data") or {}
    errors: list = list(state.get("errors", []))

    present, missing_labels, missing_keys = check_required_fields(extracted)

    score = 0.0
    for key in REQUIRED_FIELDS:
        value = extracted.get(key)
        if value is not None and (not isinstance(value, str) or value.strip()):
            score += _WEIGHT_REQUIRED
    for key in IMPORTANT_FIELDS:
        value = extracted.get(key)
        if value is not None and (not isinstance(value, str) or value.strip()):
            score += _WEIGHT_IMPORTANT
    score = round(score, 1)

    questions: list[str] = []
    if missing_labels:
        try:
            payload = llm.generate_json(
                FOLLOWUP_QUESTIONS_SYSTEM,
                "Present fields: " + ", ".join(present)
                + "\nMissing fields: " + ", ".join(missing_labels)
                + "\nGenerate follow-up questions for the missing fields.",
                max_tokens=300,
            )
            questions = [str(q) for q in payload.get("recommended_questions", [])][:3]
        except LLMError as exc:
            errors.append(f"completeness follow-up questions unavailable: {exc}")

    result = CompletenessResult(
        score=score,
        status="Complete" if score >= 90 else "Incomplete",
        present_fields=present,
        missing_fields=missing_labels,
        recommended_questions=questions,
    )
    return {"completeness": result.model_dump(), "errors": errors}
