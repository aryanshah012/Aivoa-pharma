# Interview Guide — AIVOA PharmaQMS AI

Short, simple answers an intern can confidently deliver in an interview.

## Domain
- **What is a QMS?** A Quality Management System — the documented processes a
  pharmaceutical company uses to ensure products meet quality standards (e.g. ICH Q10).
- **What is a pharmaceutical customer complaint?** Any written/verbal communication
  claiming a product is defective or of unacceptable quality. QMS requires every
  complaint to be logged, investigated and answered.
- **What are API and FDF?** API = Active Pharmaceutical Ingredient (the drug itself);
  FDF = Finished Dosage Form (the tablet/capsule/syrup the patient takes).

## Tech choices
- **Why FastAPI?** Async, automatic OpenAPI docs, Pydantic validation — ideal for
  AI-backed APIs that take seconds per request.
- **Why React + Redux Toolkit?** Predictable state for a workflow app: the complaint
  draft, AI analysis result and filters all live in one store, easy to trace.
- **Why LangGraph?** The analysis is a pipeline of 7 steps with shared state. LangGraph
  makes the pipeline explicit, testable node-by-node, and lets optional agents fail
  gracefully without breaking the run.
- **Why PostgreSQL?** Relational integrity for QMS records, JSON columns for flexible
  AI payloads, production-grade reliability.
- **Why structured LLM output?** We validate every response against a Pydantic schema.
  Structured JSON + validation + one repair retry makes AI output dependable enough
  to pre-fill a regulated form.

## AI design
- **Why human-in-the-loop?** AI never saves a complaint by itself. It extracts and
  suggests; a qualified Quality person reviews, edits and approves. The UI labels every
  AI field and shows "AI-generated suggestion — Quality review required."
- **Why separate agents/nodes?** Small focused prompts beat one giant prompt: each node
  has one job, its own prompt, its own schema, and can fail independently.
- **Deterministic vs AI:** required-field checks, SQL search and similarity scoring are
  plain Python; only extraction, reasoning text, summaries and suggestions use the LLM.
- **What is CAPA?** Corrective And Preventive Action — fixing the current issue and
  preventing recurrence. The AI drafts suggestions; only authorized Quality personnel
  approve the final CAPA.
- **How does duplicate detection work?** Explainable scoring, no vector DB: same batch
  (0.45) + same product (0.25) + same category (0.15) + TF-IDF cosine similarity of
  descriptions (0.15). Matches above 0.35 are returned with reasons.
- **How does risk classification work?** The LLM assesses 5 dimensions (overall,
  patient safety, product quality, regulatory, business) with fact-based reasoning and a
  confidence score. Deterministic rule guardrails clamp unsafe outputs (adverse event
  reported ⇒ at least High; contamination ⇒ Critical triage).

## Reliability & failure
- **What happens if Groq fails?** Invalid key/quota/model-unavailable → clear 502 with a
  human-readable message. Malformed JSON → one repair retry. If an optional agent still
  fails, its result is null with a soft error; other results are returned. Only
  extraction is blocking.
- **How would this scale?** Run analysis as a background job (Celery/RQ) with a job
  status endpoint; cache duplicate-detection vectors; move TF-IDF to embeddings in
  Postgres (pgvector) at larger volumes.
- **How would AI output be more reliable?** Schema-constrained decoding (Groq JSON
  mode), few-shot examples, temperature 0, output validators, and evaluation harness
  with golden complaints.
- **How to add authentication?** OAuth2/JWT (e.g. Keycloak), users table, login
  endpoint issuing tokens, `get_current_user` dependency on protected routes.
- **RBAC?** Roles: Quality Associate (log/edit), QA Reviewer (approve risk/CAPA),
  Admin. Enforce role checks in route dependencies and hide actions in the UI.
- **Audit integrity?** Append-only audit table (no updates/deletes), hash-chained
  entries, DB-level triggers, and a separate audit service account.
- **OCR?** Add a vision-capable model (e.g. Llama 3.2 Vision) or Tesseract for scanned
  PDFs; keep pypdf as the fast path for digital PDFs.

## Limitations (be honest)
Single-tenant, no auth, SQLite fallback in dev, no background jobs, English-only,
no real document storage (attachments table exists but files aren't persisted yet).
