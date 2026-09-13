"""Helpers to coerce possibly-malformed LLM output into validated Pydantic models."""
import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def extract_json(text: str) -> dict | list:
    """Best-effort extraction of the first JSON object/array from an LLM response."""
    text = text.strip()
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not start_candidates:
        raise ValueError("No JSON object found in model output")
    start = min(start_candidates)
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    end = text.rfind(closer)
    if end == -1 or end < start:
        raise ValueError("Unbalanced JSON in model output")
    return json.loads(text[start:end + 1])


def parse_model(cls: type[T], payload: dict, errors: list[str], label: str) -> T | None:
    """Validate dict against a Pydantic schema; record a soft error instead of raising."""
    try:
        return cls.model_validate(payload)
    except ValidationError as exc:
        errors.append(f"{label}: schema validation failed ({exc.errors()[0]['msg']})")
        return None
