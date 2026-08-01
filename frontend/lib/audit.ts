import fs from "node:fs";
import path from "node:path";

type AuditEvent = {
  event: string;
  userId?: string;
  mode?: string;
  question?: string;
  sql?: string;
  ok: boolean;
  error?: string | null;
  latencyMs?: number;
  rowCount?: number;
};

const auditPath = process.env.AUDIT_LOG_PATH || path.join(process.cwd(), "reports", "audit_log.jsonl");

export function writeAudit(event: AuditEvent) {
  const record = {
    timestamp: new Date().toISOString(),
    service: "frontend",
    ...event,
  };

  try {
    fs.mkdirSync(path.dirname(auditPath), { recursive: true });
    fs.appendFileSync(auditPath, JSON.stringify(record) + "\n", "utf-8");
  } catch {
    // Audit logging must never break the user query path.
  }
}
