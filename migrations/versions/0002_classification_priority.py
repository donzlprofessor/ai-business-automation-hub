"""Normalize inquiry priorities for optional classification.

Upgrade maps normal to medium and urgent to high. Downgrade maps medium to
normal; it cannot recover which high values were formerly urgent.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_priority", "inquiries", type_="check")
    op.execute("UPDATE inquiries SET priority = 'medium' WHERE priority = 'normal'")
    op.execute("UPDATE inquiries SET priority = 'high' WHERE priority = 'urgent'")
    op.alter_column(
        "inquiries", "priority", existing_type=sa.String(20),
        existing_nullable=False, server_default="medium",
    )
    op.create_check_constraint("ck_priority", "inquiries", "priority IN ('low', 'medium', 'high')")


def downgrade():
    op.drop_constraint("ck_priority", "inquiries", type_="check")
    op.execute("UPDATE inquiries SET priority = 'normal' WHERE priority = 'medium'")
    op.alter_column(
        "inquiries", "priority", existing_type=sa.String(20),
        existing_nullable=False, server_default="normal",
    )
    op.create_check_constraint(
        "ck_priority", "inquiries", "priority IN ('low', 'normal', 'high', 'urgent')",
    )
