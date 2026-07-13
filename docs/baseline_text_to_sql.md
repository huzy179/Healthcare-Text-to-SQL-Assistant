# Baseline Text-to-SQL Evaluation

Step 3 goal:

```text
Natural language question -> generated SQL -> SQL validation -> PostgreSQL execution -> evaluation result
```

## Files

- `datasets/text_to_sql/eval_questions.jsonl`: 20 initial evaluation questions.
- `inference/prompts/text_to_sql_prompt.txt`: prompt template.
- `inference/prompts/schema_context.txt`: database schema context for the model.
- `scripts/run_baseline_eval.py`: baseline evaluation runner.
- `reports/baseline_eval_results.jsonl`: per-question output.
- `reports/baseline_eval_summary.md`: summary metrics.

## Recommended Model

Start with:

```text
Qwen2.5-Coder-7B-Instruct
```

If hardware is limited, use:

```text
Qwen2.5-Coder-3B-Instruct
```

## Dry Run

Dry-run mode uses `expected_sql` as `generated_sql`. It verifies the database execution and reporting pipeline before connecting a real LLM.

```bash
python3 scripts/run_baseline_eval.py --dry-run
```

## LLM Run

Run a local OpenAI-compatible model server such as vLLM, then set:

```bash
export VLLM_BASE_URL=http://localhost:8000/v1
export VLLM_MODEL=Qwen2.5-Coder-7B-Instruct
python3 scripts/run_baseline_eval.py
```

The script runs SQL through Docker Compose:

```text
docker compose exec -T postgres psql ...
```

Because SQL is executed inside the PostgreSQL container, the script uses:

```text
psql -U healthcare_readonly -d healthcare
```

## Metrics

The baseline report tracks:

- Valid SQL count.
- Execution success count.
- Execution accuracy.
- Safety violations.
- Accuracy by category.

Execution accuracy is the main metric because different SQL strings can still produce the same correct result.

## Next Improvements

After the first LLM run:

1. Inspect failures in `reports/baseline_eval_summary.md`.
2. Fix prompt/schema context for repeated mistakes.
3. Add more eval questions for weak categories.
4. Only consider fine-tuning after baseline errors are understood.
