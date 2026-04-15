# Radiology Report Simplifier

Public-facing AI app to simplify de-identified radiology reports into patient-friendly language.

## MVP scope
- Backend: FastAPI service with report simplification and image text extraction endpoints.
- Frontend: Next.js app ready for Vercel deployment.
- Data policy: synthetic or de-identified text only.

## Project structure
- `backend/` FastAPI API and services.
- `frontend/` Next.js UI.
- `data/` dataset artifacts for eval.

## New features
- Image upload OCR in UI (PNG/JPG/WebP) to extract report text using backend Tesseract OCR (`pytesseract` + `Pillow`).
- Clipboard image paste support in the frontend report form.
- Radiology-domain guard that rejects non-radiology text with a clear `400` response.
- Realistic de-identified sample reports:
  - `data/samples/realistic_radiology_sample_reports.md`

## Run backend locally
1. Create a Python environment.
2. Install dependencies from `backend/requirements.txt`.
3. Copy `backend/.env.example` to `.env` and set required values.
4. Start server:
   - `uvicorn app.main:app --reload --app-dir backend`

## Required backend variables
1. `HF_API_TOKEN`
2. `HF_MODEL_ID`
3. `HF_MAX_NEW_TOKENS`
4. `HF_TEMPERATURE`
5. `OCR_LANG` (default `eng`)
6. `OCR_MAX_SIDE` (default `2200`)

If LLM inference fails, `/api/v1/simplify` returns `503`.

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
4. Set required secrets:
   - `fly secrets set HF_API_TOKEN=...`
   - `fly secrets set HF_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct`
   - `fly secrets set HF_MAX_NEW_TOKENS=400`
   - `fly secrets set HF_TEMPERATURE=0.2`
   - `fly secrets set OCR_LANG=eng`
   - `fly secrets set OCR_MAX_SIDE=2200`
   - `fly secrets set CORS_ALLOW_ORIGINS=https://<your-vercel-domain>`
5. Deploy:
   - `fly deploy`
6. Verify backend:
   - `curl https://<your-fly-app>.fly.dev/health`

### Fly memory note (important for OCR)
- `backend/fly.toml` is set to `2gb` memory.
- If you still see OOM restarts, increase memory:
  - `fly scale memory 4096 -a <your-fly-app>`

## Deploy frontend to Vercel
1. Import `frontend/` as a Vercel project.
2. Framework preset: `Next.js`.
3. Set environment variable in Vercel:
   - `BACKEND_API_BASE_URL=https://<your-fly-app>.fly.dev`
   - (optional) `NEXT_PUBLIC_API_BASE_URL=https://<your-fly-app>.fly.dev`
4. Deploy.
5. Verify frontend:
   - Open the Vercel URL and submit a sample report.
6. If you get `503` in UI, verify Fly secrets and backend logs.

## Troubleshooting

### 503 from `/api/v1/simplify`
1. Confirm `HF_API_TOKEN` is valid and has Inference permission.
2. Confirm selected model is available on Hugging Face router.
3. Open Fly logs and inspect the backend error message:
   - `fly logs -a <your-fly-app>`

### 503 from `/api/v1/extract-text`
1. Confirm image is valid and readable.
2. Confirm OCR settings (`OCR_LANG`, `OCR_MAX_SIDE`).
3. Check Fly logs for OCR errors or memory pressure.

### Failed to fetch from frontend
1. Confirm frontend env value:
   - `BACKEND_API_BASE_URL=https://<your-fly-app>.fly.dev`
2. Confirm backend CORS env value:
   - `CORS_ALLOW_ORIGINS=https://<your-vercel-domain>`
3. Confirm backend is healthy:
   - `https://<your-fly-app>.fly.dev/health`

## Current API
- `GET /health`
- `POST /api/v1/simplify`
- `POST /api/v1/extract-text`
