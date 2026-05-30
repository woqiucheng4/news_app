"""add session_id to client analytics events

Revision ID: 004
Revises: 003
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_analytics_events",
        sa.Column("session_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_client_analytics_events_session_id",
        "client_analytics_events",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_client_analytics_events_session_id", table_name="client_analytics_events")
    op.drop_column("client_analytics_events", "session_id")
