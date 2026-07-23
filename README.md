# Healthcare Text-to-SQL

Dự án import dữ liệu Synthea vào PostgreSQL, dùng LLM sinh PostgreSQL `SELECT`, validate query an toàn, chạy bằng user read-only, rồi hiển thị kết quả qua Next.js frontend.

Luồng chính:

```text
User -> Next.js FE / MCP client -> LLM -> SELECT SQL -> validator -> PostgreSQL readonly -> rows -> natural language explanation
```

Đọc tài liệu chính tại [docs/system_overview.md](docs/system_overview.md). Docs phụ đã chuyển vào `docs/archive/` để tránh nhiễu.

## Quick Start

Tạo/cập nhật `.env`:

```bash
make setup
```

Chạy PostgreSQL, vLLM và frontend:

```bash
make frontend-vllm
```

Mở frontend:

```text
http://localhost:3000
```

Nếu đang dùng WSL và lệnh `docker` không ăn, đặt biến `COMPOSE` khi chạy make:

```bash
make docker-desktop-up
```

## Environment

Các giá trị quan trọng trong `.env`:

```env
LLM_BASE_URL=http://vllm:8000/v1
LLM_API_KEY=local
LLM_MODEL=qwen-coder-3b

VLLM_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct-AWQ
VLLM_SERVED_MODEL_NAME=qwen-coder-3b
VLLM_API_KEY=local
VLLM_MAX_MODEL_LEN=2048
VLLM_GPU_MEMORY_UTILIZATION=0.85
```

`LLM_API_KEY_missing` nghĩa là frontend container chưa nhận được `LLM_API_KEY` hoặc chưa có `LLM_BASE_URL`. Sau khi sửa `.env`, recreate frontend:

```bash
make recreate-frontend
```

## Common Commands

```bash
make build              # build MCP/eval image
make build-frontend     # build Next.js image
make up                 # start PostgreSQL only
make frontend           # start PostgreSQL + frontend
make frontend-vllm      # start PostgreSQL + vLLM + frontend
make recreate-frontend  # reload frontend env
make health             # smoke test frontend schema/query path
make docker-desktop-up  # WSL Docker Desktop friendly startup
make vllm-logs          # follow vLLM logs
make frontend-logs      # follow frontend logs
make check-tables       # verify imported table row counts
make sample-queries     # run sample SQL
make eval-gold          # validate reference SQL + DB + validator
make eval-llm           # generate SQL with vLLM, then evaluate it
make down               # stop services
```

## MCP Tools

MCP server dùng `stdio`, không expose HTTP port. Tool hiện có:

- `get_users`
- `get_schema`
- `validate_readonly_sql`
- `check_sql_syntax`
- `run_readonly_query`
- `explain_query_result`

Schema-aware rules nằm ở [mcp_server/schema_metadata.json](mcp_server/schema_metadata.json). Frontend và MCP cùng đọc file này để tránh sửa case-by-case ở FE.

## Docs

- [docs/system_overview.md](docs/system_overview.md): tài liệu chính.
- [docs/mermaid_flow.md](docs/mermaid_flow.md): sơ đồ luồng.
- `docs/archive/`: tài liệu chi tiết cũ, chỉ mở khi cần.
