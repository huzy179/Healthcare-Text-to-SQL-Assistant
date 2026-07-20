import { NextResponse } from "next/server";

import { runQuery } from "@/lib/db";
import { explainRows } from "@/lib/explain";
import { addDefaultLimit, generateSql, validateSql } from "@/lib/sql";
import { canReadSql } from "@/lib/users";

export async function POST(request: Request) {
  const body = (await request.json()) as { mode?: "question" | "sql"; question?: string; sql?: string; userId?: string };
  const mode = body.mode || "question";
  const question = body.question?.trim() || "";
  const userId = body.userId || "user";

  if (mode === "question" && !question) {
    return NextResponse.json(
      { ok: false, error: "question_required", question, userId, mode, sql: "", rows: [], rowCount: 0 },
      { status: 400 },
    );
  }

  const generatedSql = mode === "sql" ? body.sql?.trim() || "" : generateSql(question);
  const validation = validateSql(generatedSql);
  if (!validation.ok) {
    return NextResponse.json({
      ok: false,
      question,
      userId,
      mode,
      sql: validation.sql,
      rows: [],
      rowCount: 0,
      explanation: "",
      error: validation.error,
    });
  }

  const permission = canReadSql(userId, validation.sql);
  if (!permission.ok) {
    return NextResponse.json({
      ok: false,
      question,
      userId,
      mode,
      sql: validation.sql,
      rows: [],
      rowCount: 0,
      explanation: "",
      error: permission.error,
    });
  }

  try {
    const limitedSql = addDefaultLimit(validation.sql, Number(process.env.MCP_MAX_ROWS || 200));
    const rows = await runQuery(limitedSql);
    return NextResponse.json({
      ok: true,
      question,
      userId,
      mode,
      sql: limitedSql,
      rows,
      rowCount: rows.length,
      explanation: explainRows(rows),
      error: null,
    });
  } catch (error) {
    return NextResponse.json({
      ok: false,
      question,
      userId,
      mode,
      sql: validation.sql,
      rows: [],
      rowCount: 0,
      explanation: "",
      error: error instanceof Error ? error.message : "query_failed",
    });
  }
}
