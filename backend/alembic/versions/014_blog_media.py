"""Add optional image/video media fields to blog posts."""

from alembic import op
import sqlalchemy as sa

revision = "014_blog_media"
down_revision = "013_investor_portal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "blog_posts",
        sa.Column("media_type", sa.String(length=16), nullable=False, server_default=""),
    )
    op.add_column(
        "blog_posts",
        sa.Column("media_url", sa.String(length=512), nullable=False, server_default=""),
    )
    op.alter_column("blog_posts", "media_type", server_default=None)
    op.alter_column("blog_posts", "media_url", server_default=None)


def downgrade() -> None:
    op.drop_column("blog_posts", "media_url")
    op.drop_column("blog_posts", "media_type")
