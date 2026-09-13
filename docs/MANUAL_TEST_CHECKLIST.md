# Manual Test Checklist

1. Start backend (`uvicorn app.main:app --reload`) and frontend (`npm run dev`).
2. Open http://localhost:5173 → Dashboard shows 6 stat cards + recent complaints (after seeding).
3. Log Customer Complaint → paste text from `sample_data/complaints/demo_complaint_email.txt`.
4. Click **Analyze with AI** → progress steps animate → "Analysis completed" disclaimer.
5. Form auto-populates; AI-extracted fields highlighted with blue tint + "AI extracted" tag.
6. Verify: Customer = CityCare Pharmacy, Product = Paracetamol Tablets, Batch = PCM240812,
   Category = Physical Defect, Quantity = 15, Adverse Event = No.
7. Check right panel: completeness %, risk assessment, duplicates (CC-2026-0001/0008),
   summary, investigation suggestions, CAPA suggestions — each with the AI disclaimer.
8. Edit any field (e.g. change quantity to 20) — must remain editable.
9. Save Complaint → redirected to list → new complaint appears with `CC-2026-XXXX` number.
10. Open its detail page → change status and final risk → audit trail records both events
    with old → new values.
11. Filters: search "Paracetamol", filter Risk=High, Status=New — table updates.
12. Upload a `.txt` complaint via drag/drop → analysis runs.
13. Upload a `.exe` or empty file → clear human-readable error, no crash.
14. Stop backend → click Analyze → UI shows a friendly network error.
15. `docker compose up` with a valid `GROQ_API_KEY` → full stack runs.
