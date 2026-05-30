"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=True),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('supabase_uid', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('google_id', sa.String(255), unique=True, nullable=True),
        sa.Column('apple_id', sa.String(255), unique=True, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_premium', sa.Boolean(), default=False, nullable=False),
        sa.Column('premium_expires_at', sa.DateTime(), nullable=True),
        sa.Column('settings', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False, index=True),
    )

    # User settings table
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('push_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('push_daily_briefing', sa.Boolean(), default=True, nullable=False),
        sa.Column('push_breaking_news', sa.Boolean(), default=True, nullable=False),
        sa.Column('push_max_per_day', sa.Integer(), default=5, nullable=False),
        sa.Column('quiet_hours_start', sa.Integer(), nullable=True),
        sa.Column('quiet_hours_end', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(10), default='en', nullable=False),
        sa.Column('theme', sa.String(20), default='system', nullable=False),
        sa.Column('font_size', sa.String(20), default='medium', nullable=False),
        sa.Column('summary_length', sa.String(20), default='balanced', nullable=False),
        sa.Column('summary_language', sa.String(10), default='auto', nullable=False),
        sa.Column('extra', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('feed_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), default=0, nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('language', sa.String(10), default='en', nullable=False),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('representative_article_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('representative_hash', sa.String(64), nullable=True),
        sa.Column('article_count', sa.Integer(), default=1, nullable=False),
        sa.Column('source_count', sa.Integer(), default=1, nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Articles table
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id'), nullable=False, index=True),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('url_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('title_hash', sa.String(64), nullable=True, index=True),
        sa.Column('content_hash', sa.String(64), nullable=True, index=True),
        sa.Column('simhash', sa.String(64), nullable=True, index=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_model', sa.String(50), nullable=True),
        sa.Column('summary_generated_at', sa.DateTime(), nullable=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id'), nullable=True, index=True),
        sa.Column('is_processed', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_summary_generated', sa.Boolean(), default=False, nullable=False),
        sa.Column('view_count', sa.Integer(), default=0, nullable=False),
        sa.Column('bookmark_count', sa.Integer(), default=0, nullable=False),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )
    op.create_index('idx_articles_source_published', 'articles', ['source_id', 'published_at'])
    op.create_index('idx_articles_category_published', 'articles', ['category', 'published_at'])

    # Topics table
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(200), unique=True, nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('subscriber_count', sa.Integer(), default=0, nullable=False),
        sa.Column('article_count', sa.Integer(), default=0, nullable=False),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id'), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('priority', sa.Integer(), default=0, nullable=False),
        sa.Column('push_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('push_breaking_only', sa.Boolean(), default=False, nullable=False),
        sa.Column('subscribed_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )
    op.create_unique_constraint('uq_user_topic', 'subscriptions', ['user_id', 'topic_id'])

    # Bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id'), nullable=False, index=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # User feeds table
    op.create_table(
        'user_feeds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id'), nullable=True),
        sa.Column('custom_url', sa.String(500), nullable=True),
        sa.Column('custom_name', sa.String(200), nullable=True),
        sa.Column('feed_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('fetch_interval', sa.Integer(), default=60, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id'), nullable=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id'), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_pushed', sa.Boolean(), default=False, nullable=False),
        sa.Column('pushed_at', sa.DateTime(), nullable=True),
        sa.Column('fcm_message_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Push tokens table
    op.create_table(
        'push_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('token', sa.String(500), unique=True, nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('device_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # API usage logs table
    op.create_table(
        'api_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('model', sa.String(50), nullable=False, index=True),
        sa.Column('endpoint', sa.String(100), nullable=True),
        sa.Column('request_type', sa.String(50), nullable=True, index=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('cache_hit', sa.Boolean(), default=False, nullable=False),
        sa.Column('prompt_cached', sa.Boolean(), default=False, nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Daily cost summary table
    op.create_table(
        'daily_cost_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('date', sa.Date(), unique=True, nullable=False, index=True),
        sa.Column('total_requests', sa.Integer(), default=0, nullable=False),
        sa.Column('successful_requests', sa.Integer(), default=0, nullable=False),
        sa.Column('failed_requests', sa.Integer(), default=0, nullable=False),
        sa.Column('cached_requests', sa.Integer(), default=0, nullable=False),
        sa.Column('total_input_tokens', sa.Integer(), default=0, nullable=False),
        sa.Column('total_output_tokens', sa.Integer(), default=0, nullable=False),
        sa.Column('total_tokens', sa.Integer(), default=0, nullable=False),
        sa.Column('total_cost_usd', sa.Float(), default=0, nullable=False),
        sa.Column('cost_by_model', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('cost_by_type', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('articles_processed', sa.Integer(), default=0, nullable=False),
        sa.Column('duplicates_detected', sa.Integer(), default=0, nullable=False),
        sa.Column('dedup_rate', sa.Float(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Budget config table
    op.create_table(
        'budget_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('budget_type', sa.String(20), nullable=False),
        sa.Column('amount_usd', sa.Float(), nullable=False),
        sa.Column('warning_threshold', sa.Float(), default=0.80, nullable=False),
        sa.Column('critical_threshold', sa.Float(), default=0.95, nullable=False),
        sa.Column('shutdown_at_threshold', sa.Float(), default=1.00, nullable=False),
        sa.Column('degradation_strategy', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Cost alerts table
    op.create_table(
        'cost_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('budget_type', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), default=False, nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )

    # Insert default budget configs
    op.execute("""
        INSERT INTO budget_config (
            budget_type,
            amount_usd,
            warning_threshold,
            critical_threshold,
            shutdown_at_threshold,
            degradation_strategy,
            is_active,
            created_at,
            updated_at,
            is_deleted
        )
        VALUES
            ('daily', 5.00, 0.80, 0.95, 1.00, '{}'::jsonb, true, NOW(), NOW(), false),
            ('weekly', 30.00, 0.80, 0.95, 1.00, '{}'::jsonb, true, NOW(), NOW(), false),
            ('monthly', 100.00, 0.80, 0.95, 1.00, '{}'::jsonb, true, NOW(), NOW(), false)
    """)


def downgrade() -> None:
    op.drop_table('cost_alerts')
    op.drop_table('budget_config')
    op.drop_table('daily_cost_summary')
    op.drop_table('api_usage_logs')
    op.drop_table('push_tokens')
    op.drop_table('notifications')
    op.drop_table('user_feeds')
    op.drop_table('bookmarks')
    op.drop_table('subscriptions')
    op.drop_table('topics')
    op.drop_table('articles')
    op.drop_table('events')
    op.drop_table('sources')
    op.drop_table('user_settings')
    op.drop_table('users')
