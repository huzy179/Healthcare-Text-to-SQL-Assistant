import { NextResponse } from "next/server";

import { runQuery } from "@/lib/db";
import { explainRows } from "@/lib/explain";
import { generateSqlWithLlm } from "@/lib/llm";
import { addDefaultLimit, validateSql } from "@/lib/sql";
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

  let generatedSql = body.sql?.trim() || "";
  let modelReasoning = "";
  if (mode === "question") {
    try {
      const generated = await generateSqlWithLlm(question, userId);
      generatedSql = generated.sql;
      modelReasoning = generated.reasoning;
    } catch (error) {
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
      explanation: [modelReasoning, explainRows(rows)].filter(Boolean).join(" "),
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
