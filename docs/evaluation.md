# Evaluation

Recommended metrics:

- Execution accuracy
- SQL exact match
- Syntax error rate
- Schema error rate
- Safety violation rate
- Average latency
- Tokens per second
- Successful query rate

Execution accuracy is the most important metric because different valid SQL queries can produce the same correct result.

Recommended MCP evaluation loop:

1. Ask the LLM client a question from `datasets/text_to_sql/eval_questions.jsonl`.
2. Confirm the LLM calls `get_schema` when it needs table or column context.
3. Confirm generated SQL passes `validate_readonly_sql`.
4. Confirm PostgreSQL accepts the SQL through `check_sql_syntax`.
5. Run the SQL with `run_readonly_query`.
6. Compare returned rows with the expected SQL result.

The current evaluation script is:

```bash
python3 scripts/evaluate_text_to_sql.py
```

It reports Exact Match Accuracy, Execution Accuracy, and average response time. Failure cases are listed for SQL error analysis.
