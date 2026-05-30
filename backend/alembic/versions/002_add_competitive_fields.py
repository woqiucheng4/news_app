"""add competitive analysis fields

Revision ID: 002
Revises: 001
Create Date: 2026-05-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column(
            "fetch_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
        ),
    )
    op.add_column(
        "sources",
        sa.Column(
            "heat_score",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "articles",
        sa.Column("relevance_score", sa.Numeric(3, 1), nullable=True),
    )

    op.alter_column("sources", "fetch_interval_minutes", server_default=None)
    op.alter_column("sources", "heat_score", server_default=None)


def downgrade() -> None:
    op.drop_column("articles", "relevance_score")
    op.drop_column("sources", "heat_score")
    op.drop_column("sources", "fetch_interval_minutes")
