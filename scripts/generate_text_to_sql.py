#!/usr/bin/env python3
"""Generate SQL for eval questions with an OpenAI-compatible chat API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "mcp_server"))


DEFAULT_EVAL = ROOT / "datasets" / "text_to_sql" / "eval_questions.jsonl"
DEFAULT_OUTPUT = ROOT / "outputs" / "generated_sql.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                items.append(json.loads(line))
    return items


def load_role_filtered_schema(user_id: str) -> dict[str, Any]:
    from permissions import filter_schema_for_user  # noqa: PLC0415

    metadata_path = ROOT / "mcp_server" / "schema_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return filter_schema_for_user(user_id, metadata)


def parse_sql_generation(text: str) -> tuple[str, str]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```sql").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned, "Model returned raw SQL instead of JSON."

    return str(parsed.get("sql", "")).strip(), str(parsed.get("reasoning", "")).strip()


def chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    timeout_seconds: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    return data["choices"][0]["message"]["content"]


def compact_schema_for_prompt(schema: dict[str, Any]) -> dict[str, Any]:
    tables: dict[str, list[str]] = {}
    for table_name, columns in schema.get("tables", {}).items():
        compact_columns = []
        for column in columns:
            text = f"{column['name']}:{column['type']}"
            if column.get("notes"):
                text += f" ({column['notes']})"
            compact_columns.append(text)
        tables[table_name] = compact_columns

    return {
        "tables": tables,
        "join_hints": schema.get("join_hints", []),
    }


def build_prompt(question: str, schema: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You generate safe PostgreSQL SELECT queries for a healthcare analytics database. "
        "Return only JSON with keys sql and reasoning. The sql must be a single SELECT statement. "
        "Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY, GRANT, REVOKE, CALL, or EXECUTE."
    )
    user_prompt = "\n".join(
        [
            "Use this role-filtered schema and join hints.",
            json.dumps(compact_schema_for_prompt(schema), ensure_ascii=False, separators=(",", ":")),
            "",
            "Question:",
            question,
            "",
            "Rules:",
            *[f"- {rule}" for rule in schema.get("prompt_rules", [])],
            "",
            "Examples:",
            *[f"Q: {example['question']}\nSQL: {example['sql']}" for example in schema.get("prompt_examples", [])],
        ]
    )
    return system_prompt, user_prompt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--user-id", default="admin")
    parser.add_argument("--base-url", default=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"))
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY", "local"))
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "qwen-coder-3b"))
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("LLM_MAX_TOKENS", "192")))
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    schema = load_role_filtered_schema(args.user_id)
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    with args.output_file.open("w", encoding="utf-8") as output:
        for item in load_jsonl(args.eval_file):
            started = time.perf_counter()
            system_prompt, user_prompt = build_prompt(item["question"], schema)
            error = None
            sql = ""
            reasoning = ""
            raw = ""
            try:
                raw = chat_completion(
                    args.base_url,
                    args.api_key,
                    args.model,
                    system_prompt,
                    user_prompt,
                    args.max_tokens,
                    args.timeout_seconds,
                )
                sql, reasoning = parse_sql_generation(raw)
            except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
                error = str(exc)

            result = {
                "id": item["id"],
                "question": item["question"],
                "generated_sql": sql,
                "reasoning": reasoning,
                "error": error,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "raw": raw,
            }
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"{item['id']}: {'error=' + error if error else sql}")

    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
