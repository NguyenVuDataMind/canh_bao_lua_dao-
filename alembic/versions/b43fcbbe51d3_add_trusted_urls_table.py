"""add trusted urls table

Revision ID: b43fcbbe51d3
Revises: acfdc833e652
Create Date: 2025-11-17 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b43fcbbe51d3"
down_revision = "acfdc833e652"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Migration này đã chạy rồi trong database
    # File này chỉ cần để Alembic nhận diện chain migration
    # Không cần thực hiện gì vì bảng trusted_urls sẽ bị xóa bởi migration update_whitelist_url
    pass


def downgrade() -> None:
    # Migration này đã chạy rồi, không cần rollback
    pass

