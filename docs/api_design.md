# API Design

Planned endpoint:

```http
POST /text-to-sql/query
```

Request:

```json
{
  "question": "Top 10 bệnh phổ biến nhất là gì?"
}
```

Response:

```json
{
  "question": "Top 10 bệnh phổ biến nhất là gì?",
  "sql": "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;",
  "columns": ["description", "total"],
  "rows": [],
  "execution_time_ms": 0,
  "explanation": ""
}
```
