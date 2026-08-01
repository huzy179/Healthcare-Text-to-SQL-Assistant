#!/usr/bin/env python3
"""Evaluate SQL validator rejection behavior."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "mcp_server"))

DEFAULT_CASES = ROOT / "datasets" / "text_to_sql" / "safety_cases.jsonl"
DEFAULT_OUTPUT = ROOT / "reports" / "sql_safety_results.jsonl"
DEFAULT_SUMMARY = ROOT / "reports" / "sql_safety_summary.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                items.append(json.loads(line))
    return items


def write_summary(path: Path, results: list[dict[str, Any]]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    unsafe = [item for item in results if item["expected_error"] is not None]
    unsafe_passed = sum(1 for item in unsafe if item["passed"])
    safe = [item for item in results if item["expected_error"] is None]
    safe_passed = sum(1 for item in safe if item["passed"])
    avg_latency = round(sum(item["latency_ms"] for item in results) / total, 2) if total else 0

    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    lines = [
        "# SQL Safety Evaluation Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total cases | {total} |",
        f"| Overall pass rate | {passed}/{total} |",
        f"| Unsafe Query Rejection Rate | {unsafe_passed}/{len(unsafe)} |",
        f"| Safe SELECT Acceptance Rate | {safe_passed}/{len(safe)} |",
        f"| Average validation time | {avg_latency} ms |",
        "",
        "## By Category",
        "",
        "| Category | Cases | Passed |",
        "|---|---:|---:|",
    ]

    for category, items in sorted(by_category.items()):
        category_passed = sum(1 for item in items if item["passed"])
        lines.append(f"| {category} | {len(items)} | {category_passed}/{len(items)} |")

    failures = [item for item in results if not item["passed"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- Category: `{item['category']}`",
                    f"- Expected error: `{item['expected_error']}`",
                    f"- Actual error: `{item['actual_error']}`",
                    f"- Valid: `{item['is_valid']}`",
                    "",
                    "```sql",
                    item["sql"],
                    "```",
                    "",
                ]
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-file", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-file", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    from sql_validator import validate_sql  # noqa: PLC0415

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for item in load_jsonl(args.cases_file):
        started = time.perf_counter()
        is_valid, normalized_sql, actual_error = validate_sql(item["sql"])
        latency_ms = int((time.perf_counter() - started) * 1000)
        expected_error = item["expected_error"]
        passed = (expected_error is None and is_valid) or (expected_error is not None and actual_error == expected_error)
        result = {
            "id": item["id"],
            "category": item["category"],
            "sql": item["sql"],
            "normalized_sql": normalized_sql,
            "expected_error": expected_error,
            "actual_error": actual_error,
            "is_valid": is_valid,
            "passed": passed,
            "latency_ms": latency_ms,
        }
        results.append(result)
        print(f"{item['id']}: passed={passed} valid={is_valid} error={actual_error}")

    with args.output_file.open("w", encoding="utf-8") as output:
        for result in results:
            output.write(json.dumps(result, ensure_ascii=False) + "\n")

    write_summary(args.summary_file, results)
    print(f"Wrote {args.output_file}")
    print(f"Wrote {args.summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
