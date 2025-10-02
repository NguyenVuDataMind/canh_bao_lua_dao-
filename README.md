Anti-Phishing / Fraud Detection Web App
======================================

What is here
------------
- PostgreSQL schema implementing the DBML and requirements: `schema_postgres.sql`.
- FastAPI backend with Python 3.11+ (authentication, models, schemas)
- Docker Compose services:
  - `db` (Postgres 16) auto-initialized with our schema
  - `redis` (Redis 7) for caching and background jobs
  - `backend` (FastAPI) API server
  - `pgadmin` (PGAdmin4) for DB management

Prerequisites
-------------
- Docker Desktop (Windows/Mac) or Docker Engine + Compose

Quick start
-----------
1. Start services:
   ```bash
   docker compose up -d
   ```
2. Access services:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050
     - Email: admin@example.com
     - Password: admin
3. Add a new server in pgAdmin:
   - Host: db
   - Port: 5432
   - Username: app
   - Password: app_password
   - DB: anti_phishing

Service details
---------------
- Postgres is exposed on `localhost:5432`.
- Redis is exposed on `localhost:6379`.
- FastAPI backend is exposed on `localhost:8000`.
- Database is initialized from files in `docker/initdb/` during first run.
- Schema file is included via `docker/initdb/001_schema.sql`.

Environment (default)
---------------------
- POSTGRES_USER=app
- POSTGRES_PASSWORD=app_password
- POSTGRES_DB=anti_phishing
- JWT_SECRET=your-secret-key-change-in-production
- JWT_REFRESH_SECRET=your-refresh-secret-key-change-in-production

Common operations
-----------------
- View logs:
  ```bash
  docker compose logs -f backend
  docker compose logs -f db
  ```
- Reset database (DANGEROUS: deletes data volume):
  ```bash
  docker compose down -v && docker compose up -d
  ```
- Rebuild backend:
  ```bash
  docker compose build backend
  docker compose up -d backend
  ```

API Endpoints
-------------
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info
- `GET /docs` - API documentation

## Nhật ký thực hiện

### 2024-12-19 15:30 ICT — Thiết lập cấu trúc dự án Python FastAPI
- **Mục tiêu**: Tạo cấu trúc dự án Python với FastAPI theo yêu cầu
- **Thay đổi chính**: 
  - Tạo `backend/` với FastAPI, SQLAlchemy, Pydantic
  - Thiết lập models cho tất cả bảng (Users, Reports, Indicators, Cases, etc.)
  - Tạo schemas Pydantic cho validation
  - Thiết lập authentication với JWT
  - Tạo API endpoints cho AUTH & USERS
  - Cập nhật Docker Compose với Redis và Backend service
- **Kết quả**: Backend API cơ bản hoạt động với authentication
- **Bước tiếp theo**: Tạo API endpoints cho REPORTS, INDICATORS, CASES



# canh_bao_lua_dao-
