"""Shared domain constants for the QMS application."""

# --- Enums (mirrored on the frontend in src/types/) ---

COMPLAINT_SOURCES = ["Email", "Phone", "Distributor", "Web", "Field Representative", "Other"]

PRODUCT_TYPES = ["API", "FDF", "Tablet", "Capsule", "Injection", "Syrup", "Other"]

COMPLAINT_TYPES = [
    "Physical Defect",
    "Packaging Defect",
    "Labeling Issue",
    "Potency Issue",
    "Contamination",
    "Missing Product",
    "Wrong Product",
    "Adverse Event",
    "Delivery/Transport",
    "Other",
]

SEVERITIES = ["Critical", "Major", "Minor"]
PRIORITIES = ["Urgent", "High", "Medium", "Low"]
RISK_LEVELS = ["Critical", "High", "Medium", "Low"]

STATUSES = [
    "New",
    "Pending Triage",
    "Open",
    "Under Investigation",
    "CAPA Required",
    "Resolved",
    "Closed",
]

# --- Deterministic completeness rules ---
# Maps a semantic field -> (form field label, complaint model attribute).
REQUIRED_FIELDS = {
    "customer_name": "Customer name",
    "product_name": "Product name",
    "complaint_type": "Complaint category",
    "description": "Complaint description",
}

IMPORTANT_FIELDS = {
    "batch_number": "Batch number",
    "complaint_date": "Complaint date",
    "received_date": "Received date",
    "manufacturing_date": "Manufacturing date",
    "expiry_date": "Expiry date",
    "quantity_affected": "Quantity affected",
    "customer_email": "Customer email",
    "market": "Market",
}

# Default action labels used by the audit trail.
AUDIT_EVENTS = [
    "Complaint created",
    "AI analysis completed",
    "Risk classification generated",
    "Complaint edited",
    "Risk manually changed",
    "Complaint status changed",
    "CAPA added",
    "Complaint saved",
]
