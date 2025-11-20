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
    # Tạo enum type và table bằng raw SQL để tránh SQLAlchemy tự tạo enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE whitelistmatchtype AS ENUM ('exact', 'prefix', 'wildcard');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Tạo table bằng raw SQL để tránh SQLAlchemy tự động tạo enum type
    op.execute("""
        CREATE TABLE IF NOT EXISTS trusted_urls (
            id SERIAL PRIMARY KEY,
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            normalized_pattern VARCHAR NOT NULL,
            match_type whitelistmatchtype NOT NULL,
            source VARCHAR,
            description VARCHAR,
            raw_example VARCHAR,
            is_active BOOLEAN NOT NULL DEFAULT true
        );
    """)
    
    # Tạo index
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_trusted_urls_normalized_pattern 
        ON trusted_urls (normalized_pattern);
    """)
    
    # Tạo unique constraint
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE trusted_urls 
            ADD CONSTRAINT uq_trusted_urls_pattern_match 
            UNIQUE (normalized_pattern, match_type);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Drop table và enum type bằng raw SQL
    op.execute("DROP TABLE IF EXISTS trusted_urls CASCADE;")
    op.execute("DROP TYPE IF EXISTS whitelistmatchtype CASCADE;")

