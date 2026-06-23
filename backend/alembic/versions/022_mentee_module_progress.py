"""Add mentee module progress for quizzes."""

from alembic import op
import sqlalchemy as sa

revision = "022_mentee_module_progress"
down_revision = "021_investor_resources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentee_module_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(length=32), nullable=False),
        sa.Column("reading_completed", sa.Boolean(), nullable=False),
        sa.Column("quiz_passed", sa.Boolean(), nullable=False),
        sa.Column("quiz_score_percent", sa.Integer(), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "module_key", name="uq_mentee_module"),
    )
    op.create_index("ix_mentee_module_progress_user_id", "mentee_module_progress", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_mentee_module_progress_user_id", table_name="mentee_module_progress")
    op.drop_table("mentee_module_progress")
