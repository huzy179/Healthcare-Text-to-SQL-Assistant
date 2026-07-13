from fastapi import FastAPI

from .config import get_settings
from .database import Database
from .llm import LlmClient
from .schemas import TextToSqlRequest, TextToSqlResponse
from .sql_validator import validate_sql


settings = get_settings()
database = Database(settings.database_url)
llm = LlmClient(
    base_url=settings.vllm_base_url,
    model=settings.vllm_model,
    api_key=settings.vllm_api_key,
    prompt_template=settings.prompt_file.read_text(encoding="utf-8"),
    schema_context=settings.schema_file.read_text(encoding="utf-8"),
)

app = FastAPI(title="Healthcare Text-to-SQL API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/text-to-sql/query", response_model=TextToSqlResponse)
def text_to_sql(payload: TextToSqlRequest) -> TextToSqlResponse:
    generated_sql = llm.generate_sql(payload.question)
    is_valid, sql, validation_error = validate_sql(generated_sql)

    rows = []
    execution_error = None
    if payload.execute and is_valid:
        try:
            rows = database.query(sql)
        except Exception as error:  # noqa: BLE001
            execution_error = str(error)

    explanation = None
    if is_valid and execution_error is None:
        explanation = "SQL đã được validate và thực thi trên PostgreSQL."

    return TextToSqlResponse(
        question=payload.question,
        sql=sql,
        is_valid_sql=is_valid,
        validation_error=validation_error,
        rows=rows,
        row_count=len(rows),
        execution_error=execution_error,
        explanation=explanation,
    )
