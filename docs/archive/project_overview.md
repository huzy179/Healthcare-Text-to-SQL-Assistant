# Project Overview

Healthcare PostgreSQL MCP Server exposes safe database tools for LLM clients to query healthcare CSV data imported into PostgreSQL.

Current focus:

1. Import healthcare CSV into PostgreSQL.
2. Write and verify sample SQL queries.
3. Expose schema, SQL validation, and readonly query execution through MCP.
4. Let a regular LLM client generate PostgreSQL `SELECT` queries and call MCP tools safely.
