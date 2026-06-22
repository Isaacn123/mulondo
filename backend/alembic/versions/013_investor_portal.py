"""Extend users and add investor messaging."""

from alembic import op
import sqlalchemy as sa

revision = "013_investor_portal"
down_revision = "012_add_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=False, server_default=""))
    op.alter_column("users", "first_name", server_default=None)
    op.alter_column("users", "last_name", server_default=None)

    op.create_table(
        "investor_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investor_id", sa.Integer(), nullable=False),
        sa.Column("from_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["investor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investor_messages_investor_id", "investor_messages", ["investor_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_investor_messages_investor_id", table_name="investor_messages")
    op.drop_table("investor_messages")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
