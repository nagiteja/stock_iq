# StockIQ

Single-stock analysis web app powered by FastAPI, React, Polygon, and Gemini.

## Architecture

### High-level flow
1. User enters a ticker in the React UI.
2. Frontend sends `POST /api/analyze` to the FastAPI backend.
3. Backend pulls company data, price aggregates, and latest financials from Polygon.
4. Backend computes derived metrics (returns, volatility, drawdown, volume).
5. Gemini agents generate the markdown report and a scorecard payload for the UI.
6. Frontend renders the markdown report and scorecard.

```
Browser -> React UI -> /api/analyze -> FastAPI -> Polygon + Gemini
      <- report_markdown + scorecard + metrics <-
```

### Repository structure
```
.
├── agent_app.py
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── orchestrator.py
│   │   │   └── prompts.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── metrics.py
│   │   │   └── polygon.py
│   │   ├── static/
│   │   │   └── .gitkeep
│   │   ├── api.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ReportView.tsx
│   │   │   └── TickerForm.tsx
│   │   └── App.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile
├── NOTEBOOK_LOGIC.md
├── railway.toml
└── README.md
```

### Component overview
- **Frontend (Vite + React)**: `frontend/src`
  - `App.tsx` orchestrates UI state and calls `/api/analyze`.
  - `components/TickerForm.tsx` captures ticker input.
  - `components/ReportView.tsx` renders markdown and scorecard (via `react-markdown`).
- **Backend (FastAPI)**: `backend/app`
  - `main.py` registers routes and serves the built SPA from `app/static`.
  - `api.py` exposes `POST /api/analyze` with error handling.
  - `models/schemas.py` defines request/response contracts.
  - `core/config.py` loads env vars (`GEMINI_API_KEY`, `POLYGON_API_KEY`).
  - `services/polygon.py` fetches Polygon data (company, aggregates, financials).
  - `services/metrics.py` computes price/fundamental metrics.
  - `agents/orchestrator.py` runs Gemini agents and assembles the final report:
    - `analysis_agent` produces the markdown report.
    - `score_agent` produces the UI scorecard (score + time horizons).
    - `technical_agent` and `fundamental_agent` generate structured diagnostics.
    - `compiler_agent` combines technical + fundamental diagnostics into the
      Technical+Fundamental scorecard shown in the UI.
- **External services**
  - Polygon REST API for market data.
  - Gemini via Google ADK + GenAI SDK for report generation and scoring.

### Agent lineup and connections
There are **5 Gemini agents**:
- `analysis_agent`
- `score_agent`
- `technical_agent`
- `fundamental_agent`
- `compiler_agent`

Connection flow:
```
Polygon data + metrics
  ├─> analysis_agent  ──> report_markdown
  ├─> score_agent     ──> scorecard
  ├─> technical_agent ─┐
  └─> fundamental_agent┴─> compiler_agent ──> compiler_scorecard
```

### Deployment model
- `Dockerfile` builds the React app, then copies `frontend/dist` into
  `backend/app/static` so FastAPI serves the SPA and assets.
- `railway.toml` uses the Dockerfile build on Railway.

### Request/response shape
`POST /api/analyze` accepts `{ "ticker": "AAPL" }` and returns:
- `report_markdown`: investor-style markdown report
- `metrics`: computed price/fundamental metrics
- `scorecard`: UI scorecard with keys `score`, `short_term`, `mid_term`,
  `long_term`, and `rationale`
- `as_of`: ISO timestamp

## Local Development

### Backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your_gemini_key"
export POLYGON_API_KEY="your_polygon_key"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` to `http://localhost:8000`.

## Environment Variables
- `GEMINI_API_KEY` (required)
- `POLYGON_API_KEY` (required)

## Python Version
Use Python 3.11+ locally to avoid dependency warnings from `google-auth` and `urllib3`.

## Railway Deployment
1. Create a new Railway project from this repo.
2. Add environment variables `GEMINI_API_KEY` and `POLYGON_API_KEY`.
3. Deploy. Railway will build the Dockerfile and run Uvicorn with `$PORT`.

## API
`POST /api/analyze`
```json
{ "ticker": "AAPL" }
```

## Quick Local Tests
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}'
```