#!/usr/bin/env python3
"""Evaluate Text-to-SQL outputs against expected SQL."""

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
        raise ValueError("generated_file_required")
    outputs = load_jsonl(path)
    return {item["id"]: item["generated_sql"] for item in outputs}


def normalize_sql_for_exact_match(sql: str) -> str:
    normalized = sql.strip()
    normalized = re.sub(r";+\s*$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def referenced_tables(sql: str) -> set[str]:
    return {match.group(1).lower() for match in re.finditer(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)\b", sql, re.I)}


def has_limit(sql: str) -> bool:
    return bool(re.search(r"\blimit\s+\d+\b", sql, re.I))


def where_clause(sql: str) -> str:
    match = re.search(r"\bwhere\b(.+?)(?:\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)", sql, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


def rows_match(expected_rows: list[dict[str, Any]], generated_rows: list[dict[str, Any]]) -> bool:
    if len(expected_rows) != len(generated_rows):
        return False

    for expected, generated in zip(expected_rows, generated_rows, strict=True):
        expected_values = [str(value) for value in expected.values()]
        generated_values = [str(value) for value in generated.values()]
        if expected_values != generated_values:
            return False
    return True


def classify_error(item: dict[str, Any]) -> str:
    error = (item.get("error") or "").lower()
    generated_sql = (item.get("generated_sql") or "").lower()

    if item["execution_match"]:
        return "none"
    if not generated_sql.strip():
        return "empty_sql"
    if "permission_denied" in error:
        return "permission_error"
    if "non_select" in error or "blocked_keyword" in error or "multiple_statements" in error:
        return "safety_error"
    if "unknown_table" in error or "relation" in error and "does not exist" in error:
        return "wrong_table"
    if "column" in error and "does not exist" in error:
        return "wrong_column"
    if "parse_error" in error or "syntax" in error:
        return "syntax_error"
    if not item["is_valid_sql"]:
        return "invalid_sql"
    if referenced_tables(item["expected_sql"]) != referenced_tables(item["generated_sql"]):
        return "wrong_table"
    if where_clause(item["expected_sql"]) != where_clause(item["generated_sql"]):
        return "wrong_filter"
    if has_limit(item["expected_sql"]) != has_limit(item["generated_sql"]):
        return "wrong_limit"
    if item["expected_row_count"] != item["generated_row_count"]:
        return "row_count_mismatch"
    if re.search(r"\bjoin\b", item["expected_sql"], re.I) != re.search(r"\bjoin\b", item["generated_sql"], re.I):
        return "wrong_join"
    if re.search(r"\b(group by|count|sum|avg|min|max)\b", item["expected_sql"], re.I) != re.search(
        r"\b(group by|count|sum|avg|min|max)\b", item["generated_sql"], re.I
    ):
        return "wrong_aggregation"
    return "execution_mismatch"


def execute(
    database: Any,
    sql: str,
    max_rows: int,
    user_id: str,
    validate_sql: Any,
    add_default_limit: Any,
    can_read_sql: Any,
) -> tuple[bool, str | None, list[dict[str, Any]], int]:
    started = time.perf_counter()
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    if not is_valid:
        return False, validation_error, [], int((time.perf_counter() - started) * 1000)

    is_allowed, permission_error = can_read_sql(user_id, normalized_sql)
    if not is_allowed:
        return False, permission_error, [], int((time.perf_counter() - started) * 1000)

    try:
        rows = database.query(add_default_limit(normalized_sql, max_rows))
    except Exception as error:  # noqa: BLE001
        return False, str(error), [], int((time.perf_counter() - started) * 1000)

    return True, None, rows, int((time.perf_counter() - started) * 1000)


def write_summary(path: Path, results: list[dict[str, Any]]) -> None:
    total = len(results)
    exact = sum(1 for item in results if item["exact_match"])
    execution = sum(1 for item in results if item["execution_match"])
    valid = sum(1 for item in results if item["is_valid_sql"])
    avg_latency = round(sum(item["latency_ms"] for item in results) / total, 2) if total else 0

    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    by_error_type: dict[str, int] = {}
    for item in results:
        by_error_type[item["error_type"]] = by_error_type.get(item["error_type"], 0) + 1

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
        "## Error Types",
        "",
        "| Error Type | Count |",
        "|---|---:|",
    ]

    for error_type, count in sorted(by_error_type.items()):
        lines.append(f"| {error_type} | {count} |")

    lines.extend(
        [
            "",
            "## By Category",
            "",
            "| Category | Questions | Exact Match | Execution Accuracy |",
            "|---|---:|---:|---:|",
        ]
    )

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
                    f"- Error type: `{item['error_type']}`",
                    f"- Validation/execution error: `{item['error']}`",
                    f"- Expected row count: `{item['expected_row_count']}`",
                    f"- Generated row count: `{item['generated_row_count']}`",
                    "",
                    "Expected SQL:",
                    "",
                    "```sql",
                    item["expected_sql"],
                    "```",
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


def write_gold_summary(path: Path, results: list[dict[str, Any]]) -> None:
    total = len(results)
    valid = sum(1 for item in results if item["is_valid_sql"])
    execution = sum(1 for item in results if item["execution_match"])
    avg_latency = round(sum(item["latency_ms"] for item in results) / total, 2) if total else 0

    lines = [
        "# Gold SQL Evaluation Summary",
        "",
        "This report validates the reference SQL, database, validator, RBAC, and reporting path. It does not measure LLM quality.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total questions | {total} |",
        f"| Valid reference SQL | {valid}/{total} |",
        f"| Executable reference SQL | {execution}/{total} |",
        f"| Average execution time | {avg_latency} ms |",
    ]

    failures = [item for item in results if not item["execution_match"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.extend(
                [
                    f"### {item['id']}: {item['question']}",
                    "",
                    f"- Error: `{item['error']}`",
                    "",
                    "```sql",
                    item["expected_sql"],
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
    parser.add_argument("--user-id", default="admin")
    parser.add_argument(
        "--mode",
        choices=["gold", "generated"],
        default="generated",
        help="gold validates expected_sql only; generated evaluates model-generated SQL from --generated-file.",
    )
    args = parser.parse_args()

    from database import Database  # noqa: PLC0415
    from permissions import can_read_sql  # noqa: PLC0415
    from sql_validator import add_default_limit, validate_sql  # noqa: PLC0415

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
    )
    query_timeout_ms = int(os.getenv("MCP_QUERY_TIMEOUT_MS", "30000"))
    max_rows = int(os.getenv("MCP_MAX_ROWS", "200"))
    database = Database(database_url, query_timeout_ms)
    generated_by_id = load_generated_sql(args.generated_file) if args.mode == "generated" else {}

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for item in load_jsonl(args.eval_file):
        generated_sql = item["expected_sql"] if args.mode == "gold" else generated_by_id.get(item["id"], "")
        expected_ok, expected_error, expected_rows, _ = execute(
            database,
            item["expected_sql"],
            max_rows,
            args.user_id,
            validate_sql,
            add_default_limit,
            can_read_sql,
        )
        generated_ok, generated_error, generated_rows, latency_ms = execute(
            database,
            generated_sql,
            max_rows,
            args.user_id,
            validate_sql,
            add_default_limit,
            can_read_sql,
        )

        is_valid, normalized_sql, validation_error = validate_sql(generated_sql)
        is_allowed, permission_error = can_read_sql(args.user_id, normalized_sql) if is_valid else (False, None)
        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_sql": item["expected_sql"],
            "generated_sql": generated_sql,
            "user_id": args.user_id,
            "is_valid_sql": is_valid and is_allowed,
            "exact_match": normalize_sql_for_exact_match(item["expected_sql"])
            == normalize_sql_for_exact_match(generated_sql),
            "execution_match": expected_ok and generated_ok and rows_match(expected_rows, generated_rows),
            "error": validation_error or permission_error or generated_error or expected_error,
            "expected_row_count": len(expected_rows),
            "generated_row_count": len(generated_rows),
            "latency_ms": latency_ms,
        }
        if args.mode == "gold":
            result["exact_match"] = True
        result["error_type"] = classify_error(result)
        print(
            f"{result['id']}: valid={result['is_valid_sql']} "
            f"exact={result['exact_match']} execution={result['execution_match']} "
            f"latency_ms={latency_ms}"
        )
        results.append(result)

    with args.output_file.open("w", encoding="utf-8") as output:
        for result in results:
            output.write(json.dumps(result, ensure_ascii=False) + "\n")

    if args.mode == "gold":
        write_gold_summary(args.summary_file, results)
    else:
        write_summary(args.summary_file, results)
    print(f"Wrote {args.output_file}")
    print(f"Wrote {args.summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
