import json
import logging
import os
from typing import Any, Dict

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # extras úteis
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            data.update(record.extra)
        return json.dumps(data, ensure_ascii=False)

def configure_logging():
    # não duplica handlers
    if getattr(configure_logging, "_configured", False):
        return
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    # limpa handlers default do uvicorn só no root; mantemos access logs padrão
    root.handlers = [handler]

    # deixa o uvicorn access em INFO para request logs
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    configure_logging._configured = True
