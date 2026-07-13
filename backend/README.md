# Backend

Python FastAPI backend for the Healthcare Text-to-SQL Assistant.

## Why Python

This project is data/NLP-heavy, so Python keeps the backend close to the evaluation scripts, prompt logic, LLM calls, and future fine-tuning workflow.

## Run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3000
```

The backend reads `.env` from the project root when present. The default database URL is:

```text
postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare
```

## API

```http
GET /health
POST /text-to-sql/query
```

Request:

```json
{
  "question": "Top 10 bệnh phổ biến nhất là gì?",
  "execute": true
}
```

If `VLLM_BASE_URL` and `VLLM_MODEL` are not set, the API uses a small fallback SQL router for basic demo questions.
