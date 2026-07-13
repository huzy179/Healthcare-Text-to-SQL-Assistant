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
    referenced = re.findall(
        r"\bfrom\s+([a-z_][a-z0-9_]*)|\bjoin\s+([a-z_][a-z0-9_]*)",
        table_scan_sql,
    )
    table_names = {name for pair in referenced for name in pair if name}
    unknown_tables = sorted(table_names - KNOWN_TABLES)
    if unknown_tables:
        return False, cleaned, "unknown_table:" + ",".join(unknown_tables)

    return True, cleaned, None
