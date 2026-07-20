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
  sql: string;
  rows: Record<string, unknown>[];
  rowCount: number;
  explanation: string;
  error: string | null;
};
