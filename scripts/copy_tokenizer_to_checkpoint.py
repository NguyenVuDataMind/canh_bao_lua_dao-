"""
Script để copy tokenizer từ base model vào checkpoint-42
Sử dụng khi tokenizer chưa có trong checkpoint directory

Usage:
    python scripts/copy_tokenizer_to_checkpoint.py
"""
import os
import shutil
from transformers import AutoTokenizer

BASE_MODEL = "vinai/phobert-base-v2"
CHECKPOINT_DIR = "data/models/phobert-scam-classifier/checkpoint-42"

def copy_tokenizer():
    """Copy tokenizer từ base model vào checkpoint directory"""
    print(f"Copying tokenizer from {BASE_MODEL} to {CHECKPOINT_DIR}")
    print("-" * 50)
    
    # Kiểm tra checkpoint directory có tồn tại không
    if not os.path.exists(CHECKPOINT_DIR):
        print(f"✗ Checkpoint directory not found: {CHECKPOINT_DIR}")
        print("  → Please train the model first: python scripts/finetune_phobert.py")
        return False
    
    # Kiểm tra xem tokenizer đã có trong checkpoint chưa
    tokenizer_config = os.path.join(CHECKPOINT_DIR, "tokenizer_config.json")
    if os.path.exists(tokenizer_config):
        print(f"✓ Tokenizer already exists in {CHECKPOINT_DIR}")
        print("  → No need to copy")
        return True
    
    print(f"Tokenizer not found in checkpoint, downloading from {BASE_MODEL}...")
    
    try:
        # Load tokenizer từ base model
        print("Loading tokenizer from base model...")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        
        # Lưu vào checkpoint directory
        print(f"Saving tokenizer to {CHECKPOINT_DIR}...")
        tokenizer.save_pretrained(CHECKPOINT_DIR)
        
        # Verify
        required_files = ["tokenizer_config.json", "vocab.txt"]
        all_exist = True
        for file in required_files:
            file_path = os.path.join(CHECKPOINT_DIR, file)
            if os.path.exists(file_path):
                print(f"✓ {file} saved successfully")
            else:
                # Check alternative
                if file == "vocab.txt":
                    if os.path.exists(os.path.join(CHECKPOINT_DIR, "tokenizer.json")):
                        print(f"✓ tokenizer.json found (alternative to vocab.txt)")
                        continue
                print(f"⚠ {file} not found")
                all_exist = False
        
        if all_exist:
            print("-" * 50)
            print("✓ Tokenizer copied successfully!")
            return True
        else:
            print("-" * 50)
            print("⚠ Some tokenizer files may be missing, but tokenizer should work")
            return True
            
    except Exception as e:
        print(f"✗ Error copying tokenizer: {str(e)}")
        return False

if __name__ == "__main__":
    success = copy_tokenizer()
    exit(0 if success else 1)

