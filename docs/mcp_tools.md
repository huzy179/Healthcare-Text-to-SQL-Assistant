# MCP Tools

The MCP server lives in `mcp_server/` and exposes database tools over stdio.

## Tools

- `get_schema`: returns public MVP tables, columns, types, and common join hints.
- `validate_readonly_sql`: checks that SQL is a safe single-statement PostgreSQL `SELECT`.
- `check_sql_syntax`: runs PostgreSQL `EXPLAIN` after safety validation.
- `run_readonly_query`: validates and executes SQL with the readonly PostgreSQL user.
- `explain_query_result`: generates a short Vietnamese natural language explanation.
- `ask_database`: handles common demo questions with deterministic SQL templates.

## Recommended LLM Flow

```text
Question
-> get_schema
-> generate SELECT SQL in the LLM client
-> validate_readonly_sql
-> check_sql_syntax
-> run_readonly_query
-> explain_query_result or summarize rows directly
```

## Runtime Environment

```text
DATABASE_URL=postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare
MCP_QUERY_TIMEOUT_MS=30000
MCP_MAX_ROWS=200
```

`MCP_MAX_ROWS` is applied by wrapping queries without an explicit `LIMIT`.
