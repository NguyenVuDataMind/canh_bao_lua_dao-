"""
Script để verify model đã được train và lưu đúng cách
Sử dụng để kiểm tra trước khi build Docker image

Usage:
    python scripts/verify_model.py
"""
import os
import sys

MODEL_PATH = "data/models/phobert-scam-classifier/checkpoint-42"
REQUIRED_FILES = [
    "config.json",
    "model.safetensors",  # hoặc pytorch_model.bin
    "tokenizer_config.json",
    "vocab.txt",  # hoặc tokenizer.json
]

def verify_model():
    """Verify model files exist"""
    print(f"Verifying model at: {MODEL_PATH}")
    print("-" * 50)
    
    if not os.path.exists(MODEL_PATH):
        print(f"✗ Model directory not found: {MODEL_PATH}")
        print("  → Run 'python scripts/finetune_phobert.py' to train the model")
        return False
    
    missing_files = []
    found_files = []
    
    for file in REQUIRED_FILES:
        file_path = os.path.join(MODEL_PATH, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_mb = size / (1024 * 1024)
            print(f"✓ {file:25s} ({size_mb:.2f} MB)")
            found_files.append(file)
        else:
            print(f"✗ {file:25s} (missing)")
            missing_files.append(file)
    
    # Check for alternative files
    if "model.safetensors" in missing_files:
        if os.path.exists(os.path.join(MODEL_PATH, "pytorch_model.bin")):
            print("  → Found pytorch_model.bin instead (acceptable)")
            missing_files.remove("model.safetensors")
    
    if "vocab.txt" in missing_files:
        if os.path.exists(os.path.join(MODEL_PATH, "tokenizer.json")):
            print("  → Found tokenizer.json instead (acceptable)")
            missing_files.remove("vocab.txt")
    
    print("-" * 50)
    
    if missing_files:
        print(f"✗ Missing {len(missing_files)} required file(s): {', '.join(missing_files)}")
        print("\n  → Run 'python scripts/finetune_phobert.py' to train the model")
        return False
    else:
        print(f"✓ All required files found! ({len(found_files)} files)")
        print("\n  → Model is ready for Docker build")
        return True

if __name__ == "__main__":
    success = verify_model()
    sys.exit(0 if success else 1)

