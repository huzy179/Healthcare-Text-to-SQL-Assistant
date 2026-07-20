import fs from "node:fs";
import path from "node:path";

import type { DemoUser, UserRole } from "./types";

type RolePolicy = {
  allowed_tables: string[];
  denied_columns: Record<string, string[]>;
};

type UserPolicy = {
  users: DemoUser[];
  roles: Record<UserRole, RolePolicy>;
  default_user_id: string;
};

const policyPathCandidates = [
  path.join(process.cwd(), "mcp_server", "users.json"),
  path.join(process.cwd(), "..", "mcp_server", "users.json"),
];

export function loadPolicy(): UserPolicy {
  const policyPath = policyPathCandidates.find((candidate) => fs.existsSync(candidate));
  if (!policyPath) {
    throw new Error("users_policy_not_found");
  }
  return JSON.parse(fs.readFileSync(policyPath, "utf-8")) as UserPolicy;
}

export function listUsers(): DemoUser[] {
  return loadPolicy().users;
}

export function getUser(userId?: string): DemoUser | null {
  const policy = loadPolicy();
  const resolved = userId || policy.default_user_id;
  return policy.users.find((user) => user.id === resolved || user.username === resolved) || null;
}

export function canReadSql(userId: string | undefined, sql: string): { ok: boolean; error: string | null } {
  const policy = loadPolicy();
  const user = getUser(userId);
  if (!user) {
    return { ok: false, error: "unknown_user" };
  }

  const role = policy.roles[user.role];
  const tables = referencedTables(sql);
  const allowed = role.allowed_tables.includes("*") ? null : new Set(role.allowed_tables);

  if (allowed) {
    const blockedTables = tables.filter((table) => !allowed.has(table));
    if (blockedTables.length > 0) {
      return { ok: false, error: `permission_denied_table:${blockedTables.join(",")}` };
    }
  }

  const blockedColumns = deniedColumns(sql, tables, role.denied_columns);
  if (blockedColumns.length > 0) {
    return { ok: false, error: `permission_denied_column:${blockedColumns.join(",")}` };
  }

  return { ok: true, error: null };
}

export function referencedTables(sql: string): string[] {
  const tables = new Set<string>();
  const pattern = /\b(?:from|join)\s+([a-z_][a-z0-9_]*)\b/gi;
  for (const match of sql.matchAll(pattern)) {
    tables.add(match[1].toLowerCase());
  }
  return [...tables];
}

function deniedColumns(
  sql: string,
  tables: string[],
  deniedByTable: Record<string, string[]>,
): string[] {
  const lowered = sql.toLowerCase();
  const blocked = new Set<string>();

  for (const table of tables) {
    const denied = deniedByTable[table] || [];
    if (denied.length === 0) {
      continue;
    }

    if (denied.includes("*")) {
      blocked.add(`${table}.*`);
      continue;
    }

    if (new RegExp(`select\\s+\\*|${table}\\s*\\.\\s*\\*`, "i").test(sql)) {
      denied.forEach((column) => blocked.add(`${table}.${column}`));
    }

    for (const column of denied) {
      const unqualified = new RegExp(`\\b${column}\\b`, "i");
      const qualified = new RegExp(`\\b${table}\\s*\\.\\s*${column}\\b`, "i");
      if (qualified.test(lowered) || (tables.length === 1 && unqualified.test(lowered))) {
        blocked.add(`${table}.${column}`);
      }
    }
  }

  return [...blocked].sort();
}
