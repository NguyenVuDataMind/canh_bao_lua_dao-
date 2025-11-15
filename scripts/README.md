# Scripts Fine-tuning PhoBERT

## Fine-tuning PhoBERT cho Scam Classification

### Cách chạy:

```bash
# Cài đặt dependencies (nếu chưa có)
pip install -r requirements.txt

# Chạy fine-tuning
python scripts/finetune_phobert.py
```

### Kết quả:

- Model sẽ được lưu tại: `data/models/phobert-scam-classifier/`
- Training logs: `data/models/phobert-scam-classifier/logs/`
- Model files bao gồm:
  - `config.json`
  - `pytorch_model.bin` (hoặc `model.safetensors`)
  - `tokenizer_config.json`
  - `vocab.txt`

### Config:

Có thể chỉnh sửa trong `scripts/finetune_phobert.py`:
- `MODEL_NAME`: Model base (mặc định: "vinai/phobert-base-v2")
- `DATASET_PATH`: Đường dẫn dataset (mặc định: "data/datasets/phishing_conversations_vi_840_nospeaker_matched.jsonl")
- `OUTPUT_DIR`: Thư mục lưu model (mặc định: "data/models/phobert-scam-classifier")
- `MAX_LENGTH`: Độ dài tối đa text (mặc định: 256)
- `BATCH_SIZE`: Batch size (mặc định: 16)
- `LEARNING_RATE`: Learning rate (mặc định: 2e-5)
- `NUM_EPOCHS`: Số epochs (mặc định: 5)

### Lưu ý:

- Fine-tuning có thể mất 10-30 phút tùy vào GPU/CPU
- Nếu có GPU, script sẽ tự động dùng FP16 để tăng tốc
- Model sẽ được evaluate sau mỗi epoch
- Early stopping sẽ dừng nếu không cải thiện trong 3 epochs

