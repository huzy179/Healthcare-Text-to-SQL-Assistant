import json
import re
from pathlib import Path

import sqlglot
from sqlglot import exp


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
    "call",
    "execute",
}

SCHEMA_METADATA_FILE = Path(__file__).resolve().parent / "schema_metadata.json"


def known_tables() -> set[str]:
    metadata = json.loads(SCHEMA_METADATA_FILE.read_text(encoding="utf-8"))
    return set(metadata["tables"].keys())


def strip_code_fence(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def normalize_sql(sql: str) -> str:
    cleaned = strip_code_fence(sql).strip()
    return re.sub(r";+\s*$", "", cleaned)


def parse_select(sql: str) -> tuple[exp.Expression | None, str | None]:
    try:
        expressions = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as error:
        return None, "parse_error:" + str(error).splitlines()[0]

    expressions = [expression for expression in expressions if expression is not None]
    if len(expressions) != 1:
        return None, "multiple_statements"

    expression = expressions[0]
    if not isinstance(expression, exp.Select):
        return None, "non_select"
    return expression, None


def referenced_tables(sql: str) -> set[str]:
    expression, error = parse_select(normalize_sql(sql))
    if error or expression is None:
        return set()
    return {table.name.lower() for table in expression.find_all(exp.Table)}


def table_aliases(sql: str) -> dict[str, str]:
    expression, error = parse_select(normalize_sql(sql))
    if error or expression is None:
        return {}

    aliases: dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        table_name = table.name.lower()
        aliases[table_name] = table_name
        if table.alias:
            aliases[table.alias.lower()] = table_name
    return aliases


def referenced_columns(sql: str) -> set[tuple[str | None, str]]:
    expression, error = parse_select(normalize_sql(sql))
    if error or expression is None:
        return set()

    aliases = table_aliases(sql)
    columns: set[tuple[str | None, str]] = set()
    for column in expression.find_all(exp.Column):
        table = column.table.lower() if column.table else None
        columns.add((aliases.get(table, table) if table else None, column.name.lower()))
    return columns


def referenced_stars(sql: str) -> set[str | None]:
    expression, error = parse_select(normalize_sql(sql))
    if error or expression is None:
        return set()

    aliases = table_aliases(sql)
    stars: set[str | None] = set()
    for column in expression.find_all(exp.Column):
        if column.name == "*":
            table = column.table.lower() if column.table else None
            stars.add(aliases.get(table, table) if table else None)
    for star in expression.find_all(exp.Star):
        parent = star.parent
        table = parent.table.lower() if isinstance(parent, exp.Column) and parent.table else None
        stars.add(aliases.get(table, table) if table else None)
    return stars


def validate_sql(sql: str) -> tuple[bool, str, str | None]:
    cleaned = normalize_sql(sql)
    lowered = cleaned.lower()

    if not cleaned:
        return False, cleaned, "empty_sql"

    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            return False, cleaned, f"blocked_keyword:{keyword}"

    expression, parse_error = parse_select(cleaned)
    if parse_error:
        return False, cleaned, parse_error
    if expression is None:
        return False, cleaned, "parse_error"

    unknown_tables = sorted(referenced_tables(cleaned) - known_tables())
    if unknown_tables:
        return False, cleaned, "unknown_table:" + ",".join(unknown_tables)

    return True, cleaned, None


def add_default_limit(sql: str, max_rows: int) -> str:
    cleaned = normalize_sql(sql)
    if re.search(r"\blimit\s+\d+\b", cleaned, flags=re.IGNORECASE):
        return cleaned
    return f"SELECT * FROM ({cleaned}) AS mcp_limited_query LIMIT {max_rows}"
