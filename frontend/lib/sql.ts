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
];

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

  for (const keyword of blockedKeywords) {
    if (new RegExp(`\\b${keyword}\\b`, "i").test(cleaned)) {
      return { ok: false, sql: cleaned, error: `blocked_keyword:${keyword}` };
    }
  }

  const unknown = referencedTables(cleaned).filter((table) => !knownTables().has(table));
  if (unknown.length > 0) {
    return { ok: false, sql: cleaned, error: `unknown_table:${unknown.join(",")}` };
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
