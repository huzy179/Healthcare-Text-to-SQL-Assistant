import fs from "node:fs";
import path from "node:path";

import { loadPolicy, getUser } from "./users";
import type { VisibleSchema } from "./types";

type SchemaMetadata = {
  tables: VisibleSchema["tables"];
  join_hints: string[];
  prompt_rules: string[];
};

const metadataPathCandidates = [
  path.join(process.cwd(), "mcp_server", "schema_metadata.json"),
  path.join(process.cwd(), "..", "mcp_server", "schema_metadata.json"),
];

export function loadSchemaMetadata(): SchemaMetadata {
  const metadataPath = metadataPathCandidates.find((candidate) => fs.existsSync(candidate));
  if (!metadataPath) {
    throw new Error("schema_metadata_not_found");
  }
  return JSON.parse(fs.readFileSync(metadataPath, "utf-8")) as SchemaMetadata;
}

export function visibleSchema(userId?: string): VisibleSchema {
  const metadata = loadSchemaMetadata();
  const policy = loadPolicy();
  const user = getUser(userId);
  if (!user) {
    return { user: null, tables: {}, join_hints: [], prompt_rules: [], error: "unknown_user" };
  }

  const role = policy.roles[user.role];
  const allowed = role.allowed_tables.includes("*") ? null : new Set(role.allowed_tables);
  const tables: VisibleSchema["tables"] = {};

  for (const [table, columns] of Object.entries(metadata.tables)) {
    if (allowed && !allowed.has(table)) {
      continue;
    }
    const denied = new Set(role.denied_columns[table] || []);
    if (denied.has("*")) {
      continue;
    }
    tables[table] = columns.filter((column) => !denied.has(column.name));
  }

  return {
    user,
    tables,
    prompt_rules: metadata.prompt_rules,
    join_hints: metadata.join_hints.filter((hint) => {
      if (!allowed) return true;
      return hint
        .split("->")
        .map((side) => side.trim().split(".")[0])
        .every((table) => allowed.has(table));
    }),
  };
}
