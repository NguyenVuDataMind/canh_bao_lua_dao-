"""add sos_requests table

Revision ID: add_sos_requests
Revises: add_description_phone
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_sos_requests'
down_revision = 'add_description_phone'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sos_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('notes', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sos_requests_created', 'sos_requests', ['created'], unique=False)
    op.create_index('ix_sos_requests_status', 'sos_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sos_requests_status', table_name='sos_requests')
    op.drop_index('ix_sos_requests_created', table_name='sos_requests')
    op.drop_table('sos_requests')

