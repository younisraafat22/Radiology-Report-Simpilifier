# Radiology Report Simplifier

Public-facing AI app to simplify de-identified radiology reports into patient-friendly language.

## MVP scope
- Backend: FastAPI service with report simplification endpoint.
- Frontend: Next.js app ready for Vercel deployment.
- Data policy: synthetic or de-identified text only.

## Project structure
- `backend/` FastAPI API and services.
- `frontend/` Next.js UI.
- `data/` dataset artifacts for eval.

## Run backend locally
1. Create a Python environment.
2. Install dependencies from `backend/requirements.txt`.
3. Optional: copy `backend/.env.example` to `.env` and set Hugging Face values.
4. Start server:
   - `uvicorn app.main:app --reload --app-dir backend`

## Hugging Face mode (optional)
- Default behavior uses deterministic fallback output.
- To enable model-based generation:
   1. Set `USE_HF_INFERENCE=true`
   2. Set `HF_API_TOKEN` with your Hugging Face token
   3. Optionally tune `HF_MODEL_ID`, `HF_MAX_NEW_TOKENS`, `HF_TEMPERATURE`

   ## Run frontend locally
   1. In `frontend/`, install dependencies:
      - `npm install`
   2. Copy `.env.local.example` to `.env.local`.
   3. Start frontend:
      - `npm run dev`

   ## Test backend
   Run tests from `backend/`:
   - `pytest`

   ## Run evaluation harness
   Run from project root:
   - `python -m backend.scripts.run_eval`

   This reads `data/eval/eval_cases.jsonl` and writes `data/eval/eval_report.json`.

   ## Deploy backend to Fly.io
   1. Install Fly CLI and login.
   2. In `backend/`, set secrets:
      - `fly secrets set USE_HF_INFERENCE=true HF_API_TOKEN=...`
   3. Deploy:
      - `fly deploy`

   ## Deploy frontend to Vercel
   1. Import `frontend/` as a Vercel project.
   2. Set env var:
      - `NEXT_PUBLIC_API_BASE_URL=https://<your-fly-app>.fly.dev`
   3. Deploy.

## Current API
- `GET /health`
- `POST /api/v1/simplify`
