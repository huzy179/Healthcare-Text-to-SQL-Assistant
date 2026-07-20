#!/usr/bin/env python3
"""Evaluate Text-to-SQL outputs against expected SQL.

By default this runs in dry-run mode and uses `expected_sql` as `generated_sql`.
For model/MCP-client outputs, provide a JSONL file with `id` and `generated_sql`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "mcp_server"))


DEFAULT_EVAL = ROOT / "datasets" / "text_to_sql" / "eval_questions.jsonl"
DEFAULT_OUTPUT = ROOT / "reports" / "text_to_sql_eval_results.jsonl"
DEFAULT_SUMMARY = ROOT / "reports" / "text_to_sql_eval_summary.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                items.append(json.loads(line))
    return items


def load_generated_sql(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    outputs = load_jsonl(path)
    return {item["id"]: item["generated_sql"] for item in outputs}


def normalize_sql_for_exact_match(sql: str) -> str:
    normalized = sql.strip()
    normalized = re.sub(r";+\s*$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def execute(database: Any, sql: str, max_rows: int, validate_sql: Any, add_default_limit: Any) -> tuple[bool, str | None, list[dict[str, Any]], int]:
    started = time.time()
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    if not is_valid:
        return False, validation_error, [], int((time.time() - started) * 1000)

    try:
        rows = database.query(add_default_limit(normalized_sql, max_rows))
    except Exception as error:  # noqa: BLE001
        return False, str(error), [], int((time.time() - started) * 1000)

    return True, None, rows, int((time.time() - started) * 1000)


def write_summary(path: Path, results: list[dict[str, Any]]) -> None:
    total = len(results)
    exact = sum(1 for item in results if item["exact_match"])
    execution = sum(1 for item in results if item["execution_match"])
    valid = sum(1 for item in results if item["is_valid_sql"])
    avg_latency = round(sum(item["latency_ms"] for item in results) / total, 2) if total else 0

    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    lines = [
        "# Text-to-SQL Evaluation Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total questions | {total} |",
        f"| Valid SQL | {valid}/{total} |",
        f"| Exact Match Accuracy | {exact}/{total} |",
        f"| Execution Accuracy | {execution}/{total} |",
        f"| Average response time | {avg_latency} ms |",
        "",
        "## By Category",
        "",
        "| Category | Questions | Exact Match | Execution Accuracy |",
        "|---|---:|---:|---:|",
    ]

    for category, items in sorted(by_category.items()):
        category_total = len(items)
        category_exact = sum(1 for item in items if item["exact_match"])
        category_execution = sum(1 for item in items if item["execution_match"])
        lines.append(
            f"| {category} | {category_total} | {category_exact}/{category_total} | {category_execution}/{category_total} |"
        )

    failures = [item for item in results if not item["execution_match"]]
    if failures:
        lines.extend(["", "## SQL Error Analysis", ""])
        for item in failures:
            lines.extend(
                [
                    f"### {item['id']}: {item['question']}",
                    "",
                    f"- Category: `{item['category']}`",
                    f"- Validation/execution error: `{item['error']}`",
                    f"- Expected row count: `{item['expected_row_count']}`",
                    f"- Generated row count: `{item['generated_row_count']}`",
                    "",
                    "Generated SQL:",
                    "",
                    "```sql",
                    item["generated_sql"],
                    "```",
                    "",
                ]
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--generated-file", type=Path)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-file", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    from database import Database  # noqa: PLC0415
    from sql_validator import add_default_limit, validate_sql  # noqa: PLC0415

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
    )
    query_timeout_ms = int(os.getenv("MCP_QUERY_TIMEOUT_MS", "30000"))
    max_rows = int(os.getenv("MCP_MAX_ROWS", "200"))
    database = Database(database_url, query_timeout_ms)
    generated_by_id = load_generated_sql(args.generated_file)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for item in load_jsonl(args.eval_file):
        generated_sql = generated_by_id.get(item["id"], item["expected_sql"])
        expected_ok, expected_error, expected_rows, _ = execute(
            database,
            item["expected_sql"],
            max_rows,
            validate_sql,
            add_default_limit,
        )
        generated_ok, generated_error, generated_rows, latency_ms = execute(
            database,
            generated_sql,
            max_rows,
            validate_sql,
            add_default_limit,
        )

        is_valid, _, validation_error = validate_sql(generated_sql)
        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_sql": item["expected_sql"],
            "generated_sql": generated_sql,
            "is_valid_sql": is_valid,
            "exact_match": normalize_sql_for_exact_match(item["expected_sql"])
            == normalize_sql_for_exact_match(generated_sql),
            "execution_match": expected_ok and generated_ok and expected_rows == generated_rows,
            "error": validation_error or generated_error or expected_error,
            "expected_row_count": len(expected_rows),
            "generated_row_count": len(generated_rows),
            "latency_ms": latency_ms,
        }
        print(
            f"{result['id']}: valid={result['is_valid_sql']} "
            f"exact={result['exact_match']} execution={result['execution_match']} "
            f"latency_ms={latency_ms}"
        )
        results.append(result)

    with args.output_file.open("w", encoding="utf-8") as output:
        for result in results:
            output.write(json.dumps(result, ensure_ascii=False) + "\n")

    write_summary(args.summary_file, results)
    print(f"Wrote {args.output_file}")
    print(f"Wrote {args.summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
