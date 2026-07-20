export type UserRole = "admin" | "staff" | "user";

export type DemoUser = {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  description: string;
};

export type QueryResponse = {
  ok: boolean;
  question: string;
  userId: string;
  mode?: "question" | "sql";
  sql: string;
  rows: Record<string, unknown>[];
  rowCount: number;
  explanation: string;
  error: string | null;
};

export type VisibleSchema = {
  user: DemoUser | null;
  tables: Record<string, { name: string; type: string }[]>;
  join_hints: string[];
  error?: string;
};
