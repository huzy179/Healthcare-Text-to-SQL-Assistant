# Text-to-SQL Pipeline

This project uses MCP as the runtime surface for Text-to-SQL.

## Pipeline

```text
Natural language question
-> MCP client / LLM
-> get_schema
-> schema-aware prompt inside the LLM client
-> generated PostgreSQL SELECT SQL
-> validate_readonly_sql
-> check_sql_syntax
-> run_readonly_query
-> explain_query_result
-> final natural language answer
```

## Schema-Aware Prompting

The LLM should call `get_schema` before writing SQL. The returned schema includes:

- MVP table names.
- Column names and PostgreSQL data types.
- Common join hints, such as `encounters.patient -> patients.id`.

Prompting rules:

- Generate PostgreSQL only.
- Return a single `SELECT` statement.
- Use only tables and columns returned by `get_schema`.
- Prefer explicit joins using documented join keys.
- Add `LIMIT` for list-style queries.
- Treat `observations.value` as text unless a numeric filter/cast is required.

## SQL Safety

`validate_readonly_sql` enforces:

- Query must start with `SELECT`.
- Query must be a single statement.
- DDL/DML keywords are blocked.
- Referenced tables must be in the MVP schema.

`check_sql_syntax` sends `EXPLAIN <sql>` to PostgreSQL after safety validation, so syntax and many schema errors are caught before execution.

## Read-Only Database Connection

All query execution uses:

```text
postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare
```

`run_readonly_query` also sets a PostgreSQL statement timeout and applies `MCP_MAX_ROWS` to queries without an explicit `LIMIT`.

## Natural Language Explanation

`run_readonly_query` returns a short `explanation` field. `explain_query_result` can also be called separately when the LLM needs a compact Vietnamese explanation from `{question, sql, rows}`.

## Evaluation

Use:

```bash
python3 scripts/evaluate_text_to_sql.py
```

Metrics:

- Exact Match Accuracy.
- Execution Accuracy.
- Average response time.

For generated SQL from an external LLM/MCP client, pass a JSONL file:

```bash
python3 scripts/evaluate_text_to_sql.py --generated-file outputs/generated_sql.jsonl
```

Expected generated file format:

```json
{"id":"q001","generated_sql":"SELECT COUNT(*) AS total_patients FROM patients;"}
```

Failures are summarized under SQL error analysis in `reports/text_to_sql_eval_summary.md`.
