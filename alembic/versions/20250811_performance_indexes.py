"""Add performance indexes

Revision ID: perf_indexes_001
Revises: ffb6eb27351c
Create Date: 2025-08-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'perf_indexes_001'
down_revision = 'ffb6eb27351c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add critical performance indexes."""
    
    # Users table - frequent lookups
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_tier', 'users', ['tier'])
    
    # Subscriptions - billing queries
    op.create_index('idx_subscriptions_user_active', 'subscriptions', ['user_id', 'status'])
    op.create_index('idx_subscriptions_expires', 'subscriptions', ['expires_at'])
    
    # API Usage - analytics and rate limiting
    op.create_index('idx_api_usage_user_created', 'api_usage', ['user_id', 'created_at'])
    op.create_index('idx_api_usage_endpoint_method', 'api_usage', ['endpoint', 'method'])
    
    # Signals - core business queries
    op.create_index('idx_signals_symbol_created', 'signals', ['symbol', 'created_at'])
    op.create_index('idx_signals_user_created', 'signals', ['user_id', 'created_at'])
    op.create_index('idx_signals_confidence', 'signals', ['confidence'])
    
    # Market Data - time series queries
    op.create_index('idx_market_data_symbol_timestamp', 'market_data', ['symbol', 'timestamp'])
    
    # Audit Logs - security queries
    op.create_index('idx_audit_logs_risk_score', 'audit_logs', ['risk_score', 'created_at'])
    op.create_index('idx_audit_logs_user_event', 'audit_logs', ['user_id', 'event_type'])


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop all indexes
    op.drop_index('idx_users_email_active', 'users')
    op.drop_index('idx_users_tier', 'users')
    op.drop_index('idx_subscriptions_user_active', 'subscriptions')
    op.drop_index('idx_subscriptions_expires', 'subscriptions')
    op.drop_index('idx_api_usage_user_created', 'api_usage')
    op.drop_index('idx_api_usage_endpoint_method', 'api_usage')
    op.drop_index('idx_signals_symbol_created', 'signals')
    op.drop_index('idx_signals_user_created', 'signals')
    op.drop_index('idx_signals_confidence', 'signals')
    op.drop_index('idx_market_data_symbol_timestamp', 'market_data')
    op.drop_index('idx_audit_logs_risk_score', 'audit_logs')
    op.drop_index('idx_audit_logs_user_event', 'audit_logs')