"""
Script fine-tune PhoBERT cho binary classification (lừa đảo / không lừa đảo)
Sử dụng dataset: phishing_conversations_vi_840_nospeaker_matched.jsonl

Usage:
    python scripts/finetune_phobert.py
"""
import json
import os
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
MODEL_NAME = "vinai/phobert-base-v2"
DATASET_PATH = "data/datasets/phishing_conversations_vi_840_nospeaker_matched.jsonl"
OUTPUT_DIR = "data/models/phobert-scam-classifier"
MAX_LENGTH = 256
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
NUM_EPOCHS = 5


class ScamDataset(Dataset):
    """Dataset cho scam classification"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


def load_dataset(file_path: str):
    """Load dataset từ JSONL file"""
    texts = []
    labels = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                text = data.get('text', '')
                label = data.get('label', '')
                
                if not text or not label:
                    continue
                
                # Convert label to binary: "lừa đảo" = 1, "không lừa đảo" = 0
                label_int = 1 if label == "lừa đảo" else 0
                
                texts.append(text)
                labels.append(label_int)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON line: {e}")
                continue
    
    logger.info(f"Loaded {len(texts)} samples")
    scam_count = sum(labels)
    not_scam_count = len(labels) - scam_count
    logger.info(f"Label distribution: {scam_count} scam, {not_scam_count} not scam")
    
    if len(texts) == 0:
        raise ValueError("No valid samples found in dataset")
    
    return texts, labels


def compute_metrics(eval_pred):
    """Compute metrics cho evaluation"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary')
    accuracy = accuracy_score(labels, predictions)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def main():
    """Main function để fine-tune model"""
    # Load dataset
    logger.info("Loading dataset...")
    texts, labels = load_dataset(DATASET_PATH)
    
    # Split train/val (80/20)
    split_idx = int(len(texts) * 0.8)
    train_texts = texts[:split_idx]
    train_labels = labels[:split_idx]
    val_texts = texts[split_idx:]
    val_labels = labels[split_idx:]
    
    logger.info(f"Train: {len(train_texts)}, Val: {len(val_texts)}")
    
    # Load tokenizer và model
    logger.info(f"Loading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2  # Binary classification
    )
    
    # Create datasets
    train_dataset = ScamDataset(train_texts, train_labels, tokenizer, MAX_LENGTH)
    val_dataset = ScamDataset(val_texts, val_labels, tokenizer, MAX_LENGTH)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=f'{OUTPUT_DIR}/logs',
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=1,  # Chỉ giữ 1 checkpoint để giảm file size
        save_safetensors=True,  # Dùng safetensors format (an toàn hơn, tránh lỗi trên Windows)
        save_only_model=True,  # Chỉ lưu model weights, không lưu optimizer state (không cần cho inference)
        fp16=torch.cuda.is_available(),  # Use FP16 nếu có GPU
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    # Train
    logger.info("Starting training...")
    trainer.train()
    
    # Evaluate
    logger.info("Evaluating...")
    eval_results = trainer.evaluate()
    logger.info(f"Final evaluation results: {eval_results}")
    
    # Trainer đã load best model (vì load_best_model_at_end=True)
    # Tìm checkpoint directory (thường là checkpoint-{số epoch cuối})
    checkpoint_dir = None
    if os.path.exists(OUTPUT_DIR):
        # Tìm tất cả checkpoint directories
        checkpoints = [d for d in os.listdir(OUTPUT_DIR) 
                     if os.path.isdir(os.path.join(OUTPUT_DIR, d)) and d.startswith('checkpoint-')]
        if checkpoints:
            # Lấy checkpoint mới nhất (số lớn nhất)
            checkpoints.sort(key=lambda x: int(x.split('-')[1]) if x.split('-')[1].isdigit() else 0, reverse=True)
            checkpoint_dir = os.path.join(OUTPUT_DIR, checkpoints[0])
            logger.info(f"Found checkpoint directory: {checkpoint_dir}")
    
    # Nếu không tìm thấy checkpoint, dùng OUTPUT_DIR
    if checkpoint_dir is None:
        checkpoint_dir = OUTPUT_DIR
        logger.warning(f"Checkpoint directory not found, using {OUTPUT_DIR}")
    
    # Đảm bảo checkpoint directory tồn tại
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Lưu model vào checkpoint directory
    logger.info(f"Saving model to {checkpoint_dir}...")
    trainer.save_model(checkpoint_dir)
    
    # Lưu tokenizer vào checkpoint directory
    logger.info(f"Saving tokenizer to {checkpoint_dir}...")
    tokenizer.save_pretrained(checkpoint_dir)
    
    # Verify model files exist trong checkpoint directory
    logger.info("Verifying model files...")
    required_files = ['config.json', 'model.safetensors', 'tokenizer_config.json']
    all_files_exist = True
    for file in required_files:
        file_path = os.path.join(checkpoint_dir, file)
        if os.path.exists(file_path):
            logger.info(f"✓ {file} saved successfully at {file_path}")
        else:
            logger.warning(f"⚠ {file} not found at {file_path}")
            all_files_exist = False
    
    if all_files_exist:
        logger.info("✓ All model files saved successfully!")
    else:
        logger.error("⚠ Some model files are missing. Model may not work correctly.")
    
    logger.info("Fine-tuning completed!")
    logger.info(f"Model saved to: {checkpoint_dir}")


if __name__ == "__main__":
    main()

