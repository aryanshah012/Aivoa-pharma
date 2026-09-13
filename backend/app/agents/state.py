"""LangGraph shared state for the complaint-analysis workflow."""
from typing import Any, Optional, TypedDict


class ComplaintState(TypedDict, total=False):
    raw_text: str
    db: Any                     # SQLAlchemy Session (duplicate detection) — not serialised
    extracted_data: dict
    completeness: dict
    risk_assessment: dict
    duplicate_matches: list
    root_cause_analysis: dict
    capa_recommendations: dict
    summary: dict
    model_used: str
    errors: list
    final_result: dict
