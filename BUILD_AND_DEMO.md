# Hướng dẫn Build và Demo

## 📋 Yêu cầu

- Docker và Docker Compose đã được cài đặt
- Python 3.11+ (để train model trước khi build)
- Ít nhất 4GB RAM trống
- Kết nối internet để download models

## ⚠️ Lưu ý quan trọng

- **PhoBERT Model**: Model cần được train TRƯỚC KHI build Docker image để tránh tốn thời gian khi container start
- **PyMuPDF đã được bỏ qua**: Dockerfile đã được cấu hình để skip PyMuPDF (optional dependency cho PDF parsing) vì dự án chỉ cần OCR từ ảnh, không cần xử lý PDF
- **Build sẽ nhanh hơn**: Không cần build PyMuPDF từ source (tiết kiệm thời gian)
- **PaddleOCR vẫn hoạt động đầy đủ**: OCR từ ảnh hoạt động bình thường, chỉ không có tính năng PDF parsing

## 🤖 Train PhoBERT Model (BẮT BUỘC trước khi build)

### Cách 1: Dùng Makefile (Khuyến nghị)

```bash
# Train model
make train-model

# Verify model đã train đúng
make verify-model

# Hoặc train + verify + build cùng lúc
make build-with-model
```

### Cách 2: Chạy trực tiếp

```bash
# Train model
python scripts/finetune_phobert.py

# Verify model
python scripts/verify_model.py
```

**Lưu ý**:
- Training có thể mất 10-30 phút tùy vào CPU/GPU
- Model sẽ được lưu tại: `data/models/phobert-scam-classifier/`
- Sau khi train xong, model sẽ sẵn sàng cho Docker build

## 🚀 Build Docker Image

### Bước 1: Đảm bảo model đã được train

```bash
# Kiểm tra model đã có chưa
make verify-model
```

Nếu chưa có model, chạy:
```bash
make train-model
```

### Bước 2: Build image

```bash
# Dùng Makefile
make build

# Hoặc build trực tiếp
docker build -t fraud-alert-api .
```

**Lưu ý**: 
- Build có thể mất 10-20 phút tùy vào tốc độ internet
- PaddleOCR sẽ tự động download models trong lúc build (lần đầu)
- Model đã train sẽ được copy vào image

### Bước 3: Kiểm tra build thành công

Nếu build thành công, bạn sẽ thấy các message:
```
✓ PaddlePaddle 2.6.2 installed successfully
✓ PaddleOCR installed successfully
✓ PaddleOCR initialized successfully with PaddlePaddle
✓ Models pre-downloaded
```

## 🏃 Chạy Container

### Option 1: Dùng Docker Compose (Khuyến nghị)

```bash
docker-compose up -d
```

### Option 2: Chạy trực tiếp với Docker

```bash
docker run -d \
  --name fraud-alert-api \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e SECRET_KEY=your-secret-key \
  fraud-alert-api
```

## ✅ Kiểm tra Service

### 1. Health Check

```bash
curl http://localhost:5000/api/v1/hello-world
```

Kết quả mong đợi:
```json
{"msg": "Hello world!"}
```

### 2. Xem Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker trực tiếp
docker logs -f fraud-alert-api
```

## 🧪 Demo OCR API

### 1. Đăng ký tài khoản (nếu chưa có)

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 2. Đăng nhập để lấy token

```bash
curl -X POST http://localhost:5000/api/v1/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

Lưu token từ response (ví dụ: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### 3. Test OCR với ảnh

```bash
curl -X POST http://localhost:5000/api/v1/image-processing/extract-text \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "image=@/path/to/your/image.png"
```

**Ví dụ với ảnh có text tiếng Việt:**

```bash
# Tạo file test image (hoặc dùng ảnh có sẵn)
curl -X POST http://localhost:5000/api/v1/image-processing/extract-text \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "image=@test_image.png"
```

**Response mẫu:**
```json
{
  "extracted_text": "Chúc mừng bạn đã trúng thưởng...",
  "cleaned_text": "Chúc mừng bạn đã trúng thưởng...",
  "detected_urls": ["https://bit.ly/scam123"],
  "detected_phones": ["0123456789"],
  "detected_emails": [],
  "cleaning_stats": {
    "original_length": 50,
    "cleaned_length": 48,
    "removed_chars": 2,
    "urls_found": 1,
    "phones_found": 1,
    "emails_found": 0
  }
}
```

## 🌐 Demo qua Web UI

1. Mở browser: `http://localhost:5000`
2. Upload ảnh qua form
3. Xem kết quả OCR

## 🔍 Troubleshooting

### Lỗi: PaddleOCR không khởi tạo được

**Kiểm tra logs:**
```bash
docker logs fraud-alert-api | grep -i "paddleocr\|error"
```

**Giải pháp:**
- Đảm bảo đã build lại image sau khi sửa Dockerfile
- Kiểm tra xem models đã được download chưa

### Lỗi: Out of memory

**Giải pháp:**
- Tăng RAM cho Docker (Settings > Resources > Memory)
- Hoặc giảm số worker trong uvicorn

### Lỗi: Models download chậm

**Giải pháp:**
- Models sẽ được download tự động lần đầu
- Có thể mất 5-10 phút tùy vào tốc độ internet
- Models được cache trong image sau lần build đầu

## 📊 Kiểm tra Performance

### Test với nhiều ảnh

```bash
# Tạo script test
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/v1/image-processing/extract-text \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -F "image=@test_$i.png"
done
```

## 🛑 Dừng Service

```bash
# Docker Compose
docker-compose down

# Docker trực tiếp
docker stop fraud-alert-api
docker rm fraud-alert-api
```

## 📝 Notes

- **Lần đầu chạy**: Models sẽ được download (có thể mất vài phút)
- **Lần sau**: Models đã được cache, chạy nhanh hơn
- **Memory**: PaddleOCR cần ~2GB RAM khi chạy
- **CPU**: Chạy tốt trên CPU, không cần GPU

