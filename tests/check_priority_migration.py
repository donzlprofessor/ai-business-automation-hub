"""PostgreSQL migration smoke check; prepend revision 0002 and pipe to container Python.

Uses a temporary table and rollback, without modifying application inquiries.
"""
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text

from app.core.config import get_settings


def check_priority_migration(upgrade_revision, downgrade_revision):
    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(text("""
            CREATE TEMP TABLE inquiries (
                priority varchar(20) NOT NULL DEFAULT 'normal',
                CONSTRAINT ck_priority CHECK (priority IN ('low','normal','high','urgent'))
            ) ON COMMIT DROP
        """))
        connection.execute(text("SET LOCAL search_path TO pg_temp"))
        connection.execute(text(
            "INSERT INTO inquiries VALUES ('low'), ('normal'), ('high'), ('urgent')"
        ))
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            upgrade_revision()
            priorities = connection.scalars(text("SELECT priority FROM inquiries")).all()
            assert sorted(priorities) == ['high', 'high', 'low', 'medium']
            assert connection.scalar(text(
                "INSERT INTO inquiries DEFAULT VALUES RETURNING priority"
            )) == "medium"
            constraint = connection.scalar(text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = 'pg_temp.inquiries'::regclass AND conname = 'ck_priority'"
            ))
            assert "medium" in constraint and "normal" not in constraint
            downgrade_revision()
            assert connection.scalar(text(
                "INSERT INTO inquiries DEFAULT VALUES RETURNING priority"
            )) == "normal"
            assert "medium" not in connection.scalars(text(
                "SELECT priority FROM inquiries"
            )).all()
        transaction.rollback()
    engine.dispose()
    print("PostgreSQL priority upgrade/downgrade and defaults verified; transaction rolled back.")
