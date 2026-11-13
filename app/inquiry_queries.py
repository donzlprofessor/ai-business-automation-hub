"""Shared, parameterized read queries for legacy and dashboard clients."""
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Inquiry
from app.schemas import InquiryQuery, InquiryStats


def filtered_query(params: InquiryQuery):
    query = select(Inquiry)
    if search := params.search.strip():
        query = query.where(or_(
            *(column.icontains(search, autoescape=True) for column in (
                Inquiry.customer_name, Inquiry.email, Inquiry.message, Inquiry.ai_summary,
            ))
        ))
    if params.category == "unclassified":
        query = query.where(Inquiry.category.is_(None))
    elif params.category:
        query = query.where(Inquiry.category == params.category)
    if params.priority:
        query = query.where(Inquiry.priority == params.priority)
    if params.status:
        query = query.where(Inquiry.status == params.status)
    return query


def read_inquiries(db: Session, params: InquiryQuery):
    sort_column = {
        "created_at": Inquiry.created_at,
        "customer_name": func.lower(Inquiry.customer_name),
        "priority": case((Inquiry.priority == "high", 3), (Inquiry.priority == "medium", 2),
                         else_=1),
    }[params.sort_by]
    ordering = sort_column.asc() if params.sort_dir == "asc" else sort_column.desc()
    return db.scalars(
        filtered_query(params).order_by(ordering, Inquiry.id.desc())
        .offset(params.offset).limit(params.limit)
    ).all()


def count_inquiries(db: Session, params: InquiryQuery) -> int:
    return db.scalar(select(func.count()).select_from(filtered_query(params).subquery())) or 0


def inquiry_stats(db: Session) -> InquiryStats:
    conditions = {
        "high_priority": Inquiry.priority == "high",
        "sales": Inquiry.category == "sales",
        "support": Inquiry.category == "support",
        "other": Inquiry.category == "other",
        "unclassified": Inquiry.category.is_(None),
        "new": Inquiry.status == "new",
        "in_progress": Inquiry.status == "in_progress",
        "resolved": Inquiry.status == "resolved",
    }
    row = db.execute(select(
        func.count(Inquiry.id).label("total"),
        *(func.count(case((condition, 1))).label(name) for name, condition in conditions.items()),
    )).mappings().one()
    return InquiryStats(**row)
