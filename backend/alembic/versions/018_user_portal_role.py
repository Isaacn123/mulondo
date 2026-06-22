"""Add portal_role to users (investor vs mentee)."""

from alembic import op
import sqlalchemy as sa

revision = "018_user_portal_role"
down_revision = "017_mentorship_sections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "portal_role" not in columns:
        op.add_column(
            "users",
            sa.Column("portal_role", sa.String(length=16), nullable=False, server_default="investor"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "portal_role" in columns:
        op.drop_column("users", "portal_role")
