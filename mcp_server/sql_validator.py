import re


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


def strip_code_fence(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def normalize_sql(sql: str) -> str:
    cleaned = strip_code_fence(sql).strip()
    return re.sub(r";+\s*$", "", cleaned)


def referenced_tables(sql: str) -> set[str]:
    lowered = re.sub(r"extract\s*\([^)]*\)", "extract_expr", sql.lower())
    referenced = re.findall(
        r"\bfrom\s+([a-z_][a-z0-9_]*)|\bjoin\s+([a-z_][a-z0-9_]*)",
        lowered,
    )
    return {name for pair in referenced for name in pair if name}


def validate_sql(sql: str) -> tuple[bool, str, str | None]:
    cleaned = normalize_sql(sql)
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

    unknown_tables = sorted(referenced_tables(cleaned) - KNOWN_TABLES)
    if unknown_tables:
        return False, cleaned, "unknown_table:" + ",".join(unknown_tables)

    return True, cleaned, None


def add_default_limit(sql: str, max_rows: int) -> str:
    cleaned = normalize_sql(sql)
    if re.search(r"\blimit\s+\d+\b", cleaned, flags=re.IGNORECASE):
        return cleaned
    return f"SELECT * FROM ({cleaned}) AS mcp_limited_query LIMIT {max_rows}"
