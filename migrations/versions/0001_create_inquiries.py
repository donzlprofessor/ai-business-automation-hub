"""Create inquiries."""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inquiries",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("customer_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("priority", sa.String(20), server_default="normal", nullable=False),
        sa.Column("status", sa.String(20), server_default="new", nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="ck_priority"),
        sa.CheckConstraint("status IN ('new', 'in_progress', 'resolved')", name="ck_status"),
    )
    op.create_index("ix_inquiries_created_at", "inquiries", ["created_at"])


def downgrade():
    op.drop_index("ix_inquiries_created_at", table_name="inquiries")
    op.drop_table("inquiries")
