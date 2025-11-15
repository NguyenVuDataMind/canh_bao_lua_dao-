# Workflow Train Model và Build Docker

## 📝 Tóm tắt thay đổi

Đã sửa các vấn đề sau để đảm bảo model được train và lưu đúng cách cho production:

### 1. ✅ Sửa script fine-tuning (`scripts/finetune_phobert.py`)
- **Vấn đề**: Model được lưu ở `checkpoint-42/` subdirectory, nhưng service tìm ở root directory
- **Giải pháp**: Sửa `trainer.save_model()` để lưu model ở root directory (`OUTPUT_DIR`)
- **Thay đổi**: 
  - Thêm argument `OUTPUT_DIR` vào `trainer.save_model(OUTPUT_DIR)`
  - Thêm verification để đảm bảo tất cả files cần thiết đã được lưu
  - Thêm logging chi tiết

### 2. ✅ Thêm Makefile targets
- `make train-model`: Train PhoBERT model
- `make verify-model`: Verify model đã train đúng
- `make build-with-model`: Train + verify + build Docker image

### 3. ✅ Tạo script verify model (`scripts/verify_model.py`)
- Kiểm tra tất cả files cần thiết có tồn tại không
- Hiển thị kích thước files
- Exit code 0 nếu OK, 1 nếu thiếu files

### 4. ✅ Cập nhật Dockerfile
- Thêm comment giải thích về model persistence
- Model sẽ được copy vào image nếu train trước khi build

### 5. ✅ Cập nhật tài liệu (`BUILD_AND_DEMO.md`)
- Thêm hướng dẫn train model trước khi build
- Giải thích workflow đầy đủ

## 🚀 Workflow cho Production

### Bước 1: Train Model (Local)

```bash
# Cài đặt dependencies (nếu chưa có)
pip install -r requirements.txt

# Train model
make train-model

# Verify model
make verify-model
```

**Kết quả**: Model được lưu tại `data/models/phobert-scam-classifier/`

### Bước 2: Build Docker Image

```bash
# Build với model đã train
make build-with-model

# Hoặc build riêng
make build
```

**Lưu ý**: Model sẽ được copy vào Docker image

### Bước 3: Deploy

```bash
# Start services
make up

# Check logs
make logs
```

**Kết quả**: 
- Container start nhanh (không cần train)
- API sẵn sàng với model đã train
- Scam classification hoạt động ngay

## 📁 Cấu trúc Model Files

Sau khi train, model sẽ có cấu trúc:

```
data/models/phobert-scam-classifier/
├── config.json              # Model configuration
├── model.safetensors        # Model weights (hoặc pytorch_model.bin)
├── tokenizer_config.json     # Tokenizer configuration
├── vocab.txt                # Vocabulary (hoặc tokenizer.json)
└── logs/                    # Training logs (optional)
```

## ⚠️ Lưu ý quan trọng

1. **Train trước khi build**: Model phải được train trước khi build Docker image
2. **Volume mount**: `docker-compose.yml` mount `./data/models` vào container, nên model từ host sẽ override model trong image (cho phép update model mà không cần rebuild)
3. **Path consistency**: Service tìm model ở `data/models/phobert-scam-classifier/` (root), không phải trong checkpoint subdirectory

## 🔧 Troubleshooting

### Model không tìm thấy khi chạy container

**Nguyên nhân**: Model chưa được train hoặc ở sai path

**Giải pháp**:
```bash
# Train model
make train-model

# Verify
make verify-model

# Rebuild và restart
make build
make restart
```

### Model files thiếu

**Nguyên nhân**: Training bị gián đoạn hoặc lỗi

**Giải pháp**:
```bash
# Xóa model cũ (nếu có)
rm -rf data/models/phobert-scam-classifier

# Train lại
make train-model

# Verify
make verify-model
```

### Container start chậm

**Nguyên nhân**: Model chưa train, container đang cố load model không tồn tại

**Giải pháp**: Train model trước khi build (theo workflow ở trên)

## 📊 Model Training Info

- **Base Model**: `vinai/phobert-base-v2`
- **Dataset**: `data/datasets/phishing_conversations_vi_840_nospeaker_matched.jsonl`
- **Task**: Binary classification (lừa đảo / không lừa đảo)
- **Training time**: 10-30 phút (tùy CPU/GPU)
- **Output**: `data/models/phobert-scam-classifier/`

## ✅ Checklist trước khi deploy

- [ ] Model đã được train (`make verify-model` pass)
- [ ] Docker image đã được build với model
- [ ] Container start thành công
- [ ] API endpoint `/image-processing/extract-text` hoạt động
- [ ] Scam classification trả về kết quả (không phải None)

