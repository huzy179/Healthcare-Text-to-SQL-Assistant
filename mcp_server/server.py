from typing import Any

from mcp.server.fastmcp import FastMCP

from config import get_settings
from database import Database
from sql_validator import add_default_limit, validate_sql


settings = get_settings()
database = Database(settings.database_url, settings.query_timeout_ms)
mcp = FastMCP("healthcare-postgres")


JOIN_HINTS = [
    "encounters.patient -> patients.id",
    "conditions.patient -> patients.id",
    "conditions.encounter -> encounters.id",
    "medications.patient -> patients.id",
    "medications.encounter -> encounters.id",
    "observations.patient -> patients.id",
    "procedures.patient -> patients.id",
    "procedures.encounter -> encounters.id",
    "encounters.provider -> providers.id",
    "providers.organization -> organizations.id",
    "encounters.organization -> organizations.id",
    "encounters.payer -> payers.id",
]


def compact_schema(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tables: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        tables.setdefault(row["table_name"], []).append(
            {
                "name": row["column_name"],
                "type": row["data_type"],
            }
        )
    return {"tables": tables, "join_hints": JOIN_HINTS}


@mcp.tool()
def get_schema() -> dict[str, Any]:
    """Return PostgreSQL tables, columns, types, and common join hints."""
    return compact_schema(database.schema())


@mcp.tool()
def validate_readonly_sql(sql: str) -> dict[str, Any]:
    """Validate that SQL is a safe single-statement SELECT over MVP healthcare tables."""
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    limited_sql = add_default_limit(normalized_sql, settings.max_rows) if is_valid else normalized_sql
    return {
        "is_valid": is_valid,
        "sql": normalized_sql,
        "limited_sql": limited_sql,
        "error": validation_error,
        "max_rows": settings.max_rows,
    }


@mcp.tool()
def check_sql_syntax(sql: str) -> dict[str, Any]:
    """Validate safety rules and ask PostgreSQL to parse the query with EXPLAIN."""
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    if not is_valid:
        return {
            "ok": False,
            "sql": normalized_sql,
            "error": validation_error,
        }

    try:
        database.query("EXPLAIN " + normalized_sql)
    except Exception as error:  # noqa: BLE001
        return {
            "ok": False,
            "sql": normalized_sql,
            "error": "syntax_error",
            "detail": str(error),
        }

    return {
        "ok": True,
        "sql": normalized_sql,
        "error": None,
    }


@mcp.tool()
def run_readonly_query(sql: str) -> dict[str, Any]:
    """Validate and run a read-only PostgreSQL SELECT query with a default row limit."""
    is_valid, normalized_sql, validation_error = validate_sql(sql)
    if not is_valid:
        return {
            "ok": False,
            "sql": normalized_sql,
            "error": validation_error,
            "rows": [],
            "row_count": 0,
        }

    limited_sql = add_default_limit(normalized_sql, settings.max_rows)
    rows = database.query(limited_sql)
    explanation = explain_rows(rows)
    return {
        "ok": True,
        "sql": limited_sql,
        "rows": rows,
        "row_count": len(rows),
        "max_rows": settings.max_rows,
        "explanation": explanation,
    }


@mcp.tool()
def ask_database(question: str) -> dict[str, Any]:
    """Answer common healthcare analytics questions with safe SQL templates."""
    sql = fallback_sql(question)
    result = run_readonly_query(sql)
    result["question"] = question
    return result


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


def fallback_sql(question: str) -> str:
    normalized = question.lower()
    if "giới tính" in normalized or "gender" in normalized:
        return "SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC"
    if "diabetes" in normalized:
        return "SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%diabetes%'"
    if "hypertension" in normalized or "tăng huyết áp" in normalized:
        return "SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%hypertension%'"
    if "bệnh" in normalized or "chẩn đoán" in normalized or "condition" in normalized:
        return "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10"
    if "lượt khám" in normalized or "encounter" in normalized:
        return "SELECT encounterclass, COUNT(*) AS total_encounters FROM encounters GROUP BY encounterclass ORDER BY total_encounters DESC"
    if "thuốc" in normalized or "medication" in normalized:
        return "SELECT description, COUNT(*) AS total FROM medications GROUP BY description ORDER BY total DESC LIMIT 10"
    if "procedure" in normalized or "thủ thuật" in normalized:
        return "SELECT description, COUNT(*) AS total FROM procedures GROUP BY description ORDER BY total DESC LIMIT 10"
    return "SELECT COUNT(*) AS total_patients FROM patients"


if __name__ == "__main__":
    mcp.run()
