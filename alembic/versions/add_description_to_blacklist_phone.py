"""add description to blacklist_phone

Revision ID: add_description_phone
Revises: remove_severity
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_description_phone'
down_revision = 'remove_severity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'blacklist_phone' AND column_name = 'description'
            ) THEN
                ALTER TABLE blacklist_phone ADD COLUMN description VARCHAR;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'blacklist_phone' AND column_name = 'description'
            ) THEN
                ALTER TABLE blacklist_phone DROP COLUMN description;
            END IF;
        END $$;
    """)

