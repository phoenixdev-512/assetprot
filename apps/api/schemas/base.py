from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    meta: dict[str, Any] = {}
    error: dict[str, Any] | None = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool
    data: list[T]
    meta: dict[str, Any] = {}
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)
