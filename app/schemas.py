from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_text(value: str, minimum_length: int) -> str:
    cleaned = value.strip()
    if len(cleaned) < minimum_length:
        raise ValueError(f"Value must contain at least {minimum_length} non-space characters")
    return cleaned


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _normalize_text(value, minimum_length=3)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _normalize_text(value, minimum_length=5)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5, max_length=2000)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _normalize_text(value, minimum_length=3)

    @field_validator("description")
    @classmethod
    def validate_optional_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _normalize_text(value, minimum_length=5)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: str
    database: str


class TicketMetricsResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int


class DeleteResponse(BaseModel):
    message: str
