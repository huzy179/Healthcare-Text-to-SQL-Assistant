# Backend

NestJS backend for the Healthcare Text-to-SQL Assistant.

## Modules

- `text-to-sql`: API flow from question to SQL result.
- `database`: PostgreSQL connection and query execution.
- `sql-validator`: SQL safety checks.
- `llm`: vLLM/OpenAI-compatible client with a small local fallback.

## Run

```bash
npm install
npm run start:dev
```

The backend expects `DATABASE_URL` from the root `.env` or shell environment.

## API

```http
POST /text-to-sql/query
```

Request:

```json
{
  "question": "Top 10 bệnh phổ biến nhất là gì?"
}
```
