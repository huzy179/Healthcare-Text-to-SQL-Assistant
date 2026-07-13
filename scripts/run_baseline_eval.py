#!/usr/bin/env python3
"""Run a baseline Text-to-SQL evaluation.

The script can work in two modes:

1. LLM mode: set VLLM_BASE_URL and VLLM_MODEL to call an OpenAI-compatible API.
2. Dry-run mode: pass --dry-run to use expected_sql as generated_sql.

Dry-run mode verifies the validator, PostgreSQL execution path, and report output
before a real model is connected.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL = ROOT / "datasets" / "text_to_sql" / "eval_questions.jsonl"
DEFAULT_PROMPT = ROOT / "inference" / "prompts" / "text_to_sql_prompt.txt"
DEFAULT_SCHEMA = ROOT / "inference" / "prompts" / "schema_context.txt"
DEFAULT_OUTPUT = ROOT / "reports" / "baseline_eval_results.jsonl"
DEFAULT_SUMMARY = ROOT / "reports" / "baseline_eval_summary.md"

BLOCKED_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "copy",
    "grant",
    "revoke",
}

KNOWN_TABLES = {
    "patients",
    "encounters",
    "conditions",
    "medications",
    "observations",
    "procedures",
    "claims",
    "providers",
    "organizations",
    "payers",
}


@dataclass
class EvalItem:
    id: str
    category: str
    question: str
    expected_sql: str


def load_jsonl(path: Path) -> list[EvalItem]:
    items: list[EvalItem] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            data = json.loads(line)
            items.append(
                EvalItem(
                    id=data["id"],
                    category=data["category"],
                    question=data["question"],
                    expected_sql=data["expected_sql"],
                )
            )
    return items


def render_prompt(prompt_template: str, schema: str, question: str) -> str:
    return (
        prompt_template.replace("{{schema}}", schema.strip())
        .replace("{{question}}", question.strip())
    )


def call_openai_compatible(prompt: str, base_url: str, model: str, api_key: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": "You generate safe PostgreSQL SELECT queries. Return SQL only.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def strip_code_fence(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def validate_sql(sql: str) -> tuple[bool, str, str | None]:
    cleaned = strip_code_fence(sql).strip()
    cleaned = re.sub(r";+\s*$", "", cleaned)
    lowered = cleaned.lower()

    if not cleaned:
        return False, cleaned, "empty_sql"
    if not lowered.startswith("select"):
        return False, cleaned, "non_select"
    if ";" in cleaned:
        return False, cleaned, "multiple_statements"
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            return False, cleaned, f"blocked_keyword:{keyword}"

    table_scan_sql = re.sub(r"extract\s*\([^)]*\)", "extract_expr", lowered)
    referenced = set(re.findall(r"\bfrom\s+([a-z_][a-z0-9_]*)|\bjoin\s+([a-z_][a-z0-9_]*)", table_scan_sql))
    table_names = {name for pair in referenced for name in pair if name}
    unknown_tables = sorted(table_names - KNOWN_TABLES)
    if unknown_tables:
        return False, cleaned, "unknown_table:" + ",".join(unknown_tables)

    return True, cleaned, None


def execute_sql(sql: str, timeout_seconds: int) -> tuple[bool, str | None, list[dict[str, Any]]]:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "healthcare_readonly",
        "-d",
        "healthcare",
        "--csv",
        "-c",
        sql,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "execution_timeout", []

    if completed.returncode != 0:
        return False, completed.stderr.strip() or completed.stdout.strip(), []

    rows = list(csv.DictReader(completed.stdout.splitlines()))
    return True, None, rows


def compare_results(expected_rows: list[dict[str, Any]], generated_rows: list[dict[str, Any]]) -> bool:
    return expected_rows == generated_rows


def write_summary(path: Path, results: list[dict[str, Any]], dry_run: bool) -> None:
    total = len(results)
    valid = sum(1 for item in results if item["is_valid_sql"])
    executed = sum(1 for item in results if item["execution_success"])
    accurate = sum(1 for item in results if item["result_match"])
    safety = sum(1 for item in results if item["validation_error"] and item["validation_error"].startswith("blocked_keyword"))

    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    lines = [
        "# Baseline Evaluation Summary",
        "",
        f"Mode: {'dry-run expected SQL' if dry_run else 'LLM generated SQL'}",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total questions | {total} |",
        f"| Valid SQL | {valid}/{total} |",
        f"| Execution success | {executed}/{total} |",
        f"| Execution accuracy | {accurate}/{total} |",
        f"| Safety violations | {safety}/{total} |",
        "",
        "## By Category",
        "",
        "| Category | Questions | Execution accuracy |",
        "|---|---:|---:|",
    ]

    for category, items in sorted(by_category.items()):
        category_total = len(items)
        category_accurate = sum(1 for item in items if item["result_match"])
        lines.append(f"| {category} | {category_total} | {category_accurate}/{category_total} |")

    failures = [item for item in results if not item["result_match"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.extend(
                [
                    f"### {item['id']}: {item['question']}",
                    "",
                    f"- Category: `{item['category']}`",
                    f"- Validation error: `{item['validation_error']}`",
                    f"- Execution error: `{item['execution_error']}`",
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
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-file", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    items = load_jsonl(args.eval_file)
    if args.limit:
        items = items[: args.limit]

    prompt_template = args.prompt_file.read_text(encoding="utf-8")
    schema = args.schema_file.read_text(encoding="utf-8")
    base_url = os.getenv("VLLM_BASE_URL", "")
    model = os.getenv("VLLM_MODEL", "")
    api_key = os.getenv("VLLM_API_KEY", "local")

    if not args.dry_run and (not base_url or not model):
        raise SystemExit("Set VLLM_BASE_URL and VLLM_MODEL, or use --dry-run.")

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with args.output_file.open("w", encoding="utf-8") as output:
        for item in items:
            prompt = render_prompt(prompt_template, schema, item.question)
            started = time.time()

            if args.dry_run:
                generated_sql = item.expected_sql
            else:
                try:
                    generated_sql = call_openai_compatible(prompt, base_url, model, api_key)
                except (urllib.error.URLError, KeyError, TimeoutError) as error:
                    generated_sql = ""
                    generation_error = str(error)
                else:
                    generation_error = None

            is_valid, normalized_sql, validation_error = validate_sql(generated_sql)

            expected_ok, expected_error, expected_rows = execute_sql(item.expected_sql, args.timeout_seconds)

            execution_success = False
            execution_error = None
            generated_rows: list[dict[str, Any]] = []
            if is_valid:
                execution_success, execution_error, generated_rows = execute_sql(normalized_sql, args.timeout_seconds)

            result = {
                "id": item.id,
                "category": item.category,
                "question": item.question,
                "expected_sql": item.expected_sql,
                "generated_sql": normalized_sql,
                "generation_error": locals().get("generation_error"),
                "is_valid_sql": is_valid,
                "validation_error": validation_error,
                "expected_execution_success": expected_ok,
                "expected_execution_error": expected_error,
                "execution_success": execution_success,
                "execution_error": execution_error,
                "result_match": expected_ok and execution_success and compare_results(expected_rows, generated_rows),
                "expected_row_count": len(expected_rows),
                "generated_row_count": len(generated_rows),
                "latency_ms": int((time.time() - started) * 1000),
            }
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()
            results.append(result)
            print(f"{item.id}: valid={is_valid} executed={execution_success} match={result['result_match']}")

    write_summary(args.summary_file, results, args.dry_run)
    print(f"Wrote {args.output_file}")
    print(f"Wrote {args.summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
