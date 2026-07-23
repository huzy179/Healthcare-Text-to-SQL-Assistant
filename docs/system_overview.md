# System Overview

Đây là tài liệu chính của dự án. Nếu cần hiểu nhanh hệ thống, đọc file này trước.

## Mục Tiêu

Xây dựng hệ thống Text-to-SQL cho dữ liệu y tế Synthea:

```text
Synthea CSV -> PostgreSQL -> LLM sinh SELECT SQL -> validate -> readonly query -> giải thích kết quả
```

Các yêu cầu chính:

- Import Synthea vào PostgreSQL.
- Schema mô phỏng hệ thống quản lý lượt khám/lịch khám.
- Schema-aware prompting.
- Chỉ cho phép `SELECT`.
- Kết nối database bằng user read-only.
- Phân quyền theo role.
- Đánh giá Exact Match, Execution Accuracy và latency.

## Kiến Trúc Ngắn Gọn

```text
User
-> Next.js frontend
-> LLM OpenAI-compatible API
-> vLLM local model
-> generated SELECT SQL
-> SQL validator + RBAC
-> PostgreSQL readonly user
-> rows + Vietnamese explanation
```

MCP server là backend database tools cho LLM/MCP client:

```text
get_schema -> validate_readonly_sql -> check_sql_syntax -> run_readonly_query -> explain_query_result
```

Frontend hiện dùng cùng logic để demo web end-to-end.

## Chạy Hệ Thống

```bash
make setup
make frontend-vllm
```

Mở:

```text
http://localhost:3000
```

Nếu dùng WSL và `docker` không chạy:

```bash
make docker-desktop-up
```

Kiểm tra nhanh:

```bash
make ps
make health
make vllm-logs
```

## File Quan Trọng

| File | Vai trò |
|---|---|
| `.env` | Cấu hình Postgres, frontend, vLLM. |
| `docker-compose.yml` | Định nghĩa Postgres, frontend, vLLM, MCP/eval. |
| `mcp_server/schema_metadata.json` | Nguồn schema, join hints, prompt rules dùng chung. |
| `mcp_server/users.json` | User/role tạm để test RBAC. |
| `mcp_server/server.py` | MCP tools. |
| `mcp_server/sql_validator.py` | Validate SQL read-only. |
| `frontend/lib/llm.ts` | Gọi LLM sinh SQL. |
| `frontend/lib/schema.ts` | Đọc schema metadata và lọc theo role. |
| `frontend/app/api/query/route.ts` | API query của demo frontend. |

## Cấu Hình LLM/vLLM

Giá trị mặc định trong `.env`:

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

Nếu gặp `LLM_API_KEY_missing`, recreate frontend sau khi cập nhật `.env`:

```bash
make recreate-frontend
```

## Schema Và Prompt Rules

Không sửa case-by-case trong frontend.

Nếu LLM sinh sai do hiểu nhầm schema, sửa tại:

```text
mcp_server/schema_metadata.json
```

Ví dụ các rule quan trọng:

- `patients.gender`: dùng `M` cho nam, `F` cho nữ.
- Câu hỏi về thuốc dùng `medications.description`.
- `medications` không có cột `id`.
- Chỉ sinh một câu PostgreSQL `SELECT`.

## Phân Quyền

Role demo:

| Role | Quyền |
|---|---|
| `admin` | Xem toàn bộ bảng MVP. |
| `staff` | Xem dữ liệu vận hành/lâm sàng, hạn chế cột nhạy cảm và tài chính. |
| `user` | Xem dữ liệu aggregate/vận hành, không xem trực tiếp hồ sơ bệnh nhân. |

RBAC chạy ở hai lớp:

- Lọc schema trước khi gửi cho LLM.
- Kiểm tra SQL trước khi chạy query.

## Luồng Query

```text
1. User nhập câu hỏi.
2. Frontend lấy schema theo role.
3. LLM sinh JSON: { sql, reasoning }.
4. App validate SQL và quyền đọc.
5. App thêm LIMIT mặc định nếu cần.
6. PostgreSQL chạy bằng readonly user.
7. Frontend hiển thị SQL, rows, latency, explanation.
```

## Đánh Giá

Metrics chính:

- Exact Match Accuracy.
- Execution Accuracy.
- Response time.
- Syntax/schema/permission error rate.

Execution Accuracy quan trọng hơn Exact Match vì nhiều SQL khác nhau vẫn có thể trả cùng kết quả đúng.

Có hai chế độ eval:

```bash
make eval-gold
```

Chế độ này chỉ kiểm tra `expected_sql`, database, validator và RBAC. Nó không đo chất lượng LLM.

```bash
make eval-llm
```

Chế độ này gọi vLLM sinh SQL cho bộ câu hỏi, ghi vào `outputs/generated_sql.jsonl`, rồi so sánh với `expected_sql`.

Kết quả chính:

```text
reports/text_to_sql_gold_summary.md
reports/text_to_sql_llm_summary.md
reports/text_to_sql_llm_results.jsonl
```

Report LLM có phân loại lỗi như `wrong_column`, `wrong_table`, `syntax_error`, `permission_error`, `wrong_join`, `wrong_filter`, `wrong_aggregation`.

## Docs Phụ

Docs cũ đã được chuyển vào:

```text
docs/archive/
```

Chỉ mở archive khi cần chi tiết phục vụ báo cáo hoặc đối chiếu lịch sử thiết kế.
