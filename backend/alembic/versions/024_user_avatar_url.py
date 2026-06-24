"""Add avatar_url to users for admin profile pictures."""

from alembic import op
import sqlalchemy as sa

revision = "024_user_avatar_url"
down_revision = "023_kyc_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(length=500), nullable=False, server_default=""),
    )
    op.alter_column("users", "avatar_url", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
