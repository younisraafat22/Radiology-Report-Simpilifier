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
3. Copy `backend/.env.example` to `.env` and set Hugging Face values.
4. Start server:
   - `uvicorn app.main:app --reload --app-dir backend`

## LLM mode (required)
- This project is now strictly LLM-based.
- If `HF_API_TOKEN` is missing or inference fails, `/api/v1/simplify` returns `503`.
- Required backend variables:
   1. `HF_API_TOKEN`
   2. `HF_MODEL_ID`
   3. `HF_MAX_NEW_TOKENS`
   4. `HF_TEMPERATURE`

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
   1. Install Fly CLI and login:
      - `fly auth login`
   2. Go to backend folder:
      - `cd backend`
   3. Create Fly app (one time):
      - `fly launch --no-deploy`
   4. Set required LLM secrets:
      - `fly secrets set HF_API_TOKEN=...`
      - `fly secrets set HF_MODEL_ID=google/flan-t5-large`
      - `fly secrets set HF_MAX_NEW_TOKENS=400`
      - `fly secrets set HF_TEMPERATURE=0.2`
   5. Deploy:
      - `fly deploy`
   6. Verify backend:
      - `curl https://<your-fly-app>.fly.dev/health`

   ## Deploy frontend to Vercel
   1. Import `frontend/` as a Vercel project.
   2. Framework preset: `Next.js`.
   3. Set environment variable in Vercel:
      - `NEXT_PUBLIC_API_BASE_URL=https://<your-fly-app>.fly.dev`
   4. Deploy.
   5. Verify frontend:
      - Open the Vercel URL and submit a sample report.
   6. If you get 503 in UI, verify Fly secrets are set correctly.

## Current API
- `GET /health`
- `POST /api/v1/simplify`
