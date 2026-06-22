"""Track investor registration time and admin review status."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "015_investor_registration_tracking"
down_revision = "014_blog_media"
branch_labels = None
depends_on = None


def _user_columns() -> set[str]:
    bind = op.get_bind()
    inspector = inspect(bind)
    return {column["name"] for column in inspector.get_columns("users")}


def upgrade() -> None:
    columns = _user_columns()

    if "created_at" not in columns:
        op.add_column(
            "users",
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )

    if "admin_registration_seen" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "admin_registration_seen",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )
        op.alter_column("users", "admin_registration_seen", server_default=None)

    # Existing investors are treated as already reviewed.
    op.execute("UPDATE users SET admin_registration_seen = 1 WHERE is_admin = 0")


def downgrade() -> None:
    columns = _user_columns()
    if "admin_registration_seen" in columns:
        op.drop_column("users", "admin_registration_seen")
    if "created_at" in columns:
        op.drop_column("users", "created_at")
