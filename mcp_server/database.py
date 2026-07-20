from typing import Any
from datetime import date, datetime
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row


class Database:
    def __init__(self, database_url: str, query_timeout_ms: int) -> None:
        self.database_url = database_url
        self.query_timeout_ms = int(query_timeout_ms)

    def query(self, sql: str) -> list[dict[str, Any]]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(f"SET LOCAL statement_timeout = {self.query_timeout_ms}")
                cursor.execute(sql)
                rows = cursor.fetchall()
        return [json_safe(dict(row)) for row in rows]

    def schema(self) -> list[dict[str, Any]]:
        sql = """
        SELECT
          table_name,
          column_name,
          data_type,
          ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name IN (
            'patients',
            'encounters',
            'conditions',
            'medications',
            'observations',
            'procedures',
            'claims',
            'providers',
            'organizations',
            'payers'
          )
        ORDER BY table_name, ordinal_position
        """
        return self.query(sql)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value
