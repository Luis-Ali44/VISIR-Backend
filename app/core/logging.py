import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):


    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "nivel": record.levelname,
            "mensaje": record.getMessage(),
        }
        if hasattr(record, "data") and isinstance(record.data, dict):
            payload.update(record.data)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str = "rag_fiscal") -> logging.Logger:
    return logging.getLogger(name)
