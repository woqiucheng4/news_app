"""add client analytics events table

Revision ID: 003
Revises: 002
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("event_name", sa.String(length=40), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("event_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_client_analytics_events_event_name", "client_analytics_events", ["event_name"])
    op.create_index("ix_client_analytics_events_event_at", "client_analytics_events", ["event_at"])
    op.create_index("ix_client_analytics_events_user_id", "client_analytics_events", ["user_id"])
    op.create_index("ix_client_analytics_events_is_deleted", "client_analytics_events", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_client_analytics_events_is_deleted", table_name="client_analytics_events")
    op.drop_index("ix_client_analytics_events_user_id", table_name="client_analytics_events")
    op.drop_index("ix_client_analytics_events_event_at", table_name="client_analytics_events")
    op.drop_index("ix_client_analytics_events_event_name", table_name="client_analytics_events")
    op.drop_table("client_analytics_events")
