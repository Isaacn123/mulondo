"""Add KYC submissions for investors and membership mentees."""

from alembic import op
import sqlalchemy as sa

revision = "023_kyc_submissions"
down_revision = "022_mentee_module_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kyc_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("portal_role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("legal_full_name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("id_number", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("government_id_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("government_id_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("proof_of_address_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("proof_of_address_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("member_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("rejection_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("admin_seen", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_kyc_submissions_user_id", "kyc_submissions", ["user_id"])
    op.create_index("ix_kyc_submissions_portal_role", "kyc_submissions", ["portal_role"])
    op.create_index("ix_kyc_submissions_status", "kyc_submissions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_kyc_submissions_status", table_name="kyc_submissions")
    op.drop_index("ix_kyc_submissions_portal_role", table_name="kyc_submissions")
    op.drop_index("ix_kyc_submissions_user_id", table_name="kyc_submissions")
    op.drop_table("kyc_submissions")
