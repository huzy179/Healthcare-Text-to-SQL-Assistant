# Healthcare Text-to-SQL Assistant

Healthcare Text-to-SQL Assistant cho phép người dùng hỏi dữ liệu y tế bằng tiếng Việt hoặc tiếng Anh, sau đó hệ thống sinh SQL an toàn, chạy trên PostgreSQL và trả kết quả phân tích.

Ví dụ:

```text
Có bao nhiêu bệnh nhân bị Diabetes trong năm 2026?
```

SQL kỳ vọng:

```sql
SELECT COUNT(DISTINCT patient) AS total_patients
FROM conditions
WHERE description ILIKE '%diabetes%'
  AND start >= '2026-01-01'
  AND start < '2027-01-01';
```

## Trạng Thái Hiện Tại

Đã có:

- Raw healthcare CSV dataset.
- PostgreSQL Docker setup đã import 10 bảng MVP.
- Sample SQL queries đã chạy được.
- Prompt mẫu cho Text-to-SQL và explanation.
- Baseline Text-to-SQL evaluation pipeline.
- Backend NestJS skeleton cho endpoint Text-to-SQL.
- Placeholder cho frontend, fine-tune và docs.

Đang làm tiếp:

- Kết nối model LLM thật vào baseline evaluation.
- Phân tích lỗi model và cải thiện prompt/schema context.
- Xây baseline Text-to-SQL API trước khi fine-tune.

## Kiến Trúc

```text
User
-> Frontend
-> NestJS Backend
-> Schema Service
-> Prompt Builder
-> LLM / vLLM
-> SQL Validator
-> PostgreSQL
-> Result Formatter
-> Response
```

MVP chưa cần fine-tune ngay. Hướng tốt nhất là làm baseline bằng prompt + schema trước, sau đó mới tạo dataset Question-SQL và fine-tune LoRA/QLoRA.

## Dataset

Dữ liệu nằm tại:

```text
data/synthea_csv
```

Các bảng chính:

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

`claims_transactions.csv` rất lớn nên chưa đưa vào MVP. Bảng này nên xử lý ở phase nâng cao sau khi database và use case chính đã ổn định.

## Quick Start

Tạo file môi trường:

```bash
cp .env.example .env
```

Chạy PostgreSQL:

```bash
docker compose up -d postgres
```

PostgreSQL được expose ở host port `5433` để tránh đụng các project khác đang dùng `5432`.

Kiểm tra container:

```bash
docker compose ps
```

Kiểm tra số dòng ước lượng sau import:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/check_tables.sql
```

Chạy sample queries:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/sample_queries.sql
```

Chạy baseline evaluation dry-run:

```bash
python3 scripts/run_baseline_eval.py --dry-run
```

Chạy backend:

```bash
cd backend
npm install
npm run start:dev
```

Gọi API:

```bash
curl -X POST http://localhost:3000/text-to-sql/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 10 bệnh phổ biến nhất là gì?"}'
```

Nếu cần import lại từ đầu:

```bash
docker compose down -v
docker compose up -d postgres
```

## Cấu Trúc Dự Án

```text
healthcare-text-to-sql/
├── data/
│   └── synthea_csv/
├── database/
│   ├── init/
│   │   ├── 01_create_tables.sql
│   │   ├── 02_import_csv.sql
│   │   └── 03_create_indexes.sql
│   ├── scripts/
│   │   ├── check_tables.sql
│   │   ├── sample_queries.sql
│   │   └── reset_db.sql
│   └── README.md
├── datasets/
│   └── text_to_sql/
│       ├── sample.jsonl
│       └── eval_questions.jsonl
├── finetune/
│   ├── configs/
│   └── scripts/
├── inference/
│   ├── prompts/
│   └── vllm/
├── backend/
│   ├── src/
│   └── package.json
├── frontend/
├── docs/
├── reports/
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Text-to-SQL Pipeline

```text
Natural language question
-> Load relevant schema
-> Build prompt
-> Generate SQL
-> Validate SQL safety
-> Execute query on PostgreSQL
-> Format result table
-> Generate short explanation
```

Validator cần đảm bảo:

- Chỉ cho phép `SELECT`.
- Chặn `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `COPY`.
- Chặn nhiều statement trong một lần chạy.
- Kiểm tra tên bảng và tên cột có trong schema.
- Thêm `LIMIT` mặc định cho query trả nhiều dòng.
- Database user nên chỉ có quyền đọc.

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

Bệnh nhân có nhiều chẩn đoán nhất:

```sql
SELECT
  p.id,
  p.first_name,
  p.last_name,
  COUNT(c.code) AS total_conditions
FROM patients p
JOIN conditions c ON c.patient = p.id
GROUP BY p.id, p.first_name, p.last_name
ORDER BY total_conditions DESC
LIMIT 10;
```

## Fine-Tuning

Fine-tune dùng để giúp model học:

- Schema healthcare CSV trong project.
- Cách đặt tên bảng và cột.
- SQL PostgreSQL đúng format.
- Cách join các bảng healthcare.
- Cách trả về SQL ngắn, an toàn, đúng yêu cầu.

Dataset mẫu nằm ở:

```text
datasets/text_to_sql/sample.jsonl
```

Format đề xuất:

```json
{
  "instruction": "Generate PostgreSQL SQL from the healthcare question and schema. Return only SQL.",
  "schema": "patients(id, gender), conditions(patient, description, start)",
  "question": "Top 10 bệnh phổ biến nhất là gì?",
  "sql": "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;"
}
```

## vLLM

Sau khi có model fine-tuned hoặc merged model, có thể serve bằng vLLM:

```bash
MODEL_PATH=./finetune/outputs/merged_model ./inference/vllm/serve.sh
```

Backend sẽ gọi OpenAI-compatible endpoint:

```text
POST /v1/chat/completions
```

## Evaluation

Các chỉ số nên đo:

- Execution accuracy.
- SQL exact match.
- Syntax error rate.
- Schema error rate.
- Safety violation rate.
- Average latency.
- Tokens per second.
- Successful query rate.

`Execution accuracy` là quan trọng nhất vì nhiều câu SQL khác nhau vẫn có thể trả cùng kết quả đúng.

## Roadmap

### Phase 1: Database

- Dựng PostgreSQL bằng Docker.
- Tạo bảng.
- Import CSV.
- Tạo index.
- Viết sample queries.

### Phase 2: Baseline Text-to-SQL

- Tạo prompt.
- Gọi base LLM.
- Sinh SQL.
- Validate SQL.
- Execute query.

### Phase 3: Backend

- NestJS API skeleton.
- Schema prompt tĩnh ban đầu.
- SQL validator cơ bản.
- Query executor.
- Result formatter.
- Nâng cấp schema service động từ PostgreSQL metadata.

### Phase 4: Dataset Fine-Tune

- Viết 300-500 question-SQL pairs.
- Tách train/validation/test.
- Chuẩn hóa JSONL.
- Đánh giá trên test set.

### Phase 5: Fine-Tune Và vLLM

- Fine-tune LoRA/QLoRA.
- Serve bằng vLLM.
- Benchmark latency/throughput.
- So sánh base model và fine-tuned model.

### Phase 6: UI Demo

- Chat interface.
- Hiển thị generated SQL.
- Hiển thị result table.
- Hiển thị explanation.
- Lưu lịch sử câu hỏi.

## CV Summary

```text
Built a Healthcare Text-to-SQL Assistant that converts natural language questions into PostgreSQL queries, validates SQL safety, executes queries on a healthcare CSV-based PostgreSQL database, and returns analytics results with explanations. The system is designed for fine-tuned LLM inference with vLLM and evaluated using execution accuracy.
```
