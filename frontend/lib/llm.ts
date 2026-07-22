import OpenAI from "openai";

import { visibleSchema } from "./schema";

type SqlGeneration = {
  sql: string;
  reasoning: string;
};

export async function generateSqlWithLlm(question: string, userId: string): Promise<SqlGeneration> {
  const baseURL = process.env.LLM_BASE_URL || process.env.OPENAI_BASE_URL;
  const apiKey = process.env.LLM_API_KEY || process.env.OPENAI_API_KEY || (baseURL ? "local" : "");
  if (!apiKey) {
    throw new Error("LLM_API_KEY_missing");
  }

  const client = new OpenAI({
    apiKey,
    baseURL,
  });
  const schema = visibleSchema(userId);
  const model = process.env.LLM_MODEL || process.env.OPENAI_MODEL || "gpt-5-mini";
  const systemPrompt =
    "You generate safe PostgreSQL SELECT queries for a healthcare analytics database. Return only JSON with keys sql and reasoning. The sql must be a single SELECT statement. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY, GRANT, REVOKE, CALL, or EXECUTE.";
  const userPrompt = [
    "Use this role-filtered schema and join hints.",
    JSON.stringify(schema),
    "",
    "Question:",
    question,
    "",
    "Rules:",
    ...schema.prompt_rules.map((rule) => `- ${rule}`),
  ].join("\n");

  if (baseURL) {
    const completion = await client.chat.completions.create({
      model,
      temperature: 0,
      max_tokens: Number(process.env.LLM_MAX_TOKENS ?? "192"),
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
    });
    return parseSqlGeneration(completion.choices[0]?.message?.content || "");
  }

  const response = await client.responses.create({
    model,
    input: [
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: userPrompt,
      },
    ],
  });

  return parseSqlGeneration(response.output_text);
}

function parseSqlGeneration(text: string): SqlGeneration {
  const cleaned = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
  try {
    const parsed = JSON.parse(cleaned) as Partial<SqlGeneration>;
    return {
      sql: parsed.sql?.trim() || "",
      reasoning: parsed.reasoning?.trim() || "",
    };
  } catch {
    return {
      sql: cleaned,
      reasoning: "Model returned raw SQL instead of JSON.",
    };
  }
}
