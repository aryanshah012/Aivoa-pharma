export type Risk = 'Critical' | 'High' | 'Medium' | 'Low';
export type Status = 'New' | 'Pending Triage' | 'Open' | 'Under Investigation' | 'CAPA Required' | 'Resolved' | 'Closed';

export interface Complaint {
  id: number; complaint_number: string;
  complaint_source?: string | null;
  customer_name: string; customer_email?: string | null; customer_phone?: string | null;
  customer_location?: string | null; country?: string | null;
  product_name: string; product_type?: string | null; strength_or_grade?: string | null;
  batch_number?: string | null; lot_number?: string | null;
  manufacturing_date?: string | null; expiry_date?: string | null;
  complaint_type: string; complaint_date?: string | null; received_date?: string | null;
  description: string; quantity_affected?: number | null; market?: string | null;
  patient_impact?: string | null; adverse_event_reported: boolean;
  initial_severity?: 'Critical' | 'Major' | 'Minor' | null;
  priority?: 'Urgent' | 'High' | 'Medium' | 'Low' | null;
  ai_risk_level?: Risk | null; final_risk_level?: Risk | null;
  status: Status; ai_summary?: string | null; ai_populated_fields?: string[] | null;
  created_at: string; updated_at: string; resolved_at?: string | null;
  audit_logs?: AuditEntry[]; capa_actions?: CapaAction[];
}
export interface ExtractedData { [key: string]: string | number | boolean | null; }
export interface Completeness { score: number; status: 'Complete' | 'Incomplete';
  present_fields: string[]; missing_fields: string[]; recommended_questions: string[]; }
export interface RiskAssessment { overall_risk: Risk; patient_safety: Risk; product_quality: Risk;
  regulatory_impact: Risk; business_impact: Risk; confidence: number;
  reasoning: string[]; recommended_actions: string[]; }
export interface DuplicateMatch { complaint_id: number; complaint_number: string;
  similarity_score: number; product_name?: string; batch_number?: string;
  complaint_type?: string; reason: string; }
export interface RootCauseAnalysis { possible_causes: { cause: string; confidence: string; rationale: string }[];
  recommended_evidence: string[]; }
export interface CapaRecommendations { corrective_actions: string[]; preventive_actions: string[];
  verification_suggestions: string[]; }
export interface Summary { short_summary: string; management_summary: string; }
export interface Analysis { extracted_data: ExtractedData; completeness: Completeness | null;
  risk_assessment: RiskAssessment | null; duplicate_matches: DuplicateMatch[];
  root_cause_analysis: RootCauseAnalysis | null; capa_recommendations: CapaRecommendations | null;
  summary: Summary | null; model_used: string; errors: string[]; }
export interface ComplaintDraft extends Partial<Complaint> { ai_populated_fields?: string[]; ai_risk_level?: Risk | null; }
export interface DashboardStats { total_complaints: number; open_complaints: number;
  under_investigation: number; critical_high_risk: number; closed_complaints: number;
  avg_resolution_days: number | null; }
export interface AuditEntry { id: number; event_type: string; detail?: string | null;
  old_value?: string | null; new_value?: string | null; actor: string; created_at: string; }
export interface CapaAction { id: number; complaint_id: number; action_type: 'Corrective' | 'Preventive';
  description: string; source: 'AI' | 'Human'; status: string; created_at: string; }
