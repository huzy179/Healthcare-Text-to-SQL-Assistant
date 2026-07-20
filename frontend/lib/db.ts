import { Pool } from "pg";

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString:
        process.env.DATABASE_URL ||
        "postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
      max: 4,
    });
  }
  return pool;
}

export async function runQuery(sql: string): Promise<Record<string, unknown>[]> {
  const client = await getPool().connect();
  try {
    await client.query("BEGIN READ ONLY");
    await client.query(`SET LOCAL statement_timeout = ${Number(process.env.MCP_QUERY_TIMEOUT_MS || 30000)}`);
    const result = await client.query(sql);
    await client.query("COMMIT");
    return result.rows;
  } catch (error) {
    await client.query("ROLLBACK").catch(() => undefined);
    throw error;
  } finally {
    client.release();
  }
}
