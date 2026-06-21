"""Add membership_sections table."""

from alembic import op
import sqlalchemy as sa

revision = "010_add_membership_section"
down_revision = "009_add_blog_posts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "membership_sections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )


def downgrade() -> None:
    op.drop_table("membership_sections")
