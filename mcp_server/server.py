import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import get_settings
from database import Database
from permissions import can_read_sql, filter_schema_for_user, list_users
from sql_validator import add_default_limit, validate_sql


settings = get_settings()
database = Database(settings.database_url, settings.query_timeout_ms)
mcp = FastMCP("healthcare-postgres")


ROOT_DIR = Path(__file__).resolve().parent
SCHEMA_METADATA_FILE = ROOT_DIR / "schema_metadata.json"


def load_schema_metadata() -> dict[str, Any]:
    return json.loads(SCHEMA_METADATA_FILE.read_text(encoding="utf-8"))


def compact_schema(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = load_schema_metadata()
    metadata_columns = {
        (table_name, column["name"]): column
        for table_name, columns in metadata["tables"].items()
        for column in columns
    }

    tables: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        column = {
            "name": row["column_name"],
            "type": row["data_type"],
        }
        column.update(metadata_columns.get((row["table_name"], row["column_name"]), {}))
        tables.setdefault(row["table_name"], []).append(column)

    return {
        "tables": tables,
        "join_hints": metadata["join_hints"],
        "prompt_rules": metadata["prompt_rules"],
        "prompt_examples": metadata.get("prompt_examples", []),
    }


@mcp.tool()
def get_users() -> dict[str, Any]:
    """Return temporary test users and their roles."""
    return {"users": list_users()}


@mcp.tool()
def get_schema(user_id: str | None = None) -> dict[str, Any]:
    """Return PostgreSQL tables, columns, types, and common join hints allowed for a user."""
    schema = compact_schema(database.schema())
    return filter_schema_for_user(user_id, schema)


@mcp.tool()
def validate_readonly_sql(sql: str, user_id: str | None = None) -> dict[str, Any]:
    """Validate that SQL is a safe single-statement SELECT over MVP healthcare tables."""
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    if is_valid:
        is_allowed, permission_error = can_read_sql(user_id, normalized_sql)
        if not is_allowed:
            is_valid = False
            validation_error = permission_error

    limited_sql = add_default_limit(normalized_sql, settings.max_rows) if is_valid else normalized_sql
    return {
        "is_valid": is_valid,
        "user_id": user_id,
        "sql": normalized_sql,
        "limited_sql": limited_sql,
        "error": validation_error,
        "max_rows": settings.max_rows,
    }


@mcp.tool()
def check_sql_syntax(sql: str, user_id: str | None = None) -> dict[str, Any]:
    """Validate safety rules and ask PostgreSQL to parse the query with EXPLAIN."""
    validation = validate_readonly_sql(sql, user_id)
    if not validation["is_valid"]:
        return {
            "ok": False,
            "user_id": user_id,
            "sql": validation["sql"],
            "error": validation["error"],
        }

    normalized_sql = validation["sql"]
    try:
        database.query("EXPLAIN " + normalized_sql)
    except Exception as error:  # noqa: BLE001
        return {
            "ok": False,
            "user_id": user_id,
            "sql": normalized_sql,
            "error": "syntax_error",
            "detail": str(error),
        }

    return {
        "ok": True,
        "user_id": user_id,
        "sql": normalized_sql,
        "error": None,
    }


@mcp.tool()
def run_readonly_query(sql: str, user_id: str | None = None) -> dict[str, Any]:
    """Validate and run a read-only PostgreSQL SELECT query with a default row limit."""
    validation = validate_readonly_sql(sql, user_id)
    if not validation["is_valid"]:
        return {
            "ok": False,
            "user_id": user_id,
            "sql": validation["sql"],
            "error": validation["error"],
            "rows": [],
            "row_count": 0,
        }

    normalized_sql = validation["sql"]
    limited_sql = add_default_limit(normalized_sql, settings.max_rows)
    rows = database.query(limited_sql)
    explanation = explain_rows(rows)
    return {
        "ok": True,
        "user_id": user_id,
        "sql": limited_sql,
        "rows": rows,
        "row_count": len(rows),
        "max_rows": settings.max_rows,
        "explanation": explanation,
    }


@mcp.tool()
def explain_query_result(question: str, sql: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    """Generate a short Vietnamese explanation for query results."""
    return {
        "question": question,
        "sql": sql,
        "explanation": explain_rows(rows),
    }


def explain_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Truy vấn không trả về dòng kết quả nào."

    if len(rows) == 1:
        parts = [f"{key} = {value}" for key, value in rows[0].items()]
        return "Kết quả truy vấn có 1 dòng: " + ", ".join(parts) + "."

    columns = list(rows[0].keys())
    return (
        f"Kết quả truy vấn trả về {len(rows)} dòng với các cột "
        + ", ".join(columns)
        + ". Các dòng đầu thể hiện những nhóm hoặc bản ghi có giá trị nổi bật theo điều kiện truy vấn."
    )


if __name__ == "__main__":
    mcp.run()
