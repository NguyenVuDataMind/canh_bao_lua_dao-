"""remove severity column from reports

Revision ID: remove_severity
Revises: rename_to_blacklist
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_severity'
down_revision = 'rename_to_blacklist'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Xóa cột severity khỏi bảng reports
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'reports' AND column_name = 'severity'
            ) THEN
                ALTER TABLE reports DROP COLUMN severity;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Thêm lại cột severity (nếu cần rollback)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'reports' AND column_name = 'severity'
            ) THEN
                ALTER TABLE reports ADD COLUMN severity VARCHAR;
            END IF;
        END $$;
    """)

