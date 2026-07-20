import json
from pathlib import Path
from typing import Any

from sql_validator import referenced_columns, referenced_stars, referenced_tables


ROOT_DIR = Path(__file__).resolve().parent
USERS_FILE = ROOT_DIR / "users.json"


def load_policy() -> dict[str, Any]:
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def list_users() -> list[dict[str, Any]]:
    return load_policy()["users"]


def get_default_user_id() -> str:
    return load_policy()["default_user_id"]


def get_user(user_id: str | None) -> dict[str, Any] | None:
    policy = load_policy()
    resolved_user_id = user_id or policy["default_user_id"]
    for user in policy["users"]:
        if user["id"] == resolved_user_id or user["username"] == resolved_user_id:
            return user
    return None


def role_policy(role: str) -> dict[str, Any]:
    return load_policy()["roles"][role]


def allowed_tables_for_user(user_id: str | None) -> set[str] | None:
    user = get_user(user_id)
    if user is None:
        return set()

    allowed = role_policy(user["role"])["allowed_tables"]
    if "*" in allowed:
        return None
    return set(allowed)


def can_read_sql(user_id: str | None, sql: str) -> tuple[bool, str | None]:
    user = get_user(user_id)
    if user is None:
        return False, "unknown_user"

    allowed_tables = allowed_tables_for_user(user["id"])
    if allowed_tables is None:
        return True, None

    blocked = sorted(referenced_tables(sql) - allowed_tables)
    if blocked:
        return False, "permission_denied_table:" + ",".join(blocked)

    blocked_columns = denied_columns_in_sql(user["role"], sql)
    if blocked_columns:
        return False, "permission_denied_column:" + ",".join(blocked_columns)

    return True, None


def denied_columns_in_sql(role: str, sql: str) -> list[str]:
    denied_columns = role_policy(role).get("denied_columns", {})
    if not denied_columns:
        return []

    tables = referenced_tables(sql)
    columns = referenced_columns(sql)
    stars = referenced_stars(sql)
    blocked: set[str] = set()

    for table_name in tables:
        denied = set(denied_columns.get(table_name, []))
        if not denied:
            continue

        if "*" in denied:
            blocked.add(f"{table_name}.*")
            continue

        if None in stars or table_name in stars:
            blocked.update(f"{table_name}.{column}" for column in denied)

        for column_table, column_name in columns:
            if column_table == table_name and column_name in denied:
                blocked.add(f"{table_name}.{column_name}")
            if column_table is None and column_name in denied:
                blocked.add(f"{table_name}.{column_name}")

    return sorted(blocked)


def filter_schema_for_user(user_id: str | None, schema: dict[str, Any]) -> dict[str, Any]:
    user = get_user(user_id)
    if user is None:
        return {"tables": {}, "join_hints": [], "user": None, "error": "unknown_user"}

    policy = role_policy(user["role"])
    allowed_tables = allowed_tables_for_user(user["id"])
    denied_columns = policy.get("denied_columns", {})

    tables: dict[str, list[dict[str, str]]] = {}
    for table_name, columns in schema["tables"].items():
        if allowed_tables is not None and table_name not in allowed_tables:
            continue

        denied = set(denied_columns.get(table_name, []))
        if "*" in denied:
            continue

        tables[table_name] = [
            column for column in columns if column["name"] not in denied
        ]

    join_hints = [
        hint
        for hint in schema["join_hints"]
        if allowed_tables is None or all(table in allowed_tables for table in tables_in_hint(hint))
    ]

    return {
        "user": user,
        "tables": tables,
        "join_hints": join_hints,
    }


def tables_in_hint(hint: str) -> set[str]:
    tables: set[str] = set()
    for side in hint.split("->"):
        table = side.strip().split(".", maxsplit=1)[0]
        if table:
            tables.add(table)
    return tables
