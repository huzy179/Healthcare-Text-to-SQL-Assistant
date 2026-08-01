import { NextResponse } from "next/server";

import { writeAudit } from "@/lib/audit";
import { runQuery } from "@/lib/db";
import { explainRows } from "@/lib/explain";
import { generateSqlWithLlm } from "@/lib/llm";
import { addDefaultLimit, validateSql } from "@/lib/sql";
import { canReadSql } from "@/lib/users";

export async function POST(request: Request) {
  const started = performance.now();
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

  let generatedSql = body.sql?.trim() || "";
  let modelReasoning = "";
  if (mode === "question") {
    try {
      const generated = await generateSqlWithLlm(question, userId);
      generatedSql = generated.sql;
      modelReasoning = generated.reasoning;
    } catch (error) {
      writeAudit({
        event: "query",
        userId,
        mode,
        question,
        sql: "",
        ok: false,
        error: error instanceof Error ? error.message : "llm_generation_failed",
        latencyMs: Math.round(performance.now() - started),
      });
      return NextResponse.json({
        ok: false,
        question,
        userId,
        mode,
        sql: "",
        rows: [],
        rowCount: 0,
        explanation: "",
        error: error instanceof Error ? error.message : "llm_generation_failed",
      });
    }
  }
  const validation = validateSql(generatedSql);
  if (!validation.ok) {
    writeAudit({
      event: "query",
      userId,
      mode,
      question,
      sql: validation.sql,
      ok: false,
      error: validation.error,
      latencyMs: Math.round(performance.now() - started),
    });
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
    writeAudit({
      event: "query",
      userId,
      mode,
      question,
      sql: validation.sql,
      ok: false,
      error: permission.error,
      latencyMs: Math.round(performance.now() - started),
    });
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
    writeAudit({
      event: "query",
      userId,
      mode,
      question,
      sql: limitedSql,
      ok: true,
      error: null,
      latencyMs: Math.round(performance.now() - started),
      rowCount: rows.length,
    });
    return NextResponse.json({
      ok: true,
      question,
      userId,
      mode,
      sql: limitedSql,
      rows,
      rowCount: rows.length,
      explanation: [modelReasoning, explainRows(rows)].filter(Boolean).join(" "),
      error: null,
    });
  } catch (error) {
    writeAudit({
      event: "query",
      userId,
      mode,
      question,
      sql: validation.sql,
      ok: false,
      error: error instanceof Error ? error.message : "query_failed",
      latencyMs: Math.round(performance.now() - started),
    });
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
