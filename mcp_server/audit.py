import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "/app/reports/audit_log.jsonl"))


def write_audit(event: dict[str, Any]) -> None:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "mcp-server",
        **event,
    }
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass
