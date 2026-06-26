"""Add cms_documents table for navigation, layout, social, survey, etc."""

from alembic import op
import sqlalchemy as sa

revision = "025_cms_documents"
down_revision = "024_user_avatar_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cms_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )


def downgrade() -> None:
    op.drop_table("cms_documents")
