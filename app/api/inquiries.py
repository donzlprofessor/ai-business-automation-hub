from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db import get_db
from app.inquiry_queries import count_inquiries, inquiry_stats, read_inquiries
from app.models import Inquiry
from app.schemas import (
    InquiryCreate,
    InquiryPage,
    InquiryQuery,
    InquiryRead,
    InquiryStats,
    InquiryStatusUpdate,
)

router = APIRouter(prefix="/api/v1/inquiries", tags=["inquiries"])
Database = Annotated[Session, Depends(get_db)]
ReadQuery = Annotated[InquiryQuery, Query()]


@router.post("", response_model=InquiryRead, status_code=status.HTTP_201_CREATED)
def create_inquiry(payload: InquiryCreate, db: Database):
    inquiry = Inquiry(**payload.model_dump())
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry


@router.get("", response_model=list[InquiryRead])
def list_inquiries(db: Database, params: ReadQuery):
    return read_inquiries(db, params)


@router.get("/page", response_model=InquiryPage)
def paginated_inquiries(db: Database, params: ReadQuery):
    return InquiryPage(
        items=read_inquiries(db, params), total=count_inquiries(db, params),
        limit=params.limit, offset=params.offset,
    )


@router.get("/stats", response_model=InquiryStats)
def get_inquiry_stats(db: Database):
    return inquiry_stats(db)


@router.get("/{inquiry_id}", response_model=InquiryRead)
def get_inquiry(inquiry_id: UUID, db: Database):
    inquiry = db.get(Inquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry


@router.patch("/{inquiry_id}/status", response_model=InquiryRead)
def update_inquiry_status(inquiry_id: UUID, payload: InquiryStatusUpdate, db: Database):
    inquiry = db.get(Inquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    current = inquiry.status
    if payload.expected_status is not None and payload.expected_status != current:
        raise HTTPException(status_code=409, detail="Status changed. Reload the inquiry and retry.")
    if payload.status == current:
        return inquiry  # Repeated requests for the current state are harmless no-ops.

    allowed = {"new": "in_progress", "in_progress": "resolved", "resolved": "in_progress"}
    if allowed[current] != payload.status:
        raise HTTPException(
            status_code=409, detail=f"Cannot change status from {current} to {payload.status}.",
        )

    # Compare-and-set also protects against a concurrent writer after the initial read.
    result = db.execute(
        update(Inquiry).where(Inquiry.id == inquiry_id, Inquiry.status == current)
        .values(status=payload.status).execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Status changed. Reload the inquiry and retry.")
    db.commit()
    db.refresh(inquiry)
    return inquiry
