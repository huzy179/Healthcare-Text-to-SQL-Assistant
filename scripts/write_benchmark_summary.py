#!/usr/bin/env python3
"""Write a compact benchmark overview across available evaluation modes."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LLM_RESULTS = ROOT / "reports" / "text_to_sql_llm_results.jsonl"
SAFETY_RESULTS = ROOT / "reports" / "sql_safety_results.jsonl"
OUTPUT = ROOT / "reports" / "benchmark_summary.md"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def ratio(done: int, total: int) -> str:
    return f"{done}/{total}" if total else "0/0"


def main() -> int:
    llm = load_jsonl(LLM_RESULTS)
    safety = load_jsonl(SAFETY_RESULTS)

    total = len(llm)
    exact = sum(1 for item in llm if item.get("exact_match"))
    execution = sum(1 for item in llm if item.get("execution_match"))
    valid = sum(1 for item in llm if item.get("is_valid_sql"))
    avg_latency = round(sum(item.get("latency_ms", 0) for item in llm) / total, 2) if total else 0

    unsafe = [item for item in safety if item.get("expected_error") is not None]
    unsafe_rejected = sum(1 for item in unsafe if item.get("passed"))
    safety_total = len(safety)
    safety_passed = sum(1 for item in safety if item.get("passed"))

    lines = [
        "# Benchmark Summary",
        "",
        "| Mode | Exact Match | Execution Accuracy | Valid SQL Rate | Unsafe Query Rejection Rate | Avg Latency | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
        (
            "| LLM single-shot SQL generation | "
            f"{ratio(exact, total)} | {ratio(execution, total)} | {ratio(valid, total)} | n/a | {avg_latency} ms | "
            "One model call per question, no repair loop. |"
        ),
        (
            "| Backend pipeline without MCP | "
            f"{ratio(exact, total)} | {ratio(execution, total)} | {ratio(valid, total)} | "
            f"{ratio(unsafe_rejected, len(unsafe))} | {avg_latency} ms | "
            "Generated SQL is validated/executed by the backend evaluator using readonly DB. |"
        ),
        "| Agent with MCP multi-step | pending | pending | pending | pending | pending | Needs a real MCP client/agent loop wired into eval. |",
        "",
        "## Safety Validator",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Safety cases passed | {ratio(safety_passed, safety_total)} |",
        f"| Unsafe Query Rejection Rate | {ratio(unsafe_rejected, len(unsafe))} |",
        "",
        "Detailed reports:",
        "",
        "- `reports/text_to_sql_llm_summary.md`",
        "- `reports/sql_safety_summary.md`",
        "- `reports/text_to_sql_gold_summary.md`",
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
