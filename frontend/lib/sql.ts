import { loadSchemaMetadata } from "./schema";

function knownTables(): Set<string> {
  return new Set(Object.keys(loadSchemaMetadata().tables));
}

const blockedKeywords = [
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
  "merge",
  "vacuum",
  "analyze",
  "listen",
  "notify",
];

const dangerousFunctions = [
  "dblink",
  "dblink_connect",
  "lo_export",
  "lo_import",
  "pg_sleep",
  "pg_read_binary_file",
  "pg_read_file",
  "pg_stat_file",
  "pg_terminate_backend",
];

const heavyTables = new Set(["observations", "procedures", "claims", "encounters", "medications"]);

export function validateSql(sql: string): { ok: boolean; sql: string; error: string | null } {
  const cleaned = sql.trim().replace(/;+\s*$/g, "");
  const lowered = cleaned.toLowerCase();

  if (!cleaned) {
    return { ok: false, sql: cleaned, error: "empty_sql" };
  }
  if (!lowered.startsWith("select")) {
    return { ok: false, sql: cleaned, error: "non_select" };
  }
  if (cleaned.includes(";")) {
    return { ok: false, sql: cleaned, error: "multiple_statements" };
  }
  if (/--|\/\*/.test(cleaned)) {
    return { ok: false, sql: cleaned, error: "comment_not_allowed" };
  }

  for (const keyword of blockedKeywords) {
    if (new RegExp(`\\b${keyword}\\b`, "i").test(cleaned)) {
      return { ok: false, sql: cleaned, error: `blocked_keyword:${keyword}` };
    }
  }
  for (const fn of dangerousFunctions) {
    if (new RegExp(`\\b${fn}\\s*\\(`, "i").test(cleaned)) {
      return { ok: false, sql: cleaned, error: `dangerous_function:${fn}` };
    }
  }

  const tables = referencedTables(cleaned);
  const unknown = tables.filter((table) => !knownTables().has(table));
  if (unknown.length > 0) {
    return { ok: false, sql: cleaned, error: `unknown_table:${unknown.join(",")}` };
  }
  if (isPotentiallyHeavy(cleaned, tables)) {
    return { ok: false, sql: cleaned, error: "query_too_heavy:add_limit_or_aggregate" };
  }

  return { ok: true, sql: cleaned, error: null };
}

export function addDefaultLimit(sql: string, maxRows: number): string {
  if (/\blimit\s+\d+\b/i.test(sql)) {
    return sql;
  }
  return `SELECT * FROM (${sql}) AS frontend_limited_query LIMIT ${maxRows}`;
}

export function referencedTables(sql: string): string[] {
  const tables = new Set<string>();
  const pattern = /\b(?:from|join)\s+([a-z_][a-z0-9_]*)\b/gi;
  for (const match of sql.matchAll(pattern)) {
    tables.add(match[1].toLowerCase());
  }
  return [...tables];
}

function isPotentiallyHeavy(sql: string, tables: string[]): boolean {
  if (!tables.some((table) => heavyTables.has(table))) {
    return false;
  }
  if (/\blimit\s+\d+\b/i.test(sql)) {
    return false;
  }
  if (/\b(count|sum|avg|min|max)\s*\(/i.test(sql)) {
    return false;
  }
  return true;
}
