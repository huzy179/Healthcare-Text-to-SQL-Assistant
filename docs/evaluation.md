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

Current baseline files:

- `datasets/text_to_sql/eval_questions.jsonl`
- `scripts/run_baseline_eval.py`
- `reports/baseline_eval_results.jsonl`
- `reports/baseline_eval_summary.md`
