"use client";

import { FormEvent, useMemo, useState } from "react";

import type { QueryResponse } from "@/lib/types";

const users = [
  {
    id: "admin",
    label: "Admin",
    description: "Toàn quyền đọc dữ liệu MVP",
  },
  {
    id: "staff",
    label: "Staff",
    description: "Đọc dữ liệu khám chữa bệnh, ẩn billing nhạy cảm",
  },
  {
    id: "user",
    label: "User",
    description: "Chỉ đọc dữ liệu phân tích vận hành",
  },
];

const suggestions = [
  "Có bao nhiêu bệnh nhân theo giới tính?",
  "Top 10 bệnh hoặc chẩn đoán phổ biến nhất là gì?",
  "Có bao nhiêu bệnh nhân từng có chẩn đoán liên quan đến Diabetes?",
  "Top 10 thuốc xuất hiện nhiều nhất là gì?",
  "Có bao nhiêu lượt khám theo từng loại encounter?",
  "Top 10 thủ thuật phổ biến nhất là gì?",
];

export default function Home() {
  const [question, setQuestion] = useState(suggestions[0]);
  const [userId, setUserId] = useState("admin");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const columns = useMemo(() => {
    if (!response?.rows?.length) {
      return [];
    }
    return Object.keys(response.rows[0]);
  }, [response]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    setIsLoading(true);
    setResponse(null);

    try {
      const result = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, userId }),
      });
      const payload = (await result.json()) as QueryResponse;
      setResponse(payload);
    } catch (error) {
      setResponse({
        ok: false,
        question,
        userId,
        sql: "",
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
        <div className="status-pill">MCP-aware RBAC demo</div>
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="panel">
            <h2>Role</h2>
            <div className="role-list">
              {users.map((user) => (
                <button
                  className={userId === user.id ? "role active" : "role"}
                  key={user.id}
                  onClick={() => setUserId(user.id)}
                  type="button"
                >
                  <span>{user.label}</span>
                  <small>{user.description}</small>
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2>Questions</h2>
            <div className="suggestions">
              {suggestions.map((item) => (
                <button
                  key={item}
                  onClick={() => {
                    setQuestion(item);
                    setResponse(null);
                  }}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        </aside>

        <section className="main-panel">
          <form className="query-form" onSubmit={submit}>
            <label htmlFor="question">Question</label>
            <textarea
              id="question"
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
              value={question}
            />
            <div className="actions">
              <button disabled={isLoading || !question.trim()} type="submit">
                {isLoading ? "Running..." : "Run query"}
              </button>
              <span>as {userId}</span>
            </div>
          </form>

          <div className="result-grid">
            <section className="panel">
              <div className="section-heading">
                <h2>Generated SQL</h2>
                {response && <span className={response.ok ? "badge ok" : "badge error"}>{response.ok ? "OK" : "Blocked"}</span>}
              </div>
              <pre className="sql-box">{response?.sql || "SQL will appear here after running a question."}</pre>
              {response?.error && <p className="error-text">{response.error}</p>}
            </section>

            <section className="panel">
              <h2>Explanation</h2>
              <p className="explanation">
                {response?.explanation || "Kết quả sẽ được giải thích ngắn gọn sau khi query chạy thành công."}
              </p>
            </section>
          </div>

          <section className="panel table-panel">
            <div className="section-heading">
              <h2>Rows</h2>
              <span className="muted">{response ? `${response.rowCount} rows` : "No result"}</span>
            </div>
            <div className="table-wrap">
              {response?.rows?.length ? (
                <table>
                  <thead>
                    <tr>
                      {columns.map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {response.rows.slice(0, 50).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {columns.map((column) => (
                          <td key={column}>{String(row[column] ?? "")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty">No rows to display.</div>
              )}
            </div>
          </section>
        </section>
      </section>
    </main>
  );
}
