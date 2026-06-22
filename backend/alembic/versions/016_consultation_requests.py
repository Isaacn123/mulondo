"""Add consultation request tracking for Calendly and website form."""

from alembic import op
import sqlalchemy as sa

revision = "016_consultation_requests"
down_revision = "015_investor_registration_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultation_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("event_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="form"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consultation_requests_email", "consultation_requests", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_consultation_requests_email", table_name="consultation_requests")
    op.drop_table("consultation_requests")
