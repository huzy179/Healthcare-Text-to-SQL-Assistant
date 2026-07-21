import { loadPolicy, getUser } from "./users";
import type { VisibleSchema } from "./types";

const schema: Record<string, { name: string; type: string; notes?: string }[]> = {
  patients: [
    { name: "id", type: "text" },
    { name: "birthdate", type: "date" },
    { name: "deathdate", type: "date" },
    { name: "ssn", type: "text" },
    { name: "drivers", type: "text" },
    { name: "passport", type: "text" },
    { name: "first_name", type: "text" },
    { name: "last_name", type: "text" },
    { name: "gender", type: "text", notes: "Synthea uses coded values: M = male/nam, F = female/nu." },
    { name: "race", type: "text" },
    { name: "ethnicity", type: "text" },
    { name: "city", type: "text" },
    { name: "state", type: "text" },
    { name: "income", type: "numeric" },
  ],
  encounters: [
    { name: "id", type: "text" },
    { name: "start", type: "timestamptz" },
    { name: "stop", type: "timestamptz" },
    { name: "patient", type: "text" },
    { name: "organization", type: "text" },
    { name: "provider", type: "text" },
    { name: "payer", type: "text" },
    { name: "encounterclass", type: "text" },
    { name: "description", type: "text" },
    { name: "total_claim_cost", type: "numeric" },
  ],
  conditions: [
    { name: "start", type: "date" },
    { name: "stop", type: "date" },
    { name: "patient", type: "text" },
    { name: "encounter", type: "text" },
    { name: "code", type: "text" },
    { name: "description", type: "text" },
  ],
  medications: [
    { name: "start", type: "timestamptz" },
    { name: "patient", type: "text" },
    { name: "payer", type: "text" },
    { name: "encounter", type: "text" },
    { name: "description", type: "text" },
    { name: "totalcost", type: "numeric" },
  ],
  observations: [
    { name: "date", type: "timestamptz" },
    { name: "patient", type: "text" },
    { name: "encounter", type: "text" },
    { name: "description", type: "text" },
    { name: "value", type: "text" },
    { name: "units", type: "text" },
  ],
  procedures: [
    { name: "start", type: "date" },
    { name: "patient", type: "text" },
    { name: "encounter", type: "text" },
    { name: "description", type: "text" },
    { name: "base_cost", type: "numeric" },
  ],
  claims: [
    { name: "id", type: "text" },
    { name: "patientid", type: "text" },
    { name: "providerid", type: "text" },
    { name: "servicedate", type: "date" },
    { name: "status1", type: "text" },
    { name: "outstanding1", type: "numeric" },
  ],
  providers: [
    { name: "id", type: "text" },
    { name: "organization", type: "text" },
    { name: "name", type: "text" },
    { name: "speciality", type: "text" },
  ],
  organizations: [
    { name: "id", type: "text" },
    { name: "name", type: "text" },
    { name: "city", type: "text" },
    { name: "state", type: "text" },
    { name: "revenue", type: "numeric" },
  ],
  payers: [
    { name: "id", type: "text" },
    { name: "name", type: "text" },
    { name: "ownership", type: "text" },
    { name: "revenue", type: "numeric" },
  ],
};

const joinHints = [
  "encounters.patient -> patients.id",
  "conditions.patient -> patients.id",
  "conditions.encounter -> encounters.id",
  "medications.patient -> patients.id",
  "medications.encounter -> encounters.id",
  "observations.patient -> patients.id",
  "procedures.patient -> patients.id",
  "procedures.encounter -> encounters.id",
  "encounters.provider -> providers.id",
  "providers.organization -> organizations.id",
  "encounters.organization -> organizations.id",
  "encounters.payer -> payers.id",
];

export function visibleSchema(userId?: string): VisibleSchema {
  const policy = loadPolicy();
  const user = getUser(userId);
  if (!user) {
    return { user: null, tables: {}, join_hints: [], error: "unknown_user" };
  }

  const role = policy.roles[user.role];
  const allowed = role.allowed_tables.includes("*") ? null : new Set(role.allowed_tables);
  const tables: VisibleSchema["tables"] = {};

  for (const [table, columns] of Object.entries(schema)) {
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
    join_hints: joinHints.filter((hint) => {
      if (!allowed) return true;
      return hint
        .split("->")
        .map((side) => side.trim().split(".")[0])
        .every((table) => allowed.has(table));
    }),
  };
}
