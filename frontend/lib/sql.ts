const knownTables = new Set([
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
]);

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

export function generateSql(question: string): string {
  const normalized = question.toLowerCase();

  if (normalized.includes("giới tính") || normalized.includes("gender")) {
    return "SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC";
  }
  if (normalized.includes("diabetes")) {
    return "SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%diabetes%'";
  }
  if (normalized.includes("hypertension") || normalized.includes("tăng huyết áp")) {
    return "SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%hypertension%'";
  }
  if (normalized.includes("thuốc") || normalized.includes("medication")) {
    return "SELECT description, COUNT(*) AS total FROM medications GROUP BY description ORDER BY total DESC LIMIT 10";
  }
  if (normalized.includes("thủ thuật") || normalized.includes("procedure")) {
    return "SELECT description, COUNT(*) AS total FROM procedures GROUP BY description ORDER BY total DESC LIMIT 10";
  }
  if (normalized.includes("lượt khám") || normalized.includes("encounter")) {
    return "SELECT encounterclass, COUNT(*) AS total_encounters FROM encounters GROUP BY encounterclass ORDER BY total_encounters DESC";
  }
  if (normalized.includes("bệnh") || normalized.includes("chẩn đoán") || normalized.includes("condition")) {
    return "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10";
  }
  return "SELECT COUNT(*) AS total_patients FROM patients";
}

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

  const unknown = referencedTables(cleaned).filter((table) => !knownTables.has(table));
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
