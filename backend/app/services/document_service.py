"""Document text extraction (PDF / TXT). No OCR — simple, reliable, testable."""
from fastapi import UploadFile, HTTPException

from app.core.config import get_settings

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}
MIN_TEXT_LENGTH = 20


async def extract_text_from_upload(file: UploadFile) -> str:
    """Validate and extract text from an uploaded complaint document."""
    settings = get_settings()
    filename = file.filename or "upload"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Supported: PDF, TXT.",
        )

    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed: {settings.MAX_UPLOAD_MB} MB.",
        )
    if not raw.strip():
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")

    if ext == ".txt":
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Could not decode TXT file.") from exc
    else:
        text = _extract_pdf_text(raw, filename)

    text = text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from the document "
                   "(it may be a scanned image — OCR is not supported).",
        )
    return text


def _extract_pdf_text(raw: bytes, filename: str) -> str:
    from io import BytesIO

    from pypdf import PdfReader  # imported lazily so TXT uploads never require it

    try:
        reader = PdfReader(BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400, detail=f"PDF extraction failed for '{filename}'."
        ) from exc
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No selectable text found in the PDF (scanned images are not supported).",
        )
    return text
