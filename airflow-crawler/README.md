# Airflow Crawler - Tinnhiemmang.vn Domain Crawler

Crawler tự động cào domain từ tinnhiemmang.vn và ghi trực tiếp vào App DB (bảng `white_listURL`).

## 🚀 Khởi động

### Bước 1: Đảm bảo App DB đang chạy

```powershell
# Trong thư mục gốc của project
cd ..
docker-compose up -d db
```

### Bước 2: Khởi động Airflow

```powershell
# Trong thư mục airflow-crawler
cd airflow-crawler
docker-compose up -d
```

### Bước 3: Kiểm tra

- **Airflow UI**: http://localhost:8083
  - Username: `admin`
  - Password: `admin`
  
- **Adminer** (để xem Airflow DB nếu cần): http://localhost:8082
  - System: PostgreSQL
  - Server: `postgres`
  - Username: `airflow`
  - Password: `airflow`
  - Database: `airflow`

## 📋 Sử dụng

### Trigger DAG thủ công

1. Mở Airflow UI: http://localhost:8083
2. Tìm DAG `tinnhiemmang_incremental_daily`
3. Bật DAG (toggle switch bên trái)
4. Click "Trigger DAG" để chạy ngay
5. Click vào DAG → Xem logs để theo dõi tiến trình

### Lịch chạy tự động

DAG sẽ tự động chạy mỗi ngày lúc **8:00 sáng** (theo schedule_interval).

### Xem kết quả

Kết nối DBeaver hoặc Adminer vào App DB để xem bảng `white_listURL`:

```sql
SELECT COUNT(*) FROM "white_listURL" WHERE source = 'tinnhiemmang';
SELECT * FROM "white_listURL" WHERE source = 'tinnhiemmang' ORDER BY id DESC LIMIT 10;
```

## ⚙️ Cấu hình

Các biến môi trường có thể chỉnh trong `docker-compose.yml`:

- `MAX_PAGE`: Số trang tối đa để crawl (mặc định: 2000)
- `SLEEP`: Thời gian nghỉ giữa các request (mặc định: 0.5 giây)
- `APP_DB_HOST`: Host của App DB (mặc định: `fraud_alert_db`)
- `APP_DB_PORT`: Port của App DB (mặc định: `5432`)
- `APP_DB_USER`: Username App DB (mặc định: `fraud_user`)
- `APP_DB_PASSWORD`: Password App DB (mặc định: `fraud_password_123`)
- `APP_DB_NAME`: Tên database App DB (mặc định: `fraud_alert`)

## 🔧 Troubleshooting

### Lỗi kết nối App DB

Nếu Airflow không kết nối được App DB, kiểm tra:

1. App DB container đang chạy:
   ```powershell
   docker ps | findstr fraud_alert_db
   ```

2. Network đã được kết nối:
   ```powershell
   docker network inspect fraud-network
   ```

3. Thử đổi `APP_DB_HOST` thành `host.docker.internal` (Windows/Mac) hoặc IP của host

### Xem logs

```powershell
# Logs của Airflow
docker-compose logs airflow -f

# Logs của crawler script
docker-compose exec airflow python /opt/airflow/crawl_incremental_pg.py
```

## 📊 Kết quả

- Crawler sẽ cào tối đa 2000 trang từ tinnhiemmang.vn
- Dừng khi gặp 2 trang trống liên tiếp
- Dữ liệu được ghi trực tiếp vào bảng `white_listURL` trong App DB
- Mỗi domain được lưu với thông tin: domain, company, first_seen, last_seen
- Source được đánh dấu là `'tinnhiemmang'`

## 🛑 Dừng dịch vụ

```powershell
docker-compose down
```

## 📝 Lưu ý

- Crawler cũ trong app đã được tắt hoàn toàn
- Tất cả việc crawl giờ được quản lý bởi Airflow
- Dữ liệu được ghi trực tiếp vào App DB, không cần sync

