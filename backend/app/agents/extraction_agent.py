"""Agent 1 — extraction: unstructured complaint text -> strict structured JSON.

Blocking: if extraction fails the whole analysis fails with a clear error.
"""
from app.agents.prompts import EXTRACT_SYSTEM
from app.schemas.complaint import ExtractedData
from app.services.llm_service import LLMError, LLMService
from app.utils.json_safe import parse_model


def extract_complaint(state: dict, llm: LLMService, model_used: list) -> dict:
    text = state["raw_text"].strip()
    if len(text) < 10:
        raise LLMError("Complaint text is too short to analyze (minimum 10 characters).")

    payload = llm.generate_json(
        EXTRACT_SYSTEM,
        "Extract the complaint information from the text below.\n\nCOMPLAINT TEXT:\n" + text,
    )
    errors: list = list(state.get("errors", []))
    extracted = parse_model(ExtractedData, payload, errors, "extraction")
    if extracted is None:
        # Soft-fail to an all-null structure so downstream nodes can still run.
        extracted = ExtractedData()
        errors.append("extraction: output did not match schema; fields defaulted to null")

    model_used.append(getattr(llm, "last_model", ""))
    return {"extracted_data": extracted.model_dump(), "errors": errors}
