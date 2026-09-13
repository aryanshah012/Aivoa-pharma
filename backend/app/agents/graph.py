"""LangGraph workflow orchestrating the 7 AI agents.

START -> extract_complaint -> validate_completeness -> classify_risk
      -> detect_duplicates -> suggest_root_causes -> recommend_capa
      -> generate_summary -> finalize_response -> END

Design notes:
- Sequential, predictable, easy to explain in a code walkthrough.
- Extraction is the only blocking node; every other node degrades gracefully:
  a failed optional agent records a soft error and the workflow continues.
- Dependencies (LLM service, DB session) are injected when the graph is built,
  which keeps every node a pure `state -> partial state` function and makes the
  whole workflow trivial to unit-test with fakes.
"""
from langgraph.graph import END, StateGraph

from app.agents.capa_agent import recommend_capa
from app.agents.completeness_agent import evaluate_completeness
from app.agents.duplicate_agent import detect_duplicates
from app.agents.extraction_agent import extract_complaint
from app.agents.risk_agent import assess_risk
from app.agents.root_cause_agent import suggest_root_causes
from app.agents.state import ComplaintState
from app.agents.summary_agent import generate_summary
from app.services.llm_service import LLMService


def _finalize(state: ComplaintState) -> dict:
    """Assemble the END payload consumed by the API route."""
    return {
        "final_result": {
            "extracted_data": state.get("extracted_data") or {},
            "completeness": state.get("completeness"),
            "risk_assessment": state.get("risk_assessment"),
            "duplicate_matches": state.get("duplicate_matches") or [],
            "root_cause_analysis": state.get("root_cause_analysis"),
            "capa_recommendations": state.get("capa_recommendations"),
            "summary": state.get("summary"),
            "errors": state.get("errors") or [],
        }
    }


def build_graph(llm: LLMService, db=None):
    """Compile the workflow with dependencies injected into each node."""
    model_used: list = []

    graph = StateGraph(ComplaintState)

    graph.add_node("extract_complaint", lambda s: extract_complaint(s, llm, model_used))
    graph.add_node("validate_completeness", lambda s: evaluate_completeness(s, llm))
    graph.add_node("classify_risk", lambda s: assess_risk(s, llm))
    graph.add_node("detect_duplicates", lambda s: detect_duplicates(s, db))
    graph.add_node("suggest_root_causes", lambda s: suggest_root_causes(s, llm))
    graph.add_node("recommend_capa", lambda s: recommend_capa(s, llm))
    graph.add_node("generate_summary", lambda s: generate_summary(s, llm))
    graph.add_node("finalize_response", _finalize)

    graph.set_entry_point("extract_complaint")
    graph.add_edge("extract_complaint", "validate_completeness")
    graph.add_edge("validate_completeness", "classify_risk")
    graph.add_edge("classify_risk", "detect_duplicates")
    graph.add_edge("detect_duplicates", "suggest_root_causes")
    graph.add_edge("suggest_root_causes", "recommend_capa")
    graph.add_edge("recommend_capa", "generate_summary")
    graph.add_edge("generate_summary", "finalize_response")
    graph.add_edge("finalize_response", END)

    return graph.compile(), model_used


def run_analysis(raw_text: str, llm: LLMService, db=None) -> dict:
    """Execute the full LangGraph workflow and return the finalized result."""
    graph, model_used = build_graph(llm, db)
    final_state = graph.invoke(
        {
            "raw_text": raw_text,
            "db": db,
            "errors": [],
            "extracted_data": {},
            "duplicate_matches": [],
        }
    )
    result = final_state["final_result"]
    result["model_used"] = next(
        (m for m in model_used if m), llm.last_model or llm.settings.GROQ_MODEL
    )
    return result
