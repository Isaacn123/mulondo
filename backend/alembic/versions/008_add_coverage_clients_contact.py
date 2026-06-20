"""add coverage, clients, and contact sections tables

Revision ID: 008_add_coverage_clients_contact
Revises: 007_add_insights_section
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_add_coverage_clients_contact"
down_revision: Union[str, Sequence[str], None] = "007_add_insights_section"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _section_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )


def upgrade() -> None:
    _section_table("coverage_sections")
    _section_table("clients_sections")
    _section_table("contact_sections")


def downgrade() -> None:
    op.drop_table("contact_sections")
    op.drop_table("clients_sections")
    op.drop_table("coverage_sections")
