"""Exercise status updates on a temporary PostgreSQL table; preserve application data.

Run through the built API container (see README). Uses the real route function and
transaction commits inside savepoints, then rolls back the outer transaction.
"""
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.inquiries import update_inquiry_status
from app.core.config import get_settings
from app.models import Inquiry
from app.schemas import InquiryStatusUpdate


def check():
    engine = create_engine(get_settings().database_url)
    fingerprint = text(
        "SELECT md5(coalesce(string_agg(row_to_json(i)::text, '|' ORDER BY id), '')) "
        "FROM public.inquiries i"
    )
    with engine.connect() as connection:
        with connection.begin() as transaction:
            before = connection.scalar(fingerprint)
            connection.execute(text(
                "CREATE TEMP TABLE inquiries (LIKE public.inquiries INCLUDING ALL) ON COMMIT DROP"
            ))
            with Session(connection, join_transaction_mode="create_savepoint") as session:
                inquiry = Inquiry(
                    customer_name="Isolated PostgreSQL status test", email="test@example.com",
                    message="Temporary test record", category="support", priority="high",
                )
                session.add(inquiry)
                session.commit()
                for expected, target in [
                    ("new", "in_progress"), ("in_progress", "resolved"),
                    ("resolved", "in_progress"),
                ]:
                    updated = update_inquiry_status(inquiry.id, InquiryStatusUpdate(
                        status=target, expected_status=expected,
                    ), session)
                    assert updated.status == target
                try:
                    update_inquiry_status(inquiry.id, InquiryStatusUpdate(
                        status="resolved", expected_status="new",
                    ), session)
                except HTTPException as error:
                    assert error.status_code == 409
                else:
                    raise AssertionError("Stale status was accepted")
                assert connection.scalar(fingerprint) == before
            transaction.rollback()
        assert connection.scalar(fingerprint) == before
    engine.dispose()
    print("PostgreSQL status progression, reopening, and stale-state checks passed.")
    print("Temporary transaction rolled back; application inquiry fingerprint unchanged.")


if __name__ == "__main__":
    check()
