from typing import Any
from pydantic import BaseModel, Field


class TextToSqlRequest(BaseModel):
    question: str = Field(min_length=1)
    execute: bool = True


class TextToSqlResponse(BaseModel):
    question: str
    sql: str
    is_valid_sql: bool
    validation_error: str | None = None
    rows: list[dict[str, Any]] = []
    row_count: int = 0
    execution_error: str | None = None
    explanation: str | None = None
