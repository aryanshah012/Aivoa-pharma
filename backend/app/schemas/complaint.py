"""Pydantic schemas: request/response contracts shared with the React frontend.

These schemas are the single source of truth mirrored by src/types/index.ts.
"""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------- Complaint ----------------

class ComplaintBase(BaseModel):
    complaint_source: Optional[str] = None
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_location: Optional[str] = Field(None, max_length=200)
    country: Optional[str] = Field(None, max_length=100)

    product_name: str = Field(..., min_length=1, max_length=200)
    product_type: Optional[str] = Field(None, max_length=50)
    strength_or_grade: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    lot_number: Optional[str] = Field(None, max_length=100)
    manufacturing_date: Optional[str] = Field(None, max_length=20)
    expiry_date: Optional[str] = Field(None, max_length=20)

    complaint_type: str = Field(..., min_length=1, max_length=100)
    complaint_date: Optional[str] = Field(None, max_length=20)
    received_date: Optional[str] = Field(None, max_length=20)
    description: str = Field(..., min_length=1)
    quantity_affected: Optional[int] = Field(None, ge=0)
    market: Optional[str] = Field(None, max_length=100)

    patient_impact: Optional[str] = Field(None, max_length=500)
    adverse_event_reported: bool = False

    initial_severity: Optional[Literal["Critical", "Major", "Minor"]] = None
    priority: Optional[Literal["Urgent", "High", "Medium", "Low"]] = None

    final_risk_level: Optional[Literal["Critical", "High", "Medium", "Low"]] = None
    status: Optional[str] = "New"
    ai_summary: Optional[str] = None
    ai_populated_fields: Optional[list[str]] = None


class ComplaintCreate(ComplaintBase):
    """Payload used when saving a complaint from the UI form."""
    ai_risk_level: Optional[str] = None


class ComplaintUpdate(BaseModel):
    """All fields optional for partial updates (human review/edit)."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_location: Optional[str] = None
    country: Optional[str] = None

    product_name: Optional[str] = None
    product_type: Optional[str] = None
    strength_or_grade: Optional[str] = None
    batch_number: Optional[str] = None
    lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    received_date: Optional[str] = None
    description: Optional[str] = None
    quantity_affected: Optional[int] = None
    market: Optional[str] = None

    patient_impact: Optional[str] = None
    adverse_event_reported: Optional[bool] = None

    initial_severity: Optional[str] = None
    priority: Optional[str] = None

    ai_risk_level: Optional[str] = None
    final_risk_level: Optional[str] = None
    status: Optional[str] = None
    ai_summary: Optional[str] = None


class ComplaintOut(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    ai_risk_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


# ---------------- AI analysis ----------------

class ExtractedData(BaseModel):
    """Strict structured output of the extraction agent. Null = not found (never fabricated)."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_location: Optional[str] = None
    country: Optional[str] = None

    product_name: Optional[str] = None
    product_type: Optional[Literal["API", "FDF", "Tablet", "Capsule", "Injection", "Syrup", "Other"]] = None
    strength_or_grade: Optional[str] = None
    batch_number: Optional[str] = None
    lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    received_date: Optional[str] = None
    description: Optional[str] = None
    quantity_affected: Optional[int] = None
    market: Optional[str] = None

    patient_impact: Optional[str] = None
    adverse_event_reported: Optional[bool] = None


class CompletenessResult(BaseModel):
    score: float = Field(..., ge=0, le=100)
    status: Literal["Complete", "Incomplete"]
    present_fields: list[str]
    missing_fields: list[str]
    recommended_questions: list[str]


class RiskAssessment(BaseModel):
    overall_risk: Literal["Critical", "High", "Medium", "Low"]
    patient_safety: Literal["Critical", "High", "Medium", "Low"]
    product_quality: Literal["Critical", "High", "Medium", "Low"]
    regulatory_impact: Literal["Critical", "High", "Medium", "Low"]
    business_impact: Literal["Critical", "High", "Medium", "Low"]
    confidence: float = Field(..., ge=0, le=1)
    reasoning: list[str]
    recommended_actions: list[str]


class DuplicateMatch(BaseModel):
    complaint_id: int
    complaint_number: str
    similarity_score: float
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    complaint_type: Optional[str] = None
    reason: str


class PossibleCause(BaseModel):
    cause: str
    confidence: Literal["High", "Medium", "Low"]
    rationale: str


class RootCauseAnalysis(BaseModel):
    possible_causes: list[PossibleCause]
    recommended_evidence: list[str]


class CapaRecommendations(BaseModel):
    corrective_actions: list[str]
    preventive_actions: list[str]
    verification_suggestions: list[str]


class SummaryResult(BaseModel):
    short_summary: str
    management_summary: str


class AnalysisResponse(BaseModel):
    """Full response of POST /api/complaints/analyze (LangGraph END state)."""
    extracted_data: ExtractedData
    completeness: Optional[CompletenessResult] = None
    risk_assessment: Optional[RiskAssessment] = None
    duplicate_matches: list[DuplicateMatch] = []
    root_cause_analysis: Optional[RootCauseAnalysis] = None
    capa_recommendations: Optional[CapaRecommendations] = None
    summary: Optional[SummaryResult] = None
    model_used: str
    errors: list[str] = []


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=10)


# ---------------- CAPA / misc ----------------

class CapaActionCreate(BaseModel):
    action_type: Literal["Corrective", "Preventive"]
    description: str = Field(..., min_length=1)
    source: Literal["AI", "Human"] = "Human"


class CapaActionOut(CapaActionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_id: int
    status: str
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_id: int
    event_type: str
    detail: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    actor: str
    created_at: datetime


class ComplaintDetailOut(ComplaintOut):
    audit_logs: list[AuditLogOut] = []
    capa_actions: list[CapaActionOut] = []
    ai_assessments: list[dict[str, Any]] = []


class DashboardStats(BaseModel):
    total_complaints: int
    open_complaints: int
    under_investigation: int
    critical_high_risk: int
    closed_complaints: int
    avg_resolution_days: Optional[float] = None


class HealthOut(BaseModel):
    status: str
    model: str
    llm_configured: bool
