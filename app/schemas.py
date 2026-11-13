from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
Category = Literal["sales", "support", "other"]
Priority = Literal["low", "medium", "high"]
InquiryStatus = Literal["new", "in_progress", "resolved"]
Summary = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=10000)
]


class InquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: Name
    email: EmailStr = Field(max_length=254)
    message: Message
    category: Category | None = None
    priority: Priority = "medium"
    ai_summary: Summary | None = None


class InquiryRead(InquiryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: Category | None
    priority: Priority
    status: InquiryStatus
    ai_summary: str | None
    created_at: datetime


class InquiryStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InquiryStatus
    expected_status: InquiryStatus | None = None


class InquiryPage(BaseModel):
    items: list[InquiryRead]
    total: int
    limit: int
    offset: int


class InquiryStats(BaseModel):
    total: int
    high_priority: int
    sales: int
    support: int
    other: int
    unclassified: int
    new: int
    in_progress: int
    resolved: int


class InquiryQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search: str = Field(default="", max_length=200)
    category: Literal["sales", "support", "other", "unclassified"] | None = None
    priority: Priority | None = None
    status: InquiryStatus | None = None
    sort_by: Literal["created_at", "customer_name", "priority"] = "created_at"
    sort_dir: Literal["asc", "desc"] = "desc"
