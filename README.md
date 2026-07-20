# Healthcare PostgreSQL MCP Server

Project này cung cấp MCP server để LLM truy vấn dữ liệu y tế Synthea trong PostgreSQL bằng các database tools an toàn.

Luồng chính:

```text
User
-> LLM / MCP client
-> Healthcare PostgreSQL MCP server
-> SQL validation
-> PostgreSQL readonly user
-> Query result
-> LLM summarizes answer
```

MCP server không fine-tune model và không chạy FastAPI API riêng. LLM client sẽ tự gọi tools để xem schema, validate SQL và chạy query.

## Dataset

Dữ liệu nằm tại:

```text
data/synthea_csv
```

Các bảng MVP:

- `patients`: thông tin bệnh nhân.
- `encounters`: lượt khám, cấp cứu, nhập viện, tái khám.
- `conditions`: chẩn đoán và bệnh.
- `medications`: thuốc được kê hoặc sử dụng.
- `observations`: chỉ số lâm sàng, xét nghiệm, vital signs.
- `procedures`: thủ thuật và quy trình điều trị.
- `claims`: claim và billing.
- `providers`: bác sĩ hoặc nhân sự y tế.
- `organizations`: bệnh viện, phòng khám, cơ sở y tế.
- `payers`: bảo hiểm hoặc bên chi trả.

`claims_transactions.csv` và các bảng lớn/phụ trợ khác chưa nằm trong MVP.

## Quick Start

Tạo file môi trường:

```bash
cp .env.example .env
```

Chạy PostgreSQL:

```bash
docker compose up -d postgres
```

PostgreSQL expose ở host port `5433`.

Kiểm tra số dòng:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/check_tables.sql
```

Chạy sample queries:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/sample_queries.sql
```

Cài dependency MCP server:

```bash
cd mcp_server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chạy MCP server bằng stdio:

```bash
python server.py
```

## Docker

Các lệnh Docker phổ biến đã được gom trong `Makefile`:

```bash
make setup
make up
make build
make check-tables
make eval
```

Build MCP image:

```bash
docker compose build mcp-server
```

Chạy PostgreSQL bằng Docker:

```bash
docker compose up -d postgres
```

Chạy evaluation trong Docker:

```bash
docker compose run --rm eval
```

Chạy MCP server qua Docker Compose:

```bash
docker compose run --rm -T mcp-server
```

Vì MCP server dùng `stdio`, service này không expose HTTP port. MCP client nên gọi command Docker Compose thay vì gọi URL.

## MCP Tools

Server hiện expose các tools:

- `get_schema`: trả schema PostgreSQL, kiểu cột và join hints.
- `get_users`: trả danh sách user/role tạm để test phân quyền đọc.
- `validate_readonly_sql`: kiểm tra SQL có phải một câu `SELECT` an toàn không.
- `check_sql_syntax`: dùng PostgreSQL `EXPLAIN` để kiểm tra cú pháp sau khi qua safety validation.
- `run_readonly_query`: validate rồi chạy SQL bằng readonly DB user, có timeout và default row limit.
- `explain_query_result`: sinh giải thích ngắn bằng tiếng Việt từ question, SQL và rows.
- `ask_database`: trả lời một số câu hỏi phân tích phổ biến bằng SQL template cơ bản.

Flow nên dùng với LLM:

```text
1. Gọi get_schema.
2. Áp dụng schema-aware prompting để sinh PostgreSQL SELECT SQL.
3. Gọi validate_readonly_sql.
4. Gọi check_sql_syntax để PostgreSQL parse query.
5. Nếu hợp lệ, gọi run_readonly_query.
6. Dùng explanation trả về hoặc gọi explain_query_result.
```

## MCP Client Config

Ví dụ cấu hình client dùng stdio:

```json
{
  "mcpServers": {
    "healthcare-postgres": {
      "command": "python",
      "args": ["/absolute/path/to/healthcare-text-to-sql/mcp_server/server.py"],
      "env": {
        "DATABASE_URL": "postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare",
        "MCP_QUERY_TIMEOUT_MS": "30000",
        "MCP_MAX_ROWS": "200"
      }
    }
  }
}
```

Ví dụ cấu hình MCP client dùng Docker Compose:

```json
{
  "mcpServers": {
    "healthcare-postgres": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "/home/huy/workspace/healthcare-text-to-sql/docker-compose.yml",
        "run",
        "--rm",
        "-T",
        "mcp-server"
      ]
    }
  }
}
```

Trước khi dùng config Docker này, chạy:

```bash
docker compose up -d postgres
docker compose build mcp-server
```

## Safety

MCP server áp dụng các lớp bảo vệ:

- Kết nối bằng `healthcare_readonly`.
- Chỉ cho phép một statement bắt đầu bằng `SELECT`.
- Chặn `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `COPY`, `GRANT`, `REVOKE`.
- Chặn tên bảng ngoài 10 bảng MVP.
- Chặn query vào bảng user không được phép đọc theo `mcp_server/users.json`.
- Kiểm tra cú pháp bằng PostgreSQL `EXPLAIN`.
- Thêm default `LIMIT` nếu query chưa có limit.
- Set PostgreSQL `statement_timeout` cho mỗi query.

## Text-to-SQL Và Evaluation

Pipeline chi tiết nằm ở:

```text
docs/text_to_sql_pipeline.md
```

Chạy evaluation dry-run bằng expected SQL:

```bash
python3 scripts/evaluate_text_to_sql.py
```

Script đo:

- Exact Match Accuracy.
- Execution Accuracy.
- Average response time.

Nếu có output SQL từ LLM/MCP client:

```bash
python3 scripts/evaluate_text_to_sql.py --generated-file outputs/generated_sql.jsonl
```

## Cấu Trúc Dự Án

```text
healthcare-text-to-sql/
├── data/
│   └── synthea_csv/
├── database/
│   ├── init/
│   └── scripts/
├── datasets/
│   └── text_to_sql/
├── docs/
├── reports/
├── scripts/
├── mcp_server/
│   ├── server.py
│   ├── database.py
│   ├── sql_validator.py
│   ├── config.py
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

`datasets/text_to_sql` được giữ lại làm bộ câu hỏi tham chiếu để kiểm thử thủ công với MCP client.

## Ví Dụ SQL

Số bệnh nhân theo giới tính:

```sql
SELECT gender, COUNT(*) AS total
FROM patients
GROUP BY gender
ORDER BY total DESC;
```

Top 10 bệnh phổ biến:

```sql
SELECT description, COUNT(*) AS total
FROM conditions
GROUP BY description
ORDER BY total DESC
LIMIT 10;
```

Số lượt khám theo năm:

```sql
SELECT EXTRACT(YEAR FROM start) AS year, COUNT(*) AS total_encounters
FROM encounters
GROUP BY year
ORDER BY year;
```

## Dọn Kiến Trúc Cũ

Các phần FastAPI backend, frontend placeholder, fine-tune/vLLM và baseline eval runner đã được bỏ khỏi runtime vì kiến trúc mới để LLM gọi database tools qua MCP.
