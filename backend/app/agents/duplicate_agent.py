"""Agent 4 — duplicate / similar complaint detection.

Deterministic, explainable similarity: exact batch/product/category matches
combined with TF-IDF cosine similarity on descriptions (scikit-learn).
No vector DB required.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:  # graceful degradation: deterministic signals only
    _SKLEARN_AVAILABLE = False

BATCH_WEIGHT = 0.45
PRODUCT_WEIGHT = 0.25
TYPE_WEIGHT = 0.15
TEXT_WEIGHT = 0.15
SIMILARITY_THRESHOLD = 0.35


def _text_similarity(texts: list[str]) -> list[float]:
    """Cosine similarity of the first text against the rest. [] if unavailable."""
    if not _SKLEARN_AVAILABLE or len(texts) < 2:
        return []
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform(texts)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return [float(s) for s in sims]
    except ValueError:
        return []


def detect_duplicates(state: dict, db: Session | None) -> dict:
    extracted = state.get("extracted_data") or {}
    errors: list = list(state.get("errors", []))
    matches: list[dict] = []

    if db is None:
        return {"duplicate_matches": matches, "errors": errors}

    existing = list(db.execute(select(Complaint)).scalars().all())
    if not existing:
        return {"duplicate_matches": matches, "errors": errors}

    new_text = extracted.get("description") or state["raw_text"]
    sims = _text_similarity([new_text] + [c.description for c in existing])

    for idx, complaint in enumerate(existing):
        score = 0.0
        reasons: list[str] = []

        if (
            extracted.get("batch_number")
            and complaint.batch_number
            and extracted["batch_number"].strip().lower() == complaint.batch_number.strip().lower()
        ):
            score += BATCH_WEIGHT
            reasons.append("same batch number")

        new_product = (extracted.get("product_name") or "").strip().lower()
        old_product = (complaint.product_name or "").strip().lower()
        if new_product and old_product and (
            new_product in old_product or old_product in new_product
        ):
            score += PRODUCT_WEIGHT
            reasons.append("same product")

        if (
            extracted.get("complaint_type")
            and complaint.complaint_type
            and extracted["complaint_type"] == complaint.complaint_type
        ):
            score += TYPE_WEIGHT
            reasons.append("same complaint category")

        text_sim = sims[idx] if idx < len(sims) else 0.0
        score += TEXT_WEIGHT * text_sim
        if text_sim > 0.5:
            reasons.append("very similar description text")

        score = round(min(score, 1.0), 2)
        if score >= SIMILARITY_THRESHOLD and reasons:
            matches.append(
                {
                    "complaint_id": complaint.id,
                    "complaint_number": complaint.complaint_number,
                    "similarity_score": score,
                    "product_name": complaint.product_name,
                    "batch_number": complaint.batch_number,
                    "complaint_type": complaint.complaint_type,
                    "reason": "Matched on " + ", ".join(reasons),
                }
            )

    matches.sort(key=lambda m: m["similarity_score"], reverse=True)
    return {"duplicate_matches": matches[:5], "errors": errors}
