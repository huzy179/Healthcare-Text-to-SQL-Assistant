# Architecture

```text
User
-> LLM / MCP client
-> Healthcare PostgreSQL MCP server
-> get_schema / validate_readonly_sql / run_readonly_query
-> SQL Validator
-> PostgreSQL
-> Query result
-> LLM summary
```

The MCP server is the runtime boundary. It does not serve a chat API, host a model, or fine-tune a model. A regular LLM client calls MCP tools, writes PostgreSQL `SELECT` queries, and summarizes the returned rows.
