"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    
    # Create urls table
    op.create_table(
        'urls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('short_code', sa.String(10), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('short_code'),
    )
    op.create_index('ix_urls_short_code', 'urls', ['short_code'])
    op.create_index('ix_urls_created_at', 'urls', ['created_at'])
    op.create_index('ix_urls_expires_at', 'urls', ['expires_at'])
    op.create_index('ix_urls_user_id', 'urls', ['user_id'])
    
    # Create clicks table
    op.create_table(
        'clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('browser_version', sa.String(50), nullable=True),
        sa.Column('os_name', sa.String(100), nullable=True),
        sa.Column('os_version', sa.String(50), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_clicks_url_id', 'clicks', ['url_id'])
    op.create_index('ix_clicks_ip_address', 'clicks', ['ip_address'])
    op.create_index('ix_clicks_clicked_at', 'clicks', ['clicked_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_clicks_clicked_at')
    op.drop_index('ix_clicks_ip_address')
    op.drop_index('ix_clicks_url_id')
    op.drop_table('clicks')
    
    op.drop_index('ix_urls_user_id')
    op.drop_index('ix_urls_expires_at')
    op.drop_index('ix_urls_created_at')
    op.drop_index('ix_urls_short_code')
    op.drop_table('urls')
    
    op.drop_index('ix_users_username')
    op.drop_index('ix_users_email')
    op.drop_table('users')
