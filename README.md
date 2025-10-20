# Scam Expert System — Fraud Detection & Tier Classification

This repository contains a fully working, *explainable* expert system for scam/fraud detection with tier classification (T0–T3), a FastAPI microservice, a seed rule-base, database schema/migrations, a toy dataset, and a first-pass ML training script.


-- linux 
## Quick start
```bash
# 1) Create a virtual environment and install deps
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt

# 2) (optional) Train the tiny ML model
python scripts/train_model.py

# 3) Run the API
uvicorn app.main:app --reload --port 8080

# 4) Try it
curl -X POST http://localhost:8080/detect -H "content-type: application/json" -d @data/sample_event.json
```


-- windows
## 
``` 
# 1. Tạo virtual environment (đã làm)
python -m venv .venv

# 2. Kích hoạt virtual environment (Windows)
.venv\Scripts\activate

# 3. Cài đặt dependencies
pip install -r app/requirements.txt

# 4. Train ML model (tùy chọn)
python scripts/train_model.py

# 5. Chạy server
uvicorn app.main:app --reload --port 8080

# Mở browser và truy cập:
# http://localhost:8080
```