# Mermaid Flow

Tài liệu này mô tả chi tiết các luồng runtime chính của hệ thống.

## 1. Docker Runtime Tổng Thể

```mermaid
flowchart LR
    subgraph Host["Host / WSL"]
        Browser["Browser<br/>http://localhost:3000"]
        Env[".env<br/>Postgres + LLM + vLLM config"]
        CSV["data/synthea_csv<br/>Synthea CSV files"]
        HFCache["HF_HOME cache<br/>Hugging Face model files"]
    end

    subgraph Docker["Docker Compose Network"]
        Frontend["frontend<br/>Next.js standalone<br/>port 3000"]
        Postgres["postgres<br/>PostgreSQL 16<br/>port 5432 in network<br/>5433 on host"]
        VLLM["vllm<br/>OpenAI-compatible API<br/>port 8000"]
        Eval["eval<br/>Python eval runner"]
        MCP["mcp-server<br/>MCP stdio tools"]
    end

    subgraph RuntimeFiles["Files copied or mounted"]
        Metadata["mcp_server/schema_metadata.json<br/>tables + join_hints + prompt_rules + examples"]
        Users["mcp_server/users.json<br/>admin/staff/user role policy"]
        InitSQL["database/init/*.sql<br/>create tables + import + indexes + readonly user"]
        Reports["reports/*.md / *.jsonl"]
        Outputs["outputs/generated_sql.jsonl"]
    end

    Browser -->|HTTP| Frontend
    Env --> Frontend
    Env --> Postgres
    Env --> VLLM
    CSV -->|read-only import mount| Postgres
    HFCache -->|model cache mount| VLLM

    Frontend -->|LLM_BASE_URL=http://vllm:8000/v1| VLLM
    Frontend -->|DATABASE_URL readonly| Postgres
    Frontend --> Metadata
    Frontend --> Users

    Eval --> VLLM
    Eval --> Postgres
    Eval --> Metadata
    Eval --> Users
    Eval --> Outputs
    Eval --> Reports

    MCP --> Postgres
    MCP --> Metadata
    MCP --> Users
    Postgres --> InitSQL
```

## 2. Frontend Runtime: Question Mode

```mermaid
flowchart TD
    U["User nhập câu hỏi tự nhiên<br/>VD: Có bao nhiêu bệnh nhân nam?"] --> UI["Next.js page<br/>frontend/app/page.tsx"]

    UI --> UsersAPI["GET /api/users"]
    UsersAPI --> LoadUsers["loadPolicy()<br/>frontend/lib/users.ts"]
    LoadUsers --> UsersJSON["mcp_server/users.json"]
    UsersJSON --> RoleList["Return demo users<br/>admin / staff / user"]
    RoleList --> UI

    UI --> SchemaAPI["GET /api/schema?userId=..."]
    SchemaAPI --> VisibleSchema["visibleSchema(userId)<br/>frontend/lib/schema.ts"]
    VisibleSchema --> Metadata["schema_metadata.json"]
    VisibleSchema --> UsersPolicy["users.json role policy"]
    Metadata --> FilterTables["Filter allowed tables"]
    UsersPolicy --> FilterTables
    FilterTables --> FilterColumns["Remove denied columns"]
    FilterColumns --> SchemaResult["Visible schema + join_hints<br/>prompt_rules + prompt_examples"]
    SchemaResult --> UI

    UI --> QueryAPI["POST /api/query<br/>mode=question"]
    QueryAPI --> Generate["generateSqlWithLlm()<br/>frontend/lib/llm.ts"]
    Generate --> SchemaAgain["visibleSchema(userId)<br/>same role-filtered schema"]
    SchemaAgain --> CompactPrompt["compactSchemaForPrompt()<br/>tables as name:type strings<br/>join hints kept"]
    CompactPrompt --> Prompt["Build prompt<br/>system + schema + rules + examples + question"]
    Prompt --> OpenAIClient["OpenAI-compatible client"]
    OpenAIClient --> VLLM["vLLM /v1/chat/completions<br/>qwen-coder-3b"]
    VLLM --> RawModel["Raw model text"]
    RawModel --> ParseJSON["parseSqlGeneration()<br/>expect JSON {sql, reasoning}"]

    ParseJSON --> Validation["validateSql(sql)<br/>frontend/lib/sql.ts"]
    Validation --> SafetyDecision{"Valid SELECT?"}
    SafetyDecision -->|No| ValidationError["Return error<br/>empty_sql / non_select<br/>multiple_statements<br/>blocked_keyword / unknown_table"]
    SafetyDecision -->|Yes| Permission["canReadSql(userId, sql)<br/>frontend/lib/users.ts"]

    Permission --> PermissionDecision{"Allowed by role?"}
    PermissionDecision -->|No| PermissionError["Return error<br/>permission_denied_table<br/>permission_denied_column"]
    PermissionDecision -->|Yes| Limit["addDefaultLimit(sql, MCP_MAX_ROWS)<br/>wrap query if no LIMIT"]

    Limit --> RunQuery["runQuery(limitedSql)<br/>frontend/lib/db.ts"]
    RunQuery --> DB["PostgreSQL<br/>healthcare_readonly user"]
    DB --> Rows["Rows"]
    Rows --> Explain["explainRows(rows)<br/>frontend/lib/explain.ts"]
    Explain --> Response["JSON response<br/>ok, sql, rows, rowCount,<br/>explanation, error=null"]

    Response --> UIResult["UI renders<br/>generated SQL<br/>result table<br/>latency<br/>explanation<br/>history"]
    ValidationError --> UIResult
    PermissionError --> UIResult
```

## 3. Frontend Runtime: SQL Manual Mode

```mermaid
flowchart TD
    U["User nhập SQL thủ công"] --> UI["Next.js page"]
    UI --> QueryAPI["POST /api/query<br/>mode=sql<br/>sql=..."]

    QueryAPI --> SkipLLM["Skip LLM generation"]
    SkipLLM --> Validation["validateSql(sql)"]

    Validation --> Checks["Checks:<br/>1. trim semicolon<br/>2. not empty<br/>3. starts with SELECT<br/>4. no extra semicolon<br/>5. no blocked keyword<br/>6. known tables only"]
    Checks --> Valid{"Valid?"}

    Valid -->|No| Error["Return validation error"]
    Valid -->|Yes| RBAC["canReadSql(userId, sql)"]
    RBAC --> Allowed{"Allowed?"}

    Allowed -->|No| PermissionError["Return permission error"]
    Allowed -->|Yes| Limit["addDefaultLimit(sql, maxRows)"]
    Limit --> DB["PostgreSQL readonly connection"]
    DB --> Rows["Rows"]
    Rows --> Explain["explainRows(rows)"]
    Explain --> UIResult["Show rows + SQL + explanation"]
    Error --> UIResult
    PermissionError --> UIResult
```

## 4. Schema-Aware Prompt Construction

```mermaid
flowchart TD
    Start["Need SQL for a question"] --> UserRole["Resolve userId<br/>default user if missing"]
    UserRole --> Policy["Load users.json"]
    UserRole --> Metadata["Load schema_metadata.json"]

    Policy --> Role["Find role policy<br/>admin / staff / user"]
    Metadata --> Tables["Full MVP schema"]
    Metadata --> Hints["Join hints"]
    Metadata --> Rules["Prompt rules"]
    Metadata --> Examples["Prompt examples"]

    Role --> AllowedTables["allowed_tables"]
    Role --> DeniedColumns["denied_columns"]
    Tables --> ApplyTables["Keep only allowed tables"]
    AllowedTables --> ApplyTables
    ApplyTables --> ApplyColumns["Remove denied columns"]
    DeniedColumns --> ApplyColumns

    ApplyColumns --> Visible["Visible schema"]
    Hints --> FilterHints["Keep join hints whose tables are visible"]
    AllowedTables --> FilterHints

    Visible --> Compact["Compact prompt schema<br/>table -> column:type notes"]
    FilterHints --> Compact
    Rules --> Prompt["Final prompt"]
    Examples --> Prompt
    Compact --> Prompt
    Prompt --> LLM["LLM receives only role-visible schema"]
```

## 5. SQL Safety + RBAC Path

```mermaid
flowchart TD
    SQL["Generated or manual SQL"] --> Normalize["Normalize SQL<br/>strip code fences / trailing semicolon"]
    Normalize --> Empty{"Empty?"}
    Empty -->|Yes| E1["empty_sql"]
    Empty -->|No| Select{"Single SELECT?"}

    Select -->|No| E2["non_select or multiple_statements"]
    Select -->|Yes| Blocked["Scan blocked keywords<br/>insert/update/delete/drop/alter/create/truncate/copy/grant/revoke/call/execute"]

    Blocked --> HasBlocked{"Blocked keyword?"}
    HasBlocked -->|Yes| E3["blocked_keyword"]
    HasBlocked -->|No| Tables["Extract referenced tables<br/>FROM / JOIN"]

    Tables --> Known{"All tables known?"}
    Known -->|No| E4["unknown_table"]
    Known -->|Yes| RoleTables["Check role allowed_tables"]

    RoleTables --> TableAllowed{"Tables allowed?"}
    TableAllowed -->|No| E5["permission_denied_table"]
    TableAllowed -->|Yes| Columns["Check denied_columns"]

    Columns --> ColumnAllowed{"Columns allowed?"}
    ColumnAllowed -->|No| E6["permission_denied_column"]
    ColumnAllowed -->|Yes| Limit["Add default LIMIT if missing"]

    Limit --> Readonly["Run with PostgreSQL readonly user"]
    Readonly --> Rows["Rows returned"]

    E1 --> Reject["Reject before database"]
    E2 --> Reject
    E3 --> Reject
    E4 --> Reject
    E5 --> Reject
    E6 --> Reject
```

## 6. MCP Stdio Runtime

```mermaid
sequenceDiagram
    actor User
    participant Client as LLM / MCP Client
    participant MCP as mcp_server/server.py
    participant Meta as schema_metadata.json
    participant Policy as users.json
    participant Validator as sql_validator.py
    participant Perm as permissions.py
    participant DB as PostgreSQL readonly

    User->>Client: Ask healthcare data question
    Client->>MCP: get_users()
    MCP->>Policy: load users
    Policy-->>MCP: admin/staff/user
    MCP-->>Client: user list

    Client->>MCP: get_schema(user_id)
    MCP->>DB: information_schema columns
    DB-->>MCP: real table/column/type rows
    MCP->>Meta: load metadata
    Meta-->>MCP: notes, join_hints, prompt_rules, examples
    MCP->>Perm: filter_schema_for_user(user_id, schema)
    Perm->>Policy: load role policy
    Policy-->>Perm: allowed_tables + denied_columns
    Perm-->>MCP: visible schema
    MCP-->>Client: role-filtered schema

    Client->>Client: Generate PostgreSQL SELECT SQL
    Client->>MCP: validate_readonly_sql(sql, user_id)
    MCP->>Validator: validate_sql(sql)
    Validator-->>MCP: normalized_sql or validation_error
    MCP->>Perm: can_read_sql(user_id, normalized_sql)
    Perm-->>MCP: allowed or permission_error
    MCP-->>Client: validation result + limited_sql

    Client->>MCP: check_sql_syntax(sql, user_id)
    MCP->>Validator: validate_sql + RBAC again
    MCP->>DB: EXPLAIN normalized_sql
    DB-->>MCP: parse OK or syntax error
    MCP-->>Client: syntax result

    Client->>MCP: run_readonly_query(sql, user_id)
    MCP->>Validator: validate_sql + add_default_limit
    MCP->>Perm: can_read_sql
    MCP->>DB: SELECT as healthcare_readonly
    DB-->>MCP: rows
    MCP->>MCP: explain_rows(rows)
    MCP-->>Client: rows + row_count + explanation

    Client->>MCP: explain_query_result(question, sql, rows)
    MCP-->>Client: Vietnamese explanation
    Client-->>User: Final natural language answer
```

## 7. Data Import Runtime

```mermaid
flowchart TD
    Start["docker compose up postgres"] --> PGInit["PostgreSQL initdb starts<br/>only when volume is empty"]
    PGInit --> CreateTables["01_create_tables.sql<br/>create MVP tables"]
    CreateTables --> ImportCSV["02_import_csv.sql<br/>COPY CSV files from /data/synthea_csv"]
    ImportCSV --> Indexes["03_create_indexes.sql<br/>indexes for joins/filtering"]
    Indexes --> Readonly["04_create_readonly_user.sql<br/>create healthcare_readonly<br/>grant SELECT only"]
    Readonly --> Healthcheck["pg_isready healthcheck"]
    Healthcheck --> Healthy["postgres service healthy"]

    Healthy --> FrontendReady["frontend can connect"]
    Healthy --> MCPReady["mcp/eval can connect"]

    subgraph Tables["Imported MVP tables"]
        Patients["patients"]
        Encounters["encounters"]
        Conditions["conditions"]
        Medications["medications"]
        Observations["observations"]
        Procedures["procedures"]
        Claims["claims"]
        Providers["providers"]
        Organizations["organizations"]
        Payers["payers"]
    end

    ImportCSV --> Tables
```

## 8. vLLM Startup Runtime

```mermaid
flowchart TD
    Start["make frontend-vllm / make dev"] --> Compose["docker compose --profile vllm up -d vllm"]
    Compose --> Image["vllm/vllm-openai:latest"]
    Image --> Args["Command args:<br/>--model Qwen/Qwen2.5-Coder-3B-Instruct-AWQ<br/>--served-model-name qwen-coder-3b<br/>--max-model-len 2048<br/>--gpu-memory-utilization 0.85<br/>--enforce-eager"]

    Args --> Cache{"Model in HF cache?"}
    Cache -->|No| Download["Download model from Hugging Face<br/>may take minutes"]
    Cache -->|Yes| Load["Load model weights"]
    Download --> Load

    Load --> GPU["Allocate GPU memory<br/>KV cache + model weights"]
    GPU --> Warmup["Engine warmup / kernels"]
    Warmup --> Ready["Application startup complete"]
    Ready --> API["OpenAI-compatible routes ready<br/>/v1/models<br/>/v1/chat/completions"]

    API --> Frontend["Frontend can call LLM"]
    API --> Eval["Eval can generate SQL"]

    Start --> Logs["make vllm-logs"]
    Logs --> Ready
```

## 9. Eval-Gold Runtime

```mermaid
flowchart TD
    Cmd["make eval-gold"] --> EvalContainer["eval container"]
    EvalContainer --> Script["scripts/evaluate_text_to_sql.py<br/>--mode gold"]
    Script --> Dataset["datasets/text_to_sql/eval_questions.jsonl"]
    Dataset --> Expected["Read expected_sql for each question"]

    Expected --> Validate["validate_sql(expected_sql)"]
    Validate --> RBAC["can_read_sql(admin, expected_sql)"]
    RBAC --> Execute["Run expected_sql with readonly DB"]
    Execute --> Rows["Expected rows"]

    Rows --> Metrics["Gold metrics:<br/>valid reference SQL<br/>executable reference SQL<br/>average execution time"]
    Metrics --> GoldResults["reports/text_to_sql_gold_results.jsonl"]
    Metrics --> GoldSummary["reports/text_to_sql_gold_summary.md"]

    GoldSummary --> Note["This validates DB + expected SQL + validator.<br/>It does NOT measure LLM quality."]
```

## 10. Eval-LLM Runtime

```mermaid
flowchart TD
    Cmd["make eval-llm"] --> GenerateTarget["generate-sql target"]
    GenerateTarget --> EnsureVLLM["Ensure vLLM service is running"]
    EnsureVLLM --> GenScript["scripts/generate_text_to_sql.py"]

    GenScript --> Dataset["eval_questions.jsonl"]
    GenScript --> Metadata["schema_metadata.json"]
    GenScript --> Users["users.json"]
    GenScript --> Prompt["Build compact schema-aware prompt<br/>rules + examples"]
    Prompt --> VLLM["POST http://vllm:8000/v1/chat/completions"]
    VLLM --> Raw["Raw JSON or raw SQL text"]
    Raw --> Parse["parse_sql_generation()"]
    Parse --> OutputSQL["outputs/generated_sql.jsonl<br/>id + generated_sql + reasoning + latency + raw"]

    OutputSQL --> EvalTarget["eval-generated target"]
    EvalTarget --> EvalScript["evaluate_text_to_sql.py<br/>--mode generated"]
    EvalScript --> ExpectedSQL["expected_sql from dataset"]
    EvalScript --> GeneratedSQL["generated_sql from outputs"]

    ExpectedSQL --> ExecExpected["Validate + execute expected SQL"]
    GeneratedSQL --> ExecGenerated["Validate + execute generated SQL"]

    ExecExpected --> ExpectedRows["Expected rows"]
    ExecGenerated --> GeneratedRows["Generated rows or error"]

    ExpectedSQL --> Exact["Exact Match<br/>normalized SQL string equality"]
    GeneratedSQL --> Exact

    ExpectedRows --> Execution["Execution Accuracy<br/>compare row values"]
    GeneratedRows --> Execution

    ExecGenerated --> ErrorType["Classify error:<br/>empty_sql<br/>safety_error<br/>permission_error<br/>wrong_table<br/>wrong_column<br/>wrong_filter<br/>wrong_limit<br/>wrong_join<br/>wrong_aggregation<br/>syntax_error<br/>execution_mismatch"]

    Exact --> Report["LLM eval report"]
    Execution --> Report
    ErrorType --> Report

    Report --> Results["reports/text_to_sql_llm_results.jsonl"]
    Report --> Summary["reports/text_to_sql_llm_summary.md"]
```

## 11. Error Handling Runtime

```mermaid
flowchart TD
    Request["/api/query request"] --> TryLLM{"Question mode?"}

    TryLLM -->|Yes| LLMCall["Call vLLM"]
    LLMCall --> LLMOK{"LLM response OK?"}
    LLMOK -->|No| LLMError["Return llm_generation_failed<br/>or connection error"]
    LLMOK -->|Yes| Parse["Parse model SQL"]

    TryLLM -->|No, SQL mode| Parse

    Parse --> Validate["Validate SQL"]
    Validate --> Valid{"Valid?"}
    Valid -->|No| ValidationError["Return validation error<br/>no DB call"]
    Valid -->|Yes| RBAC["Check role permissions"]

    RBAC --> Allowed{"Allowed?"}
    Allowed -->|No| PermissionError["Return permission error<br/>no DB call"]
    Allowed -->|Yes| Query["Run readonly query"]

    Query --> QueryOK{"DB query OK?"}
    QueryOK -->|No| DBError["Return PostgreSQL error<br/>syntax/runtime/cast/column errors"]
    QueryOK -->|Yes| Success["Return rows + explanation"]

    LLMError --> UI["Frontend shows error panel"]
    ValidationError --> UI
    PermissionError --> UI
    DBError --> UI
    Success --> UI
```

## 12. Role Permission Runtime

```mermaid
flowchart TD
    User["Selected userId"] --> Resolve["getUser(userId)"]
    Resolve --> Role{"Role?"}

    Role --> Admin["admin"]
    Role --> Staff["staff"]
    Role --> BasicUser["user"]

    Admin --> AdminTables["allowed_tables = *<br/>all MVP tables visible"]
    Staff --> StaffTables["clinical/operational tables visible<br/>sensitive columns denied"]
    BasicUser --> UserTables["aggregate/operational tables visible<br/>direct patient/claim access restricted"]

    AdminTables --> SchemaFilter["visibleSchema()"]
    StaffTables --> SchemaFilter
    UserTables --> SchemaFilter

    SchemaFilter --> PromptSchema["LLM sees only allowed schema"]

    PromptSchema --> GeneratedSQL["LLM/generated SQL"]
    GeneratedSQL --> SQLTables["Extract SQL tables"]
    GeneratedSQL --> SQLColumns["Extract SQL columns/stars"]

    SQLTables --> TableCheck["Table permission check"]
    SQLColumns --> ColumnCheck["Denied column check"]

    TableCheck --> Decision{"Allowed at runtime?"}
    ColumnCheck --> Decision
    Decision -->|Yes| Run["Run query"]
    Decision -->|No| Reject["Reject query even if LLM generated it"]
```

## 13. Current Architecture Boundary

```mermaid
flowchart LR
    subgraph DemoFrontend["Current demo web app"]
        Browser["Browser"]
        NextAPI["Next.js API routes"]
        SharedSchemaFE["Shared metadata loader"]
        FEValidator["Frontend validator/RBAC"]
    end

    subgraph MCPBoundary["MCP backend/tool surface"]
        MCPServer["MCP stdio server"]
        SharedSchemaMCP["Same schema metadata"]
        MCPValidator["MCP validator/RBAC"]
    end

    subgraph Shared["Shared runtime assets"]
        Metadata["schema_metadata.json"]
        Users["users.json"]
        DB["PostgreSQL readonly"]
        LLM["vLLM OpenAI-compatible API"]
    end

    Browser --> NextAPI
    NextAPI --> SharedSchemaFE
    NextAPI --> FEValidator
    NextAPI --> LLM
    NextAPI --> DB

    MCPServer --> SharedSchemaMCP
    MCPServer --> MCPValidator
    MCPServer --> DB

    SharedSchemaFE --> Metadata
    SharedSchemaMCP --> Metadata
    FEValidator --> Users
    MCPValidator --> Users

    Note["Important:<br/>Frontend demo does not call MCP over network today.<br/>It shares schema/rules/validation ideas with MCP.<br/>MCP is the backend/tool interface for MCP clients."]
```
