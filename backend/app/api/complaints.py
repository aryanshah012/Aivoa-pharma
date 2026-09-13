"""Complaint routes: CRUD + AI analysis endpoints.

Progress messages returned by /analyze mirror the LangGraph node order so the
frontend can show a live processing indicator.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.repositories import complaint_repo as repo
from app.schemas.complaint import (
    AnalysisResponse,
    AnalyzeTextRequest,
    CapaActionCreate,
    CapaActionOut,
    ComplaintCreate,
    ComplaintDetailOut,
    ComplaintOut,
    ComplaintUpdate,
)
from app.services.document_service import extract_text_from_upload
from app.services.llm_service import LLMError, LLMService
from app.agents.graph import run_analysis

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

ANALYSIS_PROGRESS = [
    "Reading complaint...",
    "Extracting details...",
    "Checking completeness...",
    "Assessing risk...",
    "Checking similar complaints...",
    "Generating recommendations...",
    "Summarizing...",
]


def _get_llm() -> LLMService:
    return LLMService(get_settings())


@router.get("", response_model=list[ComplaintOut])
def list_complaints(
    product: str | None = None,
    risk: str | None = None,
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return repo.list_complaints(
        db,
        product=product, risk=risk, status=status, category=category,
        search=search, date_from=date_from, date_to=date_to,
        skip=skip, limit=limit,
    )


@router.get("/progress-messages", response_model=list[str])
def progress_messages():
    """Convenience endpoint so the UI stays in sync with the graph node order."""
    return ANALYSIS_PROGRESS

@router.get("/{complaint_id}", response_model=ComplaintDetailOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    complaint = repo.create_complaint(db, payload)
    if payload.ai_risk_level:
        repo.add_audit_log(
            db, complaint.id, "Risk classification generated",
            new_value=payload.ai_risk_level, actor="ai.system",
        )
    return complaint


@router.put("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return repo.update_complaint(db, complaint, payload)


@router.delete("/{complaint_id}", status_code=204)
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    repo.delete_complaint(db, complaint)


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_text(payload: AnalyzeTextRequest, db: Session = Depends(get_db)):
    """Main AI endpoint: text -> LangGraph -> structured analysis."""
    llm = _get_llm()
    try:
        result = run_analysis(payload.text, llm, db=db)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - never leak stack traces
        raise HTTPException(status_code=500, detail="Complaint analysis failed. Please try again.")
    return result


@router.post("/analyze-document", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile, db: Session = Depends(get_db)):
    """Multipart upload (PDF/TXT) -> text extraction -> LangGraph analysis."""
    text = await extract_text_from_upload(file)  # raises 400 with a clear message
    llm = _get_llm()
    try:
        result = run_analysis(text, llm, db=db)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Complaint analysis failed. Please try again.")
    return result



@router.post("/{complaint_id}/risk-assessment", response_model=AnalysisResponse)
def risk_assessment_for_existing(complaint_id: int, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    llm = _get_llm()
    text = complaint.description or ""
    try:
        result = run_analysis(text, llm, db=db)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    repo.save_ai_assessment(db, complaint_id, result, result.get("model_used", ""))
    repo.add_audit_log(db, complaint_id, "AI analysis completed", actor="ai.system")
    return result


@router.get("/{complaint_id}/duplicates")
def duplicates(complaint_id: int, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    from app.agents.duplicate_agent import detect_duplicates

    state = {
        "raw_text": complaint.description or "",
        "extracted_data": {
            "product_name": complaint.product_name,
            "batch_number": complaint.batch_number,
            "complaint_type": complaint.complaint_type,
            "description": complaint.description,
        },
        "errors": [],
    }
    return detect_duplicates(state, db)


@router.post("/{complaint_id}/capa", response_model=CapaActionOut, status_code=201)
def add_capa(complaint_id: int, payload: CapaActionCreate, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return repo.add_capa_action(db, complaint_id, payload.action_type, payload.description, payload.source)


@router.post("/{complaint_id}/root-cause")
def root_cause_for_existing(complaint_id: int, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    llm = _get_llm()
    try:
        result = run_analysis(complaint.description or "", llm, db=None)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {
        "root_cause_analysis": result.get("root_cause_analysis"),
        "capa_recommendations": result.get("capa_recommendations"),
        "errors": result.get("errors", []),
    }
