"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import type { QueryResponse, VisibleSchema } from "@/lib/types";

type Mode = "question" | "sql";
type HistoryItem = Pick<QueryResponse, "ok" | "question" | "sql" | "userId" | "rowCount" | "error"> & {
  id: number;
  elapsedMs: number;
  mode: Mode;
};

const users = [
  { id: "admin", label: "Admin", description: "Toàn quyền đọc dữ liệu MVP" },
  { id: "staff", label: "Staff", description: "Đọc dữ liệu khám chữa bệnh, ẩn billing nhạy cảm" },
  { id: "user", label: "User", description: "Chỉ đọc dữ liệu phân tích vận hành" },
];

const suggestions = [
  "Có bao nhiêu bệnh nhân theo giới tính?",
  "Top 10 bệnh hoặc chẩn đoán phổ biến nhất là gì?",
  "Có bao nhiêu bệnh nhân từng có chẩn đoán liên quan đến Diabetes?",
  "Top 10 thuốc xuất hiện nhiều nhất là gì?",
  "Có bao nhiêu lượt khám theo từng loại encounter?",
  "Top 10 thủ thuật phổ biến nhất là gì?",
];

const sqlExamples = [
  "SELECT COUNT(*) AS total_patients FROM patients",
  "SELECT ssn FROM patients LIMIT 5",
  "SELECT encounterclass, COUNT(*) AS total FROM encounters GROUP BY encounterclass ORDER BY total DESC",
  "SELECT status1, SUM(outstanding1) AS total_outstanding FROM claims GROUP BY status1 ORDER BY total_outstanding DESC",
];

export default function Home() {
  const [mode, setMode] = useState<Mode>("question");
  const [question, setQuestion] = useState(suggestions[0]);
  const [sql, setSql] = useState(sqlExamples[0]);
  const [userId, setUserId] = useState("admin");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [schema, setSchema] = useState<VisibleSchema | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const columns = useMemo(() => {
    if (!response?.rows?.length) return [];
    return Object.keys(response.rows[0]);
  }, [response]);

  useEffect(() => {
    fetch(`/api/schema?userId=${encodeURIComponent(userId)}`)
      .then((result) => result.json())
      .then((payload: VisibleSchema) => setSchema(payload))
      .catch(() => setSchema(null));
  }, [userId]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    setIsLoading(true);
    setResponse(null);
    const started = performance.now();

    try {
      const result = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, question, sql, userId }),
      });
      const payload = (await result.json()) as QueryResponse;
      setResponse(payload);
      setHistory((current) => [
        {
          id: Date.now(),
          ok: payload.ok,
          question,
          sql: payload.sql,
          userId,
          rowCount: payload.rowCount,
          error: payload.error,
          elapsedMs: Math.round(performance.now() - started),
          mode,
        },
        ...current,
      ].slice(0, 8));
    } catch (error) {
      setResponse({
        ok: false,
        mode,
        question,
        userId,
        sql: mode === "sql" ? sql : "",
        rows: [],
        rowCount: 0,
        explanation: "",
        error: error instanceof Error ? error.message : "request_failed",
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Healthcare PostgreSQL</p>
          <h1>Text-to-SQL Console</h1>
        </div>
        <div className="status-strip">
          <span>Readonly DB</span>
          <span>RBAC</span>
          <span>SELECT only</span>
        </div>
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="panel">
            <div className="section-heading">
              <h2>Role</h2>
              <span className="muted">{schema ? Object.keys(schema.tables).length : 0} tables</span>
            </div>
            <div className="role-list">
              {users.map((user) => (
                <button className={userId === user.id ? "role active" : "role"} key={user.id} onClick={() => setUserId(user.id)} type="button">
                  <span>{user.label}</span>
                  <small>{user.description}</small>
                </button>
              ))}
            </div>
          </div>

          <div className="panel schema-panel">
            <h2>Visible Schema</h2>
            <div className="schema-list">
              {schema &&
                Object.entries(schema.tables).map(([table, fields]) => (
                  <details key={table}>
                    <summary>{table}</summary>
                    <div className="field-list">
                      {fields.map((field) => (
                        <span key={`${table}.${field.name}`}>{field.name}<small>{field.type}</small></span>
                      ))}
                    </div>
                  </details>
                ))}
            </div>
          </div>
        </aside>

        <section className="main-panel">
          <form className="query-form" onSubmit={submit}>
            <div className="mode-tabs">
              <button className={mode === "question" ? "active" : ""} onClick={() => setMode("question")} type="button">Question</button>
              <button className={mode === "sql" ? "active" : ""} onClick={() => setMode("sql")} type="button">SQL</button>
            </div>

            {mode === "question" ? (
              <>
                <label htmlFor="question">Natural language question</label>
                <textarea id="question" onChange={(event) => setQuestion(event.target.value)} rows={4} value={question} />
                <div className="quick-grid">
                  {suggestions.map((item) => (
                    <button key={item} onClick={() => setQuestion(item)} type="button">{item}</button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <label htmlFor="sql">Manual SQL for RBAC testing</label>
                <textarea className="sql-editor" id="sql" onChange={(event) => setSql(event.target.value)} rows={6} value={sql} />
                <div className="quick-grid">
                  {sqlExamples.map((item) => (
                    <button key={item} onClick={() => setSql(item)} type="button">{item}</button>
                  ))}
                </div>
              </>
            )}

            <div className="actions">
              <button disabled={isLoading || (mode === "question" ? !question.trim() : !sql.trim())} type="submit">
                {isLoading ? "Running..." : "Run"}
              </button>
              <span>as {userId}</span>
            </div>
          </form>

          <div className="result-grid">
            <section className="panel">
              <div className="section-heading">
                <h2>SQL</h2>
                {response && <span className={response.ok ? "badge ok" : "badge error"}>{response.ok ? "Executed" : "Blocked"}</span>}
              </div>
              <pre className="sql-box">{response?.sql || "SQL will appear here after running."}</pre>
              {response?.error && <p className="error-text">{response.error}</p>}
            </section>

            <section className="panel">
              <h2>Explanation</h2>
              <p className="explanation">{response?.explanation || "Kết quả sẽ được giải thích ngắn gọn sau khi query chạy thành công."}</p>
              <div className="metric-row">
                <span>{response ? response.rowCount : 0}<small>rows</small></span>
                <span>{history[0]?.elapsedMs ?? 0}<small>ms</small></span>
              </div>
            </section>
          </div>

          <section className="panel table-panel">
            <div className="section-heading">
              <h2>Rows</h2>
              <span className="muted">{response ? `${response.rowCount} rows returned` : "No result"}</span>
            </div>
            <div className="table-wrap">
              {response?.rows?.length ? (
                <table>
                  <thead>
                    <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
                  </thead>
                  <tbody>
                    {response.rows.slice(0, 50).map((row, rowIndex) => (
                      <tr key={rowIndex}>{columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty">No rows to display.</div>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>History</h2>
              <span className="muted">{history.length} recent</span>
            </div>
            <div className="history-list">
              {history.length ? history.map((item) => (
                <button key={item.id} onClick={() => {
                  setMode(item.mode);
                  setUserId(item.userId);
                  if (item.mode === "question") setQuestion(item.question);
                  setSql(item.sql);
                }} type="button">
                  <span className={item.ok ? "dot ok" : "dot error"} />
                  <strong>{item.mode}</strong>
                  <small>{item.userId} · {item.rowCount} rows · {item.elapsedMs} ms</small>
                  <code>{item.error || item.sql}</code>
                </button>
              )) : <div className="empty compact">No history yet.</div>}
            </div>
          </section>
        </section>
      </section>
    </main>
  );
}
