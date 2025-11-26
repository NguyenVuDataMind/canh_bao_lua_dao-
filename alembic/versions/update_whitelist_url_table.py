"""update whitelist url table structure

Revision ID: update_whitelist_url
Revises: b43fcbbe51d3
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_whitelist_url'
down_revision = 'b43fcbbe51d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Xóa bảng trusted_urls và enum type nếu tồn tại
    op.execute("DROP TABLE IF EXISTS trusted_urls CASCADE;")
    op.execute("DROP TYPE IF EXISTS whitelistmatchtype CASCADE;")
    
    # 2. Đảm bảo bảng white_listurl tồn tại
    # - Nếu có tinnhiemmang → đổi tên thành white_listurl
    # - Nếu chưa có cả 2 → tạo mới white_listurl với schema đúng
    op.execute("""
        DO $$ 
        BEGIN
            -- Nếu có tinnhiemmang thì đổi tên
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tinnhiemmang') THEN
                ALTER TABLE tinnhiemmang RENAME TO white_listurl;
            -- Nếu chưa có white_listurl thì tạo mới
            ELSIF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'white_listurl') THEN
                CREATE TABLE white_listurl (
                    id SERIAL PRIMARY KEY,
                    domain VARCHAR NOT NULL,
                    company VARCHAR,
                    first_seen DATE NOT NULL DEFAULT CURRENT_DATE,
                    last_seen DATE NOT NULL DEFAULT CURRENT_DATE,
                    source VARCHAR
                );
            END IF;
        END $$;
    """)
    
    # 3. Thêm cột id (SERIAL PRIMARY KEY) nếu chưa có - chỉ khi bảng tồn tại
    op.execute("""
        DO $$ 
        DECLARE
            pk_constraint_name TEXT;
        BEGIN
            -- Chỉ thực hiện nếu bảng tồn tại
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'white_listurl') THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'white_listurl' AND column_name = 'id'
                ) THEN
                    -- Tìm và drop primary key constraint cũ trên domain nếu có
                    BEGIN
                        SELECT conname INTO pk_constraint_name
                        FROM pg_constraint 
                        WHERE conrelid = 'white_listurl'::regclass 
                        AND contype = 'p'
                        LIMIT 1;
                        
                        IF pk_constraint_name IS NOT NULL THEN
                            EXECUTE format('ALTER TABLE white_listurl DROP CONSTRAINT %I', pk_constraint_name);
                        END IF;
                    EXCEPTION
                        WHEN undefined_table THEN
                            NULL;
                    END;
                    
                    -- Thêm cột id
                    ALTER TABLE white_listurl ADD COLUMN id SERIAL;
                    
                    -- Tạo primary key mới trên id
                    ALTER TABLE white_listurl ADD PRIMARY KEY (id);
                END IF;
            END IF;
        END $$;
    """)
    
    # 4. Thêm các cột còn thiếu nếu bảng đã tồn tại (từ tinnhiemmang)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'white_listurl') THEN
                -- Thêm cột company nếu chưa có
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'white_listurl' AND column_name = 'company'
                ) THEN
                    ALTER TABLE white_listurl ADD COLUMN company VARCHAR;
                END IF;
                
                -- Thêm cột first_seen nếu chưa có
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'white_listurl' AND column_name = 'first_seen'
                ) THEN
                    ALTER TABLE white_listurl ADD COLUMN first_seen DATE NOT NULL DEFAULT CURRENT_DATE;
                END IF;
                
                -- Thêm cột last_seen nếu chưa có
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'white_listurl' AND column_name = 'last_seen'
                ) THEN
                    ALTER TABLE white_listurl ADD COLUMN last_seen DATE NOT NULL DEFAULT CURRENT_DATE;
                END IF;
                
                -- Thêm cột source nếu chưa có
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'white_listurl' AND column_name = 'source'
                ) THEN
                    ALTER TABLE white_listurl ADD COLUMN source VARCHAR;
                END IF;
            END IF;
        END $$;
    """)
    
    # 5. Cập nhật source = 'tinnhiemmang' cho các dòng hiện có - chỉ khi bảng tồn tại
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'white_listurl') THEN
                UPDATE white_listurl SET source = 'tinnhiemmang' WHERE source IS NULL;
            END IF;
        END $$;
    """)
    
    # 6. Thêm unique constraint cho domain nếu chưa có - chỉ khi bảng tồn tại
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'white_listurl') THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'white_listurl_domain_key'
                ) THEN
                    ALTER TABLE white_listurl ADD CONSTRAINT white_listurl_domain_key UNIQUE (domain);
                END IF;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Xóa unique constraint trên domain
    op.execute("ALTER TABLE white_listurl DROP CONSTRAINT IF EXISTS white_listurl_domain_key;")
    
    # Xóa cột source
    op.execute("ALTER TABLE white_listurl DROP COLUMN IF EXISTS source;")
    
    # Xóa cột id và khôi phục primary key trên domain
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'white_listurl' AND column_name = 'id'
            ) THEN
                ALTER TABLE white_listurl DROP CONSTRAINT IF EXISTS white_listurl_pkey;
                ALTER TABLE white_listurl DROP COLUMN id;
                ALTER TABLE white_listurl ADD PRIMARY KEY (domain);
            END IF;
        END $$;
    """)
    
    # Đổi tên bảng về lại tinnhiemmang
    op.execute("ALTER TABLE IF EXISTS white_listurl RENAME TO tinnhiemmang;")

