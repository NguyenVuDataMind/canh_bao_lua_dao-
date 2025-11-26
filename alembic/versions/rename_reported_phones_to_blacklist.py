"""rename reported_phones to blacklist_phone and create blacklist_url

Revision ID: rename_to_blacklist
Revises: update_whitelist_url
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_to_blacklist'
down_revision = 'update_whitelist_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Đổi tên bảng reported_phones thành blacklist_phone
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reported_phones') THEN
                ALTER TABLE reported_phones RENAME TO blacklist_phone;
            END IF;
        END $$;
    """)
    
    # 2. Cập nhật foreign key constraint nếu có
    op.execute("""
        DO $$ 
        BEGIN
            -- Đổi tên constraint nếu có
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'reported_phones_report_id_fkey'
            ) THEN
                ALTER TABLE blacklist_phone 
                RENAME CONSTRAINT reported_phones_report_id_fkey TO blacklist_phone_report_id_fkey;
            END IF;
        END $$;
    """)
    
    # 3. Cập nhật relationship trong reports model (nếu cần)
    # Note: SQL không thể sửa Python code, nhưng constraint đã được cập nhật
    
    # 4. Tạo bảng blacklist_url mới
    op.execute("""
        CREATE TABLE IF NOT EXISTS blacklist_url (
            id SERIAL PRIMARY KEY,
            created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            domain VARCHAR NOT NULL,
            description VARCHAR,
            source VARCHAR,
            report_id INTEGER,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
        );
    """)
    
    # 5. Tạo unique constraint cho domain trong blacklist_url
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'blacklist_url_domain_key'
            ) THEN
                ALTER TABLE blacklist_url ADD CONSTRAINT blacklist_url_domain_key UNIQUE (domain);
            END IF;
        END $$;
    """)
    
    # 6. Tạo index cho domain
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_blacklist_url_domain 
        ON blacklist_url (domain);
    """)


def downgrade() -> None:
    # Xóa bảng blacklist_url
    op.execute("DROP TABLE IF EXISTS blacklist_url CASCADE;")
    
    # Đổi tên bảng về lại reported_phones
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blacklist_phone') THEN
                ALTER TABLE blacklist_phone RENAME TO reported_phones;
            END IF;
        END $$;
    """)
    
    # Đổi tên constraint về lại
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'blacklist_phone_report_id_fkey'
            ) THEN
                ALTER TABLE reported_phones 
                RENAME CONSTRAINT blacklist_phone_report_id_fkey TO reported_phones_report_id_fkey;
            END IF;
        END $$;
    """)

