# Agri Triage Agent

FastAPI backend with a React frontend for agriculture support triage.

## Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

## Frontend (React + Vite)

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

## API used by frontend

- `POST /ask`
- `POST /ask/image` (multipart form-data: `image`, optional `note`)
- `GET /queries?limit=20`
- `GET /queries/{id}`
- Request body:
```json
{ "msg": "My crop leaves are yellow" }
```
- Response includes:
  - `classification` (`intent`, `urgency`)
  - `entities`
  - `answer`
  - `db_id`

## Frontend features

- Text triage input
- Image triage upload
- Saved query history from database
